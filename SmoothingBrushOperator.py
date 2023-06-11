from meshutil import *
from smoothing_utils import iterative_laplace_smoothing, implicit_laplace_smoothing

class SmoothLaplacianOp(bpy.types.Operator):
    bl_idname = "object.smoothlaplacianop"
    bl_label = "GDP Smooth Laplacian"
    bl_options = {'REGISTER', 'UNDO'}

    smoothing_method: bpy.props.EnumProperty(
        name="Smoothing Method",
        description="Method used to smooth selected area",
        items=[
            ('ITERATED_AVERAGING', 'Iterative averaging', 'Laplace smoothing'),
            ('IMPLICIT_EULER', 'Semi-implicit Euler', 'Apply semi-implicit euler')
        ]
    )

    n_iters: bpy.props.IntProperty(name='Number of Iterations', default=1, min=0, max=500)
    step_size: bpy.props.FloatProperty(name='Step Size', default=0.1, min=0, max=10000)

    laplacian: sp.csr_matrix

    def invoke(self, context, event):

        # ensure single object is selected
        obj = bpy.context.selected_objects[0]

        # compute laplacian before executing
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        self.laplacian = mesh_laplacian(bm)
        bm.free()

        return self.execute(context)

    def perform_smoothing(self, obj, bm):

        """
        Smooth the mesh, depending on the selected method
        """

        if self.smoothing_method == "ITERATED_AVERAGING":
            vx, vy, vz = iterative_laplace_smoothing(bm, self.n_iters, self.step_size, self.laplacian)
            return vx, vy, vz

        elif self.smoothing_method == "IMPLICIT_EULER":

            bm_copy = bmesh.new()
            bm_copy.from_mesh(obj.data)
            vx, vy, vz = implicit_laplace_smoothing(bm_copy, self.n_iters, self.step_size)
            bm_copy.free()
            return vx, vy, vz

    def execute(self, context):

        obj = bpy.context.selected_objects[0]

        if bpy.context.mode == 'OBJECT':

            bm = bmesh.new()
            bm.from_mesh(obj.data)

            vx, vy, vz = self.perform_smoothing(obj, bm)

            for v in bm.verts:
                v.co.x = vx[v.index]
                v.co.y = vy[v.index]
                v.co.z = vz[v.index]

            bm.to_mesh(obj.data)
            bm.free()

        elif bpy.context.mode == 'EDIT_MESH':

            print('AA')

            # if in edit mode, only smooth the selected vertices
            bm = bmesh.from_edit_mesh(obj.data)
            selected_vertices = set([v for v in bm.verts if v.select])

            vx, vy, vz = self.perform_smoothing(obj, bm)

            # only affect selected vertices
            for v in selected_vertices:
                v.co.x = vx[v.index]
                v.co.y = vy[v.index]
                v.co.z = vz[v.index]

        return {'FINISHED'}

    def draw(self, context):
        layout: bpy.types.UILayout = self.layout.grid_flow()
        col = layout.column()
        col.prop(self, 'n_iters')
        col.prop(self, 'step_size')
        col.prop(self, 'smoothing_method')
