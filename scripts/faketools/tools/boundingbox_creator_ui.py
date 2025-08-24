"""
Create a bounding box around the selected objects tool.
"""

from logging import getLogger

import maya.cmds as cmds

try:
    from PySide2.QtCore import Qt
    from PySide2.QtGui import QDoubleValidator, QIntValidator, QPalette
    from PySide2.QtWidgets import (
        QCheckBox,
        QComboBox,
        QGridLayout,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QPushButton,
        QStackedWidget,
        QVBoxLayout,
        QWidget,
    )
except ImportError:
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QDoubleValidator, QIntValidator, QPalette
    from PySide6.QtWidgets import (
        QCheckBox,
        QComboBox,
        QGridLayout,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QPushButton,
        QStackedWidget,
        QVBoxLayout,
        QWidget,
    )

from ..command import create_boundingbox
from ..lib_ui import base_window, maya_qt, maya_ui, optionvar
from ..lib_ui.widgets import extra_widgets

logger = getLogger(__name__)

tool_options = optionvar.ToolOptionSettings(__name__)


class BaseBoxWidget(QWidget):
    def __init__(self, parent=None):
        """Constructor."""
        super().__init__(parent=parent)

        self.main_layout = QVBoxLayout()

        spacing = base_window.get_spacing(self)
        self.main_layout.setSpacing(spacing * 0.5)

        margins = base_window.get_margins(self)
        self.main_layout.setContentsMargins(*[margin * 0.5 for margin in margins])

        self.setLayout(self.main_layout)

    def get_options(self) -> dict:
        """Get the options.

        Returns:
            dict: Options for the bounding box type.
        """
        return {}


class WorldBoxWidget(BaseBoxWidget):
    def __init__(self, parent=None):
        """Constructor."""
        super().__init__(parent=parent)

        label = QLabel("No options available.")
        self.main_layout.addWidget(label)


class MinimumBoxWidget(BaseBoxWidget):
    def __init__(self, parent=None):
        """Constructor."""
        super().__init__(parent=parent)

        label = QLabel("No options available.")
        self.main_layout.addWidget(label)


