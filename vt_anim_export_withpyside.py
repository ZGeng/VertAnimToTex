# covert vertex animation into shader readable maps for Unity
# export the vertex motion into maps
# this script will not change the state of maya scene

import struct
import pymel.core as pm
from maya import OpenMaya
import math
from PySide2 import QtGui
pm_Color = pm.datatypes.Color
QImage = QtGui.QImage

Epsilon = 1e-6


# get selection shape
def get_sel_shape():
    shapeNode = None
    try:
        shapeNode = pm.selected()[0].getShape()
    except AttributeError:
        print "Please select one mesh"
    return shapeNode


def vt_uv_map(shapeNode):
    # vertex id as key and UVs id list as value
    # will change into api function
    vt_UV = {}
    vertexs = shapeNode.vtx

    for vt_id, vertex in enumerate(vertexs):
        # check if already create key for the vertex id
        Us, Vs, FaceIds = vertex.getUVs()
        UVs = zip(Us, Vs)
        vt_UV[vt_id] = list(set(UVs))  # remove duplicate
    return vt_UV


def get_vertex_tangent_ids(shapeNode):
    result = []
    for vt_id, vertex in enumerate(shapeNode.vtx):
        ids = []
        for face in vertex.connectedFaces():
            ids.append(shapeNode.getTangentId(face.currentItemIndex(), vt_id))
        result.append(ids)
    return result


def get_per_vertex_tangent(tangentList, tangent_ids, vt_id, normal):
    total = pm.datatypes.Vector()
    for tangent_id in tangent_ids[vt_id]:
        total += tangentList[tangent_id]
    total.normalize()
    # Orth with Gram_Schmidt method
    tangent = total - normal * total.dot(normal)
    return tangent


def vt_info_list(shapeNode, tangent_ids, tangentList):
    vt_infos = []
    vertexs = shapeNode.vtx
    # iterate throgh all the vertex
    for vt_id, vertex in enumerate(vertexs):
        position = vertex.getPosition(space="object")

        normal = vertex.getNormal(space="object")  # one or more?
        tangent = get_per_vertex_tangent(tangentList, tangent_ids,
                                         vt_id, normal)
        # build a map
        info = {"Position": position,
                "Normal": normal, "Tangent": tangent}
        vt_infos.append(info)
    return vt_infos


def get_dis_buffer(startFrame, endFrame, shapeNode):

    time = endFrame - startFrame + 1
    # get the current frame
    oldFrame = pm.getCurrentTime()
    # set the current time to the start time
    # prepare tangent data
    tangentList = shapeNode.getTangents(space="object")
    tangent_ids = get_vertex_tangent_ids(shapeNode)
    # get the info data
    vt_infoList = vt_info_list(shapeNode, tangent_ids, tangentList)
    pm.setCurrentTime(startFrame)
    # create a vt_id list to record the moved vertex id
    moved_vt_id = set()
    # creat wrap list to store data and initalize it
    dis_buffer = []

    def dis_list(frame):
        # get current frame vertex position
        result = []

        pm.setCurrentTime(frame)
        vt_infoList_cur = vt_info_list(shapeNode, tangent_ids, tangentList)

        for vt_id, vt_info in enumerate(vt_infoList):
            pos_trans = vectorDiff(vt_infoList[vt_id]["Position"],
                                   vt_infoList_cur[vt_id]["Position"])
            pos_color = convert_vector_to_argb(pos_trans)

            normal_trans = vectorDiff(vt_infoList[vt_id]["Normal"],
                                      vt_infoList_cur[vt_id]["Normal"])
            normal_color = convert_vector_to_argb(normal_trans)

            tangent_trans = vectorDiff(vt_infoList[vt_id]["Tangent"],
                                       vt_infoList_cur[vt_id]["Tangent"])
            tangent_color = convert_vector_to_argb(tangent_trans)

            dis_info = {"Position": pos_color,
                        "Normal": normal_color,
                        "Tangent": tangent_color}
            result.append(dis_info)

            if ((not vectorEqualZero(pos_trans)) or
               (not vectorEqualZero(normal_trans))): # or
               # (not vectorEqualZero(tangent_trans))):
                moved_vt_id.add(vt_id)  # modify the outside list

        return result

    for shiftFrame in range(time):
        currentFrame = startFrame + shiftFrame
        dis_buffer.append(dis_list(currentFrame))

    # setback the old time
    pm.setCurrentTime(oldFrame)
    moved_vt_id_list = list(moved_vt_id)

    return dis_buffer, moved_vt_id_list


