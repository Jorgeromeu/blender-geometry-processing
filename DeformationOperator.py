import cProfile
import pstats

import bmesh
import bpy.props
import mathutils

from .meshutil import *


def to_vs(mesh: BMesh, dims: list[int]) -> list[np.ndarray]:
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


def triangulate_object(obj):
    me = obj.data
    # Get a BMesh representation
    bm = bmesh.new()
    bm.from_mesh(me)

    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    # V2.79 : bmesh.ops.triangulate(bm, faces=bm.faces[:], quad_method=0, ngon_method=0)

    # Finish up, write the bmesh back to the mesh
    bm.to_mesh(me)
    bm.free()


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
        og_vs = to_vs(mesh, self._dims())
        og_deltas = [laplacian @ vd.reshape((len(vd), 1)) for vd in og_vs]

        # for each dimension, minimize weighted sum of constraint energy and deformation ener   gy
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

    start_mouse_pos = None
    start_vertex_pos = None
    selected_vert = None

    def modal(self, context, event):
        print('A')
        if event.type == 'MOUSEMOVE':
            mouse_pos = mathutils.Vector((event.mouse_region_x, event.mouse_region_y))

            if self.start_mouse_pos:
                translation = mouse_pos - self.start_mouse_pos
                self.selected_vert.co = self.start_vertex_pos + translation
            return {'RUNNING_MODAL'}

        elif event.type == 'LEFTMOUSE':
            return {'FINISHED'}

        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            return {'RUNNING_MODAL'}

    def invoke(self, context, event):

        if bpy.context.active_object is None:
            self.report({'WARNING'}, 'no active object')
            return {'CANCELLED'}
        if bpy.context.active_object.type != 'MESH':
            self.report({'WARNING'}, 'no mesh selected')
            return {'CANCELLED'}

        obj = bpy.context.selected_objects[0]
        mesh = bmesh.from_edit_mesh(obj.data)

        # TODO handle more than one / zero selection
        self.selected_vert = [v for v in mesh.verts if v.select][0]

        self.start_mouse_pos = mathutils.Vector((event.mouse_region_x, event.mouse_region_y))

        return {'RUNNING_MODAL'}
