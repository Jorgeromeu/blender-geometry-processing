from icputil import *

class BasicICP(bpy.types.Operator):
    """Print genus of mesh"""
    bl_idname = "object.basicicp"
    bl_label = "Basic ICP"
    bl_options = {'REGISTER', 'UNDO'}

    n_iterations: bpy.props.IntProperty(name='Max iterations', default=100, min=1, max=5000)
    epsilon: bpy.props.FloatProperty(name='Epsilon', default=0.01, min=0.0, step=0.01)
    sample_factor: bpy.props.FloatProperty(name='Sample factor', default=0.8, min=0.1, max=1)
    k: bpy.props.FloatProperty(name='k factor', default=1, min=1)

    def execute(self, context):
        objs = bpy.context.selected_objects

        if len(objs) != 2:
            self.report({'ERROR'}, "Must select two objects")
            return {'CANCELLED'}

        converged, iters_required = icp(objs[0], objs[1], self.n_iterations, self.epsilon, self.sample_factor, self.k)

        if converged:
            self.report({'INFO'}, f'converged in {iters_required} iterations')
        else:
            self.report({'INFO'}, f'Not converged')

        return {'FINISHED'}

    def draw(self, context):
        layout: bpy.types.UILayout = self.layout
        col = layout.column()

        col.prop(self, "n_iterations")
        col.prop(self, "epsilon")
        col.separator()
        col.prop(self, "sample_factor")
        col.prop(self, "k")
