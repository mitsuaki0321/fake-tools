"""
Extra widgets for the UI.
"""

from PySide2.QtCore import Qt
from PySide2.QtGui import QIcon
from PySide2.QtWidgets import (
    QApplication,
    QDoubleSpinBox,
    QFrame,
    QPushButton,
    QSizePolicy,
)

from ..tool_icons import get_icon_path


class HorizontalSeparator(QFrame):
    """Separator widget.
    """

    def __init__(self, parent=None):
        """Constructor.

        Args:
            parent (QWidget): Parent widget.
        """
        super().__init__(parent=parent)

        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Sunken)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)


class VerticalSeparator(QFrame):
    """Separator widget.
    """

    def __init__(self, parent=None):
        """Constructor.

        Args:
            parent (QWidget): Parent widget.
        """
        super().__init__(parent=parent)

        self.setFrameShape(QFrame.VLine)
        self.setFrameShadow(QFrame.Sunken)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)


class CheckBoxButton(QPushButton):
    """Check box button widget.
    """

    def __init__(self, icon_on, icon_off, parent=None):
        """Constructor.

        Args:
            icon_on (QIcon): The icon when checked.
            icon_off (QIcon): The icon when unchecked.
            parent (QWidget): Parent widget.
        """
        super().__init__(parent=parent)

        self.icon_on = QIcon(get_icon_path(icon_on))
        self.icon_off = QIcon(get_icon_path(icon_off))

        self.setCheckable(True)
        self.setChecked(False)

        self.setIcon(self.icon_off)
        self.setIconSize(self.icon_on.actualSize(self.size()))

        self.setStyleSheet('border: none;')

        self.toggled.connect(self.update_icon)

    def update_icon(self, checked):
        """Update the icon based on the checked state.

        Args:
            checked (bool): The checked state.
        """
        if checked:
            self.setIcon(self.icon_on)
        else:
            self.setIcon(self.icon_off)


class ModifierSpinBox(QDoubleSpinBox):
    """Double spin box widget with modifier keys.
    """

    def __init__(self, parent=None):
        """Constructor.
        """
        super(ModifierSpinBox, self).__init__(parent=parent)
        self.__shift_multiplier = 10.0
        self.__ctrl_multiplier = 0.1

    def setShiftStepMultiplier(self, value: float):
        """Set the step value based on the shift key.

        Args:
            value (float): The multiplier shift value.
        """
        self.__shift_multiplier = value

    def setCtrlStepMultiplier(self, value: float):
        """Set the step value based on the control key.

        Args:
            value (float): The multiplier control value.
        """
        self.__ctrl_multiplier = value

    def stepBy(self, steps):
        """Step by value. (Overrides QDoubleSpinBox.stepBy)

        Notes:
            - Maya returns 1.0 as the singleStep value under normal conditions.
            - When the Ctrl key is pressed, it returns 10.0 as the singleStep value.
        """
        modifiers = QApplication.keyboardModifiers()

        multiplier = 1.0
        if modifiers & Qt.ControlModifier:
            multiplier = self.__ctrl_multiplier * 0.1
        elif modifiers & Qt.ShiftModifier:
            multiplier = self.__shift_multiplier

        self.setValue(self.value() + self.singleStep() * steps * multiplier)
