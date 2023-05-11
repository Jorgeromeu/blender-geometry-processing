import bmesh

from bpyutil import *
from icputil import *

class BasicICP(bpy.types.Operator):
    """Print genus of mesh"""
    bl_idname = "object.basicicp"
    bl_label = "Basic ICP"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        objs = bpy.context.selected_objects

        if len(objs) != 2:
            self.report({'ERROR'}, "Must select two objects")

        obj_P, obj_Q = objs

        for i in range(10):
            enter_editmode()
            P = bmesh.from_edit_mesh(obj_P.data)
            Q = bmesh.from_edit_mesh(obj_Q.data)

            p_points = [obj_P.matrix_world @ p.co for p in P.verts]
            q_points = [obj_Q.matrix_world @ q.co for q in Q.verts]
            r_opt, t_opt = icp_step(p_points, q_points, 1, 100)
            enter_objectmode()
            rigid_transform(t_opt, r_opt, obj_P)

        return {'FINISHED'}
