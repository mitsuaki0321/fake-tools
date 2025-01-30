"""
Exchange the influence of skinCluster tool.
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

from ..lib import lib_skinCluster
from ..lib_ui import base_window, maya_qt, maya_ui

logger = getLogger(__name__)


class InfluenceExchangerWidgets(QWidget):

    def __init__(self, parent=None, window_mode: bool = False):
        """Constructor.
        """
        super().__init__(parent=parent)

        self.main_layout = QVBoxLayout()
        spacing = base_window.get_spacing(self)
        self.main_layout.setSpacing(spacing * 0.75)

        if not window_mode:
            margins = base_window.get_margins(self)
            self.main_layout.setContentsMargins(*[margin * 0.5 for margin in margins])

        layout = QGridLayout()

        label = QLabel('Target SkinClusters:', alignment=Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(label, 0, 0)

        self.target_skinCluster_field = QLineEdit()
        layout.addWidget(self.target_skinCluster_field, 0, 1)

        skinCluster_button = QPushButton('SET')
        layout.addWidget(skinCluster_button, 0, 2)

        label = QLabel('Binding Influences:', alignment=Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(label, 1, 0)

        self.binding_inf_field = QLineEdit()
        layout.addWidget(self.binding_inf_field, 1, 1)

        inf_button = QPushButton('SET')
        layout.addWidget(inf_button, 1, 2)

        label = QLabel('Exchange Influences:', alignment=Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(label, 2, 0)

        self.exchange_inf_field = QLineEdit()
        layout.addWidget(self.exchange_inf_field, 2, 1)

        exchange_button = QPushButton('SET')
        layout.addWidget(exchange_button, 2, 2)

        layout.setColumnStretch(1, 1)

        self.main_layout.addLayout(layout)

        button = QPushButton('Exchange Influence')
        self.main_layout.addWidget(button)

        self.main_layout.addStretch()

        self.setLayout(self.main_layout)

        # Signal & Slot
        skinCluster_button.clicked.connect(partial(self.__set_selected_nodes, self.target_skinCluster_field, 'skinCluster'))
        inf_button.clicked.connect(partial(self.__set_selected_nodes, self.binding_inf_field, 'joint'))
        exchange_button.clicked.connect(partial(self.__set_selected_nodes, self.exchange_inf_field, 'joint'))

        button.clicked.connect(self.exchange_influences)

    @maya_ui.error_handler
    def __set_selected_nodes(self, field: QLineEdit, node_type: str) -> None:
        """Set the selected nodes to the field.
        """
        nodes = cmds.ls(sl=True, type=node_type)
        if not nodes:
            cmds.error(f'No {node_type} selected.')

        field.setText(' '.join(nodes))

    @maya_ui.undo_chunk('Exchange Influences')
    @maya_ui.error_handler
    def exchange_influences(self):
        """Exchange the influences.
        """
        target_skinClusters = self.target_skinCluster_field.text().split()
        if not target_skinClusters:
            cmds.error('No target skinClusters found.')

        binding_influences = self.binding_inf_field.text().split()
        if not binding_influences:
            cmds.error('No binding influences found.')

        exchange_influences = self.exchange_inf_field.text().split()
        if not exchange_influences:
            cmds.error('No exchange influences found.')

        if len(binding_influences) != len(exchange_influences):
            cmds.error('The number of binding influences and exchange influences do not match.')

        for target_skinCluster in target_skinClusters:
            lib_skinCluster.exchange_influences(target_skinCluster, binding_influences, exchange_influences)


def show_ui():
    """Show the main window.
    """
    window_name = f'{__name__}MainWindow'
    maya_qt.delete_widget(window_name)

    window = QMainWindow(parent=maya_qt.get_maya_pointer())
    window.setObjectName(window_name)
    window.setWindowTitle('Influence Exchanger')
    window.setAttribute(Qt.WA_DeleteOnClose)

    widgets = InfluenceExchangerWidgets(window_mode=True)
    window.setCentralWidget(widgets)

    window.show()
    window.resize(300, 0)
