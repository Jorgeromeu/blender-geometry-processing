bl_info = {
    "name": "Geometric Data Procesing",
    "author": "Group16",
    "description": "",
    "blender": (3, 5, 0),
    "version": (0, 0, 1),
    "location": "",
    "warning": "",
    "category": "Generic"
}


import bpy

from .ObjectMoveX import *

# # from ObjectMoveX import ObjectMoveX
# from . import ObjectMoveX

def menu_func(self, context):
    self.layout.operator(ObjectMoveX.bl_idname)


def register():
    bpy.utils.register_class(ObjectMoveX)
    bpy.types.VIEW3D_MT_object.append(menu_func)  # Adds the new operator to an existing menu.


def unregister():
    bpy.utils.unregister_class(ObjectMoveX)

