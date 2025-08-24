"""
Retarget transforms tool.
"""

import glob
from logging import getLogger
import os

import maya.cmds as cmds

try:
    from PySide2.QtCore import QStringListModel, Qt
    from PySide2.QtWidgets import (
        QCheckBox,
        QComboBox,
        QGridLayout,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QListView,
        QMenu,
        QPushButton,
    )
except ImportError:
    from PySide6.QtCore import QStringListModel, Qt
    from PySide6.QtWidgets import (
        QCheckBox,
        QComboBox,
        QGridLayout,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QListView,
        QMenu,
        QPushButton,
    )

from .. import user_directory
from ..command import retarget_transforms
from ..lib_ui import base_window, maya_qt, maya_ui, optionvar
from ..lib_ui.widgets import extra_widgets

logger = getLogger(__name__)


class MainWindow(base_window.BaseMainWindow):
    _method_list = ["Default", "Barycentric", "Rbf"]
    _create_new_list = ["transform", "locator", "joint"]
    _axis_list = ["X", "Y", "Z"]

    def __init__(self, parent=None, object_name="MainWindow", window_title="Main Window"):
        """Constructor."""
        super().__init__(parent=parent, object_name=object_name, window_title=window_title)

        self.tool_options = optionvar.ToolOptionSettings(__name__)
        self.output_directory = user_directory.ToolDirectory(__name__).get_directory()

        # Export Options
        layout = QGridLayout()

        label = QLabel("Method:", alignment=Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(label, 0, 0)

        self.method_box = QComboBox()
        self.method_box.addItems(self._method_list)
        layout.addWidget(self.method_box, 0, 1)

        self.rbf_radius_label = QLabel("Rbf Radius:", alignment=Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(self.rbf_radius_label, 1, 0)

        self.rbf_radius_box = extra_widgets.ModifierSpinBox()
        self.rbf_radius_box.setRange(1.5, 10.0)
        self.rbf_radius_box.setSingleStep(0.1)
        layout.addWidget(self.rbf_radius_box, 1, 1)

        label = QLabel("File Name:", alignment=Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(label, 2, 0)

        self.file_name_field = QLineEdit()
        self.file_name_field.setPlaceholderText("File Name")
        layout.addWidget(self.file_name_field, 2, 1)

        self.central_layout.addLayout(layout)

        export_button = QPushButton("Export")
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
        self.node_length_label = QLabel(f"{self.__get_node_length_label(0)}  ")
        self.node_length_label.setFixedWidth(self.node_length_label.sizeHint().width())
        layout.addWidget(self.node_length_label)

        separator = extra_widgets.VerticalSeparator()
        separator.setFixedWidth(separator.sizeHint().width() * 2)
        layout.addWidget(separator)

        self.method_label = QLabel(self.__get_method_label("None"))
        layout.addWidget(self.method_label)

        layout.addStretch(1)

        self.central_layout.addLayout(layout)

        separator = extra_widgets.HorizontalSeparator()
        self.central_layout.addWidget(separator)

        # Import Options
        self.is_rotation_checkbox = QCheckBox("Is Rotation")
        self.central_layout.addWidget(self.is_rotation_checkbox)

        self.create_new_checkbox = QCheckBox("Create New")
        self.central_layout.addWidget(self.create_new_checkbox)

        self.restore_hierarchy_checkbox = QCheckBox("Restore Hierarchy")
        self.central_layout.addWidget(self.restore_hierarchy_checkbox)

        layout = QGridLayout()

        self.object_type_label = QLabel("Object Type:", alignment=Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(self.object_type_label, 0, 0)

        self.object_type_box = QComboBox()
        self.object_type_box.addItems(self._create_new_list)
        layout.addWidget(self.object_type_box, 0, 1)

        self.object_size_label = QLabel("Size:", alignment=Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(self.object_size_label, 1, 0)

        self.object_size_box = extra_widgets.ModifierSpinBox()
        self.object_size_box.setRange(0.00, 100.0)
        self.object_size_box.setValue(1.0)
        layout.addWidget(self.object_size_box, 1, 1)

        layout.setColumnStretch(1, 1)

        self.central_layout.addLayout(layout)

        import_button = QPushButton("Import")
        self.central_layout.addWidget(import_button)

        # Option settings
        self.method_box.setCurrentText(self.tool_options.read("method", self._method_list[0]))
        self.rbf_radius_box.setValue(self.tool_options.read("rbf_radius", 1.5))
        self.is_rotation_checkbox.setChecked(self.tool_options.read("is_rotation", False))
        self.create_new_checkbox.setChecked(self.tool_options.read("create_new", False))
        self.restore_hierarchy_checkbox.setChecked(self.tool_options.read("restore_hierarchy", False))
        self.object_type_box.setCurrentText(self.tool_options.read("object_type", self._create_new_list[0]))
        self.object_size_box.setValue(self.tool_options.read("object_size", 1.0))

        # Signals & Slots
        self.method_box.currentIndexChanged.connect(self.__update_method_options)
        self.create_new_checkbox.stateChanged.connect(self.__update_create_new_options)
        self.file_list_view.clicked.connect(self.__update_data_information)
        export_button.clicked.connect(self.export_transform_position)
        import_button.clicked.connect(self.import_transform_position)

        selection_model = self.file_list_view.selectionModel()
        selection_model.selectionChanged.connect(self.__insert_file_name)

        # Initial state
        self.__update_create_new_options()
        self.__update_file_list()

        minimum_size = self.minimumSizeHint()
        width = minimum_size.width() * 1.1
        height = minimum_size.height()
        self.resize(width, height)

    @maya_ui.error_handler
    def export_transform_position(self) -> None:
        """Export the positions of the selected objects."""
        method = self.method_box.currentText().lower()
        rbf_radius = self.rbf_radius_box.value()
        file_name = self.file_name_field.text()

        if not file_name:
            cmds.error("File name is empty.")

        retarget_transforms.export_transform_position(
            output_directory=self.output_directory, file_name=file_name, method=method, rbf_radius=rbf_radius
        )

        self.__update_file_list()
        self.__select_file(file_name)

    @maya_ui.undo_chunk("Import Transform Position")
    @maya_ui.error_handler
    def import_transform_position(self) -> None:
        """Import the positions of the selected objects."""
        sel_file_path = self.__get_selected_file_path()
        if not sel_file_path:
            cmds.error("No file selected.")

        is_rotation = self.is_rotation_checkbox.isChecked()
        create_new = self.create_new_checkbox.isChecked()
        restore_hierarchy = self.restore_hierarchy_checkbox.isChecked()
        object_type = self.object_type_box.currentText()
        object_size = self.object_size_box.value()

        result_transforms = retarget_transforms.import_transform_position(
            sel_file_path,
            create_new=create_new,
            is_rotation=is_rotation,
            restore_hierarchy=restore_hierarchy,
            creation_object_type=object_type,
            creation_object_size=object_size,
        )

        if result_transforms:
            cmds.select(result_transforms, r=True)

    @maya_ui.error_handler
    def _select_data_nodes(self) -> None:
        """Select the transform nodes from the selected file."""
        sel_file_path = self.__get_selected_file_path()
        if not sel_file_path:
            cmds.error("No file selected.")

        transform_data = retarget_transforms.load_transform_position_data(sel_file_path)
        transform_nodes = transform_data["transforms"]

        not_exists_nodes = [node for node in transform_nodes if not cmds.objExists(node)]
        if not_exists_nodes:
            cmds.error(f"Nodes do not exist: {not_exists_nodes}")

        cmds.select(transform_nodes)

    @maya_ui.error_handler
    def _remove_file(self) -> None:
        """Remove the selected file from the file list. ( Deletes the file )"""
        sel_file_path = self.__get_selected_file_path()
        if not sel_file_path:
            cmds.error("No file selected.")

        os.remove(sel_file_path)
        self.__update_file_list()

        logger.debug(f"Removed file: {sel_file_path}")

    @maya_ui.error_handler
    def _open_directory(self) -> None:
        """Open file directory."""
        os.startfile(self.output_directory)

        logger.debug(f"Opened directory: {self.output_directory}")

    def _on_context_menu(self, point) -> None:
        """Show the context menu on the file list view."""
        menu = QMenu()

        action = menu.addAction("Select Nodes")
        action.triggered.connect(self._select_data_nodes)

        menu.addSeparator()

        action = menu.addAction("Remove File")
        action.triggered.connect(self._remove_file)

        action = menu.addAction("Refresh")
        action.triggered.connect(self.__update_file_list)

        menu.addSeparator()

        action = menu.addAction("Open Directory")
        action.triggered.connect(self._open_directory)

        menu.exec_(self.file_list_view.mapToGlobal(point))

    def __update_method_options(self) -> None:
        """Update the method options based on the selected method."""
        method = self.method_box.currentText().lower()
        if method == "rbf":
            self.rbf_radius_label.setEnabled(True)
            self.rbf_radius_box.setEnabled(True)
        else:
            self.rbf_radius_label.setEnabled(False)
            self.rbf_radius_box.setEnabled(False)

    def __update_file_list(self) -> None:
        """Update the file list."""
        directory_file_list = glob.glob(os.path.join(self.output_directory, "*.pkl"))
        file_list = [os.path.splitext(os.path.basename(file))[0] for file in directory_file_list]

        self.file_list_model.setStringList(file_list)

        logger.debug(f"Updated file list: {file_list}")

    def __update_data_information(self) -> None:
        """Update the data information.

        Args:
            node_count (int): The number of nodes.
            method (str): The method.
        """
        sel_file_path = self.__get_selected_file_path()
        try:
            transform_data = retarget_transforms.load_transform_position_data(sel_file_path)
        except Exception as e:
            logger.error(f"Failed to load transform data: {sel_file_path}\n{e}")
            self.node_length_label.setText(self.__get_node_length_label(0))
            self.method_label.setText(self.__get_method_label("None"))
            return

        node_count = len(transform_data["transforms"])
        method = transform_data["method"]

        self.node_length_label.setText(self.__get_node_length_label(node_count))
        self.method_label.setText(self.__get_method_label(method))

    def __insert_file_name(self, item) -> None:
        """Insert the file name to the file name field.

        Args:
            item (QModelIndex): The selected item.
        """
        indices = item.indexes()
        if not indices:
            return

        file_name = self.file_list_model.data(indices[0])
        self.file_name_field.setText(file_name)

    def __get_selected_file_path(self) -> str:
        """Get the selected file path.

        Returns:
            str: The selected file.
        """
        selected_index = self.file_list_view.selectionModel().selectedIndexes()
        if not selected_index:
            return None

        selected_file = self.file_list_model.data(selected_index[0])

        file_path = os.path.join(self.output_directory, f"{selected_file}.pkl")
        if not os.path.exists(file_path):
            raise ValueError(f"File does not exist: {file_path}")

        return file_path

    def __select_file(self, file_name: str) -> None:
        """Select the file in the file list.

        Args:
            file_name (str): The file name.
        """
        file_list = self.file_list_model.stringList()
        if file_name not in file_list:
            return

        index = file_list.index(file_name)
        self.file_list_view.setCurrentIndex(self.file_list_model.index(index))

    def __update_create_new_options(self) -> None:
        """Enable/Disable based on the state of the Create New checkbox."""
        state = self.create_new_checkbox.isChecked()
        self.object_type_label.setEnabled(state)
        self.object_type_box.setEnabled(state)
        self.object_size_label.setEnabled(state)
        self.object_size_box.setEnabled(state)
        self.restore_hierarchy_checkbox.setEnabled(state)

    @staticmethod
    def __get_node_length_label(node_count: int) -> str:
        """Get the node length label.

        Args:
            node_count (int): The number of nodes.

        Returns:
            str: The node length label.
        """
        return f"Nodes: {node_count}"

    @staticmethod
    def __get_method_label(method: str) -> str:
        """Get the method label.

        Args:
            method (str): The method.

        Returns:
            str: The method label.
        """
        return f"Method: {method}"

    def closeEvent(self, event) -> None:
        """Close event."""
        # Save option settings
        self.tool_options.write("method", self.method_box.currentText())
        self.tool_options.write("rbf_radius", self.rbf_radius_box.value())
        self.tool_options.write("is_rotation", self.is_rotation_checkbox.isChecked())
        self.tool_options.write("create_new", self.create_new_checkbox.isChecked())
        self.tool_options.write("restore_hierarchy", self.restore_hierarchy_checkbox.isChecked())
        self.tool_options.write("object_type", self.object_type_box.currentText())
        self.tool_options.write("object_size", self.object_size_box.value())

        super().closeEvent(event)


def show_ui():
    """Show the main window."""
    window_name = f"{__name__}MainWindow"
    maya_qt.delete_widget(window_name)

    # Create the main window.
    main_window = MainWindow(parent=maya_qt.get_maya_pointer(), object_name=window_name, window_title="Retarget Transform")
    main_window.show()
