from scipy.spatial.transform import Rotation as R

import visualdebug
from meshutil import *

class LaplacianBrushOperator(bpy.types.Operator):
    bl_options = {'REGISTER', 'UNDO'}

    # bm: BMesh
    laplacian: sp.csc_matrix
    left_hand_side: sp.linalg.splu

    def matrix(self):
        scale = (np.eye(3) * np.array([self.scale_x, self.scale_z, self.scale_y]))
        rotation = R.from_euler('xyz', [self.rx, self.rz, self.ry], degrees=True).as_matrix()
        return rotation @ scale

    def invoke(self, context, event):
        visualdebug.clear_debug_collection()

        obj = bpy.context.active_object

        # ensure in edit mode
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode='EDIT')

        # get editable mesh
        mesh = obj.data
        bm = bmesh.from_edit_mesh(mesh)

        self.laplacian = mesh_laplacian(bm)
        self.left_hand_side = sp.linalg.splu(self.laplacian.T @ self.laplacian)

        bm.free()
        return self.execute(context)

    def execute(self, context):

        obj = bpy.context.active_object

        # ensure in edit mode
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode='EDIT')

        # get editable mesh
        mesh = obj.data
        bm = bmesh.from_edit_mesh(mesh)

        # get coordinate embeddings
        vx, vy, vz = to_vxvyvz(bm, dims=[0, 1, 2])

        # compute, and unflatten gradients of each embedding
        delta_x = (self.laplacian @ vx).reshape(-1, 1)
        delta_y = (self.laplacian @ vy).reshape(-1, 1)
        delta_z = (self.laplacian @ vz).reshape(-1, 1)

        # selected verts
        selected_verts_indices = [v.index for v in bm.verts if v.select]

        # select gradients
        selected_delta_x = delta_x[selected_verts_indices]
        selected_delta_y = delta_y[selected_verts_indices]
        selected_delta_z = delta_z[selected_verts_indices]

        # modify the selected gradients with the matrix
        modified_selected_deltas = np.concatenate((selected_delta_x, selected_delta_y, selected_delta_z),
                                                  axis=1) @ self.matrix()

        modified_selected_delta_x = modified_selected_deltas[:, 0]
        modified_selected_delta_y = modified_selected_deltas[:, 1]
        modified_selected_delta_z = modified_selected_deltas[:, 2]

        # get modified gradients
        modified_delta_x = delta_x.flatten()
        modified_delta_y = delta_y.flatten()
        modified_delta_z = delta_z.flatten()

        modified_delta_x[selected_verts_indices] = modified_selected_delta_x
        modified_delta_y[selected_verts_indices] = modified_selected_delta_y
        modified_delta_z[selected_verts_indices] = modified_selected_delta_z

        # flatten modified gradients
        modified_deltas_x = modified_delta_x.reshape(-1, 1)
        modified_deltas_y = modified_delta_y.reshape(-1, 1)
        modified_deltas_z = modified_delta_z.reshape(-1, 1)

        rhs_x = (self.laplacian.T @ modified_deltas_x).flatten()
        rhs_y = (self.laplacian.T @ modified_deltas_y).flatten()
        rhs_z = (self.laplacian.T @ modified_deltas_z).flatten()

        center_og = centroid([corner.co for corner in bm.verts])

        new_vx = self.left_hand_side.solve(rhs_x)
        new_vy = self.left_hand_side.solve(rhs_y)
        new_vz = self.left_hand_side.solve(rhs_z)

        for v_i, v in enumerate(bm.verts):
            v.co.x = new_vx[v_i]
            v.co.y = new_vy[v_i]
            v.co.z = new_vz[v_i]

        center_new = centroid([corner.co for corner in bm.verts])

        diff = center_new - center_og

        for v in bm.verts:
            v.co -= diff

        bm.free()

        return {'FINISHED'}

class ScaleRotateLaplacianBrush(LaplacianBrushOperator):
    bl_idname = "object.geolaplacebrush"
    bl_label = "GDP Laplace Brush"
    bl_options = {'REGISTER', 'UNDO'}

    scale_x: bpy.props.FloatProperty(name='Scale x', default=1, min=0, max=1000)
    scale_y: bpy.props.FloatProperty(name='Scale y', default=1, min=0, max=1000)
    scale_z: bpy.props.FloatProperty(name='Scale z', default=1, min=0, max=1000)

    rx: bpy.props.IntProperty(name='Rotation x', default=0, min=0, max=359)
    ry: bpy.props.IntProperty(name='Rotation y', default=0, min=0, max=359)
    rz: bpy.props.IntProperty(name='Rotation z', default=0, min=0, max=359)

    def matrix(self):
        scale = (np.eye(3) * np.array([self.scale_x, self.scale_z, self.scale_y]))
        rotation = R.from_euler('xyz', [self.rx, self.rz, self.ry], degrees=True).as_matrix()
        return rotation @ scale

class MatrixLaplacianBrushOp(LaplacianBrushOperator):
    bl_idname = "object.matrixlaplacebrush"
    bl_label = "GDP Laplacian Brush (Matrix Input)"

    val_11: bpy.props.FloatProperty(default=1)
    val_12: bpy.props.FloatProperty(default=0)
    val_13: bpy.props.FloatProperty(default=0)
    val_21: bpy.props.FloatProperty(default=0)
    val_22: bpy.props.FloatProperty(default=1)
    val_23: bpy.props.FloatProperty(default=0)
    val_31: bpy.props.FloatProperty(default=0)
    val_32: bpy.props.FloatProperty(default=0)
    val_33: bpy.props.FloatProperty(default=1)

    def matrix(self):
        return np.array([
            [self.val_11, self.val_12, self.val_13],
            [self.val_21, self.val_22, self.val_23],
            [self.val_31, self.val_32, self.val_33],
        ])

    def draw(self, context):
        layout = self.layout.grid_flow()
        row = layout.row()
        row.prop(self, "val_11", text='')
        row.prop(self, "val_12", text='')
        row.prop(self, "val_13", text='')
        row = layout.row()
        row.prop(self, "val_21", text='')
        row.prop(self, "val_22", text='')
        row.prop(self, "val_23", text='')
        row = layout.row()
        row.prop(self, "val_31", text='')
        row.prop(self, "val_32", text='')
        row.prop(self, "val_33", text='')
