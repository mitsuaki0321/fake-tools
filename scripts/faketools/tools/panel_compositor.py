"""
Camera Layer tool.
"""

import ctypes
from functools import partial
from logging import getLogger

import maya.api.OpenMaya as om
import maya.api.OpenMayaUI as omui
import maya.cmds as cmds

try:
    from PySide2.QtCore import Qt, QTimer, Signal
    from PySide2.QtGui import QColor, QIcon, QImage, QPainter, QPixmap
    from PySide2.QtWidgets import (
        QApplication,
        QColorDialog,
        QComboBox,
        QHBoxLayout,
        QLabel,
        QPushButton,
        QScrollArea,
        QSizePolicy,
        QVBoxLayout,
        QWidget,
    )
except ImportError:
    from PySide6.QtCore import Qt, QTimer, Signal
    from PySide6.QtGui import QColor, QIcon, QImage, QPainter, QPixmap
    from PySide6.QtWidgets import (
        QApplication,
        QColorDialog,
        QComboBox,
        QHBoxLayout,
        QLabel,
        QPushButton,
        QScrollArea,
        QSizePolicy,
        QVBoxLayout,
        QWidget,
    )

from ..lib_ui import base_window, maya_qt, optionvar, tool_icons
from ..lib_ui.widgets import extra_widgets

logger = getLogger(__name__)

tool_options = optionvar.ToolOptionSettings(__name__)


