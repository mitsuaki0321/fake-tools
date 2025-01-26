"""
Tool base window class.
"""

from PySide2.QtCore import Qt
from PySide2.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QMainWindow,
    QVBoxLayout,
    QWidget,
)


class BaseMainWindow(QMainWindow):

    def __init__(self,
                 parent=None,
                 object_name: str = 'MainWindow',
                 window_title: str = 'Main Window',
                 central_layout: str = 'vertical'):
        """Constructor.

        Args:
            parent (QWidget): Parent widget.
            object_name (str): Object name.
            window_title (str): Window title.
            central_layout (str): Central layout type. Default is 'vertical'. 'horizontal' is also available.
        """
        super().__init__(parent=parent)

        self.setObjectName(object_name)
        self.setWindowTitle(window_title)
        self.setAttribute(Qt.WA_DeleteOnClose)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.central_layout = QVBoxLayout() if central_layout == 'vertical' else QHBoxLayout()
        self.central_widget.setLayout(self.central_layout)

        default_widget_spacing = get_spacing(self.central_widget)
        self.central_layout.setSpacing(int(default_widget_spacing * 0.75))


def get_spacing(widget: QWidget = QWidget(), direction: str = 'vertical') -> int:
    """Get default widget spacing.

    Args:
        widget (QWidget): Widget. Default is QWidget().
        direction (str): Direction. Default is 'vertical'. 'horizontal' is also available.
    """
    return QApplication.style().layoutSpacing(
        widget.sizePolicy().controlType(),
        widget.sizePolicy().controlType(),
        direction == 'vertical' and Qt.Vertical or Qt.Horizontal
    )


def get_margins(widget: QWidget) -> tuple:
    """Get default margins (left, top, right, bottom) for a widget based on its style.

    Args:
        widget (QWidget): The target widget.

    Returns:
        tuple: A tuple of four integers representing (left, top, right, bottom) margins.
    """
    # Get the style for the widget
    style = QApplication.style()

    # Retrieve default margins from the style
    left = style.pixelMetric(style.PM_LayoutLeftMargin, None, widget)
    top = style.pixelMetric(style.PM_LayoutTopMargin, None, widget)
    right = style.pixelMetric(style.PM_LayoutRightMargin, None, widget)
    bottom = style.pixelMetric(style.PM_LayoutBottomMargin, None, widget)

    # Return as a tuple
    return (left, top, right, bottom)
