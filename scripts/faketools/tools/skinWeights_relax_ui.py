"""
Copy weights relax tool.
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
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QPushButton,
        QSizePolicy,
        QSlider,
        QSpacerItem,
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
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QPushButton,
        QSizePolicy,
        QSlider,
        QSpacerItem,
        QStackedWidget,
        QVBoxLayout,
        QWidget,
    )

from ..command import relax_weight
from ..lib import lib_skinCluster
from ..lib_ui import base_window, maya_qt, maya_ui, optionvar
from ..lib_ui.widgets import extra_widgets

logger = getLogger(__name__)

tool_options = optionvar.ToolOptionSettings(__name__)


class SkinWeightsWidgets(QWidget):
    """Base class for skin weights widgets.

    This is the base class for widgets used in SkinWeightsRelaxWidgets.
    """

    def __init__(self, parent=None):
        """Constructor."""
        super().__init__(parent=parent)

        self.main_layout = QVBoxLayout()
        spacing = base_window.get_spacing(self)
        self.main_layout.setSpacing(spacing * 0.75)

        margins = base_window.get_margins(self)
        self.main_layout.setContentsMargins(*[margin * 0.5 for margin in margins])

        self.setLayout(self.main_layout)

    def get_options(self):
        """Get the skin weight options."""
        return {}


class LaplacianSkinWeightsWidgets(SkinWeightsWidgets):
    """Laplacian Skin Weights Widgets."""

    def __init__(self, parent=None):
        """Constructor."""
        super().__init__(parent=parent)

        label = QLabel("No options available.")

        self.main_layout.addWidget(label)

        spacer = QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.main_layout.addItem(spacer)


class RBFSkinWeightsWidgets(SkinWeightsWidgets):
    """RBF Skin Weights Widgets."""

    def __init__(self, parent=None):
        """Constructor."""
        super().__init__(parent=parent)

        # RBF Weight Method
        layout = QHBoxLayout()

        label = QLabel("Weight Method:", alignment=Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(label)

        self.method_box = QComboBox()
        self.method_box.addItems(self.weight_function_map().keys())
        layout.addWidget(self.method_box, stretch=1)

        self.main_layout.addLayout(layout)

        separator = extra_widgets.HorizontalSeparator()
        self.main_layout.addWidget(separator)

        # Method Options
        option_stack_widget = QStackedWidget()
        self.main_layout.addWidget(option_stack_widget)

        # Gaussian
        gaussian_widget = QWidget()
        gaussian_layout = QVBoxLayout()

        layout = QHBoxLayout()

        label = QLabel("Sigma:")
        layout.addWidget(label)

        self.sigma_field = QLineEdit("1.0")
        self.sigma_field.setValidator(QDoubleValidator(0.0, 100.0, 2))
        self.sigma_field.setFixedWidth(self.sigma_field.sizeHint().width() / 2)
        self.sigma_field.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        layout.addWidget(self.sigma_field)

        spacer = QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addItem(spacer)

        gaussian_layout.addLayout(layout)

        gaussian_widget.setLayout(gaussian_layout)

        option_stack_widget.addWidget(gaussian_widget)

        # Linear
        linear_widget = QWidget()
        linear_layout = QVBoxLayout()

        label = QLabel("No options available.")
        linear_layout.addWidget(label)

        linear_widget.setLayout(linear_layout)

        option_stack_widget.addWidget(linear_widget)

        # Inverse Distance
        inverse_distance_widget = QWidget()
        inverse_distance_layout = QVBoxLayout()

        layout = QHBoxLayout()

        label = QLabel("Power:")
        layout.addWidget(label)

        self.power_field = QLineEdit("2.0")
        self.power_field.setValidator(QDoubleValidator(0.0, 100.0, 2))
        self.power_field.setFixedWidth(self.power_field.sizeHint().width() / 2)
        self.power_field.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        layout.addWidget(self.power_field)

        spacer = QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addItem(spacer)

        inverse_distance_layout.addLayout(layout)

        inverse_distance_widget.setLayout(inverse_distance_layout)

        option_stack_widget.addWidget(inverse_distance_widget)

        # Option settings
        self.method_box.setCurrentIndex(tool_options.read("rbf_method", 0))
        option_stack_widget.setCurrentIndex(self.method_box.currentIndex())
        self.sigma_field.setText(tool_options.read("rbf_sigma", "1.0"))
        self.power_field.setText(tool_options.read("rbf_power", "2.0"))

        # Signal & Slot
        self.method_box.currentIndexChanged.connect(option_stack_widget.setCurrentIndex)

        self.main_layout.addLayout(layout)

    @staticmethod
    def weight_function_map():
        """Get the weight function map."""
        return {
            "Gaussian": "gaussian",
            "Linear": "linear",
            "Inverse Distance": "inverse_distance",
        }

    def get_options(self):
        """Get the weight function options."""
        method = self.method_box.currentText()

        options = {}
        if method == "Gaussian":
            options["sigma"] = float(self.sigma_field.text())
        elif method == "Inverse Distance":
            options["power"] = float(self.power_field.text())

        return {
            "weight_type": self.weight_function_map()[method],
            "options": options,
        }

    def closeEvent(self, event):
        """Close event."""
        # Save the option settings
        tool_options.write("rbf_method", self.method_box.currentIndex())
        tool_options.write("rbf_sigma", self.sigma_field.text())
        tool_options.write("rbf_power", self.power_field.text())

        super().closeEvent(event)


class BiharmonicSkinWeightsWidgets(SkinWeightsWidgets):
    """Biharmonic Skin Weights Widgets."""

    def __init__(self, parent=None):
        """Constructor."""
        super().__init__(parent=parent)

        layout = QHBoxLayout()

        label = QLabel("First Order Weight:", alignment=Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(label)

        self.first_order_field = QLineEdit("0.75")
        self.first_order_field.setValidator(QDoubleValidator(0.0, 1.0, 2))
        self.first_order_field.setFixedWidth(self.first_order_field.sizeHint().width() / 2)
        self.first_order_field.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        layout.addWidget(self.first_order_field)

        self.first_order_slider = QSlider(Qt.Horizontal)
        self.first_order_slider.setRange(0, 100)
        self.first_order_slider.setValue(75)
        layout.addWidget(self.first_order_slider)

        self.main_layout.addLayout(layout)

        spacer = QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.main_layout.addItem(spacer)

        # Option settings
        self.first_order_field.setText(tool_options.read("first_order_weight", "0.75"))
        self.first_order_slider.setValue(float(self.first_order_field.text()) * 100)

        # Signal & Slot
        self.first_order_field.textChanged.connect(self._update_field_slider_value)
        self.first_order_slider.valueChanged.connect(self._update_field_slider_value)

    def _update_field_slider_value(self):
        """Update the field and slider value."""
        sender = self.sender()

        if sender == self.first_order_field:
            value = float(self.first_order_field.text())
            self.first_order_slider.setValue(value * 100)
        elif sender == self.first_order_slider:
            value = self.first_order_slider.value() / 100
            self.first_order_field.setText(str(value))

    def get_options(self):
        """Get the biharmonic weight options."""
        return {
            "first_order_weight": float(self.first_order_field.text()),
            "second_order_weight": 1.0 - float(self.first_order_field.text()),
        }

    def closeEvent(self, event):
        """Close event."""
        # Save the option settings
        tool_options.write("first_order_weight", self.first_order_field.text())

        super().closeEvent(event)


class RelaxSkinWeightsWidgets(SkinWeightsWidgets):
    """Relax Skin Weights Widgets."""

    def __init__(self, parent=None):
        """Constructor."""
        super().__init__(parent=parent)

        layout = QHBoxLayout()

        label = QLabel("Relaxation Factor:", alignment=Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(label)

        self.relaxation_factor_field = QLineEdit("0.5")
        self.relaxation_factor_field.setValidator(QDoubleValidator(0.0, 1.0, 2))
        self.relaxation_factor_field.setFixedWidth(self.relaxation_factor_field.sizeHint().width() / 2)
        self.relaxation_factor_field.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        layout.addWidget(self.relaxation_factor_field)

        self.relaxation_factor_slider = QSlider(Qt.Horizontal)
        self.relaxation_factor_slider.setRange(0, 100)
        self.relaxation_factor_slider.setValue(50)
        layout.addWidget(self.relaxation_factor_slider)

        self.main_layout.addLayout(layout)

        spacer = QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.main_layout.addItem(spacer)

        # Option settings
        self.relaxation_factor_field.setText(tool_options.read("relaxation_factor", "0.5"))
        self.relaxation_factor_slider.setValue(float(self.relaxation_factor_field.text()) * 100)

        # Signal & Slot
        self.relaxation_factor_field.textChanged.connect(self._update_field_slider_value)
        self.relaxation_factor_slider.valueChanged.connect(self._update_field_slider_value)

    def _update_field_slider_value(self):
        """Update the field and slider value."""
        sender = self.sender()

        if sender == self.relaxation_factor_field:
            value = float(self.relaxation_factor_field.text())
            self.relaxation_factor_slider.setValue(value * 100)

        elif sender == self.relaxation_factor_slider:
            value = self.relaxation_factor_slider.value() / 100
            self.relaxation_factor_field.setText(str(value))

    def get_options(self):
        """Get the relax weight options."""
        return {
            "relaxation_factor": float(self.relaxation_factor_field.text()),
        }

    def closeEvent(self, event):
        """Close event."""
        # Save the option settings
        tool_options.write("relaxation_factor", self.relaxation_factor_field.text())

        super().closeEvent(event)


class MainWindow(base_window.BaseMainWindow):
    """Skin Weights Relax main window.

    This class is the main widget for relaxing weights.
    It switches between widgets corresponding to each relax method and performs the weight relaxation process.

    The widgets to switch must inherit from SkinWeightsWidgets.
    """

    method_data = {
        "Laplacian": {"command": relax_weight.LaplacianSkinWeights, "widget": LaplacianSkinWeightsWidgets},
        "RBF": {"command": relax_weight.RBFSkinWeights, "widget": RBFSkinWeightsWidgets},
        "Biharmonic": {"command": relax_weight.BiharmonicSkinWeights, "widget": BiharmonicSkinWeightsWidgets},
        "Relax": {"command": relax_weight.RelaxSkinWeights, "widget": RelaxSkinWeightsWidgets},
    }

    def __init__(self, parent=None, object_name="MainWindow", window_title="Main Window"):
        """Constructor."""
        super().__init__(parent=parent, object_name=object_name, window_title=window_title)

        method_layout = QVBoxLayout()
        method_layout.setSpacing(0)
        method_layout.setContentsMargins(0, 0, 0, 0)

        # Method
        self.method_box = QComboBox()
        self.method_box.addItems(self.method_data.keys())
        method_layout.addWidget(self.method_box, stretch=1)

        option_group = QGroupBox()
        method_layout.addWidget(option_group)

        # Stack widget
        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        self.method_stack_widget = QStackedWidget()

        palette = self.method_stack_widget.palette()
        role = QPalette.Background if hasattr(QPalette, "Background") else QPalette.Window
        color = palette.color(role)
        color = color.lighter(115)
        self.method_stack_widget.setStyleSheet(f"QStackedWidget {{ background-color: {color.name()}; }}")

        # Add widgets to the stack
        for data in self.method_data.values():
            widget_cls = data["widget"]
            if not issubclass(widget_cls, SkinWeightsWidgets):
                raise TypeError(f"Widget class must inherit from SkinWeightsWidgets: {widget_cls}")
            widget = widget_cls()
            self.method_stack_widget.addWidget(widget)

        layout.addWidget(self.method_stack_widget)
        option_group.setLayout(layout)

        self.central_layout.addLayout(method_layout)

        # Options
        layout = QGridLayout()

        label = QLabel("Iterations:", alignment=Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(label, 0, 0)

        self.iterations_field = QLineEdit("1")
        self.iterations_field.setValidator(QIntValidator(0, 50))
        self.iterations_field.setFixedWidth(self.iterations_field.sizeHint().width() / 2)
        self.iterations_field.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        layout.addWidget(self.iterations_field, 0, 1)

        self.iterations_slider = QSlider(Qt.Horizontal)
        self.iterations_slider.setRange(0, 50)
        self.iterations_slider.setValue(1)
        layout.addWidget(self.iterations_slider, 0, 2)

        label = QLabel("After Blend:", alignment=Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(label, 1, 0)

        self.after_blend_field = QLineEdit("1.0")
        self.after_blend_field.setValidator(QDoubleValidator(0.0, 1.0, 2))
        self.after_blend_field.setFixedWidth(self.after_blend_field.sizeHint().width() / 2)
        self.after_blend_field.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        layout.addWidget(self.after_blend_field, 1, 1)

        self.after_blend_slider = QSlider(Qt.Horizontal)
        self.after_blend_slider.setRange(0, 100)
        self.after_blend_slider.setValue(100)
        layout.addWidget(self.after_blend_slider, 1, 2)

        self.central_layout.addLayout(layout)

        self.only_unlock_inf_checkBox = QCheckBox("Use Only Unlocked Influences")
        self.central_layout.addWidget(self.only_unlock_inf_checkBox)

        separator = extra_widgets.HorizontalSeparator()
        self.central_layout.addWidget(separator)

        execute_button = QPushButton("Relax Skin Weights")
        self.central_layout.addWidget(execute_button)

        # Option settings
        self.method_box.setCurrentIndex(tool_options.read("method", 0))
        self.iterations_field.setText(tool_options.read("iterations", "1"))
        self.iterations_slider.setValue(int(self.iterations_field.text()))
        self.after_blend_field.setText(tool_options.read("after_blend", "1.0"))
        self.after_blend_slider.setValue(int(float(self.after_blend_field.text()) * 100))

        # Signal & Slot
        self.method_box.currentIndexChanged.connect(self.method_stack_widget.setCurrentIndex)
        self.iterations_field.textChanged.connect(self._update_field_slider_value)
        self.iterations_slider.valueChanged.connect(self._update_field_slider_value)
        self.after_blend_field.textChanged.connect(self._update_field_slider_value)
        self.after_blend_slider.valueChanged.connect(self._update_field_slider_value)

        execute_button.clicked.connect(self.relax_weights)

    def _update_field_slider_value(self):
        """Update the field and slider value."""
        sender = self.sender()

        if sender == self.iterations_field:
            value = int(self.iterations_field.text())
            self.iterations_slider.setValue(value)
        elif sender == self.iterations_slider:
            value = self.iterations_slider.value()
            self.iterations_field.setText(str(value))

        if sender == self.after_blend_field:
            value = float(self.after_blend_field.text())
            self.after_blend_slider.setValue(value * 100)
        elif sender == self.after_blend_slider:
            value = self.after_blend_slider.value() / 100
            self.after_blend_field.setText(str(value))

    @maya_ui.undo_chunk("Relax Skin Weights")
    @maya_ui.error_handler
    def relax_weights(self):
        """Relax the skin weights."""
        vertices = cmds.filterExpand(selectionMask=31)
        if not vertices:
            cmds.error("No vertices selected")

        shapes = list(set(cmds.ls(vertices, objectsOnly=True)))
        if len(shapes) > 1:
            cmds.error("Vertices must belong to the same object")

        skinCluster = lib_skinCluster.get_skinCluster(shapes[0])
        if not skinCluster:
            cmds.error(f"Object is not bound to a skinCluster: {shapes[0]}")

        method = self.method_box.currentText()
        smooth_skin_weights = self.method_data[method]["command"]
        options = self.method_stack_widget.currentWidget().get_options()

        logger.debug(f"Smooth method: {method}")
        logger.debug(f"Smooth options: {options}")

        iterations = int(self.iterations_field.text())
        after_blend = float(self.after_blend_field.text())
        only_unlock_inf = self.only_unlock_inf_checkBox.isChecked()

        logger.debug(f"UI options: {iterations}, {after_blend}, {only_unlock_inf}")

        smooth_skin_weights(skinCluster, vertices).smooth(
            iterations=iterations, blend_weights=after_blend, only_unlock_influences=only_unlock_inf, **options
        )

        logger.debug(f"Smoothed skin weights: {vertices}")

    def closeEvent(self, event):
        """Close event."""
        # Save the option settings
        tool_options.write("method", self.method_box.currentIndex())
        tool_options.write("iterations", self.iterations_field.text())
        tool_options.write("after_blend", self.after_blend_field.text())
        tool_options.write("only_unlock_inf", self.only_unlock_inf_checkBox.isChecked())

        super().closeEvent(event)


def show_ui():
    """Show the main window."""
    window_name = f"{__name__}MainWindow"
    maya_qt.delete_widget(window_name)

    # Create the main window.
    main_window = MainWindow(parent=maya_qt.get_maya_pointer(), object_name=window_name, window_title="SkinWeights Relax")
    main_window.show()
