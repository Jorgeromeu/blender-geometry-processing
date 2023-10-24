# Blender Geometry Processing

A collection of geometry processing algorithms implemented as a Blender addon:


[![video](https://github.com/Jorgeromeu/blender-geometry-processing/assets/40536127/525e1dc9-d2e6-4041-b6af-01b883cf4fc4)](https://www.youtube.com/watch?v=GvlJ_SaGOhw)

## Pycharm Setup instructions

1. Create a folder anywhere on your computer, with the following three empty folders:

```
addons/  modules/  startup/
```

2. Ensure this repo, is cloned in the `addons` folder
3. In blender, open preferences, and under `File Paths`, set the "Scripts path" to the folder created in step 1
4. Now to run the addon, run the script `start_blender.py`, if this does not work, change the blender path to wherever your blender is installed
5. On first run, open edit, preferences, addons, and enable the addon by searching for it. If preferences are saved, this will then persist among blender sessions
6. To reload the plugin, simply re-run the `start_blender.py` script, which will re-open blender with the new



