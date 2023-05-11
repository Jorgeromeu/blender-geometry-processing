import bpy
from bmesh.types import BMesh

def get_selected_object(ctx: bpy.context) -> bpy.types.Object:
    return bpy.context.object

def enter_editmode():
    bpy.ops.object.mode_set(mode='EDIT')

def enter_object_mode():
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