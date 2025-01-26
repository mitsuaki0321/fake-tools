"""
Set driven key tools.
"""

import os
import tempfile
from logging import getLogger

import maya.cmds as cmds
from PySide2.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QWidget,
)

from .. import user_directory
from ..command import manage_drivenkey, transfer_drivenkey
from ..lib import lib_keyframe
from ..lib_ui import base_window, maya_qt, maya_ui, optionvar
from ..lib_ui.widgets import extra_widgets

logger = getLogger(__name__)

TEMP_DIR = os.path.normpath(os.path.join(tempfile.gettempdir(), 'drivenKeys'))

global_settings = user_directory.ToolSettings(__name__).load()
REGEX = global_settings.get('LEFT_TO_RIGHT', ['(.*)(L)', r'\g<1>R'])


class MainWindow(base_window.BaseMainWindow):

    def __init__(self,
                 parent=None,
                 object_name='MainWindow',
                 window_title='Main Window'):
        """Constructor.
        """
        super().__init__(parent=parent, object_name=object_name, window_title=window_title)

        self.tool_options = optionvar.ToolOptionSettings(__name__)
        self.root_path = user_directory.ToolDirectory(__name__).get_directory()

        self.menu_bar = self.menuBar()
        self.__add_menu()

        one_to_all_button = QPushButton('One to All')
        self.central_layout.addWidget(one_to_all_button)

        one_to_replace_button = QPushButton('One to Replace')
        self.central_layout.addWidget(one_to_replace_button)

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        self.regex_line_edit = QLineEdit()
        layout.addWidget(self.regex_line_edit)

        self.replace_to_line_edit = QLineEdit()
        layout.addWidget(self.replace_to_line_edit)

        self.central_layout.addLayout(layout)

        self.replace_driver_check_box = QCheckBox('Replace Driver')
        self.central_layout.addWidget(self.replace_driver_check_box)

        self.force_delete_check_box = QCheckBox('Force Delete Driven Key')
        self.central_layout.addWidget(self.force_delete_check_box)

        self.mirror_check_box = QCheckBox('Mirror')
        self.central_layout.addWidget(self.mirror_check_box)

        layout = QGridLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        self.time_label = QLabel('Time')
        self.time_label.setStyleSheet('font-weight: bold;')
        layout.addWidget(self.time_label, 0, 0)

        self.time_translate_check_box = MirrorCheckBox('T', 'translate')
        layout.addWidget(self.time_translate_check_box, 1, 0)

        self.time_rotate_check_box = MirrorCheckBox('R', 'rotate')
        layout.addWidget(self.time_rotate_check_box, 2, 0)

        self.time_scale_check_box = MirrorCheckBox('S', 'scale')
        layout.addWidget(self.time_scale_check_box, 3, 0)

        self.value_label = QLabel('Value')
        self.value_label.setStyleSheet('font-weight: bold;')
        layout.addWidget(self.value_label, 0, 1)

        self.value_translate_check_box = MirrorCheckBox('T', 'translate')
        layout.addWidget(self.value_translate_check_box, 1, 1)

        self.value_rotate_check_box = MirrorCheckBox('R', 'rotate')
        layout.addWidget(self.value_rotate_check_box, 2, 1)

        self.value_scale_check_box = MirrorCheckBox('S', 'scale')
        layout.addWidget(self.value_scale_check_box, 3, 1)

        self.central_layout.addLayout(layout)

        separator = extra_widgets.HorizontalSeparator()
        self.central_layout.addWidget(separator)

        label = QLabel('Mirror Curve')
        label.setStyleSheet('font-weight: bold;')
        self.central_layout.addWidget(label)

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        mirror_curve_time_button = QPushButton('Time')
        layout.addWidget(mirror_curve_time_button)

        mirror_curve_value_button = QPushButton('Value')
        layout.addWidget(mirror_curve_value_button)

        self.central_layout.addLayout(layout)

        # Option Settings
        self.regex_line_edit.setText(self.tool_options.read('regex', REGEX[0]))
        self.replace_to_line_edit.setText(self.tool_options.read('replace_to', REGEX[1]))
        self.mirror_check_box.setChecked(self.tool_options.read('mirror', False))
        self.replace_driver_check_box.setChecked(self.tool_options.read('replace_driver', True))
        self.force_delete_check_box.setChecked(self.tool_options.read('force_delete', False))
        self.time_translate_check_box.set_values(self.tool_options.read('time_translate', []))
        self.time_rotate_check_box.set_values(self.tool_options.read('time_rotate', []))
        self.time_scale_check_box.set_values(self.tool_options.read('time_scale', []))
        self.value_translate_check_box.set_values(self.tool_options.read('value_translate', ['translateX', 'translateY', 'translateZ']))
        self.value_rotate_check_box.set_values(self.tool_options.read('value_rotate', []))
        self.value_scale_check_box.set_values(self.tool_options.read('value_scale', []))

        # Signal & Slot
        one_to_all_button.clicked.connect(self.transfer_one_to_all)
        one_to_replace_button.clicked.connect(self.transfer_one_to_replace)
        mirror_curve_time_button.clicked.connect(self.mirror_curve_time)
        mirror_curve_value_button.clicked.connect(self.mirror_curve_value)
        self.mirror_check_box.stateChanged.connect(self.__update_mirror_check_box)

        # Initial state
        self.__update_mirror_check_box()

    def __add_menu(self):
        """Add the menu.
        """
        menu = self.menu_bar.addMenu('Export/Import')

        export_temp_action = menu.addAction('Export')
        export_temp_action.triggered.connect(self.export_to_temp)

        import_temp_action = menu.addAction('Import')
        import_temp_action.triggered.connect(self.import_from_temp)

        menu.addSeparator()

        export_file_action = menu.addAction('Export File')
        export_file_action.triggered.connect(self.export_to_file)

        import_file_action = menu.addAction('Import File')
        import_file_action.triggered.connect(self.import_from_file)

        menu = self.menu_bar.addMenu('Options')

        option_action = menu.addAction('Select Driven Key Nodes')
        option_action.triggered.connect(self.select_driven_key_nodes)

        option_action = menu.addAction('Cleanup Driven Key')
        option_action.triggered.connect(self.cleanup_driven_keys)

    @maya_ui.error_handler
    def export_to_temp(self):
        """Export driven key to temp directory.
        """
        temp_dir = TEMP_DIR
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)

        temp_file = os.path.join(temp_dir, 'driven_key.json')
        transfer_drivenkey.DrivenKeyExportImport().export_driven_keys(temp_file)

    @maya_ui.undo_chunk('Import Driven Key')
    @maya_ui.error_handler
    def import_from_temp(self):
        """Import driven key from temp directory.
        """
        temp_file = os.path.join(TEMP_DIR, 'driven_key.json')
        if not os.path.exists(temp_file):
            cmds.warning('Driven key file does not exists')
            return

        transfer_drivenkey.DrivenKeyExportImport().import_driven_keys(temp_file)

    @maya_ui.error_handler
    def export_to_file(self):
        """Export driven key to file.
        """
        file_dialog = QFileDialog(self, directory=self.root_path)
        file_dialog.setAcceptMode(QFileDialog.AcceptSave)
        file_dialog.setNameFilter("JSON Files (*.json)")
        file_dialog.setDefaultSuffix("json")

        if file_dialog.exec_() == QFileDialog.Accepted:
            file_path = file_dialog.selectedFiles()[0]
            transfer_drivenkey.DrivenKeyExportImport().export_driven_keys(file_path)

    @maya_ui.undo_chunk('Import Driven Key')
    @maya_ui.error_handler
    def import_from_file(self):
        """Import driven key from file.
        """
        file_dialog = QFileDialog(self)
        file_dialog.setAcceptMode(QFileDialog.AcceptOpen)
        file_dialog.setNameFilter("JSON Files (*.json)")

        if file_dialog.exec_() == QFileDialog.Accepted:
            file_path = file_dialog.selectedFiles()[0]
            transfer_drivenkey.DrivenKeyExportImport().import_driven_keys(file_path)

    @maya_ui.undo_chunk('Transfer Driven Key')
    @maya_ui.error_handler
    def transfer_one_to_all(self):
        """Transfer driven key one to all.
        """
        transfer_drivenkey.DrivenKeyTransfer().one_to_all()

    @maya_ui.undo_chunk('Transfer Driven Key')
    @maya_ui.error_handler
    def transfer_one_to_replace(self):
        """Transfer driven key one to replace.
        """
        regex = self.regex_line_edit.text()
        replace_to = self.replace_to_line_edit.text()
        replace_driver = self.replace_driver_check_box.isChecked()
        force_delete = self.force_delete_check_box.isChecked()

        replaced_nodes = transfer_drivenkey.DrivenKeyTransfer().one_to_replace(regex, replace_to, replace_driver, force_delete)
        cmds.select(replaced_nodes, r=True)

        if not self.mirror_check_box.isChecked():
            return

        time_attrs = self.time_translate_check_box.get_values() + self.time_rotate_check_box.get_values() + self.time_scale_check_box.get_values()
        value_attrs = self.value_translate_check_box.get_values() + self.value_rotate_check_box.get_values() + self.value_scale_check_box.get_values()

        if not time_attrs and not value_attrs:
            return

        for node in replaced_nodes:
            manage_drivenkey.mirror_transform_anim_curve(node, time_attrs, value_attrs)

    @maya_ui.undo_chunk('Mirror Curve')
    @maya_ui.error_handler
    def mirror_curve_time(self):
        """Mirror the curve time.
        """
        anim_curves = cmds.keyframe(q=True, sl=True, n=True)
        if not anim_curves:
            cmds.error('No animation curve selected')

        for anim_curve in anim_curves:
            lib_keyframe.mirror_anim_curve(anim_curve, mirror_time=True, mirror_value=False)

    @maya_ui.undo_chunk('Mirror Curve')
    @maya_ui.error_handler
    def mirror_curve_value(self):
        """Mirror the curve value.
        """
        anim_curves = cmds.keyframe(q=True, sl=True, n=True)
        if not anim_curves:
            cmds.error('No animation curve selected')

        for anim_curve in anim_curves:
            lib_keyframe.mirror_anim_curve(anim_curve, mirror_time=False, mirror_value=True)

    @maya_ui.undo_chunk('Select Driven Key Nodes')
    @maya_ui.error_handler
    def select_driven_key_nodes(self):
        """Select driven key nodes.
        """
        sel_nodes = manage_drivenkey.get_driven_key_nodes()
        if not sel_nodes:
            cmds.waning('No driven key nodes found')
            return

        cmds.select(sel_nodes, r=True)

    @maya_ui.undo_chunk('Cleanup Driven Key')
    @maya_ui.error_handler
    def cleanup_driven_keys(self):
        """Cleanup driven keys.
        """
        sel_nodes = cmds.ls(sl=True)
        if not sel_nodes:
            cmds.error('No nodes selected')

        for node in sel_nodes:
            manage_drivenkey.cleanup_driven_keys(node)

    def __update_mirror_check_box(self):
        """Update the mirror check box.
        """
        state = self.mirror_check_box.isChecked()

        self.time_label.setEnabled(state)
        self.time_translate_check_box.set_enabled(state)
        self.time_rotate_check_box.set_enabled(state)
        self.time_scale_check_box.set_enabled(state)
        self.value_label.setEnabled(state)
        self.value_translate_check_box.set_enabled(state)
        self.value_rotate_check_box.set_enabled(state)
        self.value_scale_check_box.set_enabled(state)

    def closeEvent(self, event):
        """Close event.
        """
        # Save option settings
        self.tool_options.write('regex', self.regex_line_edit.text())
        self.tool_options.write('replace_to', self.replace_to_line_edit.text())
        self.tool_options.write('mirror', self.mirror_check_box.isChecked())
        self.tool_options.write('replace_driver', self.replace_driver_check_box.isChecked())
        self.tool_options.write('force_delete', self.force_delete_check_box.isChecked())
        self.tool_options.write('time_translate', self.time_translate_check_box.get_values())
        self.tool_options.write('time_rotate', self.time_rotate_check_box.get_values())
        self.tool_options.write('time_scale', self.time_scale_check_box.get_values())
        self.tool_options.write('value_translate', self.value_translate_check_box.get_values())
        self.tool_options.write('value_rotate', self.value_rotate_check_box.get_values())
        self.tool_options.write('value_scale', self.value_scale_check_box.get_values())

        super().closeEvent(event)


