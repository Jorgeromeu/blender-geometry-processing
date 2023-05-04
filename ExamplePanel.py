import bpy

class ExamplePanel(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_idname = 'VIEW3D_PT_geometric_data_processing'
    bl_label = 'Geometric Data Processing'

    def draw(self, context):
        layout = self.layout

        layout.label(text='Hello World')

        box = layout.box()
        box.label(text="Abc")

