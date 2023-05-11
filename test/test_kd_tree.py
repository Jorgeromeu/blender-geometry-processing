import os
import unittest
import random

import numpy as np
from mathutils import Vector

from kd_tree import KDTree, distance


def rand_point(dim):
    x, y, z = [random.uniform(-1, 1) for d in range(dim)]
    v = Vector((x, y, z))
    print(v.x)
    return v


def get_nearest_naive(points, point):
    nearest = min(points, key=lambda p: distance(p, point))
    return nearest


class KDTreeUnitTest(unittest.TestCase):

    def test_all(self):
        dim = 3
        points = [rand_point(dim) for x in range(10000)]
        query_points = [rand_point(dim) for x in range(100)]

        kd_tree_results, naive_results = [], []
        kd_tree = KDTree(points)

        for q in query_points:
            kd_tree_results.append(kd_tree.get_nearest_neighbor(q))
            naive_results.append(get_nearest_naive(points, q))

        self.assertTrue(np.allclose(kd_tree_results, naive_results), "Mismatch in closest point")

if __name__ == '__main__':
    unittest.main()