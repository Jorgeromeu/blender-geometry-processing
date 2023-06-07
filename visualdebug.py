import bpy
import numpy as np

DEBUG_COLLECTION_NAME = 'DEBUG'

def clear_debug_collection():
    collection = bpy.data.collections.get(DEBUG_COLLECTION_NAME)

    # If the collection exists
    if collection:
        # Iterate over all the objects in the collection
        for obj in collection.objects:
            # Unlink the object from the collection
            collection.objects.unlink(obj)
            # Remove the object from the Blender scene
            bpy.data.objects.remove(obj)

def get_debug_collection():
    """
    Get collection by name, and create if doesnt exist

    :param collection_name: name of collection
    :return: reference to collection
    """

    # if collection doesn't exist, make one
    if not bpy.data.collections.get(DEBUG_COLLECTION_NAME):
        collection = bpy.data.collections.new(DEBUG_COLLECTION_NAME)
        bpy.context.scene.collection.children.link(collection)

    return bpy.data.collections[DEBUG_COLLECTION_NAME]

def create_dir_vector(name: str, origin: np.ndarray, direction: np.ndarray, length=0.1):
    endpoint = origin + length * direction

    # length of arrow heads
    arrowlen = length / 7

    # vector orthogonal to direction (for arrow heads)
    direction_orth = np.array([-direction[1] * arrowlen, -direction[0] * arrowlen, 0])
    arrow_l = endpoint - arrowlen * direction + direction_orth
    arrow_r = endpoint - arrowlen * direction - direction_orth

    verts = [tuple(origin), tuple(endpoint), tuple(arrow_l), tuple(arrow_r)]
    edges = [(0, 1), (1, 2), (1, 3)]
    faces = []

    collection = get_debug_collection()
    create_object_from_pydata(verts, edges, faces, name, collection)

def create_object_from_pydata(verts, edges, faces, name, collection):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, edges, faces)
    mesh.validate()
    mesh.update()

    # create obj
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
