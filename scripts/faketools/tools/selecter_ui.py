"""
Maya scene selection tools.
"""

import re

from maya.app.general.mayaMixin import MayaQWidgetDockableMixin
import maya.cmds as cmds

try:
    from PySide2.QtCore import Qt
    from PySide2.QtGui import QColor
    from PySide2.QtWidgets import (
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QPushButton,
        QSizePolicy,
        QSpacerItem,
        QVBoxLayout,
        QWidget,
    )
except ImportError:
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QColor
    from PySide6.QtWidgets import (
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QPushButton,
        QSizePolicy,
        QSpacerItem,
        QVBoxLayout,
        QWidget,
    )

from .. import user_directory
from ..command import duplicate_node, rename_node, rigging_setup
from ..lib import lib_name, lib_selection, lib_transform
from ..lib_ui import base_window, maya_qt, maya_ui, optionvar
from ..lib_ui.widgets import extra_widgets

tool_options = optionvar.ToolOptionSettings(__name__)

global_settings = user_directory.ToolSettings(__name__).load()
LEFT_TO_RIGHT = global_settings.get("LEFT_TO_RIGHT", ["(.*)(L)", r"\g<1>R"])
RIGHT_TO_LEFT = global_settings.get("RIGHT_TO_LEFT", ["(.*)(R)", r"\g<1>L"])

FILTER_COLOR = global_settings.get("FILTER_COLOR", "#6D7B8D")
HIERARCHY_COLOR = global_settings.get("HIERARCHY_COLOR", "#4C516D")
SUBSTITUTION_COLOR = global_settings.get("SUBSTITUTION_COLOR", "#6E7F80")
RENAME_COLOR = global_settings.get("RENAME_COLOR", "#536878")
BUTTON_SIZE = global_settings.get("BUTTON_SIZE", 32)
FONT_SIZE = global_settings.get("FONT_SIZE", 12)


def selecter_handler(func):
    """Selection handler for selecter tools.

    Args:
        func (function): Function to decorate.

    Returns:
        function: Decorated function.
    """

    def wrap(**kwargs):
        sel_nodes = cmds.ls(sl=True)
        if not sel_nodes:
            cmds.error("No object selected.")
            return

        result_nodes = func(nodes=sel_nodes, **kwargs)
        mod_keys = maya_ui.get_modifiers()

        if not mod_keys:
            cmds.select(result_nodes, r=True)
        elif mod_keys == ["Shift", "Ctrl"] or "Shift" in mod_keys:
            cmds.select(sel_nodes, r=True)
            cmds.select(result_nodes, add=True)
        elif "Ctrl" in mod_keys:
            cmds.select(sel_nodes, r=True)
            cmds.select(result_nodes, d=True)

    return wrap


class DockableWidget(MayaQWidgetDockableMixin, QWidget):
    def __init__(self, parent=None, object_name="dockableWidget", window_title="Dockable Widget"):
        super().__init__(parent=parent)

        self.setObjectName(object_name)
        self.setWindowTitle(window_title)
        self.setAttribute(Qt.WA_DeleteOnClose)

        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(10, 1, 1, 1)

        filter_selection_widget = FilterSelectionWidget()
        main_layout.addWidget(filter_selection_widget)

        separator = extra_widgets.VerticalSeparator()
        main_layout.addWidget(separator)

        hierarchical_selection_widget = HierarchicalSelectionWidget()
        main_layout.addWidget(hierarchical_selection_widget)

        separator = extra_widgets.VerticalSeparator()
        main_layout.addWidget(separator)

        substitution_selection_widget = SubstitutionSelectionWidget()
        main_layout.addWidget(substitution_selection_widget)

        separator = extra_widgets.VerticalSeparator()
        main_layout.addWidget(separator)

        rename_selection_widget = RenameSelectionWidget()
        main_layout.addWidget(rename_selection_widget)

        separator = extra_widgets.VerticalSeparator()
        main_layout.addWidget(separator)

        extra_selection_widget = ExtraSelectionWidget()
        main_layout.addWidget(extra_selection_widget)

        spacer = QSpacerItem(20, 40, QSizePolicy.Expanding, QSizePolicy.Expanding)
        main_layout.addItem(spacer)

        self.setLayout(main_layout)


