import re

import bpy
import numpy as np
from bmesh.types import BMesh
from mathutils import Matrix, Vector

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

def get_or_else(d: dict, key, other):
    return other if d.get(key) is None else d.get(key)

def get_first_by_regex(r: str, d=None):
    if d is None:
        d = bpy.data.objects

    for (k, v) in d.items():
        if re.match(r, k):
            return v
    return None

def linear_map(data):
    mn = min(data)
    mx = max(data)
    return (data - mn) / (mx - mn)

def set_float_attrib(obj, name: str, domain: str, data: np.ndarray, normalize=True):
    # if no attribute exists, make it
    if not obj.data.attributes.get(name):
        obj.data.attributes.new(name, type='FLOAT', domain=domain)

    if normalize:
        data = linear_map(data)

    obj.data.attributes[name].data.foreach_set("value", data)

def set_vector_attrib(obj, name: str, domain: str, vectors: np.ndarray):
    # if no attribute exists, make it
    if not obj.data.attributes.get(name):
        obj.data.attributes.new(name, type='FLOAT_VECTOR', domain=domain)

    for i, vector in enumerate(vectors):
        obj.data.attributes[name].data[i].vector = Vector(vector)

def set_vector_face_attrib(obj, name: str, vectors):
    set_vector_attrib(obj, name, 'FACE', vectors)

def set_vector_vertex_attrib(obj, name: str, vectors):
    set_vector_attrib(obj, name, 'POINT', vectors)

def set_float_vertex_attrib(obj, name: str, data: np.ndarray, normalize=True):
    set_float_attrib(obj, name, 'POINT', data, normalize)

def set_float_face_attrib(obj, name: str, data: np.ndarray, normalize=True):
    set_float_attrib(obj, name, 'FACE', data, normalize)
