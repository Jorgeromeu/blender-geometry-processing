import random

from mathutils import Vector

from bpyutil import *
from kd_tree import KDTree

def icp(obj_P, obj_Q, max_iterations=100, eps=0.001, sample_rate=0.5, k=1) -> (bool, int):
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

    converged = False
    num_iterations_so_far = 0

    # kdtree of vertices of object Q
    qs = [obj_Q.matrix_world @ q.co for q in obj_Q.data.vertices]
    qs_kdtree = KDTree(qs, lambda p1, p2: (p1 - p2).length)

    for i in range(max_iterations):
        num_iterations_so_far += 1

        # get worldspace vertices of object P
        ps = [obj_P.matrix_world @ q.co for q in obj_P.data.vertices]

        # compute optimal rigid transformation from ps to qs
        r_opt, t_opt = optimal_rigid_transformation(ps, qs_kdtree, sample_rate, k)

        # check if converged, if so stop
        trans_norm = np.linalg.norm(t_opt)
        if trans_norm <= eps and np.allclose(r_opt, np.eye(3), atol=eps):
            converged = True
            break

        # transform
        rigid_transform(t_opt, r_opt, obj_P)

    return converged, num_iterations_so_far

def centroid(ps: list[Vector]):
    p_sum = Vector((0, 0, 0))
    for p in ps:
        p_sum += p

    return p_sum / len(ps)

def optimal_rigid_transformation(ps: list[Vector],
                                 qs_kdtree: KDTree,
                                 sample_rate: float,
                                 k: float) -> (np.ndarray, np.ndarray):
    """
    Compute the optimal rigid transformation from vertices ps to vertices (in kdtree) qs
    :param ps: vertices of mesh P, to transform to Q
    :param qs_kdtree: vertices of mesh Q, stored in quadtree
    :param sample_rate: ratio of vertices in P to sample, between 0 and 1
    :param k: cutoff for discarding pairs that are too far away

    :return: rotation matrix, and translation vector corresponding to optimal rigid transformation
    """

    # sample n_samples random points in mesh P
    n_samples = int(sample_rate * len(ps))
    ps_samples = random.sample(ps, n_samples)

    # for each sampled point, get the closest point in q and its distance
    point_pairs = []
    for p in ps_samples:
        q, dist = qs_kdtree.get_nearest_neighbor(p)
        point_pairs.append((p, q, dist))

    # compute median distance
    point_pairs = sorted(point_pairs, key=lambda t: t[2])
    median_distance = point_pairs[len(point_pairs) // 2][2]

    # filter out triples that don't satisfy the k*median condition
    filtered_point_pairs = [t for t in point_pairs if t[2] <= k * median_distance]

    # compute centroids
    centroid_p = np.array(centroid([t[0] for t in filtered_point_pairs]))
    centroid_q = np.array(centroid([t[1] for t in filtered_point_pairs]))

    # compute covariance matrix
    covariance_matrix = np.zeros((3, 3))
    for pi, qi, _ in filtered_point_pairs:
        covariance_matrix += np.outer(np.array(pi) - centroid_p, np.array(qi) - centroid_q)
    covariance_matrix /= len(filtered_point_pairs)

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