class FilterSelectionWidget(QWidget):
    def __init__(self, parent=None):
        """Constructor."""
        super().__init__(parent=parent)

        main_layout = QHBoxLayout()
        main_layout.setSpacing(base_window.get_spacing(self, "horizontal") * 0.5)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Filter selection
        self.filter_name_field = QLineEdit()
        self.filter_name_field.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        main_layout.addWidget(self.filter_name_field)

        self.filter_name_ignorecase_cb = extra_widgets.TextCheckBoxButton(
            text="Aa", width=BUTTON_SIZE, height=BUTTON_SIZE, font_size=FONT_SIZE, parent=self
        )
        main_layout.addWidget(self.filter_name_ignorecase_cb)

        filter_name_button = SelecterButton("NAM", color=FILTER_COLOR)
        main_layout.addWidget(filter_name_button)

        self.filter_type_field = QLineEdit()
        self.filter_type_field.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        main_layout.addWidget(self.filter_type_field)

        filter_type_button = SelecterButton("TYP", color=FILTER_COLOR)
        main_layout.addWidget(filter_type_button)

        self.setLayout(main_layout)

        # Option settings
        self.filter_name_field.setText(tool_options.read("filter_name_field", ""))
        self.filter_name_ignorecase_cb.setChecked(tool_options.read("filter_name_ignorecase", False))
        self.filter_type_field.setText(tool_options.read("filter_type_field", "shape"))

        # Signal & Slot
        filter_name_button.clicked.connect(self.select_by_name)
        filter_type_button.clicked.connect(self.select_by_type)

    @maya_ui.undo_chunk("Selecter: Filter Name")
    @maya_ui.error_handler
    @selecter_handler
    def select_by_name(self, nodes: list[str]):
        """Select by name."""
        # Save option settings
        self.save_tool_options()

        # Select by name
        filter_name = self.filter_name_field.text()
        if not filter_name:
            cmds.error("No filter name specified.")

        # If only alphanumeric characters, convert to .*filter_name.*
        if re.match(r"^[a-zA-Z0-9]+$", filter_name):
            filter_name = f".*{filter_name}.*"

        ignorecase = self.filter_name_ignorecase_cb.isChecked()

        node_filter = lib_selection.NodeFilter(nodes)
        result_nodes = node_filter.by_regex(filter_name, ignorecase=ignorecase)

        if not result_nodes:
            cmds.warning("No matching nodes found.")
            return nodes

        return result_nodes

    @maya_ui.undo_chunk("Selecter: Filter Type")
    @maya_ui.error_handler
    @selecter_handler
    def select_by_type(self, nodes: list[str]):
        """Select by type."""
        # Save option settings
        self.save_tool_options()

        # Select by type
        filter_type = self.filter_type_field.text()
        if not filter_type:
            cmds.error("No filter type specified.")

        node_filter = lib_selection.NodeFilter(nodes)
        result_nodes = node_filter.by_type(filter_type)

        if not result_nodes:
            cmds.warning("No matching nodes found.")
            return nodes

        return result_nodes

    def save_tool_options(self):
        """Save the tool option settings."""
        tool_options.write("filter_name_field", self.filter_name_field.text())
        tool_options.write("filter_name_ignorecase", self.filter_name_ignorecase_cb.isChecked())
        tool_options.write("filter_type_field", self.filter_type_field.text())


