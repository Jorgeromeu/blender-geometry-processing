import numpy as np
from scipy.spatial.transform import Rotation as R

import visualdebug
from meshutil import *
from smoothing_utils import laplace_smoothing


class IterativeSmoothingBrushOperator(bpy.types.Operator):
    bl_idname = "object.iterativesmoothbrush"
    bl_label = "GDP Smoothing Brush"
    bl_options = {'REGISTER', 'UNDO'}

    smoothing_method: bpy.props.EnumProperty(
        name="Smoothing Method",
        description="Method used to smooth selected area",
        items=[
            ('ITERATED_AVERAGING', 'Iterative averaging', 'Laplace smoothing'),
            ('IMPLICIT_EULER', 'Semi-implicit Euler', 'Apply semi-implicit euler')
        ]
    )

    n_iters: bpy.props.IntProperty(name='Number of Iterations', default=1, min=0, max=10)
    step_size: bpy.props.FloatProperty(name='Step Size', default=0.1, min=0, max=1)

    def execute(self, context):
        # ensure single object is selected
        obj = bpy.context.selected_objects[0]

        # get editable mesh
        bpy.ops.object.mode_set(mode='EDIT')
        bm = bmesh.from_edit_mesh(obj.data)

        selected_vertex_indices = set([v.index for v in bm.verts if v.select])
        if self.smoothing_method == "ITERATED_AVERAGING":
            vx, vy, vz = laplace_smoothing(bm, self.n_iters, self.step_size)
            # set vertex coordinates
            for v_i, v in enumerate(bm.verts):
                if v_i in selected_vertex_indices:
                    v.co.x = vx[v_i]
                    v.co.y = vy[v_i]
                    v.co.z = vz[v_i]
        elif self.smoothing_method == "IMPLICIT_EULER":
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
                    if v_i in selected_vertex_indices:
                        v.co.x = vx1[v_i]
                        v.co.y = vy1[v_i]
                        v.co.z = vz1[v_i]

        return {'FINISHED'}

    def draw(self, context):
        layout: bpy.types.UILayout = self.layout.grid_flow()
        col = layout.column()
        col.prop(self, 'n_iters')
        col.prop(self, 'step_size')
        col.prop(self, 'smoothing_method')
