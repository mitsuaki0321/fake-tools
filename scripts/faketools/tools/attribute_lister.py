"""
Attribute set tool.
"""

from logging import getLogger

import maya.cmds as cmds
from PySide2.QtCore import Qt
from PySide2.QtWidgets import QLineEdit, QMainWindow, QVBoxLayout, QWidget

from ..lib_ui import maya_qt, maya_ui, optionvar
from ..lib_ui.widgets import nodeAttr_widgets

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

        self.view = nodeAttr_widgets.NodeAttributeWidgets()
        self.central_layout.addWidget(self.view)

        self.value_field = QLineEdit()
        self.view.main_layout.addWidget(self.value_field)

        # Signal & Slot
        self.view.attr_list.selectionModel().selectionChanged.connect(self._display_value)
        self.value_field.returnPressed.connect(self._set_value)
        self.view.attr_list.attribute_lock_changed.connect(self._display_value)

    def _display_value(self) -> None:
        """Display the value of the selected attribute.
        """
        nodes = self.view.get_selected_nodes()
        attrs = self.view.get_selected_attributes()

        if not nodes or not attrs:
            self.value_field.setText('')
            self.value_field.setEnabled(False)
            return

        value = cmds.getAttr(f'{nodes[-1]}.{attrs[-1]}')
        self.value_field.setText(str(value))

        attr_types = set()
        for node in nodes:
            for attr in attrs:
                if cmds.getAttr(f'{node}.{attr}', lock=True):
                    self.value_field.setEnabled(False)
                    self.value_field.setStyleSheet("background-color: darkgrey;")

                    logger.debug(f'Attribute is locked: {node}.{attr}')
                    return

                if cmds.connectionInfo(f'{node}.{attr}', isDestination=True):
                    self.value_field.setEnabled(False)
                    self.value_field.setStyleSheet("background-color: lightyellow;")

                    logger.debug(f'Attribute is connected: {node}.{attr}')
                    return

                attr_type = cmds.getAttr(f'{node}.{attr}', type=True)
                attr_types.add(attr_type)

        if len(attr_types) > 1:
            self.value_field.setEnabled(False)
            self.value_field.setStyleSheet("background-color: pink;")
        else:
            self.value_field.setEnabled(True)
            self.value_field.setStyleSheet("")

    @maya_ui.undo_chunk('Set Attribute Value')
    @maya_ui.error_handler
    def _set_value(self) -> None:
        """Set the value of the selected attribute.
        """
        nodes = self.view.get_selected_nodes()
        attrs = self.view.get_selected_attributes()

        if not nodes or not attrs:
            return

        if not self.value_field.text():
            cmds.error('No value is entered.')

        if not self.value_field.isEnabled():
            cmds.error('Cannot change the value because the attribute type is different, it is connected, or it is locked.')

        try:
            value = self.value_field.text()
            attr_type = cmds.getAttr(f'{nodes[-1]}.{attrs[-1]}', type=True)
            if attr_type == 'bool':
                value = bool(int(value))
            elif attr_type in ['long', 'short', 'byte', 'char', 'enum', 'time']:
                value = int(value)
            elif attr_type == 'string':
                value = str(value)
            elif attr_type in ['float', 'double', 'doubleLinear', 'doubleAngle']:
                value = float(value)
            elif attr_type == 'matrix':
                value = eval(value)
            else:
                raise ValueError(f'Unsupported attribute type: {attr_type}')

            for node in nodes:
                for attr in attrs:
                    if attr_type == 'matrix':
                        cmds.setAttr(f'{node}.{attr}', *value, type=attr_type)
                    elif attr_type == 'string':
                        cmds.setAttr(f'{node}.{attr}', value, type=attr_type)
                    else:
                        cmds.setAttr(f'{node}.{attr}', value)

        except (ValueError, SyntaxError, TypeError) as e:
            cmds.error(f'Invalid input value: {value}. \n{str(e)}')


def show_ui():
    """Show the main window.
    """
    window_name = f'{__name__}MainWindow'
    maya_qt.delete_widget(window_name)

    # Create the main window.
    main_window = MainWindow(parent=maya_qt.get_maya_pointer(),
                             object_name=window_name,
                             window_title='Attribute Lister')
    main_window.show()
