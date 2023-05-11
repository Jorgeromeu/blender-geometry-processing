import bmesh

from .bpyutil import *
from .meshutil import compute_boundary_loops

class BoundaryLoopsOp(bpy.types.Operator):
    """Compute Boundary Loops of mesh"""
    bl_idname = "object.boundaryloops"
    bl_label = "Compute Boundary Loops"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = get_selected_object(context)

        if obj is None:
            self.report({'ERROR'}, "No object selected!")
            return {'CANCELLED'}

        bpy.ops.object.mode_set(mode='EDIT')
        mesh = bmesh.from_edit_mesh(obj.data)

        n_boundary_loops = compute_boundary_loops(mesh)

        self.report({'INFO'}, f'{n_boundary_loops} boundary loops')

        return {'FINISHED'}