# post buffer clean up
def buffer_resort(data):
    return zip(*data)  # remap data


# ---------------------VECTOR-OPERATION---------------------------#

def vectorDiff(v1, v2):
    size = len(v1)
    try:
        result = [v2[i] - v1[i] for i in range(size)]
        return result
    except:
        print 'cannot do vecter diff'
        return None


def vectorEqualZero(v):
    total = 0
    for value in v:
        total += value * value
    return total <= Epsilon


# -------------------PIXEL-CONVERTION-----------------------------#


def convert_vector_to_argb(v):
    scale = 1

    scale = int(math.ceil(math.sqrt(v[0]**2 + v[1]**2 + v[2]**2)))
    if scale > 255:
        print 'unable to convert displacement vector into color'

    if scale == 0:
        return struct.pack("I", 0)

    R = int(round(127.5 + 127.5 * (v[0] / scale)))  # 127.5 is half 255
    G = int(round(127.5 + 127.5 * (v[1] / scale)))
    B = int(round(127.5 + 127.5 * (v[2] / scale)))
    A = scale
    pixel = A * 256 * 256 * 256 + R * 256 * 256 + G * 256 + B
    return struct.pack("I", pixel)


def convert_int_to_argb(num):
    # alpha channel is 0
    return struct.pack('I', num)


def convert_two_int_argb(num1, num2):
    # AR--num1 GB--num2
    return struct.pack('I', num1 * 256 * 256 + num2)


def imageWriteInt(imgData_ptr, size, u, v, value):
    x = int(size * u) % size
    y = int(size * v) % size
    index = 4 * (y * size + x)

    try:
        if not imgData_ptr[index: index + 4] == chr(0) * 4:
            raise RuntimeError(
                'Vertex map to same pixel,'
                ' try to enlarge the image size or readjust the UV')
        imgData_ptr[index: index + 4] = convert_int_to_argb(value)
        # not modify the imgData pointer
    except:
        print x, y
    return


def data_image_size(frameNum, vtNum):
    # vtNum is the moved vt number
    pixelNum = 3 * frameNum * (vtNum + 1) + 1
    # 3 pixel per vertex per frame
    # two extra pixels used for
    # 1  first line is to store the zero value
    # 2 last pixel is to store the frameNum,vtNum information
    size = int(math.pow(2, math.ceil(math.log(pixelNum, 4))))
    # get the dimention of the image
    return size


def create_data_img(size):
    img = QImage(size, size, QImage.Format_ARGB32)
    img.fill(0)
    return img


def create_index_img(size=32):
    img = QImage(size, size, QImage.Format_ARGB32)
    # fill the image with empty color
    img.fill(0)
    return img

def convert_int_to_color(num):
    R = num // (256 * 256)
    if R > 255:
        R = 255
    G = (num - R * 256 * 256) // 256
    B = num - R * 256 * 256 - G * 256
    return pm_Color([R/255.0, G/255.0, B/255.0, 1.0])


def set_index_img(shapeNode, img, moved_vtList, vt_uv):
    # get the index in the moved_vt
    # image size
    size = img.width()  # assume width equals height
    imgData_ptr = img.bits()  # load img data
    # debug to print out all the buffer data
    vertexs = shapeNode.vtx

    for vtId in vt_uv: # vt_uv is a dict
        if vtId not in moved_vtList:
            # write to the empty cell
            # value = 255 * 256 * 256 * 256
            value = 0

            # set vertex color
            vt_color = pm_Color([0.0, 0.0, 0.0, 0.0])
            vertexs[vtId].setColor(vt_color)


            for UVs in vt_uv[vtId]:  # this can wrap into imageWrite Function
                u, v = UVs
                imageWriteInt(imgData_ptr, size, u, v, value)
        else:

            value = moved_vtList.index(vtId) + 1

            # set vertex color
            vt_color = convert_int_to_color(value)
            vertexs[vtId].setColor(vt_color)

            
            value += 255 * 256 * 256 * 256
            for UVs in vt_uv[vtId]:
                u, v = UVs
                imageWriteInt(imgData_ptr, size, u, v, value)

    return  # the img should be modified


