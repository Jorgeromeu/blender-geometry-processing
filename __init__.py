import subprocess
import sys

from NumericalTest import *
from .BoundaryLoops import *
from .BrushOperator import *
from .ComputeDifferentialCoordsOp import *
from .ComputeGenus import *
from .ConnectedComponentsOp import *
from .DeformationOperator import *
from .ICPOperator import *
from .LaplaceSmooth import LaplaceSmoothOperator
from .LaplaceSmoothImplicit import *
from .SmoothingBrushOperator import SmoothingBrushOp
from .VolumeOperator import *

subprocess.check_call([sys.executable, "-m", "pip", "install", "scipy"])

bl_info = {
    "name": "Geometric Data Processing",
    "author": "Group16",
    "description": "",
    "blender": (3, 5, 0),
    "version": (0, 0, 2),
    "location": "",
    "warning": "",
    "category": "Generic"
}

classes = [
    # assignment 1 things
    ComputeGenus, ConnectedComponentsOp, VolumeOperator, BoundaryLoopsOp, ICPOperator,

    # constraint deformation
    ConstraintDeformationOp,

    # Gradient brushes
    BrushOperator, MatrixBrushOperator,

    # Laplacian smoothing
    LaplaceSmoothOperator, LaplaceSmoothImplicitOperator, SmoothingBrushOp,

    # For testing
    ComputeDifferentialCoordsOp, NumericalTestOp,
]

def register():
    print('gdp-addon registered')
    for c in classes:
        bpy.utils.register_class(c)

    bpy.types.VIEW3D_MT_object.append(lambda self, context: self.layout.operator(ComputeGenus.bl_idname))
    bpy.types.VIEW3D_MT_object.append(lambda self, context: self.layout.operator(ConnectedComponentsOp.bl_idname))
    bpy.types.VIEW3D_MT_object.append(lambda self, context: self.layout.operator(VolumeOperator.bl_idname))
    bpy.types.VIEW3D_MT_object.append(lambda self, context: self.layout.operator(BoundaryLoopsOp.bl_idname))
    bpy.types.VIEW3D_MT_object.append(lambda self, context: self.layout.operator(ICPOperator.bl_idname))
    bpy.types.VIEW3D_MT_object.append(lambda self, context: self.layout.operator(ComputeDifferentialCoordsOp.bl_idname))
    bpy.types.VIEW3D_MT_object.append(lambda self, context: self.layout.operator(LaplaceSmoothOperator.bl_idname))
    bpy.types.VIEW3D_MT_object.append(lambda self, context: self.layout.operator(ConstraintDeformationOp.bl_idname))
    bpy.types.VIEW3D_MT_object.append(lambda self, context: self.layout.operator(NumericalTestOp.bl_idname))
    bpy.types.VIEW3D_MT_object.append(
        lambda self, context: self.layout.operator(LaplaceSmoothImplicitOperator.bl_idname))
    bpy.types.VIEW3D_MT_edit_mesh.append(lambda self, context: self.layout.operator(BrushOperator.bl_idname))
    bpy.types.VIEW3D_MT_edit_mesh.append(lambda self, context: self.layout.operator(MatrixBrushOperator.bl_idname))
    bpy.types.VIEW3D_MT_edit_mesh.append(lambda self, context: self.layout.operator(BrushOperator.bl_idname))
    bpy.types.VIEW3D_MT_edit_mesh.append(lambda self, context: self.layout.operator(SmoothingBrushOp.bl_idname))

def unregister():
    print('gdp-addon unregistered')
    for c in classes:
        bpy.utils.unregister_class(c)
