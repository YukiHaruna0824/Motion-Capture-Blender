import bpy
import os
from math import radians, ceil
from .bvhutils import *
from bpy.app.handlers import persistent
import decimal

#管理匯入資料物件
class DataManager():
    #key : filename
    #value : bvh object
    all_bvh = {}
    current_bvh_name = ''
    current_bvh_object = None
    current_bvh_name_concat = ''
    current_bvh_object_concat = None
    nowSelectingFragment = 0

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
        DataManager.current_bvh_object.destiny_points_nodes = None
        return {'FINISHED'}

class SetPath(bpy.types.Operator):
    bl_idname = "ldops.set_path"
    bl_label = "Set path"

    def execute(self,context):
        if DataManager.current_bvh_object == None:
            return {'FINISHED'}
        index = 0
        for spline in SplineBvhContainer.spline_list:
            for i in range(len(spline)):
                if bpy.context.view_layer.objects.active == spline[i]:
                    number = int(DataManager.nowSelectingFragment)
                    spline_list_t = []
                    for k in range(number,number+4):
                        spline_list_t.append(spline[k].location)

                    Points = calc_path(spline_list_t,200)
                    for k, coord in enumerate(Points):
                        x,y,z = coord
                        SplineBvhContainer.curve_object_list[index].data.splines[0].points[k].co = (x,y,z,0)
                    DataManager.current_bvh_object.destiny_points_nodes = spline_list_t
            index+=1
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
        path,source_points,original_points = current_bvh.getRootJointPath()
        nodes = DataManager.current_bvh_object.destiny_points_nodes
        nodelists = [nodes[0],nodes[1],nodes[2],nodes[3]]
        DataManager.current_bvh_object.destiny_points = calc_path(nodelists,len(source_points))
        current_bvh.add_joint(context, scene.frame_start,source_points)
        return {'FINISHED'}

def add_concat_joint(a,b,context, frame_start):
    if frame_start < 1:
        frame_start = 1
    
    scene = context.scene
    for obj in scene.objects:
        obj.select_set(False)
    
    objects = []

    def add_ob(name):
        obj = bpy.data.objects.new(name, None)
        context.collection.objects.link(obj)
        objects.append(obj)
        obj.select_set(True)
        obj.empty_display_type = 'CUBE'
        obj.empty_display_size = 0.5
        return obj
    
    #Add objects
    for name, joint in a.joints.items():
        joint.temp = add_ob(name)
        joint.temp.rotation_mode = joint.rot_order_str[::-1]
    
    #Set Parent
    for joint in a.joints.values():
        for child in joint.children:
            child.temp.parent = joint.temp
    
    #Set location
    for joint in a.joints.values():
        joint.temp.location = joint.rest_head_local

    #Add tail objects
    for name, joint in a.joints.items():
        if not joint.children:
            ob_end = add_ob(name + '_end')
            ob_end.parent = joint.temp
            ob_end.location = joint.rest_tail_world - joint.rest_head_world
    

    fcprev = 0
    lxp=lyp=lzp=0
    root_index=0
    obj_p = []
    for name, joint in a.joints.items():
        obj = joint.temp
        fcprev=len(joint.anim_data)
        obj_p.append(joint.temp)
        root_index=0

        print(len(joint.anim_data))
        for fc in range(len(joint.anim_data)):

            lx, ly, lz, rx, ry, rz = joint.anim_data[fc]

            if joint.has_loc:
                obj.delta_location = Vector((lx, ly, lz)) - joint.rest_head_world
                obj.keyframe_insert("delta_location", index=-1, frame=frame_start + fc)
            
            if joint.has_rot:
                obj.delta_rotation_euler = rx, ry, rz
                obj.keyframe_insert("delta_rotation_euler", index=-1, frame=frame_start + fc)
            
            if root_index == 0:
                lxp=lx
                lyp=ly
                lzp=lz
            
        root_index += 1

    joint_index=0
    for name, joint in b.joints.items():
        obj = joint.temp
        obj_first = obj_p[joint_index]
        print(len(joint.anim_data))
        for fc in range(len(joint.anim_data)):
            lx, ly, lz, rx, ry, rz = joint.anim_data[fc]
            
            if joint.has_loc:
                obj_first.delta_location = Vector((lx, ly, lz)) - joint.rest_head_world
                obj_first.keyframe_insert("delta_location", index=-1, frame=frame_start + fc + fcprev)
            
            if joint.has_rot:
                obj_first.delta_rotation_euler = rx, ry, rz
                obj_first.keyframe_insert("delta_rotation_euler", index=-1, frame=frame_start + fc + fcprev)
        joint_index+=1

