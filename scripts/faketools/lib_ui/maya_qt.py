"""
This module contains Maya-specific functions in Qt.
"""

import re

import maya.OpenMayaUI as OpenMayaUI  # type: ignore
import maya.OpenMayaUI as omui  # type: ignore
import shiboken2 as shiboken
from PySide2.QtWidgets import QApplication, QWidget


def get_maya_pointer() -> QWidget:
    """Obtain the main window of Maya in a format recognizable by PySide.

    Returns:
        QWidget: Main window of Maya.
    """
    return shiboken.wrapInstance(int(OpenMayaUI.MQtUtil.mainWindow()), QWidget)


def get_qt_window(object_name):
    """Convert a cmds maya window to a PySide2 QWidget.

    Args:
        object_name (str): The object name of the cmds window.

    Returns:
        QWidget: PySide2 QWidget representation of the cmds maya window, or None if not found.
    """
    ptr = omui.MQtUtil.findWindow(object_name)
    if ptr is None:
        raise RuntimeError(f'Failed to find window "{object_name}".')

    return shiboken.wrapInstance(int(ptr), QWidget)


def delete_widget(obj_name: str) -> None:
    """Deletes the QMainWindow object created to prevent multiple windows from launching, if it exists, before creation.

    Args:
        obj_name (str, optional): Object name.
    """
    if not obj_name:
        return
    widgets = QApplication.topLevelWidgets()
    for w in widgets:
        try:
            this_name = w.objectName()
            if not this_name:
                continue
            if re.search(obj_name, this_name):
                w.close()
                break
        except Exception:
            continue
