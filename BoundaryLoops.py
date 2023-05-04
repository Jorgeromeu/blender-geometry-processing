import bmesh
import bpy

from meshutil import neighbors, is_boundary_edge

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

        boundary_edges = {e for e in bm.edges if is_boundary_edge(e)}
        boundary_verts = set()

        for e in boundary_edges:
            s, t = e.verts
            if is_boundary_edge(e):
                boundary_verts.add(s)
                boundary_verts.add(t)

        unvisited = set(boundary_verts)

        n_components = 0

        while unvisited:

            n_components += 1

            # select a random unvisited edge
            v: bmesh.types.BMVert = next(iter(unvisited))

            # traverse
            queue = [v]
            unvisited.remove(v)
            while queue:
                v = queue.pop(0)

                for neighbor in neighbors(v, only_boundaries=True):
                    if neighbor in unvisited:
                        queue.append(neighbor)
                        unvisited.remove(neighbor)

        print(n_components)

        bm.to_mesh(mesh)
        bm.free()

        return {'FINISHED'}
