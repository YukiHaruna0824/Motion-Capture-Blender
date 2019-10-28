import bpy
import os
from math import radians, ceil
from .bvhutil import *

#管理匯入資料物件
class DataManager():
    #key : filename
    #value : bvh object
    all_bvh = {}
    current_bvh_name = ''
    current_bvh_object = None

class ImportBvh(bpy.types.Operator):
    '''Add Bvh File'''
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
        name = os.path.basename(self.filepath)[:-4]
        bvh = Bvh()
        bp = BvhParser()
        bp.GetTokenInfo(self.filepath)
        if bp.Parse(bvh) == 0:
            #bvh.GetJointInfo()
            bvh.Calculate(bvh.Root_joint)
            index = 0
            basename = name
            #Avoid the same name
            while True:
                if name in DataManager.all_bvh.keys():
                    index = index + 1
                    name = basename + '_' + str(index)
                else:
                    break    
            DataManager.current_bvh_name = name
            DataManager.current_bvh_object = bvh
            DataManager.all_bvh[name] = bvh
        return {'FINISHED'}

class GenerateJointAndBone(bpy.types.Operator):
    '''Generate JointBone'''
    bl_idname = "ldops.generate_bone"
    bl_label = "Generate Bone"

    def execute(self, context):
        scene = context.scene
        if DataManager.current_bvh_object == None:
            return {'FINISHED'}

        current_bvh = DataManager.current_bvh_object
        #生成管理Node
        bone_manager = bpy.data.objects.new(DataManager.current_bvh_name, None)
        scene.collection.objects.link(bone_manager)

        #Create Object
        for joint in current_bvh.Joints:
            bpy.ops.mesh.primitive_uv_sphere_add()
            obj = context.object
            obj.name = joint.Name
            joint.Object = obj
        
        for joint in current_bvh.Joints:
            for child in joint.Children:
                child.Object.parent = joint.Object
        current_bvh.Joints[0].Object.parent = bone_manager
        
        '''
        frame_start = 1
        for joint in current_bvh.Joints:
            for frame_current in range(current_bvh.Num_frames):
                joint.Object.location = joint.LocalPos[frame_current]
                joint.Object.keyframe_insert("location", index=-1, frame=frame_start + frame_current)
                joint.Object.rotation_euler = Vector((radians(joint.LocalRot[frame_current].x), radians(joint.LocalRot[frame_current].y), radians(joint.LocalRot[frame_current].z)))
                joint.Object.keyframe_insert("rotation_euler", index=-1, frame=frame_start + frame_current)
        '''
        return {'FINISHED'}
    
def register():
    bpy.utils.register_class(ImportBvh)
    bpy.utils.register_class(GenerateJointAndBone)

def unregister():
    bpy.utils.unregister_class(ImportBvh)
    bpy.utils.unregister_class(GenerateJointAndBone)