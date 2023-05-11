import bmesh
from icputil import *
import bpy

from bpyutil import *


class BasicICP(bpy.types.Operator):
    """Print genus of mesh"""
    bl_idname = "object.basicicp"
    bl_label = "Basic ICP"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        objs = bpy.context.selected_objects

        if len(objs) != 2:
            self.report({'ERROR'}, "Must select two objects")

        obj1, obj2 = objs

        enter_editmode()
        mesh1 = bmesh.from_edit_mesh(obj1.data)
        mesh2 = bmesh.from_edit_mesh(obj2.data)

        basic_registration(mesh1, mesh2, 100)

        return {'FINISHED'}