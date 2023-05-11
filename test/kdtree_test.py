import random

import numpy as np
from mathutils import Vector
from numpy import inf

# BEGIN_COPIED_CODE

def distance(p1: Vector, p2: Vector):
    return (p1 - p2).length

def median(num: int):
    return num >> 1

class KDTree:

    def __init__(self, points: list[Vector], k=3):

        def build(points, depth):
            if len(points) == 0:
                return None

            if len(points) == 1:
                return [None, None, points[0]]

            _axis = depth % k
            # sort values in ascending order for corresponding axis.
            points.sort(key=lambda x: x[_axis])
            m = median(len(points))
            return [build(points[:m], depth + 1), build(points[m + 1:], depth + 1), points[m]]

        def nearest_neighbour(node, point, closest_point, closest_dist, depth):
            if node is None:
                return closest_point, closest_dist

            left, right, cur = node[0], node[1], node[2]
            dist = distance(point, cur)

            if dist < closest_dist:
                closest_dist = dist
                closest_point = cur

            # decide which side to go to.
            _axis = depth % k
            if point[_axis] < cur[_axis]:
                good_side = left
                bad_side = right
            else:
                good_side = right
                bad_side = left

            closest_point, closest_dist = nearest_neighbour(good_side, point, closest_point, closest_dist, depth + 1)

            if abs(cur[_axis] - point[_axis]) ** 2 < closest_dist:
                closest_point, closest_dist = nearest_neighbour(bad_side, point, closest_point, closest_dist, depth + 1)

            return closest_point, closest_dist

        self._tree = build(points, depth=0)
        self._get_nn = lambda p: nearest_neighbour(node=self._tree, point=p, closest_point=None, closest_dist=inf,
                                                   depth=0)

    def get_nearest_neighbor(self, point):
        closest_point, _ = self._get_nn(point)
        return closest_point

# END_COPIED_CODE

def rand_point(dim):
    x, y, z = [random.uniform(-1, 1) for d in range(dim)]
    return Vector((x, y, z))

def get_nearest_naive(points, point):
    nearest = min(points, key=lambda p: distance(p, point))
    return nearest

def test_all():
    dim = 3
    points = [rand_point(dim) for x in range(10000)]
    query_points = [rand_point(dim) for x in range(100)]

    kd_tree_results, naive_results = [], []
    kd_tree = KDTree(points)

    for q in query_points:
        kd_tree_results.append(kd_tree.get_nearest_neighbor(q))
        naive_results.append(get_nearest_naive(points, q))

    assert np.allclose(kd_tree_results, naive_results)

if __name__ == '__main__':
    test_all()
