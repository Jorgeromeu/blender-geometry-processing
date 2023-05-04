import bmesh

def neighbors(v: bmesh.types.BMVert, only_boundaries=False) -> list[bmesh.types.BMVert]:
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

def is_boundary_edge(e: bmesh.types.BMEdge) -> bool:
    # edge is a boundary loop when it only has one adjacent face
    return len(e.link_faces) == 1

def compute_genus(bm: bmesh.types.BMesh, n_boundaries: int):
    n_verts = len(list(bm.verts))
    n_edges = len(list(bm.edges))
    n_faces = len(list(bm.faces))

    return 1 - (n_verts - n_edges + n_faces + n_boundaries) / 2

def compute_num_boundary_loops(bm: bmesh.types.BMesh):
    boundary_edges = {e for e in bm.edges if is_boundary_edge(e)}
    boundary_verts = set()

    for e in boundary_edges:
        s, t = e.verts
        if is_boundary_edge(e):
            boundary_verts.add(s)
            boundary_verts.add(t)

    unvisited = set(boundary_verts)

    n_loops = 0

    while unvisited:

        n_loops += 1

        # select a random unvisited edge
        v: bmesh.types.BMVert = next(iter(unvisited))

        # traverse
        queue = [v]
        unvisited.remove(v)
        while queue:
            v = queue.pop(0)

            for neighbor in neighbors(v, only_boundaries=True):
                if neighbor in unvisited:
                    queue.append(neighbor)
                    unvisited.remove(neighbor)

    return n_loops

def compute_mesh_volume(bm: bmesh.types.BMesh):
    total_volume = 0
    for face in bm.faces:
        v1, v2, v3 = [v.co for v in face.verts]

        # compute signed volume of each tetrahedron
        tetra_volume = v1.cross(v2).dot(v3) / 6
        total_volume += tetra_volume

    return total_volume

def compute_connected_components(bm: bmesh.types.BMesh, vertex_set=None):
    # keep track of unvisited vertices
    if vertex_set:
        unvisited = set(vertex_set)
    else:
        unvisited = set(bm.verts)

    n_components = 0

    while unvisited:

        n_components += 1

        # select a random unvisited vertex
        v: bmesh.types.BMVert = next(iter(unvisited))

        # traverse
        queue = [v]
        unvisited.remove(v)
        while queue:
            v = queue.pop(0)

            # print(v.index)

            for neighbor in neighbors(v):
                if neighbor in unvisited:
                    queue.append(neighbor)
                    unvisited.remove(neighbor)

    return n_components
