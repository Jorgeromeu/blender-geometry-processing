from meshutil import *

def fun(p: Vector) -> float:
    return p[1] ** 2

class NumericalTestOp(bpy.types.Operator):
    bl_idname = "object.numercaltest"
    bl_label = "Numerical Matrix Test"
    bl_options = {'REGISTER', 'UNDO'}

    def test_gradient_matrix(self, bm):

        gradient_matrix = compute_gradient_matrix(bm)

        fun_vals = np.array([fun(v.co) for v in bm.verts])

        grads_vz_matrix = (gradient_matrix @ fun_vals).reshape(-1, 3)

        grads_vz_manual = []
        for f in bm.faces:
            f: BMFace = f

            face_verts = list(f.verts)

            grad_f = Vector((0, 0, 0))

            for v_i, v in enumerate(face_verts):
                succ_v = face_verts[(v_i + 1) % 3]
                succ_succ_v = face_verts[(v_i + 2) % 3]
                opposite_edge = succ_succ_v.co - succ_v.co

                grad_f += 1 / (2 * f.calc_area()) * fun(v.co) * f.normal.cross(opposite_edge)

            grads_vz_manual.append(grad_f)

        assert (grads_vz_matrix == [np.array(g) for g in grads_vz_manual]).all()

    def test_laplace_matrix(self, bm):

        laplace_coords = compute_laplace_coords(bm)

        vx, vy, vz = to_vxvyvz(bm, [0, 1, 2])
        laplacian = mesh_laplacian(bm)

        delta_x = laplacian @ vx
        delta_y = laplacian @ vy
        delta_z = laplacian @ vz

        for i in range(len(vx)):
            assert laplace_coords[i] == Vector((delta_x[i], delta_y[i], delta_z[i]))

    def execute(self, context):
        obj = get_selected_object(bpy.context)

        mesh = obj.data
        bm = bmesh.new()
        bm.from_mesh(mesh)

        self.test_gradient_matrix(bm)
        self.test_laplace_matrix(bm)

        return {'FINISHED'}