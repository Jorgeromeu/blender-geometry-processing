import bpy.props

from icputil import *


class BasicICP(bpy.types.Operator):
    """Iterative Closest Point"""
    bl_idname = "object.basicicp"
    bl_label = "Basic ICP"
    bl_options = {'REGISTER', 'UNDO'}

    max_iterations: bpy.props.IntProperty(name='Max iterations', default=100, min=1, max=5000)
    epsilon: bpy.props.FloatProperty(name='Epsilon', default=0.01, min=0.0, step=0.01)
    sample_ratio: bpy.props.FloatProperty(name='Sample ratio', default=0.8, min=0.1, max=1)
    k: bpy.props.FloatProperty(name='k factor', default=2.5, min=1)  # Default is 2.5 based on Masuda, 1996

    dist_method: bpy.props.EnumProperty(name='Distance', items=[
        ('POINT_TO_POINT', 'Point to Point', '...'),
        ('POINT_TO_PLANE', 'Point to Plane', '...'),
    ])

    sampling_method: bpy.props.EnumProperty(name='Point Sampling', items=[
        ('RANDOM_POINT', 'Random point', '...'),
        ('NORMAL', 'Normal sampling', '...'),
    ])

    def execute(self, context):
        objs = bpy.context.selected_objects

        if len(objs) != 2:
            self.report({'ERROR'}, "Select 2 objects for ICP")
            return {'CANCELLED'}

        # TODO for rodrigo, use this check to toggle between point to plane and point to point
        if self.dist_method == 'POINT_TO_POINT':
            pass
        elif self.dist_method == 'POINT_TO_PLANE':
            pass

        # Run ICP algorithm
        try:
            sampling_strategy = "RANDOM_POINT"
            converged, iters_required = icp(objs[0], objs[1],
                                            self.max_iterations, self.epsilon,
                                            self.sample_ratio, self.k, sampling_strategy=self.sampling_method)

            if converged:
                self.report({'INFO'}, f'converged in {iters_required} iterations')
            else:
                self.report({'INFO'}, f'Not converged')
        except RuntimeError as e:
            self.report({'ERROR'}, str(e))

        return {'FINISHED'}

    def draw(self, context):
        layout: bpy.types.UILayout = self.layout
        col = layout.column()

        col.prop(self, "max_iterations")
        col.prop(self, "epsilon")
        col.separator()
        col.prop(self, "sample_ratio")
        col.prop(self, "k")
        col.prop(self, "dist_method")
        col.prop(self, "sampling_method")
