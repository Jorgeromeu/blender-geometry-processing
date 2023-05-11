import random

import bpy
import mathutils
import numpy as np
from mathutils import Vector

def get_nearest_naive(points, point):
    nearest = min(points, key=lambda p: (p - point).length)
    dist = (point - nearest).length
    return nearest, dist

from kd_tree import KDTree

def centroid(ps: list[Vector]):
    p_sum = Vector((0, 0, 0))
    for p in ps:
        p_sum += p

    return p_sum / len(ps)

def basic_icp(ps: list[Vector], qs: list[Vector], sample_rate: float, k: float):
    # create kd tree from verts in mesh Q
    tree = KDTree(qs)

    # sample n random points in mesh P
    n_samples = int(sample_rate * len(ps))
    print('n_samples', n_samples)

    ps_samples = random.sample(ps, n_samples)

    triples = []
    for p in ps_samples:
        q, dist = tree.get_nearest_neighbor(p)
        # q, dist = get_nearest_naive(qs, p)
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
        m1 = (np.array(pi) - centroid_p)
        m2 = (np.array(qi) - centroid_q)
        diff = np.outer(m1, m2)
        mat_M += diff
    mat_M /= len(filtered_triples)

    # singular value decomposition
    U, _, Vt, = np.linalg.svd(mat_M, full_matrices=False)
    V = Vt.transpose()
    Ut = U.transpose()

    m = np.eye(3)
    m[2, 2] = np.linalg.det((V @ Ut))
    r_opt = V @ m @ Ut
    # r_opt = U @ m @ Vt

    r_opt_mu = mathutils.Matrix(r_opt)
    ex, ey, ez = r_opt_mu.to_euler("XYZ")

    t_opt = centroid_q - r_opt @ centroid_p

    print('eulerangles', [np.degrees(r) for r in [ex, ey, ez]])
    print(t_opt)
