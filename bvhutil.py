import bpy
import os
import re

from math import radians, ceil
from mathutils import Vector, Matrix
import enum

class Channel(enum.IntEnum):
    XPOSITION = 0
    YPOSITION = 1
    ZPOSITION = 2
    ZROTATION = 3
    XROTATION = 4
    YROTATION = 5

class Offset():
    def __init__(self, x = 0, y = 0, z = 0):
        self.x = x
        self.y = y
        self.z = z

class Joint():
    def __init__(self):
        self._parent = None
        self._name = ""
        self._offset = None
        self._channels_order = []
        self._children = []
        self._channel_data = []
        self._localpos = []
        self._localrot = []
        self._object = None

    def Copy(self, otherJoint):
        self._parent = otherJoint.Parent
        self._name = otherJoint.Name
        self._offset = otherJoint.Offset
        self._channels_order = otherJoint.Channels_order
        self._children = otherJoint.Children
        self._channel_data = otherJoint.Channel_data
        self._localpos = otherJoint.LocalPos
        self._localrot = otherJoint.LocalRot

    @property 
    def Parent(self):
        return self._parent
    @Parent.setter
    def Parent(self, value):
        self._parent = value

    @property
    def Name(self):
        return self._name
    @Name.setter
    def Name(self, value):
        self._name = value

    @property
    def Offset(self):
        return self._offset
    @Offset.setter
    def Offset(self, value):
        self._offset = value
    
    @property
    def Channels_order(self):
        return self._channels_order
    @Channels_order.setter
    def Channels_order(self, value):
        self._channels_order = value
    
    @property
    def Children(self):
        return self._children
    @Children.setter
    def Children(self, value):
        self._children = value

    @property
    def Channel_data(self):
        return self._channel_data
    @Channel_data.setter
    def Channel_data(self, value):
        self._channel_data = value

    @property
    def LocalPos(self):
        return self._localpos
    @LocalPos.setter
    def LocalPos(self, value):
        self._localpos = value

    @property
    def LocalRot(self):
        return self._localrot
    @LocalRot.setter
    def LocalRot(self, value):
        self._localrot = value

    @property
    def Object(self):
        return self._object
    @Object.setter
    def Object(self, value):
        self._object = value

    def num_channels(self):
        return len(self._channels_order)

    def Add_motion_data(self, data):
        self._channel_data.append(data)

    def Set_localpos(self, pos, frame):
        if frame > 0 and frame < len(self._localpos):
            self._localpos[frame] = pos
        else:
            self._localpos.append(pos)

    def Set_localrot(self, rot, frame):
        if frame > 0 and frame < len(self._localrot):
            self._localrot[frame] = rot
        else:
            self._localrot.append(rot)

class Bvh():
    def __init__(self):
        self._root_joint = None
        self._joints = []
        self._num_frames = 0
        self._frame_time = 0
        self._num_channels = 0

    @property
    def Root_joint(self):
        return self._root_joint
    @Root_joint.setter
    def Root_joint(self, value):
        self._root_joint = value

    @property
    def Joints(self):
        return self._joints
    @Joints.setter
    def Joints(self, value):
        self._joints = value

    @property
    def Num_frames(self):
        return self._num_frames
    @Num_frames.setter
    def Num_frames(self, value):
        self._num_frames = value

    @property
    def Frame_time(self):
        return self._frame_time
    @Frame_time.setter
    def Frame_time(self, value):
        self._frame_time = value
    
    @property
    def Num_channels(self):
        return self._num_channels
    @Num_channels.setter
    def Num_channels(self, value):
        self._num_channels = value

    def Add_joint(self, joint):
        self._joints.append(joint)
        self._num_channels = self._num_channels + joint.num_channels()

    def Calculate(self, startJoint):
        localPos = Vector((startJoint.Offset.x, startJoint.Offset.y, startJoint.Offset.z))
        localRot = Vector((0, 0, 0))
        data = startJoint.Channel_data
        for i in range(self._num_frames):
            for j in range(len(startJoint.Channels_order)):
                channel_info = startJoint.Channels_order[j]
                if channel_info == Channel.XPOSITION:
                    localPos.x = localPos.x + data[i][j]
                elif channel_info == Channel.YPOSITION:
                    localPos.y = localPos.y + data[i][j]
                elif channel_info == Channel.ZPOSITION:
                    localPos.z = localPos.z + data[i][j]
                elif channel_info == Channel.XROTATION:
                    localRot.x = localRot.x + data[i][j]
                elif channel_info == Channel.YROTATION:
                    localRot.y = localRot.y + data[i][j]
                elif channel_info == Channel.ZROTATION:
                    localRot.z = localRot.z + data[i][j]
            startJoint.Set_localpos(localPos, i)
            startJoint.Set_localrot(localRot, i)
        
        for i in range(len(startJoint.Children)):
            self.Calculate(startJoint.Children[i])

    def GetJointInfo(self):
        for joint in self._joints:
            print("Joint : " + joint.Name)
            if not joint.Parent == None:
                print("Joint Parent: " + joint.Parent.Name)

            print("Joint Offset: " + str(joint.Offset.x) + " " + str(joint.Offset.y) + " " + str(joint.Offset.z))

            print("Joint Channel order : ")
            for i in range(joint.num_channels()):
                print(str(joint.Channels_order[i]))

            print("Joint Children : ")
            for child in joint._children:
                print(child.Name)

            if not joint.Name == KeyWord.kEndSite:
                for i in range(len(joint.Channel_data)):
                    print('Frame' + str(i) + ' :', end= ' ')
                    for j in range(len(joint.Channel_data[i])):
                        if not j == len(joint.Channel_data[i]) - 1:
                            print(str(joint.Channel_data[i][j]), end= ' ')
                        else:
                            print(str(joint.Channel_data[i][j]))
            print('---------------------------------------------')

