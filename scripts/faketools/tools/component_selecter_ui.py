"""
Component selection tool.
"""

from logging import getLogger

import maya.cmds as cmds

try:
    from PySide2.QtCore import Qt
    from PySide2.QtWidgets import (
        QButtonGroup,
        QGridLayout,
        QHBoxLayout,
        QLabel,
        QPushButton,
        QRadioButton,
        QSpinBox,
    )
except ImportError:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import (
        QButtonGroup,
        QGridLayout,
        QHBoxLayout,
        QLabel,
        QPushButton,
        QRadioButton,
        QSpinBox,
    )

from ..lib import lib_component
from ..lib_ui import base_window, maya_qt, maya_ui, optionvar
from ..lib_ui.widgets import extra_widgets

logger = getLogger(__name__)


class MainWindow(base_window.BaseMainWindow):
    def __init__(self, parent=None, object_name="MainWindow", window_title="Main Window"):
        """Constructor."""
        super().__init__(parent=parent, object_name=object_name, window_title=window_title)

        self.tool_options = optionvar.ToolOptionSettings(__name__)

        self.menu = self.menuBar()
        self._add_menu()

        # Unique selection
        label = QLabel("Unique Selection")
        label.setStyleSheet("font-weight: bold;")
        self.central_layout.addWidget(label)

        unique_sel_button = QPushButton("Unique")
        self.central_layout.addWidget(unique_sel_button)

        reverse_sel_button = QPushButton("Reverse")
        self.central_layout.addWidget(reverse_sel_button)

        same_sel_button = QPushButton("Same")
        self.central_layout.addWidget(same_sel_button)

        separator = extra_widgets.HorizontalSeparator()
        self.central_layout.addWidget(separator)

        # Area selection
        label = QLabel("Area Selection")
        label.setStyleSheet("font-weight: bold;")
        self.central_layout.addWidget(label)

        layout = QHBoxLayout()

        right_area_sel_button = QPushButton("Right")
        layout.addWidget(right_area_sel_button)

        center_area_sel_button = QPushButton("Center")
        layout.addWidget(center_area_sel_button)

        left_area_sel_button = QPushButton("Left")
        layout.addWidget(left_area_sel_button)

        self.central_layout.addLayout(layout)

        separator = extra_widgets.HorizontalSeparator()
        self.central_layout.addWidget(separator)

        # Control components selection
        label = QLabel("CV Area Selection")
        label.setStyleSheet("font-weight: bold;")
        self.central_layout.addWidget(label)

        layout = QGridLayout()

        label = QLabel("UV:", alignment=Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(label, 0, 0)

        self.u_button = QRadioButton("u")
        layout.addWidget(self.u_button, 0, 1)

        self.v_button = QRadioButton("v")
        layout.addWidget(self.v_button, 0, 2)

        self.uv_button_group = QButtonGroup()
        self.uv_button_group.addButton(self.u_button)
        self.uv_button_group.addButton(self.v_button)

        label = QLabel("Min:", alignment=Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(label, 1, 0)

        self.min_param_spinbox = QSpinBox()
        self.min_param_spinbox.setRange(0, 100)
        layout.addWidget(self.min_param_spinbox, 1, 1)

        label = QLabel("Max:", alignment=Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(label, 1, 2)

        self.max_param_spinbox = QSpinBox()
        self.max_param_spinbox.setRange(0, 100)
        layout.addWidget(self.max_param_spinbox, 1, 3)

        self.central_layout.addLayout(layout)

        layout.setColumnStretch(1, 1)
        layout.setColumnStretch(3, 1)

        uv_sel_button = QPushButton("Select")
        self.central_layout.addWidget(uv_sel_button)

        # Option settings
        if self.tool_options.read("uv", "u") == "u":
            self.u_button.setChecked(True)
        else:
            self.v_button.setChecked(True)

        self.min_param_spinbox.setValue(self.tool_options.read("min_param", 0))
        self.max_param_spinbox.setValue(self.tool_options.read("max_param", 1))

        # Signal and slot
        unique_sel_button.clicked.connect(self.unique_selection)
        reverse_sel_button.clicked.connect(self.reverse_selection)
        same_sel_button.clicked.connect(self.same_selection)
        right_area_sel_button.clicked.connect(self.right_area_selection)
        center_area_sel_button.clicked.connect(self.center_area_selection)
        left_area_sel_button.clicked.connect(self.left_area_selection)
        uv_sel_button.clicked.connect(self.uv_area_selection)

        self.min_param_spinbox.valueChanged.connect(self.__update_uv_spinbox)
        self.max_param_spinbox.valueChanged.connect(self.__update_uv_spinbox)

    def _add_menu(self):
        """Add menu."""
        menu = self.menu.addMenu("Edit")

        action = menu.addAction("Toggle Soft Selection")
        action.triggered.connect(self.toggle_soft_selection)

        action = menu.addAction("Toggle Symmetry Selection")
        action.triggered.connect(self.toggle_symmetry_selection)

    @maya_ui.undo_chunk("Unique selection")
    @maya_ui.error_handler
    def unique_selection(self):
        """Unique selection."""
        sel_components = cmds.ls(selection=True, flatten=True)
        if not sel_components:
            cmds.error("Select components.")

        unique_components = lib_component.ComponentSelection(sel_components).unique_selection()
        cmds.select(unique_components, r=True)

    @maya_ui.undo_chunk("Reverse selection")
    @maya_ui.error_handler
    def reverse_selection(self):
        """Reverse selection."""
        sel_components = cmds.ls(selection=True, flatten=True)
        if not sel_components:
            cmds.error("Select components.")

        reverse_components = lib_component.ComponentSelection(sel_components).reverse_selection()
        cmds.select(reverse_components, r=True)

    @maya_ui.undo_chunk("Same selection")
    @maya_ui.error_handler
    def same_selection(self):
        """Same selection."""
        sel_nodes = cmds.ls(selection=True, flatten=True)
        if not sel_nodes:
            cmds.error("Select objects.")

        if len(sel_nodes) < 2:
            cmds.error("Select more than 2 objects.")

        mesh_transform = sel_nodes[0]
        components = sel_nodes[1:]

        if cmds.nodeType(mesh_transform) != "transform":
            cmds.error("First selected object is not transform node.")

        mesh = cmds.listRelatives(mesh_transform, shapes=True)
        if not mesh:
            cmds.error("First selected object has no shape node.")

        if cmds.nodeType(mesh[0]) != "mesh":
            cmds.error("First selected object has no mesh shape node.")
        else:
            mesh = mesh[0]

        same_components = lib_component.ComponentSelection(components).same_position_selection(mesh)
        if not same_components:
            cmds.warning("No same position components.")
        else:
            cmds.select(same_components, r=True)

    @maya_ui.undo_chunk("Right area selection")
    @maya_ui.error_handler
    def right_area_selection(self):
        """Right area selection."""
        sel_components = self._select_objects_to_components()
        if not sel_components:
            cmds.error("Select transform or shape nodes.")

        right_components = lib_component.ComponentSelection(sel_components).x_area_selection(area="right")
        if not right_components:
            cmds.warning("No right components.")
        else:
            cmds.select(right_components, r=True)

    @maya_ui.undo_chunk("Left area selection")
    @maya_ui.error_handler
    def left_area_selection(self):
        """Left selection."""
        sel_components = self._select_objects_to_components()
        if not sel_components:
            cmds.error("Select transform or shape nodes.")

        left_components = lib_component.ComponentSelection(sel_components).x_area_selection(area="left")
        if not left_components:
            cmds.warning("No left components.")
        else:
            cmds.select(left_components, r=True)

    @maya_ui.undo_chunk("Center area selection")
    @maya_ui.error_handler
    def center_area_selection(self):
        """Center selection."""
        sel_components = self._select_objects_to_components()
        if not sel_components:
            cmds.error("Select transform or shape nodes.")

        center_components = lib_component.ComponentSelection(sel_components).x_area_selection(area="center")
        if not center_components:
            cmds.warning("No center components.")
        else:
            cmds.select(center_components, r=True)

    @maya_ui.undo_chunk("UV area selection")
    @maya_ui.error_handler
    def uv_area_selection(self):
        """UV area selection."""
        sel_components = self._select_objects_to_components(filter_types=["nurbsCurve", "nurbsSurface"])
        if not sel_components:
            cmds.error("Select transform or shape nodes. (nurbsCurve, nurbsSurface)")

        min_param = self.min_param_spinbox.value()
        max_param = self.max_param_spinbox.value()

        uv = "u" if self.uv_button_group.checkedButton().text() == "u" else "v"

        uv_components = lib_component.ComponentSelection(sel_components).uv_area_selection(uv=uv, area=[min_param, max_param])
        if not uv_components:
            cmds.warning("No uv components.")
        else:
            cmds.select(uv_components, r=True)

    @maya_ui.undo_chunk("Toggle soft selection")
    @maya_ui.error_handler
    def toggle_soft_selection(self):
        """Toggle soft selection."""
        current_soft_select = cmds.softSelect(q=True, sse=True)
        if current_soft_select:
            cmds.softSelect(sse=False)
        else:
            cmds.softSelect(sse=True)

    @maya_ui.undo_chunk("Toggle symmetry selection")
    @maya_ui.error_handler
    def toggle_symmetry_selection(self):
        """Toggle symmetry selection."""
        current_symmetric = cmds.symmetricModelling(q=True, s=True)
        if current_symmetric:
            cmds.symmetricModelling(s=False)
        else:
            cmds.symmetricModelling(s=True)
            cmds.select(cmds.ls(sl=True), sym=True)

    def _select_objects_to_components(self, filter_types: list[str] = None) -> list[str]:
        """Convert objects to components.

        Args:
            filter_types (list[str]): Filter types. Defaults to ['mesh', 'nurbsCurve', 'nurbsSurface', 'lattice'].

        Returns:
            list[str]: Component list.
        """
        if filter_types is None:
            filter_types = ["mesh", "nurbsCurve", "nurbsSurface", "lattice"]
        objects = cmds.ls(sl=True, objectsOnly=True, long=True)
        if not objects:
            cmds.error("Select transform or shape nodes.")

        objects = list(dict.fromkeys(objects))
        components = []
        for obj in objects:
            if cmds.nodeType(obj) == "transform":
                shape = cmds.listRelatives(obj, shapes=True, fullPath=True, ni=True)
                if not shape:
                    continue
                shape = shape[0]
            elif "geometryShape" in cmds.nodeType(obj, i=True):
                shape = obj
                obj = cmds.listRelatives(obj, parent=True, fullPath=True)[0]
            else:
                logger.debug(f"Invalid object: {obj}")
                continue

            if cmds.nodeType(shape) not in filter_types:
                logger.debug(f"Invalid shape type not in {filter_types}: {shape}")
                continue

            components.extend(cmds.ls(f"{obj}.cp[*]", flatten=True))

        return components

    def __update_uv_spinbox(self):
        """Update UV spinbox."""
        sender = self.sender()
        if sender not in [self.max_param_spinbox, self.min_param_spinbox]:
            return

        max_value = self.max_param_spinbox.value()
        min_value = self.min_param_spinbox.value()

        if sender == self.max_param_spinbox:
            if max_value < min_value:
                cmds.warning("Max value is smaller than min value.")
                self.max_param_spinbox.setValue(min_value)
        elif sender == self.min_param_spinbox and min_value > max_value:
            cmds.warning("Min value is larger than max value.")
            self.min_param_spinbox.setValue(max_value)

    def closeEvent(self, event):
        """Close event."""
        # Save option settings
        self.tool_options.write("uv", self.uv_button_group.checkedButton().text())
        self.tool_options.write("min_param", self.min_param_spinbox.value())
        self.tool_options.write("max_param", self.max_param_spinbox.value())

        super().closeEvent(event)


def show_ui():
    """Show the main window."""
    window_name = f"{__name__}MainWindow"
    maya_qt.delete_widget(window_name)

    # Create the main window.
    main_window = MainWindow(parent=maya_qt.get_maya_pointer(), object_name=window_name, window_title="Component Selecter")
    main_window.show()
