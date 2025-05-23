import logging
from typing import *

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap, QCursor
from PyQt6.QtWidgets import QVBoxLayout, QPushButton, QHBoxLayout, QLabel, QSpacerItem, QSizePolicy, QGraphicsOpacityEffect

from src.data.button_functions import ButtonFunctions
from src.data.config import CONFIG
from src.data.font_styles import FontStyle
from src.gui.elements.scrolling_text_label import ScrollingLabel
from src.utils.functions_utils import close_window_by_handle, launch_app, focus_window_by_handle
from src.utils.icon_utils import invert_icon
from src.utils.program_utils import main_window_hide, main_window_force_refresh

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from src.gui.menus.pie_menu import PieMenu

NO_HWND_ASSIGNED = -1
PROGRAM_NOT_YET_REGISTERED = -1
READY_TO_OPEN_PROGRAM = 0


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

        logger.debug(f"Initializing PieButton: {object_name}, Index: {index}")

        self.setObjectName(object_name)
        self.index: int = index
        self.text_1: str = text_1
        self.text_2: str = text_2
        self.icon_path: str = icon_path
        self.windowHandle: int = -1

        self.button_type = "normal_pie_button"

        self.pie_menu_parent: "PieMenu" = parent

        # Store actions for each mouse button
        self.left_click_action = None
        self.right_click_action = None
        self.middle_click_action = None

        self.opacity_effect = QGraphicsOpacityEffect()
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(0.0)

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

        self.update_icon(self.icon_path)

        # Add the VBoxLayout as a pie_menu of the HBoxLayout
        self.layout().addLayout(self.label_layout)

        # Set position if provided
        x, y = pos
        # Set position using `move()`, not `setGeometry()`
        self.move(x, y)

        self.set_right_click_action(action=lambda: main_window_hide())

    def print_button_type(self):
        # print(f"I am {self.button_type} {self.index}")
        pass

    def default_action(self):
        """Default action when no external action is provided."""
        print(f"There was only the default action assigned for {self.objectName()}")

    def update_button(self, properties: dict) -> None:
        """Update the whole button UI and functionality"""
        button_text_1 = properties["window_title"]
        window_handle = properties["window_handle"]
        button_text_2 = properties["app_name"]
        app_icon_path = properties["app_icon_path"]

        if window_handle == NO_HWND_ASSIGNED:
            self.clear()
            return

        # Update button text and icon
        self._update_ui(button_text_1, button_text_2, app_icon_path)

        # check if there's anything to update
        if self.windowHandle == window_handle:
            return

        self.windowHandle = window_handle

        # Handle window actions
        self.set_left_click_action(
            lambda hwnd=window_handle: (
                main_window_hide(),
                QTimer.singleShot(0, lambda: focus_window_by_handle(hwnd)),
            )
        )
        self.set_middle_click_action(
            lambda hwnd=window_handle: (
                QTimer.singleShot(0, lambda: close_window_by_handle(hwnd)),
                QTimer.singleShot(100, lambda: main_window_force_refresh()),
            )
        )
        self.setEnabled(True)

    def clear(self, button_text_2=""):
        # Disable the button
        self.set_left_click_action(action=None)
        self.set_middle_click_action(action=None)
        self.setEnabled(False)  # Disable the button

        self._update_ui("Empty", "", "")

    def _update_ui(self, text_1: str, text_2: str, app_icon_path=None, is_invert_icon=False) -> None:
        # Update label 1 text if it's different
        if self.text_1 != text_1:
            self._set_label_1_text(text_1)
            self.text_1 = text_1  # Store the updated value

        # Update label 2 text if it's different
        if self.text_2 != text_2:
            self._set_label_2_text(text_2)
            self.text_2 = text_2  # Store the updated value

        # Update icon if it's different
        if self.icon_path != app_icon_path:
            self.update_icon(app_icon_path, is_invert_icon)
            self.icon_path = app_icon_path  # Store the updated value

    def _set_label_1_text(self, text: str):
        """Change the text of label_1 from outside."""
        self.label_1.update_text(text)
        if not hasattr(self, 'label_2'):
            self.label_1.update_v_offset(1)

    def _set_label_2_text(self, text: str):
        """Change the text of label_2 from outside."""
        if text:  # If text is not empty or None
            self.label_1.update_v_offset(-1)
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
            logger.debug(f"Left-click action not set for button: {self.objectName()}")

    def trigger_right_click_action(self):
        """Trigger the right-click action."""
        if self.right_click_action:
            self.right_click_action()
        else:
            logger.debug(f"Right-click action not set for button: {self.objectName()}")

    def trigger_middle_click_action(self):
        """Trigger the middle-click action."""
        if self.middle_click_action:
            self.middle_click_action()
        else:
            logger.debug(f"Middle-click action not set for button: {self.objectName()}")

    def enterEvent(self, event):
        logger.debug(f"Mouse entered button: {self.objectName()}")
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))  # Change cursor on hover

    def leaveEvent(self, event):
        logger.debug(f"Mouse left button: {self.objectName()}")
        self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))  # Restore default cursor

    def update_hover_state(self, hovered):
        self.setProperty("hovered", hovered)
        self.style().unpolish(self)
        self.style().polish(self)


