"""
Attribute connection tool.
"""

from __future__ import annotations

from functools import partial
from logging import getLogger

import maya.cmds as cmds
from PySide2.QtCore import QItemSelectionModel, Qt, Signal
from PySide2.QtGui import QStandardItem
from PySide2.QtWidgets import (
    QApplication,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpacerItem,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from ..command import singleCommands
from ..lib.lib_singleCommand import PairCommand
from ..lib_ui import base_window, maya_qt, maya_ui, optionvar
from ..lib_ui.widgets import nodeAttr_widgets

logger = getLogger(__name__)


class MainWindow(base_window.BaseMainWindow):

    def __init__(self,
                 parent=None,
                 object_name='MainWindow',
                 window_title='Main Window'):
        """Constructor.
        """
        super().__init__(parent=parent, object_name=object_name, window_title=window_title)

        self.tool_options = optionvar.ToolOptionSettings(__name__)

        # Load button
        load_button_layout = QHBoxLayout()
        load_button_layout.setContentsMargins(0, 0, 0, 0)

        source_load_button = QPushButton('Load Source')
        load_button_layout.addWidget(source_load_button)

        dest_load_button = QPushButton('Load Destination')
        load_button_layout.addWidget(dest_load_button)

        self.central_layout.addLayout(load_button_layout)

        # Node list
        node_list_layout = QHBoxLayout()
        node_list_layout.setContentsMargins(0, 0, 0, 0)

        self.source_node_list = nodeAttr_widgets.NodeListView()
        node_list_layout.addWidget(self.source_node_list)

        self.dest_node_list = nodeAttr_widgets.NodeListView()
        node_list_layout.addWidget(self.dest_node_list)

        self.central_layout.addLayout(node_list_layout)

        # Node count
        node_count_layout = QHBoxLayout()
        node_count_layout.setContentsMargins(0, 0, 0, 0)

        self.source_node_count_label = NodeCountLabel()
        node_count_layout.addWidget(self.source_node_count_label)

        self.dest_node_count_label = NodeCountLabel()
        node_count_layout.addWidget(self.dest_node_count_label)

        self.central_layout.addLayout(node_count_layout)

        # Operation
        operation_layout = QVBoxLayout()

        # Operation switch
        operation_switch_widget = OperationSwitchWidget()
        operation_layout.addWidget(operation_switch_widget)

        self.operation_stack_widget = QStackedWidget()
        operation_layout.addWidget(self.operation_stack_widget)

        # Attribute list
        attr_layout = QWidget()
        layout = QGridLayout(attr_layout)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(self.central_layout.spacing())

        self.operation_stack_widget.addWidget(attr_layout)

        self.source_attr_list = nodeAttr_widgets.AttributeListView(self.source_node_list)
        layout.addWidget(self.source_attr_list, 0, 0)

        self.source_filter_line_edit = QLineEdit()
        self.source_filter_line_edit.setPlaceholderText("Filter attributes...")
        layout.addWidget(self.source_filter_line_edit, 1, 0)

        self.dest_attr_list = nodeAttr_widgets.AttributeListView(self.dest_node_list)
        layout.addWidget(self.dest_attr_list, 0, 1)

        self.dest_filter_line_edit = QLineEdit()
        self.dest_filter_line_edit.setPlaceholderText("Filter attributes...")
        layout.addWidget(self.dest_filter_line_edit, 1, 1)

        copy_value_button = QPushButton('Copy Value')
        layout.addWidget(copy_value_button, 2, 0)

        connect_button = QPushButton('Connect')
        layout.addWidget(connect_button, 2, 1)

        # Command list
        command_layout = QWidget()
        layout = QVBoxLayout(command_layout)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(1)

        # Load single pair commands
        commands = singleCommands.PAIR_COMMANDS
        if commands:
            for cls_name in commands:
                button = QPushButton(cls_name)
                layout.addWidget(button)

                button.clicked.connect(partial(self._execute_single_command, cls_name))

            spacer = QSpacerItem(1, 1, QSizePolicy.Minimum, QSizePolicy.Expanding)
            layout.addItem(spacer)

        # Add QScrollArea for command list
        command_list_scroll_area = QScrollArea()
        command_list_scroll_area.setWidget(command_layout)
        command_list_scroll_area.setWidgetResizable(True)
        self.operation_stack_widget.addWidget(command_list_scroll_area)

        self.central_layout.addLayout(operation_layout)

        # Signal & Slot
        source_load_button.clicked.connect(lambda: self._list_nodes(self.source_node_list, self._source_display_attributes))
        dest_load_button.clicked.connect(lambda: self._list_nodes(self.dest_node_list, self._dest_display_attributes))
        self.source_node_list.node_changed.connect(lambda: self._set_node_count(self.source_node_list, self.source_node_count_label))
        self.dest_node_list.node_changed.connect(lambda: self._set_node_count(self.dest_node_list, self.dest_node_count_label))
        self.source_node_list.selectionModel().selectionChanged.connect(lambda: self._set_node_count(self.source_node_list, self.source_node_count_label))  # noqa
        self.dest_node_list.selectionModel().selectionChanged.connect(lambda: self._set_node_count(self.dest_node_list, self.dest_node_count_label))
        operation_switch_widget.button_changed.connect(self.__switch_operation)
        self.source_filter_line_edit.textChanged.connect(self.source_attr_list.attr_model.setFilterFixedString)
        self.dest_filter_line_edit.textChanged.connect(self.dest_attr_list.attr_model.setFilterFixedString)
        copy_value_button.clicked.connect(self._copy_value)
        connect_button.clicked.connect(self._connect_attribute)

    def __switch_operation(self, index) -> None:
        """Switch operation stack widget.

        Args:
            index (int): The index of the operation stack widget.
        """
        self.operation_stack_widget.setCurrentIndex(index)

    @maya_ui.error_handler
    def _list_nodes(self, node_list_widget: nodeAttr_widgets.NodeListView,
                    display_attributes_callback: callable) -> None:
        """Update the node list

        Args:
            node_list_widget (NodeList): The node list widget.
            display_attributes_callback (callable): The function to display the attributes of the node.
        """
        sel_nodes = cmds.ls(sl=True)
        if not sel_nodes:
            cmds.error('Please select the nodes to list.')

        shift_pressed = QApplication.keyboardModifiers() == Qt.ShiftModifier
        if shift_pressed:
            nodes = node_list_widget.get_all_nodes()
            selection_indexes = node_list_widget.selectionModel().selectedIndexes()
            if not nodes:
                nodes = sel_nodes
            else:
                for node in sel_nodes:
                    if node not in nodes:
                        nodes.append(node)
        else:
            nodes = sel_nodes

        node_list_widget.replace_nodes(nodes)

        # Connect the signal after setting the model
        selection_model = node_list_widget.selectionModel()
        selection_model.selectionChanged.connect(display_attributes_callback)

        # Select the current selection
        if shift_pressed and selection_indexes:
            for index in selection_indexes:
                node_list_widget.selectionModel().select(index, QItemSelectionModel.Select)
        else:
            selection_model.select(node_list_widget.node_model.index(0, 0), QItemSelectionModel.Select)

    def _set_node_count(self, node_list_widget: nodeAttr_widgets.NodeListView, node_count_label: NodeCountLabel) -> None:
        """Set the node count.

        Args:
            node_list_widget (NodeList): The node list widget.
            node_count_label (NodeCountLabel): The node count label.
        """
        total_count = node_list_widget.get_count()
        selected_count = node_list_widget.get_selected_count()
        node_count_label.set_count(selected_count, total_count)

    def _source_display_attributes(self) -> None:
        """Display the attributes of the selected source nodes.
        """
        self.__display_attributes(self.source_node_list, self.source_attr_list, self.__source_list_attributes)

    def _dest_display_attributes(self) -> None:
        """Display the attributes of the selected destination nodes.
        """
        self.__display_attributes(self.dest_node_list, self.dest_attr_list, self.__dest_list_attributes)

    def __display_attributes(self, node_list_widget: nodeAttr_widgets.NodeListView,
                             attr_list_widget: nodeAttr_widgets.AttributeListView,
                             list_attributes_callback: callable) -> None:
        """Display the attributes of the selected nodes

        Args:
            node_list_widget (NodeList): The node list widget.
            attr_list_widget (AttributeList): The attribute list widget.
            list_attributes_callback (callable): The function to list the attributes of the node.
        """
        attr_list_widget.model().sourceModel().clear()
        selected_indexes = node_list_widget.selectionModel().selectedIndexes()
        if not selected_indexes:
            return

        selected_nodes = [index.data() for index in selected_indexes]
        common_attributes = list_attributes_callback(selected_nodes[0])

        if len(selected_nodes) > 1:
            for node in selected_nodes[1:]:
                node_attrs = list_attributes_callback(node)
                common_attributes = [attr for attr in common_attributes if attr in node_attrs]

        for attr in common_attributes:
            item = QStandardItem(attr)
            attr_list_widget.model().sourceModel().appendRow(item)

    def __source_list_attributes(self, node: str) -> list[str]:
        """List the attributes of the node.

        Args:
            node (str): The node name.

        Returns:
            list[str]: The attributes of the node.
        """
        return self.__list_attributes(node)

    def __dest_list_attributes(self, node: str) -> list[str]:
        """List the attributes of the node.

        Args:
            node (str): The node name.

        Returns:
            list[str]: The attributes of the node.
        """
        return self.__list_attributes(node)

    def __list_attributes(self, node: str) -> list[str]:
        """List the attributes of the node.

        Args:
            node (str): The node name.

        Returns:
            list[str]: The attributes of the node.
        """
        result_attrs = []

        if 'transform' in cmds.nodeType(node, inherited=True):
            result_attrs.extend(['translate', 'rotate', 'scale', 'shear',
                                 'translateX', 'translateY', 'translateZ',
                                 'rotateX', 'rotateY', 'rotateZ',
                                 'scaleX', 'scaleY', 'scaleZ',
                                 'shearXY', 'shearXZ', 'shearYZ',
                                 'visibility'])

        user_attrs = cmds.listAttr(node, userDefined=True)
        if user_attrs:
            result_attrs.extend(user_attrs)

        attrs = cmds.listAttr(node) or []
        except_attr_types = ['TdataCompound']
        for attr in attrs:
            if attr in result_attrs:
                continue
            try:
                if cmds.getAttr(f'{node}.{attr}', type=True) in except_attr_types:
                    continue
                result_attrs.append(attr)
            except Exception:
                logger.debug(f'Failed to list attribute: {node}.{attr}')

        return result_attrs

    @maya_ui.undo_chunk('Copy Attribute Value')
    @maya_ui.error_handler
    def _copy_value(self) -> None:
        """Copy the value of the source attribute to the destination attribute.
        """
        self.__transfer_attribute(self.__copy_value)

    @maya_ui.undo_chunk('Connect Attribute')
    @maya_ui.error_handler
    def _connect_attribute(self) -> None:
        """Connect the source attribute to the destination attribute.
        """
        self.__transfer_attribute(self.__connect_attribute)

    def __transfer_attribute(self, func: callable) -> None:
        """Transfer the attribute value.

        Args:
            func (callable): The function to transfer the attribute value. (copy_value or connect_attribute)
        """
        source_nodes = self.source_node_list.get_selected_nodes()
        dest_nodes = self.dest_node_list.get_selected_nodes()
        source_attrs = self.source_attr_list.get_selected_attributes()
        dest_attrs = self.dest_attr_list.get_selected_attributes()

        if not source_nodes or not dest_nodes or not source_attrs or not dest_attrs:
            cmds.error('Please select the source and destination nodes and attributes.')

        if len(source_nodes) > 1 and len(source_nodes) != len(dest_nodes):
            cmds.error('Please select the same number of nodes or select only one source node.')

        if len(source_attrs) > 1 and len(source_attrs) != len(dest_attrs):
            cmds.error('Please select the same number of attributes or select only one source attribute.')

        if len(source_nodes) == 1:
            source_nodes = source_nodes * len(dest_nodes)

        if len(source_attrs) == 1:
            source_attrs = source_attrs * len(dest_attrs)

        for source_node, dest_node in zip(source_nodes, dest_nodes):
            for source_attr, dest_attr in zip(source_attrs, dest_attrs):
                func(source_node, source_attr, dest_node, dest_attr)

    @staticmethod
    def __copy_value(source_node: str, source_attr: str, dest_node: str, dest_attr: str) -> None:
        """Copy the value of the source attribute to the destination attribute.

        Args:
            source_node (str): The source node name.
            source_attr (str): The source attribute name.
            dest_node (str): The destination node name.
            dest_attr (str): The destination attribute name.
        """
        source_plug = f'{source_node}.{source_attr}'
        dest_plug = f'{dest_node}.{dest_attr}'
        if cmds.getAttr(dest_plug, lock=True):
            cmds.error(f'The attribute is locked: {dest_plug}')

        if cmds.connectionInfo(dest_plug, isDestination=True):
            cmds.error(f'The attribute is connected: {dest_plug}')

        source_type = cmds.getAttr(source_plug, type=True)
        dest_type = cmds.getAttr(dest_plug, type=True)

        if source_type == 'string' or dest_type == 'string':
            if source_type != dest_type:
                cmds.error('Both attributes must be strings.')
            cmds.setAttr(dest_plug, cmds.getAttr(source_plug), type='string')
        elif source_type == 'matrix' or dest_type == 'matrix':
            if source_type != dest_type:
                cmds.error('Both attributes must be matrices.')
            cmds.setAttr(dest_plug, cmds.getAttr(source_plug), type='matrix')
        else:
            num_source_elements = cmds.attributeQuery(source_attr, node=source_node, numberOfChildren=True)
            num_dest_elements = cmds.attributeQuery(dest_attr, node=dest_node, numberOfChildren=True)
            if num_source_elements or num_dest_elements:
                if num_source_elements != num_dest_elements:
                    cmds.error('The number of elements in the compound attributes does not match.')

                cmds.setAttr(dest_plug, *cmds.getAttr(source_plug)[0])
            else:
                cmds.setAttr(dest_plug, cmds.getAttr(source_plug))

        logger.debug(f'Copied: {source_plug} -> {dest_plug}')

    @staticmethod
    def __connect_attribute(source_node: str, source_attr: str, dest_node: str, dest_attr: str) -> None:
        """Connect the source attribute to the destination attribute.

        Args:
            source_node (str): The source node name.
            source_attr (str): The source attribute name.
            dest_node (str): The destination node name.
            dest_attr (str): The destination attribute name.
        """
        source_plug = f'{source_node}.{source_attr}'
        dest_plug = f'{dest_node}.{dest_attr}'
        if cmds.getAttr(dest_plug, lock=True):
            cmds.error(f'The attribute is locked: {dest_plug}')

        if cmds.isConnected(source_plug, dest_plug, iuc=True):
            cmds.error(f'The attribute is already connected: {dest_plug}')

        source_type = cmds.getAttr(source_plug, type=True)
        dest_type = cmds.getAttr(dest_plug, type=True)

        if source_type == 'string' or dest_type == 'string':
            if source_plug != dest_plug:
                cmds.error('Both attributes must be strings.')
            cmds.connectAttr(source_plug, dest_plug, f=True)
        elif source_type == 'matrix' or dest_type == 'matrix':
            if source_plug != dest_plug:
                cmds.error('Both attributes must be matrices.')
            cmds.connectAttr(source_plug, dest_plug, f=True)
        else:
            cmds.connectAttr(source_plug, dest_plug, f=True)

        logger.debug(f'Connected: {source_plug} -> {dest_plug}')

    @maya_ui.undo_chunk('Execute Single Command')
    @maya_ui.error_handler
    def _execute_single_command(self, command_name: str) -> None:
        """Execute the single command.

        Args:
            command_name (str): The single command class name.
        """
        if not hasattr(singleCommands, command_name):
            cmds.error(f'Command does not exist: {command_name}')

        single_command_cls = getattr(singleCommands, command_name)
        if not issubclass(single_command_cls, PairCommand):
            cmds.error(f'Command is not a pair command: {command_name}')

        source_nodes = self.source_node_list.get_selected_nodes()
        dest_nodes = self.dest_node_list.get_selected_nodes()

        if not source_nodes or not dest_nodes:
            cmds.error('Please select the source and destination nodes.')

        if len(source_nodes) > 1 and len(source_nodes) != len(dest_nodes):
            cmds.error('Please select the same number of nodes or select only one source node.')

        if len(source_nodes) == 1:
            source_nodes = source_nodes * len(dest_nodes)

        single_command_cls(source_nodes, dest_nodes)

        logger.debug(f'Executed: {command_name}')


class OperationSwitchWidget(QWidget):
    """Switch operation stack widget.
    """

    button_changed = Signal(int)

    def __init__(self, parent=None):
        """Initialize the widget.
        """
        super().__init__(parent=parent)

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.connect_button = OperationSwitchButton('Connect')
        self.connect_button.setCheckable(True)
        self.connect_button.setChecked(True)
        layout.addWidget(self.connect_button)

        self.command_button = OperationSwitchButton('Command')
        self.command_button.setCheckable(True)
        self.command_button.setChecked(False)
        layout.addWidget(self.command_button)

        self.setLayout(layout)

        # Signal & Slot
        self.connect_button.clicked.connect(self.__toggle_checked)
        self.command_button.clicked.connect(self.__toggle_checked)

    def __toggle_checked(self) -> None:
        """Toggle the checked state of the buttons.
        """
        sender = self.sender()
        if sender == self.connect_button:
            self.blockSignals(True)

            if self.connect_button.isChecked():
                self.command_button.setChecked(False)
            else:
                self.connect_button.setChecked(True)

            self.blockSignals(False)
        elif sender == self.command_button:
            self.blockSignals(True)

            if self.command_button.isChecked():
                self.connect_button.setChecked(False)
            else:
                self.command_button.setChecked(True)

            self.blockSignals(False)

        self.button_changed.emit(int(self.command_button.isChecked()))


class OperationSwitchButton(QPushButton):
    """Switch operation button.
    """

    def __init__(self, text: str, parent=None):
        """Initialize the button.

        Args:
            text (str): The button text.
        """
        super().__init__(text, parent=parent)

        self.setCheckable(True)
        self.setChecked(False)
        self.toggled.connect(self.__update_style)

    def __update_style(self, checked: bool) -> None:
        """Update the button style based on the checked state.

        Args:
            checked (bool): The checked state.
        """
        if checked:
            stylesheet = """
            QPushButton {
                border: 1px solid #444444;
                background-color: #3c3c3c;
                color: #cccccc;
                padding: 5px 10px;
            }
            QPushButton:checked {
                background-color: #5285A6;
                color: #ffffff;
            }
            """
            self.setStyleSheet(stylesheet)
        else:
            self.setStyleSheet("")


class NodeCountLabel(QLabel):
    """Label to display the number of nodes.
    """

    def __init__(self, parent=None):
        """Initialize the label.
        """
        super().__init__(parent=parent)
        self.setText('0 / 0')
        self.setAlignment(Qt.AlignCenter)

    def set_count(self, current: int, total: int) -> None:
        """Set the current and total count.

        Args:
            current (int): The current count.
            total (int): The total count.
        """
        self.setText(f'{current} / {total}')


def show_ui():
    """Show the main window.
    """
    window_name = f'{__name__}MainWindow'
    maya_qt.delete_widget(window_name)

    # Create the main window.
    main_window = MainWindow(parent=maya_qt.get_maya_pointer(),
                             object_name=window_name,
                             window_title='Connection Lister')
    main_window.show()
    size = main_window.size()
    main_window.resize(size.width() * 0.75, size.height() * 0.75)
