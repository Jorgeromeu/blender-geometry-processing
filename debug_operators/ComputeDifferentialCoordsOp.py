import meshutil
from meshutil import *

class ComputeDifferentialCoordsOp(bpy.types.Operator):
    bl_idname = "object.computecoords"
    bl_label = "GDP Compute Differential Coordinates"
    bl_options = {'REGISTER', 'UNDO'}

    compute_gradients: bpy.props.BoolProperty(name='Gradients of embeddings', default=False)
    compute_laplace: bpy.props.BoolProperty(name='Laplace Coordinates', default=False)
    compute_cotangent: bpy.props.BoolProperty(name='Cotangent Coordinates', default=False)

    gradient_matrix = None
    laplace_matrix = None
    cotangent_matrix = None

    def compute_embedding_gradients(self, obj, bm, embedding):

        if self.gradient_matrix is None:
            self.gradient_matrix = meshutil.compute_gradient_matrix(bm)

        vx, vy, vz = embedding

        grads_x = (self.gradient_matrix @ vx).reshape(-1, 3)
        grads_y = (self.gradient_matrix @ vy).reshape(-1, 3)
        grads_z = (self.gradient_matrix @ vz).reshape(-1, 3)

        # save embeddings to attributes
        set_float_vertex_attrib(obj, 'vx', np.array(vx))
        set_float_vertex_attrib(obj, 'vy', np.array(vy))
        set_float_vertex_attrib(obj, 'vz', np.array(vz))

        # save actual gradients as attributes
        set_vector_face_attrib(obj, 'grad_vx', [Vector(grad) for grad in grads_x])
        set_vector_face_attrib(obj, 'grad_vy', grads_y)
        set_vector_face_attrib(obj, 'grad_vz', grads_z)

    def compute_laplace_coords(self, obj, bm, embedding):

        if self.laplace_matrix is None:
            self.laplace_matrix = mesh_laplacian(bm)

        vx, vy, vz = embedding

        delta_x = self.laplace_matrix @ vx.reshape(-1, 1)
        delta_y = self.laplace_matrix @ vy.reshape(-1, 1)
        delta_z = self.laplace_matrix @ vz.reshape(-1, 1)

        set_vector_vertex_attrib(obj, 'delta', [Vector(delta) for delta in zip(delta_x, delta_y, delta_z)])
        set_float_vertex_attrib(obj, 'delta_normalized',
                                np.array([Vector(delta).length for delta in zip(delta_x, delta_y, delta_z)]),
                                normalize=True)

    def compute_cotangent_coords(self, obj, bm, embedding):
        vx, vy, vz = embedding

        if self.cotangent_matrix is None:
            self.cotangent_matrix = compute_cotangent_matrix(bm)

        delta_x = self.cotangent_matrix @ vx.reshape(-1, 1)
        delta_y = self.cotangent_matrix @ vy.reshape(-1, 1)
        delta_z = self.cotangent_matrix @ vz.reshape(-1, 1)

        set_vector_vertex_attrib(obj, 'delta_cotan', [Vector(delta) for delta in zip(delta_x, delta_y, delta_z)])
        set_float_vertex_attrib(obj, 'delta_cotan_normalized',
                                np.array([Vector(delta).length for delta in zip(delta_x, delta_y, delta_z)]),
                                normalize=True)

    def execute(self, context):

        # ensure single object is selected
        if len(bpy.context.selected_objects) != 1:
            self.report({'ERROR'}, "Select a single object")
            return {'CANCELLED'}

        obj = bpy.context.selected_objects[0]
        bm = bmesh.new()
        bm.from_mesh(obj.data)

        vx, vy, vz = to_vxvyvz(bm, dims=[0, 1, 2])

        if self.compute_gradients == True:
            self.compute_embedding_gradients(obj, bm, (vx, vy, vz))

        if self.compute_laplace == True:
            self.compute_laplace_coords(obj, bm, (vx, vy, vz))

        if self.compute_cotangent_coords == True:
            self.compute_cotangent_coords(obj, bm, (vx, vy, vz))

        bm.free()

        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout.grid_flow()
        col = layout.column()
        col.prop(self, "compute_gradients")
        col.prop(self, "compute_laplace")
        col.prop(self, "compute_cotangent")
