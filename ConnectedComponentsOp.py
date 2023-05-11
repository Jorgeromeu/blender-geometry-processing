import bmesh

from bpyutil import *
from meshutil import compute_connected_components

class ConnectedComponentsOp(bpy.types.Operator):
    """Print genus of mesh"""
    bl_idname = "object.conectedcomponents"
    bl_label = "Connected Components"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = get_selected_object(context)

        if obj is None:
            self.report({'ERROR'}, "No object selected!")

        mesh = obj.data
        bm = bmesh.new()
        bm.from_mesh(mesh)

        print('connected components', compute_connected_components(bm))

        bm.to_mesh(mesh)
        bm.free()

        return {'FINISHED'}
