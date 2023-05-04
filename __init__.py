from ComputeGenus import *
from ConnectedComponentsOp import *
from ExampleOperator import *
from ExamplePanel import *

bl_info = {
    "name": "Geometric Data Processing",
    "author": "Group16",
    "description": "",
    "blender": (3, 5, 0),
    "version": (0, 0, 1),
    "location": "",
    "warning": "",
    "category": "Generic"
}

classes = [ExampleOperator, ComputeGenus, ConnectedComponentsOp, ExamplePanel]

def menu_func(self, context):
    self.layout.operator(ExampleOperator.bl_idname)

def register():
    print('registered')
    for c in classes:
        bpy.utils.register_class(c)

    bpy.types.VIEW3D_MT_object.append(menu_func)  # Adds the new operator to an existing menu.
    bpy.types.VIEW3D_MT_object.append(lambda self, context: self.layout.operator(ComputeGenus.bl_idname))
    bpy.types.VIEW3D_MT_object.append(lambda self, context: self.layout.operator(ConnectedComponentsOp.bl_idname))

def unregister():
    print('unregistered')
    for c in classes:
        bpy.utils.unregister_class(c)
