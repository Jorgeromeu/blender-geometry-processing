import subprocess
import sys

from .BoundaryLoops import *
from .BrushOperator import BrushOperator, MatrixBrushOperator
from .ComputeGenus import *
from .ConnectedComponentsOp import *
from .DeformationOperator import *
from .DifferentialCoordinatesOperator import *
from .HeatmapOperator import *
from .ICPOperator import *
from .LaplaceSmooth import LaplaceSmoothOperator
from .LaplacianBrushOperator import LaplacianBrushOperator
from .SmoothingBrushOperator import IterativeSmoothingBrushOperator
from .VolumeOperator import *
from .LaplaceSmoothImplicit import LaplaceSmoothImplicitOperator

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

classes = [ComputeGenus, ConnectedComponentsOp, VolumeOperator,
           BoundaryLoopsOp, ICPOperator, DeformationOp,
           TranslateVertexOperator, DifferentialCoordinatesOp,
           HeatmapOperator, BrushOperator, LaplacianBrushOperator,
           LaplaceSmoothOperator, MatrixBrushOperator, IterativeSmoothingBrushOperator, LaplaceSmoothImplicitOperator]


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
    bpy.types.VIEW3D_MT_object.append(lambda self, context: self.layout.operator(DifferentialCoordinatesOp.bl_idname))
    bpy.types.VIEW3D_MT_object.append(lambda self, context: self.layout.operator(HeatmapOperator.bl_idname))
    bpy.types.VIEW3D_MT_object.append(lambda self, context: self.layout.operator(LaplaceSmoothOperator.bl_idname))
    bpy.types.VIEW3D_MT_object.append(
        lambda self, context: self.layout.operator(LaplaceSmoothImplicitOperator.bl_idname))
    bpy.types.VIEW3D_MT_edit_mesh.append(lambda self, context: self.layout.operator(BrushOperator.bl_idname))
    bpy.types.VIEW3D_MT_edit_mesh.append(lambda self, context: self.layout.operator(MatrixBrushOperator.bl_idname))
    bpy.types.VIEW3D_MT_edit_mesh.append(lambda self, context: self.layout.operator(BrushOperator.bl_idname))
    bpy.types.VIEW3D_MT_edit_mesh.append(lambda self, context: self.layout.operator(LaplacianBrushOperator.bl_idname))
    bpy.types.VIEW3D_MT_edit_mesh.append(
        lambda self, context: self.layout.operator(IterativeSmoothingBrushOperator.bl_idname))


def unregister():
    print('gdp-addon unregistered')
    for c in classes:
        bpy.utils.unregister_class(c)
