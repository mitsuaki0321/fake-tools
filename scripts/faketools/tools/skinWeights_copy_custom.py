"""
Copy weights tool using custom plug-in.
"""

from logging import getLogger

import maya.cmds as cmds
from PySide2.QtCore import Qt
from PySide2.QtGui import QDoubleValidator
from PySide2.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from ..lib import lib_skinCluster
from ..lib_ui import base_window, maya_qt, maya_ui, optionvar
from ..lib_ui.widgets import extra_widgets

logger = getLogger(__name__)


class SkinWeightsCopyCustomWidgets(QWidget):

    def __init__(self, parent=None, window_mode: bool = False):
        """Constructor.
        """
        super().__init__(parent=parent)

        self.tool_options = optionvar.ToolOptionSettings(__name__)

        self.preview_mesh = None
        self.preview_mesh_node = None

        self.main_layout = QVBoxLayout()
        spacing = base_window.get_spacing(self)
        self.main_layout.setSpacing(spacing * 0.75)

        if not window_mode:
            margins = base_window.get_margins(self)
            self.main_layout.setContentsMargins(*[margin * 0.5 for margin in margins])

        layout = QHBoxLayout()

        label = QLabel('Blend:', alignment=Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(label)

        self.blend_field = QLineEdit()
        self.blend_field.setValidator(QDoubleValidator(0.0, 1.0, 2))
        self.blend_field.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.blend_field.setFixedWidth(self.blend_field.sizeHint().width() / 2.0)
        layout.addWidget(self.blend_field)

        self.blend_slider = QSlider(Qt.Horizontal)
        self.blend_slider.setRange(0, 100)
        layout.addWidget(self.blend_slider)

        self.main_layout.addLayout(layout)

        separator = extra_widgets.HorizontalSeparator()
        self.main_layout.addWidget(separator)

        self.only_unlock_inf_checkBox = QCheckBox('Use Only Unlocked Influences')
        self.main_layout.addWidget(self.only_unlock_inf_checkBox)

        self.reference_orig_checkBox = QCheckBox('Reference Original Shape')
        self.main_layout.addWidget(self.reference_orig_checkBox)

        self.add_missing_infs_checkBox = QCheckBox('Add Missing Influences')
        self.main_layout.addWidget(self.add_missing_infs_checkBox)

        separator = extra_widgets.HorizontalSeparator()
        self.main_layout.addWidget(separator)

        execute_button = QPushButton('Copy Skin Weights')
        self.main_layout.addWidget(execute_button)

        self.main_layout.addStretch()

        self.setLayout(self.main_layout)

        # Option settings
        self.blend_field.setText(str(self.tool_options.read('blend_value', '1.0')))
        self.blend_slider.setValue(float(self.blend_field.text()) * 100)
        self.only_unlock_inf_checkBox.setChecked(self.tool_options.read('only_unlock_inf', False))
        self.reference_orig_checkBox.setChecked(self.tool_options.read('reference_orig', False))
        self.add_missing_infs_checkBox.setChecked(self.tool_options.read('add_missing_infs', True))

        # Signal & Slot
        self.blend_field.textChanged.connect(self.__blend_value_change)
        self.blend_slider.valueChanged.connect(self.__blend_value_change)
        execute_button.clicked.connect(self.copy_skin_weights)

    def __blend_value_change(self, *args, **kwargs):
        """Change the blend value.
        """
        sender = self.sender()

        if sender == self.blend_field:
            value = float(sender.text())
            self.blend_slider.setValue(value * 100)
        elif sender == self.blend_slider:
            value = sender.value() / 100
            self.blend_field.setText(str(value))

    @maya_ui.undo_chunk('Copy Skin Weights Custom')
    @maya_ui.error_handler
    def copy_skin_weights(self):
        """Copy the skin weights.
        """
        shapes = cmds.ls(sl=True, dag=True, type='deformableShape', ni=True, objectsOnly=True)
        if not shapes or len(shapes) < 2:
            cmds.error('Select 2 or more deformable shapes')

        src_shape = shapes[0]
        dst_shapes = shapes[1:]

        src_skinCluster = lib_skinCluster.get_skinCluster(src_shape)
        if not src_skinCluster:
            cmds.error(f'No skinCluster found: {src_shape}')

        blend_value = float(self.blend_field.text())

        only_unlock_inf = self.only_unlock_inf_checkBox.isChecked()
        reference_orig = self.reference_orig_checkBox.isChecked()
        add_missing_infs = self.add_missing_infs_checkBox.isChecked()

        for dst_shape in dst_shapes:
            dst_skinCluster = lib_skinCluster.get_skinCluster(dst_shape)
            if not dst_skinCluster:
                cmds.warning(f'No skinCluster found: {dst_shape}')
                continue

            lib_skinCluster.copy_skin_weights_custom(src_skinCluster,
                                                     dst_skinCluster,
                                                     only_unlock_influences=only_unlock_inf,
                                                     blend_weights=blend_value,
                                                     reference_orig=reference_orig,
                                                     add_missing_influences=add_missing_infs)

    def closeEvent(self, event):
        """Close event.
        """
        # Save the option settings
        self.tool_options.write('blend_value', self.blend_field.text())
        self.tool_options.write('only_unlock_inf', self.only_unlock_inf_checkBox.isChecked())
        self.tool_options.write('reference_orig', self.reference_orig_checkBox.isChecked())
        self.tool_options.write('add_missing_infs', self.add_missing_infs_checkBox.isChecked())

        super().closeEvent(event)


def show_ui():
    """Show the main window.
    """
    window_name = f'{__name__}MainWindow'
    maya_qt.delete_widget(window_name)

    window = QMainWindow(parent=maya_qt.get_maya_pointer())
    window.setObjectName(window_name)
    window.setWindowTitle('Skin Weights Copy Custom')
    window.setAttribute(Qt.WA_DeleteOnClose)

    widgets = SkinWeightsCopyCustomWidgets(window_mode=True)
    window.setCentralWidget(widgets)

    window.show()
    window.resize(300, 0)
