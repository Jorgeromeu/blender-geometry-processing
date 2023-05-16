
from icputil import *
from bpyutil import *
from timer import Timer

def to_filename(s: str) -> str:
    return s.lower().replace(' ', '-')

class EvaluationOperator(bpy.types.Operator):
    bl_idname = "object.evaluation"
    bl_label = "Evaluation"
    bl_options = {'REGISTER', 'UNDO'}

    # all experiments should be placed as subcollections of this collection
    eval_collection_name = 'Evaluation'

    initialized = False

    def execute(self, context):
        if not self.initialized:
            try:
                import matplotlib.pyplot as plt
                plt.switch_backend('TkAgg')
            except ModuleNotFoundError:
                self.report({'ERROR'}, "Cannot run evaluations: Blender could not find matplotlib")
                return {"FINISHED"}

        # setup timer
        t = Timer()
        t.logging_enabled = True

        max_iters = 20
        eps = 0.001
        max_points = 1000

        suzanne = {
            "title": "Suzanne",
            "collection": "Suzanne",
            "solvers": [{'name': f'$k$={k}',
                         'marker': '.',
                         'solver': ICP(max_iterations=max_iters,
                                       eps=eps, max_points=max_points,
                                       k=k)}
                        for k in [1, 1.5, 2, 3, 10, 11]],
            "folder": 'evaluation/suzanne',
            "render_initial_state": True,
            "render_final_states": False,
        }

        gdp_planes = {
            "title": "GDP",
            "collection": "GDP",
            "solvers": [{'name': f'{ss}',
                         'marker': '.',
                         'solver': ICP(max_iterations=20, eps=eps, max_points=max_points, k=2.5,
                                       point_to_plane=True,
                                       sampling_strategy=ss)}
                        for ss in ['RANDOM_POINT', 'NORMAL']],
            'folder': 'evaluation/gdp-planes',
            "render_initial_state": True,
            "render_final_states": True,
        }

        cubes = {
            "title": "Cubes",
            "collection": "cubes",
            "solvers": [{'name': f'{"Point to Plane" if is_point_to_plane else "Point to Point"}',
                         'marker': '.',
                         'solver': ICP(max_iterations=max_iters, eps=eps, max_points=max_points, k=2.5,
                                       point_to_plane=is_point_to_plane)}
                        for is_point_to_plane in [True, False]],
            'folder': 'evaluation/cubes',
            "render_initial_state": True,
            "render_final_states": True,
        }

        bunnies = {
            "title": "Bunnies",
            "collection": "bunnies",
            "solvers": [{'name': f'{"Point to Plane" if is_point_to_plane else "Point to Point"}',
                         'marker': '.',
                         'solver': ICP(max_iterations=max_iters, eps=eps, max_points=max_points, k=2.5,
                                       point_to_plane=is_point_to_plane)}
                        for is_point_to_plane in [True, False]],
            'folder': 'evaluation/bunnies/',
            "render_initial_state": True,
            "render_final_states": True,
        }

        experiments = [
            suzanne
        ]

        for experiment in experiments:

            # create folder for experiment output
            experiment_folder = pathlib.Path(experiment['folder'])
            if not experiment_folder.exists():
                experiment_folder.mkdir()

            # get experiment collection
            evaluation_coll = bpy.data.collections[self.eval_collection_name]
            experiment_coll = evaluation_coll.children[experiment["collection"]]

            # get objects for particular experiment
            fixed = get_first_by_regex(experiment_coll.all_objects, 'fixed')
            moving = get_first_by_regex(experiment_coll.all_objects, 'moving')
            target = get_first_by_regex(experiment_coll.all_objects, 'target')
            camera = get_first_by_regex(experiment_coll.all_objects, 'cam')

            # if rendering, setup eevee
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
            if camera and experiment['render_initial_state']:
                scene.render.filepath = str(experiment_folder / 'original.png')
                bpy.ops.render.render(write_still=True)

            # save original transform of moving object
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
                if camera and experiment['render_final_states']:
                    render_path = str(experiment_folder / to_filename(entry['name']))
                    scene.render.filepath = render_path
                    bpy.ops.render.render(write_still=True)

                # reset transform of object
                moving.matrix_world = original_transform

            # style convergence plot
            plt.legend()
            plt.title(experiment["title"])
            plt.xlabel('time (seconds)')
            plt.ylabel('RMSE')
            plt.savefig(str(experiment_folder / 'plot.pdf'))
            plt.cla()
            plt.clf()

        return {'FINISHED'}