class HierarchicalSelectionWidget(QWidget):
    def __init__(self, parent=None):
        """Constructor."""
        super().__init__(parent=parent)

        main_layout = QHBoxLayout()
        main_layout.setSpacing(base_window.get_spacing(self, "horizontal") * 0.5)
        main_layout.setContentsMargins(0, 0, 0, 0)

        parent_button = SelecterButton("PAR", color=HIERARCHY_COLOR)
        main_layout.addWidget(parent_button)

        children_button = SelecterButton("CHI", color=HIERARCHY_COLOR)
        main_layout.addWidget(children_button)

        siblings_button = SelecterButton("SIB", color=HIERARCHY_COLOR)
        main_layout.addWidget(siblings_button)

        children_all_button = SelecterButton("ALL", color=HIERARCHY_COLOR)
        main_layout.addWidget(children_all_button)

        children_bottom_button = SelecterButton("BTM", color=HIERARCHY_COLOR)
        main_layout.addWidget(children_bottom_button)

        hierarchy_all_button = SelecterButton("HIE", color=HIERARCHY_COLOR)
        main_layout.addWidget(hierarchy_all_button)

        self.setLayout(main_layout)

        # Signal & Slot
        parent_button.clicked.connect(self.parent_selection)
        children_button.clicked.connect(self.children_selection)
        siblings_button.clicked.connect(self.siblings_selection)
        children_all_button.clicked.connect(self.children_all_transform_selection)
        children_bottom_button.clicked.connect(self.children_bottom_selection)
        hierarchy_all_button.clicked.connect(self.hierarchy_all_selection)

    @maya_ui.undo_chunk("Selecter: Parent Selection")
    @maya_ui.error_handler
    @selecter_handler
    def parent_selection(self, nodes: list[str]):
        """Select the parent node."""
        node_hierarchy = lib_selection.DagHierarchy(nodes)
        result_nodes = node_hierarchy.get_parent()

        if not result_nodes:
            cmds.warning("No parent node found.")
            return nodes

        return result_nodes

    @maya_ui.undo_chunk("Selecter: Children Selection")
    @maya_ui.error_handler
    @selecter_handler
    def children_selection(self, nodes: list[str]):
        """Select the children nodes."""
        node_hierarchy = lib_selection.DagHierarchy(nodes)
        result_nodes = node_hierarchy.get_children()

        if not result_nodes:
            cmds.warning("No children nodes found.")
            return nodes

        return result_nodes

    @maya_ui.undo_chunk("Selecter: Siblings Selection")
    @maya_ui.error_handler
    @selecter_handler
    def siblings_selection(self, nodes: list[str]):
        """Select the siblings nodes."""
        node_hierarchy = lib_selection.DagHierarchy(nodes)
        result_nodes = node_hierarchy.get_siblings()

        if not result_nodes:
            cmds.warning("No sibling nodes found.")
            return nodes

        return result_nodes

    @maya_ui.undo_chunk("Selecter: Children Transform All Selection")
    @maya_ui.error_handler
    @selecter_handler
    def children_all_transform_selection(self, nodes: list[str]):
        """Select the children nodes."""
        node_hierarchy = lib_selection.DagHierarchy(nodes)
        result_nodes = node_hierarchy.get_hierarchy(include_shape=False)

        if not result_nodes:
            cmds.warning("No children nodes found.")
            return nodes

        return result_nodes

    @maya_ui.undo_chunk("Selecter: Children Bottom Selection")
    @maya_ui.error_handler
    @selecter_handler
    def children_bottom_selection(self, nodes: list[str]):
        """Select the children nodes."""
        node_hierarchy = lib_selection.DagHierarchy(nodes)
        result_nodes = node_hierarchy.get_children_bottoms()

        if not result_nodes:
            cmds.warning("No children nodes found.")
            return nodes

        return result_nodes

    @maya_ui.undo_chunk("Selecter: Hierarchy All Selection")
    @maya_ui.error_handler
    @selecter_handler
    def hierarchy_all_selection(self, nodes: list[str]):
        """Select the hierarchy nodes."""
        node_hierarchy = lib_selection.DagHierarchy(nodes)
        result_nodes = node_hierarchy.get_hierarchy(include_shape=True)

        if not result_nodes:
            cmds.warning("No children nodes found.")
            return nodes

        return result_nodes


