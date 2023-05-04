import bmesh

from bpyutil import *
from meshutil import compute_num_boundary_loops

class BoundaryLoopsOp(bpy.types.Operator):
    """Print genus of mesh"""
    bl_idname = "object.boundaryloops"
    bl_label = "Boundary Loops"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = get_selected_object(context)

        if obj is None:
            self.report({'ERROR'}, "No object selected!")

        mesh = obj.data
        bm = bmesh.new()
        bm.from_mesh(mesh)

        print(compute_num_boundary_loops(bm))

        bm.free()

        return {'FINISHED'}
