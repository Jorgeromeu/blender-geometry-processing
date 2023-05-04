import bmesh
import bpy
import mathutils

class VolumeOperator(bpy.types.Operator):
    """Print genus of mesh"""
    bl_idname = "object.computevolume"
    bl_label = "Compute Volume"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        obj: bpy.types = bpy.context.object
        if obj is None:
            self.report({'ERROR'}, "No object selected!")

        mesh = obj.data

        bm = bmesh.new()
        bm.from_mesh(mesh)

        # ensure mesh is triangulated
        bmesh.ops.triangulate(bm, faces=bm.faces[:])

        total_volume = 0

        for face in bm.faces:
            face: bmesh.types.BMFace = face
            v1, v2, v3 = [v.co for v in face.verts]

            tetra_volume = v1.cross(v2).dot(v3) / 6
            total_volume += tetra_volume

        print(total_volume)

        bm.free()

        return {'FINISHED'}
