import pathlib
import shutil

import bpy.props

from ..meshutil import *

class RenderCollection(bpy.types.Operator):
    bl_idname = "object.rendercollection"
    bl_label = "GDP Render Collection"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        collection_name = bpy.context.collection.name

        renders_path = pathlib.Path(collection_name)

        if renders_path.exists():
            shutil.rmtree(renders_path)
        renders_path.mkdir()

        collection = bpy.data.collections[collection_name]

        scene = bpy.context.scene

        meshes = [ob for ob in collection.all_objects if ob.type == 'MESH']

        initial_hide_render = {}
        initial_transform = {}

        # initially hide all objects, and move them to center
        for ob in meshes:
            initial_hide_render[ob] = ob.hide_render
            initial_transform[ob] = ob.matrix_world.copy()

            ob.hide_render = True
            ob.matrix_world = Matrix.Identity(4)

        # render each mesh individually
        for ob in meshes:
            ob.hide_render = False
            scene.render.filepath = str(renders_path / f'{ob.name}.png')
            bpy.ops.render.render(write_still=True)
            ob.hide_render = True

        # reset objects
        for ob in meshes:
            ob.hide_render = initial_hide_render[ob]
            ob.matrix_world = initial_transform[ob]

        return {'FINISHED'}
