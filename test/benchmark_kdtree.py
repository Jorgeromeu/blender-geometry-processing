from matplotlib import pyplot as plt

plt.switch_backend('TkAgg')

from kd_tree import KDTree
from test_kd_tree import rand_point, get_nearest_naive
from timer import Timer

def benchmark_kdtree():
    t = Timer()
    t.logging_enabled = True

    # generate random points
    dim = 3
    points = [rand_point(dim) for x in range(10000)]

    t.start()
    kd_tree = KDTree(points)
    t.stop('tree construction')

    n_query_points = [1, 5, 10, 20, 50, 100, 200, 400, 800, 1000]

    times_naive = []
    times_kdtree = []
    for num_query in n_query_points:
        query_points = [rand_point(dim) for x in range(num_query)]

        t.start()
        for q in query_points:
            get_nearest_naive(points, q)
        times_naive.append(t.stop(f'naive q={num_query}'))

        t.start()
        for q in query_points:
            kd_tree.get_nearest_neighbor(q)
        times_kdtree.append(t.stop(f'kdtree q={num_query}'))

    plt.plot(n_query_points, times_naive, marker='.', label='brute force')
    plt.plot(n_query_points, times_kdtree, marker='.', label='KDtree')
    plt.legend()
    plt.xlabel('num query points')
    plt.ylabel('time (seconds)')
    plt.yscale('log')
    plt.show()

if __name__ == '__main__':
    benchmark_kdtree()