class SubstitutionSelectionWidget(QWidget):
    def __init__(self, parent=None):
        """Constructor."""
        super().__init__(parent=parent)

        main_layout = QHBoxLayout()
        main_layout.setSpacing(base_window.get_spacing(self, "horizontal") * 0.5)
        main_layout.setContentsMargins(0, 0, 0, 0)

        left_to_right_button = SelecterButton("LR", color=SUBSTITUTION_COLOR)
        main_layout.addWidget(left_to_right_button)

        right_to_left_button = SelecterButton("RL", color=SUBSTITUTION_COLOR)
        main_layout.addWidget(right_to_left_button)

        self.search_text_field = QLineEdit()
        self.search_text_field.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        main_layout.addWidget(self.search_text_field)

        self.arrow_button = extra_widgets.CheckBoxButton(icon_on="arrow-left", icon_off="arrow-right")
        main_layout.addWidget(self.arrow_button)

        self.replace_text_field = QLineEdit()
        self.replace_text_field.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        main_layout.addWidget(self.replace_text_field)

        select_button = SelecterButton("SEL", color=SUBSTITUTION_COLOR)
        main_layout.addWidget(select_button)

        rename_button = SelecterButton("REN", color=SUBSTITUTION_COLOR)
        main_layout.addWidget(rename_button)

        mirror_button = SelecterButton("MIR", color=SUBSTITUTION_COLOR)
        main_layout.addWidget(mirror_button)

        separator = extra_widgets.VerticalSeparator()
        main_layout.addWidget(separator)

        duplicate_button = SelecterButton("DUP", color=SUBSTITUTION_COLOR)
        main_layout.addWidget(duplicate_button)

        self.mirror_checkbox = extra_widgets.TextCheckBoxButton(text="MIR", width=BUTTON_SIZE, height=BUTTON_SIZE, font_size=FONT_SIZE, parent=self)
        main_layout.addWidget(self.mirror_checkbox)

        layout = QVBoxLayout()
        layout.setSpacing(2)
        layout.setContentsMargins(0, 0, 0, 0)

        self.mirror_pos_checkbox = extra_widgets.TextCheckBoxButton(
            text="POS", width=BUTTON_SIZE, height=BUTTON_SIZE // 2 - 1, font_size=FONT_SIZE // 1.5, parent=self
        )
        self.mirror_pos_checkbox.setChecked(True)
        layout.addWidget(self.mirror_pos_checkbox)

        self.mirror_rot_checkbox = extra_widgets.TextCheckBoxButton(
            text="ROT", width=BUTTON_SIZE, height=BUTTON_SIZE // 2 - 1, font_size=FONT_SIZE // 1.5, parent=self
        )
        layout.addWidget(self.mirror_rot_checkbox)

        main_layout.addLayout(layout)

        self.freeze_checkbox = extra_widgets.TextCheckBoxButton(text="FRZ", width=BUTTON_SIZE, height=BUTTON_SIZE, font_size=FONT_SIZE, parent=self)
        self.freeze_checkbox.setChecked(True)
        main_layout.addWidget(self.freeze_checkbox)

        separator = extra_widgets.VerticalSeparator()
        main_layout.addWidget(separator)

        duplicate_orig_button = SelecterButton("ORG", color=SUBSTITUTION_COLOR)
        main_layout.addWidget(duplicate_orig_button)

        self.setLayout(main_layout)

        # Option settings
        self.search_text_field.setText(tool_options.read("sub_left_field", "L"))
        self.replace_text_field.setText(tool_options.read("sub_right_field", "R"))

        # Signal & Slot
        left_to_right_button.clicked.connect(self.select_left_to_right)
        right_to_left_button.clicked.connect(self.select_right_to_left)
        select_button.clicked.connect(self.select_substitution)
        rename_button.clicked.connect(self.rename_substitution)
        mirror_button.clicked.connect(self.mirror_position)
        duplicate_button.clicked.connect(self.duplicate_substitution)
        duplicate_orig_button.clicked.connect(self.duplicate_original_substitution)

    @maya_ui.undo_chunk("Selecter: Select Left to Right")
    @maya_ui.error_handler
    @selecter_handler
    def select_left_to_right(self, nodes: list[str]):
        """Select the left to right nodes."""
        nodes = [node.split("|")[-1] for node in nodes]
        convert_names = lib_name.substitute_names(nodes, LEFT_TO_RIGHT[0], LEFT_TO_RIGHT[1])

        result_nodes = []
        for name, node in zip(convert_names, nodes, strict=False):
            if not cmds.objExists(name):
                cmds.warning(f"Node does not exist: {node}")
                continue

            if name == node:
                cmds.warning(f"Failed to name substitution: {node}")
                continue

            if name not in result_nodes:
                result_nodes.append(name)

        if not result_nodes:
            cmds.warning("No matching nodes found.")
            return nodes

        return result_nodes

    @maya_ui.undo_chunk("Selecter: Select Right to Left")
    @maya_ui.error_handler
    @selecter_handler
    def select_right_to_left(self, nodes: list[str]):
        """Select the right to left nodes."""
        nodes = [node.split("|")[-1] for node in nodes]
        convert_names = lib_name.substitute_names(nodes, RIGHT_TO_LEFT[0], RIGHT_TO_LEFT[1])

        result_nodes = []
        for name, node in zip(convert_names, nodes, strict=False):
            if not cmds.objExists(name):
                cmds.warning(f"Node does not exist: {node}")
                continue

            if name == node:
                cmds.warning(f"Failed to name substitute: {node}")
                continue

            if name not in result_nodes:
                result_nodes.append(name)

        if not result_nodes:
            cmds.warning("No matching nodes found.")
            return nodes

        return result_nodes

    @maya_ui.undo_chunk("Selecter: Select Substitution")
    @maya_ui.error_handler
    @selecter_handler
    def select_substitution(self, nodes: list[str]):
        """Select the substitution nodes."""
        search_text, replace_text = self._get_substitution_option()

        nodes = [node.split("|")[-1] for node in nodes]
        convert_names = lib_name.substitute_names(nodes, search_text, replace_text)

        result_nodes = []
        for name, node in zip(convert_names, nodes, strict=False):
            if not cmds.objExists(name):
                cmds.warning(f"Node does not exist: {node}")
                continue

            if name == node:
                cmds.warning(f"Failed to name substitute: {node}")
                continue

            if name not in result_nodes:
                result_nodes.append(name)

        # Save tool options
        self.save_tool_options()

        if not result_nodes:
            cmds.warning("No matching nodes found.")
            return nodes

        return result_nodes

    @maya_ui.undo_chunk("Selecter: Rename Substitution")
    @maya_ui.error_handler
    def rename_substitution(self):
        """Rename the substitution nodes."""
        search_text, replace_text = self._get_substitution_option()

        nodes = cmds.ls(sl=True, fl=True)
        if not nodes:
            cmds.error("No object selected.")

        result_nodes = rename_node.substitute_rename(nodes, search_text, replace_text)

        cmds.select(result_nodes, r=True)

    @maya_ui.undo_chunk("Selecter: Mirror Position")
    @maya_ui.error_handler
    def mirror_position(self):
        """Mirror the position of the substitution nodes."""
        nodes = cmds.ls(sl=True, type="transform")
        if not nodes:
            cmds.error("No object selected.")

        mirror_pos = self.mirror_pos_checkbox.isChecked()
        mirror_rot = self.mirror_rot_checkbox.isChecked()
        search_text, replace_text = self._get_substitution_option()

        nodes = [node.split("|")[-1] for node in nodes]
        convert_names = lib_name.substitute_names(nodes, search_text, replace_text)

        result_nodes = []
        for name, node in zip(convert_names, nodes, strict=False):
            if not cmds.objExists(name):
                cmds.warning(f"Node does not exist: {node}")
                continue

            if name == node:
                cmds.warning(f"Failed to name substitute: {node}")
                continue

            rigging_setup.mirror_dag_node(node, name, mirror_position=mirror_pos, mirror_rotation=mirror_rot)

            result_nodes.append(name)

        # Save tool options
        self.save_tool_options()

        cmds.select(result_nodes, r=True)

    @maya_ui.undo_chunk("Selecter: Duplicate Substitution")
    @maya_ui.error_handler
    def duplicate_substitution(self):
        """Duplicate the substitution nodes."""
        search_text, replace_text = self._get_substitution_option()

        mirror = self.mirror_checkbox.isChecked()
        mirror_pos = self.mirror_pos_checkbox.isChecked()
        mirror_rot = self.mirror_rot_checkbox.isChecked()
        freeze = self.freeze_checkbox.isChecked()

        nodes = cmds.ls(sl=True, fl=True)
        if not nodes:
            cmds.error("No object selected.")

        result_nodes = duplicate_node.substitute_duplicate(nodes, search_text, replace_text)
        if not result_nodes:
            return

        if all(["dagNode" in cmds.nodeType(node, inherited=True) for node in result_nodes]):
            result_top_nodes = lib_selection.DagHierarchy(result_nodes).get_hierarchy_tops()
            if mirror:
                for node in result_top_nodes:
                    rigging_setup.mirror_dag_node(node, node, mirror_position=mirror_pos, mirror_rotation=mirror_rot)
                    if freeze:
                        lib_transform.FreezeTransformNode(node).freeze()

            cmds.select(result_top_nodes, r=True)
        else:
            cmds.select(result_nodes, r=True)

    @maya_ui.undo_chunk("Selecter: Duplicate Original Substitution")
    @maya_ui.error_handler
    def duplicate_original_substitution(self):
        """Duplicate the original substitution nodes."""
        search_text, replace_text = self._get_substitution_option()

        nodes = cmds.ls(sl=True, fl=True)
        if not nodes:
            cmds.error("No object selected.")

        result_nodes = duplicate_node.substitute_duplicate_original(nodes, search_text, replace_text)

        cmds.select(result_nodes, r=True)

    def _get_substitution_option(self):
        """Get the substitution option.

        Returns:
            tuple: The search and replace text.
        """
        search_text = self.search_text_field.text()
        replace_text = self.replace_text_field.text()

        if self.arrow_button.isChecked():
            search_text, replace_text = replace_text, search_text

        if not search_text:
            cmds.error("No search text specified.")

        return search_text, replace_text

    def save_tool_options(self):
        """Save the tool option settings."""
        tool_options.write("sub_left_field", self.search_text_field.text())
        tool_options.write("sub_right_field", self.replace_text_field.text())


