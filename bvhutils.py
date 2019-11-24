import bpy
from mathutils import Vector, Euler, Matrix
from math import radians, ceil

class Joint:
    __slots__ = (
        # Bvh joint name.
        'name',
        # BVH_Node type or None for no parent.
        'parent',
        # A list of children of this type..
        'children',
        # Worldspace rest location for the head of this node.
        'rest_head_world',
        # Localspace rest location for the head of this node.
        'rest_head_local',
        # Worldspace rest location for the tail of this node.
        'rest_tail_world',
        # Worldspace rest location for the tail of this node.
        'rest_tail_local',
        # List of 6 ints, -1 for an unused channel,
        # otherwise an index for the BVH motion data lines,
        # loc triple then rot triple.
        'channels',
        # A triple of indices as to the order rotation is applied.
        # [0,1,2] is x/y/z - [None, None, None] if no rotation..
        'rot_order',
        # Same as above but a string 'XYZ' format..
        'rot_order_str',
        # A list one tuple's one for each frame: (locx, locy, locz, rotx, roty, rotz),
        # euler rotation ALWAYS stored xyz order, even when native used.
        'anim_data',
        # Convenience function, bool, same as: (channels[0] != -1 or channels[1] != -1 or channels[2] != -1).
        'has_loc',
        # Convenience function, bool, same as: (channels[3] != -1 or channels[4] != -1 or channels[5] != -1).
        'has_rot',
        # Index from the file, not strictly needed but nice to maintain order.
        'index',
        # Use this for whatever you want.
        'temp',
    )

    _eul_order_lookup = {
        (None, None, None): 'XYZ',  # XXX Dummy one, no rotation anyway!
        (0, 1, 2): 'XYZ',
        (0, 2, 1): 'XZY',
        (1, 0, 2): 'YXZ',
        (1, 2, 0): 'YZX',
        (2, 0, 1): 'ZXY',
        (2, 1, 0): 'ZYX',
    }

    def __init__(self, name, rest_head_world, rest_head_local, parent, channels, rot_order, index):
        self.name = name
        self.rest_head_world = rest_head_world
        self.rest_head_local = rest_head_local
        self.rest_tail_world = None
        self.rest_tail_local = None
        self.parent = parent
        self.channels = channels
        self.rot_order = tuple(rot_order)
        self.rot_order_str = Joint._eul_order_lookup[self.rot_order]
        self.index = index

        # convenience functions
        self.has_loc = channels[0] != -1 or channels[1] != -1 or channels[2] != -1
        self.has_rot = channels[3] != -1 or channels[4] != -1 or channels[5] != -1

        self.children = []

        # List of 6 length tuples: (lx, ly, lz, rx, ry, rz)
        # even if the channels aren't used they will just be zero.
        #self.anim_data = [(0, 0, 0, 0, 0, 0)]
        self.anim_data = []

    def __repr__(self):
        return (
            "BVH name: '%s', rest_loc:(%.3f,%.3f,%.3f), rest_tail:(%.3f,%.3f,%.3f)" % (
                self.name,
                *self.rest_head_world,
                *self.rest_head_world,
            )
        )

