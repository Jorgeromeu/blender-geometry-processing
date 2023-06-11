import json
from pathlib import *

from icputil import *
from timer import Timer

def to_filename(s: str) -> str:
    return s.lower().replace(' ', '-')

def uniquify_dir(path: Path):
    parent = path.parent
    name = path.name

    counter = 1
    while path.exists():
        path = parent / f'{name}_{counter}'
        counter += 1

    return path

class EvaluationOperator(bpy.types.Operator):
    bl_idname = "object.evaluation"
    bl_label = "Evaluation"
    bl_options = {'REGISTER', 'UNDO'}

    # all experiments should be placed as sub-collections of this collection
    eval_collection_name = 'Evaluation'

    # folder to place all evaluation results
    eval_folder = pathlib.Path('evaluation')

    def execute(self, context):

        # setup timer
        t = Timer()
        t.logging_enabled = True

        max_iters = 35
        eps = 0.001
        max_points = 1000

        k_rejection_rabbits_ez = {
            "name": 'k_rejection_rabbits_ez',
            "collection": "rabbits_ez",
            "solvers": [{'name': f'$k$={k}',
                         'solver': ICP(max_iterations=max_iters,
                                       eps=0.0, max_points=1000, k=k)}
                        for k in reversed([1, 1.5, 2, 2., 3, 3.5, 10000])],
            "render_initial_state": True,
            "render_final_states": True,
        }

        k_rejection_rabbits_mid = k_rejection_rabbits_ez.copy()
        k_rejection_rabbits_mid['name'] = 'k_rejection_rabbits_mid'
        k_rejection_rabbits_mid['collection'] = 'rabbits_mid'

        k_rejection_rabbits_hard = k_rejection_rabbits_ez.copy()
        k_rejection_rabbits_hard['name'] = 'k_rejection_rabbits_hard'
        k_rejection_rabbits_hard['collection'] = 'rabbits_hard'

        gdp_sampling = {
            "collection": "GDP",
            "name": 'gdp_sampling',
            "solvers": [{'name': f'{sampling_strat} - {"Point to Plane" if is_point_to_plane else "Point to Point"}',
                         'solver': ICP(max_iterations=20, eps=0, max_points=max_points, rejection_criterion='NONE',
                                       point_to_plane=is_point_to_plane,
                                       sampling_strategy=sampling_strat)}
                        for sampling_strat in ['RANDOM_POINT', 'NORMAL', 'STRATIFIED_NORMAL'] for is_point_to_plane in
                        [True, False]],
            "render_initial_state": True,
            "render_final_states": True,
        }

        bunnies_point_v_plane = {
            "name": 'bunnies_point_v_plane',
            "collection": "bunnies",
            "solvers": [{'name': f'{"Point to Plane" if is_point_to_plane else "Point to Point"}',
                         'solver': ICP(max_iterations=50, eps=0.00, max_points=max_points, rejection_criterion='NONE',
                                       point_to_plane=is_point_to_plane)}
                        for is_point_to_plane in [True, False]],
            "render_initial_state": True,
            "render_final_states": True,
        }

        bunnies_weighting = {
            'name': 'bunnies_weighting',
            'collection': 'bunnies',
            "solvers": [{'name': weight_strat.lower().replace('_', ' '),
                         'solver': ICP(max_iterations=20, eps=0, max_points=max_points,
                                       weighting_strategy=weight_strat)}
                        for weight_strat in ['NORMAL_SIMILARITY', 'DISTANCE', 'NONE']],
            "render_initial_state": True,
            "render_final_states": True,
        }

        bunnies_matching = {
            'name': 'bunnies_matching',
            'collection': 'bunnies',
            "solvers": [{'name': matching_strat.lower().replace('_', ' '),
                         'solver': ICP(max_iterations=35, eps=0, max_points=max_points, rejection_criterion='NONE',
                                       weighting_strategy=matching_strat)}
                        for matching_strat in ['EUCLIDEAN', 'NORMAL_WEIGHTED']],
            "render_initial_state": True,
            "render_final_states": True,
        }

        normal_rejection_rabbits_ez = {
            "name": 'normal_rejection_rabbits_ez',
            "collection": "rabbits_ez",
            "solvers": [{'name': f'thresh={thresh}',
                         'solver': ICP(max_iterations=40,
                                       rejection_criterion='DISSIMILAR_NORMALS',
                                       eps=0.0, max_points=1000, normal_dissimilarity_thresh=thresh)}
                        for thresh in [0, 0.1, 0.2, 0.3, -1000]],
            "render_initial_state": True,
            "render_final_states": True,
        }

        normal_rejection_rabbits_mid = normal_rejection_rabbits_ez.copy()
        normal_rejection_rabbits_mid['name'] = 'normal_rejection_rabbits_mid'
        normal_rejection_rabbits_mid['collection'] = 'rabbits_mid'

        normal_rejection_rabbits_hard = normal_rejection_rabbits_ez.copy()
        normal_rejection_rabbits_hard['name'] = 'normal_rejection_rabbits_hard'
        normal_rejection_rabbits_hard['collection'] = 'rabbits_hard'

        experiments = [
            normal_rejection_rabbits_mid,
            normal_rejection_rabbits_hard
        ]

        for experiment in experiments:

            # create folder for experiment output
            experiment_folder = self.eval_folder / to_filename(experiment['name'])
            if not experiment_folder.exists():
                experiment_folder.mkdir()
            run_folder = uniquify_dir(experiment_folder / 'run')
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
                scene.render.filepath = str(run_folder / 'original.png')
                bpy.ops.render.render(write_still=True)

            # save original transform of moving object
            original_transform = moving.matrix_world.copy()

            # for each entry, store the results of experiment
            experiment_results = {}

            for entry in experiment["solvers"]:

                # call the ICP solver, with error tracing
                solver = entry['solver']
                solver.evaluation_object = target
                t.start()
                solver.icp(moving, fixed)
                t.stop(entry['name'])

                # save results of experiment
                experiment_results[entry['name']] = {
                    'times': [t for (_, t) in solver.errors],
                    'errors': [err for (err, _) in solver.errors],
                    'num_rejected': solver.num_rejected
                }

                # render result after running ICP
                if camera and experiment['render_final_states']:
                    render_path = str(run_folder / to_filename(entry['name']))
                    scene.render.filepath = render_path
                    bpy.ops.render.render(write_still=True)

                # reset transform of object
                moving.matrix_world = original_transform

                # save experiment results to json, at each iteration
                experiment_results_file = run_folder / 'results.json'
                experiment_results_file.touch()
                print(experiment_results)
                with open(experiment_results_file, 'w') as fp:
                    json.dump(experiment_results, fp)

        return {'FINISHED'}
