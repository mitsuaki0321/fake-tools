"""
Create transform nodes on the curve tool.
"""

from functools import partial
from logging import getLogger

import maya.cmds as cmds

try:
    from PySide2.QtCore import Qt
    from PySide2.QtWidgets import (
        QCheckBox,
        QComboBox,
        QDoubleSpinBox,
        QHBoxLayout,
        QLabel,
        QPushButton,
        QSpinBox,
    )
except ImportError:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import (
        QCheckBox,
        QComboBox,
        QDoubleSpinBox,
        QHBoxLayout,
        QLabel,
        QPushButton,
        QSpinBox,
    )

from ..command import create_transforms
from ..lib_ui import base_window, maya_qt, maya_ui, optionvar
from ..lib_ui.widgets import extra_widgets

logger = getLogger(__name__)


class MainWindow(base_window.BaseMainWindow):
    def __init__(self, parent=None, object_name="MainWindow", window_title="Main Window"):
        """Constructor."""
        super().__init__(parent=parent, object_name=object_name, window_title=window_title)

        self.tool_options = optionvar.ToolOptionSettings(__name__)

        self.preview_locator = None
        self.script_job_ids = []

        self.method_box = QComboBox()
        self.method_box.addItems(self.method_data().keys())
        self.central_layout.addWidget(self.method_box)

        self.node_type_box = QComboBox()
        self.node_type_box.addItems(["locator", "joint"])
        self.central_layout.addWidget(self.node_type_box)

        layout = QHBoxLayout()

        size_label = QLabel("Size:")
        layout.addWidget(size_label)

        self.size_field = extra_widgets.ModifierSpinBox()
        self.size_field.setDecimals(2)
        layout.addWidget(self.size_field, stretch=1)

        self.central_layout.addLayout(layout)

        layout = QHBoxLayout()

        div_label = QLabel("Divisions:")
        layout.addWidget(div_label)

        self.divisions_field = QSpinBox()
        self.divisions_field.setMinimum(1)
        self.divisions_field.setMaximum(100)
        layout.addWidget(self.divisions_field, stretch=1)

        self.central_layout.addLayout(layout)

        self.central_layout.addWidget(extra_widgets.HorizontalSeparator())

        self.include_rotation_cb = QCheckBox("Include Rotation")
        self.central_layout.addWidget(self.include_rotation_cb)

        layout = QHBoxLayout()
        layout.setSpacing(0)

        self.rotate_offset_field_x = QDoubleSpinBox()
        self.rotate_offset_field_x.setSingleStep(45.0)
        self.rotate_offset_field_x.setDecimals(2)
        self.rotate_offset_field_x.setMaximum(360.0)
        self.rotate_offset_field_x.setMinimum(-360.0)
        layout.addWidget(self.rotate_offset_field_x)

        self.rotate_offset_field_y = QDoubleSpinBox()
        self.rotate_offset_field_y.setSingleStep(45.0)
        self.rotate_offset_field_y.setDecimals(2)
        self.rotate_offset_field_y.setMaximum(360.0)
        self.rotate_offset_field_y.setMinimum(-360.0)
        layout.addWidget(self.rotate_offset_field_y)

        self.rotate_offset_field_z = QDoubleSpinBox()
        self.rotate_offset_field_z.setSingleStep(45.0)
        self.rotate_offset_field_z.setDecimals(2)
        self.rotate_offset_field_z.setMaximum(360.0)
        self.rotate_offset_field_z.setMinimum(-360.0)
        layout.addWidget(self.rotate_offset_field_z)

        self.central_layout.addLayout(layout)

        layout = QHBoxLayout()

        aim_label = QLabel("AimVector:")
        layout.addWidget(aim_label)

        self.aim_vector_box = QComboBox()
        self.aim_vector_box.addItems(self.aim_vector_data().keys())
        layout.addWidget(self.aim_vector_box, stretch=1)

        self.central_layout.addLayout(layout)

        layout = QHBoxLayout()

        up_label = QLabel("UpVector:")
        layout.addWidget(up_label)

        self.up_vector_box = QComboBox()
        self.up_vector_box.addItems(self.up_vector_data().keys())
        layout.addWidget(self.up_vector_box, stretch=1)

        self.central_layout.addLayout(layout)

        self.central_layout.addWidget(extra_widgets.HorizontalSeparator())

        self.reverse_cb = QCheckBox("Reverse")
        self.central_layout.addWidget(self.reverse_cb)

        self.chain_cb = QCheckBox("Chain")
        self.central_layout.addWidget(self.chain_cb)

        self.central_layout.addWidget(extra_widgets.HorizontalSeparator())

        self.preview_cb = QCheckBox("Preview")
        self.central_layout.addWidget(self.preview_cb)

        self.central_layout.addWidget(extra_widgets.HorizontalSeparator())

        self.create_button = QPushButton("Create")
        self.central_layout.addWidget(self.create_button)

        # Option settings
        self.method_box.setCurrentIndex(self.tool_options.read("method", 0))
        self.node_type_box.setCurrentIndex(self.tool_options.read("node_type", 0))
        self.size_field.setValue(self.tool_options.read("size", 1.0))
        self.divisions_field.setValue(self.tool_options.read("divisions", 3))
        self.include_rotation_cb.setChecked(self.tool_options.read("include_rotation", False))
        self.rotate_offset_field_x.setValue(self.tool_options.read("rotate_offsetX", 0.0))
        self.rotate_offset_field_y.setValue(self.tool_options.read("rotate_offsetY", 0.0))
        self.rotate_offset_field_z.setValue(self.tool_options.read("rotate_offsetZ", 0.0))
        self.aim_vector_box.setCurrentIndex(self.tool_options.read("aim_vector", 0))
        self.up_vector_box.setCurrentIndex(self.tool_options.read("up_vector", 0))
        self.reverse_cb.setChecked(self.tool_options.read("reverse", False))
        self.chain_cb.setChecked(self.tool_options.read("chain", False))

        # Signal and slot
        # Preview options
        self.method_box.currentIndexChanged.connect(partial(self.update_preview_options, sender=self.method_box))
        self.method_box.currentIndexChanged.connect(self.switch_method)
        self.node_type_box.currentIndexChanged.connect(partial(self.update_preview_options, sender=self.node_type_box))
        self.size_field.valueChanged.connect(partial(self.update_preview_options, sender=self.size_field))
        self.divisions_field.valueChanged.connect(partial(self.update_preview_options, sender=self.divisions_field))
        self.include_rotation_cb.stateChanged.connect(partial(self.update_preview_options, sender=self.include_rotation_cb))
        self.rotate_offset_field_x.valueChanged.connect(partial(self.update_preview_options, sender=self.rotate_offset_field_x))
        self.rotate_offset_field_y.valueChanged.connect(partial(self.update_preview_options, sender=self.rotate_offset_field_y))
        self.rotate_offset_field_z.valueChanged.connect(partial(self.update_preview_options, sender=self.rotate_offset_field_z))
        self.aim_vector_box.currentIndexChanged.connect(partial(self.update_preview_options, sender=self.aim_vector_box))
        self.up_vector_box.currentIndexChanged.connect(partial(self.update_preview_options, sender=self.up_vector_box))
        self.reverse_cb.stateChanged.connect(partial(self.update_preview_options, sender=self.reverse_cb))
        self.chain_cb.stateChanged.connect(partial(self.update_preview_options, sender=self.chain_cb))

        # Preview
        self.preview_cb.stateChanged.connect(self.toggle_preview)

        # Create
        self.create_button.clicked.connect(self.create_transform)

        # Initialize
        # Rearrange label width
        max_width = 0
        for label in [size_label, div_label, aim_label, up_label]:
            max_width = max(max_width, label.sizeHint().width())

        for label in [size_label, div_label, aim_label, up_label]:
            label.setFixedWidth(max_width)
            label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # Initialize by method
        self.switch_method(self.method_box.currentIndex())

    @staticmethod
    def aim_vector_data() -> dict:
        """Aim vector method list.

        Returns:
            dict: Aim vector label and method pairs.
        """
        return {"CurveTangent": "tangent", "NextPoint": "next_point", "PreviousPoint": "previous_point"}

    @staticmethod
    def up_vector_data() -> dict:
        """Up vector method list.

        Returns:
            dict: Up vector label and method pairs.
        """
        return {"SceneUp": "scene_up", "CurveNormal": "normal", "SurfaceNormal": "surface_normal"}

    @staticmethod
    def method_data() -> dict:
        """Return label and function pairs.

        Returns:
            dict: Label and function pairs.
        """
        return {
            "CVPositions": {"function": "cv_positions", "divisions": False},
            "EPPositions": {"function": "ep_positions", "divisions": False},
            "CVClosestPositions": {"function": "cv_closest_positions", "divisions": False},
            "ParameterPositions": {"function": "param_positions", "divisions": True},
            "LengthPositions": {"function": "length_positions", "divisions": True},
            "CloudPositions": {"function": "cloud_positions", "divisions": True},
        }

    def switch_method(self, index):
        """Switch enable or disable widgets by method.

        Args:
            index (int): Index of method box.
        """
        method_name = self.method_box.itemText(index)
        method_data = self.method_data()[method_name]

        self.divisions_field.setEnabled(method_data["divisions"])

    @maya_ui.undo_chunk("Transform Creater: Create")
    @maya_ui.error_handler
    def create_transform(self):
        """Create transform nodes."""
        # Get function name
        function_name = self.method_data()[self.method_box.currentText()]["function"]
        if not hasattr(create_transforms, function_name):
            raise ValueError(f"Invalid function name: {function_name}")

        # Default variables
        function = getattr(create_transforms, function_name)
        node_type = self.node_type_box.currentText()
        size = self.size_field.value()
        reverse = self.reverse_cb.isChecked()
        chain = self.chain_cb.isChecked()
        rotation_offset = [self.rotate_offset_field_x.value(), self.rotate_offset_field_y.value(), self.rotate_offset_field_z.value()]

        # Extra variables
        include_rotation = self.include_rotation_cb.isChecked()
        divisions = self.divisions_field.value()
        aim_vector_method = self.aim_vector_data()[self.aim_vector_box.currentText()]
        up_vector_method = self.up_vector_data()[self.up_vector_box.currentText()]

        # Create transform nodes
        make_transform = create_transforms.CreateTransforms(
            func=function, size=size, shape_type=node_type, chain=chain, reverse=reverse, rotation_offset=rotation_offset
        )

        result_nodes = make_transform.create(
            include_rotation=include_rotation, divisions=divisions, aim_vector_method=aim_vector_method, up_vector_method=up_vector_method
        )

        if result_nodes:
            cmds.select(result_nodes, r=True)

        logger.debug(f"Create transform nodes: {result_nodes}")

    @maya_ui.error_handler
    def toggle_preview(self, state):
        """Toggle preview result nodes."""
        if state == Qt.Checked:
            selection_job = cmds.scriptJob(event=["SelectionChanged", self.update_preview_locator], protected=True, compressUndo=True)
            self.script_job_ids.append(selection_job)

            self.update_preview_locator()

            logger.debug("Start preview mode.")
        else:
            self.end_preview()

    @maya_ui.without_undo
    @maya_ui.error_handler
    def update_preview_locator(self):
        """Update preview result nodes."""
        # Get function name
        function_name = self.method_data()[self.method_box.currentText()]["function"]
        if not hasattr(create_transforms, function_name):
            raise ValueError(f"Invalid function name: {function_name}")

        # Default variables
        function = getattr(create_transforms, function_name)
        node_type = self.node_type_box.currentText()
        size = self.size_field.value()
        reverse = self.reverse_cb.isChecked()
        chain = self.chain_cb.isChecked()
        rotation_offset = [self.rotate_offset_field_x.value(), self.rotate_offset_field_y.value(), self.rotate_offset_field_z.value()]

        # Extra variables
        divisions = self.divisions_field.value()
        include_rotation = self.include_rotation_cb.isChecked()
        aim_vector_method = self.aim_vector_data()[self.aim_vector_box.currentText()]
        up_vector_method = self.up_vector_data()[self.up_vector_box.currentText()]

        self.preview_locator = PreviewLocatorForTransformOnCurve(
            func=function, size=size, shape_type=node_type, chain=chain, reverse=reverse, rotation_offset=rotation_offset
        )

        self.preview_locator.preview(
            include_rotation=include_rotation, divisions=divisions, aim_vector_method=aim_vector_method, up_vector_method=up_vector_method
        )

        logger.debug("Update preview locator.")

    @maya_ui.without_undo
    @maya_ui.error_handler
    def update_preview_options(self, sender=None):
        """Update preview options."""
        if not self.preview_locator:
            logger.debug("Preview locator is not found.")
            return

        if sender is None:
            logger.debug("Sender is None.")
            return

        if sender == self.method_box:
            self.update_preview_locator()

        elif sender == self.node_type_box:
            self.preview_locator.change_shape_type(self.node_type_box.currentText())

        elif sender == self.size_field:
            self.preview_locator.change_size(self.size_field.value())

        elif sender == self.divisions_field or sender == self.include_rotation_cb:
            self.update_preview_locator()

        elif sender in [self.rotate_offset_field_x, self.rotate_offset_field_y, self.rotate_offset_field_z]:
            self.preview_locator.change_rotation_offset(
                [self.rotate_offset_field_x.value(), self.rotate_offset_field_y.value(), self.rotate_offset_field_z.value()]
            )
        elif sender == self.aim_vector_box or sender == self.up_vector_box:
            self.update_preview_locator()

        elif sender == self.reverse_cb:
            self.preview_locator.change_reverse(self.reverse_cb.isChecked())

        elif sender == self.chain_cb:
            self.preview_locator.change_chain(self.chain_cb.isChecked())

        logger.debug("Update preview options.")

    @maya_ui.without_undo
    @maya_ui.error_handler
    def end_preview(self):
        """Kill script jobs."""
        # Delete script jobs
        for job_id in self.script_job_ids:
            if cmds.scriptJob(exists=job_id):
                cmds.scriptJob(kill=job_id, force=True)

        self.script_job_ids.clear()

        # Delete preview locator
        if self.preview_locator is not None:
            self.preview_locator.delete()
            self.preview_locator = None

        logger.debug("End preview mode.")

    def closeEvent(self, event):
        """Close event."""
        # Save option settings
        self.tool_options.write("method", self.method_box.currentIndex())
        self.tool_options.write("node_type", self.node_type_box.currentIndex())
        self.tool_options.write("size", self.size_field.value())
        self.tool_options.write("divisions", self.divisions_field.value())
        self.tool_options.write("include_rotation", self.include_rotation_cb.isChecked())
        self.tool_options.write("rotate_offsetX", self.rotate_offset_field_x.value())
        self.tool_options.write("rotate_offsetY", self.rotate_offset_field_y.value())
        self.tool_options.write("rotate_offsetZ", self.rotate_offset_field_z.value())
        self.tool_options.write("aim_vector", self.aim_vector_box.currentIndex())
        self.tool_options.write("up_vector", self.up_vector_box.currentIndex())
        self.tool_options.write("reverse", self.reverse_cb.isChecked())
        self.tool_options.write("chain", self.chain_cb.isChecked())

        # End preview mode
        self.end_preview()

        super().closeEvent(event)


class PreviewLocatorForTransformOnCurve(create_transforms.PreviewLocatorForTransform):
    preview_locator_name = "createTransformOnCurvePreview"


def show_ui():
    """Show the main window."""
    window_name = f"{__name__}MainWindow"
    maya_qt.delete_widget(window_name)

    # Create the main window.
    main_window = MainWindow(parent=maya_qt.get_maya_pointer(), object_name=window_name, window_title="Transform Creator on Curve")
    main_window.show()