class AxisAlignedBoxWidget(BaseBoxWidget):
    _axis = ["x", "y", "z"]

    def __init__(self, parent=None):
        """Constructor."""
        super().__init__(parent=parent)

        layout = QGridLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        spacing = base_window.get_spacing(self)
        layout.setSpacing(spacing * 0.5)

        label = QLabel("Axis Direction:", alignment=Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(label, 0, 0)

        self.x_axis_direction = QLineEdit()
        self.x_axis_direction.setValidator(QDoubleValidator(0, 1, 2))
        layout.addWidget(self.x_axis_direction, 0, 1)

        self.y_axis_direction = QLineEdit()
        self.y_axis_direction.setValidator(QDoubleValidator(0, 1, 2))
        layout.addWidget(self.y_axis_direction, 0, 2)

        self.z_axis_direction = QLineEdit()
        self.z_axis_direction.setValidator(QDoubleValidator(0, 1, 2))
        layout.addWidget(self.z_axis_direction, 0, 3)

        label = QLabel("Axis:", alignment=Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(label, 1, 0)

        self.axis_box = QComboBox()
        self.axis_box.addItems(self._axis)
        layout.addWidget(self.axis_box, 1, 1, 1, 3)

        label = QLabel("Sampling:", alignment=Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(label, 2, 0)

        self.sampling = QLineEdit()
        self.sampling.setValidator(QIntValidator(0, 36000))
        layout.addWidget(self.sampling, 2, 1)

        self.main_layout.addLayout(layout)

        # Option settings
        self.set_axis_direction(tool_options.read("axis_direction", [0.0, 1.0, 0.0]))
        self.set_axis(tool_options.read("axis", "y"))
        self.set_sampling(tool_options.read("sampling", 360))

    def get_options(self) -> dict:
        """Get the options.

        Returns:
            dict: Options for the bounding box type.
        """
        return {"axis_direction": self.get_axis_direction(), "axis": self.axis_box.currentText(), "theta_samples": self.get_sampling()}

    def get_axis_direction(self) -> list[float]:
        """Get the axis direction.

        Returns:
            list[float]: Axis direction.
        """
        result_axis = []
        for axis in [self.x_axis_direction, self.y_axis_direction, self.z_axis_direction]:
            try:
                result_axis.append(float(axis.text()))
            except ValueError:
                result_axis.append(0.0)

        return result_axis

    def set_axis_direction(self, axis_direction: list[float]):
        """Set the axis direction.

        Args:
            axis_direction (list[float]): Axis direction.
        """
        if not axis_direction:
            raise ValueError("Axis direction is empty.")

        if len(axis_direction) != 3:
            raise ValueError("Axis direction must have 3 elements.")

        self.x_axis_direction.setText(str(axis_direction[0]))
        self.y_axis_direction.setText(str(axis_direction[1]))
        self.z_axis_direction.setText(str(axis_direction[2]))

    def set_axis(self, axis: str):
        """Set the axis.

        Args:
            axis (str): Axis.
        """
        if axis not in self._axis:
            raise ValueError(f"Invalid axis: {axis}")

        self.axis_box.setCurrentText(axis)

    def get_sampling(self) -> int:
        """Get the sampling.

        Returns:
            int: Sampling.
        """
        try:
            return int(self.sampling.text())
        except ValueError:
            return 0

    def set_sampling(self, sampling: int):
        """Set the sampling.

        Args:
            sampling (int): Sampling.
        """
        self.sampling.setText(str(sampling))

    def closeEvent(self, event):
        """Override the close event."""
        # Save the option settings.
        options = self.get_options()
        tool_options.write("axis_direction", options["axis_direction"])
        tool_options.write("axis", options["axis"])
        tool_options.write("sampling", options["theta_samples"])

        super().closeEvent(event)


class MainWindow(base_window.BaseMainWindow):
    _boundingbox_types = {"World": "world", "Minimum": "minimum", "AxisAligned": "axis_aligned"}
    _boundingbox_widgets = {"world": WorldBoxWidget, "minimum": MinimumBoxWidget, "axis_aligned": AxisAlignedBoxWidget}
    _box_types = ["mesh", "curve", "locator"]

    _default_axis_direction = [0, 1, 0]
    _default_axis = "y"

    def __init__(self, parent=None, object_name="MainWindow", window_title="Main Window"):
        """Constructor."""
        super().__init__(parent=parent, object_name=object_name, window_title=window_title)

        bounding_type_layout = QVBoxLayout()
        bounding_type_layout.setSpacing(0)

        self.bounding_type_box = QComboBox()
        self.bounding_type_box.addItems(self._boundingbox_types.keys())
        bounding_type_layout.addWidget(self.bounding_type_box)

        layout = QVBoxLayout()

        self.stock_widget = QStackedWidget()
        palette = self.stock_widget.palette()
        role = QPalette.Background if hasattr(QPalette, "Background") else QPalette.Window
        color = palette.color(role)
        color = color.lighter(115)
        self.stock_widget.setStyleSheet(f"QStackedWidget {{ background-color: {color.name()}; }}")

        for bounding_type in self._boundingbox_widgets:
            widget = self._boundingbox_widgets[bounding_type]()
            self.stock_widget.addWidget(widget)

        layout.addWidget(self.stock_widget)
        bounding_type_layout.addLayout(layout)
        self.central_layout.addLayout(bounding_type_layout)

        self.box_type_box = QComboBox()
        self.box_type_box.addItems(self._box_types)
        self.central_layout.addWidget(self.box_type_box)

        self.base_line_widget = BaseLineWidget()
        self.central_layout.addWidget(self.base_line_widget)

        self.include_scale_box = QCheckBox("Include Scale")
        self.central_layout.addWidget(self.include_scale_box)

        self.is_parent_box = QCheckBox("Parent")
        self.central_layout.addWidget(self.is_parent_box)

        separator = extra_widgets.HorizontalSeparator()
        self.central_layout.addWidget(separator)

        create_button = QPushButton("Create")
        self.central_layout.addWidget(create_button)

        # Option settings
        self.bounding_type_box.setCurrentText(tool_options.read("bounding_type", "World"))
        self.box_type_box.setCurrentText(tool_options.read("box_type", "mesh"))
        self.base_line_widget.set_base_line(tool_options.read("base_line", [0.0, 0.0, 0.0]))
        self.include_scale_box.setChecked(tool_options.read("include_scale", True))
        self.is_parent_box.setChecked(tool_options.read("is_parent", False))

        # Signal & Slot
        self.bounding_type_box.currentIndexChanged.connect(self.stock_widget.setCurrentIndex)
        create_button.clicked.connect(self.create_bounding_box)

        # Initialize the UI.
        self.stock_widget.setCurrentIndex(self.bounding_type_box.currentIndex())

        size_hint = self.sizeHint()
        self.resize(size_hint.width() * 0.5, size_hint.height())

    @maya_ui.undo_chunk("Create Bounding Box")
    @maya_ui.error_handler
    def create_bounding_box(self):
        """Create the bounding box."""
        bounding_type = self._boundingbox_types[self.bounding_type_box.currentText()]
        box_type = self.box_type_box.currentText()
        include_scale = self.include_scale_box.isChecked()
        is_parent = self.is_parent_box.isChecked()
        base_line = self.base_line_widget.get_base_line()

        kwargs = self.stock_widget.currentWidget().get_options()

        create_boundingbox.main(
            bounding_box_type=bounding_type, box_type=box_type, include_scale=include_scale, is_parent=is_parent, base_line=base_line, **kwargs
        )

    def closeEvent(self, event):
        """Override the close event."""
        # Save the option settings.
        tool_options.write("bounding_type", self.bounding_type_box.currentText())
        tool_options.write("box_type", self.box_type_box.currentText())
        tool_options.write("base_line", self.base_line_widget.get_base_line())
        tool_options.write("include_scale", self.include_scale_box.isChecked())
        tool_options.write("is_parent", self.is_parent_box.isChecked())

        super().closeEvent(event)


class BaseLineWidget(QWidget):
    def __init__(self, parent=None):
        """Constructor."""
        super().__init__(parent=parent)

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        spacing = base_window.get_spacing(self)
        layout.setSpacing(spacing * 0.5)

        label = QLabel("Base Line:", alignment=Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(label)

        self.x_base_line = QLineEdit()
        self.x_base_line.setValidator(QDoubleValidator(-1, 1, 2))
        layout.addWidget(self.x_base_line)

        self.y_base_line = QLineEdit()
        self.y_base_line.setValidator(QDoubleValidator(-1, 1, 2))
        layout.addWidget(self.y_base_line)

        self.z_base_line = QLineEdit()
        self.z_base_line.setValidator(QDoubleValidator(-1, 1, 2))
        layout.addWidget(self.z_base_line)

        self.setLayout(layout)

        # Signal & Slot
        self.x_base_line.textChanged.connect(self._on_text_changed)
        self.y_base_line.textChanged.connect(self._on_text_changed)
        self.z_base_line.textChanged.connect(self._on_text_changed)

        self.set_base_line([0.0, 1.0, 0.0])

    def get_base_line(self) -> list[float]:
        """Get the base line.

        Returns:
            list[float]: Base line.
        """
        return [float(self.x_base_line.text()), float(self.y_base_line.text()), float(self.z_base_line.text())]

    def set_base_line(self, base_line: list[float]):
        """Set the base line.

        Args:
            base_line (list[float]): Base line.
        """
        if not base_line:
            raise ValueError("Base line is empty.")

        if len(base_line) != 3:
            raise ValueError("Base line must have 3 elements.")

        self.x_base_line.setText(str(base_line[0]))
        self.y_base_line.setText(str(base_line[1]))
        self.z_base_line.setText(str(base_line[2]))

    def _on_text_changed(self, text):
        """Slot for the text changed signal."""
        try:
            value = float(text)
        except ValueError:
            value = 0.0

        if not (-1.0 <= value <= 1.0):
            cmds.warning("Base line must be in the range of -1.0 to 1.0.")

            value = max(min(value, 1.0), -1.0)
            self.sender().setText(str(value))


def show_ui():
    """Show the main window."""
    window_name = f"{__name__}MainWindow"
    maya_qt.delete_widget(window_name)

    # Create the main window.
    main_window = MainWindow(parent=maya_qt.get_maya_pointer(), object_name=window_name, window_title="BoundingBox Creator")
    main_window.show()
