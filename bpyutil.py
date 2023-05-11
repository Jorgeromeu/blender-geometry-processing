import bpy
import numpy as np
from bmesh.types import BMesh
from mathutils import Matrix


def get_selected_object(ctx: bpy.context) -> bpy.types.Object:
    return bpy.context.object

def enter_editmode():
    bpy.ops.object.mode_set(mode='EDIT')

def enter_objectmode():
    bpy.ops.object.mode_set(mode='OBJECT')

def clear_editmode_selection(bm: BMesh):
    for v in bm.verts:
        v.select = False

def switch_select_mode(type: str):
    bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type=type)

def invert_selection():
    bpy.ops.mesh.select_all(action='INVERT')

def update_viewports():
    for area in bpy.context.window.screen.areas:
        if area.type == 'VIEW_3D':
            area.tag_redraw()
    bpy.ops.wm.save_mainfile()

def rigid_transform(t: np.ndarray, r: np.ndarray, obj):

    """
    Transform an object according to a vector and rotation matrix
    :param t: translation vector
    :param r: 3x3 rotation matrix
    :param obj: the object to be transformed
    """

    translation_matrix = Matrix.Translation(t)
    rotation_matrix = np.eye(4)
    rotation_matrix[:3, :3] = r
    rotation_matrix = Matrix(rotation_matrix)
    transform_matrix = translation_matrix @ rotation_matrix
    obj.matrix_world = transform_matrix @ obj.matrix_world