class MainWindow(base_window.BaseMainWindow):
    """Panel Compositor Main Window."""

    _default_image_label = "Captured image will appear here"
    _panel_height = 500
    _background_color = "#000000"

    def __init__(self, parent=None, object_name="MainWindow", window_title="Main Window"):
        """Constructor."""
        super().__init__(parent=parent, object_name=object_name, window_title=window_title)

        self.panel_layout_list = []
        self.panel_list = []
        self.loaded_camera_list = []
        self.view_list = []

        # Maya ui name
        central_layout_name = self._ui_name("centralLayout")
        scroll_area_name = self._ui_name("scrollArea")
        content_layout_name = self._ui_name("contentLayout")

        # Central widget
        self.central_layout.setObjectName(central_layout_name)
        central_layout_name = maya_qt.get_maya_control(self.central_layout)
        cmds.setParent(central_layout_name)

        # Tool bar
        tool_bar_layout = QHBoxLayout()
        tool_bar_layout.setContentsMargins(0, 0, 0, 0)

        self.camera_list_widget = CameraListWidget()
        self.camera_list_widget._set_camera_list()
        tool_bar_layout.addWidget(self.camera_list_widget, alignment=Qt.AlignLeft | Qt.AlignVCenter)

        tool_bar_layout.addStretch()

        self.play_button = PlayButton()
        tool_bar_layout.addWidget(self.play_button, alignment=Qt.AlignRight | Qt.AlignVCenter)

        self.background_color_button = BackGroundColorButton()
        tool_bar_layout.addWidget(self.background_color_button, alignment=Qt.AlignRight | Qt.AlignVCenter)

        self.control_panel_size_widget = ControlPanelSizeWidget()
        tool_bar_layout.addWidget(self.control_panel_size_widget, alignment=Qt.AlignRight | Qt.AlignVCenter)

        self.clear_button = extra_widgets.ToolIconButton("trash-2")
        tool_bar_layout.addWidget(self.clear_button, alignment=Qt.AlignRight | Qt.AlignVCenter)

        self.central_layout.addLayout(tool_bar_layout)

        # Panel
        # Scroll area
        content_widget = QWidget()
        self.content_layout = QVBoxLayout(content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)
        self.content_layout.setObjectName(content_layout_name)
        scroll_area = QScrollArea()
        scroll_area.setObjectName(scroll_area_name)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setWidget(content_widget)

        # Image label
        self.image_label = QLabel(self._default_image_label, content_widget)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.content_layout.addWidget(self.image_label)

        # Add scroll area
        self.central_layout.addWidget(scroll_area)

        # Setting for the capture
        self.capturing = False
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._capture)

        # Signal & Slot
        self.camera_list_widget.load_camera_signal.connect(self._add_panel)
        self.play_button.clicked.connect(self.run_capture)
        self.clear_button.clicked.connect(self.clear_panels)
        self.control_panel_size_widget.size_up_signal.connect(partial(self.resize_panels, 50))
        self.control_panel_size_widget.size_down_signal.connect(partial(self.resize_panels, -50))
        self.control_panel_size_widget.size_fit_signal.connect(self.fit_panel)

    def _add_panel(self):
        """Add the panel."""
        camera = self.camera_list_widget.get_current_camera()
        if not camera:
            return

        if camera in self.loaded_camera_list:
            cmds.warning(f"Camera already loaded: {camera}")
            return

        if self.play_button.is_play():
            cmds.warning("Stop the capture before loading the camera.")
            return

        panel_layout = cmds.paneLayout(configuration="single", height=self._panel_height, p=self.content_layout.objectName())
        panel = cmds.modelPanel(cam=camera, p=panel_layout)
        cmds.modelEditor(
            modelPanel=panel,
            displayAppearance="smoothShaded",
            allObjects=False,
            polymeshes=True,
            grid=False,
            headsUpDisplay=False,
        )
        cmds.modelPanel(panel, e=True, cam=camera)
        view = omui.M3dView.getM3dViewFromModelPanel(panel)

        self.panel_layout_list.append(panel_layout)
        self.panel_list.append(panel)
        self.loaded_camera_list.append(camera)
        self.view_list.append(view)

        logger.debug(f"Add panel: {panel}")

    def run_capture(self):
        """Run the capture."""
        if self.play_button.is_play():
            self.play_button.stop()
            self.timer.stop()
        else:
            if not self.view_list:
                cmds.warning("No camera loaded.")
                return

            self.image_label.clear()

            self.play_button.run()
            self.timer.start(100)

    def resize_panels(self, size: int):
        """Resize the panels.

        Args:
            size (int): Panel size.
        """
        if self.play_button.is_play():
            cmds.warning("Stop the capture before resizing the panels.")
            return

        if not self.panel_layout_list:
            cmds.warning("No panels to resize.")
            return

        for panel_layout in self.panel_layout_list:
            current_size = cmds.paneLayout(panel_layout, q=True, height=True)
            cmds.paneLayout(panel_layout, e=True, height=current_size + size)

        logger.debug(f"Resized the panels: {size}")

    def fit_panel(self):
        """Fit the panel size to window size."""
        if self.play_button.is_play():
            cmds.warning("Stop the capture before fitting the panels.")
            return

        if not self.panel_layout_list:
            cmds.warning("No panels to fit.")
            return

        label_size = self.image_label.size()
        print(label_size)
        self.resize(label_size)

        # panel = maya_qt.get_qt_control(self.panel_list[0])
        # panel_width = panel.width()
        # panel_height = panel.height()

        # self.resize(panel_width, panel_height)

        logger.debug("Fitted the panels to the window size.")

    def clear_panels(self):
        """Clear the panels."""
        if self.play_button.is_play():
            cmds.warning("Stop the capture before clearing the panels.")
            return

        for panel in self.panel_list:
            if cmds.modelPanel(panel, q=True, exists=True):
                cmds.deleteUI(panel)

                logger.debug(f"Deleted panel: {panel}")

        for panel_layout in self.panel_layout_list:
            if cmds.paneLayout(panel_layout, q=True, exists=True):
                cmds.deleteUI(panel_layout)

                logger.debug(f"Deleted panel layout: {panel_layout}")

        self.panel_layout_list.clear()
        self.panel_list.clear()
        self.loaded_camera_list.clear()
        self.view_list.clear()

        self.image_label.setText(self._default_image_label)

    def _capture(self):
        """Capture the model panels."""
        if self.capturing:
            return

        self.capturing = True

        images = []
        for view in self.view_list:
            image = self._view_to_image(view)
            if image is None:
                self.capturing = False
                return

            images.append(image)

        logger.debug(f"Captured {len(images)} images.")

        pixmap = self._composite_images(images)
        self.image_label.setPixmap(pixmap)

        self.capturing = False

    def _view_to_image(self, view: omui.M3dView) -> QImage:
        """Convert the M3dView to QImage.

        Args:
            view (omui.M3dView): M3dView.

        Returns:
            QImage: QImage.
        """
        try:
            view.refresh(force=True, all=False)
            mImg = om.MImage()
            view.readColorBuffer(mImg, True)
        except Exception as e:
            logger.error(f"Failed to capture the model panel: {e}")
            return None

        width, height = mImg.getSize()
        bytesPerLine = width * 4

        nbytes = width * height * 4
        pixelPtr = mImg.pixels()
        if not pixelPtr:
            logger.error("Failed to get the pixel data.")
            return None

        buffer = (ctypes.c_ubyte * nbytes).from_address(pixelPtr)
        pixelData = bytes(buffer)

        image = QImage(pixelData, width, height, bytesPerLine, QImage.Format_RGBA8888)
        image = image.copy()
        image = image.mirrored(False, True)

        return image

    def _composite_images(self, images: list[QImage]) -> QPixmap:
        """Composite the images.

        Args:
            images (list[QImage]): Images.

        Returns:
            QPixmap: Composite image.
        """
        composite = QImage(images[0].size(), QImage.Format_ARGB32_Premultiplied)
        composite.fill(self.background_color_button.get_color())

        painter = QPainter(composite)
        for image in images:
            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
            painter.drawImage(0, 0, image)
        painter.end()

        return QPixmap.fromImage(composite)

    def _ui_name(self, name) -> str:
        """Get the UI name.

        Args:
            name (str): UI name.

        Returns:
            str: UI name.
        """
        return "{}_{}".format(__name__.replace(".", "_"), name)

    def closeEvent(self, event):
        """Close event."""
        if hasattr(self, "timer") and self.timer.isActive():
            self.timer.stop()
            logger.debug("Stopped the timer.")

        self.clear_panels()

        super().closeEvent(event)


