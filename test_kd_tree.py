import time
import unittest
import random

import matplotlib.pyplot as plt
import numpy as np
from kd_tree import *


def distance(a, b):
    return sum((x - b[i]) ** 2 for i, x in enumerate(a))


def rand_point(dim):
    return [round(random.uniform(-1, 1), 3) for d in range(dim)]


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