import random
import time

from mathutils import Vector
from numpy.linalg import solve, svd, det

from bpyutil import *
from kd_tree import KDTree

def rmse(ob1, ob2) -> float:
    verts_1 = np.array([np.array(ob1.matrix_world @ v.co) for v in ob1.data.vertices])
    verts_2 = np.array([np.array(ob2.matrix_world @ v.co) for v in ob2.data.vertices])

    # assume that both objects are the same one
    assert len(verts_1) == len(verts_2)

    return np.sqrt(np.mean(np.linalg.norm(verts_1 - verts_2, axis=1) ** 2))

class ICP:

    def __init__(self, max_iterations=100, eps=0.001, max_points=1000, k=2.5, nu=0.1, normal_dissimilarity_thres=0.5,
                 point_to_plane=False, sampling_strategy="RANDOM_POINT", distance_strategy="EUCLIDEAN",
                 rejection_criterion="K_MEDIAN", weighting_strategy="NONE", evaluation_object=None,
                 evaluation_metric=rmse):

        self.max_iterations = max_iterations
        self.eps = eps
        self.max_points = max_points
        self.k = k
        self.nu = None
        self.min_nu = nu
        self.normal_dissimilarity_thres = normal_dissimilarity_thres
        self.point_to_plane = point_to_plane
        self.sampling_strategy = sampling_strategy
        self.distance_strategy = distance_strategy
        self.rejection_criterion = rejection_criterion
        self.weighting_strategy = weighting_strategy
        self.max_distance = -1

        # used for evaluations
        self.evaluation_object = evaluation_object
        self.evaluation_metric = evaluation_metric
        self.errors = []


    def icp(self, obj_P, obj_Q) -> (bool, int):
        """
        Perform iterative closest point on two objects
        :param obj_P: First object, to be transformed to second one
        :param obj_Q: Second object
        :return: if algorithm converged, and in how many iterations
        """

        # keep track of errors at each iteration, and time
        self.errors = []
        t_start = time.perf_counter()

        # keep track of convergence
        converged = False
        num_iterations_so_far = 0

        # kd-tree of worldspace verts and normals of object Q, for optimizing nearest neighbor queries
        q_world = obj_Q.matrix_world
        qs = [(q_world @ q.co, q_world @ q.normal) for q in obj_Q.data.vertices]

        distance_lambda = lambda p1, p2: (p1[0] - p2[0]).length
        if self.distance_strategy == "NORMAL_WEIGHTED":
            # Use cosine similarity to weigh the distance
            distance_lambda = lambda p1, p2: np.dot(p1, p2) * (p1[0] - p2[0]).length

        qs_kdtree = KDTree(qs, distance_lambda, lambda point, ax: point[0][ax])

        # Initial values for the rotation and translation of the previous iteration
        # these are updated during iterations to be used in case the weighting strategy needs it
        prev_R = np.eye(3)
        prev_t = np.zeros((3,))

        # Main ICP iteration loop
        for _ in range(self.max_iterations):
            num_iterations_so_far += 1

            ps_samples = self.sample_points(obj_P)
            n_samples = len(ps_samples)

            # for each sampled point, get the closest point in q and its distance
            point_pairs = []
            for p, p_normal in ps_samples:
                (q, nq), dist = qs_kdtree.get_nearest_neighbor((p, None))
                self.max_distance = max(self.max_distance, dist)
                point_pairs.append((p, q, nq, p_normal, dist))

            if self.weighting_strategy == "WELSCH" and self.nu is None:
                # Set initial nu value for Welsch function weighting
                sorted_point_pairs = sorted(point_pairs, key=lambda t: t[4])
                self.nu = 3 * sorted_point_pairs[n_samples // 2][4]

            if self.rejection_criterion == "K_MEDIAN":
                # compute median distance, for filtering outliers
                sorted_point_pairs = sorted(point_pairs, key=lambda t: t[4])
                median_distance = sorted_point_pairs[n_samples // 2][4]

                # filter outlier point-pairs that don't satisfy the k*median condition
                point_pairs = [(p, q, nq, p_normal, dist) for (p, q, nq, p_normal, dist) in point_pairs if
                               dist <= self.k * median_distance]
            elif self.rejection_criterion == "DISSIMILAR_NORMALS":
                point_pairs = [(p, q, nq, p_normal, dist) for (p, q, nq, p_normal, dist) in point_pairs if
                               (1 - nq.dot(p_normal)) <= self.normal_dissimilarity_thres]

            # compute optimal rigid transformation.
            if self.point_to_plane:
                r_opt, t_opt = self.opt_rigid_transformation_point_to_plane(point_pairs)
            else:
                r_opt, t_opt = self.opt_rigid_transformation_point_to_point(point_pairs,
                                                                            prev_R=prev_R, prev_t=prev_t)

            # check if converged, if so stop
            trans_norm = np.linalg.norm(t_opt)
            if trans_norm <= self.eps and np.allclose(r_opt, np.eye(3), atol=self.eps):
                converged = True
                break

            # Update the previous rotation and translation
            prev_R = r_opt
            prev_t = t_opt

            # transform object optimal transformation
            rigid_transform(t_opt, r_opt, obj_P)

            # record error after iteration
            if self.evaluation_object is not None:
                err = self.evaluation_metric(obj_P, self.evaluation_object)
                t_iter = time.perf_counter()
                self.errors.append((err, t_iter - t_start))

        return converged, num_iterations_so_far

    def _centroid(self, ps: list[Vector]):
        p_sum = Vector((0, 0, 0))
        for p in ps:
            p_sum += p

        return p_sum / len(ps)

    def opt_rigid_transformation_point_to_point(self, point_pairs: list[(Vector, Vector)], prev_R=None, prev_t=None):
        """
        Compute the optimal rigid transformation between pairs of points

        :param point_pairs: a list of pairs (p_i, q_i)
        :param prev_R: the previous rotation matrix. Pass it if it is needed by the weighting strategy
        :param prev_t: the previous translation vector. Pass it if is need by the weighting strategy.
        :return: translation vector and rotation matrix for optimal rigid transformation from
        points p_i to q_i
        """

        # compute centroids
        centroid_p = np.array(self._centroid([t[0] for t in point_pairs]))
        centroid_q = np.array(self._centroid([t[1] for t in point_pairs]))

        # compute covariance matrix
        covariance_matrix = np.zeros((3, 3))
        weights_sum = 0.0
        for pi, qi, q_normal, p_normal, dist in point_pairs:
            wi = 1.0
            if self.weighting_strategy == "NORMAL_SIMILARITY":
                wi = q_normal.dot(p_normal)
            elif self.weighting_strategy == "DISTANCE":
                wi = 1.0 - (dist / self.max_distance)  # Based on Godin, 1994
            elif self.weighting_strategy == "WELSCH":
                welsch_vector = np.matmul(prev_R, pi) + prev_t - qi
                welsch_norm = np.linalg.norm(welsch_vector)
                wi = np.exp(-welsch_norm / (2 * self.nu ** 2))
                self.nu = max(self.nu / 2, self.min_nu)
            weights_sum += wi
            covariance_matrix += wi * np.outer(np.array(pi) - centroid_p, np.array(qi) - centroid_q)

        covariance_matrix /= weights_sum

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

    def opt_rigid_transformation_point_to_plane(self, point_pairs: list[(Vector, Vector, Vector)]):
        A = np.zeros((6, 6))
        b = np.zeros((6,))

        for p, q, nq, _, _ in point_pairs:
            # convert vectors to numpy arrays.
            p = np.array(p)
            q = np.array(q)
            nq = np.array(nq)

            # compute cross product of p and nq in R3 which is a vector perpendicular to both p and nq.
            cross = np.cross(p, nq)
            # concatenate cross product with normal to create a vector in R6.
            ai = np.concatenate((cross, nq))
            # compute outer product to generate 6x6 matrix A.
            ai_ait = np.outer(ai, ai)
            A += ai_ait

            # create a vector of 6-D.
            ci = np.dot((p - q), nq)
            ci_ai = ci * ai
            b += ci_ai

        # solve system that minimizes r, t: A (r t) + b = 0
        rt_vec = solve(A, -b)

        r1, r2, r3 = rt_vec[0], rt_vec[1], rt_vec[2]
        t_opt = rt_vec[3:]

        # compute approximation of rotation matrix R.
        R = np.eye(3)
        R[0, 1] = -r3  # first row, second column.
        R[0, 2] = r2
        R[1, 0] = r3
        R[1, 2] = -r1
        R[2, 0] = -r2
        R[2, 1] = r1

        # perform singular value decomposition.
        U, _, Vt = svd(R, full_matrices=False)
        D = np.eye(3)
        D[2, 2] = det((U @ Vt))

        # compute optimal rotation matrix.
        r_opt = U @ D @ Vt

        return r_opt, t_opt

    def sample_points(self, obj) -> list[(np.ndarray, np.ndarray)]:
        """
        Returns a list of tuples (point, normal)
        """
        # Get world space vertices and the normals of object P
        ps = [(obj.matrix_world @ p.co, p.normal.copy()) for p in obj.data.vertices]
        n_samples = min(len(ps) - 1, self.max_points)

        if self.sampling_strategy == "RANDOM_POINT":
            # Sample n random points in mesh P
            ps_samples = random.sample(ps, n_samples)
            return ps_samples
        elif self.sampling_strategy == "NORMAL":
            # Create the normal "buckets" and sample from them
            normal_dictionary = self._construct_normal_space_buckets(ps)
            normal_samples = random.sample(normal_dictionary.keys(), n_samples)
            ps_samples = [(random.choice(normal_dictionary[sample]), sample) for sample in normal_samples]
            return ps_samples
        elif self.sampling_strategy == "STRATIFIED_NORMAL":
            normal_dictionary = self._construct_normal_space_buckets(ps)
            ps_samples = []
            # Sample once from each stratum until we have the amount of requested samples
            while len(ps_samples) < n_samples:
                for stratum in normal_dictionary.keys():
                    ps_samples.append((random.choice(normal_dictionary[stratum]), stratum))
            return ps_samples
        else:
            raise RuntimeError("Invalid point sampling strategy")

    def _construct_normal_space_buckets(self, ps_normals) -> dict:
        """
        Returns a dictionary of normal -> list[Vector].
        The normal is represented as a triple.
        """
        # Create dictionary of normals so we can sample them uniformly
        normal_dictionary = dict()
        for point, normal in ps_normals:
            key = (normal[0], normal[1], normal[2])
            if key not in normal_dictionary.keys():
                normal_dictionary[key] = []
            normal_dictionary[key].append(point)
        return normal_dictionary
