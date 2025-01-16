"""
Node Stocker Tool.
"""

import importlib
from logging import getLogger

import maya.cmds as cmds
from PySide2.QtCore import Qt, Signal
from PySide2.QtGui import QIcon
from PySide2.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QRadioButton,
    QSizePolicy,
    QSpacerItem,
    QStyle,
    QVBoxLayout,
    QWidget,
)

from .. import user_directory
from ..command import node_storage
from ..lib import lib_name
from ..lib_ui import maya_qt, maya_ui, optionvar, tool_icons
from ..lib_ui.widgets import extra_widgets, nodeStock_view

logger = getLogger(__name__)

importlib.reload(nodeStock_view)
importlib.reload(node_storage)


class MainWindow(QMainWindow):

    _stock_file_name = 'node'

    def __init__(self,
                 parent=None,
                 object_name='MainWindow',
                 window_title='Main Window',
                 num_areas=7,
                 *args, **kwargs):
        """Constructor.

        Args:
            parent (QWidget): The parent widget.
            object_name (str): The object name.
            window_title (str): The window title.
            num_areas (int): The number of areas.

        Keyword Args:
            rows (int): The number of button rows.
            cols (int): The number of button columns.
            button_size (int): The size of the buttons.
        """
        super().__init__(parent=parent)

        rows = kwargs.get('rows', 2)
        cols = kwargs.get('cols', 7)
        button_size = kwargs.get('button_size', 50)

        tool_directory = user_directory.ToolDirectory(__name__)
        self.node_storage = node_storage.NodeStorage(tool_directory.get_directory())
        self.tool_options = optionvar.ToolOptionSettings(__name__)

        self._current_scene_data = {}
        self._hilite_nodes = []
        self._hilite_selected_nodes = []

        self.setObjectName(object_name)
        self.setWindowTitle(window_title)
        self.setAttribute(Qt.WA_DeleteOnClose)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.central_layout = QVBoxLayout()
        self.central_widget.setLayout(self.central_layout)

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # Stock area switch buttons
        self.switch_buttons = StockAreaSwitchButtons(num_buttons=num_areas)
        self.switch_buttons.set_index(0)
        layout.addWidget(self.switch_buttons)

        # Tool bar
        self.tool_bar = ToolBar()
        layout.addWidget(self.tool_bar)

        self.central_layout.addLayout(layout)

        # Stock area
        self.scenes = [nodeStock_view.NodeStockGraphicsScene() for _ in range(num_areas)]
        self.view = nodeStock_view.NodeStockGraphicsView(self.scenes[0], self)
        self.central_layout.addWidget(self.view, stretch=1)

        self.__create_button_grid(rows=rows, cols=cols, button_size=button_size, spacing=5)
        self.__load_scene_data(0)

        separator = extra_widgets.HorizontalSeparator()
        self.central_layout.addWidget(separator)

        # Options
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        self.name_space_box = NameSpaceBox()
        layout.addWidget(self.name_space_box)

        self.name_replace_field = NameReplaceField()
        layout.addWidget(self.name_replace_field)

        self.central_layout.addLayout(layout)

        separator = extra_widgets.HorizontalSeparator()
        self.central_layout.addWidget(separator)

        # Status bar
        layout = QHBoxLayout()

        self.status_bar = self.statusBar()
        self.status_bar.setStyleSheet('QStatusBar::item { border: none; }')
        self.status_bar.setSizeGripEnabled(False)
        layout.addWidget(self.status_bar)

        self.node_length_label = QLabel('{}   '.format(self.__get_node_length_label(0)))
        self.node_length_label.setFixedWidth(self.node_length_label.sizeHint().width())
        self.status_separator = extra_widgets.VerticalSeparator()
        self.node_names_label = QLabel()

        self.status_bar.addWidget(self.node_length_label)
        self.status_bar.addWidget(self.status_separator)
        self.status_bar.addWidget(self.node_names_label)

        self.central_layout.addLayout(layout)

        # Option settings
        self.tool_bar.set_hilite(self.tool_options.read('hilite', False))
        self.name_space_box.set_enabled(self.tool_options.read('name_space_enabled', False))
        self.name_replace_field.set_enabled(self.tool_options.read('name_replace_enabled', False))
        self.name_replace_field.set_search_replace_text(*self.tool_options.read('search_replace', ('', '')))
        self.name_replace_field.set_switched(self.tool_options.read('name_replace_switched', False))
        self.name_replace_field.set_re(self.tool_options.read('name_replace_re', False))

        # Signals & Slots
        self.switch_buttons.button_selection_changed.connect(self.__switch_scene)
        self.tool_bar.refresh_button_clicked.connect(self.__refresh_window)
        self.view.rubber_band_selection.connect(self._select_nodes_rubber_band)

        # For updating the status bar
        style = self.status_bar.style()
        margin = style.pixelMetric(QStyle.PM_LayoutLeftMargin, None, self.status_bar)
        padding = style.pixelMetric(QStyle.PM_LayoutHorizontalSpacing, None, self.status_bar)
        self.font_metrics = self.node_names_label.fontMetrics()
        self.status_bar_spacing = self.node_length_label.width() + self.status_separator.width() + margin + padding

        # For resize view
        self.resize(self.minimumSize())

    def __switch_scene(self, index: int) -> None:
        """Switch the scene in the graphic widget.

        Args:
            index (int): The index of the scene.
        """
        if 0 <= index < len(self.scenes):
            self.view.setScene(self.scenes[index])
            self.view.setAlignment(Qt.AlignCenter)
            self.__load_scene_data(index)

    def __create_button_grid(self, rows, cols, button_size, spacing) -> None:
        """Create a grid of buttons in each scene.

        Args:
            rows (int): The number of rows.
            cols (int): The number of columns.
            button_size (int): The size of the buttons.
            spacing (int): The spacing between buttons.
        """
        margin = spacing
        offset = spacing / 2

        for scene in self.scenes:
            total_width = cols * (button_size + spacing) - spacing + margin * 2
            total_height = rows * (button_size + spacing) - spacing + margin * 2
            scene.setSceneRect(0, 0, total_width, total_height)

            for row in range(rows):
                for col in range(cols):
                    x = margin + col * (button_size + spacing) + offset
                    y = margin + row * (button_size + spacing)
                    button = nodeStock_view.NodeStockButton(f'{row}_{col}', x, y, button_size, label=str(row * cols + col))
                    button.left_button_clicked.connect(self._select_nodes)
                    button.middle_button_clicked.connect(self._add_nodes)
                    button.right_button_clicked.connect(self._remove_nodes)
                    button.hovered.connect(self.__update_status_bar)
                    button.unhovered.connect(self.__clear_status_bar)
                    button.hovered.connect(self.__highlight_nodes)
                    button.unhovered.connect(self.__unhighlight_nodes)
                    scene.addItem(button)

            self.view.setSceneRect(scene.sceneRect())

        logger.debug(f"Created button grid: {rows}x{cols}")

    def __load_scene_data(self, index: int) -> None:
        """Load the data for the specified scene.

        Args:
            index (int): The index of the scene.
        """
        scene_file_name = self.__get_file_prefix(index)
        storage_file = self.node_storage.get_file(scene_file_name)
        self._current_scene_data = storage_file.get_data()
        scene = self.scenes[index]
        for button in scene.list_buttons():
            if button.key in self._current_scene_data and self._current_scene_data[button.key]:
                button.apply_stoked_color()
            else:
                button.reset_stoked_color()

        logger.debug(f"Loaded scene data: {scene_file_name}")

    def __get_file_prefix(self, index: int) -> str:
        """Make the file prefix.
        """
        return f'{self._stock_file_name}_{index}'

    def __get_node_stock_file(self, button: nodeStock_view.NodeStockButton) -> node_storage.NodeStockFile:
        """Get the node stock file from the button.

        Args:
            button (nodeStock_view.NodeStockButton): The button.

        Returns:
            node_storage.NodeStockFile: The node stock file.
        """
        if not isinstance(button, nodeStock_view.NodeStockButton):
            return TypeError("Button must be an instance of NodeStockButton.")

        scene_index = self.scenes.index(button.scene())
        name = self.__get_file_prefix(scene_index)

        return self.node_storage.get_file(name)

    def __refresh_window(self) -> None:
        """Refresh the window.
        """
        self.__load_scene_data(self.switch_buttons.button_group.checkedId())
        self.name_space_box.refresh_name_spaces()

    @staticmethod
    def __get_node_length_label(node_count: int) -> str:
        """Get the node length label.

        Args:
            node_count (int): The number of nodes.

        Returns:
            str: The node length label.
        """
        return f'Nodes: {node_count}'

    def __update_status_bar(self, button: nodeStock_view.NodeStockButton) -> None:
        """Update the status bar with the button's information.

        Args:
            button (nodeStock_view.NodeStockButton): The button.
        """
        self.current_button = button
        nodes = self._current_scene_data.get(button.key, [])
        if not nodes:
            self.node_length_label.setText(self.__get_node_length_label(0))
            self.node_names_label.clear()

        node_count = len(nodes)
        node_names = ' '.join(nodes)
        max_width = self.status_bar.width() - self.status_bar_spacing
        elided_text = self.font_metrics.elidedText(node_names, Qt.ElideRight, max_width)
        self.node_length_label.setText(self.__get_node_length_label(node_count))
        self.node_names_label.setText(elided_text)

    def __clear_status_bar(self) -> None:
        """Clear the status bar.
        """
        self.node_length_label.setText(self.__get_node_length_label(0))
        self.node_names_label.clear()

    def __highlight_nodes(self, button: nodeStock_view.NodeStockButton) -> None:
        """Highlight the nodes in the Maya scene when the button is hovered.

        Args:
            button (nodeStock_view.NodeStockButton): The button.
        """
        if not self.tool_bar.is_hilite():
            return

        self._hilite_nodes = []
        nodes = self._current_scene_data.get(button.key, [])
        if not nodes:
            return

        # Get the replace and name space settings.
        nodes = self.__replace_node_names(nodes, echo_error=False)
        nodes = self.__name_space_with_nodes(nodes)
        nodes = [node for node in nodes if cmds.objExists(node)]
        if not nodes:
            return

        self._hilite_selected_nodes = cmds.ls(sl=True)
        cmds.hilite(nodes)
        self._hilite_nodes = nodes

    def __unhighlight_nodes(self) -> None:
        """Unhighlight the nodes in the Maya scene when the button is unhovered.
        """
        if not self._hilite_nodes:
            return

        cmds.hilite(self._hilite_nodes, u=True)
        cmds.select(self._hilite_selected_nodes, r=True)

    def __select_nodes(self, nodes: list[str]) -> None:
        """Select the nodes in the scene.

        Args:
            nodes (list[str]): The nodes to select.
        """
        # Get the replace and name space settings.
        nodes = self.__replace_node_names(nodes, echo_error=True)
        nodes = self.__name_space_with_nodes(nodes)

        # Validate the nodes.
        not_exists_nodes = [node for node in nodes if not cmds.objExists(node)]
        if not_exists_nodes:
            cmds.error(f"No existing nodes to select: {not_exists_nodes}")

        # Select the nodes.
        sel_nodes = cmds.ls(sl=True)
        mod_keys = maya_ui.get_modifiers()
        if not mod_keys:
            cmds.select(nodes, r=True)
            logger.debug(f"Selected new nodes: {nodes}")
        elif ['Shift', 'Ctrl'] == mod_keys:
            cmds.select(sel_nodes, r=True)
            cmds.select(nodes, add=True)
            logger.debug(f"Add selected new nodes: {nodes}")
        elif 'Shift' in mod_keys:
            cmds.select(sel_nodes, r=True)
            cmds.select(nodes, add=True)
            logger.debug(f"Add selected new nodes: {nodes}")
        elif 'Ctrl' in mod_keys:
            cmds.select(sel_nodes, r=True)
            cmds.select(nodes, d=True)
            logger.debug(f"Deselect selected new nodes: {nodes}")

        if self.tool_bar.is_hilite():
            self._hilite_selected_nodes = cmds.ls(sl=True)

    def __replace_node_names(self, nodes: list[str], echo_error: bool = False) -> list[str]:
        """Replace the node names.

        Args:
            nodes (list[str]): The nodes.
            echo_error (bool): If True, output an error.

        Returns:
            list[str]: The replaced nodes.
        """
        if not self.name_replace_field.is_enabled():
            logger.debug("Not enabled name replace field.")
            return nodes

        search_text, replace_text = self.name_replace_field.get_search_replace_text()
        if search_text or replace_text:
            if self.name_replace_field.is_switched():
                search_text, replace_text = replace_text, search_text

            if self.name_replace_field.is_re():
                nodes = lib_name.substitute_names(nodes, search_text, replace_text)
            else:
                if not search_text:
                    if echo_error:
                        cmds.error("Search text is required when not in regular expression mode.")

                    logger.debug("Search text is required when not in regular expression mode.")
                else:
                    nodes = [node.replace(search_text, replace_text) for node in nodes]

            return nodes
        else:
            logger.debug("No search and replace text.")
            return nodes

    def __name_space_with_nodes(self, nodes: list[str]) -> list[str]:
        """Get the name space with the nodes.

        Args:
            nodes (list[str]): The nodes.

        Returns:
            list[str]: The name space with the nodes.
        """
        if not self.name_space_box.is_enabled():
            logger.debug("No name space.")
            return nodes

        name_space = self.name_space_box.get_name_space()
        nodes = lib_name.replace_namespaces(nodes, name_space)

        logger.debug(f"Name spaced nodes: {nodes}")

        return nodes

    @maya_ui.undo_chunk('Select Nodes')
    @maya_ui.error_handler
    def _select_nodes(self, button: nodeStock_view.NodeStockButton) -> None:
        """Select the nodes when the left button is clicked.
        """
        nodes = self._current_scene_data.get(button.key, [])
        if not nodes:
            return

        self.__select_nodes(nodes)

        logger.debug(f"Selected nodes: {nodes}")

    @maya_ui.undo_chunk('Select Nodes by Rubber Band')
    @maya_ui.error_handler
    def _select_nodes_rubber_band(self, buttons: list[nodeStock_view.NodeStockButton]) -> None:
        """Select the nodes when the left button is clicked.
        """
        if not buttons:
            logger.debug("No buttons to select.")
            return

        nodes = []
        for button in buttons:
            nodes.extend(self._current_scene_data.get(button.key, []))

        if not nodes:
            logger.debug("No nodes to select.")
            return

        self.__select_nodes(nodes)

        logger.debug(f"Selected nodes by rubber band: {nodes}")

    @maya_ui.error_handler
    def _add_nodes(self, button: nodeStock_view.NodeStockButton) -> None:
        """Add the nodes to nodeStorage when the middle button is clicked.
        """
        sel_nodes = cmds.ls(sl=True)
        if not sel_nodes:
            cmds.warning("No nodes selected.")
            return

        # Add the nodes to the storage file.
        node_stock_file = self.__get_node_stock_file(button)
        node_stock_file.add_nodes(button.key, sel_nodes, overwrite=True)

        # Update the current scene data.
        self._current_scene_data[button.key] = sel_nodes

        # Change the button color.
        button.apply_stoked_color()

        logger.debug(f"Added nodes: {sel_nodes}")

    @maya_ui.error_handler
    def _remove_nodes(self, button: nodeStock_view.NodeStockButton) -> None:
        """Remove the nodes from nodeStorage when the right button is clicked.
        """
        # Remove the nodes from the storage file.
        node_stock_file = self.__get_node_stock_file(button)
        nodes = node_stock_file.get_nodes(button.key)
        if not nodes:
            logger.debug("No nodes registered to the button.")
            return

        node_stock_file.remove_nodes(button.key)

        # Update the current scene data.
        self._current_scene_data.pop(button.key, None)

        # Change the button color.
        button.reset_stoked_color()

        logger.debug(f"Removed nodes: {nodes}")

    def closeEvent(self, event) -> None:
        """Close the window.
        """
        # Save option settings
        self.tool_options.write('hilite', self.tool_bar.is_hilite())
        self.tool_options.write('name_space_enabled', self.name_space_box.is_enabled())
        self.tool_options.write('name_replace_enabled', self.name_replace_field.is_enabled())
        self.tool_options.write('search_replace', self.name_replace_field.get_search_replace_text())
        self.tool_options.write('name_replace_switched', self.name_replace_field.is_switched())
        self.tool_options.write('name_replace_re', self.name_replace_field.is_re())

        super().closeEvent(event)


