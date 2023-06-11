from meshutil import *
from smoothing_utils import laplace_smoothing



class LaplaceSmoothOperator(bpy.types.Operator):
    bl_idname = "object.laplacesmoothop"
    bl_label = "GDP Laplace Smooth"
    bl_options = {'REGISTER', 'UNDO'}

    n_iters: bpy.props.IntProperty('Num Iterations', default=1, min=0, max=10)
    step_size: bpy.props.FloatProperty('Step Size', default=0.1, min=0, max=1)

    def execute(self, context):
        # ensure single object is selected
        if len(bpy.context.selected_objects) != 1:
            self.report({'ERROR'}, "Select a single object to deform")
            return {'CANCELLED'}
        obj = bpy.context.selected_objects[0]

        # get editable mesh
        bpy.ops.object.mode_set(mode='EDIT')
        bm = bmesh.from_edit_mesh(obj.data)

        vx, vy, vz = laplace_smoothing(bm, self.n_iters, self.step_size)

        # set vertex coordinates
        for v_i, v in enumerate(bm.verts):
            v.co.x = vx[v_i]
            v.co.y = vy[v_i]
            v.co.z = vz[v_i]

        return {'FINISHED'}
