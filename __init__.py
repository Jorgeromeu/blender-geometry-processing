import subprocess
import sys

# Install scipy in blender
subprocess.check_call([sys.executable, "-m", "pip", "install", "scipy"])

from .BoundaryLoops import *
from .ComputeGenus import *
from .ConnectedComponentsOp import *
from .DeformationOperator import *
from .ICPOperator import *
from .VolumeOperator import *

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

classes = [ComputeGenus, ConnectedComponentsOp, VolumeOperator, BoundaryLoopsOp, ICPOperator, DeformationOp,
           TranslateVertexOperator]

def register():
    print('gdp-addon registered')
    for c in classes:
        bpy.utils.register_class(c)

    bpy.types.VIEW3D_MT_object.append(lambda self, context: self.layout.operator(ComputeGenus.bl_idname))
    bpy.types.VIEW3D_MT_object.append(lambda self, context: self.layout.operator(ConnectedComponentsOp.bl_idname))
    bpy.types.VIEW3D_MT_object.append(lambda self, context: self.layout.operator(VolumeOperator.bl_idname))
    bpy.types.VIEW3D_MT_object.append(lambda self, context: self.layout.operator(BoundaryLoopsOp.bl_idname))
    bpy.types.VIEW3D_MT_object.append(lambda self, context: self.layout.operator(ICPOperator.bl_idname))
    bpy.types.VIEW3D_MT_object.append(lambda self, context: self.layout.operator(DeformationOp.bl_idname))
    bpy.types.VIEW3D_MT_object.append(lambda self, context: self.layout.operator(TranslateVertexOperator.bl_idname))

    # # register all operators
    # for op in object_ops:
    #     bpy.types.VIEW3D_MT_object.append(lambda self, ctx: self.layout.operator(op.bl_idname))

def unregister():
    print('gdp-addon unregistered')
    for c in classes:
        bpy.utils.unregister_class(c)
