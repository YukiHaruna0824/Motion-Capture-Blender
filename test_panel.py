import bpy
from bpy.props import *
from .test_op import *


#註冊共用變數class
class MyPreferece(bpy.types.PropertyGroup):
    bvhFilePath = StringProperty(name = 'bvh Path', description = "bvh Path")
    
    def loadBvh(self, context):
        item = []
        bvh_names = DataManager.all_bvh.keys()
        for bvh_name in bvh_names:
            item.append((bvh_name, bvh_name, ''))
        return item
    def updateBvh(self, context):
        DataManager.current_bvh_name = self.bvhRecord
        DataManager.current_bvh_object = DataManager.all_bvh[self.bvhRecord]
    def loadBvh2(self, context):
        item = []
        bvh_names = DataManager.all_bvh.keys()
        for bvh_name in bvh_names:
            item.append((bvh_name, bvh_name, ''))
        return item
    def updateBvh2(self, context):
        DataManager.current_bvh_name_concat = self.bvhRecordConcat
        DataManager.current_bvh_object_concat = DataManager.all_bvh[self.bvhRecordConcat]
    def loadNode(self,context):
        item = []
        spline_list = SplineBvhContainer.spline_list
        for spline in spline_list:
            for i in range(len(spline)):
                if bpy.context.view_layer.objects.active == spline[i]:
                    for spline_index in range(len(spline)-3):
                        item.append((str(spline_index), str(spline_index), ''))
        return item
    def updateNode(self, context):
        DataManager.nowSelectingFragment = self.node_select
    bvhRecord = EnumProperty(name='Current Bvh', description = "",items = loadBvh, update = updateBvh)
    bvhRecordConcat = EnumProperty(name='Current Bvh2', description = "",items = loadBvh2, update = updateBvh2)
    node_select = EnumProperty(name='Node Select', description = "",items = loadNode, update = updateNode)

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
        row = layout.row()
        row.operator('ldops.create_spline')
        row = layout.row()
        row.prop(pref, 'node_select')
        row.operator('ldops.set_path')
        row = layout.row()
        row.prop(pref, 'bvhRecord')
        row.operator('ldops.generate_bone', text='Generate Bone')
        row = layout.row()
        row.operator('ldops.draw_bvh_initial')
        row = layout.row()
        row.prop(pref, 'bvhRecordConcat')
        row = layout.row()
        row.operator('ldops.generate_concat_bone', text='Generate Concat Bone')

        row = layout.row()
        row.operator('ldops.add_point')
        row.operator('ldops.del_point')


def register():
    bpy.utils.register_class(Test_Panel)
    bpy.utils.register_class(MyPreferece)

    #將物件綁定在場景上
    bpy.types.Scene.setting = PointerProperty(type = MyPreferece)

def unregister():
    bpy.utils.unregister_class(Test_Panel)
    bpy.utils.unregister_class(MyPreferece)
    del bpy.types.Scene.setting