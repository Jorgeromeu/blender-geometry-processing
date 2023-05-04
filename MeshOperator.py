import bmesh
import bpy
import numpy as np

class TweakMeshOperator(bpy.types.Operator):
    """My Mesh editing Script"""
    bl_idname = "object.tweakmesh"
    bl_label = "Tweak Mesh"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        obj: bpy.types = bpy.context.object
        if obj is None:
            self.report({'ERROR'}, "No object selected!")

        mesh = obj.data

        bm = bmesh.new()
        bm.from_mesh(mesh)

        n_verts = len(list(bm.verts))
        n_edges = len(list(bm.edges))
        n_faces = len(list(bm.faces))

        genus = 1 - ((n_verts - n_edges + n_faces) / 2)
        # genus = int(genus)
        print(genus)

        bm.to_mesh(mesh)
        bm.free()

        return {'FINISHED'}
