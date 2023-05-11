import bmesh
import bpy

import bpyutil
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

        bpy.ops.object.mode_set(mode='EDIT')
        mesh = bmesh.from_edit_mesh(obj.data)

        print('boundary loops', compute_num_boundary_loops(mesh))

        return {'FINISHED'}