class CameraListWidget(QWidget):
    """Camera list widget."""

    load_camera_signal = Signal(str)

    _ignore_camera_list = ["perspShape", "topShape", "sideShape", "frontShape", "rightShape", "leftShape", "bottomShape"]

    def __init__(self, parent=None):
        """Constructor."""
        super().__init__(parent)

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(1)

        self.camera_box = QComboBox()
        self.camera_box.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)
        layout.addWidget(self.camera_box)

        self.load_button = extra_widgets.ToolIconButton("download")
        layout.addWidget(self.load_button)

        self.reload_button = extra_widgets.ToolIconButton("refresh-cw-2")
        layout.addWidget(self.reload_button)

        self.setLayout(layout)

        # Signal & Slot
        self.load_button.clicked.connect(self._load_camera)
        self.reload_button.clicked.connect(self._reload_camera_list)

        # Initial UI
        self.camera_box.setMinimumWidth(self.camera_box.sizeHint().width() * 2)

    def _set_camera_list(self):
        """Set the camera list."""
        camera_list = cmds.ls(type="camera")
        camera_list = [camera for camera in camera_list if camera not in self._ignore_camera_list]

        if not camera_list:
            cmds.warning("Camera not found.")
            return

        self.camera_box.addItems(camera_list)

        logger.debug(f"Set camera list: {camera_list}")

    def get_current_camera(self) -> str:
        """Get the current camera.

        Returns:
            str: The current camera.
        """
        camera = self.camera_box.currentText()
        if not camera:
            cmds.warning("Camera not selected.")
            return None

        if not cmds.objExists(camera):
            cmds.warning(f"Camera not found: {camera}")
            return None

        return camera

    def _load_camera(self):
        """Load the camera."""
        camera = self.get_current_camera()
        if camera is None:
            return

        self.load_camera_signal.emit(camera)

    def _reload_camera_list(self):
        """Reload the camera list."""
        self.camera_box.clear()
        self._set_camera_list()


