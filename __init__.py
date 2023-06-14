import subprocess
import sys

from .BoundaryLoops import *
from .ComputeGenus import *
from .ConnectedComponentsOp import *
from .DeformationOperator import *
from .ICPOperator import *
from .LaplacianBrushOperator import *
from .ScaleRotateGradientBrushOp import *
from .SmoothingBrushOperator import SmoothLaplacianOp
from .VolumeOperator import *
from .debug_operators.AttributeStatsOp import *
from .debug_operators.ComputeDifferentialCoordsOp import *
from .debug_operators.NumericalTest import *
from .debug_operators.RenderCollection import *

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
    ScaleRotateGradientBrushOp, MatrixGradientBrushOp,

    # Laplace coordinates brush
    ScaleRotateLaplacianBrush, MatrixLaplacianBrushOp,

    # Laplacian smoothing
    SmoothLaplacianOp,

    # For testing
    ComputeDifferentialCoordsOp, NumericalTestOp, AttributeStatsOp, RenderCollection
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
    bpy.types.VIEW3D_MT_edit_mesh.append(
        lambda self, context: self.layout.operator(ScaleRotateGradientBrushOp.bl_idname))
    bpy.types.VIEW3D_MT_edit_mesh.append(lambda self, context: self.layout.operator(MatrixGradientBrushOp.bl_idname))
    bpy.types.VIEW3D_MT_edit_mesh.append(
        lambda self, context: self.layout.operator(ScaleRotateLaplacianBrush.bl_idname))
    bpy.types.VIEW3D_MT_edit_mesh.append(lambda self, context: self.layout.operator(MatrixGradientBrushOp.bl_idname))

    # Testing operators
    bpy.types.VIEW3D_MT_object.append(lambda self, context: self.layout.operator(NumericalTestOp.bl_idname))
    bpy.types.VIEW3D_MT_object.append(lambda self, context: self.layout.operator(ComputeDifferentialCoordsOp.bl_idname))
    bpy.types.VIEW3D_MT_object.append(lambda self, context: self.layout.operator(AttributeStatsOp.bl_idname))
    bpy.types.VIEW3D_MT_object.append(lambda self, context: self.layout.operator(RenderCollection.bl_idname))
    bpy.types.VIEW3D_PT_collections.append(lambda self, context: self.layout.operator(RenderCollection.bl_idname))

def unregister():
    print('gdp-addon unregistered')
    for c in classes:
        bpy.utils.unregister_class(c)
