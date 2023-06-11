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

        return {'FINISHED'}

    def draw(self, context):
        layout: bpy.types.UILayout = self.layout.grid_flow()
        col = layout.column()
        col.prop(self, 'smoothing_method')
        if self.smoothing_method == "ITERATED_AVERAGING":
            col.prop(self, 'n_iters')
            col.prop(self, 'step_size')
