from meshutil import *
import numpy as np


class LaplaceSmoothImplicitOperator(bpy.types.Operator):
    bl_idname = "object.laplacesmoothimplicitop"
    bl_label = "GDP Laplace Smooth Implicit"
    bl_options = {'REGISTER', 'UNDO'}

    n_iters: bpy.props.IntProperty('Num Iterations', default=1, min=0, max=10)
    step_size: bpy.props.FloatProperty('Step Size', default=0.1, min=0, max=1)

    def execute(self, context):
        # ensure single object is selected
        if len(bpy.context.selected_objects) != 1:
            self.report({'ERROR'}, "Select a single object to deform")
            return {'CANCELLED'}
        obj = bpy.context.selected_objects[0]

        # get editable mesh
        bpy.ops.object.mode_set(mode='EDIT')
        bm = bmesh.from_edit_mesh(obj.data)

        for _ in range(self.n_iters):
            laplacian = mesh_laplacian(bm)
            vx, vy, vz = to_vxvyvz(bm, dims=[0, 1, 2])

            # solve linear system
            lhs = np.eye(len(vx)) + self.step_size * laplacian
            vx1 = np.linalg.solve(lhs, vx)
            vy1 = np.linalg.solve(lhs, vy)
            vz1 = np.linalg.solve(lhs, vz)

            # set vertex coordinates
            for v_i, v in enumerate(bm.verts):
                v.co.x = vx1[v_i]
                v.co.y = vy1[v_i]
                v.co.z = vz1[v_i]

        return {'FINISHED'}
