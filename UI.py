from PySide2 import QtCore, QtGui, QtWidgets
import pymel.core as pm
import maya.OpenMaya as om
import maya.OpenMayaUI as omui
from shiboken2 import wrapInstance
import vt_anim_export_withpyside as vae
import os


def get_sel_shape():
    shapeNode = None
    try:
        shapeNode = pm.selected()[0].getShape()
    except:
        # print "Please select one mesh"
        shapeNode = None
    return shapeNode


def get_maya_window():
    main_window_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(long(main_window_ptr), QtWidgets.QWidget)


@QtCore.Slot(object)
def exportTexCallback(values):
    # vae.createTex(*values)
    vae.generateTextures(*values)
    print "success"

    def test(name, start, end, size, path):
        print name
        print start
        print end
        print size
        print path
    test(*values)


elementList = [
    {"name": "meshLable", "type": QtWidgets.QLabel,
        "position": (0, 0, 1, 1), "arg": ["mesh"], "parent":"None"},
    {"name": "objectLable", "type": QtWidgets.QLabel,
        "position": (0, 1, 1, 3), "arg": [" "], "parent":"None"},
    {"name": "setting", "type": QtWidgets.QGroupBox,
     "position": (1, 0, 4, 4), "arg": ["Setting"], "parent":"None"},
    {"name": "frameLable_1", "type": QtWidgets.QLabel,
        "position": (2, 0, 1, 1), "arg": [" Start Frame"], "parent":"setting"},
    {"name": "startFrame", "type": QtWidgets.QSpinBox,
        "position": (2, 1, 1, 1), "arg": [], "parent":"setting"},
    {"name": "frameLable_2", "type": QtWidgets.QLabel,
        "position": (2, 2, 1, 1), "arg": [" End Frame"], "parent":"setting"},
    {"name": "endFrame", "type": QtWidgets.QSpinBox,
        "position": (2, 3, 1, 1), "arg": [], "parent":"setting"},
    {"name": "indexTexSizeLable", "type": QtWidgets.QLabel,
     "position": (3, 0, 1, 2), "arg": [" indexTexSize"], "parent":"setting"},
    {"name": "indexTexSize", "type": QtWidgets.QComboBox,
        "position": (3, 2, 1, 2), "arg": [], "parent":"setting"},
    {"name": "fileDirLabel", "type": QtWidgets.QLabel,
     "position": (4, 0, 1, 1), "arg": ["  Save As"], "parent":"setting"},
    {"name": "fileDirButton", "type": QtWidgets.QPushButton,
        "position": (4, 1, 1, 1), "arg": [''], "parent":"setting"},
    {"name": "fileDir", "type": QtWidgets.QLineEdit,
     "position": (4, 2, 1, 2), "arg": [], "parent":"setting"},
    {"name": "info", "type": QtWidgets.QLabel,
     "position": (5, 0, 1, 2), "arg": ["......"], "parent":"None"},
    {"name": "exportButton", "type": QtWidgets.QPushButton,
     "position": (5, 2, 1, 2), "arg": ["Export"], "parent":"None"}
]


class UILayout(QtWidgets.QMainWindow):
    export = QtCore.Signal(object)

    def setMesh(self, *args, **kwargs):
        self.dagPath = get_sel_shape()
        labelText = " "
        if not(self.dagPath is None):
            labelText = self.dagPath.nodeName()
        self.elements["objectLable"].setText(labelText)

    def __init__(self, parent=get_maya_window()):
        super(UILayout, self).__init__(parent)
        self.setWindowTitle('VertAnimToTex')
        self.setFixedSize(350, 200)
        self.elements = dict()
        self.container = QtWidgets.QWidget(self)
        self.exportedData = ["dagPath", 0, 10, 1, "filePath"]
        self.idx = om.MEventMessage.addEventCallback(
            "SelectionChanged", self.setMesh)
        self.dagPath = None

    def createLayout(self, elementList):

        grid = QtWidgets.QGridLayout()
        for element in elementList:
            name = element["name"]
            pos = element["position"]
            arg = element["arg"]
            widget_parent_name = element["parent"]
            widget_parent = self.container  # default
            if (widget_parent_name != "None"):
                widget_parent = self.elements[widget_parent_name]
            widget = element["type"](*arg)
            widget.setParent(widget_parent)
            self.elements[name] = widget
            grid.addWidget(widget, pos[0], pos[1], pos[
                           2], pos[3])

        self.container.setLayout(grid)
        self.setCentralWidget(self.container)

    def exportOnClick(self):  # define the function to send out message
        self.updateExportedData()
        self.export.emit(self.exportedData)

    def dirOnClick(self):
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save File", os.getcwd())
        self.elements["fileDir"].setText(path)
        return path

    def updateExportedData(self):
        self.exportedData[0] = self.dagPath
        self.exportedData[1] = self.elements["startFrame"].value()
        self.exportedData[2] = self.elements["endFrame"].value()
        self.exportedData[3] = self.elements["indexTexSize"].currentIndex()
        self.exportedData[4] = self.elements["fileDir"].text()

    def closeEvent(self, event):
        om.MMessage.removeCallback(self.idx)
        event.accept()  # let the window close


def setupElement(uiWindow):
    uiWindow.elements["startFrame"].setMaximum(300)
    uiWindow.elements["endFrame"].setMaximum(300)
    fileButton = uiWindow.elements["fileDirButton"]
    fileButton.setIcon(
        fileButton.style().standardIcon(QtWidgets.QStyle.SP_DirIcon))
    indexTexSize = uiWindow.elements["indexTexSize"]
    indexTexSize.addItems(["32*32", "64*64", "128*128",
                           "256*256", "512*512", "1024*1024","2048*2048"])
    indexTexSize.setCurrentIndex(1)


def setupEvent(uiWindow):
    # inside function connection
    exportButton = uiWindow.elements["exportButton"]
    exportButton.clicked.connect(uiWindow.exportOnClick)

    fileButton = uiWindow.elements["fileDirButton"]
    fileButton.clicked.connect(uiWindow.dirOnClick)
    # outside function connection
    uiWindow.export.connect(exportTexCallback)


def main():
    # app = QtWidgets.QApplication([])
    # assign a callback function

    win = UILayout(get_maya_window())
    win.createLayout(elementList)
    setupElement(win)
    setupEvent(win)

    win.show()
    print 'executing'
    # win.exec_()
    return