class ToolBar(QWidget):
    """Tool bar for the node stocker.
    """

    refresh_button_clicked = Signal()

    def __init__(self, parent=None):
        """Constructor.
        """
        super().__init__(parent=parent)

        self.main_layout = QHBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        spacer = QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.main_layout.addItem(spacer)

        self.hilite_button = extra_widgets.CheckBoxButton(icon_off='lightbulb-off', icon_on='lightbulb')
        self.main_layout.addWidget(self.hilite_button)

        self.refresh_button = QPushButton()
        icon = QIcon(tool_icons.get_icon_path('refresh-cw'))
        self.refresh_button.setIcon(icon)
        self.refresh_button.setStyleSheet("""
            QPushButton {
                border: none;
            }
            QPushButton:pressed {
                background-color: #5285a6;
            }
        """)
        self.main_layout.addWidget(self.refresh_button)

        self.setLayout(self.main_layout)

        # Signals & Slots
        self.refresh_button.clicked.connect(self.refresh_button_clicked.emit)

    def is_hilite(self) -> bool:
        """Check if the hilite button is checked.

        Returns:
            bool: True if the hilite button is checked.
        """
        return self.hilite_button.isChecked()

    def set_hilite(self, checked: bool) -> None:
        """Set the hilite button checked.

        Args:
            checked (bool): True if the hilite button is checked.
        """
        self.hilite_button.setChecked(checked)