class ShowAnyWindowPieButton(PieButton):
    """Primary Button with customized actions or behavior."""

    def __init__(self, *args, **kwargs):
        # Pass all arguments to the parent class constructor
        super().__init__(*args, **kwargs)

        self.setObjectName("show_any_window_button")
        self.button_type = "show_any_window"

        self.print_button_type()


class ShowProgramWindowPieButton(PieButton):
    """Primary Button with customized actions or behavior."""

    def __init__(self, *args, **kwargs):
        # Pass all arguments to the parent class constructor
        super().__init__(*args, **kwargs)

        self.setObjectName("show_program_window_button")
        self.button_type = "show_program_window"

        self.print_button_type()

    def update_button(self, properties: dict) -> None:
        button_text_1 = properties["window_title"]
        window_handle = properties["window_handle"]
        exe_path = properties["exe_path"]
        button_text_2 = properties["app_name"]
        app_icon_path = properties["app_icon_path"]

        if window_handle == PROGRAM_NOT_YET_REGISTERED:
            self.clear(button_text_2)
            return

        # Handle reserved button actions that have no open window
        if window_handle == READY_TO_OPEN_PROGRAM:
            if exe_path:
                self.set_left_click_action(
                    lambda captured_exe_path=exe_path: (
                        main_window_hide(),
                        QTimer.singleShot(0, lambda: launch_app(captured_exe_path)),
                    )
                )
            button_text_1 = ""
            self._update_ui(button_text_1, button_text_2, app_icon_path)
            return

        # Update button text and icon
        self._update_ui(button_text_1, button_text_2, app_icon_path)

        # check if there's anything to update
        if self.windowHandle == window_handle:
            return

        self.windowHandle = window_handle

        # Handle window actions
        self.set_left_click_action(
            lambda hwnd=window_handle: (
                main_window_hide(),
                QTimer.singleShot(0, lambda: focus_window_by_handle(hwnd)),
            )
        )
        self.set_middle_click_action(
            lambda hwnd=window_handle: (
                QTimer.singleShot(0, lambda: close_window_by_handle(hwnd)),
                QTimer.singleShot(100, lambda: main_window_force_refresh()),
            )
        )
        self.setEnabled(True)

    def clear(self, button_text_2=""):
        # Disable the button
        self.set_left_click_action(action=None)
        self.set_middle_click_action(action=None)
        self.setEnabled(False)  # Disable the button

        self._update_ui("Not launched yet.", button_text_2, "")


class LaunchProgramPieButton(PieButton):
    """Primary Button with customized actions or behavior."""

    def __init__(self, *args, **kwargs):
        # Pass all arguments to the parent class constructor
        super().__init__(*args, **kwargs)

        self.setObjectName("launch_program_button")
        self.button_type = "launch_program"

        self.print_button_type()

        self.exe_path: str = ""

    def update_button(self, properties: dict) -> None:
        button_text_2 = "- Launch -"
        exe_path = properties["exe_path"]
        button_text_1 = properties["app_name"]
        app_icon_path = properties["app_icon_path"]

        # Update button text and icon
        self._update_ui(button_text_1, button_text_2, app_icon_path)

        # check if there's anything to update
        if self.exe_path == exe_path or not exe_path:
            return

        self.exe_path = exe_path

        self.set_left_click_action(
            lambda captured_exe_path=exe_path: (
                main_window_hide(),
                QTimer.singleShot(0, lambda: launch_app(captured_exe_path)),
            )
        )

        # self.set_middle_click_action()
        self.setEnabled(True)


class CallFunctionPieButton(PieButton):
    """Primary Button with customized actions or behavior."""

    def __init__(self, *args, **kwargs):
        # Pass all arguments to the parent class constructor
        super().__init__(*args, **kwargs)

        self.setObjectName("call_function_button")
        self.button_type = "call_function"

        self.button_functions = ButtonFunctions()

        self.print_button_type()

    def update_button(self, properties: dict) -> None:
        function_metadata = self.button_functions.get_function(properties["function_name"])

        # Access the text, icon, and action
        button_text_1 = function_metadata["text_1"]
        button_text_2 = ""
        app_icon_path = function_metadata["icon"]

        if button_text_1 == "":
            self.clear()
            return

        self._update_ui(button_text_1, button_text_2, app_icon_path, is_invert_icon=True)

        # Define the left-click action, which will invoke the wrapped function
        left_click_action = lambda: function_metadata["action"]()

        # Handle window actions
        self.set_left_click_action(
            lambda: (
                main_window_hide(),  # Hide the window first
                QTimer.singleShot(0, left_click_action)  # Schedule the action
            )
        )

        # self.set_middle_click_action()
        self.setEnabled(True)


BUTTON_TYPES: dict[str, Type[PieButton]] = {
    "show_any_window": ShowAnyWindowPieButton,
    "show_program_window": ShowProgramWindowPieButton,
    "launch_program": LaunchProgramPieButton,
    "call_function": CallFunctionPieButton,
}
