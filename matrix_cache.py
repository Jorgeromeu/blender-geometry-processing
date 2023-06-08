from meshutil import *

MATRIX_CACHE = {}

def get_matrices(obj, bm: BMesh):
    if MATRIX_CACHE.get(obj) is None:
        print('Recomputing matrices')
        recompute_matrices(obj, bm)

    return MATRIX_CACHE[obj]

def recompute_matrices(obj, bm: BMesh):
    gradient, cotangent, gtmv = compute_deformation_matrices(bm)
    MATRIX_CACHE[obj] = (gradient, sp.linalg.splu(cotangent), gtmv)
