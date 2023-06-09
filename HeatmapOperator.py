import meshutil
import visualdebug
from meshutil import *

class HeatmapOperator(bpy.types.Operator):
    bl_idname = "object.heatmapop"
    bl_label = "Heatmap"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        visualdebug.clear_debug_collection()

        # ensure single object is selected
        if len(bpy.context.selected_objects) != 1:
            self.report({'ERROR'}, "Select a single object to deform")
            return {'CANCELLED'}

        obj = bpy.context.selected_objects[0]
        mesh = obj.data
        bm = bmesh.new()
        bm.from_mesh(mesh)

        gradient_matrix = meshutil.compute_gradient_matrix(bm)

        vx = [v.co.x for v in bm.verts]
        vy = [v.co.y for v in bm.verts]
        vz = [v.co.z for v in bm.verts]

        grads_x = (gradient_matrix @ vx).reshape(-1, 3)
        grads_y = (gradient_matrix @ vy).reshape(-1, 3)
        grads_z = (gradient_matrix @ vz).reshape(-1, 3)

        # save embeddings to attributes
        set_float_vertex_attrib(obj, 'vx', np.array(vx))
        set_float_vertex_attrib(obj, 'vy', np.array(vy))
        set_float_vertex_attrib(obj, 'vz', np.array(vz))

        # save gradients for each embedding to attributes
        set_float_face_attrib(obj, 'grad_magnitude_vx', np.linalg.norm(grads_x, axis=1))
        set_float_face_attrib(obj, 'grad_magnitude_vy', np.linalg.norm(grads_y, axis=1))
        set_float_face_attrib(obj, 'grad_magnitude_vz', np.linalg.norm(grads_z, axis=1))

        # save actual gradients as attributes
        set_vector_face_attrib(obj, 'grad_vx', [Vector(grad) for grad in grads_x])
        set_vector_face_attrib(obj, 'grad_vy', grads_y)
        set_vector_face_attrib(obj, 'grad_vz', grads_z)

        return {'FINISHED'}
