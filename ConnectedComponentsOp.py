import bmesh
import bpy

from meshutil import neighbors

class ConnectedComponentsOp(bpy.types.Operator):
    """Print genus of mesh"""
    bl_idname = "object.conectedcomponents"
    bl_label = "Connected Components"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        obj: bpy.types = bpy.context.object
        if obj is None:
            self.report({'ERROR'}, "No object selected!")

        mesh = obj.data

        bm = bmesh.new()
        bm.from_mesh(mesh)

        unvisited = set(bm.verts)

        n_components = 0

        while unvisited:

            n_components += 1

            # select a random unvisited vertex
            v: bmesh.types.BMVert = next(iter(unvisited))

            # traverse
            queue = [v]
            unvisited.remove(v)
            while queue:
                v = queue.pop(0)

                # print(v.index)

                for neighbor in neighbors(v):
                    if neighbor in unvisited:
                        queue.append(neighbor)
                        unvisited.remove(neighbor)

        print(n_components)

        bm.to_mesh(mesh)
        bm.free()

        return {'FINISHED'}
