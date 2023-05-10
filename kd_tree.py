import time
from math import floor, inf

from matplotlib import pyplot as plt


def median(num):
    return num >> 1


def distance(a, b):
    return sum((x - b[i]) ** 2 for i, x in enumerate(a))


class KDTree:

    def __init__(self, points, k=3):

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
        self._get_nn = lambda p: nearest_neighbour(node=self._tree, point=p, closest_point=None, closest_dist=inf, depth=0)

    def get_nearest_neighbor(self, point):
        closest_point, _ = self._get_nn(point)
        return closest_point



def benchmark_kdtree():
    from test_kd_tree import rand_point, get_nearest_naive


    dim = 3
    points = [rand_point(dim) for x in range(10000)]

    kd_tree = KDTree(points)

    times_naive = []
    times_kdtree = []

    n_query_points = [10, 100, 1000]

    for num_query in n_query_points:
        query_points = [rand_point(dim) for x in range(num_query)]

        t_start = time.perf_counter()
        for q in query_points:
            get_nearest_naive(points, q)
        t_stop = time.perf_counter()
        duration_naive = t_stop - t_start
        times_naive.append(duration_naive)

        t_start = time.perf_counter()
        for q in query_points:
            kd_tree.get_nearest_neighbor(q)
        t_stop = time.perf_counter()
        duration_kdtree = t_stop - t_start
        times_kdtree.append(duration_kdtree)

    plt.plot(x=num_query, y=times_naive)
    plt.plot(x=num_query, y=times_kdtree)
    plt.show()

if __name__ == '__main__':
    benchmark_kdtree()
