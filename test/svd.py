import numpy as np

M = np.random.rand(3, 3)

U, D, Vt = np.linalg.svd(M)

print(U @ U.transpose())
print(Vt @ Vt.transpose())

# print(M)
# print(U @ np.diag(D) @ Vt)

# U, _, Vt = np.linalg.svd(M)
#
# V = Vt.transpose()
#
# m = np.eye(3)
# m[2, 2] = np.linalg.det(V @ U.transpose())
#
# R_opt = V @ m @ U.transpose()
