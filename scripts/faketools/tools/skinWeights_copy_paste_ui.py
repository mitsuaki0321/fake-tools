"""
Skin weights copy and paste tool.
"""

from logging import getLogger

from maya.api.OpenMaya import MGlobal
import maya.cmds as cmds

try:
    from PySide2.QtCore import Qt, Signal
    from PySide2.QtGui import QIcon
    from PySide2.QtWidgets import QPushButton, QSlider
except ImportError:
    from PySide6.QtCore import Qt, Signal
    from PySide6.QtGui import QIcon
    from PySide6.QtWidgets import QPushButton, QSlider

from ..command.transfer_weight import SkinWeightsCopyPaste
from ..lib_ui import base_window, maya_qt, maya_ui, tool_icons
from ..lib_ui.widgets import extra_widgets

logger = getLogger(__name__)


class MainWindow(base_window.BaseMainWindow):
    def __init__(self, parent=None, object_name="MainWindow", window_title="Main Window"):
        """Constructor.

        Args:
            parent (QWidget, optional): The parent widget. Defaults to None.
            window_title (str, optional): The window title. Defaults to 'Main Window'.
        """
        super().__init__(parent=parent, object_name=object_name, window_title=window_title, central_layout="horizontal")

        self.skinWeights_copy_paste = SkinWeightsCopyPaste()
        self.is_value_changed = False
        self.is_use_select_pref = False  # Save the preference by user for trackSelectionOrder

        # Method button
        self.method_toggle_button = MethodButton(self.skinWeights_copy_paste)
        self.central_layout.addWidget(self.method_toggle_button)

        separator = extra_widgets.VerticalSeparator()
        self.central_layout.addWidget(separator)

        # Clipboard buttons
        self.src_clipboard_button = SourceClipboardButton(self.skinWeights_copy_paste)
        self.central_layout.addWidget(self.src_clipboard_button)

        self.dst_clipboard_button = DestinationClipboardButton(self.skinWeights_copy_paste)
        self.central_layout.addWidget(self.dst_clipboard_button)

        separator = extra_widgets.VerticalSeparator()
        self.central_layout.addWidget(separator)

        # Paste button
        self.paste_button = extra_widgets.ToolIconButton("clipboard-paste")
        self.paste_button.setEnabled(False)
        self.central_layout.addWidget(self.paste_button)

        # Blend field, slider
        self.blend_spin_box = extra_widgets.ModifierSpinBox()
        self.blend_spin_box.setRange(0.0, 1.0)
        self.blend_spin_box.setSingleStep(0.01)
        self.blend_spin_box.setFixedWidth(self.blend_spin_box.sizeHint().width() * 1.2)
        self.blend_spin_box.setEnabled(False)
        blend_line_edit = self.blend_spin_box.lineEdit()
        blend_line_edit.setReadOnly(True)
        self.central_layout.addWidget(self.blend_spin_box)

        self.blend_slider = QSlider(Qt.Horizontal)
        self.blend_slider.setRange(0, 100)
        self.blend_slider.setEnabled(False)
        self.central_layout.addWidget(self.blend_slider, stretch=1)

        # Rearrange the method button
        self.method_toggle_button.setMinimumHeight(self.blend_spin_box.sizeHint().height())

        # Signal & Slot
        self.src_clipboard_button.clear_clipboard_signal.connect(self.dst_clipboard_button.clear_clipboard)
        self.dst_clipboard_button.stock_clipboard_signal.connect(self.__set_destination_clipboard)
        self.dst_clipboard_button.clear_clipboard_signal.connect(self.__clear_destination_clipboard)

        self.blend_spin_box.valueChanged.connect(self.__update_field_slider)
        self.blend_slider.valueChanged.connect(self.__update_field_slider)

        self.blend_spin_box.valueChanged.connect(self.__change_spin_box_value)

        self.blend_slider.valueChanged.connect(self.__on_slider_value_changed)
        self.blend_slider.sliderReleased.connect(self.__on_slider_released)

        self.paste_button.clicked.connect(self.__paste_skinWeights)

        # Initialize the UI.
        margins = base_window.get_margins(self.central_widget)
        self.central_layout.setContentsMargins(*[margin * 0.5 for margin in margins])

        minimum_size_hint = self.minimumSizeHint()
        size_hint = self.sizeHint()
        self.resize(size_hint.width() * 1.2, minimum_size_hint.height())

    def __on_slider_value_changed(self):
        """Slot for the slider value changed."""
        if not self.is_value_changed:
            cmds.undoInfo(openChunk=True)
            self.is_value_changed = True

        try:
            self.__paste_skinWeights_blend()
        except Exception as e:
            MGlobal.displayError(str(e))

            self.is_value_changed = False

    def __on_slider_released(self):
        """Slot for the slider released."""
        if self.is_value_changed:
            cmds.undoInfo(closeChunk=True)
            self.is_value_changed = False

    @maya_ui.undo_chunk("Skin Weights Copy Paste")
    @maya_ui.error_handler
    def __change_spin_box_value(self):
        """Change the spin box value."""
        self.__paste_skinWeights_blend()

    def __paste_skinWeights_blend(self):
        """paste the skin weights."""
        self.skinWeights_copy_paste.set_blend_weights(self.blend_slider.value() / 100.0)
        self.skinWeights_copy_paste.paste_skinWeights()

    @maya_ui.undo_chunk("Skin Weights Copy Paste")
    @maya_ui.error_handler
    def __paste_skinWeights(self):
        """Paste the skin weights."""
        self.blend_spin_box.setValue(1.0)
        self.blend_slider.setValue(100)

    def __update_field_slider(self, value):
        """Update the field and slider."""
        sender = self.sender()
        if sender == self.blend_spin_box:
            self.blend_slider.blockSignals(True)
            self.blend_slider.setValue(value * 100)
            self.blend_slider.blockSignals(False)
        else:
            self.blend_spin_box.blockSignals(True)
            self.blend_spin_box.setValue(value)
            self.blend_spin_box.blockSignals(False)

    def __clear_destination_clipboard(self):
        """Clear the destination clipboard."""
        self.blend_spin_box.setEnabled(False)
        self.blend_slider.setEnabled(False)
        self.paste_button.setEnabled(False)

        self.blend_spin_box.blockSignals(True)
        self.blend_slider.blockSignals(True)

        self.blend_spin_box.setValue(0.0)
        self.blend_slider.setValue(0)

        self.blend_spin_box.blockSignals(False)
        self.blend_slider.blockSignals(False)

    def __set_destination_clipboard(self):
        """Set the destination clipboard."""
        self.blend_spin_box.setEnabled(True)
        self.blend_slider.setEnabled(True)
        self.paste_button.setEnabled(True)

        self.blend_spin_box.blockSignals(True)
        self.blend_slider.blockSignals(True)

        self.blend_spin_box.setValue(0.0)
        self.blend_slider.setValue(0)

        self.blend_spin_box.blockSignals(False)
        self.blend_slider.blockSignals(False)

    def showEvent(self, event):
        """Show event."""
        # Settings for trackSelectionOrder
        self.is_use_select_pref = cmds.selectPref(q=True, trackSelectionOrder=True)
        if not self.is_use_select_pref:
            cmds.selectPref(trackSelectionOrder=True)

        super().showEvent(event)

    def closeEvent(self, event):
        """Close event."""
        # Restore the settings for trackSelectionOrder
        if not self.is_use_select_pref:
            cmds.selectPref(trackSelectionOrder=False)

        super().closeEvent(event)