class MirrorCheckBox(QWidget):

    def __init__(self, label: str = 'T', attribute: str = 'translate', parent=None):
        """Initialize.

        Args:
            label: Label.
        """
        super().__init__(parent)

        self.__attribute = attribute

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        self.label = QLabel(f'{label}:')
        layout.addWidget(self.label)

        self.x_check_box = QCheckBox('')
        layout.addWidget(self.x_check_box)

        self.y_check_box = QCheckBox('')
        layout.addWidget(self.y_check_box)

        self.z_check_box = QCheckBox('')
        layout.addWidget(self.z_check_box)

        self.setLayout(layout)

    def get_values(self) -> list[str]:
        """Get the values.

        Returns:
            list[str]: The values.
        """
        values = []
        for check_box, axis in [(self.x_check_box, 'X'), (self.y_check_box, 'Y'), (self.z_check_box, 'Z')]:
            if check_box.isChecked():
                values.append(f'{self.__attribute}{axis}')

        return values

    def set_values(self, values: list[str]):
        """Set the values.

        Args:
            values (list[str]): The values.
        """
        for check_box, axis in [(self.x_check_box, 'X'), (self.y_check_box, 'Y'), (self.z_check_box, 'Z')]:
            attribute = f'{self.__attribute}{axis}'
            if attribute in values:
                check_box.setChecked(True)
            else:
                check_box.setChecked(False)

    def set_enabled(self, enabled: bool):
        """Set the enabled.

        Args:
            enabled (bool): The enabled.
        """
        self.label.setEnabled(enabled)
        for check_box in [self.x_check_box, self.y_check_box, self.z_check_box]:
            check_box.setEnabled(enabled)


def show_ui():
    """Show the main window.
    """
    window_name = f'{__name__}MainWindow'
    maya_qt.delete_widget(window_name)

    # Create the main window.
    main_window = MainWindow(parent=maya_qt.get_maya_pointer(),
                             object_name=window_name,
                             window_title='Driven Key Tools')
    main_window.show()