class KeyWord():
    kChannels = "CHANNELS"
    kEnd = "End"
    kEndSite = "End Site"
    kFrame = "Frame"
    kFrames = "Frames:"
    kHierarchy = "HIERARCHY"
    kJoint = "JOINT"
    kMotion = "MOTION"
    kOffset = "OFFSET"
    kRoot = "ROOT"

    kXpos = "Xposition"
    kYpos = "Yposition"
    kZpos = "Zposition"
    kXrot = "Xrotation"
    kYrot = "Yrotation"
    kZrot = "Zrotation"

class BvhParser():
    def __init__(self):
        self._tokens = []
        self._tokenIndex = 0
        self._bvh = None
        self._debug = False

    def GetTokenInfo(self, path):
        if os.path.isfile(path):
            f = open(path, 'r')
            text = f.read()
            tokens = re.split(' |\t|\n', text)
            for token in tokens:
                if not token == '':
                    self._tokens.append(token)
        else:
            if self._debug:
                print("File Open Failed")

    def Parse(self, bvh):
        self._bvh = bvh
        token = self.GetToken()
        if token == KeyWord.kHierarchy:
            ret = self.Parse_Hierarchy()
            if ret < 0:
                if self._debug:
                    print('Parsing Hierarchy Error!')
                return ret
        else:
            if self._debug:
                print('Bad structure of .bvh file. ' + KeyWord.kHierarchy + ' should be on the top of the file');
            return -1;

        if self._debug:
            print('Successfully parse file!')

        #Create Children Relation
        for joint in self._bvh.Joints:
            parent = joint.Parent
            if parent in self._bvh.Joints:
                parent.Children.append(joint)
        
        return 0

    def Parse_Hierarchy(self):
        if self.CheckTokenIndex():
            token = self.GetToken()
            if token == KeyWord.kRoot:
                rootJoint = Joint()
                emptyJoint = None
                ret = self.Parse_Joint(emptyJoint, rootJoint)
                if ret < 0:
                    if self._debug:
                        print('Parsing Joint Error!')
                    return ret
                self._bvh.Root_joint = self._bvh.Joints[0]
            else:
                if self._debug:
                    print('Bad structure of .bvh file. Expected ' + KeyWord.kRoot + ", but found " + token)
                return -1

            #Parsing Motion
            if not self.CheckTokenIndex():
                return -1
            token = self.GetToken()
            if token == KeyWord.kMotion:
                ret = self.Parsing_Motion()
                if ret < 0:
                    if self._debug:
                        print('Parsing Motion Error!')
                    return ret
            else:
                if self._debug:
                    print('Bad structure of .bvh file. Expected ' + KeyWord.kMotion + ', but found ' + token)
                    return -1
        return 0
        
    def Parse_Joint(self, parent, parsed):
        if not self.CheckTokenIndex():
            return -1
        
        #Consuming '{'
        name = self.GetToken(2)
        joint = Joint()
        joint.Name = name
        joint.Parent = parent

        if self._debug:
            print('Joint name : ' + joint.Name)

        if not self.CheckTokenIndex():
            return -1

        #get offset
        token = self.GetToken()
        if token == KeyWord.kOffset:
            offset = []
            for i in range(3):
                if self.CheckTokenIndex():
                    offset.append(float(self.GetToken()))
                else:
                    if self._debug:
                        print('Failure Parsing ' + joint.Name + ' Offset Error!')
                        return -1
            joint.Offset = Offset(offset[0], offset[1], offset[2])
        else:
            if self._debug:
                print('Bad structure of .bvh file. Expected ' + KeyWord.kOffset + ", but found " + token)
                return -1

        if not self.CheckTokenIndex():
            return -1
        
        #Channel Parsing
        token = self.GetToken()
        if token == KeyWord.kChannels:
            ret = self.Parsing_Channel_Order(joint)
            if ret < 0:
                if self._debug:
                    print('Parsing Channel Failed!')
                return ret
        else:
            if self._debug:
                print('Bad structure of .bvh file. Expected ' + KeyWord.kChannels + ', but found ' + token);
            return -1; 

        self._bvh.Add_joint(joint)

        #Parsing Children Joint
        #children = []
        while self.CheckTokenIndex():
            token = self.GetToken()
            if token == KeyWord.kJoint:
                child = Joint()
                ret = self.Parse_Joint(joint, child)
                #children.append(child)
            elif token == KeyWord.kEnd:
                #Consuming 'Site' and '{'
                self._tokenIndex = self._tokenIndex + 2

                endJoint = Joint()
                endJoint.Parent = joint
                endJoint.Name = KeyWord.kEndSite
                #children.append(endJoint)

                if not self.CheckTokenIndex():
                    return -1
                token = self.GetToken()

                if token == KeyWord.kOffset:
                    offset = []
                    for i in range(3):
                        if self.CheckTokenIndex():
                            offset.append(float(self.GetToken()))
                        else:
                            if self._debug:
                                print('Failure Parsing ' + joint.Name + ' Offset Error!')
                                return -1
                    endJoint.Offset = Offset(offset[0], offset[1], offset[2])
                else:
                    if self._debug:
                        print('Bad structure of .bvh file. Expected ' + KeyWord.kOffset + ", but found " + token)
                        return -1
            
                #Consuming '}'
                self._tokenIndex = self._tokenIndex + 1
                self._bvh.Add_joint(endJoint)
            elif token == '}':
                #joint.Children = children
                #parsed = joint
                #parsed.Copy(joint)
                return 0

        if self._debug:
            print('Cannot parse joint, unexpected end of file. Last token : ' + token);
        return -1;

    def Parsing_Channel_Order(self, joint):
        if not self.CheckTokenIndex():
            return -1
        num = int(self.GetToken())

        channels = []
        for i in range(num):
            if self.CheckTokenIndex():
                token = self.GetToken()
                if token == KeyWord.kXpos:
                    channels.append(Channel.XPOSITION)
                elif token == KeyWord.kYpos:
                    channels.append(Channel.YPOSITION)
                elif token == KeyWord.kZpos:
                    channels.append(Channel.ZPOSITION)
                elif token == KeyWord.kXrot:
                    channels.append(Channel.XROTATION)
                elif token == KeyWord.kYrot:
                    channels.append(Channel.YROTATION)
                elif token == KeyWord.kZrot:
                    channels.append(Channel.ZROTATION)
                else:
                    if self._debug:
                        print('Invalid Channel!')
                    return -1
            else:
                return -1

        joint.Channels_order = channels
        return 0

    def Parsing_Motion(self):
        if not self.CheckTokenIndex():
            return -1
        token = self.GetToken()
        if token == KeyWord.kFrames:
            if not self.CheckTokenIndex():
                return -1
            self._bvh.Num_frames = int(self.GetToken())
        else:
            if self._debug:
                print('Bad structure of .bvh file. Expected ' + KeyWord.kFrames + ', but found ' + token)
            return -1

        if not self.CheckTokenIndex():
            return -1
        
        #Consuming 'Time:'
        token = self.GetToken(2)
        if token == KeyWord.kFrame:
            if not self.CheckTokenIndex():
                return -1
            self._bvh.Frame_time = float(self.GetToken())
            for i in range(self._bvh.Num_frames):
                for joint in self._bvh.Joints:
                    data = []
                    for j in range(joint.num_channels()):
                        if self.CheckTokenIndex():
                            num = float(self.GetToken())
                            data.append(num)
                        else:
                            return -1
                    joint.Add_motion_data(data)
        else:
            if self._debug:
                print('Bad structure of .bvh file. Expected ' + KeyWord.kFrame + ', but found ' + token)
            return -1
        return 0

    def GetToken(self, offset = 1):
        token = self._tokens[self._tokenIndex]
        self._tokenIndex = self._tokenIndex + offset
        return token

    def CheckTokenIndex(self):
        if self._tokenIndex >= len(self._tokens):
            if self._debug:
                print('Parsing Error!')
            return False
        else:
            return True