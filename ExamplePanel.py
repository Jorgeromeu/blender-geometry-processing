import bpy

class ExamplePanel(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_idname = 'example_panel'
    bl_label = 'Example Panel'

    def draw(self, context):
        self.layout.label(text='Hello World')

