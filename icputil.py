import random
from mathutils import Vector
from bpyutil import *
from kd_tree import KDTree


def icp(obj_P, obj_Q, max_iterations=100, eps=0.001, sample_rate=0.5, k=2.5, point_to_plane=False,
        sampling_strategy="RANDOM_POINT") -> (bool, int):
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

    # kdtree of worldspace verts of object Q, for optimizing nearest neighbor queries
    qs = [obj_Q.matrix_world @ q.co for q in obj_Q.data.vertices]

    qs_kdtree = KDTree(qs, lambda p1, p2: (p1 - p2).length, lambda p, ax: p[ax])

    for _ in range(max_iterations):
        num_iterations_so_far += 1

        # # get worldspace vertices of object P
        # ps = [obj_P.matrix_world @ q.co for q in obj_P.data.vertices]
        #
        # # sample n random points in mesh P
        # n_samples = int(sample_rate * len(ps))
        # ps_samples = random.sample(ps, n_samples)
        ps_samples = sample_points(obj_P, sample_rate, sampling_strategy)
        n_samples = len(ps_samples)

        # for each sampled point, get the closest point in q and its distance
        point_pairs = []
        for p in ps_samples:
            q, dist = qs_kdtree.get_nearest_neighbor(p)
            point_pairs.append((p, q, dist))

        # compute median distance, for filtering outliers
        sorted_point_pairs = sorted(point_pairs, key=lambda t: t[2])
        median_distance = sorted_point_pairs[n_samples // 2][2]

        # filter outlier point-pairs that don't satisfy the k*median condition
        point_pairs = [(p, q) for (p, q, dist) in point_pairs if dist <= k * median_distance]

        # compute optimal rigid transformation
        if point_to_plane:
            r_opt, t_opt = opt_rigid_transformation_point_to_plane()
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
    for pi, qi in point_pairs:
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
    if (sampling_strategy == "RANDOM_POINT"):
        # Get world space vertices of object P
        ps = [obj.matrix_world @ p.co for p in obj.data.vertices]
        # sample n random points in mesh P
        n_samples = int(sample_rate * len(ps))
        ps_samples = random.sample(ps, n_samples)
        return ps_samples
    elif (sampling_strategy == "NORMAL"):
        # Get world space vertices and the normals of object P
        ps_normals = [(obj.matrix_world @ p.co, p.normal.copy()) for p in obj.data.vertices]
        # Create dictionary of normals so we can sample them uniformly
        normal_dictionary = dict()
        for point, normal in ps_normals:
            key = (normal[0], normal[1], normal[2])
            if key not in normal_dictionary.keys():
                normal_dictionary[key] = []
            normal_dictionary[key].append(point)
        n_samples = int(sample_rate * len(normal_dictionary.keys()))
        normal_samples = random.sample(normal_dictionary.keys(), n_samples)
        ps_samples = [random.choice(normal_dictionary[sample]) for sample in normal_samples]
        return ps_samples
    else:
        raise RuntimeError("Invalid ICP sampling strategy")


def opt_rigid_transformation_point_to_plane(point_pairs: list[(Vector, Vector, Vector)]):
    pass
