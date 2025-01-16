"""
Create a curve from a surface tool.
"""

from logging import getLogger

import maya.cmds as cmds
from PySide2.QtCore import Qt
from PySide2.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QDoubleSpinBox,
    QGridLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QRadioButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from ..command import create_curveSurface
from ..lib import lib_component
from ..lib_ui import maya_qt, maya_ui, optionvar
from ..lib_ui.widgets import extra_widgets

logger = getLogger(__name__)


class MainWindow(QMainWindow):

    def __init__(self,
                 parent=None,
                 object_name='MainWindow',
                 window_title='Main Window'):
        """Constructor.
        """
        super().__init__(parent=parent)

        self.tool_options = optionvar.ToolOptionSettings(__name__)

        self.setObjectName(object_name)
        self.setWindowTitle(window_title)
        self.setAttribute(Qt.WA_DeleteOnClose)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.central_layout = QVBoxLayout()
        self.central_widget.setLayout(self.central_layout)

        # Menu
        self.menu = self.menuBar()
        self.__add_menu()

        layout = QGridLayout()

        # Main Options
        # Select Type
        label = QLabel('Select Type:', alignment=Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(label, 0, 0)

        sel_button = QRadioButton('Selected')
        layout.addWidget(sel_button, 0, 1)

        hierarchy_button = QRadioButton('Hierarchy')
        layout.addWidget(hierarchy_button, 0, 2)

        self.select_button_group = QButtonGroup()
        self.select_button_group.addButton(sel_button)
        self.select_button_group.addButton(hierarchy_button)

        # Object Type
        label = QLabel('Object Type:', alignment=Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(label, 1, 0)

        curve_button = QRadioButton('Curve')
        layout.addWidget(curve_button, 1, 1)

        surface_button = QRadioButton('Surface')
        layout.addWidget(surface_button, 1, 2)

        mesh_button = QRadioButton('Mesh')
        layout.addWidget(mesh_button, 1, 3)

        curve_button.setChecked(True)

        self.object_button_group = QButtonGroup()
        self.object_button_group.addButton(curve_button)
        self.object_button_group.addButton(surface_button)
        self.object_button_group.addButton(mesh_button)

        h_line = extra_widgets.HorizontalSeparator()
        layout.addWidget(h_line, 2, 0, 1, 4)

        # Curve Options

        # Degree
        label = QLabel('Degree:', alignment=Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(label, 3, 0)

        degree_1_button = QRadioButton('1')
        layout.addWidget(degree_1_button, 3, 1)

        degree_3_button = QRadioButton('3')
        layout.addWidget(degree_3_button, 3, 2)

        degree_1_button.setChecked(True)

        self.degree_button_group = QButtonGroup()
        self.degree_button_group.addButton(degree_1_button)
        self.degree_button_group.addButton(degree_3_button)

        # Center
        self.center_checkbox = QCheckBox('Center')
        layout.addWidget(self.center_checkbox, 4, 1)

        # Close
        self.close_checkbox = QCheckBox('Close')
        layout.addWidget(self.close_checkbox, 4, 2)

        self.reverse_checkbox = QCheckBox('Reverse')
        layout.addWidget(self.reverse_checkbox, 4, 3)

        # Divisions
        label = QLabel('Divisions:', alignment=Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(label, 7, 0)

        self.divisions_spin_box = QSpinBox()
        self.divisions_spin_box.setRange(0, 100)
        self.divisions_spin_box.setValue(0)
        layout.addWidget(self.divisions_spin_box, 7, 1)

        # Skip
        label = QLabel('Skip:', alignment=Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(label, 8, 0)

        self.skip_spin_box = QSpinBox()
        self.skip_spin_box.setRange(0, 100)
        self.skip_spin_box.setValue(0)
        layout.addWidget(self.skip_spin_box, 8, 1)

        self.central_layout.addLayout(layout)

        h_line = extra_widgets.HorizontalSeparator()
        layout.addWidget(h_line, 9, 0, 1, 4)

        # Surface Options

        # Axis
        self.surface_axis_label = QLabel('Axis:', alignment=Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(self.surface_axis_label, 10, 0)

        x_button = QRadioButton('X')
        layout.addWidget(x_button, 10, 1)

        y_button = QRadioButton('Y')
        layout.addWidget(y_button, 10, 2)

        z_button = QRadioButton('Z')
        layout.addWidget(z_button, 10, 3)

        normal_button = QRadioButton('Normal')
        layout.addWidget(normal_button, 11, 1)

        binormal_button = QRadioButton('Binormal')
        layout.addWidget(binormal_button, 11, 2)

        x_button.setChecked(True)

        self.surface_axis_button_group = QButtonGroup()
        self.surface_axis_button_group.addButton(x_button)
        self.surface_axis_button_group.addButton(y_button)
        self.surface_axis_button_group.addButton(z_button)
        self.surface_axis_button_group.addButton(normal_button)
        self.surface_axis_button_group.addButton(binormal_button)

        # Width
        self.surface_width_label = QLabel('Width:', alignment=Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(self.surface_width_label, 12, 0)

        self.surface_width_spin_box = QDoubleSpinBox()
        self.surface_width_spin_box.setRange(0.00, 100.0)
        self.surface_width_spin_box.setSingleStep(0.5)
        layout.addWidget(self.surface_width_spin_box, 12, 1)

        # Width Center
        self.surface_width_center_label = QLabel('Width Center:', alignment=Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(self.surface_width_center_label, 13, 0)

        self.surface_width_center_spin_box = QDoubleSpinBox()
        self.surface_width_center_spin_box.setRange(0.0, 1.0)
        self.surface_width_center_spin_box.setSingleStep(0.5)
        layout.addWidget(self.surface_width_center_spin_box, 13, 1)

        h_line = extra_widgets.HorizontalSeparator()
        layout.addWidget(h_line, 14, 0, 1, 4)

        # Bind Options

        # Is Bind
        label = QLabel('Is Bind:', alignment=Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(label, 15, 0)

        self.is_bind_checkbox = QCheckBox()
        layout.addWidget(self.is_bind_checkbox, 15, 1)

        # Bind method
        self.bind_method_label = QLabel('Bind Method:', alignment=Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(self.bind_method_label, 16, 0)

        linear_button = QRadioButton('Linear')
        layout.addWidget(linear_button, 16, 1)

        ease_button = QRadioButton('Ease')
        layout.addWidget(ease_button, 16, 2)

        step_button = QRadioButton('Step')
        layout.addWidget(step_button, 16, 3)

        linear_button.setChecked(True)

        self.bind_method_button_group = QButtonGroup()
        self.bind_method_button_group.addButton(linear_button)
        self.bind_method_button_group.addButton(ease_button)
        self.bind_method_button_group.addButton(step_button)

        # Smooth level
        self.smooth_level_label = QLabel('Smooth Levels:', alignment=Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(self.smooth_level_label, 17, 0)

        self.smooth_level_spin_box = QSpinBox()
        self.smooth_level_spin_box.setRange(0, 100)
        layout.addWidget(self.smooth_level_spin_box, 17, 1)

        # To skin cage
        self.to_skin_cage_label = QLabel('To Skin Cage:', alignment=Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(self.to_skin_cage_label, 18, 0)

        self.to_skin_cage_checkbox = QCheckBox()
        layout.addWidget(self.to_skin_cage_checkbox, 18, 1)

        self.to_skin_cage_div_label = QLabel('Division Levels:', alignment=Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(self.to_skin_cage_div_label, 19, 0)

        self.to_skin_cage_spinBox = QSpinBox()
        self.to_skin_cage_spinBox.setRange(1, 100)
        layout.addWidget(self.to_skin_cage_spinBox, 19, 1)

        h_line = extra_widgets.HorizontalSeparator()
        layout.addWidget(h_line, 20, 0, 1, 4)

        create_button = QPushButton('Create')
        layout.addWidget(create_button, 21, 0, 1, 4)

        self.central_layout.addLayout(layout)

        # Option settings
        self.select_button_group.buttons()[0].setChecked(self.tool_options.read('selected', True))
        self.select_button_group.buttons()[1].setChecked(self.tool_options.read('hierarchy', False))
        self.object_button_group.buttons()[0].setChecked(self.tool_options.read('nurbsCurve', True))
        self.object_button_group.buttons()[1].setChecked(self.tool_options.read('nurbsSurface', False))
        self.object_button_group.buttons()[2].setChecked(self.tool_options.read('mesh', False))
        self.degree_button_group.buttons()[0].setChecked(self.tool_options.read('degree1', False))
        self.degree_button_group.buttons()[1].setChecked(self.tool_options.read('degree3', True))
        self.center_checkbox.setChecked(self.tool_options.read('center', False))
        self.close_checkbox.setChecked(self.tool_options.read('close', False))
        self.reverse_checkbox.setChecked(self.tool_options.read('reverse', False))
        self.divisions_spin_box.setValue(self.tool_options.read('divisions', 0))
        self.skip_spin_box.setValue(self.tool_options.read('skip', 0))
        self.surface_axis_button_group.buttons()[0].setChecked(self.tool_options.read('x', True))
        self.surface_axis_button_group.buttons()[1].setChecked(self.tool_options.read('y', False))
        self.surface_axis_button_group.buttons()[2].setChecked(self.tool_options.read('z', False))
        self.surface_axis_button_group.buttons()[3].setChecked(self.tool_options.read('normal', False))
        self.surface_axis_button_group.buttons()[4].setChecked(self.tool_options.read('binormal', False))
        self.surface_width_spin_box.setValue(self.tool_options.read('surface_width', 1.0))
        self.surface_width_center_spin_box.setValue(self.tool_options.read('surface_width_center', 0.5))
        self.is_bind_checkbox.setChecked(self.tool_options.read('is_bind', False))
        self.bind_method_button_group.buttons()[0].setChecked(self.tool_options.read('linear', True))
        self.bind_method_button_group.buttons()[1].setChecked(self.tool_options.read('ease', False))
        self.bind_method_button_group.buttons()[2].setChecked(self.tool_options.read('step', False))
        self.smooth_level_spin_box.setValue(self.tool_options.read('smooth_levels', 0))
        self.to_skin_cage_checkbox.setChecked(self.tool_options.read('to_skin_cage', False))
        self.to_skin_cage_spinBox.setValue(self.tool_options.read('skin_cage_division_levels', 1))

        # Signal & Slot
        self.is_bind_checkbox.stateChanged.connect(self.__change_bind_mode)
        self.object_button_group.buttonClicked.connect(self.__change_surface_mode)
        self.to_skin_cage_checkbox.stateChanged.connect(self.to_skin_cage_div_label.setEnabled)
        self.to_skin_cage_checkbox.stateChanged.connect(self.to_skin_cage_spinBox.setEnabled)

        create_button.clicked.connect(self.create_curve_surface)

        self.__change_bind_mode()
        self.__change_surface_mode()

    def __add_menu(self):
        """Add the menu.
        """
        menu = self.menu.addMenu('Edit')

        action = menu.addAction('Move CVs Position')
        action.triggered.connect(self.move_cvs_position)

        action = menu.addAction('Create Curve to Vertices')
        action.triggered.connect(self.create_curve_to_vertices)

    def __change_bind_mode(self):
        """Change the bind method.
        """
        is_bind = self.is_bind_checkbox.isChecked()

        self.bind_method_label.setEnabled(is_bind)
        self.bind_method_button_group.setExclusive(not is_bind)
        self.bind_method_button_group.buttons()[0].setEnabled(is_bind)
        self.bind_method_button_group.buttons()[1].setEnabled(is_bind)
        self.bind_method_button_group.buttons()[2].setEnabled(is_bind)
        self.bind_method_button_group.setExclusive(is_bind)

        self.smooth_level_label.setEnabled(is_bind)
        self.smooth_level_spin_box.setEnabled(is_bind)

        is_surface = self.object_button_group.buttons()[1].isChecked()
        self.to_skin_cage_label.setEnabled(is_bind and is_surface)
        self.to_skin_cage_checkbox.setEnabled(is_bind and is_surface)

        is_to_skin_cage = self.to_skin_cage_checkbox.isChecked()
        self.to_skin_cage_div_label.setEnabled(is_bind and is_surface and is_to_skin_cage)
        self.to_skin_cage_spinBox.setEnabled(is_bind and is_surface and is_to_skin_cage)

    def __change_surface_mode(self):
        """Change the surface mode.
        """
        is_curve = self.object_button_group.buttons()[0].isChecked()

        self.surface_axis_label.setEnabled(not is_curve)
        self.surface_axis_button_group.setExclusive(is_curve)
        self.surface_axis_button_group.buttons()[0].setEnabled(not is_curve)
        self.surface_axis_button_group.buttons()[1].setEnabled(not is_curve)
        self.surface_axis_button_group.buttons()[2].setEnabled(not is_curve)
        self.surface_axis_button_group.buttons()[3].setEnabled(not is_curve)
        self.surface_axis_button_group.buttons()[4].setEnabled(not is_curve)
        self.surface_axis_button_group.setExclusive(not is_curve)

        self.surface_width_label.setEnabled(not is_curve)
        self.surface_width_spin_box.setEnabled(not is_curve)
        self.surface_width_label.setEnabled(not is_curve)
        self.surface_width_center_spin_box.setEnabled(not is_curve)
        self.surface_width_center_label.setEnabled(not is_curve)

        is_surface = self.object_button_group.buttons()[1].isChecked()
        is_bind = self.is_bind_checkbox.isChecked()
        self.to_skin_cage_label.setEnabled(is_surface and is_bind)
        self.to_skin_cage_checkbox.setEnabled(is_surface and is_bind)

        is_to_skin_cage = self.to_skin_cage_checkbox.isChecked()
        self.to_skin_cage_div_label.setEnabled(is_surface and is_bind and is_to_skin_cage)
        self.to_skin_cage_spinBox.setEnabled(is_surface and is_bind and is_to_skin_cage)

    @maya_ui.undo_chunk('Create Curve Surface')
    @maya_ui.error_handler
    def create_curve_surface(self):
        """Create a curve surface.
        """
        # Get the options.
        # Basic Options
        select_type = 'selected' if self.select_button_group.buttons()[0].isChecked() else 'hierarchy'

        object_type = 'nurbsCurve'
        if self.object_button_group.buttons()[1].isChecked():
            object_type = 'nurbsSurface'
        elif self.object_button_group.buttons()[2].isChecked():
            object_type = 'mesh'

        is_bind = self.is_bind_checkbox.isChecked()
        to_skin_cage = self.to_skin_cage_checkbox.isChecked()
        skin_cage_levels = self.to_skin_cage_spinBox.value()

        # Select Options
        skip = self.skip_spin_box.value()
        reverse = self.reverse_checkbox.isChecked()

        select_options = {'skip': skip, 'reverse': reverse}

        # Curve Options
        degree = 1 if self.degree_button_group.buttons()[0].isChecked() else 3
        center = self.center_checkbox.isChecked()
        close = self.close_checkbox.isChecked()
        divisions = self.divisions_spin_box.value()
        surface_width = self.surface_width_spin_box.value()
        surface_width_center = self.surface_width_center_spin_box.value()

        if surface_width == 0.0:
            surface_width = 1e-3

        surface_axis = 'x'
        if self.surface_axis_button_group.buttons()[1].isChecked():
            surface_axis = 'y'
        elif self.surface_axis_button_group.buttons()[2].isChecked():
            surface_axis = 'z'
        elif self.surface_axis_button_group.buttons()[3].isChecked():
            surface_axis = 'normal'
        elif self.surface_axis_button_group.buttons()[4].isChecked():
            surface_axis = 'binormal'

        create_options = {'degree': degree, 'center': center, 'close': close, 'divisions': divisions,
                          'surface_width': surface_width, 'surface_width_center': surface_width_center, 'surface_axis': surface_axis}

        # Bind Options
        method = 'linear'
        if self.bind_method_button_group.buttons()[1].isChecked():
            method = 'ease'
        elif self.bind_method_button_group.buttons()[2].isChecked():
            method = 'step'

        smooth_levels = self.smooth_level_spin_box.value()

        bind_options = {'method': method, 'smooth_iterations': smooth_levels}

        # Create the curve surface
        result_objs = create_curveSurface.main(select_type=select_type,
                                               object_type=object_type,
                                               is_bind=is_bind,
                                               to_skin_cage=to_skin_cage,
                                               skin_cage_division_levels=skin_cage_levels,
                                               select_options=select_options,
                                               create_options=create_options,
                                               bind_options=bind_options)

        cmds.select(result_objs, r=True)

    @maya_ui.undo_chunk('Move CVs Position')
    @maya_ui.error_handler
    def move_cvs_position(self):
        """Move the CVs position.
        """
        cvs = cmds.filterExpand(sm=28, ex=True)
        if not cvs:
            cmds.error('Select nurbsCurve CVs.')
            return

        for cv in cvs:
            create_curveSurface.move_cv_positions(cv)

    @maya_ui.undo_chunk('Create Curve to Vertices')
    @maya_ui.error_handler
    def create_curve_to_vertices(self):
        """Create a curve to vertices.
        """
        vertices = cmds.filterExpand(sm=31, ex=True)
        if not vertices:
            cmds.error('Select vertices.')
            return

        comp_filter = lib_component.ComponentFilter(vertices)

        result_curves = []
        for mesh, components in comp_filter.get_components(component_type=['vertex']).items():
            curve = create_curveSurface.create_curve_from_vertices(components)
            result_curves.append(curve)

            logger.debug(f'Created curve: {mesh} --> {curve}')

        cmds.select(result_curves, r=True)

    def closeEvent(self, event):
        """Close event.
        """
        # Save option settings
        self.tool_options.write('selected', self.select_button_group.buttons()[0].isChecked())
        self.tool_options.write('hierarchy', self.select_button_group.buttons()[1].isChecked())
        self.tool_options.write('nurbsCurve', self.object_button_group.buttons()[0].isChecked())
        self.tool_options.write('nurbsSurface', self.object_button_group.buttons()[1].isChecked())
        self.tool_options.write('mesh', self.object_button_group.buttons()[2].isChecked())
        self.tool_options.write('degree1', self.degree_button_group.buttons()[0].isChecked())
        self.tool_options.write('degree3', self.degree_button_group.buttons()[1].isChecked())
        self.tool_options.write('center', self.center_checkbox.isChecked())
        self.tool_options.write('close', self.close_checkbox.isChecked())
        self.tool_options.write('reverse', self.reverse_checkbox.isChecked())
        self.tool_options.write('divisions', self.divisions_spin_box.value())
        self.tool_options.write('skip', self.skip_spin_box.value())
        self.tool_options.write('x', self.surface_axis_button_group.buttons()[0].isChecked())
        self.tool_options.write('y', self.surface_axis_button_group.buttons()[1].isChecked())
        self.tool_options.write('z', self.surface_axis_button_group.buttons()[2].isChecked())
        self.tool_options.write('normal', self.surface_axis_button_group.buttons()[3].isChecked())
        self.tool_options.write('binormal', self.surface_axis_button_group.buttons()[4].isChecked())
        self.tool_options.write('surface_width', self.surface_width_spin_box.value())
        self.tool_options.write('surface_width_center', self.surface_width_center_spin_box.value())
        self.tool_options.write('is_bind', self.is_bind_checkbox.isChecked())
        self.tool_options.write('linear', self.bind_method_button_group.buttons()[0].isChecked())
        self.tool_options.write('ease', self.bind_method_button_group.buttons()[1].isChecked())
        self.tool_options.write('step', self.bind_method_button_group.buttons()[2].isChecked())
        self.tool_options.write('smooth_levels', self.smooth_level_spin_box.value())
        self.tool_options.write('to_skin_cage', self.to_skin_cage_checkbox.isChecked())
        self.tool_options.write('skin_cage_division_levels', self.to_skin_cage_spinBox.value())

        super().closeEvent(event)


def show_ui():
    """Show the main window.
    """
    window_name = f'{__name__}MainWindow'
    maya_qt.delete_widget(window_name)

    # Create the main window.
    main_window = MainWindow(parent=maya_qt.get_maya_pointer(),
                             object_name=window_name,
                             window_title='Curve Surface Creator')
    main_window.show()
    main_window.setFixedSize(main_window.sizeHint())
