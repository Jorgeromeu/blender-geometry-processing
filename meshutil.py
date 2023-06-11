import bmesh
import scipy.sparse as sp
from bmesh.types import BMFace, BMEdge, BMVert

from bpyutil import *


def mesh_from_object(object) -> BMesh:
    mesh = object.data
    bm = bmesh.new()
    bm.from_mesh(mesh)
    return bm


def triangulate_object(obj):
    """
    Triangulates an object.
    """
    me = obj.data

    # Get a BMesh representation
    bm = bmesh.new()
    bm.from_mesh(me)

    # Check if the mesh is already triangular
    bm.faces.ensure_lookup_table()  # ensures next lines index access works
    if len(bm.faces[0].verts) == 3:
        print("Mesh already triangulated")
        return

    bmesh.ops.triangulate(bm, faces=bm.faces[:])

    # Finish up, write the bmesh back to the mesh
    bm.to_mesh(me)
    bm.free()


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


def compute_mass_matrix(mesh: BMesh, return_sparse=True) -> np.ndarray:
    """
    Returns the mash matrix for a given mesh.
    M = [ A_{T1} 0 ...        0   ]
        [   0    A_{T2} ...   0   ]
                    .
                    .
                    .
        [   0      0   ... A_{Tm} ],
    with $M \in \mathbb{R}^{3m\times3m}$, where m is the number of triangles.
    See `triangle_mass` for a definition of A_{T1}.
    """

    mass = np.eye(3 * len(mesh.faces))
    for face_index, face in enumerate(mesh.faces):
        ti_area = mass[(face_index * 3):(face_index * 3 + 3)]
        ti_area[np.where(ti_area == 1)] = face.calc_area()

    if return_sparse:
        mass = sp.csr_matrix(mass)
    return mass


def compute_gradient_matrix(bm: BMesh, return_sparse=True) -> np.ndarray:
    """
    Computes gradient matrix of a mesh.
    If `return_sparse` is set to true, the method returns a SCS Sparse Scipy matrix.
    """

    V = len(bm.verts)
    F = len(bm.faces)

    global_gradient_matrix = np.zeros((3 * F, V))

    for face_idx, face in enumerate(bm.faces):
        face: BMFace = face
        normal: Vector = face.normal
        area = face.calc_area()
        constant = 1 / (2 * area)

        local_gradient_matrix = np.zeros((3, V))

        face_verts = list(face.verts)
        for v_ix, v in enumerate(face_verts):
            # Get subsequent vertices
            successor = face_verts[(v_ix + 1) % 3].co
            suc_successor = face_verts[(v_ix + 2) % 3].co
            opp_edge = suc_successor - successor

            grad = constant * normal.cross(opp_edge)
            grad = np.array(grad)
            local_gradient_matrix[:, v.index] = grad

        global_gradient_matrix[face_idx * 3:face_idx * 3 + 3, :] = local_gradient_matrix

    if return_sparse:
        global_gradient_matrix = sp.csr_matrix(global_gradient_matrix)
    return global_gradient_matrix


def compute_cotangent_matrix(bm: BMesh):
    """
    Computes cotangent matrix of a mesh.
    """
    gradient_matrix = compute_gradient_matrix(bm)
    mass_matrix = compute_mass_matrix(bm)
    return gradient_matrix.T @ mass_matrix @ gradient_matrix


def compute_deformation_matrices(bm: BMesh) -> (sp.csr_matrix, sp.csr_matrix):
    """
    Compute the cotangent matrix of a mesh, G^TM_vG and the partial
    right hand side matrix G^TM_v.
    """
    gradient_matrix = compute_gradient_matrix(bm)
    mass_matrix = compute_mass_matrix(bm)
    gradient_matrix_trans = gradient_matrix.T

    cotangent = gradient_matrix_trans @ mass_matrix @ gradient_matrix
    gtmv = gradient_matrix_trans @ mass_matrix

    return gradient_matrix, cotangent, gtmv


def to_vxvyvz(mesh: BMesh, dims: list[int]) -> list[np.ndarray]:
    """
    Convert a BMesh into vx, vy, vz representation
    :param mesh: the mesh
    :param dims: the set of dimensions to convert, e.g [0, 1, 2] for full representation
    """

    vs = [[] for _ in dims]

    for v in mesh.verts:
        for d_i, _ in enumerate(dims):
            vs[d_i].append(v.co[d_i])

    for i, _ in enumerate(vs):
        vs[i] = np.array(vs[i])

    return vs


def set_vs(bm: BMesh, vs: list[np.ndarray], dims: list[int]) -> BMesh:
    """
    Set the mesh to the provided vx, vy, vz
    """

    for v_i, v in enumerate(bm.verts):

        # set each dimension of v
        for d_i, dim in enumerate(dims):
            v.co[dim] = vs[d_i][v_i]
