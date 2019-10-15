import bpy
import os

class ImportBvh(bpy.types.Operator):
    """Add Bvh File"""
    bl_idname = "ldops.import_bvh"
    bl_label = "Add bvh"

    filter_glob = bpy.props.StringProperty(default="*.bvh", options={'HIDDEN'})
    filepath = bpy.props.StringProperty(subtype="FILE_PATH") 
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self) 
        return {'RUNNING_MODAL'}
    def execute(self, context):
        scene = context.scene
        pref = scene.setting
        pref.bvhFilePath = os.path.basename(self.filepath)
        return {'FINISHED'} 



def register():
    bpy.utils.register_class(ImportBvh)

def unregister():
    bpy.utils.unregister_class(ImportBvh)
