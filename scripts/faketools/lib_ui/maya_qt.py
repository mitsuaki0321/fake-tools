"""
This module contains Maya-specific functions in Qt.
"""

import re

import maya.OpenMayaUI as OpenMayaUI  # type: ignore
import shiboken2 as shiboken
import six  # type: ignore
from PySide2.QtWidgets import QApplication, QWidget


def get_maya_pointer() -> QWidget:
    """Obtain the main window of Maya in a format recognizable by PySide.

    Returns:
        QWidget: Main window of Maya.
    """
    return shiboken.wrapInstance(six.integer_types[-1](OpenMayaUI.MQtUtil.mainWindow()), QWidget)


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
