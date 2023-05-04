import bmesh

def neighbors(v: bmesh.types.BMVert) -> list[bmesh.types.BMVert]:
    ns = []
    for e in v.link_edges:

        neighbor = None
        if v == e.verts[0]:
            neighbor = e.verts[1]
        else:
            neighbor = e.verts[0]
        ns.append(neighbor)

    return ns

def is_boundary_edge(e: bmesh.types.BMEdge) -> bool:
    # edge is a boundary loop when it only has one connected face
    # 0 is degenerate,
    return len(e.link_faces) == 1
