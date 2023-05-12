from mathutils import Vector
class DirectionBucket:
    def __init__(self):
        pass

    def insert(self, direction: Vector):
        direction = direction.normalized()
        theta = ...
        phi = ...
