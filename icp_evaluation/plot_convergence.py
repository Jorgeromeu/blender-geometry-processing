import json
import pathlib

import matplotlib.pyplot as plt

plt.switch_backend('TkAgg')
plt.rcParams.update({
    "text.usetex": True,
    "font.family": "serif",
})

# REJECTION: k
experiments = [('k_rejection_rabbits_ez', 'run_1', 'Rabbits: Easy'),
               ('k_rejection_rabbits_mid', 'run', 'Rabbits: Medium'),
               ('k_rejection_rabbits_hard', 'run', 'Rabbits: Hard')]

# REJECTION_NORMAL
experiments += [('normal_rejection_rabbits_ez', 'run', 'Rabbits: Easy'),
                ('normal_rejection_rabbits_mid', 'run_1', 'Rabbits: Medium'),
                ('normal_rejection_rabbits_hard', 'run_1', 'Rabbits: Hard')]

# BUNNIES POINT-v-PLANE
experiments += [('bunnies_point_v_plane', 'run', 'Bunnies: Comparison of Point-to-Point and Point-to-Plane')]

# GDP, sampling
experiments += [('gdp_sampling', 'run_1', 'GDP planes: Comparing Normal sampling and Point sampling')]

# Weighting
experiments += [('bunnies_weighting', 'run', 'Bunnies: Comparing point-pair weighting')]

# Matching
experiments += [('bunnies_matching', 'run_1', 'Bunnies: Comparing point-matching criteria')]

for experiment_dir, run, plot_title in experiments:

    run_dir = pathlib.Path(f'{experiment_dir}/{run}')
    results_path = run_dir / 'results.json'

    with open(results_path, 'r') as fp:
        data = json.load(fp)

    # reverse items for consistency
    items = data.items() if experiment_dir != 'k_rejection_rabbits_hard' else reversed(data.items())

    for (name, results) in items:

        times = results['times']
        errs = results['errors']
        iters = range(len(errs))

        if experiment_dir == 'bunnies_point_v_plane':
            times, errs, iters = (seq[0:17] for seq in (times, errs, iters))

        if name == "$k$=10000" or name == "thresh=-1000":
            name = 'No rejection'

        if experiment_dir == 'bunnies_weighting' and name == 'normal similarity':
            continue

        if experiment_dir == 'bunnies_weighting' and name == 'distance':
            name = 'Distance weighted'

        if experiment_dir == 'bunnies_weighting' and name == 'none':
            name = 'No weighting'

        if experiment_dir == 'bunnies_matching' and name == 'distance':
            name = 'Distance weighted'

        if experiment_dir == 'bunnies_weighting' and name == 'none':
            name = 'No weighting'

        if experiment_dir == 'bunnies_matching' and name == 'euclidean':
            name = 'Euclidean distance'

        if experiment_dir == 'bunnies_matching' and name == 'normal weighted':
            name = 'Normal weighted distance'

        if experiment_dir == 'gdp_sampling':
            sampling_strat, min_fun = name.split(' - ')
            sampling_strat.strip()

            if sampling_strat == 'RANDOM_POINT':
                color = 'tab:blue'
            elif sampling_strat == 'NORMAL':
                color = 'tab:orange'
            elif sampling_strat == 'STRATIFIED_NORMAL':
                color = 'tab:green'

            sampling_strat = sampling_strat.lower().replace('_', ' ')
            name = f'{sampling_strat} sampling, {min_fun}'

            if min_fun == 'Point to Plane':
                marker = 's'
            else:
                marker = '.'

            plt.plot(iters, errs, marker=marker, color=color, label=name)

        else:
            plt.plot(iters, errs, marker='.', label=name)

    # save the plot
    plt.title(plot_title)
    plt.ylabel('RMSD')
    plt.xlabel('Iterations')
    plt.legend()
    plt.xticks(range(0, len(iters), 2))
    fig = plt.gcf()
    fig.set_size_inches(7.5, 4)
    plt.savefig(experiment_dir + '/plot.pdf')
    plt.cla()
    plt.clf()
