"""
Membership Handler for deformer tags tool.
"""

from logging import getLogger

import maya.cmds as cmds
from PySide2.QtCore import Qt
from PySide2.QtGui import QIcon
from PySide2.QtWidgets import QHBoxLayout, QLineEdit, QMainWindow, QPushButton, QWidget

from ..lib import lib_memberShip
from ..lib_ui import maya_qt, maya_ui, tool_icons

logger = getLogger(__name__)


class MainWindow(QMainWindow):

    def __init__(self,
                 parent=None,
                 object_name='MainWindow',
                 window_title='Main Window'):
        """Constructor.
        """
        super().__init__(parent=parent)

        self.deformer = None

        self.setObjectName(object_name)
        self.setWindowTitle(window_title)
        self.setAttribute(Qt.WA_DeleteOnClose)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.central_layout = QHBoxLayout()
        self.central_widget.setLayout(self.central_layout)

        set_deformer_button = QPushButton()
        icon = QIcon(tool_icons.get_icon_path('log-in'))
        set_deformer_button.setIcon(icon)
        self.central_layout.addWidget(set_deformer_button)

        self.deformer_field = QLineEdit()
        self.deformer_field.setReadOnly(True)
        self.deformer_field.setPlaceholderText('Deformer')
        self.central_layout.addWidget(self.deformer_field, stretch=1)

        update_button = QPushButton()
        icon = QIcon(tool_icons.get_icon_path('refresh-cw'))
        update_button.setIcon(icon)
        self.central_layout.addWidget(update_button)

        select_button = QPushButton()
        icon = QIcon(tool_icons.get_icon_path('mouse-pointer-2'))
        select_button.setIcon(icon)
        self.central_layout.addWidget(select_button)

        # Signal & Slot
        set_deformer_button.clicked.connect(self.set_deformer)
        update_button.clicked.connect(self.update_memberships)
        select_button.clicked.connect(self.select_memberships)

    @maya_ui.error_handler
    def set_deformer(self):
        """Set the deformer to the selected deformer.
        """
        # Get the selected deformer.
        sel_deformers = cmds.ls(sl=True, type='weightGeometryFilter')
        if not sel_deformers:
            cmds.error('Select any weightGeometryFilter.')
            return

        self.deformer_field.setText(sel_deformers[0])
        self.deformer = lib_memberShip.DeformerMembership(sel_deformers[0])

    @maya_ui.undo_chunk('Update Memberships')
    @maya_ui.error_handler
    def update_memberships(self):
        """Update the memberships.
        """
        if not self.deformer:
            cmds.error('Set any deformer to field.')

        components = cmds.filterExpand(expand=True, sm=(28, 31, 46))
        if not components:
            cmds.error('Select any components (vertex, cv, latticePoint).')

        self.deformer.update_components(components)

    @maya_ui.error_handler
    def select_memberships(self):
        """Select the memberships.
        """
        if not self.deformer:
            cmds.error('Set any deformer to field.')

        components = self.deformer.get_components()
        cmds.select(components, r=True)


def show_ui():
    """Show the main window.
    """
    if not lib_memberShip.is_use_component_tag():
        cmds.warning('Please enable component tags from preferences of rigging before launching the tool.')
        return

    window_name = f'{__name__}MainWindow'
    maya_qt.delete_widget(window_name)

    # Create the main window.
    main_window = MainWindow(parent=maya_qt.get_maya_pointer(),
                             object_name=window_name,
                             window_title='Membership Handler')
    main_window.show()
    main_window.setFixedHeight(0)
