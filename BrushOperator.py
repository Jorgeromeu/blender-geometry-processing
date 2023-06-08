import visualdebug
from matrix_cache import get_matrices
from meshutil import *

class BrushOperator(bpy.types.Operator):
    bl_idname = "object.geobrush"
    bl_label = "GDP Brush"
    bl_options = {'REGISTER', 'UNDO'}

    length: bpy.props.FloatProperty(name='Length', default=1, min=0, max=5)

    rx: bpy.props.IntProperty(name='Rx', default=0, min=0, max=359)
    ry: bpy.props.IntProperty(name='Ry', default=0, min=0, max=359)
    rz: bpy.props.IntProperty(name='Rz', default=0, min=0, max=359)

    def matrix(self):
        return np.eye(3) * self.length
        # return R.from_euler('xyz', [self.rx, self.ry, self.rz], degrees=True).as_matrix()

    def execute(self, context):
        visualdebug.clear_debug_collection()

        obj = bpy.context.active_object

        # ensure in edit mode
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode='EDIT')

        # get editable mesh
        mesh = obj.data
        bm = bmesh.from_edit_mesh(mesh)

        # get cached matrices
        gradient_matrix, cotangent_matrix, gtmv = get_matrices(obj, bm)

        # get coordinate embeddings
        vx, vy, vz = to_vxvyvz(bm, dims=[0, 1, 2])

        # compute, and unflatten gradients of each embedding
        grads_x = (gradient_matrix @ vx).reshape(-1, 3)
        grads_y = (gradient_matrix @ vy).reshape(-1, 3)
        grads_z = (gradient_matrix @ vz).reshape(-1, 3)

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

        rhs_x = (gtmv @ modified_grads_x).flatten()
        rhs_y = (gtmv @ modified_grads_y).flatten()
        rhs_z = (gtmv @ modified_grads_z).flatten()

        center_og = centroid([corner.co for corner in bm.verts])

        new_vx = cotangent_matrix.solve(rhs_x)
        new_vy = cotangent_matrix.solve(rhs_y)
        new_vz = cotangent_matrix.solve(rhs_z)

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