class StockAreaSwitchButtons(QWidget):
    """Switch buttons for the stock area stack widget.
    """
    button_selection_changed = Signal(int)

    def __init__(self, num_buttons: int = 10, parent=None):
        """Constructor.

        Args:
            num_buttons (int): The number of buttons.
        """
        super().__init__(parent=parent)

        self.main_layout = QHBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)

        for i in range(num_buttons):
            radio_button = QRadioButton()
            self.button_group.addButton(radio_button, i)
            self.main_layout.addWidget(radio_button)

        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.main_layout.addItem(spacer)

        self.setLayout(self.main_layout)

        # Signals & Slots
        self.button_group.buttonClicked.connect(self.__button_clicked)

    def set_index(self, index: int) -> None:
        """Set the index of the radio button to be selected.
        """
        self.button_group.button(index).setChecked(True)

    def __button_clicked(self, button: QRadioButton) -> None:
        """Emit the signal when the button is clicked.
        """
        self.button_selection_changed.emit(self.button_group.id(button))


class NameSpaceBox(QWidget):

    def __init__(self, parent=None):
        """Constructor.
        """
        super().__init__(parent=parent)

        self.main_layout = QHBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        self.check_box = QCheckBox()
        self.main_layout.addWidget(self.check_box)

        self.name_space_box = QComboBox()
        self.main_layout.addWidget(self.name_space_box, stretch=1)

        self.setLayout(self.main_layout)

        self.refresh_name_spaces()

        # Signals & Slots
        self.check_box.stateChanged.connect(self.name_space_box.setEnabled)

    def refresh_name_spaces(self) -> None:
        """Populate the name space box with the name spaces.
        """
        name_spaces = lib_name.list_all_namespace()
        name_spaces.insert(0, '')
        self.name_space_box.clear()
        self.name_space_box.addItems(name_spaces)

    def get_name_space(self) -> str:
        """Get the name space.

        Returns:
            str: The name space.
        """
        if not self.check_box.isChecked():
            return ''

        return self.name_space_box.currentText()

    def set_enabled(self, enabled: bool) -> None:
        """Set the name space box enabled.

        Args:
            enabled (bool): True if the name space box is enabled.
        """
        self.check_box.setChecked(enabled)

    def is_enabled(self) -> bool:
        """Check if the name space box is enabled.

        Returns:
            bool: True if the name space box is enabled.
        """
        return self.check_box.isChecked()


