import cProfile
import pstats

import bpy.props

from .meshutil import *

def optimal_v(og_delta: np.ndarray, laplacian, a: float,
              constraint_matrix: np.ndarray, constraint_rhs: np.ndarray) -> np.ndarray:
    """
    Compute transformation that minimizes weighted sum of Laplacian energy and constraint energy
    """

    matrix = laplacian.transpose() @ laplacian + a * constraint_matrix.transpose() @ constraint_matrix

    rhs = laplacian.transpose() @ og_delta.reshape(
        (len(og_delta), 1)) + a * constraint_matrix.transpose() @ constraint_rhs

    opt_v = sp.linalg.spsolve(matrix, rhs)
    # opt_v = np.linalg.solve(matrix, rhs.flatten())
    return opt_v

class DeformationOp(bpy.types.Operator):
    bl_idname = "object.implicitdeform"
    bl_label = "GDP deformation"
    bl_options = {'REGISTER', 'UNDO'}

    constraint_weight: bpy.props.FloatProperty(name='Lambda', default=0.9, min=0, max=1)

    preserve_centroid: bpy.props.BoolProperty(name='Preserve Centroid', default=True)

    matrix_cache = {}

    # define which axis to affect
    affect_x: bpy.props.BoolProperty(name='X', default=True)
    affect_y: bpy.props.BoolProperty(name='Y', default=True)
    affect_z: bpy.props.BoolProperty(name='Z', default=True)

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

    def construct_constraint_system(self, dim_idx, og_vs) -> (np.ndarray, np.ndarray):

        num_verts = len(og_vs)

        # create a constraint for each handle
        constraint_matrix = sp.lil_array((len(self.handles), num_verts))
        constraint_rhs = sp.lil_array((len(self.handles), 1))

        for i, (vertex_index, desired_pos_object) in enumerate(self.handles):
            desired_pos = get_first_by_regex(desired_pos_object).location

            constraint_matrix[i, vertex_index] = 1
            constraint_rhs[i] = desired_pos[self._dims()[dim_idx]]

        # add a constraint to preserve centroid
        if self.preserve_centroid:
            constraint_matrix_centroid = np.ones((1, num_verts)) / num_verts
            constraint_rhs_centroid = np.array([np.average(og_vs)]).reshape(1, 1)

            constraint_matrix = sp.vstack([constraint_matrix, constraint_matrix_centroid])
            constraint_rhs = sp.vstack([constraint_rhs, constraint_rhs_centroid])

        return constraint_matrix.tocsc(), constraint_rhs

    def deform_mesh(self, mesh: BMesh):
        # Compute laplacian of mesh
        laplacian = mesh_laplacian(mesh)

        # get original vertex positions and laplacian coordinates of the mesh
        og_vs = to_vxvyvz(mesh, self._dims())
        og_deltas = [laplacian @ vd.reshape((len(vd), 1)) for vd in og_vs]

        # for each dimension, minimize weighted sum of constraint energy and deformation energy
        opt_vs = og_vs
        for d_i, d in enumerate(self._dims()):
            constraint_matrix, constraint_rhs = self.construct_constraint_system(d_i, og_vs[d_i])
            opt_vd = optimal_v(og_deltas[d_i], laplacian, self.constraint_weight, constraint_matrix, constraint_rhs)
            opt_vs[d_i] = opt_vd

        # set vertices to updated vertex positions
        set_vs(mesh, opt_vs, self._dims())

    def execute(self, context):

        # ensure single object is selected
        if len(bpy.context.selected_objects) != 1:
            self.report({'ERROR'}, "Select a single object to deform")
            return {'CANCELLED'}
        obj = bpy.context.selected_objects[0]

        triangulate_object(obj)

        if obj not in self.__class__.matrix_cache:
            print("Matrix cache miss - building and factorizing")
            mesh = mesh_from_object(obj)
            # Get the gradient, cotangent matrix G^TM_vG and the partial rhs G^TM_v and cache them.
            gradient, cotangent, gtmv = compute_deformation_matrices(mesh)
            self.__class__.matrix_cache[obj] = (sp.linalg.splu(cotangent), gtmv)

        contangent_matrix = self.__class__.matrix_cache[obj][0]
        partial_rhs = self.__class__.matrix_cache[obj][1]

        # TODO: SOMETHING AFTER THIS POINT IS VERY SLOW

        # read handles
        self.handles = []
        vertex_groups = obj.vertex_groups
        for group in vertex_groups:
            vs = [v.index for v in obj.data.vertices if group.index in [vg.group for vg in v.groups]]
            self.handles.append((vs[0], group.name))

        # get editable mesh
        bpy.ops.object.mode_set(mode='EDIT')
        mesh = bmesh.from_edit_mesh(obj.data)

        with cProfile.Profile() as pr:
            self.deform_mesh(mesh)

        stats = pstats.Stats(pr)
        stats.sort_stats(pstats.SortKey.TIME)
        stats.dump_stats(filename='profile.prof')

        return {'FINISHED'}

class TranslateVertexOperator(bpy.types.Operator):
    bl_idname = "object.translate_vertex"
    bl_label = "Translate Vertex"

    def modal(self, context, event):
        pass

    def invoke(self, context, event):
        pass

    def execute(self, context):
        pass