class RenameSelectionWidget(QWidget):
    def __init__(self, parent=None):
        """Constructor."""
        super().__init__(parent=parent)

        main_layout = QHBoxLayout()
        main_layout.setSpacing(base_window.get_spacing(self, "horizontal") * 0.5)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.name_field = QLineEdit()
        self.name_field.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        main_layout.addWidget(self.name_field)

        rename_button = SelecterButton("REN", color=RENAME_COLOR)
        main_layout.addWidget(rename_button)

        label = QLabel("@ : ")
        main_layout.addWidget(label)

        self.start_alpha_field = QLineEdit("A")
        self.start_alpha_field.setMaximumWidth(32)
        self.start_alpha_field.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        main_layout.addWidget(self.start_alpha_field)

        label = QLabel("# : ")
        main_layout.addWidget(label)

        self.start_number_field = QLineEdit("1")
        self.start_number_field.setMaximumWidth(32)
        self.start_number_field.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        main_layout.addWidget(self.start_number_field)

        self.setLayout(main_layout)

        # Option settings
        self.name_field.setText(tool_options.read("rename_name_field", ""))
        self.start_alpha_field.setText(tool_options.read("rename_start_alpha_field", "A"))
        self.start_number_field.setText(tool_options.read("rename_start_number_field", "1"))

        # Signal & Slot
        rename_button.clicked.connect(self.rename_nodes)

    @maya_ui.undo_chunk("Selecter: Rename")
    @maya_ui.error_handler
    def rename_nodes(self):
        """Rename the nodes."""
        new_name = self.name_field.text()
        if not new_name:
            cmds.error("No new name specified.")

        start_alpha = self.start_alpha_field.text()
        start_number = self.start_number_field.text()

        nodes = cmds.ls(sl=True, fl=True)
        if not nodes:
            cmds.error("No object selected.")

        nodes = rename_node.solve_rename(nodes, new_name, start_alpha=start_alpha, start_number=start_number)

        cmds.select(nodes, r=True)

        # Save tool options
        self.save_tool_options()

    def save_tool_options(self):
        """Save the tool option settings."""
        tool_options.write("rename_name_field", self.name_field.text())
        tool_options.write("rename_start_alpha_field", self.start_alpha_field.text())
        tool_options.write("rename_start_number_field", self.start_number_field.text())


