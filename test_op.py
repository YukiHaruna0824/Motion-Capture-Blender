import bpy
import os
from math import radians, ceil
from .bvhutils import *
from bpy.app.handlers import persistent

#管理匯入資料物件
class DataManager():
    #key : filename
    #value : bvh object
    all_bvh = {}
    current_bvh_name = ''
    current_bvh_object = None

class SplineBvhContainer():
    spline_list = []
    spline_list_preserve = []
    curve_object_list = []
    index = 0
    function_added = 0

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
        Path,Points,Points_ori = current_bvh.getRootJointPath()

        # create the Curve Datablock
        curveData = bpy.data.curves.new('PathCurve', type='CURVE')

        curveData_ori = bpy.data.curves.new('PathCurve-original', type='CURVE')

        for i, coord in enumerate(Path):
            x,y,z = coord
            bpy.ops.mesh.primitive_cube_add(size=5.0,location=(x, y, z))

        # map coords to spline
        polyline = curveData.splines.new('POLY')
        polyline.points.add(len(Points)-1)

        for i, coord in enumerate(Points):
            x,y,z = coord
            polyline.points[i].co=(x,y,z,0)

        polyline_ori = curveData_ori.splines.new('POLY')
        polyline_ori.points.add(len(Points_ori)-1)

        for i, coord in enumerate(Points_ori):
            x,y,z = coord
            polyline_ori.points[i].co=(x,y,z,0)

        # create Object
        curveOB = bpy.data.objects.new('PathCurve', curveData)

        curveOB_ori = bpy.data.objects.new('PathCurve-original', curveData_ori)

        # attach to scene and validate context
        context.collection.objects.link(curveOB)
        context.collection.objects.link(curveOB_ori)
        '''
        bpy.ops.object.select_all(action='DESELECT')
        context.view_layer.objects.active = curveOB
        curveOB.select_set(True)
        bpy.ops.object.mode_set(mode='EDIT')
        '''
        return {'FINISHED'}

class CreateSpline(bpy.types.Operator):
    bl_idname = "ldops.create_spline"
    bl_label = "Add spline"

    def getCubicConstant(self, t, mode):
        result = 0
        if mode == 0:
            result = float(pow(1 - t, 3) / 6)
        elif mode == 1:
            result = float((3 * pow(t, 3) - 6 * pow(t, 2) + 4) / 6)
        elif mode == 2:
            result = float((-3 * pow(t, 3) + 3 * pow(t, 2) + 3 * t + 1) / 6)
        elif mode == 3:
            result = pow(t, 3) / 6

        return result

    def calc_path(self,coords):
        points = []
        for t in range(200):
            point = Vector((0, 0, 0))
            for index in range(4):
                point.x += self.getCubicConstant(t, index) * coords[index][0]
                point.y += self.getCubicConstant(t, index) * coords[index][1]
                point.z += self.getCubicConstant(t, index) * coords[index][2]
            points.append(point)
        return points

    @persistent
    def loc_change(dump1,dump2):
        for i in range(SplineBvhContainer.index):
            for j in range(4):
                loc = Vector((SplineBvhContainer.spline_list[i][j].location.x,
                                SplineBvhContainer.spline_list[i][j].location.y,
                                SplineBvhContainer.spline_list[i][j].location.z))
                dloc = loc - SplineBvhContainer.spline_list_preserve[i][j]
                
                if dloc.length > 1.0e-4:
                    calc_path(SplineBvhContainer.spline_list[i])
                    print("Cube has moved")
                    SplineBvhContainer.spline_list_preserve[i][j] = loc

    def execute(self, context):
        if(SplineBvhContainer.function_added == 0):
            SplineBvhContainer.function_added = 1
            bpy.app.handlers.depsgraph_update_post.append(self.loc_change)

        master_collection = bpy.context.scene.collection
        collection = bpy.data.collections.new("Cubes" + str(SplineBvhContainer.index))
        master_collection.children.link(collection)

        coords = [(4,1,0), (6,0,0), (8,1,0), (10,0,0)]

        cube_list = []
        cube_list_preserve = []
        for i, coord in enumerate(coords):
            x,y,z = coord
            bpy.ops.mesh.primitive_cube_add(size=2.0,location=(x, y, z))
            ob = bpy.context.object
            ob.data.name = 'CubeMesh' + str(SplineBvhContainer.index) + '_' + str(i)
            ob.name = 'Cube' + str(SplineBvhContainer.index) + '_' + str(i)
            collection.objects.link(ob)
            bpy.context.view_layer.active_layer_collection.collection.objects.unlink(ob)
            cube_list.append(ob)
            loc = Vector((ob.location.x, ob.location.y, ob.location.z))
            cube_list_preserve.append(loc)
        
        SplineBvhContainer.spline_list.append(cube_list)
        SplineBvhContainer.spline_list_preserve.append(cube_list_preserve)
        SplineBvhContainer.index += 1

        # create the Curve Datablock
        curveData = bpy.data.curves.new('UserCurve', type='CURVE')

        Points = self.calc_path(coords)

        # map coords to spline
        polyline = curveData.splines.new('POLY')
        polyline.points.add(len(Points)-1)

        for i, coord in enumerate(Points):
            x,y,z = coord
            polyline.points[i].co=(x,y,z,0)

        curveOB = bpy.data.objects.new('UserCurve', curveData)
        context.collection.objects.link(curveOB)

        SplineBvhContainer.curve_object_list.append(curveOB)

        return {'FINISHED'}


class AddPoint(bpy.types.Operator):
    bl_idname = "ldops.add_point"
    bl_label = "Add point"

    def execute(self, context):
        scene = context.scene
        
        for spline in SplineBvhContainer.spline_list:
            for i in range(4):
                print(spline[i].name)
                print(spline[i].location)
        for spline in SplineBvhContainer.spline_list_preserve:
            for i in range(4):
                print(spline[i])
        '''
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
        '''
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
