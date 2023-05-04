import bpy

class ObjectMoveX(bpy.types.Operator):
    """My Object Moving Script"""  # Use this as a tooltip for menu items and buttons.
    bl_idname = "object.move_x"  # Unique identifier for buttons and menu items to reference.
    bl_label = "Move X by One"  # Display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # Enable undo for the operator.

    def execute(self, context):
        # The original script
        scene = context.scene
        obj = bpy.context.object
        if obj is None:
            self.report({'ERROR'}, "No object selected!")
        else:
            # for obj in scene.objects:
            obj.location.y -= 1

        return {'FINISHED'}
