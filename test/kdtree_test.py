import random
import unittest

from kd_tree import KDTree

import numpy as np

def distance(p1: np.ndarray, p2: np.ndarray):
    return np.linalg.norm(p1[0] - p2[0])

def rand_point(dim):
    x, y, z = [random.uniform(-1, 1) for d in range(dim)]
    return np.array([x, y, z])

def get_nearest_naive(points, point):
    nearest = min(points, key=lambda p: distance(p, point))
    return nearest

class TestKdTtree(unittest.TestCase):

    def test_all(self):
        dim = 3
        points = [(rand_point(dim), rand_point(dim)) for x in range(10000)]
        query_points = [rand_point(dim) for x in range(100)]

        kd_tree = KDTree(points, distance, lambda p, ax: p[0][ax])

        for q in query_points:

            (closest_kd, n), d = kd_tree.get_nearest_neighbor((q, None))
            (closest_naive, _) = get_nearest_naive(points, (q, None))

            self.assertTrue(np.allclose(closest_kd, closest_naive))


