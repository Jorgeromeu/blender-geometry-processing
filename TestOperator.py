import bmesh

import meshutil
import visualdebug
from meshutil import *

class TestOperator(bpy.types.Operator):
    bl_idname = "object.testop"
    bl_label = "Test Operator"
    bl_options = {'REGISTER', 'UNDO'}

    length: bpy.props.FloatProperty(name='Length', default=0.1, min=0, max=5)

    def fun(self, v):
        print(v)
        return v[2]

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

        funvals = np.array([self.fun(obj.matrix_world @ v.co) for v in bm.verts]).reshape((-1, 1))
        grads = (gradient_matrix @ funvals)
        grads = grads.reshape(-1, 3)

        grad_magnitudes = []

        for tri, grad in zip(bm.faces, grads):
            centroid = np.average([obj.matrix_world @ v.co for v in tri.verts], axis=0)
            grad_magnitudes.append(np.linalg.norm(grad))
            gradient_normalized = grad / np.linalg.norm(grad)
            visualdebug.create_dir_vector(f'dir{tri.index}', centroid, grad, length=self.length)

        # set 'height' attribute to z coord of each vertex
        set_vertex_attrib(obj, 'fun', np.array([self.fun(v.co) for v in bm.verts]))
        set_face_attrib(obj, 'grad', np.array(grad_magnitudes))

        return {'FINISHED'}
