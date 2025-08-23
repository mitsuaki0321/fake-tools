"""
This module contains Maya-specific functions in Qt.
"""

import re

import maya.OpenMayaUI as OpenMayaUI
import maya.OpenMayaUI as omui

try:
    from PySide2.QtCore import QObject
    from PySide2.QtWidgets import QApplication, QWidget
    import shiboken2 as shiboken
except ImportError:
    from PySide6.QtCore import QObject
    from PySide6.QtWidgets import QApplication, QWidget
    import shiboken6 as shiboken


def get_qt_control(name: str, qt_object: QObject = QWidget) -> QWidget:
    """Get the control of the qt_object from the maya ui name.

    Args:
        name (str): Name of the control.
        qt_object (QObject, optional): Qt object to wrap the control with. Defaults to QWidget.

    Returns:
        Mixed: The control of the qt object.
    """
    ptr = omui.MQtUtil.findControl(name)
    if ptr is None:
        raise RuntimeError(f'Failed to find control "{name}".')

    return shiboken.wrapInstance(int(ptr), qt_object)


def get_maya_control(qt_object: QObject) -> str:
    """Get the full name of the ui maya object.

    Args:
        qt_object (QObject): Object to wrap.

    Returns:
        str: Full name of the ui maya object.
    """
    return OpenMayaUI.MQtUtil.fullName(int(shiboken.getCppPointer(qt_object)[0]))


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
