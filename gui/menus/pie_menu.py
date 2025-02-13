import math
from typing import TYPE_CHECKING, Optional

from PyQt6.QtCore import Qt, QPropertyAnimation, QRect, QEasingCurve, QSize, pyqtSignal, pyqtSlot, QTimer
from PyQt6.QtGui import QPainter
from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QWidget, QPushButton, QGraphicsOpacityEffect

from data.config import CONFIG
from gui.buttons.area_button import AreaButton
from gui.buttons.expanded_button import ExpandedButton
from gui.buttons.pie_button import PieButton
from gui.buttons.pie_menu_middle_button import PieMenuMiddleButton
from gui.elements.svg_indicator_button import SVGIndicatorButton
from utils.window_utils import load_cache, launch_app, focus_window_by_handle, close_window_by_handle

if TYPE_CHECKING:
    from gui.pie_window import PieWindow


class PieMenu(QWidget):
    update_buttons_signal = pyqtSignal(list)

    def __init__(self, pie_menu_index: int, obj_name: str = "", parent: 'PieWindow' = None):
        super().__init__(parent)

        # Initialize these attributes BEFORE calling setup methods
        self.pie_menu_index: int = pie_menu_index
        self.obj_name: str = obj_name
        self.pie_window: 'PieWindow' = parent
        self.indicator: Optional[SVGIndicatorButton] = None
        self.scene = None
        self.view = None
        self.btn = None
        self.pie_buttons: dict[int, PieButton] = {}
        self.animations = []

        self.hotkey = CONFIG.HOTKEY_PRIMARY

        self.middle_button: Optional[ExpandedButton] = None
        self.area_button: Optional[AreaButton] = None

        self.update_buttons_signal.connect(self.update_button_ui)

        self.setup_window()  # Configure main_window properties
        # Create scene and graphical elements
        self.setup_scene_and_view()
        # Create all buttons (task and main_window controls)
        self.setup_ui()

    def setup_window(self):
        """Set up the main main_window properties."""
        # Non-resizable main_window
        self.setFixedSize(CONFIG.INTERNAL_RADIUS * 2 + CONFIG.INTERNAL_BUTTON_WIDTH * 2,
                          CONFIG.INTERNAL_RADIUS * 2 + CONFIG.INTERNAL_BUTTON_HEIGHT * 2)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)

    def setup_scene_and_view(self):
        """Set up the scene and graphical elements."""
        self.scene = QGraphicsScene(self)
        self.view = QGraphicsView(self.scene, self)
        self.view.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        self.view.setGeometry(0, 0, self.width(), self.height())
        self.view.setObjectName(self.obj_name)
        self.view.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

    def setup_ui(self):
        """Create and position all buttons."""
        self.indicator = SVGIndicatorButton(
            object_name="Indicator",
            size=300,
            pos=(self.rect().center().x(), self.rect().center().y()),
            parent=self
        )

        # Create and configure the refresh button
        self.middle_button = PieMenuMiddleButton(
            text="",
            object_name="middleButton",
            pos=(self.width() // 2 - CONFIG.INTERNAL_INNER_RADIUS, self.height() // 2 - CONFIG.INTERNAL_INNER_RADIUS),
            parent=self
        )

        # Creates the area button that has the screen spanning pie sections
        self.area_button = AreaButton("Slice!",
                                      pos=(self.width() // 2, self.height() // 2),
                                      parent=self)
        # Make the actual button click-through
        self.area_button.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        self.create_pie_buttons()

    def create_pie_buttons(self):
        """Create pie menu buttons in a circular pattern."""
        # Define all the CONFIG variables at the start
        num_buttons = CONFIG.INTERNAL_NUM_BUTTONS_IN_PIE_MENU
        button_width = CONFIG.INTERNAL_BUTTON_WIDTH
        button_height = CONFIG.INTERNAL_BUTTON_HEIGHT
        radius = CONFIG.INTERNAL_RADIUS

        # Define the nudge values
        nudge_x = button_width / 2 - button_height / 2
        nudge_y = button_height / 2

        for i in range(num_buttons):
            angle_in_rad = math.radians(i / num_buttons * 360)  # Calculate button's position using angle_in_radians

            # the base offset moves the anchor point from top left to center
            offset_x = -button_width / 2
            offset_y = button_height / 2

            # Apply nudges for specific button positions
            if i == 1:  # 45 degrees
                offset_x += nudge_x
                offset_y += -nudge_y
            elif i == 2:  # 90 degrees
                offset_x += nudge_x
                offset_y += 0
            elif i == 3:  # 135 degrees
                offset_x += nudge_x
                offset_y += nudge_y
            elif i == 5:  # 225 degrees
                offset_x += -nudge_x
                offset_y += nudge_y
            elif i == 6:  # 270 degrees
                offset_x += -nudge_x
                offset_y += 0
            elif i == 7:  # 315 degrees
                offset_x += -nudge_x
                offset_y += -nudge_y

            # Distribute the buttons in a circle
            button_pos_x = int(self.width() / 2 + offset_x + radius * math.sin(angle_in_rad))
            button_pos_y = int(self.height() / 2 - offset_y - radius * math.cos(angle_in_rad))

            button_name = "Pie_Button" + str(i)  # name of the button not used
            button_index = CONFIG.INTERNAL_NUM_BUTTONS_IN_PIE_MENU * self.pie_menu_index + i

            self.btn = PieButton(button_name, button_index, pos=(button_pos_x, button_pos_y), parent=self)

            self.pie_buttons[i] = self.btn

    def showEvent(self, event):
        super().showEvent(event)  # Call the parent class's method
        for button in self.pie_buttons.values():
            self.animate_button(button, button.geometry())

    def animate_button(self, button: QPushButton, rect: QRect):

        # Apply a QGraphicsOpacityEffect to the button to control its opacity
        opacity_effect = QGraphicsOpacityEffect()
        button.setGraphicsEffect(opacity_effect)

        duration = 100

        # Position animation
        pos_animation = QPropertyAnimation(button, b"pos")
        pos_animation.setDuration(duration)  # Duration in milliseconds
        pos_animation.setStartValue(self.rect().center())  # Initial position
        pos_animation.setEndValue(rect.topLeft())  # Final position
        pos_animation.setEasingCurve(QEasingCurve.Type.OutCirc)  # Easing curve for position

        # Size animation
        size_animation = QPropertyAnimation(button, b"size")
        size_animation.setDuration(duration)  # Duration in milliseconds
        size_animation.setStartValue(QSize(CONFIG.INTERNAL_BUTTON_WIDTH // 4, CONFIG.INTERNAL_BUTTON_HEIGHT // 4))  # Initial size (small)
        size_animation.setEndValue(QSize(CONFIG.INTERNAL_BUTTON_WIDTH, CONFIG.INTERNAL_BUTTON_HEIGHT))  # Final size (target size)
        size_animation.setEasingCurve(QEasingCurve.Type.OutCurve)  # Easing curve for size

        # Opacity animation to fade in/out the button
        opacity_animation = QPropertyAnimation(opacity_effect, b"opacity")
        opacity_animation.setDuration(duration // 4)  # Duration in milliseconds
        opacity_animation.setStartValue(0.0)  # Start from fully transparent
        opacity_animation.setEndValue(1.0)  # End at fully opaque
        opacity_animation.setEasingCurve(QEasingCurve.Type.Linear)  # Easing curve for opacity

        # Append animations to the list to avoid garbage collection
        self.animations.extend([pos_animation, size_animation, opacity_animation])

        # Start both animations
        pos_animation.start()
        size_animation.start()
        opacity_animation.start()

    @pyqtSlot(list)
    def update_button_ui(self, button_updates):
        """Update button UI in the main thread."""
        app_info_cache = load_cache()

        if isinstance(self, SecondaryPieMenu):
            return

        pie_menu_updates = [update for update in button_updates if
                            update["index"] // CONFIG.INTERNAL_NUM_BUTTONS_IN_PIE_MENU == self.pie_menu_index]

        for pie_button in self.pie_buttons.values():
            print(pie_button.index)
            if not any(update["index"] == pie_button.index for update in pie_menu_updates):
                # Clear the button
                pie_button.clear()
                # print(f"Clearing button {pie_button.index}")
                continue

            try:
                pie_button_update = next(update for update in pie_menu_updates if update["index"] == pie_button.index)
            except StopIteration:
                raise ValueError("No update found for the specified pie button index.")

            button_text_1 = pie_button_update["properties"]["text_1"]
            button_text_2 = pie_button_update["properties"]["text_2"]
            window_handle = pie_button_update["properties"]["window_handle"]
            app_icon_path = pie_button_update["properties"]["app_icon_path"]
            exe_name = pie_button_update["properties"]["exe_name"]
            # Update button text and icon
            pie_button.update_content(button_text_1, button_text_2, app_icon_path)

            # Disconnect any previous connections
            try:
                pie_button.clicked.disconnect()
            except TypeError:
                pass  # No connections to disconnect

            # Handle reserved button actions
            if window_handle == 0:
                exe_path = app_info_cache.get(exe_name, {}).get("exe_path")
                if exe_path:
                    pie_button.set_left_click_action(
                        lambda captured_exe_path=exe_path: (
                            self.pie_window.hide(),
                            QTimer.singleShot(0, lambda: launch_app(captured_exe_path)),
                        )
                    )
                continue

            # Handle window actions
            pie_button.set_left_click_action(
                lambda hwnd=window_handle: (
                    self.pie_window.hide(),
                    QTimer.singleShot(0, lambda: focus_window_by_handle(hwnd)),
                )
            )
            pie_button.set_middle_click_action(
                lambda hwnd=window_handle: (
                    QTimer.singleShot(0, lambda: close_window_by_handle(hwnd)),
                    QTimer.singleShot(100, lambda: self.pie_window.auto_refresh()),
                )
            )
            pie_button.setEnabled(True)


class PrimaryPieMenu(PieMenu):
    def __init__(self, pie_menu_index: int, obj_name: str = "", parent: 'PieWindow' = None):
        super().__init__(pie_menu_index, obj_name, parent)

        self.hotkey = CONFIG.HOTKEY_PRIMARY


class SecondaryPieMenu(PieMenu):
    def __init__(self, pie_menu_index: int, obj_name: str = "", parent: 'PieWindow' = None):
        super().__init__(pie_menu_index, obj_name, parent)

        self.hotkey = CONFIG.HOTKEY_SECONDARY
