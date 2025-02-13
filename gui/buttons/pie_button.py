from typing import *

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap, QCursor
from PyQt6.QtWidgets import QVBoxLayout, QPushButton, QHBoxLayout, QLabel, QSpacerItem, QSizePolicy

from data.config import CONFIG
from data.font_styles import FontStyle
from gui.elements.scrolling_text_label import ScrollingLabel
from utils.icon_utils import invert_icon
from utils.window_utils import load_cache, launch_app, focus_window_by_handle, close_window_by_handle

if TYPE_CHECKING:
    from gui.pie_window import PieWindow
    from gui.menus.pie_menu import PieMenu


class PieButton(QPushButton):
    """Custom Button with text animation for long text."""

    def __init__(self,
                 object_name: str,
                 index: int,
                 text_1: str = "Empty",
                 text_2: str = "",
                 icon_path: str = "",
                 pos: Tuple[int, int] = (0, 0),
                 parent: Optional["PieMenu"] = None
                 ):
        super().__init__(parent)

        self.setObjectName(object_name)
        self.index = index
        self.text_1 = text_1
        self.text_2 = text_2

        self.pie_menu_parent: "PieMenu" = parent
        self.main_window: "PieWindow" = cast("PieWindow", self.pie_menu_parent.parent())

        # Store actions for each mouse button
        self.left_click_action = None
        self.right_click_action = None
        self.middle_click_action = None

        self.hovered = False
        # Create a QVBoxLayout for the label
        self.label_layout = QVBoxLayout()
        # self.label_layout.setSpacing(0)  # No space between widgets

        # Create a Label (which is on top, when both texts are set
        self.label_1 = ScrollingLabel(self.text_1, h_align=Qt.AlignmentFlag.AlignLeft, font_style=FontStyle.Normal, v_offset=-1)
        self.label_1.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        self.label_layout.addWidget(self.label_1)
        self.label_layout.setContentsMargins(0, 0, 0, 0)

        # Create a second bottom label if text_2 is set
        self._set_label_2_text("")

        # Create the main layout for the button (HBoxLayout)
        self.setLayout(QHBoxLayout())

        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(0)  # Set minimal spacing between widgets

        self.update_icon(icon_path)

        # Add the VBoxLayout as a pie_menu of the HBoxLayout
        self.layout().addLayout(self.label_layout)

        # Set position if provided
        x, y = pos
        # Set position using `move()`, not `setGeometry()`
        self.move(x, y)

    def default_action(self):
        """Default action when no external action is provided."""
        print(f"There was only the default action assigned for {self.objectName()}")

    def update_button(self, properties: dict) -> None:
        app_info_cache = load_cache()

        button_text_1 = properties["text_1"]
        button_text_2 = properties["text_2"]
        window_handle = properties["window_handle"]
        app_icon_path = properties["app_icon_path"]
        exe_name = properties["exe_name"]

        # Update button text and icon
        self._update_ui(button_text_1, button_text_2, app_icon_path)

        # Disconnect any previous connections
        try:
            self.clicked.disconnect()
        except TypeError:
            pass  # No connections to disconnect

        # Handle reserved button actions that have no open window
        if window_handle == 0:
            exe_path = app_info_cache.get(exe_name, {}).get("exe_path")
            if exe_path:
                self.set_left_click_action(
                    lambda captured_exe_path=exe_path: (
                        self.main_window.hide(),
                        QTimer.singleShot(0, lambda: launch_app(captured_exe_path)),
                    )
                )
            return

        # Handle window actions
        self.set_left_click_action(
            lambda hwnd=window_handle: (
                self.main_window.hide(),
                QTimer.singleShot(0, lambda: focus_window_by_handle(hwnd)),
            )
        )
        self.set_middle_click_action(
            lambda hwnd=window_handle: (
                QTimer.singleShot(0, lambda: close_window_by_handle(hwnd)),
                QTimer.singleShot(100, lambda: self.main_window.auto_refresh()),
            )
        )
        self.setEnabled(True)



    def clear(self):
        # Disable the button
        self.set_left_click_action(action=None)
        self.set_middle_click_action(action=None)
        self.setEnabled(False)  # Disable the button

        self._update_ui("Empty", "", "")

    def _update_ui(self, text_1: str, text_2: str, app_icon_path=None, is_invert_icon=False) -> None:
        self._set_label_1_text(text_1)
        self._set_label_2_text(text_2)
        self.update_icon(app_icon_path, is_invert_icon)

    def _set_label_1_text(self, text: str):
        """Change the text of label_1 from outside."""
        self.label_1.update_text(text)

    def _set_label_2_text(self, text: str):
        """Change the text of label_2 from outside."""
        if text:  # If text is not empty or None
            if hasattr(self, 'label_2'):  # Check if label_2 already exists
                self.label_2.update_text(text)
            else:
                # Create label_2 dynamically
                self.label_2 = ScrollingLabel(text, h_align=Qt.AlignmentFlag.AlignLeft, font_style=FontStyle.Italic, v_offset=1,
                                              font_size=10)
                self.label_2.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

                # Add label_2 to the layout
                self.label_layout.addWidget(self.label_2)

                # Force layout to update
                self.label_layout.update()
        else:  # If text is empty or None, remove label_2
            if hasattr(self, 'label_2'):
                # Remove label_2 from the layout
                self.label_layout.removeWidget(self.label_2)
                self.label_2.deleteLater()  # Safely delete the widget
                del self.label_2  # Delete the attribute to avoid future references

    def update_icon(self, app_icon_path=None, is_invert_icon=False):
        """Add or remove an icon and spacer in the given layout based on the provided icon path."""
        # Remove existing icon and spacer if present
        existing_spacer = None
        existing_icon_label = None

        # Iterate through layout items to find existing spacer or icon label
        for i in range(self.layout().count()):
            item = self.layout().itemAt(i)
            widget = item.widget()
            if isinstance(widget, QLabel):  # Check for QLabel
                existing_icon_label = widget
            elif isinstance(item, QSpacerItem):  # Check for spacer
                existing_spacer = item

        # Remove existing icon label
        if existing_icon_label:
            self.layout().removeWidget(existing_icon_label)
            existing_icon_label.deleteLater()

        # Remove existing spacer
        if existing_spacer:
            self.layout().removeItem(existing_spacer)

        # Add new icon and spacer if an icon path is provided
        if app_icon_path:
            spacer = QSpacerItem(CONFIG.INTERNAL_PIE_TEXT_LABEL_MARGINS, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
            self.layout().insertItem(0, spacer)

            # Load the icon from the file path
            icon = QPixmap(app_icon_path)

            # Check if the icon is valid
            if not icon.isNull():
                # Optionally invert the icon
                if is_invert_icon:
                    icon = invert_icon(icon, return_pixmap=True)

                icon_label = QLabel()
                # Determine scale factor dynamically
                logical_size = 16  # Default logical size (adjust based on use case)
                actual_size = icon.width()  # Use the actual image width

                scale_factor = actual_size / logical_size  # Compute scale factor
                icon.setDevicePixelRatio(scale_factor)  # Apply dynamic scaling

                icon_label.setPixmap(icon)

                # Keep logical size at 16x16, but allow Qt to scale it for high-DPI screens
                icon_label.setFixedSize(16, CONFIG.INTERNAL_BUTTON_HEIGHT)

                icon_label.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
                icon_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

                self.layout().insertWidget(1, icon_label)

    def set_left_click_action(self, action):
        """Set the action for left-click."""
        self.left_click_action = action

    def set_right_click_action(self, action):
        """Set the action for right-click."""
        self.right_click_action = action

    def set_middle_click_action(self, action):
        """Set the action for middle-click."""
        self.middle_click_action = action

    def trigger_left_click_action(self):
        """Trigger the left-click action."""
        if self.left_click_action:
            self.left_click_action()
        else:
            print(f"Left-click action has not been set for button: {self.objectName()}")

    def trigger_right_click_action(self):
        """Trigger the right-click action."""
        if self.right_click_action:
            self.right_click_action()
        else:
            print(f"Right-click action has not been set for button: {self.objectName()}")

    def trigger_middle_click_action(self):
        """Trigger the middle-click action."""
        if self.middle_click_action:
            self.middle_click_action()
        else:
            print(f"Middle-click action has not been set for button: {self.objectName()}")

    def enterEvent(self, event):
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))  # Change cursor on hover

    def leaveEvent(self, event):
        self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))  # Restore default cursor

    def update_hover_state(self, hovered):
        self.setProperty("hovered", hovered)
        self.style().unpolish(self)
        self.style().polish(self)
