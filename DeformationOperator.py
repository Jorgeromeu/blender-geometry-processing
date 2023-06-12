import bpy.props

from .meshutil import *

def solve_optimal_pos(og_delta: np.ndarray, laplacian, a: float,
                      constraint_matrix: np.ndarray,
                      constraint_rhs: np.ndarray) -> np.ndarray:
    """
    Compute transformation that minimizes weighted sum of Laplacian energy and constraint energy
    """

    matrix = laplacian.transpose() @ laplacian + a * constraint_matrix.transpose() @ constraint_matrix

    rhs = laplacian.transpose() @ og_delta.reshape(
        (len(og_delta), 1)) + a * constraint_matrix.transpose() @ constraint_rhs

    opt_v = sp.linalg.spsolve(matrix, rhs)
    return opt_v

class ConstraintDeformationOp(bpy.types.Operator):
    bl_idname = "object.laplaciandeform"
    bl_label = "GDP deformation"
    bl_options = {'REGISTER', 'UNDO'}

    constraint_weight: bpy.props.FloatProperty(name='Lambda', default=0.9, min=0, max=1)

    preserve_centroid: bpy.props.BoolProperty(name='Preserve Centroid', default=False)

    matrix_cache = {}

    # define which axis to affect
    affect_x: bpy.props.BoolProperty(name='X', default=True)
    affect_y: bpy.props.BoolProperty(name='Y', default=True)
    affect_z: bpy.props.BoolProperty(name='Z', default=True)

    def _affected_dims(self) -> list[int]:

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

    def construct_constraint_system(self, dim_constraints, og_positions):
        num_verts = len(og_positions)

        # create a constraint for each handle
        constraint_matrix = sp.lil_array((len(dim_constraints), num_verts))
        constraint_rhs = sp.lil_array((len(dim_constraints), 1))

        for constraint_i, (vert_index, pos) in enumerate(dim_constraints):
            constraint_matrix[constraint_i, vert_index] = 1
            constraint_rhs[constraint_i] = pos

        # if self.preserve_centroid:
        #     constraint_matrix_centroid = np.ones((1, num_verts)) / num_verts
        #     constraint_rhs_centroid = np.array([np.average(og_positions)]).reshape(1, 1)
        #
        #     constraint_matrix = sp.vstack([constraint_matrix, constraint_matrix_centroid])
        #     constraint_rhs = sp.vstack([constraint_rhs, constraint_rhs_centroid])

        return constraint_matrix, constraint_rhs

    def deform_mesh(self, mesh: BMesh, constraints):

        laplacian = mesh_laplacian(mesh)

        # get original vertex positions and laplacian coordinates of the mesh
        og_vs = to_vxvyvz(mesh, self._affected_dims())
        og_deltas = [laplacian @ vd.reshape((len(vd), 1)) for vd in og_vs]

        # for each dimension, minimize weighted sum of constraint energy and deformation energy
        opt_vs = og_vs
        for d_i, d in enumerate(self._affected_dims()):

            constraint_matrix, constraint_rhs = self.construct_constraint_system(constraints[d], og_vs[d])

            if d == 2:
                print(constraint_matrix)

            opt_vd = solve_optimal_pos(og_deltas[d_i], laplacian, self.constraint_weight, constraint_matrix,
                                       constraint_rhs)
            opt_vs[d_i] = opt_vd

        # set vertices to updated vertex positions
        set_vs(mesh, opt_vs, self._affected_dims())

    def parse_constraints(self, obj):

        constraints = [[] for _ in range(3)]
        axis_mapping = {'x': 0, 'y': 1, 'z': 2}

        vertex_groups = obj.vertex_groups
        for group in vertex_groups:
            group_vs = [v.index for v in obj.data.vertices if group.index in [vg.group for vg in v.groups]]

            axis, object_name = group.name.split('-')
            target_pos_ob = get_first_by_regex(object_name)

            if target_pos_ob == None:
                self.report({'ERROR'}, f'No object called {object_name}')
                continue

            target_pos = target_pos_ob.location
            affected_axis = [axis_mapping[c] for c in axis]

            for ax in affected_axis:

                for v in group_vs:
                    constraints[ax].append((v, target_pos[ax]))

        return constraints

    def execute(self, context):
        # ensure single object is selected
        if len(bpy.context.selected_objects) != 1:
            self.report({'ERROR'}, "Select a single object to deform")
            return {'CANCELLED'}
        obj = bpy.context.selected_objects[0]

        # parse the constraints
        constraints = self.parse_constraints(obj)

        bpy.ops.object.mode_set(mode='EDIT')
        bm = bmesh.from_edit_mesh(obj.data)

        self.deform_mesh(bm, constraints)

        return {'FINISHED'}
