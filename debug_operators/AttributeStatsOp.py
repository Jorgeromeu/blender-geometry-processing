import bpy

class AttributeStatsOp(bpy.types.Operator):
    bl_idname = "object.attributestats"
    bl_label = "GDP AttributeStats"
    bl_options = {'REGISTER', 'UNDO'}

    def plot_attrib_distribution(self, obj, attrib_name, filename):
        values = [val.vector for val in obj.data.attributes[attrib_name].data.values()]
        norms = [delta.length for delta in values]

        print(min(norms))
        print(max(norms))

        # plt.hist(norms, bins=30, edgecolor='black')
        # plt.xlabel(f'{obj.name}: {attrib_name}')
        # plt.ylabel(f'norm')
        # plt.savefig(filename)
        # plt.clf()
        # plt.cla()

    def execute(self, context):
        # ensure single object is selected
        if len(bpy.context.selected_objects) != 1:
            self.report({'ERROR'}, "Select a single object")
            return {'CANCELLED'}

        obj = bpy.context.selected_objects[0]
        self.plot_attrib_distribution(obj, 'delta', 'plots/delta_norms.pdf')

        return {'FINISHED'}
