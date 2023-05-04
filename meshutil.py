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
    # edge is a boundary loop when it only has one connected face
    # 0 is degenerate,
    return len(e.link_faces) == 1
