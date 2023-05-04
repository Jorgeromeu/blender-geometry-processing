import bmesh
import bpy

from meshutil import neighbors

class BoundaryLoopsOp(bpy.types.Operator):
    """Print genus of mesh"""
    bl_idname = "object.boundaryloops"
    bl_label = "Boundary Loops"
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

            edges = v.link_edges
            for e in edges:
                e: bmesh.types.BMEdge = e
                edge_faces = e.link_faces


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

        bm.free()

        return {'FINISHED'}
