import bmesh
import bpy.props

from .meshutil import *

def to_vs(mesh: BMesh, dims: list[int]) -> list[np.ndarray]:
    vs = [[], [], []]

    for v in mesh.verts:
        for d in dims:
            vs[d].append(v.co[d])

    for d in dims:
        vs[d] = np.array(vs[d])

    return vs

def set_vs(bm: BMesh, vs) -> BMesh:
    """
    Set the mesh to the provided vx, vy, vz
    """

    for i, v in enumerate(bm.verts):
        v.co.x = vs[0][i]
        v.co.y = vs[1][i]
        v.co.z = vs[2][i]

def optimal_v(og_delta: np.ndarray, laplacian: np.ndarray, a: float,
              constraint_matrix: np.ndarray, constraint_rhs: np.ndarray) -> np.ndarray:
    """
    Compute transformation that minimizes weighted sum of Laplacian energy and constraint energy
    """
    matrix = laplacian.transpose() @ laplacian + a * constraint_matrix.transpose() @ constraint_matrix

    rhs = laplacian.transpose() @ og_delta.reshape(
        (len(og_delta), 1)) + a * constraint_matrix.transpose() @ constraint_rhs

    return np.linalg.solve(matrix, rhs.flatten())

def mesh_laplacian(mesh: BMesh) -> np.ndarray:
    n = len(mesh.verts)

    D = np.zeros((n, n))
    A = np.zeros((n, n))

    for i, v_i in enumerate(mesh.verts):
        for j, v_j in enumerate(mesh.verts):

            if i == j:
                D[i, i] = len(neighbors(v_i))

            if v_j in neighbors(v_i):
                A[i, j] = 1

    L = np.eye(n) - np.linalg.inv(D) @ A
    return L

class DeformationOp(bpy.types.Operator):
    bl_idname = "object.implicitdeform"
    bl_label = "GDP deformation"
    bl_options = {'REGISTER', 'UNDO'}

    constraint_weight: bpy.props.FloatProperty(name='Lambda', default=0.9, min=0, max=1)

    preserve_centroid: bpy.props.BoolProperty(name='Preserve Centroid', default=True)

    # define which axis to affect
    affect_x: bpy.props.BoolProperty(name='X', default=True)
    affect_y: bpy.props.BoolProperty(name='Y', default=True)
    affect_z: bpy.props.BoolProperty(name='Z', default=True)

    # TODO make property, hook up to UI
    handles = [
        (431, 'Empty'),
        (432, 'Empty.001'),
    ]

    def _dims(self) -> list[int]:

        """
        Return the affected dimensions
        """

        res = []
        if self.affect_x:
            res.append(0)
        if self.affect_y:
            res.append(1)
        if self.affect_z:
            res.append(2)

        return res

    def compute_constraints_system(self, dim, og_vs):

        num_verts = len(og_vs)

        # create a constraint for each handle
        constraint_matrix = np.zeros((len(self.handles), num_verts))
        constraint_rhs = np.zeros((len(self.handles), 1))

        for i, (vertex_index, desired_pos_object) in enumerate(self.handles):
            desired_pos = get_first_by_regex(desired_pos_object).location

            constraint_matrix[i, vertex_index] = 1
            constraint_rhs[i] = desired_pos[dim]

        # add a constraint to preserve centroid
        if self.preserve_centroid:
            constraint_matrix_centroid = np.ones((1, num_verts)) / num_verts
            constraint_rhs_centroid = np.array([np.average(og_vs)]).reshape(1, 1)

            constraint_matrix = np.concatenate((constraint_matrix, constraint_matrix_centroid), axis=0)
            constraint_rhs = np.concatenate((constraint_rhs, constraint_rhs_centroid), axis=0)

        return constraint_matrix, constraint_rhs

    def execute(self, context):

        if not bpy.context.selected_objects:
            self.report({'ERROR'}, "Select an object to deform")
            return {'CANCELLED'}

        # object to be deformed
        obj = bpy.context.selected_objects[0]

        # get editable mesh
        bpy.ops.object.mode_set(mode='EDIT')
        mesh = bmesh.from_edit_mesh(obj.data)

        # Compute laplacian of mesh
        laplacian = mesh_laplacian(mesh)

        # get original vertex positions and laplacian coordinates
        og_vs = to_vs(mesh, self._dims())
        og_deltas = [laplacian @ vd.reshape((len(vd), 1)) for vd in og_vs]

        # compute optimal vertex positions for each dimension
        opt_vs = og_vs

        # for each dimension, minimize weighted sum of constraint energy and deformation energy
        for d in self._dims():
            constraint_matrix, constraint_rhs = self.compute_constraints_system(d, og_vs[d])
            opt_vd = optimal_v(og_deltas[d], laplacian, self.constraint_weight, constraint_matrix, constraint_rhs)
            opt_vs[d] = opt_vd

        # set vertices to updated vertex positions
        set_vs(mesh, opt_vs)

        return {'FINISHED'}
