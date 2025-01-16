"""
Skin Weights to mesh converter tool.
"""

from functools import partial
from logging import getLogger

import maya.cmds as cmds
from PySide2.QtCore import Qt
from PySide2.QtGui import QIntValidator
from PySide2.QtWidgets import (
    QGridLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from ..command import convert_weight
from ..lib import lib_skinCluster
from ..lib_ui import maya_qt, maya_ui, optionvar
from ..lib_ui.widgets import extra_widgets

logger = getLogger(__name__)


class SkinWeightsMeshConverterWidgets(QWidget):

    def __init__(self, parent=None):
        """Constructor.
        """
        super().__init__(parent=parent)

        self.tool_options = optionvar.ToolOptionSettings(__name__)

        self.preview_mesh = None
        self.preview_mesh_node = None

        self.main_layout = QVBoxLayout()

        layout = QGridLayout()

        label = QLabel('Mesh Divisions:', alignment=Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(label, 0, 0)

        self.mesh_div_field = QLineEdit()
        self.mesh_div_field.setValidator(QIntValidator(1, 10))
        self.mesh_div_field.setFixedWidth(30)
        layout.addWidget(self.mesh_div_field, 0, 1)

        self.mesh_div_slider = QSlider(Qt.Horizontal)
        self.mesh_div_slider.setRange(1, 10)
        layout.addWidget(self.mesh_div_slider, 0, 2)

        label = QLabel('U Divisions:', alignment=Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(label, 1, 0)

        self.u_div_field = QLineEdit()
        self.u_div_field.setValidator(QIntValidator(1, 10))
        self.u_div_field.setFixedWidth(30)
        layout.addWidget(self.u_div_field, 1, 1)

        self.u_div_slider = QSlider(Qt.Horizontal)
        self.u_div_slider.setRange(1, 10)
        layout.addWidget(self.u_div_slider, 1, 2)

        label = QLabel('V Divisions:', alignment=Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(label, 2, 0)

        self.v_div_field = QLineEdit()
        self.v_div_field.setValidator(QIntValidator(1, 10))
        self.v_div_field.setFixedWidth(30)
        layout.addWidget(self.v_div_field, 2, 1)

        self.v_div_slider = QSlider(Qt.Horizontal)
        self.v_div_slider.setRange(1, 10)
        layout.addWidget(self.v_div_slider, 2, 2)

        layout.setColumnStretch(2, 1)

        self.main_layout.addLayout(layout)

        separator = extra_widgets.HorizontalSeparator()
        self.main_layout.addWidget(separator)

        template_button = QPushButton('Create Template Mesh')
        self.main_layout.addWidget(template_button)

        convert_button = QPushButton('Convert Skin Weights to Mesh')
        self.main_layout.addWidget(convert_button)

        self.main_layout.addStretch()

        self.setLayout(self.main_layout)

        # Option settings
        self.mesh_div_field.setText(str(self.tool_options.read('mesh_divisions', '1')))
        self.mesh_div_slider.setValue(int(self.mesh_div_field.text()))
        self.u_div_field.setText(str(self.tool_options.read('u_divisions', '2')))
        self.u_div_slider.setValue(int(self.u_div_field.text()))
        self.v_div_field.setText(str(self.tool_options.read('v_divisions', '2')))

        # Signal & Slot
        self.mesh_div_field.textChanged.connect(partial(self.__update_preview_values, self.mesh_div_field))
        self.mesh_div_slider.valueChanged.connect(partial(self.__update_preview_values, self.mesh_div_slider))
        self.u_div_field.textChanged.connect(partial(self.__update_preview_values, self.u_div_field))
        self.u_div_slider.valueChanged.connect(partial(self.__update_preview_values, self.u_div_slider))
        self.v_div_field.textChanged.connect(partial(self.__update_preview_values, self.v_div_field))
        self.v_div_slider.valueChanged.connect(partial(self.__update_preview_values, self.v_div_slider))

        template_button.clicked.connect(self.create_template_mesh)
        convert_button.clicked.connect(self.convert_skin_weights_to_mesh)

    @maya_ui.undo_chunk('Update Preview Values')
    @maya_ui.error_handler
    def __update_preview_values(self, sender, *args, **kwargs):
        """Update the preview values.
        """
        # Check slide and field values
        if sender == self.mesh_div_field:
            value = self.mesh_div_field.text()
            self.mesh_div_slider.setValue(int(value))
        elif sender == self.mesh_div_slider:
            value = self.mesh_div_slider.value()
            self.mesh_div_field.setText(str(value))
        elif sender == self.u_div_field:
            value = self.u_div_field.text()
            self.u_div_slider.setValue(int(value))
        elif sender == self.u_div_slider:
            value = self.u_div_slider.value()
            self.u_div_field.setText(str(value))
        elif sender == self.v_div_field:
            value = self.v_div_field.text()
            self.v_div_slider.setValue(int(value))
        elif sender == self.v_div_slider:
            value = self.v_div_slider.value()
            self.v_div_field.setText(str(value))

        # Change preview values
        if self.preview_mesh is None and self.preview_mesh_node is None:
            logger.debug('No preview mesh found.')
            return

        if not cmds.objExists(self.preview_mesh) or not cmds.objExists(self.preview_mesh_node):
            logger.debug('Preview mesh not found.')
            return

        if cmds.nodeType(self.preview_mesh_node) == 'polySmoothFace':
            value = self.mesh_div_slider.value()
            cmds.setAttr(f'{self.preview_mesh_node}.divisions', value)

            logger.debug(f'Update preview node values: {self.preview_mesh_node} >> {value}')
        elif cmds.nodeType(self.preview_mesh_node) == 'nurbsTessellate':
            u_value = self.u_div_slider.value()
            cmds.setAttr(f'{self.preview_mesh_node}.uNumber', u_value)

            v_value = self.v_div_slider.value()
            cmds.setAttr(f'{self.preview_mesh_node}.vNumber', v_value)

            logger.debug(f'Update preview node values: {self.preview_mesh_node} >> {u_value}, {v_value}')

    @maya_ui.undo_chunk('Create Template Mesh')
    @maya_ui.error_handler
    def create_template_mesh(self):
        """Create a template mesh.
        """
        shapes = cmds.ls(sl=True, dag=True, type='geometryShape', ni=True)
        if not shapes:
            cmds.error('Select any geometry.')
        else:
            shape = shapes[0]

        skinCluster = lib_skinCluster.get_skinCluster(shape)
        if not skinCluster:
            cmds.error('No skinCluster found.')

        mesh_divisions = int(self.mesh_div_field.text())
        u_divisions = int(self.u_div_field.text())
        v_divisions = int(self.v_div_field.text())

        skinCluster_to_mesh_ins = convert_weight.SkinClusterToMesh(skinCluster,
                                                                   divisions=mesh_divisions,
                                                                   u_divisions=u_divisions,
                                                                   v_divisions=v_divisions)

        self.preview_mesh, self.preview_mesh_node = skinCluster_to_mesh_ins.preview()

        cmds.select(self.preview_mesh)

        logger.debug(f'Created template mesh: {self.preview_mesh}')

    @maya_ui.undo_chunk('Convert Skin Weights to Mesh')
    @maya_ui.error_handler
    def convert_skin_weights_to_mesh(self):
        """Convert the skin weights to mesh.
        """
        shapes = cmds.ls(sl=True, dag=True, type='geometryShape', ni=True)
        if not shapes:
            cmds.error('Select any geometry.')

        mesh_divisions = int(self.mesh_div_field.text())
        u_divisions = int(self.u_div_field.text())
        v_divisions = int(self.v_div_field.text())

        converted_meshes = []
        for shape in shapes:
            skinCluster = lib_skinCluster.get_skinCluster(shape)
            if not skinCluster:
                cmds.warning(f'No skinCluster found: {shape}')
                continue

            skinCluster_to_mesh_ins = convert_weight.SkinClusterToMesh(skinCluster,
                                                                       divisions=mesh_divisions,
                                                                       u_divisions=u_divisions,
                                                                       v_divisions=v_divisions)

            converted_mesh = skinCluster_to_mesh_ins.convert()
            converted_meshes.append(converted_mesh)

            logger.debug(f'Converted skin weights to mesh: {converted_mesh}')

        if converted_meshes:
            cmds.select(converted_meshes, r=True)

    def closeEvent(self, event):
        """Close event.
        """
        # Save the option settings
        self.tool_options.write('mesh_divisions', self.mesh_div_field.text())
        self.tool_options.write('u_divisions', self.u_div_field.text())
        self.tool_options.write('v_divisions', self.v_div_field.text())

        super().closeEvent(event)


def show_ui():
    """Show the main window.
    """
    window_name = f'{__name__}MainWindow'
    maya_qt.delete_widget(window_name)

    window = QMainWindow(parent=maya_qt.get_maya_pointer())
    window.setObjectName(window_name)
    window.setWindowTitle('Skin Weights to Mesh Converter')
    window.setAttribute(Qt.WA_DeleteOnClose)

    widgets = SkinWeightsMeshConverterWidgets()
    window.setCentralWidget(widgets)

    window.show()
    window.resize(300, 0)
