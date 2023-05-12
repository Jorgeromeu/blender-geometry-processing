import random

from mathutils import Vector

from bpyutil import *
from kd_tree import KDTree
from numpy.linalg import solve, svd, det


def icp(obj_P, obj_Q, max_iterations=100, eps=0.001, sample_rate=0.5, k=1, point_to_plane=False) -> (bool, int):
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

    qs_kdtree = KDTree(qs, lambda p1, p2: (p1[0] - p2[0]).length, lambda p, ax: p[0][ax])

    for _ in range(max_iterations):
        num_iterations_so_far += 1

        # get world space vertices of object P.
        ps = [obj_P.matrix_world @ p.co for p in obj_P.data.vertices]

        # sample n random points in mesh P
        n_samples = int(sample_rate * len(ps))
        ps_samples = random.sample(ps, n_samples)

        # for each sampled point, get the closest point in q and its distance
        point_pairs = []
        for p in ps_samples:
            (q, nq), dist = qs_kdtree.get_nearest_neighbor((p, None))
            point_pairs.append((p, q, nq, dist))

        # compute median distance, for filtering outliers
        sorted_point_pairs = sorted(point_pairs, key=lambda t: t[3])
        median_distance = sorted_point_pairs[n_samples // 2][3]

        # filter outlier point-pairs that don't satisfy the k*median condition
        point_pairs = [(p, q, nq) for (p, q, nq, dist) in point_pairs if dist <= k * median_distance]

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
    for pi, qi, _ in point_pairs:
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


def opt_rigid_transformation_point_to_plane(point_pairs: list[(Vector, Vector, Vector)]):
    A = np.zeros((6, 6))
    b = np.zeros((6,))

    for p, q, nq in point_pairs:
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
        ci_ai = ci*ai
        b += ci_ai

    # solve system that minimizes r, t: A (r t) + b = 0
    rt_vec = solve(A, -b)

    r1, r2, r3 = rt_vec[0], rt_vec[1], rt_vec[2]
    t_opt = rt_vec[3:]

    # compute approximation of rotation matrix R.
    R = np.eye(3)
    R[0, 1] = -r3       # first row, second column.
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
