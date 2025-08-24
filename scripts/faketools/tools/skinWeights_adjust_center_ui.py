"""
Adjust the center weights of the selected vertices tool.
"""

from functools import partial
from logging import getLogger

import maya.cmds as cmds

try:
    from PySide2.QtCore import Qt
    from PySide2.QtWidgets import (
        QCheckBox,
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
        QCheckBox,
        QGridLayout,
        QLabel,
        QLineEdit,
        QMainWindow,
        QPushButton,
        QVBoxLayout,
        QWidget,
    )

from .. import user_directory
from ..command import convert_weight
from ..lib_ui import base_window, maya_qt, maya_ui
from ..lib_ui.widgets import extra_widgets

logger = getLogger(__name__)

global_settings = user_directory.ToolSettings(__name__).load()
ADJUST_CENTER_WEIGHT = global_settings.get("ADJUST_CENTER_WEIGHT", ["(.*)(L$)", r"\g<1>R"])


class AdjustCenterSkinWeightsWidgets(QWidget):
    def __init__(self, parent=None, window_mode: bool = False):
        """Constructor."""
        super().__init__(parent=parent)

        self.main_layout = QVBoxLayout()
        spacing = base_window.get_spacing(self)
        self.main_layout.setSpacing(spacing * 0.75)

        if not window_mode:
            margins = base_window.get_margins(self)
            self.main_layout.setContentsMargins(*[margin * 0.5 for margin in margins])

        self.auto_search_checkbox = QCheckBox("Auto Search")
        self.main_layout.addWidget(self.auto_search_checkbox)

        layout = QGridLayout()

        self.src_label = QLabel("Source Influences:", alignment=Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(self.src_label, 0, 0)

        self.src_infs_field = QLineEdit()
        layout.addWidget(self.src_infs_field, 0, 1)

        self.src_infs_button = QPushButton("SET")
        layout.addWidget(self.src_infs_button, 0, 2)

        self.target_label = QLabel("Target Influences:", alignment=Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(self.target_label, 1, 0)

        self.target_infs_field = QLineEdit()
        layout.addWidget(self.target_infs_field, 1, 1)

        self.target_infs_button = QPushButton("SET")
        layout.addWidget(self.target_infs_button, 1, 2)

        separator = extra_widgets.HorizontalSeparator()
        layout.addWidget(separator, 2, 0, 1, 3)

        label = QLabel("Static Influence:", alignment=Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(label, 3, 0)

        self.static_inf_field = QLineEdit()
        layout.addWidget(self.static_inf_field, 3, 1)

        static_inf_button = QPushButton("SET")
        layout.addWidget(static_inf_button, 3, 2)

        layout.setColumnStretch(1, 1)

        self.main_layout.addLayout(layout)

        button = QPushButton("Adjust Center Weights")
        self.main_layout.addWidget(button)

        self.main_layout.addStretch()

        self.setLayout(self.main_layout)

        # Signal & Slot
        self.auto_search_checkbox.stateChanged.connect(self.toggle_auto_search)
        self.src_infs_button.clicked.connect(partial(self.___set_selected_nodes, self.src_infs_field))
        self.target_infs_button.clicked.connect(partial(self.___set_selected_nodes, self.target_infs_field))
        static_inf_button.clicked.connect(partial(self.__set_selected_node, self.static_inf_field))

        button.clicked.connect(self.exchange_influences)

        # Initialize UI
        self.auto_search_checkbox.setCheckState(Qt.Checked)
        self.toggle_auto_search(Qt.Checked)

    def toggle_auto_search(self, state):
        """Toggle the auto search."""
        if state == Qt.Checked:
            self.src_label.setEnabled(False)
            self.src_infs_field.setEnabled(False)
            self.src_infs_button.setEnabled(False)
            self.target_label.setEnabled(False)
            self.target_infs_field.setEnabled(False)
            self.target_infs_button.setEnabled(False)
        else:
            self.src_label.setEnabled(True)
            self.src_infs_field.setEnabled(True)
            self.src_infs_button.setEnabled(True)
            self.target_label.setEnabled(True)
            self.target_infs_field.setEnabled(True)
            self.target_infs_button.setEnabled(True)

    @maya_ui.error_handler
    def ___set_selected_nodes(self, field):
        """Set the selected nodes to the field."""
        nodes = cmds.ls(sl=True, type="joint")
        if not nodes:
            if not cmds.ls(sl=True):
                field.setText("")
            else:
                cmds.error("Select joints.")

        field.setText(" ".join(nodes))

    @maya_ui.error_handler
    def __set_selected_node(self, field):
        """Set the selected node to the field."""
        nodes = cmds.ls(sl=True, type="joint")
        if not nodes:
            if not cmds.ls(sl=True):
                field.setText("")
            else:
                cmds.error("Select a joint.")

        field.setText(nodes[0])

    @maya_ui.undo_chunk("Adjust Center Weights")
    @maya_ui.error_handler
    def exchange_influences(self):
        """Exchange the influences."""
        components = cmds.filterExpand(sm=[28, 31, 46], ex=True)
        if not components:
            cmds.error("No components selected.")

        static_inf = self.static_inf_field.text()
        if not static_inf:
            static_inf = None

        if self.auto_search_checkbox.isChecked():
            convert_weight.combine_pair_skin_weights(
                components, method="auto", static_inf=static_inf, regex_name=ADJUST_CENTER_WEIGHT[0], replace_name=ADJUST_CENTER_WEIGHT[1]
            )
        else:
            src_infs = self.src_infs_field.text().split()
            target_infs = self.target_infs_field.text().split()

            if not src_infs:
                cmds.error("Source influences are not set.")
            if not target_infs:
                cmds.error("Target influences are not set.")

            if len(src_infs) != len(target_infs):
                cmds.error("Influence count mismatch.")

            pair_infs = list(zip(src_infs, target_infs, strict=False))

            convert_weight.combine_pair_skin_weights(components, method="manual", pair_infs=pair_infs, static_inf=static_inf)


def show_ui():
    """Show the main window."""
    window_name = f"{__name__}MainWindow"
    maya_qt.delete_widget(window_name)

    window = QMainWindow(parent=maya_qt.get_maya_pointer())
    window.setObjectName(window_name)
    window.setWindowTitle("Skin Weights Adjust Center")
    window.setAttribute(Qt.WA_DeleteOnClose)

    widgets = AdjustCenterSkinWeightsWidgets(window_mode=True)
    window.setCentralWidget(widgets)

    window.show()
    window.resize(300, 0)
