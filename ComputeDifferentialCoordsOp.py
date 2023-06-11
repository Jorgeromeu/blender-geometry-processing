import meshutil
from meshutil import *

class ComputeDifferentialCoordsOp(bpy.types.Operator):
    bl_idname = "object.computecoords"
    bl_label = "Compute Differential Coordinates"
    bl_options = {'REGISTER', 'UNDO'}

    compute_gradients: bpy.props.BoolProperty('Compute Gradients of embeddings', default=False)
    compute_laplace: bpy.props.BoolProperty('Compute Laplace Coordinates', default=False)
    compute_cotangent: bpy.props.BoolProperty('Compute Cotangent Coordinates', default=False)

    def embedding(self, bm):
        vx = np.array([v.co.x for v in bm.verts])
        vy = np.array([v.co.y for v in bm.verts])
        vz = np.array([v.co.z for v in bm.verts])

        return vx, vy, vz

    def compute_embedding_gradients(self, obj, bm):
        gradient_matrix = meshutil.compute_gradient_matrix(bm)

        vx, vy, vz = self.embedding(bm)

        grads_x = (gradient_matrix @ vx).reshape(-1, 3)
        grads_y = (gradient_matrix @ vy).reshape(-1, 3)
        grads_z = (gradient_matrix @ vz).reshape(-1, 3)

        # save embeddings to attributes
        set_float_vertex_attrib(obj, 'vx', np.array(vx))
        set_float_vertex_attrib(obj, 'vy', np.array(vy))
        set_float_vertex_attrib(obj, 'vz', np.array(vz))

        # save actual gradients as attributes
        set_vector_face_attrib(obj, 'grad_vx', [Vector(grad) for grad in grads_x])
        set_vector_face_attrib(obj, 'grad_vy', grads_y)
        set_vector_face_attrib(obj, 'grad_vz', grads_z)

    def compute_laplace_coords(self, obj, bm):
        vx, vy, vz = self.embedding(bm)

        laplacian = mesh_laplacian(bm)

        delta_x = laplacian @ vx.reshape(-1, 1)
        delta_y = laplacian @ vy.reshape(-1, 1)
        delta_z = laplacian @ vz.reshape(-1, 1)

        set_vector_vertex_attrib(obj, 'delta', [Vector(delta) for delta in zip(delta_x, delta_y, delta_z)])
        set_float_vertex_attrib(obj, 'delta_normalized',
                                np.array([Vector(delta).length for delta in zip(delta_x, delta_y, delta_z)]),
                                normalize=True)

    def compute_cotangent_coords(self, obj, bm):
        vx, vy, vz = self.embedding(bm)

        cotangent = compute_cotangent_matrix(bm)

        delta_x = cotangent @ vx.reshape(-1, 1)
        delta_y = cotangent @ vy.reshape(-1, 1)
        delta_z = cotangent @ vz.reshape(-1, 1)

        set_vector_vertex_attrib(obj, 'delta_cotan', [Vector(delta) for delta in zip(delta_x, delta_y, delta_z)])
        set_float_vertex_attrib(obj, 'delta_cotan_normalized',
                                np.array([Vector(delta).length for delta in zip(delta_x, delta_y, delta_z)]),
                                normalize=True)

    def execute(self, context):
        # ensure single object is selected
        if len(bpy.context.selected_objects) != 1:
            self.report({'ERROR'}, "Select a single object to deform")
            return {'CANCELLED'}

        obj = bpy.context.selected_objects[0]
        mesh = obj.data
        bm = bmesh.new()
        bm.from_mesh(mesh)

        if self.compute_gradients:
            self.compute_embedding_gradients(obj, bm)

        if self.compute_laplace:
            self.compute_laplace_coords(obj, bm)

        if self.compute_cotangent_coords:
            self.compute_cotangent_coords(obj, bm)

        return {'FINISHED'}
