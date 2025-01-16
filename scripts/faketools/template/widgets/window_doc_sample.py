"""
PySide Window Sample for Maya.
"""

import maya.cmds as cmds
from PySide2.QtCore import Qt
from PySide2.QtWidgets import QMainWindow, QPushButton, QVBoxLayout, QWidget

from ..lib_ui import maya_qt  # type: ignore


class MainWindow(QMainWindow):

    def __init__(self,
                 parent=None,
                 object_name='MainWindow',
                 window_title='Main Window'):
        """Main window sample.
        """
        super().__init__(parent=parent)

        self.setObjectName(object_name)
        self.setWindowTitle(window_title)
        self.setAttribute(Qt.WA_DeleteOnClose)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.central_layout = QVBoxLayout()
        self.central_widget.setLayout(self.central_layout)

        button = QPushButton('Sample Button A')
        self.central_layout.addWidget(button)

        button = QPushButton('Sample Button B')
        self.central_layout.addWidget(button)


def show_ui(dockable=True):
    """Show the main window.

    Args:
        dockable (bool): Show dockable window.
    """
    # Delete the existing tool bar and window.
    tool_bar_name = f'{__name__}MainSampleToolBar'
    if cmds.toolBar(tool_bar_name, q=True, ex=True):
        cmds.deleteUI(tool_bar_name)
    window_name = f'{__name__}MainWindow'
    maya_qt.delete_widget(window_name)

    # Create the main window.
    main_window = MainWindow(parent=maya_qt.get_maya_pointer(),
                             object_name=window_name,
                             window_title='Main Sampel Window')
    main_window.show()

    # Create the tool bar.
    if dockable:
        cmds.toolBar(tool_bar_name, area='top', content=window_name, allowedArea=['top', 'left', 'bottom', 'right'])