class Bvh():
    def __init__(self):
        #key : name, value : class Joint
        self.joints = {}
        self.rootJoint = None
        self.frame_time = 0
        self.frame_count = 0
        self.bvh_path = None
        
    def read_bvh(self, file_path):
        file = open(file_path, 'rU')
        file_lines = file.readlines()
        if len(file_lines) == 1:
            file_lines = file_lines[0].split('\r')
        
        file_lines = [ll for ll in [l.split() for l in file_lines] if ll]
        
        if file_lines[0][0].lower() == 'hierarchy':
            pass
        else:
            raise Exception("This is not a BVH file")
        
        self.joints = {None: None}
        joint_serial = [None]
        channelIndex = -1
        isRoot = False

        lineIdx = 0
        while lineIdx < len(file_lines) - 1:
            if file_lines[lineIdx][0].lower() in {'root', 'joint'}:
                #get root joint
                isRoot = False
                if file_lines[lineIdx][0].lower() == 'root':
                    isRoot = True

                #Joint name
                name = file_lines[lineIdx][1]
                
                #get offset
                lineIdx += 2
                rest_head_local = Vector((
                    float(file_lines[lineIdx][1]),
                    float(file_lines[lineIdx][2]),
                    float(file_lines[lineIdx][3]),
                ))

                #get channel
                lineIdx += 1
                channels = [-1, -1, -1, -1, -1, -1]
                rot_orders = [None, None, None]
                rot_count = 0
                for channel in file_lines[lineIdx][2:]:
                    channel = channel.lower()
                    channelIndex += 1
                    if channel == 'xposition':
                        channels[0] = channelIndex
                    elif channel == 'yposition':
                        channels[1] = channelIndex
                    elif channel == 'zposition':
                        channels[2] = channelIndex

                    elif channel == 'xrotation':
                        channels[3] = channelIndex
                        rot_orders[rot_count] = 0
                        rot_count += 1
                    elif channel == 'yrotation':
                        channels[4] = channelIndex
                        rot_orders[rot_count] = 1
                        rot_count += 1
                    elif channel == 'zrotation':
                        channels[5] = channelIndex
                        rot_orders[rot_count] = 2
                        rot_count += 1
                
                parent = joint_serial[-1]
                #Add the parent offset
                if parent is None:
                    rest_head_world = Vector(rest_head_local)
                else:
                    rest_head_world = parent.rest_head_world + rest_head_local
                
                joint = self.joints[name] = Joint(
                    name,
                    rest_head_world,
                    rest_head_local,
                    parent,
                    channels,
                    rot_orders,
                    len(self.joints) - 1,
                )
                if isRoot:
                    self.rootJoint = joint
                joint_serial.append(joint)

            if file_lines[lineIdx][0].lower() == 'end' and file_lines[lineIdx][1].lower() == 'site':
                #get offset
                lineIdx += 2
                rest_tail = Vector((
                    float(file_lines[lineIdx][1]),
                    float(file_lines[lineIdx][2]),
                    float(file_lines[lineIdx][3]),
                ))
                
                joint_serial[-1].rest_tail_world = joint_serial[-1].rest_head_world + rest_tail
                joint_serial[-1].rest_tail_local = joint_serial[-1].rest_head_local + rest_tail
                joint_serial.append(None)
            
            #remove serial joint
            if len(file_lines[lineIdx]) == 1 and file_lines[lineIdx][0] == '}':
                joint_serial.pop()

            #End of Hierarchy
            if len(file_lines[lineIdx]) == 1 and file_lines[lineIdx][0].lower() == 'motion':
                lineIdx += 1  # Read frame
                if (len(file_lines[lineIdx]) == 2 and file_lines[lineIdx][0].lower() == 'frames:'):
                    self.frame_count = int(file_lines[lineIdx][1])

                lineIdx += 1  # Read frame rate.
                if (len(file_lines[lineIdx]) == 3 and file_lines[lineIdx][0].lower() == 'frame' and file_lines[lineIdx][1].lower() == 'time:'):
                    self.frame_time = float(file_lines[lineIdx][2])
                lineIdx += 1  # get the first frame
                break
            lineIdx += 1
        
        del self.joints[None]
        del joint_serial

        joint_list = list(self.joints.values())
        joint_list.sort(key=lambda joint: joint.index)
        
        while lineIdx < len(file_lines):
            line = file_lines[lineIdx]
            for joint in joint_list:
                lx = ly = lz = rx = ry = rz = 0.0
                channels = joint.channels
                anim_data = joint.anim_data
                if channels[0] != -1:
                    lx = float(line[channels[0]])
                if channels[1] != -1:
                    ly = float(line[channels[1]])
                if channels[2] != -1:
                    lz = float(line[channels[2]])
                
                if channels[3] != -1 or channels[4] != -1 or channels[5] != -1:
                    rx = radians(float(line[channels[3]]))
                    ry = radians(float(line[channels[4]]))
                    rz = radians(float(line[channels[5]]))
                anim_data.append((lx, ly, lz, rx, ry, rz))
            lineIdx += 1

        #Assign children
        for joint in joint_list:
            parent = joint.parent
            if parent:
                joint.parent.children.append(joint)
        
        #Set tail for each joint
        for joint in joint_list:
            if not joint.rest_tail_world:
                if len(joint.children) == 0:
                    joint.rest_tail_world = Vector(joint.rest_head_world)
                    joint.rest_tail_local = Vector(joint.rest_head_local)
                elif len(joint.children) == 1:
                    joint.rest_tail_world = Vector(joint.children[0].rest_head_world)
                    joint.rest_tail_local = joint.rest_head_local + joint.children[0].rest_head_local
                else:
                    rest_tail_world = Vector((0.0, 0.0, 0.0))
                    rest_tail_local = Vector((0.0, 0.0, 0.0))
                    for child in joint.children:
                        rest_tail_world += child.rest_head_world
                        rest_tail_local += child.rest_head_local

                    joint.rest_tail_world = rest_tail_world * (1.0 / len(joint.children))
                    joint.rest_tail_local = rest_tail_local * (1.0 / len(joint.children))
                    
    def add_joint(self, context, frame_start):
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
        for name, joint in self.joints.items():
            joint.temp = add_ob(name)
            joint.temp.rotation_mode = joint.rot_order_str[::-1]
        
        #Set Parent
        for joint in self.joints.values():
            for child in joint.children:
                child.temp.parent = joint.temp
        
        #Set location
        for joint in self.joints.values():
            joint.temp.location = joint.rest_head_local

        #Add tail objects
        for name, joint in self.joints.items():
            if not joint.children:
                ob_end = add_ob(name + '_end')
                ob_end.parent = joint.temp
                ob_end.location = joint.rest_tail_world - joint.rest_head_world
        
        for name, joint in self.joints.items():
            obj = joint.temp
            for fc in range(len(joint.anim_data)):
                if self.bvh_path != None:
                    A = Matrix([self.bvh_path[0].location, self.bvh_path[1].location, self.bvh_path[2].location, self.bvh_path[3].location])
                    A_invert = A.inverted()
                    lx, ly, lz, rx, ry, rz = joint.anim_data[fc] @ A

                if joint.has_loc:
                    obj.delta_location = Vector((lx, ly, lz)) - joint.rest_head_world
                    obj.keyframe_insert("delta_location", index=-1, frame=frame_start + fc)
                
                if joint.has_rot:
                    obj.delta_rotation_euler = rx, ry, rz
                    obj.keyframe_insert("delta_rotation_euler", index=-1, frame=frame_start + fc)

    def add_armature(self, context, frame_start):
        if frame_start < 1:
            frame_start = 1

        scene = context.scene
        for obj in scene.objects:
            obj.select_set(False)

        arm_data = bpy.data.armatures.new('test')
        arm_ob = bpy.data.objects.new('test', arm_data)
        context.collection.objects.link(arm_ob)
        
        arm_ob.select_set(True)
        context.view_layer.objects.active = arm_ob

        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
        bpy.ops.object.mode_set(mode='EDIT', toggle=False)

        joint_list = list(self.joints.values())
        joint_list.sort(key=lambda joint: joint.index)

    def getTimeStamp(self):
        total_d = 0
        accumulate_d = [0] * len(self.rootJoint.anim_data)

        for index in range(1, len(self.rootJoint.anim_data)):
            last = Vector((self.rootJoint.anim_data[index - 1][0:3]))
            current = Vector((self.rootJoint.anim_data[index][0:3]))
            accumulate_d[index] = accumulate_d[index - 1] + (current - last).length
            total_d += (current - last).length
        timestamp = [(d / total_d) for d in accumulate_d]
        return timestamp

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

    # return  4 control points (Matrix 4 * 3) and sample point (List of Vector)
    def getRootJointPath(self):

        timestamp = self.getTimeStamp()

        A = Matrix([[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]])
        for row in range(4):
            for col in range(4):
                for fc in range(self.frame_count):
                    t = timestamp[fc]
                    A[row][col] += float(self.getCubicConstant(t, row) * self.getCubicConstant(t, col))

        B = Matrix([[0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0]])
        for row in range(4):
            for fc in range(self.frame_count):
                lx, ly, lz, rx, ry, rz = self.rootJoint.anim_data[fc]
                t = timestamp[fc]
                B[row] += self.getCubicConstant(t, row) * Vector((lx, ly, lz))

        A_invert = A.inverted()
        # P = A^-1 * B
        P = A_invert @ B

        '''
        print(A)
        print(A_invert)
        print(B)
        print(P)
        '''

        points = []
        for t in timestamp:
            point = Vector((0, 0, 0))
            for index in range(4):
                point += self.getCubicConstant(t, index) * P[index]
            points.append(point)

        #print(points)

        originalPoints = []
        for fc in range(self.frame_count):
            location = Vector((self.rootJoint.anim_data[fc][0:3]))
            originalPoints.append(location)

        return P, points , originalPoints