import bmesh

from .meshutil import *

class VolumeOperator(bpy.types.Operator):
    """Print genus of mesh"""
    bl_idname = "object.computevolume"
    bl_label = "Compute Volume"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = get_selected_object(context)

        if obj is None:
            self.report({'ERROR'}, "No object selected!")
            return {'CANCELLED'}

        mesh = obj.data
        bm = bmesh.new()
        bm.from_mesh(mesh)

        # ensure mesh is triangulated
        bmesh.ops.triangulate(bm, faces=bm.faces[:])

        total_volume = compute_mesh_volume(bm)
        self.report({'INFO'}, f'Mesh has volume {total_volume}')

        bm.free()

        return {'FINISHED'}
