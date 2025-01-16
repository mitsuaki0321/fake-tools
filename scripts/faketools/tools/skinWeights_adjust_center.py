"""
Adjust the center weights of the selected vertices tool.
"""

from functools import partial
from logging import getLogger

import maya.cmds as cmds
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

from ..command import convert_weight
from ..lib_ui import maya_qt, maya_ui

logger = getLogger(__name__)


class AdjustCenterSkinWeightsWidgets(QWidget):

    def __init__(self, parent=None):
        """Constructor.
        """
        super().__init__(parent=parent)

        self.main_layout = QVBoxLayout()

        layout = QGridLayout()

        label = QLabel('Source Influences:', alignment=Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(label, 0, 0)

        self.src_infs_field = QLineEdit()
        layout.addWidget(self.src_infs_field, 0, 1)

        src_infs_button = QPushButton('SET')
        layout.addWidget(src_infs_button, 0, 2)

        label = QLabel('Target Influences:', alignment=Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(label, 1, 0)

        self.target_infs_field = QLineEdit()
        layout.addWidget(self.target_infs_field, 1, 1)

        target_infs_button = QPushButton('SET')
        layout.addWidget(target_infs_button, 1, 2)

        label = QLabel('Static Influence:', alignment=Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(label, 2, 0)

        self.static_inf_field = QLineEdit()
        layout.addWidget(self.static_inf_field, 2, 1)

        static_inf_button = QPushButton('SET')
        layout.addWidget(static_inf_button, 2, 2)

        layout.setColumnStretch(1, 1)

        self.main_layout.addLayout(layout)

        button = QPushButton('Adjust Center Weights')
        self.main_layout.addWidget(button)

        self.main_layout.addStretch()

        self.setLayout(self.main_layout)

        # Signal & Slot
        src_infs_button.clicked.connect(partial(self.___set_selected_nodes, self.src_infs_field))
        target_infs_button.clicked.connect(partial(self.___set_selected_nodes, self.target_infs_field))
        static_inf_button.clicked.connect(partial(self.__set_selected_node, self.static_inf_field))

        button.clicked.connect(self.exchange_influences)

    @maya_ui.error_handler
    def ___set_selected_nodes(self, field):
        """Set the selected nodes to the field.
        """
        nodes = cmds.ls(sl=True, type='joint')
        if not nodes:
            if not cmds.ls(sl=True):
                field.setText('')
            else:
                cmds.error('Select joints.')

        field.setText(' '.join(nodes))

    @ maya_ui.error_handler
    def __set_selected_node(self, field):
        """Set the selected node to the field.
        """
        nodes = cmds.ls(sl=True, type='joint')
        if not nodes:
            if not cmds.ls(sl=True):
                field.setText('')
            else:
                cmds.error('Select a joint.')

        field.setText(nodes[0])

    @ maya_ui.undo_chunk('Adjust Center Weights')
    @ maya_ui.error_handler
    def exchange_influences(self):
        """Exchange the influences.
        """
        src_infs = self.src_infs_field.text().split()
        target_infs = self.target_infs_field.text().split()
        static_inf = self.static_inf_field.text()

        if not src_infs:
            cmds.error('No source influences.')
        if not target_infs:
            cmds.error('No target influences.')

        if not static_inf:
            static_inf = None

        if len(src_infs) != len(target_infs):
            cmds.error('Influence count mismatch.')

        components = cmds.filterExpand(sm=[28, 31, 46], ex=True)
        if not components:
            cmds.error('No components selected.')

        pair_infs = list(zip(src_infs, target_infs))

        convert_weight.combine_pair_skin_weights(pair_infs, components, static_inf=static_inf)


def show_ui():
    """Show the main window.
    """
    window_name = f'{__name__}MainWindow'
    maya_qt.delete_widget(window_name)

    window = QMainWindow(parent=maya_qt.get_maya_pointer())
    window.setObjectName(window_name)
    window.setWindowTitle('Skin Weights Adjust Center')
    window.setAttribute(Qt.WA_DeleteOnClose)

    widgets = AdjustCenterSkinWeightsWidgets()
    window.setCentralWidget(widgets)

    window.show()
    window.resize(300, 0)