class MethodButton(QPushButton):
    """This button is used to toggle the method for SkinWeightsCopyPaste."""

    def __init__(self, skinWeights_copy_paste: SkinWeightsCopyPaste, parent=None):
        """Initializer.

        Args:
            skinWeights_copy_paste (SkinWeightsCopyPaste): SkinWeightsCopyPaste instance.
        """
        super().__init__(parent=parent)

        if not isinstance(skinWeights_copy_paste, SkinWeightsCopyPaste):
            raise ValueError("Invalid skinWeights_copy_paste.")
        self.__skinWeights_copy_paste = skinWeights_copy_paste

        self.method_label_map = {"oneToAll": "1:N", "oneToOne": "1:1"}

        self.setText(self.method_label_map[self.__skinWeights_copy_paste.method])

        minimum_size_hint = self.minimumSizeHint()
        self.setMinimumWidth(minimum_size_hint.width() * 1.2)

        self.clicked.connect(self.toggle_method)

    @maya_ui.error_handler
    def toggle_method(self):
        """Toggle the method."""
        if self.__skinWeights_copy_paste.method == "oneToAll":
            self.__skinWeights_copy_paste.set_method("oneToOne")
        elif self.__skinWeights_copy_paste.method == "oneToOne":
            self.__skinWeights_copy_paste.set_method("oneToAll")

        self.setText(self.method_label_map[self.__skinWeights_copy_paste.method])


