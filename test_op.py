import bpy
import os
from math import radians, ceil
from .bvhutils import *

#管理匯入資料物件
class DataManager():
    #key : filename
    #value : bvh object
    all_bvh = {}
    current_bvh_name = ''
    current_bvh_object = None

class SplineBvhContainer():
    all_spline = {}

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
        bvh.read_bvh(self.filepath)
        index = 0
        basename = name
        #Avoid complicated name
        while True:
            if name in DataManager.all_bvh.keys():
                index += 1
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
        current_bvh.add_joint(context, scene.frame_start)
        return {'FINISHED'}

class DrawBvhInitial(bpy.types.Operator):
    bl_idname = "ldops.draw_bvh_initial"
    bl_label = "Draw BVH Initial"

    def execute(self, context):
        scene = context.scene
        if DataManager.current_bvh_object == None:
            return {'FINISHED'}

        current_bvh = DataManager.current_bvh_object
        Path = current_bvh.getRootJointPath()

        # create the Curve Datablock
        curveData = bpy.data.curves.new('myCurve', type='CURVE')
        curveData.dimensions = '3D'


        # map coords to spline
        polyline = curveData.splines.new('BEZIER')
        polyline.bezier_points.add((len(Path)/2)-1)
        for i, coord in enumerate(Path):
            x,y,z = coord
            index = (i + 1)//3
            
            if i % 3 == 0:
                polyline.bezier_points[index].co = (x, y, z)
                if i == 0:
                    polyline.bezier_points[index].handle_left = (x, y, z)
                    polyline.bezier_points[index].handle_left_type = 'AUTO'
                if i == len(Path) - 1:
                    polyline.bezier_points[index].handle_right = (x, y, z)
                    polyline.bezier_points[index].handle_right_type = 'AUTO'
            elif i % 3 == 1:
                polyline.bezier_points[index].handle_right = (x, y, z)
                polyline.bezier_points[index].handle_right_type = 'AUTO'
            elif i % 3 == 2:
                polyline.bezier_points[index].handle_left = (x, y, z)
                polyline.bezier_points[index].handle_left_type = 'AUTO'

        # create Object
        curveOB = bpy.data.objects.new('myCurve', curveData)
        curveData.bevel_depth = 0.01

        # attach to scene and validate context
        context.collection.objects.link(curveOB)
        bpy.ops.object.select_all(action='DESELECT')
        context.view_layer.objects.active = curveOB
        curveOB.select_set(True)
        bpy.ops.object.mode_set(mode='EDIT')

        return {'FINISHED'}

class CreateSpline(bpy.types.Operator):
    bl_idname = "ldops.create_spline"
    bl_label = "Add spline"

    def execute(self, context):
        scene = context.scene
        # print all objects
        # for obj in bpy.data.objects:
        #     print(obj.name)
        #     if("Curve" in obj.name):
        #         print("found")
        #         scene.collection.objects.unlink(obj)
        #         bpy.data.objects.remove(obj)

        # for cur in bpy.data.curves:
        #     print(cur.name)
        #     bpy.data.curves.remove(cur)

        coords = [(4,1,0), (6,0,0), (8,1,0)]

        # create the Curve Datablock
        curveData = bpy.data.curves.new('myCurve', type='CURVE')
        curveData.dimensions = '2D'
        curveData.resolution_u = 2

        # map coords to spline
        polyline = curveData.splines.new('BEZIER')
        polyline.bezier_points.add(len(coords)-1)
        for i, coord in enumerate(coords):
            x,y,z = coord
            polyline.bezier_points[i].co = (x, y, z)
            polyline.bezier_points[i].handle_left = (x-0.5, y, z)
            polyline.bezier_points[i].handle_left_type = 'AUTO'
            polyline.bezier_points[i].handle_right = (x+0.5, y, z)
            polyline.bezier_points[i].handle_right_type = 'AUTO'

        # create Object
        curveOB = bpy.data.objects.new('myCurve', curveData)
        curveData.bevel_depth = 0.01

        # attach to scene and validate context
        context.collection.objects.link(curveOB)
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        context.view_layer.objects.active = curveOB
        curveOB.select_set(True)
        bpy.ops.object.mode_set(mode='EDIT')

        SplineBvhContainer.all_spline[curveOB]='None'
        return {'FINISHED'}


