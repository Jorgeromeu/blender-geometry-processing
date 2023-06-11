import subprocess
import sys

from debug_operators.ComputeDifferentialCoordsOp import *
from debug_operators.NumericalTest import *
from .BoundaryLoops import *
from .BrushOperator import *
from .ComputeGenus import *
from .ConnectedComponentsOp import *
from .DeformationOperator import *
from .ICPOperator import *
from .SmoothingBrushOperator import SmoothLaplacianOp
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
    SmoothLaplacianOp,

    # For testing
    ComputeDifferentialCoordsOp, NumericalTestOp,
]

def register():
    print('gdp-addon registered')
    for c in classes:
        bpy.utils.register_class(c)

    # Task 1
    bpy.types.VIEW3D_MT_object.append(lambda self, context: self.layout.operator(ComputeGenus.bl_idname))
    bpy.types.VIEW3D_MT_object.append(lambda self, context: self.layout.operator(ConnectedComponentsOp.bl_idname))
    bpy.types.VIEW3D_MT_object.append(lambda self, context: self.layout.operator(VolumeOperator.bl_idname))
    bpy.types.VIEW3D_MT_object.append(lambda self, context: self.layout.operator(BoundaryLoopsOp.bl_idname))
    bpy.types.VIEW3D_MT_object.append(lambda self, context: self.layout.operator(ICPOperator.bl_idname))

    # Deformation
    bpy.types.VIEW3D_MT_object.append(lambda self, context: self.layout.operator(ConstraintDeformationOp.bl_idname))

    # Smoothing
    bpy.types.VIEW3D_MT_object.append(lambda self, context: self.layout.operator(SmoothLaplacianOp.bl_idname))
    bpy.types.VIEW3D_MT_edit_mesh.append(lambda self, context: self.layout.operator(SmoothLaplacianOp.bl_idname))

    # Brushes
    bpy.types.VIEW3D_MT_edit_mesh.append(lambda self, context: self.layout.operator(BrushOperator.bl_idname))
    bpy.types.VIEW3D_MT_edit_mesh.append(lambda self, context: self.layout.operator(MatrixBrushOperator.bl_idname))

    # Testing operators
    bpy.types.VIEW3D_MT_object.append(lambda self, context: self.layout.operator(NumericalTestOp.bl_idname))
    bpy.types.VIEW3D_MT_object.append(lambda self, context: self.layout.operator(ComputeDifferentialCoordsOp.bl_idname))

def unregister():
    print('gdp-addon unregistered')
    for c in classes:
        bpy.utils.unregister_class(c)
