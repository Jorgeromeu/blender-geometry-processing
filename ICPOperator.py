import cProfile
import pstats

import bpy.props

from .icputil import *

class ICPOperator(bpy.types.Operator):
    """Iterative Closest Point"""
    bl_idname = "object.icp"
    bl_label = "Iterative Closest Point (ICP)"
    bl_options = {'REGISTER', 'UNDO'}

    minimization_function: bpy.props.EnumProperty(name='Minimization Function',
                                                  description='The function that is minimized at each iteration',
                                                  items=[
                                                      ('POINT_TO_POINT', 'Point to Point distance',
                                                       'Minimize point-to-point distance of matched points'),
                                                      ('POINT_TO_PLANE', 'Point to Plane distance',
                                                       'Minimize point-to-plane distance of matched points'),
                                                  ])

    max_iterations: bpy.props.IntProperty(name='Max iterations',
                                          description='Maximum amount of iterations to run, until converges',
                                          default=10, min=1, max=5000)

    epsilon: bpy.props.FloatProperty(name='Epsilon',
                                     description='Threshold used to detect if converged',
                                     default=0.01, min=0.0, step=0.01)

    normal_dissimilarity_threshold: bpy.props.FloatProperty(name='normal dissimilarity threshold', default=0.5,
                                                            min=0.0001)
    # Point selection method
    sampling_method: bpy.props.EnumProperty(name='Method',
                                            description='Method used to sample points to match in original mesh',
                                            items=[
                                                ('RANDOM_POINT', 'Random point', 'Random point sampling'),
                                                ('NORMAL', 'Normal sampling', 'Normal space sampling'),
                                                ('STRATIFIED_NORMAL', 'Stratified normal sampling',
                                                 'Uses stratification to sample the normal space')
                                            ])

    max_points: bpy.props.IntProperty(name='Max Points',
                                      description='Maximum number of points to sample',
                                      default=1000,
                                      min=1)

    matching_dist_metric: bpy.props.EnumProperty(name='Method',
                                                 description='Metric used to create point correspondences',
                                                 items=[
                                                     ('EUCLIDEAN', 'Euclidean', 'Uses euclidean distance'),
                                                     ('NORMAL_WEIGHTED', 'Normal weighted',
                                                      'Normal weighted Euclidean distance'),
                                                 ])

    rejection_criterion: bpy.props.EnumProperty(name='Criterion',
                                                description='Criterion used to reject outlier point-pairs',
                                                items=[
                                                    ('K_MEDIAN', 'Distance > k*median',
                                                     'Discards point pairs if the point distance is larger than k times the median'),
                                                    ('DISSIMILAR_NORMALS', 'Dissimilar normals',
                                                     'Discards point pairs based on how dissimilar their normals are'),
                                                    ('NONE', 'None', 'Do not discard any points')
                                                ])
    k: bpy.props.FloatProperty(name='k factor', default=2.5, min=1)  # Default is 2.5 based on Masuda, 1996

    weighting_strategy: bpy.props.EnumProperty(name="Method",
                                               description='Method used to weigh, point-pairs',
                                               items=[
                                                   ('NONE', 'None', 'All point pairs receive the same weights'),
                                                   ('NORMAL_SIMILARITY', 'Normal similarity',
                                                    'Point pairs are weighted according to how similar the normals are'),
                                                   ('DISTANCE', 'Distance',
                                                    'Point pairs are weighted according the distance of the pairs'),
                                                   ("WELSCH", "Welsch's function",
                                                    'Point pairs are weighted using the Welsch function (Zhang, 2022)')
                                               ])

    nu: bpy.props.FloatProperty(name='nu', default=1, min=0.01)

    animate: bpy.props.BoolProperty('Animate', default=False, description='output animation as set of frames')
    animation_dir: bpy.props.StringProperty('Animation dir', default='animation',
                                            description='relative path to animation directory')

    def draw(self, context):
        layout: bpy.types.UILayout = self.layout.grid_flow()
        col = layout.column()

        col.prop(self, "minimization_function")

        box = col.box()
        box.label(text="Iteration options:")
        box.prop(self, "max_iterations")
        box.prop(self, "epsilon")

        box = col.box()
        box.label(text='Point sampling:')
        box.prop(self, "sampling_method")
        box.prop(self, "max_points")

        box = col.box()
        box.label(text='Point matching:')
        box.prop(self, "matching_dist_metric")

        box = col.box()
        box.label(text='Point-pair rejection:')

        box.prop(self, "rejection_criterion")
        if self.rejection_criterion == 'K_MEDIAN':
            box.prop(self, "k")
        elif self.rejection_criterion == 'DISSIMILAR_NORMALS':
            box.prop(self, "normal_dissimilarity_threshold")

        if self.minimization_function == 'POINT_TO_POINT':

            box = col.box()
            box.label(text="Point-pair weighing:")
            box.prop(self, "weighting_strategy")

            if self.weighting_strategy == 'WELSCH':
                box.prop(self, "nu")

        box = col.box()
        box.label(text='Animation')
        box.prop(self, "animate")
        box.prop(self, "animation_dir")

    def execute(self, context):
        objs = bpy.context.selected_objects

        if len(objs) != 2:
            self.report({'ERROR'}, "Select 2 objects for ICP")
            return {'CANCELLED'}

        # first selected is moving, second selected is fixed
        fixed = bpy.context.active_object
        moving = objs[1] if fixed == objs[0] else objs[0]

        icp_solver = ICP(max_iterations=self.max_iterations, eps=self.epsilon, max_points=self.max_points,
                         k=self.k, nu=self.nu, sampling_strategy=self.sampling_method,
                         normal_dissimilarity_thresh=self.normal_dissimilarity_threshold,
                         point_to_plane=self.minimization_function == 'POINT_TO_PLANE',
                         rejection_criterion=self.rejection_criterion,
                         weighting_strategy=self.weighting_strategy,
                         animate=self.animate,
                         frames_folder=self.animation_dir)

        try:

            with cProfile.Profile() as pr:
                converged, iters_required = icp_solver.icp(moving, fixed)

            stats = pstats.Stats(pr)
            stats.sort_stats(pstats.SortKey.TIME)
            stats.dump_stats(filename='profile.prof')

            if converged:
                self.report({'INFO'}, f'converged in {iters_required} iterations')
            else:
                self.report({'INFO'}, f'Not converged')

        except RuntimeError as e:
            self.report({'ERROR'}, str(e))

        return {'FINISHED'}