class NameReplaceField(QWidget):

    def __init__(self, parent=None):
        """Constructor.
        """
        super().__init__(parent=parent)

        self.main_layout = QHBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        self.check_box = QCheckBox()
        self.main_layout.addWidget(self.check_box)

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(1)

        self.search_field = QLineEdit()
        layout.addWidget(self.search_field)

        self.switch_button = extra_widgets.CheckBoxButton(icon_off='arrow-right-half', icon_on='arrow-left-half')
        layout.addWidget(self.switch_button)

        self.replace_field = QLineEdit()
        layout.addWidget(self.replace_field)

        self.re_button = extra_widgets.CheckBoxButton(icon_off='wildcard-half', icon_on='wildcard-checked-half')
        layout.addWidget(self.re_button)

        self.main_layout.addLayout(layout)

        self.setLayout(self.main_layout)

        # Signals & Slots
        self.check_box.stateChanged.connect(self.enabled_changed)

    def set_enabled(self, enabled: bool) -> None:
        """Set the name replace field enabled.

        Args:
            enabled (bool): True if the name replace field is enabled.
        """
        self.check_box.setChecked(enabled)

    def is_enabled(self) -> bool:
        """Check if the name replace field is enabled.

        Returns:
            bool: True if the name replace field is enabled.
        """
        return self.check_box.isChecked()

    def enabled_changed(self, enabled: bool) -> None:
        """Set the name replace field enabled.

        Args:
            enabled (bool): True if the name replace field is enabled.
        """
        self.search_field.setEnabled(enabled)
        self.switch_button.setEnabled(enabled)
        self.replace_field.setEnabled(enabled)
        self.re_button.setEnabled(enabled)

    def is_switched(self) -> bool:
        """Check if the switch button is checked.

        Returns:
            bool: True if the switch button is checked.
        """
        return self.switch_button.isChecked()

    def set_switched(self, checked: bool) -> None:
        """Set the switch button checked.

        Args:
            checked (bool): True if the switch button is checked.
        """
        self.switch_button.setChecked(checked)

    def is_re(self) -> bool:
        """Check if the re button is checked.

        Returns:
            bool: True if the re button is checked.
        """
        return self.re_button.isChecked()

    def set_re(self, checked: bool) -> None:
        """Set the re button checked.

        Args:
            checked (bool): True if the re button is checked.
        """
        self.re_button.setChecked(checked)

    def get_search_replace_text(self) -> tuple[str, str]:
        """Get the search and replace text.

        Returns:
            tuple[str, str]: The search and replace text.
        """
        search_text = self.search_field.text()
        replace_text = self.replace_field.text()

        return search_text, replace_text

    def set_search_replace_text(self, search_text: str, replace_text: str) -> None:
        """Set the search and replace text.

        Args:
            search_text (str): The search text.
            replace_text (str): The replace text.
        """
        self.search_field.setText(search_text)
        self.replace_field.setText(replace_text)


def show_ui(num_areas: int = 7, *args, **kwargs):
    """Show the main window.

    Args:
        num_areas (int): The number of areas.

    Keyword Args:
        rows (int): The number of button rows.
        cols (int): The number of button columns.
        button_size (int): The size of the buttons.
    """
    window_name = f'{__name__}MainWindow'
    maya_qt.delete_widget(window_name)

    # Create the main window.
    main_window = MainWindow(parent=maya_qt.get_maya_pointer(),
                             object_name=window_name,
                             window_title='Node Stocker',
                             num_areas=num_areas,
                             *args, **kwargs)
    main_window.show()