class AddPoint(bpy.types.Operator):
    bl_idname = "ldops.add_point"
    bl_label = "Add point"

    def execute(self, context):
        scene = context.scene
        
        # print all objects
        for obj in bpy.data.objects:
            print(obj.name)
            if("Curve" in obj.name):
                if bpy.context.view_layer.objects.active == obj:
                    splines = obj.data.splines[0]
                    length = len(splines.bezier_points)

                    if length >= 2:
                        prev2 = splines.bezier_points[length - 2]
                        prev1 = splines.bezier_points[length - 1]

                        splines.bezier_points.add(1)
                        tmpVector = prev1.co - prev2.co
                        dirVector = Vector((tmpVector[0],tmpVector[1],tmpVector[2]))
                        dirVector = dirVector.normalized()*2.0
                        splines.bezier_points[length].co = splines.bezier_points[length-1].co + dirVector
                        splines.bezier_points[length].handle_left = splines.bezier_points[length-1].co + dirVector * 0.75
                        splines.bezier_points[length].handle_left_type = 'AUTO'
                        splines.bezier_points[length].handle_right = splines.bezier_points[length-1].co + dirVector * 1.25
                        splines.bezier_points[length].handle_right_type = 'AUTO'
                        print("found")
                    else:
                        prev1 = splines.bezier_points[length - 1]
                        dirVector = Vector((2,0,0))
                        splines.bezier_points.add(1)
                        splines.bezier_points[length].co = splines.bezier_points[length-1].co + dirVector
                        splines.bezier_points[length].handle_left = splines.bezier_points[length-1].co + dirVector * 0.75
                        splines.bezier_points[length].handle_left_type = 'AUTO'
                        splines.bezier_points[length].handle_right = splines.bezier_points[length-1].co + dirVector * 1.25
                        splines.bezier_points[length].handle_right_type = 'AUTO'

                    bpy.ops.object.mode_set(mode='OBJECT')
                    bpy.ops.object.select_all(action='DESELECT')
                    bpy.context.view_layer.objects.active = obj
                    obj.select_set(True)
                    bpy.ops.object.mode_set(mode='EDIT')

        return {'FINISHED'}

class DelPoint(bpy.types.Operator):
    bl_idname = "ldops.del_point"
    bl_label = "Delete point"

    def execute(self, context):
        scene = context.scene
        
        # print all objects
        for obj in bpy.data.objects:
            print(obj.name)
            if("Curve" in obj.name):
                if bpy.context.view_layer.objects.active == obj:
                    splineOri = obj.data.splines[0]
                    length = len(splineOri.bezier_points)

                    if length >= 2:
                        index = length - 1 # index of bez point to remove.
                        x = [0] * length * 3 # flat list of vectors
                        hr = x[:]
                        hl = x[:]
                        auto = ['AUTO'] * length * 3
                        splineOri.bezier_points.foreach_get("co", x)
                        splineOri.bezier_points.foreach_get("handle_left", hl)
                        splineOri.bezier_points.foreach_get("handle_right", hr)
                        print(len(x))
                        # pop off index 0
                        for i in range(3):
                            j = 3 * index
                            x.pop(j)
                            hl.pop(j)
                            hr.pop(j)
                            auto.pop(j)

                        # one less for removed, one more less for splines new
                        length -= 2 

                        # add a new spline
                        splineNew = obj.data.splines.new('BEZIER')

                        splineNew.bezier_points.add(length)
                        splineNew.bezier_points.foreach_set("co", x)
                        splineNew.bezier_points.foreach_set("handle_left", hl)
                        splineNew.bezier_points.foreach_set("handle_right", hr)

                        for i in range(len(splineNew.bezier_points)):
                            splineNew.bezier_points[i].handle_left_type = 'AUTO'
                            splineNew.bezier_points[i].handle_right_type = 'AUTO'

                        #remove spline 0
                        obj.data.splines.remove(splineOri)


                    bpy.ops.object.mode_set(mode='OBJECT')
                    bpy.ops.object.select_all(action='DESELECT')
                    bpy.context.view_layer.objects.active = obj
                    obj.select_set(True)
                    bpy.ops.object.mode_set(mode='EDIT')

        return {'FINISHED'}
    
def register():
    bpy.utils.register_class(ImportBvh)
    bpy.utils.register_class(GenerateJointAndBone)
    bpy.utils.register_class(DrawBvhInitial)
    bpy.utils.register_class(CreateSpline)
    bpy.utils.register_class(AddPoint)
    bpy.utils.register_class(DelPoint)

def unregister():
    bpy.utils.unregister_class(ImportBvh)
    bpy.utils.unregister_class(GenerateJointAndBone)
    bpy.utils.unregister_class(DrawBvhInitial)
    bpy.utils.unregister_class(CreateSpline)
    bpy.utils.unregister_class(AddPoint)
    bpy.utils.unregister_class(DelPoint)
