from bpyutil import *
from meshutil import *

class ComputeGenus(bpy.types.Operator):
    """Print genus of mesh"""
    bl_idname = "object.genus"
    bl_label = "Compute Genus"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        obj = get_selected_object(context)

        if obj is None:
            self.report({'ERROR'}, "No object selected!")

        mesh = obj.data
        bm = bmesh.new()
        bm.from_mesh(mesh)

        n_boundaries = compute_num_boundary_loops(bm)
        genus = compute_genus(bm, n_boundaries)

        print(genus)

        bm.free()

        return {'FINISHED'}
