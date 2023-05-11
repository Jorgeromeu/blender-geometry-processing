from bmesh.types import BMesh
from kd_tree import KDTree
import numpy as np

import bpyutil


def basic_registration(P: BMesh, Q: BMesh, no_samples: int):
    ps = np.random.choice(P.verts, no_samples)
    bpyutil.clear_editmode_selection(P)
    for p in ps:
        p.select = True

    tree = KDTree(Q.verts)

    bpyutil.switch_select_mode('VERT')
    bpyutil.update_viewports()