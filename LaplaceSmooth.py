from meshutil import *

class LaplaceSmoothOperator(bpy.types.Operator):
    bl_idname = "object.laplacesmoothop"
    bl_label = "GDP Laplace Smooth"
    bl_options = {'REGISTER', 'UNDO'}

    n_iters: bpy.props.IntProperty('Num Iterations', default=1, min=0, max=10)
    step_size: bpy.props.FloatProperty('Step Size', default=0.3, min=0, max=1)

    def execute(self, context):
        # ensure single object is selected
        if len(bpy.context.selected_objects) != 1:
            self.report({'ERROR'}, "Select a single object to deform")
            return {'CANCELLED'}
        obj = bpy.context.selected_objects[0]

        # get editable mesh
        bpy.ops.object.mode_set(mode='EDIT')
        bm = bmesh.from_edit_mesh(obj.data)

        laplacian = mesh_laplacian(bm)

        vx, vy, vz = to_vxvyvz(bm, dims=[0, 1, 2])

        for _ in range(self.n_iters):
            delta_x = laplacian @ vx
            delta_y = laplacian @ vy
            delta_z = laplacian @ vz

            vx -= self.step_size * delta_x
            vy -= self.step_size * delta_y
            vz -= self.step_size * delta_z

        # set vertex coordinates
        for v_i, v in enumerate(bm.verts):
            v.co.x = vx[v_i]
            v.co.y = vy[v_i]
            v.co.z = vz[v_i]

        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout.grid_flow()
        row = layout.row()
        row.prop(self, "n_iters")
        row.prop(self, "step_size", text='')
