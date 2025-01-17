"""
Maya scene optimize tool.
"""

from PySide2.QtCore import Qt
from PySide2.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ..command import scene_optimize
from ..lib_ui import maya_qt, maya_ui, optionvar
from ..lib_ui.widgets import extra_widgets


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

        self.optimizers = scene_optimize.list_optimizers()

        self.enable_checkboxes = []
        for optimizer in self.optimizers:
            layout = QHBoxLayout()

            checkbox = QCheckBox(optimizer.label)
            checkbox.setToolTip(optimizer.description)
            layout.addWidget(checkbox)
            self.enable_checkboxes.append(checkbox)

            button = QPushButton('Run')
            button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            button.clicked.connect(lambda: optimizer.execute(echo=True))
            layout.addWidget(button)

            self.central_layout.addLayout(layout)

        self.central_layout.addWidget(extra_widgets.HorizontalSeparator())

        layout = QHBoxLayout()
        layout.setSpacing(1)

        all_on_checked_button = QPushButton('All On')
        layout.addWidget(all_on_checked_button)

        all_off_checked_button = QPushButton('All Off')
        layout.addWidget(all_off_checked_button)

        toggle_checked_button = QPushButton('Toggle Checked')
        layout.addWidget(toggle_checked_button)

        self.central_layout.addLayout(layout)

        self.central_layout.addWidget(extra_widgets.HorizontalSeparator())

        execute_button = QPushButton('Optimize Scene')
        self.central_layout.addWidget(execute_button)

        # Option settings
        for checkbox in self.enable_checkboxes:
            checkbox.setChecked(self.tool_options.read(checkbox.text(), True))

        # Signal & Slot
        all_on_checked_button.clicked.connect(self.__all_on_checked)
        all_off_checked_button.clicked.connect(self.__all_off_checked)
        toggle_checked_button.clicked.connect(self.__toggle_checked)
        execute_button.clicked.connect(self.__execute)

    def __all_on_checked(self):
        """All on checked.
        """
        for checkbox in self.enable_checkboxes:
            checkbox.setChecked(True)

    def __all_off_checked(self):
        """All off checked.
        """
        for checkbox in self.enable_checkboxes:
            checkbox.setChecked(False)

    def __toggle_checked(self):
        """Toggle checked.
        """
        for checkbox in self.enable_checkboxes:
            checkbox.setChecked(not checkbox.isChecked())

    @maya_ui.error_handler
    @maya_ui.undo_chunk('Optimize Scene')
    def __execute(self):
        """Execute.
        """
        start_msg = 'Start Optimize Scene'
        print('#' * len(start_msg))
        print(start_msg)
        print('#' * len(start_msg))
        print('')

        for checkbox, optimizer in zip(self.enable_checkboxes, self.optimizers):
            if checkbox.isChecked():
                optimizer.execute(echo=True)

        end_msg = 'End Optimize Scene'
        print('')
        print('#' * len(end_msg))
        print(end_msg)
        print('#' * len(end_msg))

    def closeEvent(self, event):
        """Close event.
        """
        # Save option settings
        for checkbox in self.enable_checkboxes:
            self.tool_options.write(checkbox.text(), checkbox.isChecked())

        super().closeEvent(event)


def show_ui():
    """Show the main window.
    """
    window_name = f'{__name__}MainWindow'
    maya_qt.delete_widget(window_name)

    # Create the main window.
    main_window = MainWindow(parent=maya_qt.get_maya_pointer(),
                             object_name=window_name,
                             window_title='Scene Optimizer')
    main_window.show()
