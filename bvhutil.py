import bpy
from mathutils import Vector,Matrix
import enum

class Channel(enum.IntEnum):
    XPOSITION = 0
    YPOSITION = 1
    ZPOSITION = 2
    ZROTATION = 3
    XROTATION = 4
    YROTATION = 5

class Offset():
    def __init__(self, x, y, z):
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

    def num_channels(self):
        return len(self._channels_order)

    def Add_motion_data(self, data):
        self._channel_data.append(data)

    def Set_localpos(self, pos, frame):
        if frame > 0 and frame < len(self._localpos):
            _localpos[frame] = pos
        else:
            _localpos.append(pos)

    def Set_localrot(self, rot, frame):
        if frame > 0 and frame < len(_localrot):
            _localrot[frame] = rot
        else:
            _localrot.append(rot)

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
        localPos = Vector(startJoint.Offset.x, startJoint.Offset.y, startJoint.Offset.z)
        localRot = Vector(0, 0, 0)
        data = startJoint.Channel_data
        for i in range(len(self._num_frames)):
            for j in range(len(startJoint.Channels_order)):
                channel_info = startJoint.Channels_order[index]
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

class KeyWord:
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

    def GetTokenInfo(self, path):


    def Parse(self, bvh):
