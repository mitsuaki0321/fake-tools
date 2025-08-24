"""
Combine the skin weights of the selected components tool.
"""

from functools import partial
from logging import getLogger

import maya.cmds as cmds

try:
    from PySide2.QtCore import Qt
    from PySide2.QtWidgets import (
        QGridLayout,
        QLabel,
        QLineEdit,
        QMainWindow,
        QPushButton,
        QVBoxLayout,
        QWidget,
    )
except ImportError:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import (
        QGridLayout,
        QLabel,
        QLineEdit,
        QMainWindow,
        QPushButton,
        QVBoxLayout,
        QWidget,
    )

from ..command import convert_weight
from ..lib_ui import base_window, maya_qt, maya_ui

logger = getLogger(__name__)


class CombineSkinWeightsWidgets(QWidget):
    """Combine Skin Weights Widgets."""

    def __init__(self, parent=None, window_mode: bool = False):
        """Constructor."""
        super().__init__(parent=parent)

        self.main_layout = QVBoxLayout()
        spacing = base_window.get_spacing(self)
        self.main_layout.setSpacing(spacing * 0.75)

        if not window_mode:
            margins = base_window.get_margins(self)
            self.main_layout.setContentsMargins(*[margin * 0.5 for margin in margins])

        layout = QGridLayout()

        label = QLabel("Source Influences:", alignment=Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(label, 0, 0)

        self.src_infs_field = QLineEdit()
        layout.addWidget(self.src_infs_field, 0, 1)

        src_infs_button = QPushButton("SET")
        layout.addWidget(src_infs_button, 0, 2)

        label = QLabel("Target Influence:", alignment=Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(label, 1, 0)

        self.target_inf_field = QLineEdit()
        layout.addWidget(self.target_inf_field, 1, 1)

        target_infs_button = QPushButton("SET")
        layout.addWidget(target_infs_button, 1, 2)

        layout.setColumnStretch(1, 1)

        self.main_layout.addLayout(layout)

        button = QPushButton("Combine Skin Weights")
        self.main_layout.addWidget(button)

        self.main_layout.addStretch()

        self.setLayout(self.main_layout)

        # Signal & Slot
        src_infs_button.clicked.connect(partial(self._set_selected_nodes, self.src_infs_field))
        target_infs_button.clicked.connect(partial(self._set_selected_node, self.target_inf_field))

        button.clicked.connect(self.combine_skin_weights)

    @maya_ui.error_handler
    def _set_selected_nodes(self, field):
        """Set the selected nodes to the field."""
        nodes = cmds.ls(sl=True, type="joint")
        if not nodes:
            if not cmds.ls(sl=True):
                field.setText("")
            else:
                cmds.error("Select joints.")

        field.setText(" ".join(nodes))

    @maya_ui.error_handler
    def _set_selected_node(self, field):
        """Set the selected node to the field."""
        nodes = cmds.ls(sl=True, type="joint")
        if not nodes:
            if not cmds.ls(sl=True):
                field.setText("")
            else:
                cmds.error("Select a joint.")

        field.setText(nodes[0])

    @maya_ui.undo_chunk("Combine Skin Weights")
    @maya_ui.error_handler
    def combine_skin_weights(self):
        """Combine the skin weights."""
        src_infs = self.src_infs_field.text().split()
        target_inf = self.target_inf_field.text()

        if not src_infs:
            cmds.error("No source influences.")
        if not target_inf:
            cmds.error("No target influence.")

        components = cmds.filterExpand(sm=[28, 31, 46], ex=True)
        if not components:
            cmds.error("No components selected.")

        convert_weight.combine_skin_weights(src_infs, target_inf, components)

        logger.info("Combined skin weights")


def show_ui():
    """Show the main window."""
    window_name = f"{__name__}MainWindow"
    maya_qt.delete_widget(window_name)

    window = QMainWindow(parent=maya_qt.get_maya_pointer())
    window.setObjectName(window_name)
    window.setWindowTitle("Skin Weights Combine")
    window.setAttribute(Qt.WA_DeleteOnClose)

    widgets = CombineSkinWeightsWidgets(window_mode=True)
    window.setCentralWidget(widgets)

    window.show()
    window.resize(300, 0)
