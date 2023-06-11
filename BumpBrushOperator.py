import bpy.props
import numpy as np
from scipy.spatial.transform import Rotation as R

from meshutil import *


class BumpBrushOperator(bpy.types.Operator):
    bl_idname = "object.geobumpbrush"
    bl_label = "GDP Bump Brush"
    bl_options = {'REGISTER', 'UNDO'}

    radius: bpy.props.FloatProperty(name="Radius", default=0.1, min=0)
    slope_value: bpy.props.FloatProperty(name='Slope Value', default=0, min=-np.pi / 2, max=np.pi / 2)

    gradient_matrix: sp.csr_matrix
    cotangent_matrix: sp.linalg.splu
    gtmv: sp.csr_matrix
    center: Vector
    center_normal: Vector

    def invoke(self, context, event):
        obj = bpy.context.active_object

        # ensure in edit mode
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode='EDIT')

        # get editable mesh
        mesh = obj.data
        bm = bmesh.from_edit_mesh(mesh)

        selected_vertices = [(v.index, v) for v in bm.verts if v.select]
        if len(selected_vertices) > 1:
            self.report({'ERROR'}, "Please select exactly one vertex.")
        selected_vertex = selected_vertices[0]

        self.center = selected_vertex[1].co
        self.center_normal = selected_vertex[1].normal

        # compute gradient matrix
        self.gradient_matrix, self.cotangent_matrix, self.gtmv = compute_deformation_matrices(bm)

        # compute and factorize cotangent matrix
        self.cotangent_matrix = sp.linalg.splu(self.cotangent_matrix)

        bm.free()

        return self.execute(context)

    def execute(self, context):
        obj = bpy.context.active_object

        # ensure in edit mode
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode='EDIT')

        # get editable mesh
        mesh = obj.data
        bm = bmesh.from_edit_mesh(mesh)

        # get coordinate embeddings
        vx, vy, vz = to_vxvyvz(bm, dims=[0, 1, 2])

        # compute, and unflatten gradients of each embedding
        grads_x = (self.gradient_matrix @ vx).reshape(-1, 3)
        grads_y = (self.gradient_matrix @ vy).reshape(-1, 3)
        grads_z = (self.gradient_matrix @ vz).reshape(-1, 3)

        # selected faces
        selected_faces_indices = []
        selected_faces = []
        for face in bm.faces:
            for vertex in face.verts:
                if (vertex.co - self.center).length <= self.radius and vertex.normal.dot(self.center_normal) >= 0.9:
                    selected_faces_indices.append(face.index)
                    selected_faces.append(face)
                    break

        # modify the selected gradients based on the bump
        modified_selected_grads_x = grads_x[selected_faces_indices]
        modified_selected_grads_y = grads_y[selected_faces_indices]
        modified_selected_grads_z = grads_z[selected_faces_indices]

        factor = np.pi / self.radius
        for i in range(len(modified_selected_grads_x)):
            face_centroid = centroid([v.co for v in selected_faces[i].verts])
            point_difference = (self.center - face_centroid)
            diff_length = point_difference.length
            # Derive the rotation
            rotation_angle = self.slope_value * np.sin(factor * diff_length)
            rotation_axis = selected_faces[i].normal.cross(point_difference.normalized())
            rotation_matrix = R.from_rotvec(rotation_angle * rotation_axis.normalized()).as_matrix()
            # Derive the anisotropic scaling
            scale_factor = 1 / np.cos(rotation_angle)
            scale_matrix = np.eye(3) * [0, 0, 1]  # (point_difference / diff_length)
            scale_matrix = scale_factor * scale_matrix
            modified_selected_grads_x[i] = scale_matrix @ rotation_matrix @ modified_selected_grads_x[i]
            modified_selected_grads_y[i] = scale_matrix @ rotation_matrix @ modified_selected_grads_y[i]
            modified_selected_grads_z[i] = scale_matrix @ rotation_matrix @ modified_selected_grads_z[i]

        # get modified gradients
        modified_grads_x = grads_x
        modified_grads_y = grads_y
        modified_grads_z = grads_z

        modified_grads_x[selected_faces_indices] = modified_selected_grads_x
        modified_grads_y[selected_faces_indices] = modified_selected_grads_y
        modified_grads_z[selected_faces_indices] = modified_selected_grads_z

        # flatten modified gradients
        modified_grads_x = modified_grads_x.reshape(-1, 1)
        modified_grads_y = modified_grads_y.reshape(-1, 1)
        modified_grads_z = modified_grads_z.reshape(-1, 1)

        rhs_x = (self.gtmv @ modified_grads_x).flatten()
        rhs_y = (self.gtmv @ modified_grads_y).flatten()
        rhs_z = (self.gtmv @ modified_grads_z).flatten()

        center_og = centroid([corner.co for corner in bm.verts])

        new_vx = self.cotangent_matrix.solve(rhs_x)
        new_vy = self.cotangent_matrix.solve(rhs_y)
        new_vz = self.cotangent_matrix.solve(rhs_z)

        # set vertex coordinates
        for v_i, v in enumerate(bm.verts):
            v.co.x = new_vx[v_i]
            v.co.y = new_vy[v_i]
            v.co.z = new_vz[v_i]

        center_new = centroid([corner.co for corner in bm.verts])

        diff = center_new - center_og

        for v in bm.verts:
            v.co -= diff

        bm.free()

        return {'FINISHED'}
