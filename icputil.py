import random
from mathutils import Vector
from bpyutil import *
from kd_tree import KDTree
from numpy.linalg import solve, svd, det


def icp(obj_P, obj_Q, max_iterations=100, eps=0.001, sample_rate=0.5, k=2.5, normal_dissimilarity_thres=0.5,
        point_to_plane=False, sampling_strategy="RANDOM_POINT", distance_strategy="EUCLIDEAN",
        rejection_criterion="K_MEDIAN") -> (bool, int):
    """
    Perform iterative closest point on two objects
    :param obj_P: First object, to be transformed to second one
    :param obj_Q: Second object
    :param max_iterations: maximum number of iterations
    :param eps: threshold for stopping if converged

    :param sample_rate: portion of points to sample in first mesh
    :param k: cutoff distance
    :return: if algorithm converged, and in how many iterations
    """

    # keep track of convergence
    converged = False
    num_iterations_so_far = 0

    # kdtree of worldspace verts and normals of object Q, for optimizing nearest neighbor queries
    q_world = obj_Q.matrix_world
    qs = [(q_world @ q.co, q_world @ q.normal) for q in obj_Q.data.vertices]

    distance_lambda = lambda p1, p2: (p1[0] - p2[0]).length
    if distance_strategy == "NORMAL_WEIGHTED":
        # Use cosine similarity to weigh the distance
        distance_lambda = lambda p1, p2: np.dot(p1, p2) * (p1[0] - p2[0]).length

    qs_kdtree = KDTree(qs, distance_lambda, lambda point, ax: point[0][ax])

    for _ in range(max_iterations):
        num_iterations_so_far += 1

        ps_samples = sample_points(obj_P, sample_rate, sampling_strategy)
        n_samples = len(ps_samples)

        # for each sampled point, get the closest point in q and its distance
        point_pairs = []
        for p, p_normal in ps_samples:
            (q, nq), dist = qs_kdtree.get_nearest_neighbor((p, None))
            point_pairs.append((p, q, nq, p_normal, dist))
        if rejection_criterion == "K_MEDIAN":
            # compute median distance, for filtering outliers
            sorted_point_pairs = sorted(point_pairs, key=lambda t: t[4])
            median_distance = sorted_point_pairs[n_samples // 2][4]

            # filter outlier point-pairs that don't satisfy the k*median condition
            point_pairs = [(p, q, nq, p_normal) for (p, q, nq, p_normal, dist) in point_pairs if
                           dist <= k * median_distance]
        elif rejection_criterion == "DISSIMILAR_NORMALS":
            point_pairs = [(p, q, nq, p_normal) for (p, q, nq, p_normal, dist) in point_pairs if (1-nq.dot(p_normal)) <= normal_dissimilarity_thres]
            # for _, _, nq, p_normal in point_pairs:
            #     print(nq.dot(p_normal))
            # print(point_pairs[0])
            # print(type(point_pairs[0][2]), type(point_pairs[0][3]))
            # raise RuntimeError("Todo")
        else:
            raise RuntimeError("Invalid point-pair rejection criterion")

        # compute optimal rigid transformation.
        if point_to_plane:
            r_opt, t_opt = opt_rigid_transformation_point_to_plane(point_pairs)
        else:
            r_opt, t_opt = opt_rigid_transformation_point_to_point(point_pairs)

        # check if converged, if so stop
        trans_norm = np.linalg.norm(t_opt)
        if trans_norm <= eps and np.allclose(r_opt, np.eye(3), atol=eps):
            converged = True
            break

        # transform object optimal transformation
        rigid_transform(t_opt, r_opt, obj_P)

    return converged, num_iterations_so_far


def centroid(ps: list[Vector]):
    p_sum = Vector((0, 0, 0))
    for p in ps:
        p_sum += p

    return p_sum / len(ps)


def opt_rigid_transformation_point_to_point(point_pairs: list[(Vector, Vector)]):
    """
    Compute the optimal rigid transformation between pairs of points

    :param point_pairs: a list of pairs (p_i, q_i)
    :return: translation vector and rotation matrix for optimal rigid transformation from
    points p_i to q_i
    """

    # compute centroids
    centroid_p = np.array(centroid([t[0] for t in point_pairs]))
    centroid_q = np.array(centroid([t[1] for t in point_pairs]))

    # compute covariance matrix
    covariance_matrix = np.zeros((3, 3))
    for pi, qi, _, _ in point_pairs:
        covariance_matrix += np.outer(np.array(pi) - centroid_p, np.array(qi) - centroid_q)
    covariance_matrix /= len(point_pairs)

    # singular value decomposition
    U, _, Vt, = np.linalg.svd(covariance_matrix, full_matrices=False)
    V = Vt.transpose()
    Ut = U.transpose()

    # compute optimal rotation and translation
    m = np.eye(3)
    m[2, 2] = np.linalg.det((V @ Ut))
    r_opt = V @ m @ Ut
    t_opt = centroid_q - r_opt @ centroid_p

    return r_opt, t_opt


def sample_points(obj, sample_rate=0.5, sampling_strategy="RANDOM_POINT"):
    """
    Returns a list of tuples: List[(point,normal)]
    """
    # Get world space vertices and the normals of object P
    ps = [(obj.matrix_world @ p.co, p.normal.copy()) for p in obj.data.vertices]
    n_samples = int(sample_rate * len(ps))
    if sampling_strategy == "RANDOM_POINT":
        # Sample n random points in mesh P
        n_samples = int(sample_rate * len(ps))
        ps_samples = random.sample(ps, n_samples)
        return ps_samples
    elif sampling_strategy == "NORMAL":
        # Create the normal "buckets" and sample from them
        normal_dictionary = _construct_normal_space_buckets(ps)
        normal_samples = random.sample(normal_dictionary.keys(), n_samples)
        ps_samples = [(random.choice(normal_dictionary[sample]), sample) for sample in normal_samples]
        return ps_samples
    elif sampling_strategy == "STRATIFIED_NORMAL":
        normal_dictionary = _construct_normal_space_buckets(ps)
        ps_samples = []
        # Sample once from each stratum until we have the amount of requested samples
        while len(ps_samples) < n_samples:
            for stratum in normal_dictionary.keys():
                ps_samples.append((random.choice(normal_dictionary[stratum]), stratum))
        return ps_samples
    else:
        raise RuntimeError("Invalid point sampling strategy")


def _construct_normal_space_buckets(ps_normals) -> dict:
    """
    Returns a dictionary of normal -> list[Vector].
    The normal is represented as a triple.
    """
    # Create dictionary of normals so we can sample them uniformly
    normal_dictionary = dict()
    for point, normal in ps_normals:
        key = (normal[0], normal[1], normal[2])
        if key not in normal_dictionary.keys():
            normal_dictionary[key] = []
        normal_dictionary[key].append(point)
    return normal_dictionary


def opt_rigid_transformation_point_to_plane(point_pairs: list[(Vector, Vector, Vector)]):
    A = np.zeros((6, 6))
    b = np.zeros((6,))

    for p, q, nq, _ in point_pairs:
        # convert vectors to numpy arrays.
        p = np.array(p)
        q = np.array(q)
        nq = np.array(nq)

        # compute cross product of p and nq in R3 which is a vector perpendicular to both p and nq.
        cross = np.cross(p, nq)
        # concatenate cross product with normal to create a vector in R6.
        ai = np.concatenate((cross, nq))
        # compute outer product to generate 6x6 matrix A.
        ai_ait = np.outer(ai, ai)
        A += ai_ait

        # create a vector of 6-D.
        ci = np.dot((p - q), nq)
        ci_ai = ci * ai
        b += ci_ai

    # solve system that minimizes r, t: A (r t) + b = 0
    rt_vec = solve(A, -b)

    r1, r2, r3 = rt_vec[0], rt_vec[1], rt_vec[2]
    t_opt = rt_vec[3:]

    # compute approximation of rotation matrix R.
    R = np.eye(3)
    R[0, 1] = -r3  # first row, second column.
    R[0, 2] = r2
    R[1, 0] = r3
    R[1, 2] = -r1
    R[2, 0] = -r2
    R[2, 1] = r1

    # perform singular value decomposition.
    U, _, Vt = svd(R, full_matrices=False)
    D = np.eye(3)
    D[2, 2] = det((U @ Vt))

    # compute optimal rotation matrix.
    r_opt = U @ D @ Vt

    return r_opt, t_opt
