"""
SkinWeights Tools. All skinWeights tools are integrated into one tool.
"""

from logging import getLogger

import maya.cmds as cmds

try:
    from PySide2.QtWidgets import QComboBox, QGroupBox, QStackedWidget, QVBoxLayout
except ImportError:
    from PySide6.QtWidgets import QComboBox, QGroupBox, QStackedWidget, QVBoxLayout

from ..command import convert_weight
from ..lib import lib_skinCluster
from ..lib_ui import base_window, maya_qt, maya_ui
from ..lib_ui.widgets import extra_widgets
from . import (
    influence_exchanger_ui,
    skinWeights_adjust_center_ui,
    skinWeights_bar_ui,
    skinWeights_combine_ui,
    skinWeights_copy_custom_ui,
    skinWeights_to_mesh_ui,
)

logger = getLogger(__name__)


class MainWindow(base_window.BaseMainWindow):
    """Skin Weights Tools Main Window."""

    def __init__(self, parent=None, object_name="MainWindow", window_title="Main Window"):
        """Constructor."""
        super().__init__(parent=parent, object_name=object_name, window_title=window_title)

        # Menu
        self.menu = self.menuBar()
        self._add_menu()

        # Add skinWeights bar
        self.skinWeightsBar = skinWeights_bar_ui.SkinWeightsBar()
        self.central_layout.addWidget(self.skinWeightsBar)

        separator = extra_widgets.HorizontalSeparator()
        self.central_layout.addWidget(separator)

        # Add skinWeights widgets
        widgets_layout = QVBoxLayout()
        widgets_layout.setSpacing(0)
        widgets_layout.setContentsMargins(0, 0, 0, 0)

        self.widgets_box = QComboBox()
        self.widgets_box.addItems(self.widgets_data().keys())
        widgets_layout.addWidget(self.widgets_box)

        widgets_group = QGroupBox()
        widgets_layout.addWidget(widgets_group)

        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        self.widgets_stack_widget = QStackedWidget()

        for widget in self.widgets_data().values():
            self.widgets_stack_widget.addWidget(widget())

        layout.addWidget(self.widgets_stack_widget)
        widgets_group.setLayout(layout)

        widgets_layout.addLayout(layout)

        self.central_layout.addLayout(widgets_layout)

        # Signal & Slot
        self.widgets_box.currentIndexChanged.connect(self.widgets_stack_widget.setCurrentIndex)

    def widgets_data(self):
        """List of widgets data."""
        return {
            "Copy Skin Weights Custom": skinWeights_copy_custom_ui.SkinWeightsCopyCustomWidgets,
            "Skin Weights to Mesh": skinWeights_to_mesh_ui.SkinWeightsMeshConverterWidgets,
            "Adjust Center Skin Weights": skinWeights_adjust_center_ui.AdjustCenterSkinWeightsWidgets,
            "Combine Skin Weights": skinWeights_combine_ui.CombineSkinWeightsWidgets,
            "Influence Exchange": influence_exchanger_ui.InfluenceExchangerWidgets,
        }

    def _add_menu(self):
        """Add menu."""
        edit_menu = self.menu.addMenu("Edit")

        action = edit_menu.addAction("Select Influences")
        action.triggered.connect(self.select_influences)

        action = edit_menu.addAction("Rebind SkinCluster")
        action.triggered.connect(self.rebind_skinCluster)

        edit_menu.addSeparator()

        action = edit_menu.addAction("Prune Small Weights")
        action.triggered.connect(self.prune_small_weights)

        action = edit_menu.addAction("Remove Unused Influences")
        action.triggered.connect(self.remove_unused_influences)

        edit_menu.addSeparator()

        action = edit_menu.addAction("Average Skin Weights")
        action.triggered.connect(self.average_skin_weights)

        action = edit_menu.addAction("Average Skin Weights Shell")
        action.triggered.connect(self.average_skin_weights_shell)

    @maya_ui.undo_chunk("Select Influences")
    @maya_ui.error_handler
    def select_influences(self):
        """Select the influences."""
        sel_nodes = cmds.ls(sl=True)
        if not sel_nodes:
            cmds.error("Select geometry or components.")

        influences = convert_weight.get_influences_from_objects(sel_nodes)
        if not influences:
            cmds.warning("No influences found.")
            return

        cmds.select(influences, r=True)

    @maya_ui.undo_chunk("Rebind SkinCluster")
    @maya_ui.error_handler
    def rebind_skinCluster(self):
        """Rebind the skinCluster."""
        target_skinClusters = self._get_skinClusters()
        influences = cmds.ls(sl=True, type="joint")

        if target_skinClusters:
            for skinCluster in target_skinClusters:
                lib_skinCluster.rebind_skinCluster(skinCluster)

        if influences:
            lib_skinCluster.rebind_skinCluster_from_influence(influences)

    @maya_ui.undo_chunk("Prune Small Weights")
    @maya_ui.error_handler
    def prune_small_weights(self):
        """Prune small weights."""
        sel_dag_nodes = cmds.ls(sl=True, dag=True, shapes=True, ni=True)
        if not sel_dag_nodes:
            cmds.error("Select geometry to prune small weights.")

        convert_weight.prune_small_weights(sel_dag_nodes, threshold=0.005)

    @maya_ui.undo_chunk("Remove Unused Influences")
    @maya_ui.error_handler
    def remove_unused_influences(self):
        """Remove unused influences."""
        shapes = cmds.ls(sl=True, dag=True, shapes=True, ni=True)
        if not shapes:
            cmds.error("Select geometry to remove unused influences.")

        for shape in shapes:
            skinCluster = lib_skinCluster.get_skinCluster(shape)
            if not skinCluster:
                cmds.warning(f"No skinCluster found: {shape}")
                continue

            lib_skinCluster.remove_unused_influences(skinCluster)

    @maya_ui.undo_chunk("Average Skin Weights")
    @maya_ui.error_handler
    def average_skin_weights(self):
        """Average skin weights."""
        sel_components = cmds.filterExpand(sm=[28, 31, 46])
        if not sel_components:
            cmds.error("Select components to average skin weights.")

        convert_weight.average_skin_weights(sel_components)

    @maya_ui.undo_chunk("Average Skin Weights Shell")
    @maya_ui.error_handler
    def average_skin_weights_shell(self):
        """Average skin weights shell."""
        meshs = cmds.ls(sl=True, dag=True, type="mesh", ni=True)
        if not meshs:
            cmds.error("Select mesh to average skin weights shell.")

        for mesh in meshs:
            convert_weight.average_skin_weights_shell(mesh)

    def _get_skinClusters(self):
        """Get the skinClusters."""
        shapes = cmds.ls(sl=True, dag=True, type="deformableShape", objectsOnly=True, ni=True)
        skinClusters = cmds.ls(sl=True, type="skinCluster")

        target_skinClusters = []
        if shapes:
            for shape in shapes:
                skinCluster = lib_skinCluster.get_skinCluster(shape)
                if skinCluster and skinCluster not in target_skinClusters:
                    target_skinClusters.append(skinCluster)
        if skinClusters:
            for skinCluster in skinClusters:
                if skinCluster not in target_skinClusters:
                    target_skinClusters.append(skinCluster)

        return target_skinClusters


def show_ui():
    """Show the main window."""
    window_name = f"{__name__}MainWindow"
    maya_qt.delete_widget(window_name)

    # Create the main window.
    main_window = MainWindow(parent=maya_qt.get_maya_pointer(), object_name=window_name, window_title="Skin Weights Tools")
    main_window.show()
    main_window.resize(0, 0)
