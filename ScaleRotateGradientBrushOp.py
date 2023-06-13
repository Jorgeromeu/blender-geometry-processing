from scipy.spatial.transform import Rotation as R

from meshutil import *

class GradientBrushOperator(bpy.types.Operator):
    bl_options = {'REGISTER', 'UNDO'}

    gradient_matrix: sp.csr_matrix
    cotangent_matrix: sp.linalg.splu
    gtmv: sp.csr_matrix

    def matrix(self) -> np.ndarray:
        np.eye(3)

    def invoke(self, context, event):

        obj = bpy.context.active_object

        # ensure in edit mode
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode='EDIT')

        # get editable mesh
        mesh = obj.data
        bm = bmesh.from_edit_mesh(mesh)

        # compute gradient matrix
        self.gradient_matrix, self.cotangent_matrix, self.gtmv = compute_deformation_matrices(bm)

        # compute and factorize cotangent matrix
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

        # set vertex coordinates
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

class ScaleRotateGradientBrushOp(GradientBrushOperator):
    bl_idname = "edit.gradientbrush"
    bl_label = "GDP Gradient Brush"

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

    def invoke(self, context, event):

        obj = bpy.context.active_object

        # ensure in edit mode
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode='EDIT')

        # get editable mesh
        mesh = obj.data
        bm = bmesh.from_edit_mesh(mesh)

        # compute gradient matrix
        self.gradient_matrix, self.cotangent_matrix, self.gtmv = compute_deformation_matrices(bm)

        # compute and factorize cotangent matrix
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

        # set vertex coordinates
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

    def draw(self, context):
        layout = self.layout.grid_flow()
        col = layout.column()

        box = col.box()
        box.prop(self, "scale_x")
        box.prop(self, "scale_y")
        box.prop(self, "scale_z")

        box = col.box()
        box.prop(self, "rx")
        box.prop(self, "ry")
        box.prop(self, "rz")

class MatrixGradientBrushOp(GradientBrushOperator):
    bl_idname = "object.matrixgradientbrush"
    bl_label = "GDP Gradient Brush (Matrix Input)"

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
