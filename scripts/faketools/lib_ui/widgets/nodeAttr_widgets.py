"""Node list widget.
"""

from logging import getLogger

import maya.cmds as cmds
from PySide2.QtCore import (
    QEvent,
    QItemSelectionModel,
    QSortFilterProxyModel,
    Qt,
    Signal,
)
from PySide2.QtGui import QStandardItem, QStandardItemModel
from PySide2.QtWidgets import (
    QApplication,
    QLineEdit,
    QListView,
    QMenu,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .. import maya_ui

logger = getLogger(__name__)


class NodeList(QListView):
    """Node list view.
    """

    def __init__(self, parent=None):
        """Initialize the NodeList.
        """
        super(NodeList, self).__init__(parent)
        self.setSelectionMode(QListView.ExtendedSelection)
        self.setEditTriggers(QListView.NoEditTriggers)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        self.viewport().installEventFilter(self)

    def eventFilter(self, source, event) -> bool:
        """Event filter to handle right-click context menu.
        """
        if source is self.viewport() and event.type() == QEvent.MouseButtonPress:
            if event.button() == Qt.RightButton:
                position = event.pos()
                global_position = self.viewport().mapToGlobal(position)
                self.show_context_menu(global_position)
                return True
            elif event.button() == Qt.MiddleButton:
                return True

        return super(NodeList, self).eventFilter(source, event)

    def show_context_menu(self, position) -> None:
        """Show context menu for node list.

        Args:
            position (Qt.Pos): The position of the context menu
        """
        menu = QMenu()
        menu.addAction("Select Node(s)", self.select_nodes)
        menu.addAction("Select All Nodes", self.select_all_nodes)
        menu.exec_(position)

    @maya_ui.undo_chunk('Select Nodes')
    @maya_ui.error_handler
    def select_nodes(self) -> None:
        """Select the nodes in Maya scene that are selected in the node list.
        """
        selected_nodes = self.get_selected_nodes()
        if selected_nodes:
            cmds.select(selected_nodes, replace=True)
        else:
            cmds.select(clear=True)

    @maya_ui.undo_chunk('Select All Nodes')
    @maya_ui.error_handler
    def select_all_nodes(self) -> None:
        """Select all nodes in the node list in Maya scene.
        """
        all_nodes = self.get_all_nodes()
        if all_nodes:
            cmds.select(all_nodes, replace=True)
        else:
            cmds.select(clear=True)

    def get_selected_nodes(self) -> list[str]:
        """Get the selected nodes.

        Returns:
            list[str]: The selected nodes.
        """
        selected_indexes = self.selectionModel().selectedIndexes()
        return [index.data() for index in selected_indexes]

    def get_all_nodes(self) -> list[str]:
        """Get all the nodes.

        Returns:
            list[str]: All the nodes.
        """
        return [self.model().item(i).text() for i in range(self.model().rowCount())]


class AttributeList(QListView):
    """Attribute list view.
    """
    attribute_lock_changed = Signal()

    def __init__(self, node_widgets: NodeList, parent=None):
        """Initialize the AttributeList.

        Args:
            node_widgets (NodeList): The node list widget.
        """
        super(AttributeList, self).__init__(parent)
        self.setSelectionMode(QListView.ExtendedSelection)
        self.setEditTriggers(QListView.NoEditTriggers)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        self.viewport().installEventFilter(self)

        self.attr_model = QSortFilterProxyModel(self)
        self.attr_model.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.attribute_source_model = QStandardItemModel(self)
        self.attr_model.setSourceModel(self.attribute_source_model)
        self.setModel(self.attr_model)

        self.node_widgets = node_widgets

    def eventFilter(self, source, event) -> bool:
        """Event filter to handle right-click context menu.
        """
        if source is self.viewport() and event.type() == QEvent.MouseButtonPress:
            if event.button() == Qt.RightButton:
                position = event.pos()
                global_position = self.viewport().mapToGlobal(position)
                self.show_context_menu(global_position)
                return True
            elif event.button() == Qt.MiddleButton:
                return True
        return super(AttributeList, self).eventFilter(source, event)

    def show_context_menu(self, position) -> None:
        """Show context menu for attribute list.
        """
        menu = QMenu()
        menu.addAction("Lock", self.__lock_attributes)
        menu.addAction("Unlock", self.__unlock_attributes)
        menu.addSeparator()
        menu.addAction("Keyable", self.__keyable_attributes)
        menu.addAction("Unkeyable", self.__unkeyable_attributes)
        menu.exec_(position)

    @maya_ui.undo_chunk('Lock Attributes')
    @maya_ui.error_handler
    def __lock_attributes(self) -> None:
        """Lock the selected attributes.
        """
        selected_nodes = self.node_widgets.get_selected_nodes()
        selected_attrs = self.get_selected_attributes()

        if not selected_nodes or not selected_attrs:
            return

        for node in selected_nodes:
            for attr in selected_attrs:
                cmds.setAttr(f'{node}.{attr}', lock=True)

        self.attribute_lock_changed.emit()

    @maya_ui.undo_chunk('Unlock Attributes')
    @maya_ui.error_handler
    def __unlock_attributes(self) -> None:
        """Unlock the selected attributes.
        """
        selected_nodes = self.node_widgets.get_selected_nodes()
        selected_attrs = self.get_selected_attributes()

        if not selected_nodes or not selected_attrs:
            return

        for node in selected_nodes:
            for attr in selected_attrs:
                cmds.setAttr(f'{node}.{attr}', lock=False)

        self.attribute_lock_changed.emit()

    @maya_ui.undo_chunk('Keyable Attributes')
    @maya_ui.error_handler
    def __keyable_attributes(self) -> None:
        """Set the selected attributes keyable.
        """
        selected_nodes = self.node_widgets.get_selected_nodes()
        selected_attrs = self.get_selected_attributes()

        if not selected_nodes or not selected_attrs:
            return

        for node in selected_nodes:
            for attr in selected_attrs:
                cmds.setAttr(f'{node}.{attr}', keyable=True)

    @maya_ui.undo_chunk('Unkeyable Attributes')
    @maya_ui.error_handler
    def __unkeyable_attributes(self) -> None:
        """Set the selected attributes unkeyable.
        """
        selected_nodes = self.node_widgets.get_selected_nodes()
        selected_attrs = self.get_selected_attributes()

        if not selected_nodes or not selected_attrs:
            return

        for node in selected_nodes:
            for attr in selected_attrs:
                cmds.setAttr(f'{node}.{attr}', keyable=False)

    def get_selected_attributes(self) -> list[str]:
        """Get the selected attributes.

        Returns:
            list[str]: The selected attributes.
        """
        selected_indexes = self.selectionModel().selectedIndexes()
        return [index.data() for index in selected_indexes]

    def get_all_attributes(self) -> list[str]:
        """Get all the attributes.

        Returns:
            list[str]: All the attributes.
        """
        return [self.model().item(i).text() for i in range(self.model().rowCount())]


class NodeAttributeWidgets(QWidget):
    """Node attribute widgets.
    """

    def __init__(self, parent=None):
        """Initialize the NodeListWidget.
        """
        super(NodeAttributeWidgets, self).__init__(parent)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        load_button = QPushButton('Load')
        self.main_layout.addWidget(load_button)

        self.node_list = NodeList()
        self.main_layout.addWidget(self.node_list)

        self.attr_list = AttributeList(self.node_list)
        self.main_layout.addWidget(self.attr_list)

        self.filter_line_edit = QLineEdit()
        self.filter_line_edit.setPlaceholderText("Filter attributes...")
        self.main_layout.addWidget(self.filter_line_edit)

        self.setLayout(self.main_layout)

        # Signal & Slot
        load_button.clicked.connect(self._list_nodes)
        self.filter_line_edit.textChanged.connect(self.attr_list.attr_model.setFilterFixedString)

    @maya_ui.error_handler
    def _list_nodes(self) -> None:
        """Update the node list.
        """
        sel_nodes = cmds.ls(sl=True)
        if not sel_nodes:
            cmds.error('Please select the nodes to list.')

        shift_pressed = QApplication.keyboardModifiers() == Qt.ShiftModifier
        if shift_pressed:
            nodes = self.get_all_nodes()
            selection_indexes = self.node_list.selectionModel().selectedIndexes()
            if not nodes:
                nodes = sel_nodes
            else:
                for node in sel_nodes:
                    if node not in nodes:
                        nodes.append(node)
        else:
            nodes = sel_nodes

        self.node_list.setModel(QStandardItemModel(self.node_list))
        model = self.node_list.model()

        for node in nodes:
            item = QStandardItem(node)
            model.appendRow(item)

        # Connect the signal after setting the model
        selection_model = self.node_list.selectionModel()
        selection_model.selectionChanged.connect(self._display_attributes)

        # Select the current selection
        if shift_pressed and selection_indexes:
            for index in selection_indexes:
                selection_model.select(index, QItemSelectionModel.Select)
        else:
            selection_model.select(model.index(0, 0), QItemSelectionModel.Select)

    def _display_attributes(self) -> None:
        """Display the attributes of the selected nodes.
        """
        self.attr_list.model().sourceModel().clear()
        selected_indexes = self.node_list.selectionModel().selectedIndexes()
        if not selected_indexes:
            return

        selected_nodes = [index.data() for index in selected_indexes]
        common_attributes = self.__list_attributes(selected_nodes[0])

        if len(selected_nodes) > 1:
            for node in selected_nodes[1:]:
                node_attrs = self.__list_attributes(node)
                common_attributes = [attr for attr in common_attributes if attr in node_attrs]

        for attr in common_attributes:
            item = QStandardItem(attr)
            self.attr_list.model().sourceModel().appendRow(item)

    def __list_attributes(self, node, *args, **kwargs) -> list[str]:
        """List the attributes of the node.

        Args:
            node (str): The node name.

        Returns:
            list[str]: The attributes of the node.
        """
        except_attr_types = kwargs.get('except_attr_types', ['message', 'TdataCompound'])

        result_attrs = []

        if 'transform' in cmds.nodeType(node, inherited=True):
            result_attrs.extend(['translateX', 'translateY', 'translateZ',
                                 'rotateX', 'rotateY', 'rotateZ',
                                 'scaleX', 'scaleY', 'scaleZ',
                                 'visibility'])

        user_attrs = cmds.listAttr(node, userDefined=True)
        if user_attrs:
            result_attrs.extend(user_attrs)

        write_attrs = cmds.listAttr(node, write=True) or []
        for attr in write_attrs:
            if attr in result_attrs:
                continue
            try:
                if cmds.attributeQuery(attr, node=node, listChildren=True):
                    continue
                if cmds.getAttr(f'{node}.{attr}', type=True) in except_attr_types:
                    continue
                result_attrs.append(attr)
            except RuntimeError:
                logger.debug(f'Failed to list attribute: {node}.{attr}')

        return result_attrs

    def get_selected_nodes(self) -> list[str]:
        """Get the selected nodes.

        Returns:
            list[str]: The selected nodes.
        """
        return self.node_list.get_selected_nodes()

    def get_selected_attributes(self) -> list[str]:
        """Get the selected attributes.

        Returns:
            list[str]: The selected attributes.
        """
        return self.attr_list.get_selected_attributes()

    def get_all_nodes(self) -> list[str]:
        """Get all the nodes.

        Returns:
            list[str]: All the nodes.
        """
        return self.node_list.get_all_nodes()

    def get_all_attributes(self) -> list[str]:
        """Get all the attributes.

        Returns:
            list[str]: All the attributes.
        """
        return self.attr_list.get_all_attributes()