class GenerateJointAndBoneConcat(bpy.types.Operator):
    '''Generate JointBone'''
    bl_idname = "ldops.generate_concat_bone"
    bl_label = "Generate Concat Bone"

    def execute(self, context):
        scene = context.scene
        if DataManager.current_bvh_object == None:
            return {'FINISHED'}
        if DataManager.current_bvh_object_concat == None:
            return {'FINISHED'}

        current_bvh = DataManager.current_bvh_object
        current_bvh_concat = DataManager.current_bvh_object_concat

        add_concat_joint(current_bvh,current_bvh_concat,context, scene.frame_start)
        return {'FINISHED'}

class DrawBvhInitial(bpy.types.Operator):
    bl_idname = "ldops.draw_bvh_initial"
    bl_label = "Draw BVH Initial"

    def execute(self, context):
        scene = context.scene
        if DataManager.current_bvh_object == None:
            return {'FINISHED'}

        current_bvh = DataManager.current_bvh_object
        path,source_points,original_points = current_bvh.getRootJointPath()

        # create the Curve Datablock
        curveData = bpy.data.curves.new('PathCurve', type='CURVE')

        curveData_ori = bpy.data.curves.new('PathCurve-original', type='CURVE')

        for i, coord in enumerate(path):
            x,y,z = coord
            bpy.ops.mesh.primitive_cube_add(size=3.0,location=(x, y, z))

        # map coords to spline
        polyline = curveData.splines.new('POLY')
        polyline.points.add(len(source_points)-1)

        for i, coord in enumerate(source_points):
            x,y,z = coord
            polyline.points[i].co=(x,y,z,0)

        polyline_ori = curveData_ori.splines.new('POLY')
        polyline_ori.points.add(len(original_points)-1)

        for i, coord in enumerate(original_points):
            x,y,z = coord
            polyline_ori.points[i].co=(x,y,z,0)

        # create Object
        curveOB = bpy.data.objects.new('PathCurve', curveData)

        curveOB_ori = bpy.data.objects.new('PathCurve-original', curveData_ori)

        # attach to scene and validate context
        context.collection.objects.link(curveOB)
        context.collection.objects.link(curveOB_ori)
        return {'FINISHED'}

def getCubicConstant(t, mode):
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

def float_range(start, stop, step):
    while start < stop:
        yield float(start)
        start += decimal.Decimal(step)

def calc_path(coords,timestamp):
    points = []
    fr = float_range(0,1,1.0/timestamp)
    for t in list(fr):
        point = Vector((0, 0, 0))
        for index in range(4):
            point.x += getCubicConstant(t, index) * coords[index][0]
            point.y += getCubicConstant(t, index) * coords[index][1]
            point.z += getCubicConstant(t, index) * coords[index][2]
        points.append(point)
    return points


# def loc_change():
#     for i in range(SplineBvhContainer.index):
#         for j in range(len(SplineBvhContainer.index[i])):
#             loc = Vector((SplineBvhContainer.spline_list[i][j].location.x,
#                             SplineBvhContainer.spline_list[i][j].location.y,
#                             SplineBvhContainer.spline_list[i][j].location.z))

#             coords = [SplineBvhContainer.spline_list[i][0].location,SplineBvhContainer.spline_list[i][1].location
#                      ,SplineBvhContainer.spline_list[i][2].location,SplineBvhContainer.spline_list[i][3].location]
#             if dloc.length > 1.0e-4:
#                 Points = calc_path(coords,200)
#                 for k, coord in enumerate(Points):
#                     x,y,z = coord
#                     SplineBvhContainer.curve_object_list[i].data.splines[0].points[k].co = (x,y,z,0)
    
