import bpy
from bpy.props import *

class MyPreferece(bpy.types.PropertyGroup):
    bvhFilePath = StringProperty(name = 'bvh Path', description = "bvh Path")

#實作Blender介面class
class Test_Panel(bpy.types.Panel):
    bl_idname = "Test_Panel"
    bl_label = "Test Panel"
    bl_category = "Motion_Capture"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        pref = scene.setting

        row = layout.row()
        row.prop(pref, 'bvhFilePath')
        row.operator('ldops.import_bvh', text='', icon='FILE_NEW')



def register():
    bpy.utils.register_class(Test_Panel)
    bpy.utils.register_class(MyPreferece)
    bpy.types.Scene.setting = PointerProperty(type = MyPreferece)

def unregister():
    bpy.utils.unregister_class(Test_Panel)
    bpy.utils.unregister_class(MyPreferece)
    del bpy.types.Scene.setting