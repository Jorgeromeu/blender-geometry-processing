import numpy as np
import scipy.sparse as sp
from bmesh.types import BMesh

from meshutil import mesh_laplacian, to_vxvyvz

def iterative_laplace_smoothing(bm: BMesh, n_iters: int, step_size: float, laplacian=None) -> (np.ndarray, np.ndarray, np.ndarray):

    if laplacian is None:
        laplacian = mesh_laplacian(bm)

    vx, vy, vz = to_vxvyvz(bm, dims=[0, 1, 2])

    for _ in range(n_iters):
        delta_x = laplacian @ vx
        delta_y = laplacian @ vy
        delta_z = laplacian @ vz

        vx -= step_size * delta_x
        vy -= step_size * delta_y
        vz -= step_size * delta_z

    return vx, vy, vz

def implicit_laplace_smoothing(bm: BMesh, n_iters: int, step_size: float):

    for _ in range(n_iters):
        laplacian = mesh_laplacian(bm)
        vx, vy, vz = to_vxvyvz(bm, dims=[0, 1, 2])

        # solve linear system
        lhs = sp.eye(len(vx)) + step_size * laplacian

        lhs_factorized = sp.linalg.splu(lhs)

        vx = lhs_factorized.solve(vx)
        vy = lhs_factorized.solve(vy)
        vz = lhs_factorized.solve(vz)

        # set vertex coordinates
        for v_i, v in enumerate(bm.verts):
            v.co.x = vx[v_i]
            v.co.y = vy[v_i]
            v.co.z = vz[v_i]

    return vx, vy, vz