class ExtraSelectionWidget(QWidget):
    def __init__(self, parent=None):
        """Constructor."""
        super().__init__(parent=parent)

        main_layout = QHBoxLayout()
        main_layout.setSpacing(base_window.get_spacing(self, "horizontal") * 0.5)
        main_layout.setContentsMargins(0, 0, 0, 0)

        last_to_first_button = SelecterButton("L2F")
        main_layout.addWidget(last_to_first_button)

        self.setLayout(main_layout)

        # Signal & Slot
        last_to_first_button.clicked.connect(self.last_to_first_selection)

    @maya_ui.undo_chunk("Selecter: Last to First Selection")
    def last_to_first_selection(self):
        """Select the last object in the selection list."""
        nodes = cmds.ls(sl=True, fl=True)
        if not nodes:
            cmds.error("No object selected.")

        if len(nodes) == 1:
            cmds.error("Only one object selected.")

        cmds.select(nodes[-1], r=True)
        cmds.select(nodes[:-1], add=True)


class SelecterButton(QPushButton):
    """Select button widget."""

    def __init__(self, text: str, color: str = "#333", parent=None):
        """Constructor.

        Args:
            text (str): The button text.
            color (str): The button color.
            parent (QWidget): Parent widget.
        """
        super().__init__(text, parent=parent)
        self.setFixedSize(BUTTON_SIZE, BUTTON_SIZE)
        color = QColor(color)
        hover_color = self._get_lightness_color(color, 1.2)
        pressed_color = self._get_lightness_color(color, 0.8)
        self.setStyleSheet(f"""
                   QPushButton {{
                       font-weight: bold;
                       font-size: {FONT_SIZE}px;
                       border: 1px solid #333;
                       background-color: {color.name()};
                   }}
                   QPushButton:hover {{
                       background-color: {hover_color};
                   }}
                    QPushButton:pressed {{
                       background-color: {pressed_color};
                   }}
                   """)

    def _get_lightness_color(self, color: QColor, factor: float) -> str:
        """Adjust the brightness of a color for hover and pressed states.

        Args:
            color (QColor): The color to adjust.
            factor (float): The brightness factor.

        Returns:
            str: The adjusted color in hex format.
        """
        h, s, v, a = color.getHsv()
        v = max(0, min(v * factor, 255))
        adjusted_color = QColor.fromHsv(h, s, v, a)
        return adjusted_color.name()


def show_ui():
    """Show the main window then dock it."""
    # Delete the window
    window_name = f"{__name__}MainWindow"
    maya_qt.delete_widget(window_name)

    # Delete the workspace control
    workspace_control_name = f"{__name__}MainWindowWorkspaceControl"

    if cmds.workspaceControl(workspace_control_name, exists=True):
        cmds.workspaceControl(workspace_control_name, e=True, close=True)
        cmds.deleteUI(workspace_control_name)

    # Create the main window.
    main_window = DockableWidget(parent=maya_qt.get_maya_pointer(), object_name=window_name, window_title="Selecter")

    main_window.show(dockable=True)

    # Edit actLikeMayaUIElement
    cmds.workspaceControl(workspace_control_name, e=True, dockToControl=("Shelf", "bottom"), tabToControl=("Shelf", -1))
    cmds.workspaceControl(workspace_control_name, e=True, actLikeMayaUIElement=True)
