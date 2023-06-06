import numpy as np
import scipy.sparse as sp
from bmesh.types import BMVert, BMEdge, BMFace
from mathutils import Vector

from .bpyutil import *


def neighbors(v: BMVert, only_boundaries=False) -> list[BMVert]:
    neighbors = []
    for e in v.link_edges:

        if only_boundaries and not is_boundary_edge(e):
            continue

        neighbor = None
        if v == e.verts[0]:
            neighbor = e.verts[1]
        else:
            neighbor = e.verts[0]
        neighbors.append(neighbor)

    return neighbors


def centroid(ps: list[Vector]):
    p_sum = Vector((0, 0, 0))
    for p in ps:
        p_sum += p

    return p_sum / len(ps)


def is_boundary_edge(e: BMEdge) -> bool:
    # edge is a boundary loop when it only has one adjacent face
    return len(e.link_faces) == 1


def compute_genus(bm: BMesh, n_boundaries: int) -> float:
    n_verts = len(list(bm.verts))
    n_edges = len(list(bm.edges))
    n_faces = len(list(bm.faces))

    return 1 - (n_verts - n_edges + n_faces + n_boundaries) / 2


def compute_boundary_loops(bm: BMesh, select_edges=False) -> int:
    # find all edges that are boundaries
    boundary_edges = {e for e in bm.edges if is_boundary_edge(e)}

    if select_edges:
        clear_editmode_selection(bm)
        for e in boundary_edges:
            e.select = True
        switch_select_mode('EDGE')
        update_viewports()

    # get all vertices that lie on a boundary
    boundary_verts = set()
    for e in boundary_edges:
        if is_boundary_edge(e):
            s, t = e.verts
            boundary_verts.add(s)
            boundary_verts.add(t)

    n_loops = 0

    # keep track of unvisited boundary verts
    unvisited = set(boundary_verts)

    while unvisited:

        n_loops += 1

        # select a random unvisited edge
        v: BMVert = next(iter(unvisited))

        # traverse
        queue = [v]
        unvisited.remove(v)
        while queue:
            v = queue.pop(0)

            print('visited', v)

            for neighbor in neighbors(v, only_boundaries=True):
                if neighbor in unvisited:
                    queue.append(neighbor)
                    unvisited.remove(neighbor)

    return n_loops


def compute_mesh_volume(bm: BMesh) -> float:
    total_volume = 0
    for face in bm.faces:
        v1, v2, v3 = [v.co for v in face.verts]

        # compute signed volume of each tetrahedron
        tetra_volume = v1.cross(v2).dot(v3) / 6
        total_volume += tetra_volume

    return total_volume


def compute_connected_components(bm: BMesh) -> int:
    n_components = 0

    # keep track of unvisited vertices
    unvisited = set(bm.verts)

    while unvisited:

        n_components += 1

        # select a random unvisited vertex
        v: BMVert = next(iter(unvisited))

        # traverse, from v
        queue = [v]
        unvisited.remove(v)
        while queue:
            v = queue.pop(0)

            print('visited', v.index)

            for neighbor in neighbors(v):
                if neighbor in unvisited:
                    queue.append(neighbor)
                    unvisited.remove(neighbor)

    return n_components


def compute_laplace_coords(bm: BMesh) -> dict[int, Vector]:
    # precompute laplace coordinates of mesh
    laplace_coords = {}

    for v in bm.verts:
        v: BMVert
        v_neighbors = [n.co for n in neighbors(v)]

        laplace_coord = Vector()
        for n in v_neighbors:
            laplace_coord += v.co - n
        laplace_coord /= len(v_neighbors)

        laplace_coords[v.index] = laplace_coord

    return laplace_coords


def mesh_laplacian(mesh: BMesh) -> np.ndarray:
    n = len(mesh.verts)
    D = sp.lil_array((n, n))
    A = sp.lil_array((n, n))

    for i, v_i in enumerate(mesh.verts):

        vi_neighbors = neighbors(v_i)

        D[i, i] = len(vi_neighbors)

        for neighbor in vi_neighbors:
            A[i, neighbor.index] = 1

    L = sp.eye(n) - sp.linalg.inv(D.tocsc()) @ A
    return L.tocsc()


def triangle_area(triangle: BMFace) -> float:
    """Calculates the mass matrix for a single triangle:
    """
    v1 = triangle.verts[0].co
    v2 = triangle.verts[1].co
    v3 = triangle.verts[2].co
    AB = v2 - v1
    AC = v3 - v1
    cosTheta = AB.dot(AC) / (AB.length * AC.length)
    sinTheta = np.sqrt(1 - cosTheta ** 2)
    area = 0.5 * AB.length * AC.length * sinTheta
    # return np.eye(3) * area
    return area


def mesh_mash(mesh: BMesh) -> np.ndarray:
    """
    Returns the mash matrix for a given mesh.
    M = [ A_{T1} 0 ...        0   ]
        [   0    A_{T2} ...   0   ]
                    .
                    .
                    .
        [   0      0   ... A_{Tm} ],
    with $M \in \mathbb{R}^{3m\times3m}$, where m is the number of triangles.
    See `triangle_mass` for a definiton of A_{T1}.
    """
    mass = np.eye(3 * len(mesh.faces))
    for face_index, face in enumerate(mesh.faces):
        ti_area = mass[(face_index * 3):(face_index * 3 + 3)]
        ti_area[np.where(ti_area == 1)] = triangle_area(face)
    return mass