class PlayButton(extra_widgets.ToolIconButton):
    """Play and stop button."""

    def __init__(self, parent=None):
        """Constructor."""
        self._play = False

        self.play_icon = QIcon(tool_icons.get_icon_path("play"))
        self.stop_icon = QIcon(tool_icons.get_icon_path("pause"))

        super().__init__(icon_name="play", parent=parent)

    def run(self):
        """Run the capture."""
        self._play = True
        self.setIcon(self.stop_icon)

    def stop(self):
        """Stop the capture."""
        self._play = False
        self.setIcon(self.play_icon)

    def is_play(self) -> bool:
        """Check if the play button is on.

        Returns:
            bool: True if the play button is on.
        """
        return self._play


class BackGroundColorButton(QPushButton):
    """Change the background color button."""

    _default_color = "#000000"

    def __init__(self, parent=None):
        """Constructor."""
        super().__init__(parent)

        self._color = self._default_color

        white_icon_path = tool_icons.get_icon_path("paint-bucket")
        self.write_icon = QIcon(white_icon_path)
        black_icon_path = tool_icons.get_icon_path("paint-bucket-black")
        self.black_icon = QIcon(black_icon_path)

        self.setIcon(self.write_icon)

        style = QApplication.style()
        pm_button_margin = style.PM_ButtonMargin if hasattr(style, "PM_ButtonMargin") else style.PixelMetric.PM_ButtonMargin
        padding = style.pixelMetric(pm_button_margin)

        self.setStyleSheet(f"""
            QPushButton {{
                border: none;
                background-color: {self._color};
                border-radius: 1px;
                text-align: center;
            }}
        """)

        pixmap = QPixmap(white_icon_path)
        size = pixmap.width() + padding
        self.setMinimumSize(size, size)

    def mousePressEvent(self):
        """Mouse press event."""
        color = QColorDialog.getColor(QColor(self._color), None)
        if not color.isValid():
            return

        self.set_color(color)

    def get_color(self) -> str:
        """Get the color.

        Returns:
            str: The color.
        """
        return self._color

    def set_color(self, color: QColor):
        """Set the color.

        Args:
            color (QColor): The color.
        """
        if color.lightnessF() > 0.5:
            self.setIcon(self.black_icon)
        else:
            self.setIcon(self.write_icon)

        self.setStyleSheet(f"""
            QPushButton {{
                border: none;
                background-color: {color.name()};
                border-radius: 1px;
                text-align: center;
            }}
        """)

        self._color = color


class ControlPanelSizeWidget(QWidget):
    """Control panel size widget."""

    size_up_signal = Signal()
    size_down_signal = Signal()
    size_fit_signal = Signal()

    def __init__(self, parent=None):
        """Constructor."""
        super().__init__(parent)

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(1)

        self.size_up_button = extra_widgets.ToolIconButton("square-arrow-up")
        layout.addWidget(self.size_up_button)

        self.size_down_button = extra_widgets.ToolIconButton("square-arrow-down")
        layout.addWidget(self.size_down_button)

        self.size_fit_button = extra_widgets.ToolIconButton("scaling")
        layout.addWidget(self.size_fit_button)

        self.setLayout(layout)

        # Signal & Slot
        self.size_up_button.clicked.connect(self._size_up)
        self.size_down_button.clicked.connect(self._size_down)
        self.size_fit_button.clicked.connect(self._size_fit)

    def _size_up(self):
        """Size up."""
        self.size_up_signal.emit()

    def _size_down(self):
        """Size down."""
        self.size_down_signal.emit()

    def _size_fit(self):
        """Size fit."""
        self.size_fit_signal.emit()


def show_ui():
    """Show the main window."""
    window_name = f"{__name__}MainWindow"
    maya_qt.delete_widget(window_name)

    # Create the main window.
    main_window = MainWindow(parent=maya_qt.get_maya_pointer(), object_name=window_name, window_title="Panel Compositor")
    main_window.show()
