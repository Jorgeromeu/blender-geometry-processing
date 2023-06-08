import numpy as np

import visualdebug
from meshutil import *
from scipy.spatial.transform import Rotation as R


class BrushOperator(bpy.types.Operator):
    bl_idname = "object.geobrush"
    bl_label = "GDP Brush"
    bl_options = {'REGISTER', 'UNDO'}

    scale_x: bpy.props.FloatProperty(name='Scale x', default=1, min=0, max=1000)
    scale_y: bpy.props.FloatProperty(name='Scale y', default=1, min=0, max=1000)
    scale_z: bpy.props.FloatProperty(name='Scale z', default=1, min=0, max=1000)

    rx: bpy.props.IntProperty(name='Rotation x', default=0, min=0, max=359)
    ry: bpy.props.IntProperty(name='Rotation y', default=0, min=0, max=359)
    rz: bpy.props.IntProperty(name='Rotation z', default=0, min=0, max=359)

    # bm: BMesh
    gradient_matrix: sp.csr_matrix
    cotangent_matrix: sp.linalg.splu
    gtmv: sp.csr_matrix

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

        self.gradient_matrix, self.cotangent_matrix, self.gtmv = compute_deformation_matrices(bm)

        self.cotangent_matrix = sp.linalg.splu(self.cotangent_matrix)

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
        grads_x = (self.gradient_matrix @ vx).reshape(-1, 3)
        grads_y = (self.gradient_matrix @ vy).reshape(-1, 3)
        grads_z = (self.gradient_matrix @ vz).reshape(-1, 3)

        # selected faces
        selected_faces_indices = [f.index for f in bm.faces if f.select]

        # select gradients
        selected_grads_x = grads_x[selected_faces_indices]
        selected_grads_y = grads_y[selected_faces_indices]
        selected_grads_z = grads_z[selected_faces_indices]

        # modify the selected gradients with the matrix
        modified_selected_grads_x = selected_grads_x @ self.matrix()
        modified_selected_grads_y = selected_grads_y @ self.matrix()
        modified_selected_grads_z = selected_grads_z @ self.matrix()

        # get modified gradients
        modified_grads_x = grads_x
        modified_grads_y = grads_y
        modified_grads_z = grads_z

        modified_grads_x[selected_faces_indices] = modified_selected_grads_x
        modified_grads_y[selected_faces_indices] = modified_selected_grads_y
        modified_grads_z[selected_faces_indices] = modified_selected_grads_z

        # flatten modified gradients
        modified_grads_x = modified_grads_x.reshape(-1, 1)
        modified_grads_y = modified_grads_y.reshape(-1, 1)
        modified_grads_z = modified_grads_z.reshape(-1, 1)

        rhs_x = (self.gtmv @ modified_grads_x).flatten()
        rhs_y = (self.gtmv @ modified_grads_y).flatten()
        rhs_z = (self.gtmv @ modified_grads_z).flatten()

        center_og = centroid([corner.co for corner in bm.verts])

        new_vx = self.cotangent_matrix.solve(rhs_x)
        new_vy = self.cotangent_matrix.solve(rhs_y)
        new_vz = self.cotangent_matrix.solve(rhs_z)

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
