import numpy as np
from scipy.spatial.transform import Rotation as R

import visualdebug
from meshutil import *


class LaplacianBrushOperator(bpy.types.Operator):
    bl_idname = "object.geolaplacebrush"
    bl_label = "GDP Laplace Brush"
    bl_options = {'REGISTER', 'UNDO'}

    scale_x: bpy.props.FloatProperty(name='Scale x', default=1, min=0, max=1000)
    scale_y: bpy.props.FloatProperty(name='Scale y', default=1, min=0, max=1000)
    scale_z: bpy.props.FloatProperty(name='Scale z', default=1, min=0, max=1000)

    rx: bpy.props.IntProperty(name='Rotation x', default=0, min=0, max=359)
    ry: bpy.props.IntProperty(name='Rotation y', default=0, min=0, max=359)
    rz: bpy.props.IntProperty(name='Rotation z', default=0, min=0, max=359)

    # bm: BMesh
    laplacian: sp.csc_matrix
    left_hand_side: sp.linalg.splu

    def matrix(self):
        scale = (np.eye(3) * np.array([self.scale_x, self.scale_y, self.scale_z]))
        rotation = R.from_euler('xyz', [self.rx, self.ry, self.rz], degrees=True).as_matrix()
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
        self.left_hand_side = sp.linalg.splu(2 * self.laplacian.T @ self.laplacian)

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
        selected_verts_set = set(selected_verts_indices)
        print(f"Selected indices: {len(selected_verts_indices)}")

        # select gradients
        selected_delta_x = delta_x[selected_verts_indices]
        selected_delta_y = delta_y[selected_verts_indices]
        selected_delta_z = delta_z[selected_verts_indices]
        print(f"Selected delta shapes: {selected_delta_x.shape}")

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

        rhs_x = 2 * (self.laplacian.T @ modified_deltas_x).flatten()
        rhs_y = 2 * (self.laplacian.T @ modified_deltas_y).flatten()
        rhs_z = 2 * (self.laplacian.T @ modified_deltas_z).flatten()

        center_og = centroid([corner.co for corner in bm.verts])

        new_vx = self.left_hand_side.solve(rhs_x)
        new_vy = self.left_hand_side.solve(rhs_y)
        new_vz = self.left_hand_side.solve(rhs_z)

        for v_i, v in enumerate(bm.verts):
            if v_i in selected_verts_set:
                v.co.x = new_vx[v_i]
                v.co.y = new_vy[v_i]
                v.co.z = new_vz[v_i]

        center_new = centroid([corner.co for corner in bm.verts])

        diff = center_new - center_og

        for v in bm.verts:
            v.co -= diff

        bm.free()

        return {'FINISHED'}
