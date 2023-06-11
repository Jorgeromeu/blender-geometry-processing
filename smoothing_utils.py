import numpy as np
from bmesh.types import BMesh
from meshutil import mesh_laplacian, to_vxvyvz


def laplace_smoothing(bm: BMesh, n_iters: int, step_size: float) -> (np.ndarray, np.ndarray, np.ndarray):
    laplacian = mesh_laplacian(bm)
    vx, vy, vz = to_vxvyvz(bm, dims=[0, 1, 2])

    for _ in range(n_iters):
        delta_x = laplacian @ vx
        delta_y = laplacian @ vy
        delta_z = laplacian @ vz

        vx -= step_size * delta_x
        vy -= step_size * delta_y
        vz -= step_size * delta_z

    return (vx, vy, vz)
