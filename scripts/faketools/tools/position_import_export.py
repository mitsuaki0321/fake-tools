"""
Transform node position export and import tool.
"""

import glob
import importlib
import os
from logging import getLogger

import maya.cmds as cmds
from PySide2.QtCore import QStringListModel, Qt
from PySide2.QtWidgets import (
    QCheckBox,
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListView,
    QMainWindow,
    QMenu,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .. import user_directory
from ..command import object_morph
from ..lib_ui import maya_qt, maya_ui, optionvar
from ..lib_ui.widgets import extra_widgets

logger = getLogger(__name__)


importlib.reload(object_morph)


class MainWindow(QMainWindow):

    _method_list = ['Default', 'Barycentric', 'Rbf']
    _create_new_list = ['transform', 'locator', 'joint']
    _axis_list = ['X', 'Y', 'Z']

    def __init__(self,
                 parent=None,
                 object_name='MainWindow',
                 window_title='Main Window'):
        """Constructor.
        """
        super().__init__(parent=parent)

        self.tool_options = optionvar.ToolOptionSettings(__name__)
        self.output_directory = user_directory.ToolDirectory(__name__).get_directory()

        self.setObjectName(object_name)
        self.setWindowTitle(window_title)
        self.setAttribute(Qt.WA_DeleteOnClose)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.central_layout = QVBoxLayout()
        self.central_layout.setSpacing(5)
        self.central_widget.setLayout(self.central_layout)

        # Export Options
        self.method_box = QComboBox()
        self.method_box.addItems(self._method_list)
        self.central_layout.addWidget(self.method_box)

        self.file_name_field = QLineEdit()
        self.file_name_field.setPlaceholderText('File Name')
        self.central_layout.addWidget(self.file_name_field)

        export_button = QPushButton('Export')
        self.central_layout.addWidget(export_button)

        self.file_list_view = QListView()
        self.file_list_view.setEditTriggers(QListView.NoEditTriggers)
        self.file_list_model = QStringListModel()
        self.file_list_view.setModel(self.file_list_model)
        self.central_layout.addWidget(self.file_list_view)

        self.file_list_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.file_list_view.customContextMenuRequested.connect(self._on_context_menu)

        layout = QHBoxLayout()

        # Data Information
        self.node_length_label = QLabel('{}  '.format(self.__get_node_length_label(0)))
        self.node_length_label.setFixedWidth(self.node_length_label.sizeHint().width())
        layout.addWidget(self.node_length_label)

        separator = extra_widgets.VerticalSeparator()
        separator.setFixedWidth(separator.sizeHint().width() * 2)
        layout.addWidget(separator)

        self.method_label = QLabel(self.__get_method_label('None'))
        layout.addWidget(self.method_label)

        layout.addStretch(1)

        self.central_layout.addLayout(layout)

        separator = extra_widgets.HorizontalSeparator()
        self.central_layout.addWidget(separator)

        # Import Options
        import_button = QPushButton('Import')
        self.central_layout.addWidget(import_button)

        self.is_rotation_checkbox = QCheckBox('Is Rotation')
        self.central_layout.addWidget(self.is_rotation_checkbox)

        self.create_new_checkbox = QCheckBox('Create New')
        self.central_layout.addWidget(self.create_new_checkbox)

        layout = QGridLayout()

        self.object_type_label = QLabel('Object Type:', alignment=Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(self.object_type_label, 0, 0)

        self.object_type_box = QComboBox()
        self.object_type_box.addItems(self._create_new_list)
        layout.addWidget(self.object_type_box, 0, 1)

        self.object_size_label = QLabel('Size:', alignment=Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(self.object_size_label, 1, 0)

        self.object_size = extra_widgets.ModifierSpinBox()
        self.object_size.setRange(0.01, 100.0)
        self.object_size.setValue(1.0)
        layout.addWidget(self.object_size, 1, 1)

        layout.setColumnStretch(1, 1)

        self.central_layout.addLayout(layout)

        # Signals & Slots
        self.create_new_checkbox.stateChanged.connect(self.__update_create_new_options)
        self.file_list_view.clicked.connect(self.__update_data_information)
        export_button.clicked.connect(self.export_transform_position)
        import_button.clicked.connect(self.import_transform_position)

        # Initial state
        self.__update_create_new_options()
        self.__update_file_list()

        self.resize(self.minimumSize())

    @maya_ui.error_handler
    def export_transform_position(self) -> None:
        """Export the positions of the selected objects.
        """
        method = self.method_box.currentText().lower()
        file_name = self.file_name_field.text()

        if not file_name:
            cmds.error('File name is empty.')

        object_morph.export_transform_position(output_directory=self.output_directory,
                                               file_name=file_name,
                                               method=method)

        self.__update_file_list()

    @maya_ui.undo_chunk('Import Transform Position')
    @maya_ui.error_handler
    def import_transform_position(self) -> None:
        """Import the positions of the selected objects.
        """
        sel_file_path = self.__get_selected_file_path()
        if not sel_file_path:
            cmds.error('No file selected.')

        is_rotation = self.is_rotation_checkbox.isChecked()
        create_new = self.create_new_checkbox.isChecked()
        object_type = self.object_type_box.currentText()
        object_size = self.object_size.value()

        object_morph.import_transform_position(sel_file_path,
                                               create_new=create_new,
                                               is_rotation=is_rotation,
                                               creation_object_type=object_type,
                                               creation_object_size=object_size)

    @maya_ui.error_handler
    def _open_directory(self) -> None:
        """Open file directory.
        """
        os.startfile(self.output_directory)

        logger.debug(f'Opened directory: {self.output_directory}')

    @maya_ui.error_handler
    def _remove_file(self) -> None:
        """Remove the selected file from the file list. ( Deletes the file )
        """
        sel_file_path = self.__get_selected_file_path()
        if not sel_file_path:
            cmds.error('No file selected.')

        os.remove(sel_file_path)
        self.__update_file_list()

        logger.debug(f'Removed file: {sel_file_path}')

    def _on_context_menu(self, point) -> None:
        """Show the context menu on the file list view.
        """
        menu = QMenu()

        action = menu.addAction('Remove File')
        action.triggered.connect(self._remove_file)

        menu.addSeparator()

        action = menu.addAction('Refresh')
        action.triggered.connect(self.__update_file_list)

        menu.addSeparator()

        action = menu.addAction('Open Directory')
        action.triggered.connect(self._open_directory)

        menu.exec_(self.file_list_view.mapToGlobal(point))

    def __update_file_list(self) -> None:
        """Update the file list.
        """
        directory_file_list = glob.glob(os.path.join(self.output_directory, '*.pkl'))
        file_list = [os.path.splitext(os.path.basename(file))[0] for file in directory_file_list]

        self.file_list_model.setStringList(file_list)

        logger.debug(f'Updated file list: {file_list}')

    def __update_data_information(self) -> None:
        """Update the data information.

        Args:
            node_count (int): The number of nodes.
            method (str): The method.
        """
        sel_file_path = self.__get_selected_file_path()
        try:
            transform_data = object_morph.load_transform_position_data(sel_file_path)
        except Exception as e:
            logger.error(f'Failed to load transform data: {sel_file_path}\n{e}')
            self.node_length_label.setText(self.__get_node_length_label(0))
            self.method_label.setText(self.__get_method_label('None'))
            return

        node_count = len(transform_data['transforms'])
        method = transform_data['method']

        self.node_length_label.setText(self.__get_node_length_label(node_count))
        self.method_label.setText(self.__get_method_label(method))

    def __get_selected_file_path(self) -> str:
        """Get the selected file path.

        Returns:
            str: The selected file.
        """
        selected_index = self.file_list_view.selectionModel().selectedIndexes()
        if not selected_index:
            return None

        selected_file = self.file_list_model.data(selected_index[0])

        file_path = os.path.join(self.output_directory, f'{selected_file}.pkl')
        if not os.path.exists(file_path):
            raise ValueError(f'File does not exist: {file_path}')

        return file_path

    def __update_create_new_options(self) -> None:
        """Enable/Disable based on the state of the Create New checkbox.
        """
        state = self.create_new_checkbox.isChecked()
        self.object_type_label.setEnabled(state)
        self.object_type_box.setEnabled(state)

    @ staticmethod
    def __get_node_length_label(node_count: int) -> str:
        """Get the node length label.

            Args:
                node_count (int): The number of nodes.

            Returns:
                str: The node length label.
            """
        return f'Nodes: {node_count}'

    @ staticmethod
    def __get_method_label(method: str) -> str:
        """Get the method label.

            Args:
                method (str): The method.

            Returns:
                str: The method label.
        """
        return f'Method: {method}'


def show_ui():
    """Show the main window.
    """
    window_name = f'{__name__}MainWindow'
    maya_qt.delete_widget(window_name)

    # Create the main window.
    main_window = MainWindow(parent=maya_qt.get_maya_pointer(),
                             object_name=window_name,
                             window_title='Position Import/Export')
    main_window.show()
