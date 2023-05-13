import matplotlib.pyplot as plt

plt.switch_backend('TkAgg')

from icputil import *

class EvaluationOperator(bpy.types.Operator):
    bl_idname = "object.evaluation"
    bl_label = "Evaluation"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        evaluation_collection = 'Evaluation'

        max_iters = 20
        eps = 0.001
        max_points = 1000

        experiments = [
            # {
            #     "title": "Suzanne",
            #     "collection": "Suzanne",
            #     "solvers": [{'name': f'$k$={k}', 'marker': '.',
            #                  'solver': ICP(max_iterations=max_iters, eps=eps, max_points=max_points, k=k)} for k in
            #                 [1, 1.5, 2, 3, 10, 11]],
            #     "filename": "evaluation/plot.pdf"
            # },
            {
                "title": "GDP",
                "collection": "GDP",
                "solvers": [{'name': f'{ss}', 'marker': '.',
                             'solver': ICP(max_iterations=max_iters, eps=eps, max_points=max_points, k=2.5,
                                           sampling_strategy=ss)}
                            for ss in ['RANDOM_POINT', 'NORMAL', 'STRATIFIED_NORMAL']],
                "filename": "evaluation/plot.pdf"
            }
        ]

        for experiment in experiments:

            collection = bpy.data.collections[evaluation_collection].children[experiment["collection"]].all_objects

            fixed = collection['fixed']
            moving = collection['moving']
            target = collection['target']

            original_transform = moving.matrix_world.copy()
            for entry in experiment["solvers"]:
                solver = entry['solver']
                solver.evaluation_object = target

                solver.icp(moving, fixed)

                errors = [err for (err, t) in solver.errors]
                times = [t for (err, t) in solver.errors]

                plt.plot(times, errors, label=entry['name'])

                # reset transform of object
                moving.matrix_world = original_transform

            plt.legend()
            plt.title(experiment["title"])
            plt.xlabel('time (seconds)')
            plt.ylabel('RMSE')
            plt.savefig(experiment["filename"])
            plt.cla()
            plt.clf()

        return {'FINISHED'}