#     return 0.02

class CreateSpline(bpy.types.Operator):
    bl_idname = "ldops.create_spline"
    bl_label = "Add spline"

    def execute(self, context):
        if(SplineBvhContainer.function_added == 0):
            SplineBvhContainer.function_added = 1
            # bpy.app.timers.register(loc_change)
            bpy.ops.object.select_all(action='DESELECT')
            bpy.data.objects['Cube'].select_set(True)
            bpy.ops.object.delete()

        master_collection = bpy.context.scene.collection
        collection = bpy.data.collections.new("Cubes" + str(SplineBvhContainer.index))
        master_collection.children.link(collection)

        coords = [(30,0,5), (30,30,40), (30,0,75), (30,30,110)]

        cube_list = []
        for i, coord in enumerate(coords):
            x,y,z = coord
            bpy.ops.mesh.primitive_cube_add(size=1.0,location=(x, y, z))
            ob = bpy.context.object
            ob.data.name = 'CubeMesh' + str(SplineBvhContainer.index) + '_' + str(i)
            ob.name = 'Cube' + str(SplineBvhContainer.index) + '_' + str(i)
            collection.objects.link(ob)
            bpy.context.view_layer.active_layer_collection.collection.objects.unlink(ob)
            cube_list.append(ob)
            loc = Vector((ob.location.x, ob.location.y, ob.location.z))
        
        SplineBvhContainer.spline_list.append(cube_list)
        SplineBvhContainer.index += 1

        # create the Curve Datablock
        curveData = bpy.data.curves.new('UserCurve', type='CURVE')

        Points = calc_path(coords,200)

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
        spline_list = SplineBvhContainer.spline_list
        for spline in spline_list:
            for i in range(len(spline)):
                if bpy.context.view_layer.objects.active == spline[i]:
                    collectionCube = None
                    for col in bpy.data.collections:
                        for obj in col.all_objects:
                            if bpy.context.view_layer.objects.active == obj:
                                collectionCube=col
                    bpy.ops.mesh.primitive_cube_add(size=1.0,location=(spline[-1].location.x, spline[-1].location.y, spline[-1].location.z+10))
                    ob = bpy.context.object
                    ob.data.name = 'CubeMesh' + str(SplineBvhContainer.index) + '_' + str(i)
                    ob.name = 'Cube' + str(SplineBvhContainer.index) + '_' + str(i)
                    collectionCube.objects.link(ob)
                    bpy.context.view_layer.active_layer_collection.collection.objects.unlink(ob)
                    spline.append(ob)


        return {'FINISHED'}

class DelPoint(bpy.types.Operator):
    bl_idname = "ldops.del_point"
    bl_label = "Delete point"

    def execute(self, context):
        scene = context.scene
        
        spline_list = SplineBvhContainer.spline_list
        for spline in spline_list:
            for i in range(len(spline)):
                if bpy.context.view_layer.objects.active == spline[i]:
                    if len(spline) > 4:
                        bpy.ops.object.select_all(action='DESELECT')
                        spline[-1].select_set(True)
                        bpy.ops.object.delete()
                        del spline[-1]

        return {'FINISHED'}

def register():
    bpy.utils.register_class(SetPath)
    bpy.utils.register_class(ImportBvh)
    bpy.utils.register_class(GenerateJointAndBone)
    #bpy.utils.register_class(GenerateJointAndBoneConcat)
    bpy.utils.register_class(DrawBvhInitial)
    bpy.utils.register_class(CreateSpline)
    bpy.utils.register_class(AddPoint)
    bpy.utils.register_class(DelPoint)

def unregister():
    bpy.utils.unregister_class(SetPath)
    bpy.utils.unregister_class(ImportBvh)
    bpy.utils.unregister_class(GenerateJointAndBone)
    #bpy.utils.unregister_class(GenerateJointAndBoneConcat)
    bpy.utils.unregister_class(DrawBvhInitial)
    bpy.utils.unregister_class(CreateSpline)
    bpy.utils.unregister_class(AddPoint)
    bpy.utils.unregister_class(DelPoint)
