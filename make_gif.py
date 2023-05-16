import pathlib

import imageio

anim_folder = pathlib.Path('animation')
outfile = 'evaluation/icp.gif'

with imageio.get_writer(outfile) as writer:
    n_frames = len([f for f in anim_folder.iterdir()])
    for i in range(0, n_frames):
        image = imageio.imread(anim_folder / f'frame_{i}.png')
        writer.append_data(image)
