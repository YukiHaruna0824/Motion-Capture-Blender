import bpy
import os
from .bvhutil import *


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

        bvh = Bvh()
        bp = BvhParser()
        bp.GetTokenInfo(self.filepath)
        if bp.Parse(bvh) == 0:
            bvh.GetJointInfo()
        return {'FINISHED'}


class CreateSpline(bpy.types.Operator):
    """Create Spline"""
    bl_idname = "ldops.create_spline"
    bl_label = "Add spline"

    def execute(self, context):
        scene = context.scene
        pref = scene.setting
        # print all objects
        for obj in bpy.data.objects:
            print(obj.name)
            if("Curve" in obj.name):
                print("found")
                scene.collection.objects.unlink(obj)
                bpy.data.objects.remove(obj)

        for cur in bpy.data.curves:
            print(cur.name)
            bpy.data.curves.remove(cur)

        # sample data
        coords = [(1,0,1), (2,0,0), (3,0,1)]

        # create the Curve Datablock
        curveData = bpy.data.curves.new('myCurve', type='CURVE')
        curveData.dimensions = '3D'
        curveData.resolution_u = 2

        # map coords to spline
        polyline = curveData.splines.new('BEZIER')
        polyline.bezier_points.add(len(coords)-1)
        for i, coord in enumerate(coords):
            x,y,z = coord
            polyline.bezier_points[i].co = (x, y, z)
            polyline.bezier_points[i].handle_left = (x-0.5, y, z)
            polyline.bezier_points[i].handle_right = (x+0.5, y, z)

        # create Object
        curveOB = bpy.data.objects.new('myCurve', curveData)
        curveData.bevel_depth = 0.01

        # attach to scene and validate context
        scene.collection.objects.link(curveOB)
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = curveOB
        curveOB.select_set(True)
        return {'FINISHED'}



def register():
    bpy.utils.register_class(ImportBvh)
    bpy.utils.register_class(CreateSpline)

def unregister():
    bpy.utils.unregister_class(ImportBvh)
    bpy.utils.unregister_class(CreateSpline)
