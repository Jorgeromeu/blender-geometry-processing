from typing import Generic, TypeVar

from mathutils import Vector
from numpy import inf

# P can be any point representation, which can be indexed with index_fun, and
# distance can be computed with provided dist_fun.
P = TypeVar('P')

class KDTree(Generic[P]):

    def __init__(self, points: list[P], dist_fun, index_fun, dim=3):

        def build(points, depth):
            if len(points) == 0:
                return None

            if len(points) == 1:
                return [None, None, points[0]]

            # cycle axis with depth
            _axis = depth % dim

            # sort values in ascending order for corresponding axis.
            points.sort(key=lambda x: self.index_fun(x, _axis))
            median = len(points) // 2
            return [build(points[:median], depth + 1), build(points[median + 1:], depth + 1), points[median]]

        self.dim = dim
        self.dist_fun = dist_fun
        self.index_fun = index_fun
        self._tree = build(points, depth=0)

    def _nearest_neighbour(self, node, point, closest_point, closest_dist, depth):
        if node is None:
            return closest_point, closest_dist

        left, right, cur = node[0], node[1], node[2]
        dist = self.dist_fun(point, cur)

        if dist < closest_dist:
            closest_dist = dist
            closest_point = cur

        # decide which side to go to.
        _axis = depth % self.dim
        if self.index_fun(point, _axis) < self.index_fun(cur, _axis):
            good_side = left
            bad_side = right
        else:
            good_side = right
            bad_side = left

        closest_point, closest_dist = self._nearest_neighbour(good_side, point, closest_point, closest_dist, depth + 1)

        if abs(self.index_fun(cur, _axis) - self.index_fun(point, _axis)) ** 2 < closest_dist:
            closest_point, closest_dist = self._nearest_neighbour(bad_side, point, closest_point, closest_dist, depth + 1)

        return closest_point, closest_dist

    def get_nearest_neighbor(self, point: P) -> (P, float):
        closest_point, closest_distance = self._nearest_neighbour(node=self._tree, point=point,
                                                                  closest_point=None, closest_dist=inf,
                                                                  depth=0)
        return closest_point, closest_distance
