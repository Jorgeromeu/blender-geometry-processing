import bmesh

from .bpyutil import *
from .meshutil import compute_connected_components

class ConnectedComponentsOp(bpy.types.Operator):
    """Print number of connected components of mesh"""
    bl_idname = "object.conectedcomponents"
    bl_label = "Connected Components"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = get_selected_object(context)

        if obj is None:
            self.report({'ERROR'}, "No object selected!")
            return {'CANCELLED'}

        mesh = obj.data
        bm = bmesh.new()
        bm.from_mesh(mesh)

        n_components = compute_connected_components(bm)
        self.report({'INFO'}, f"Mesh has {n_components} connected components")

        bm.to_mesh(mesh)
        bm.free()

        return {'FINISHED'}
