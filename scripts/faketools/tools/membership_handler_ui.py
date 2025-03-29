"""
Membership Handler for deformer tags tool.
"""

from logging import getLogger

import maya.cmds as cmds

try:
    from PySide2.QtWidgets import QLineEdit
except ImportError:
    from PySide6.QtWidgets import QLineEdit

from ..lib import lib_memberShip, lib_selection
from ..lib_ui import base_window, maya_qt, maya_ui
from ..lib_ui.widgets import extra_widgets

logger = getLogger(__name__)


class MainWindow(base_window.BaseMainWindow):

    def __init__(self,
                 parent=None,
                 object_name='MainWindow',
                 window_title='Main Window'):
        """Constructor.
        """
        super().__init__(parent=parent, object_name=object_name, window_title=window_title, central_layout='horizontal')

        self.deformer = None

        set_deformer_button = extra_widgets.ToolIconButton('log-in')
        self.central_layout.addWidget(set_deformer_button)

        self.deformer_field = QLineEdit()
        self.deformer_field.setReadOnly(True)
        self.deformer_field.setPlaceholderText('Deformer')
        self.central_layout.addWidget(self.deformer_field, stretch=1)

        update_button = extra_widgets.ToolIconButton('refresh-cw-2')
        self.central_layout.addWidget(update_button)

        select_button = extra_widgets.ToolIconButton('mouse-pointer-2')
        self.central_layout.addWidget(select_button)

        # Signal & Slot
        set_deformer_button.clicked.connect(self.set_deformer)
        update_button.clicked.connect(self.update_memberships)
        select_button.clicked.connect(self.select_memberships)

        # Initialize the UI.
        margins = base_window.get_margins(self.central_widget)
        self.central_layout.setContentsMargins(*[margin * 0.5 for margin in margins])

        minimum_size_hint = self.minimumSizeHint()
        size_hint = self.sizeHint()
        self.resize(size_hint.width() * 1.2, minimum_size_hint.height())

    @maya_ui.error_handler
    def set_deformer(self):
        """Set the deformer to the selected deformer.
        """
        # Get the selected deformer.
        sel_deformers = cmds.ls(sl=True, type='weightGeometryFilter')
        if not sel_deformers:
            cmds.error('Select any weightGeometryFilter.')

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

        lib_memberShip.remove_deformer_blank_indices(self.deformer.deformer_name)
        self.deformer.update_components(components)

    @maya_ui.error_handler
    def select_memberships(self):
        """Select the memberships.
        """
        if not self.deformer:
            cmds.error('Set any deformer to field.')

        components = self.deformer.get_components()
        cmds.select(components, r=True)

        # Change the component mode.
        selection_mode = lib_selection.SelectionMode()
        selection_mode.to_component()

        for component_type in ['vertex', 'controlVertex', 'latticePoint']:
            selection_mode.set_component_mode(component_type, True)

        objs = cmds.ls(sl=True, objectsOnly=True)
        hilite_selection = lib_selection.HiliteSelection()
        hilite_selection.hilite(objs, replace=True)


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
