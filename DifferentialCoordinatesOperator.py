import bpy
import bmesh
from meshutil import global_gradient_matrix


class DifferentialCoordinatesOp(bpy.types.Operator):
    bl_idname = "object.differentialcoordinates"
    bl_label = "GDP Differential Coordinates"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        # ensure single object is selected
        if len(bpy.context.selected_objects) != 1:
            self.report({'ERROR'}, "Select a single object to deform")
            return {'CANCELLED'}
        obj = bpy.context.selected_objects[0]

        # get editable mesh
        bpy.ops.object.mode_set(mode='EDIT')
        mesh = bmesh.from_edit_mesh(obj.data)

        global_gradient_matrix(mesh)

        return {'FINISHED'}
