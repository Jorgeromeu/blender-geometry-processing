from bmesh.types import BMVert, BMEdge, BMesh

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
