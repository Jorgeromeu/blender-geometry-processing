import pathlib

import matplotlib.pyplot as plt

plt.switch_backend('TkAgg')

from icputil import *
from bpyutil import *
from timer import Timer

class EvaluationOperator(bpy.types.Operator):
    bl_idname = "object.evaluation"
    bl_label = "Evaluation"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        t = Timer()
        t.logging_enabled = True

        eval_collection_name = 'Evaluation'

        max_iters = 20
        eps = 0.001
        max_points = 1000

        suzanne = {
            "title": "Suzanne",
            "collection": "Suzanne",
            "solvers": [{'name': f'$k$={k}',
                         'marker': '.',
                         'filename': f'{k}.png',
                         'solver': ICP(max_iterations=max_iters,
                                       eps=eps, max_points=max_points,
                                       k=k)}
                        for k in [1, 1.5, 2, 3, 10, 11]],
            "folder": 'evaluation/suzanne'
        }

        gdp_planes = {
            "title": "GDP",
            "collection": "GDP",
            "solvers": [{'name': f'{ss}',
                         'marker': '.',
                         'filename': f'{ss}.png',
                         'solver': ICP(max_iterations=20, eps=eps, max_points=max_points, k=2.5,
                                       point_to_plane=True,
                                       sampling_strategy=ss)}
                        for ss in ['RANDOM_POINT', 'NORMAL']],
            'folder': 'evaluation/gdp-planes'
        }

        cubes = {
            "title": "Cubes",
            "collection": "cubes",
            "solvers": [{'name': f'{"Point to Plane" if is_point_to_plane else "Point to Point"}',
                         'marker': '.',
                         'filename': f'{"point-to-plane" if is_point_to_plane else "point-to-point"}.png',
                         'solver': ICP(max_iterations=max_iters, eps=eps, max_points=max_points, k=2.5,
                                       point_to_plane=is_point_to_plane)}
                        for is_point_to_plane in [True, False]],
            'folder': 'evaluation/cubes'
        }

        bunnies = {
            "title": "Bunnies",
            "collection": "bunnies",
            "solvers": [{'name': f'{"Point to Plane" if is_point_to_plane else "Point to Point"}',
                         'marker': '.',
                         'filename': f'{"point-to-plane" if is_point_to_plane else "point-to-point"}.png',
                         'solver': ICP(max_iterations=max_iters, eps=eps, max_points=max_points, k=2.5,
                                       point_to_plane=is_point_to_plane)}
                        for is_point_to_plane in [True, False]],
            'folder': 'evaluation/bunnies/',
        }

        experiments = [
            suzanne
        ]

        for experiment in experiments:

            experiment_folder = pathlib.Path(experiment['folder'])
            if not experiment_folder.exists():
                experiment_folder.mkdir()

            # get experiment collection
            evaluation_coll = bpy.data.collections[eval_collection_name]
            experiment_coll = evaluation_coll.children[experiment["collection"]]

            # get objects for particular experiment
            fixed = get_first_by_regex(experiment_coll.all_objects, 'fixed')
            moving = get_first_by_regex(experiment_coll.all_objects, 'moving')
            target = get_first_by_regex(experiment_coll.all_objects, 'target')
            camera = get_first_by_regex(experiment_coll.all_objects, 'cam')

            # if rendering, setup eevie
            scene = bpy.context.scene
            if camera:
                # hide target
                target.hide_render = True

                # setup camera
                scene.render.engine = 'BLENDER_EEVEE'
                scene.camera = camera
                scene.render.resolution_x = 1920
                scene.render.resolution_x = 1920

                # ensure collection is the only one visible in render
                for c in bpy.data.collections:
                    c.hide_render = True
                evaluation_coll.hide_render = False
                experiment_coll.hide_render = False

                # render state before ICP
                scene.render.filepath = str(experiment_folder / 'original.png')
                bpy.ops.render.render(write_still=True)

            original_transform = moving.matrix_world.copy()
            for entry in experiment["solvers"]:

                # call the ICP solver, with error tracing
                solver = entry['solver']
                solver.evaluation_object = target
                t.start()
                solver.icp(moving, fixed)
                t.stop(entry['name'])

                # plot errors
                errors = [err for (err, t) in solver.errors]
                times = [t for (err, t) in solver.errors]
                plt.plot(times, errors, label=entry['name'],
                         marker=get_or_else(entry, 'marker', ''))

                # render result after running ICP
                if camera and entry.get('filename'):
                    render_path = str(experiment_folder / entry['filename'])
                    if render_path:
                        scene.render.filepath = render_path
                        bpy.ops.render.render(write_still=True)

                # reset transform of object
                moving.matrix_world = original_transform

            # plot
            plt.legend()
            plt.title(experiment["title"])
            plt.xlabel('time (seconds)')
            plt.ylabel('RMSE')
            plt.savefig(str(experiment_folder / 'plot.pdf'))
            plt.cla()
            plt.clf()

        return {'FINISHED'}