class SourceClipboardButton(extra_widgets.ToolIconButton):
    """This button is used to stock the source components for SkinWeightsCopyPaste."""

    clear_clipboard_signal = Signal()

    def __init__(self, skinWeights_copy_paste: SkinWeightsCopyPaste, parent=None):
        """Initializer.

        Args:
            skinWeights_copy_paste (SkinWeightsCopyPaste): SkinWeightsCopyPaste instance.
        """
        super().__init__(parent=parent, icon_name="clipboard")

        if not isinstance(skinWeights_copy_paste, SkinWeightsCopyPaste):
            raise ValueError("Invalid skinWeights_copy_paste.")

        self.__skinWeights_copy_paste = skinWeights_copy_paste
        self.__select_icon = QIcon(tool_icons.get_icon_path("clipboard"))
        self.__selected_icon = QIcon(tool_icons.get_icon_path("clipboard-list"))

        self.setText("0")
        self.setIcon(self.__select_icon)

        minimum_size_hint = self.minimumSizeHint()
        self.setMinimumWidth(minimum_size_hint.width() * 1.2)

        self.clicked.connect(self.stock_clipborad)

    @maya_ui.error_handler
    def stock_clipborad(self):
        """Stock the clipboard."""
        sel_objs = cmds.ls(sl=True)
        if not sel_objs:
            self.setText("0")
            self.setIcon(self.__select_icon)

            self.__skinWeights_copy_paste.clear_src_components()
            self.clear_clipboard_signal.emit()

            cmds.warning("Clear the source components.")
            return

        sel_components = cmds.ls(orderedSelection=True, flatten=True)
        filter_components = cmds.filterExpand(sel_components, ex=True, sm=[28, 31, 46])
        if len(sel_components) != len(filter_components):
            cmds.error("Invalid components or objects selected.")

        try:
            self.__skinWeights_copy_paste.set_src_components(sel_components)
            self.setText(str(len(sel_components)))
            self.setIcon(self.__selected_icon)

            self.clear_clipboard_signal.emit()
        except Exception as e:
            cmds.error(str(e))


class DestinationClipboardButton(extra_widgets.ToolIconButton):
    """This button is used to stock the destination components for SkinWeightsCopyPaste."""

    stock_clipboard_signal = Signal()
    clear_clipboard_signal = Signal()

    def __init__(self, skinWeights_copy_paste: SkinWeightsCopyPaste, parent=None):
        """Initializer.

        Args:
            skinWeights_copy_paste (SkinWeightsCopyPaste): SkinWeightsCopyPaste instance.
        """
        super().__init__(parent=parent, icon_name="square-dashed-mouse-pointer")

        if not isinstance(skinWeights_copy_paste, SkinWeightsCopyPaste):
            raise ValueError("Invalid skinWeights_copy_paste.")

        self.__skinWeights_copy_paste = skinWeights_copy_paste
        self.__select_icon = QIcon(tool_icons.get_icon_path("square-dashed-mouse-pointer"))
        self.__selected_icon = QIcon(tool_icons.get_icon_path("square-mouse-pointer"))

        self.setText("0")
        self.setIcon(self.__select_icon)

        minimum_size_hint = self.minimumSizeHint()
        self.setMinimumWidth(minimum_size_hint.width() * 1.2)

        self.clicked.connect(self.stock_clipborad)

    @maya_ui.error_handler
    def stock_clipborad(self):
        """Stock the clipboard."""
        sel_objs = cmds.ls(sl=True)
        if not sel_objs:
            self.setText("0")
            self.setIcon(self.__select_icon)

            self.__skinWeights_copy_paste.clear_dst_components()
            self.clear_clipboard_signal.emit()

            cmds.warning("Clear the destination components.")
            return

        sel_components = cmds.ls(orderedSelection=True, flatten=True)
        filter_components = cmds.filterExpand(sel_components, ex=True, sm=[28, 31, 46])
        if len(sel_components) != len(filter_components):
            cmds.error("Invalid components or objects selected.")

        try:
            self.__skinWeights_copy_paste.set_dst_components(sel_components)
            self.setText(str(len(sel_components)))
            self.setIcon(self.__selected_icon)
        except Exception as e:
            cmds.error(str(e))

        self.stock_clipboard_signal.emit()

    def clear_clipboard(self):
        """Clear the clipboard."""
        self.setText("0")
        self.setIcon(self.__select_icon)

        self.clear_clipboard_signal.emit()

        logger.debug("Clear the destination components.")


def show_ui():
    """Show the main window."""
    window_name = f"{__name__}MainWindow"
    maya_qt.delete_widget(window_name)

    # Create the main window.
    main_window = MainWindow(parent=maya_qt.get_maya_pointer(), object_name=window_name, window_title="Skin Weights Copy Paste")
    main_window.show()