def set_data_img(img, frameNum, vtNum, bufferData, vtIds):
    imgData_ptr = img.bits()  # load image data
    buffer_size = img.byteCount()
    # creat an empty framNum elements
    currentPosition = 0  # current data list positon

    for i in range(frameNum * 3):
        # get x and y position
        imgData_ptr[i * 4: i * 4 + 4] = struct.pack("I", 0)

    currentPosition = frameNum * 3

    for vtId in vtIds:
        for i in range(frameNum):
            # get x and y position
            # retrive the data
            # print len(bufferData)
            data = bufferData[vtId][i]
            # put data into image
            imgData_ptr[currentPosition * 4:
                        currentPosition * 4 + 4] = data["Position"]
            imgData_ptr[currentPosition * 4 + 4:
                        currentPosition * 4 + 8] = data["Normal"]
            imgData_ptr[currentPosition * 4 + 8:
                        currentPosition * 4 + 12] = data["Tangent"]
            currentPosition += 3
    # And last pixel, write the frameNum and vtId size data
    vt_size = len(vtIds)
    # convert 2 int into RGBA
    info_color = convert_two_int_argb(frameNum, vt_size)
    # write the info color in to last pixel
    imgData_ptr[buffer_size - 4: buffer_size] = info_color

    return

# ------------------MAIN-TEX-GENRATOR----------------------------#


indexSize = [32, 64, 128, 256, 512, 1024, 2048]


def generateTextures(shapeNode, start, end, size_index, path):
    vt_uv = vt_uv_map(shapeNode)  # result is UV lists map
    # name = shapeNode.name()
    # print vt_uv
    data, vtIds = get_dis_buffer(start, end, shapeNode)
    index_img = create_index_img(indexSize[size_index])
    set_index_img(shapeNode, index_img, vtIds, vt_uv)
    index_img.save('%s_index.png' % (path))

    data = buffer_resort(data)
    vtId_size = len(vtIds)
    frameNum = end - start + 1  # if end smaller than start raise error
    data_img_size = data_image_size(frameNum, vtId_size)
    data_img = create_data_img(data_img_size)
    set_data_img(data_img, frameNum, vtId_size, data, vtIds)
    data_img.save('%s_data.png' % (path))
    return


# ----------------TEST-FUNCTIONS-------------------------------#

def indexImageTest(startFrame, endFrame):
    shapeNode = get_sel_shape()
    vt_uv = vt_uv_map(shapeNode)  # result is UV lists map
    # print vt_uv
    data, vtIds = get_dis_buffer(startFrame, endFrame, shapeNode)
    print type(vtIds)
    img = create_index_img(64)
    set_index_img(img, vtIds, vt_uv)

    img.save('C:/mypy/indexImageTest.png', 'PNG')
    return


def dataImageTest(startFrame, endFrame):
    shapeNode = get_sel_shape()
    data, vtIds = get_dis_buffer(startFrame, endFrame, shapeNode)
    data = buffer_resort(data)
    vtId_size = len(vtIds)
    frameNum = endFrame - startFrame + 1
    img_size = data_image_size(frameNum, vtId_size)
    img = create_data_img(img_size)
    set_data_img(img, frameNum, vtId_size, data, vtIds)

    img.save('C:/mypy/dataImageTest.png', 'PNG')
    return


def dataTest(startFrame, endFrame):
    shapeNode = get_sel_shape()
    data, vtIds = get_dis_buffer(startFrame, endFrame, shapeNode)
    new_data = buffer_resort(data)
    new_data = [j for i, j in enumerate(new_data) if i in vtIds]
    return len(new_data)
