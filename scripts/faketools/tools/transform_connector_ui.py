"""
Connection transform tool.
"""

from logging import getLogger

import maya.cmds as cmds

try:
    from PySide2.QtCore import Qt
    from PySide2.QtWidgets import (
        QCheckBox,
        QGridLayout,
        QHBoxLayout,
        QLabel,
        QPushButton,
        QSizePolicy,
    )
except ImportError:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import (
        QCheckBox,
        QGridLayout,
        QHBoxLayout,
        QLabel,
        QPushButton,
        QSizePolicy,
    )

from ..lib_ui import base_window, maya_qt, maya_ui, optionvar
from ..lib_ui.widgets import extra_widgets

logger = getLogger(__name__)


class MainWindow(base_window.BaseMainWindow):
    def __init__(self, parent=None, object_name="MainWindow", window_title="Main Window"):
        """Constructor."""
        super().__init__(parent=parent, object_name=object_name, window_title=window_title)

        self.tool_options = optionvar.ToolOptionSettings(__name__)

        # Translate, Rotate, Scale, JointOrient
        self.checkboxes = {}
        layout = QGridLayout()
        for i, (label, attribute) in enumerate(
            zip(
                ["Translate", "Rotate", "Scale", "JointOrient", "Visibility"],
                ["translate", "rotate", "scale", "jointOrient", "visibility"],
                strict=False,
            )
        ):
            # Label
            check_box_label = QLabel(f"{label}:")
            check_box_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            check_box_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            layout.addWidget(check_box_label, i, 0)

            if label == "Visibility":
                # Visibility
                checkbox = QCheckBox()
                layout.addWidget(checkbox, i, 1)
                self.checkboxes.setdefault(attribute, []).append(checkbox)
            else:
                # Checkboxes
                for j, axis in enumerate(["X", "Y", "Z"]):
                    checkbox = QCheckBox(axis)
                    layout.addWidget(checkbox, i, j + 1)
                    self.checkboxes.setdefault(attribute, []).append(checkbox)

                # On & Off Button
                on_button = QPushButton("On")
                on_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
                layout.addWidget(on_button, i, 4)

                off_button = QPushButton("Off")
                off_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
                layout.addWidget(off_button, i, 5)

                # Signal & Slot
                on_button.clicked[bool].connect(lambda _, attr=attribute: self._all_on_checked(self.checkboxes[attr]))
                off_button.clicked[bool].connect(lambda _, attr=attribute: self._all_off_checked(self.checkboxes[attr]))

        self.central_layout.addLayout(layout)

        self.central_layout.addWidget(extra_widgets.HorizontalSeparator())

        layout = QHBoxLayout()

        copy_value_button = QPushButton("Copy Value")
        self.central_layout.addWidget(copy_value_button)

        connect_value_button = QPushButton("Connect Value")
        self.central_layout.addWidget(connect_value_button)

        zero_out_button = QPushButton("Zero Out")
        self.central_layout.addWidget(zero_out_button)

        # Option settings
        for attribute, checkboxes in self.checkboxes.items():
            if attribute == "visibility":
                checkboxes[0].setChecked(self.tool_options.read(attribute, False))
            else:
                attribute_values = self.tool_options.read(attribute, [False, False, False])
                for checkbox, value in zip(checkboxes, attribute_values, strict=False):
                    checkbox.setChecked(value)

        # Signal & Slot
        copy_value_button.clicked.connect(self._copy_value)
        connect_value_button.clicked.connect(self._connect_attr)
        zero_out_button.clicked.connect(self._zero_out)

    @staticmethod
    def _all_on_checked(checkboxes):
        """All on checked."""
        for checkbox in checkboxes:
            checkbox.setChecked(True)

    @staticmethod
    def _all_off_checked(checkboxes):
        """All off checked."""
        for checkbox in checkboxes:
            checkbox.setChecked(False)

    @maya_ui.undo_chunk("Connect Transform: Copy Value")
    @maya_ui.error_handler
    def _copy_value(self):
        """Copy Value."""
        sel_nodes = cmds.ls(sl=True, type="transform")
        if not sel_nodes:
            cmds.error("Select transform nodes.")
            return

        if len(sel_nodes) == 1:
            cmds.error("Select multiple transform nodes.")
            return

        src_node = sel_nodes[0]
        dest_nodes = sel_nodes[1:]

        enable_attributes = self._get_enable_attributes()
        if not enable_attributes:
            cmds.error("Select attributes.")
            return

        for dest_node in dest_nodes:
            for attribute in enable_attributes:
                src_attr = f"{src_node}.{attribute}"
                dest_attr = f"{dest_node}.{attribute}"

                if not cmds.attributeQuery(attribute, node=src_node, exists=True):
                    cmds.warning(f"Failed to copy value. Attribute not exists: {src_attr}")
                    continue

                if not cmds.attributeQuery(attribute, node=dest_node, exists=True):
                    cmds.warning(f"Failed to copy value. Attribute not exists: {dest_attr}")
                    continue

                if cmds.connectionInfo(src_attr, isDestination=True):
                    cmds.error(f"Failed to copy value. Attribute is connected: {src_attr}")
                    continue

                if cmds.getAttr(dest_attr, lock=True):
                    cmds.setAttr(dest_attr, lock=False)

                cmds.setAttr(dest_attr, cmds.getAttr(src_attr))

                if cmds.getAttr(dest_attr, lock=True):
                    cmds.setAttr(dest_attr, lock=True)

                logger.debug(f"Copy value: {src_attr} -> {dest_attr}")

    @maya_ui.undo_chunk("Connect Transform: Connect Value")
    @maya_ui.error_handler
    def _connect_attr(self):
        """Connect Value."""
        sel_nodes = cmds.ls(sl=True, type="transform")
        if not sel_nodes:
            cmds.error("Select transform nodes.")
            return

        if len(sel_nodes) == 1:
            cmds.error("Select multiple transform nodes.")
            return

        src_node = sel_nodes[0]
        dest_nodes = sel_nodes[1:]

        enable_attributes = self._get_enable_attributes()
        if not enable_attributes:
            cmds.error("Select attributes.")
            return

        for dest_node in dest_nodes:
            for attribute in enable_attributes:
                src_attr = f"{src_node}.{attribute}"
                dest_attr = f"{dest_node}.{attribute}"

                if not cmds.attributeQuery(attribute, node=src_node, exists=True):
                    cmds.warning(f"Failed to connect value. Attribute not exists: {src_attr}")
                    continue

                if not cmds.attributeQuery(attribute, node=dest_node, exists=True):
                    cmds.warning(f"Failed to connect value. Attribute not exists: {dest_attr}")
                    continue

                if cmds.getAttr(dest_attr, lock=True):
                    cmds.setAttr(dest_attr, lock=False)

                cmds.connectAttr(src_attr, dest_attr, force=True)

                if cmds.getAttr(dest_attr, lock=True):
                    cmds.setAttr(dest_attr, lock=True)

                logger.debug(f"Connect value: {src_attr} -> {dest_attr}")

    @maya_ui.undo_chunk("Connect Transform: Zero Out")
    @maya_ui.error_handler
    def _zero_out(self):
        """Zero Out."""
        sel_nodes = cmds.ls(sl=True, type="transform")
        if not sel_nodes:
            cmds.error("Select transform nodes.")
            return

        enable_attributes = self._get_enable_attributes()
        if not enable_attributes:
            cmds.error("Select attributes.")
            return

        for node in sel_nodes:
            for attribute in enable_attributes:
                attr = f"{node}.{attribute}"

                if not cmds.attributeQuery(attribute, node=node, exists=True):
                    cmds.warning(f"Failed to zero out. Attribute not exists: {attr}")
                    continue

                if cmds.connectionInfo(attr, isDestination=True):
                    cmds.error(f"Failed to zero out. Attribute is connected: {attr}")
                    continue

                if cmds.getAttr(attr, lock=True):
                    cmds.setAttr(attr, lock=False)

                if attribute in ["scaleX", "scaleY", "scaleZ", "visibility"]:
                    cmds.setAttr(attr, 1)
                else:
                    cmds.setAttr(attr, 0)

                if cmds.getAttr(attr, lock=True):
                    cmds.setAttr(attr, lock=True)

                logger.debug(f"Zero out: {attr}")

    def _get_enable_attributes(self):
        """Get enable attributes from checkboxes."""
        enable_attributes = []
        for attribute, checkboxes in self.checkboxes.items():
            if attribute == "visibility":
                if checkboxes[0].isChecked():
                    enable_attributes.append(attribute)
            else:
                for a, checkbox in zip(["X", "Y", "Z"], checkboxes, strict=False):
                    if checkbox.isChecked():
                        enable_attributes.append(f"{attribute}{a}")

        return enable_attributes

    def closeEvent(self, event):
        """Close event."""
        # Save option settings
        for attribute, checkboxes in self.checkboxes.items():
            if attribute == "visibility":
                self.tool_options.write(attribute, checkboxes[0].isChecked())
            else:
                self.tool_options.write(attribute, [checkbox.isChecked() for checkbox in checkboxes])

        super().closeEvent(event)


def show_ui():
    """Show the main window."""
    window_name = f"{__name__}MainWindow"
    maya_qt.delete_widget(window_name)

    # Create the main window.
    main_window = MainWindow(parent=maya_qt.get_maya_pointer(), object_name=window_name, window_title="Transform Connector")
    main_window.show()
