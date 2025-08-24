"""
Retarget mesh tool.
"""

from logging import getLogger

import maya.cmds as cmds

try:
    from PySide2.QtCore import QStringListModel
    from PySide2.QtWidgets import (
        QCheckBox,
        QLineEdit,
        QPushButton,
        QVBoxLayout,
        QWidget,
    )
except ImportError:
    from PySide6.QtCore import QStringListModel
    from PySide6.QtWidgets import QCheckBox, QLineEdit, QPushButton, QVBoxLayout, QWidget

from ..command import retarget_mesh
from ..lib_ui import base_window, maya_qt, maya_ui, optionvar
from ..lib_ui.widgets import extra_widgets, nodeAttr_widgets

logger = getLogger(__name__)


class MainWindow(base_window.BaseMainWindow):
    """Retarget Mesh Main Window."""

    def __init__(self, parent=None, object_name="MainWindow", window_title="Main Window"):
        """Constructor."""
        super().__init__(parent=parent, object_name=object_name, window_title=window_title)

        self.tool_options = optionvar.ToolOptionSettings(__name__)

        self.src_node_widgets = SetNodeWidgets("Set Source Mesh")
        self.central_layout.addWidget(self.src_node_widgets)

        self.dst_node_widgets = SetNodesWidgets("Set Destination Mesh")
        self.central_layout.addWidget(self.dst_node_widgets)

        self.trg_node_widgets = SetNodesWidgets("Set Target Mesh")
        self.central_layout.addWidget(self.trg_node_widgets)

        self.is_create_checkbox = QCheckBox("Create New Mesh")
        self.central_layout.addWidget(self.is_create_checkbox)

        separator = extra_widgets.HorizontalSeparator()
        self.central_layout.addWidget(separator)

        button = QPushButton("Retarget Mesh")
        self.central_layout.addWidget(button)

        # Option Settings
        self.is_create_checkbox.setChecked(self.tool_options.read("is_create", True))

        # Signal & Slot
        button.clicked.connect(self._retarget_mesh)

        # Initialize the UI.
        size_hint = self.sizeHint()
        self.resize(size_hint.width() * 0.8, size_hint.height() * 0.4)

    @maya_ui.undo_chunk("Retarget Mesh")
    @maya_ui.error_handler
    def _retarget_mesh(self):
        """Retarget the mesh."""
        src_node = self.src_node_widgets.get_node()
        dst_nodes = self.dst_node_widgets.get_nodes()
        trg_nodes = self.trg_node_widgets.get_nodes()
        is_create = self.is_create_checkbox.isChecked()

        retarget_mesh.retarget_mesh(src_node, dst_nodes, trg_nodes, is_create=is_create)

    def closeEvent(self, event):
        """Override the close event."""
        # Save option settings
        self.tool_options.write("is_create", self.is_create_checkbox.isChecked())

        super().closeEvent(event)


class SetNodeWidgets(QWidget):
    """Set Node Widgets."""

    def __init__(self, label: str, parent=None):
        """Constructor."""
        super().__init__(parent)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        button = QPushButton(label)
        layout.addWidget(button)

        self.node_field = QLineEdit()
        self.node_field.setReadOnly(True)
        layout.addWidget(self.node_field)

        self.setLayout(layout)

        button.clicked.connect(self._set_node)

    def _set_node(self):
        """Set the node."""
        sel_nodes = cmds.ls(sl=True, dag=True, type="mesh")
        if not sel_nodes:
            cmds.warning("Please select a transform node.")
            return

        self.node_field.setText(sel_nodes[0])

    def get_node(self):
        """Get the node."""
        return self.node_field.text()


class SetNodesWidgets(QWidget):
    """Set Nodes Widgets."""

    def __init__(self, label: str, parent=None):
        """Constructor."""
        super().__init__(parent)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        button = QPushButton(label)
        layout.addWidget(button)

        self.node_list_view = nodeAttr_widgets.NodeListView()
        self.model = QStringListModel()
        self.node_list_view.setModel(self.model)
        layout.addWidget(self.node_list_view)

        self.setLayout(layout)

        button.clicked.connect(self._set_nodes)

    def _set_nodes(self):
        """Set the nodes."""
        sel_nodes = cmds.ls(sl=True, dag=True, type="mesh")
        if not sel_nodes:
            cmds.warning("Please select transform nodes.")
            return

        self.model.setStringList(sel_nodes)

    def get_nodes(self):
        """Get the nodes."""
        return self.model.stringList()


def show_ui():
    """Show the main window."""
    window_name = f"{__name__}MainWindow"
    maya_qt.delete_widget(window_name)

    # Create the main window.
    main_window = MainWindow(parent=maya_qt.get_maya_pointer(), object_name=window_name, window_title="Retarget Mesh")
    main_window.show()
