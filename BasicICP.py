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
    normal_dissimilarity_threshold: bpy.props.FloatProperty(name='normal dissimilarity threshold', default=0.5,
                                                            min=0.0001)
    nu: bpy.props.FloatProperty(name='nu', default=1, min=0.01)  # nu parameter for Welsch function weighting

    # Point selection method
    sampling_method: bpy.props.EnumProperty(name='Point Sampling', items=[
        ('RANDOM_POINT', 'Random point', 'Random point sampling'),
        ('NORMAL', 'Normal sampling', 'Normal space sampling'),
        ('STRATIFIED_NORMAL', 'Stratified normal sampling', 'Uses stratification to sample the normal space')
    ])

    dist_method: bpy.props.EnumProperty(name='Distance', items=[
        ('POINT_TO_POINT', 'Point to Point', 'use the normal...'),
        ('POINT_TO_PLANE', 'Point to Plane', '...'),
    ])

    matching_dist_metric: bpy.props.EnumProperty(name='Point Matching Distance Metric', items=[
        ('EUCLIDEAN', 'Euclidean', 'Uses euclidean distance'),
        ('NORMAL_WEIGHTED', 'Normal weighted', 'Normal weighted Euclidean distance'),
    ])

    rejection_criterion: bpy.props.EnumProperty(name='Point-Pair Rejection Criterion', items=[
        ('K_MEDIAN', 'Distance > k*median',
         'Discards point pairs if the point distance is larger than k times the median'),
        ('DISSIMILAR_NORMALS', 'Dissimilar normals', 'Discards point pairs based on how dissimilar their normals are'),
        ('NONE', 'None', 'Do not discard any points')
    ])

    weighting_strategy: bpy.props.EnumProperty(name="Point-Pair Weighting Method", items=[
        ('NONE', 'None', 'All point pairs receive the same weights'),
        ('NORMAL_SIMILARITY', 'Normal similarity', 'Point pairs are weighted according to how similar the normals are'),
        ('DISTANCE', 'Distance', 'Point pairs are weighted according the distance of the pairs'),
        ("WELSCH", "Welsch's function", 'Point pairs are weighted using the Welch function (Zhang, 2022)')
    ])

    def execute(self, context):
        objs = bpy.context.selected_objects

        if len(objs) != 2:
            self.report({'ERROR'}, "Select 2 objects for ICP")
            return {'CANCELLED'}
        icpSolver = ICP(max_iterations=self.max_iterations, eps=self.epsilon, sample_rate=self.sample_ratio,
                        k=self.k, nu=self.nu, sampling_strategy=self.sampling_method,
                        normal_dissimilarity_thres=self.normal_dissimilarity_threshold,
                        point_to_plane=self.dist_method == 'POINT_TO_PLANE',
                        rejection_criterion=self.rejection_criterion,
                        weighting_strategy=self.weighting_strategy)
        try:
            converged, iters_required = icpSolver.icp(objs[0], objs[1])

            if converged:
                self.report({'INFO'}, f'converged in {iters_required} iterations')
            else:
                self.report({'INFO'}, f'Not converged')
        except RuntimeError as e:
            self.report({'ERROR'}, str(e))

        return {'FINISHED'}

    def draw(self, context):
        layout: bpy.types.UILayout = self.layout.grid_flow()
        col = layout.column()
        col.prop(self, "max_iterations")
        col.prop(self, "epsilon")
        col.separator()
        col.prop(self, "sample_ratio")
        col.prop(self, "k")
        col.prop(self, "normal_dissimilarity_threshold")
        col.prop(self, "nu")
        col.prop(self, "sampling_method")
        col.prop(self, "dist_method")
        col.prop(self, "matching_dist_metric")
        col.prop(self, "rejection_criterion")
        col.prop(self, "weighting_strategy")
