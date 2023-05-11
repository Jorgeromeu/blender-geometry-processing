import random
import time

import bmesh
from mathutils import Vector

from bpyutil import *

def get_nearest_naive(points, point):
    nearest = min(points, key=lambda p: (p - point).length)
    dist = (point - nearest).length
    return nearest, dist

from kd_tree import KDTree

def icp(obj_P, obj_Q, num_iterations=100, eps=0.001, sample_rate=0.5, k=1):

    qs = [obj_Q.matrix_world @ q.co for q in obj_P.data.vertices]

    # compute kdtree of Q
    qs_kdtree = KDTree(qs)

    for i in range(num_iterations):
        print(i)

        enter_editmode()
        P = bmesh.from_edit_mesh(obj_P.data)
        Q = bmesh.from_edit_mesh(obj_Q.data)

        p_points = [obj_P.matrix_world @ p.co for p in P.verts]
        q_points = [obj_Q.matrix_world @ q.co for q in Q.verts]
        r_opt, t_opt = icp_step(p_points, q_points, qs_kdtree, sample_rate, k)
        enter_objectmode()

        # check if converged
        trans_norm = np.linalg.norm(t_opt)

        print(i, trans_norm)

        if trans_norm <= eps and np.allclose(r_opt, np.eye(3), atol=eps):
            print('converged')
            break

        rigid_transform(t_opt, r_opt, obj_P)

def centroid(ps: list[Vector]):
    p_sum = Vector((0, 0, 0))
    for p in ps:
        p_sum += p

    return p_sum / len(ps)

def icp_step(ps: list[Vector],
             qs: list[Vector],
             qs_kdtree: KDTree,
             sample_rate: float,
             k: float) -> (np.ndarray, np.ndarray):

    # sample n random points in mesh P
    n_samples = int(sample_rate * len(ps))

    ps_samples = random.sample(ps, n_samples)

    triples = []
    for p in ps_samples:
        q, dist = qs_kdtree.get_nearest_neighbor(p)
        triples.append((p, q, dist))

    # sort triples based on distance
    triples = sorted(triples, key=lambda t: t[2])

    median_distance = triples[len(triples) // 2][2]

    # filter out triples that don't satisfy the k*median condition
    filtered_triples = [t for t in triples if t[2] <= k * median_distance]

    centroid_p = np.array(centroid([t[0] for t in filtered_triples]))
    centroid_q = np.array(centroid([t[1] for t in filtered_triples]))

    mat_M = np.zeros((3, 3))
    for pi, qi, _ in filtered_triples:
        mat_M += np.outer(np.array(pi) - centroid_p, np.array(qi) - centroid_q)
    mat_M /= len(filtered_triples)

    # singular value decomposition
    U, _, Vt, = np.linalg.svd(mat_M, full_matrices=False)
    V = Vt.transpose()
    Ut = U.transpose()

    m = np.eye(3)
    m[2, 2] = np.linalg.det((V @ Ut))
    r_opt = V @ m @ Ut
    t_opt = centroid_q - r_opt @ centroid_p

    # r_opt_mu = mathutils.Matrix(r_opt)
    # ex, ey, ez = r_opt_mu.to_euler("XYZ")
    # print('eulerangles', [np.degrees(r) for r in [ex, ey, ez]])

    return r_opt, t_opt
