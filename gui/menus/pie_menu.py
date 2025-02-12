import math
from enum import Enum
from typing import TYPE_CHECKING, List, Optional

from PyQt6.QtCore import Qt, QPropertyAnimation, QRect, QEasingCurve, QSize, pyqtSignal, pyqtSlot, QTimer
from PyQt6.QtGui import QPainter
from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QWidget, QPushButton, QGraphicsOpacityEffect
from pynput.mouse import Controller, Button

from data.config import CONFIG
from functions.window_functions import load_cache, launch_app, focus_window_by_handle, close_window_by_handle
from gui.buttons.area_button import AreaButton
from gui.buttons.expanded_button import ExpandedButton
from gui.buttons.pie_button import PieButton
from gui.elements.svg_indicator_button import SVGIndicatorButton

if TYPE_CHECKING:
    from gui.pie_window import PieWindow


class PieMenuType(Enum):
    TASK_SWITCHER = "TaskSwitcher"
    WIN_CONTROL = "WinControl"


class PieMenu(QWidget):
    update_buttons_signal = pyqtSignal(list)  # Expect QWidget and list

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
        self.pie_button_texts: List[str] = ["Empty" for _ in range(CONFIG._MAX_BUTTONS)]
        self.pie_buttons: list[PieButton] = []
        self.animations = []

        self.middle_button: Optional[ExpandedButton] = None
        self.area_button: Optional[AreaButton] = None

        self.update_buttons_signal.connect(self.update_button_ui)

        self.setup_window()  # Configure main_window properties
        # Create scene and graphical elements
        self.setup_scene_and_view()
        # Create all buttons (task and main_window controls)
        self.setup_buttons()

    def setup_window(self):
        """Set up the main main_window properties."""
        # Non-resizable main_window
        self.setFixedSize(CONFIG._RADIUS * 2 + CONFIG._BUTTON_WIDTH * 2, CONFIG._RADIUS * 2 + CONFIG._BUTTON_HEIGHT * 2)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)

    def setup_scene_and_view(self):
        """Set up the scene and graphical elements."""
        self.scene = QGraphicsScene(self)
        self.view = QGraphicsView(self.scene, self)
        self.view.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        self.view.setGeometry(0, 0, self.width(), self.height())
        self.view.setObjectName(self.obj_name)

    def setup_buttons(self):
        """Create and position all buttons."""

        self.indicator = SVGIndicatorButton(
            object_name="Indicator",
            size=300,
            action=None,
            pos=(self.rect().center().x(), self.rect().center().y()),
            parent=self
        )
        self.indicator.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        # Create and configure the refresh button
        self.middle_button = ExpandedButton(
            text="",
            object_name="middleButton",
            fixed_size=True,
            # Using size instead of geometry
            size=(CONFIG._INNER_RADIUS * 2, CONFIG._INNER_RADIUS * 2),
            pos=(self.width() // 2 - CONFIG._INNER_RADIUS, self.height() // 2 - CONFIG._INNER_RADIUS)  # Using position for x and y
        )
        self.middle_button.left_clicked.connect(
            lambda: [self.parent().hide(), Controller().press(Button.x2), Controller().release(Button.x2)])
        self.middle_button.right_clicked.connect(lambda: self.pie_window.hide())
        self.middle_button.middle_clicked.connect(lambda: self.pie_window.open_special_menu())
        self.middle_button.setParent(self)
        self.middle_button.lower()
        self.view.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        # Creates the area button that has the screen spanning pie sections
        self.area_button = AreaButton("Slice!",
                                      "",
                                      pos=(self.width() // 2, self.height() // 2),
                                      parent=self)
        # Make the actual button click-through
        self.area_button.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        self.create_pie_buttons()

    def create_pie_buttons(self):
        # Create 8 buttons in a circular pattern, starting with top middle
        for i, pie_button_text in enumerate(self.pie_button_texts):
            angle_in_degrees = (
                    i / 8 * 360
            )  # Calculate button's position using angle_in_radians

            # the base offset here moves the anchor point from top left to center
            offset_x = -CONFIG._BUTTON_WIDTH / 2
            offset_y = CONFIG._BUTTON_HEIGHT / 2

            # the standard anchor position is the middle of a square area at the side of the button
            # the top and bottom buttons don't need it, they should remain centered
            nudge_x = CONFIG._BUTTON_WIDTH / 2 - CONFIG._BUTTON_HEIGHT / 2
            # some buttons need to be nudged so the distribution looks more circular
            # so we nudge the buttons at 45 degrees closer to the x-axis
            nudge_y = CONFIG._BUTTON_HEIGHT / 2

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
            else:
                pass

            # distribute the buttons in a circle
            button_pos_x = int(self.width() / 2 + offset_x + CONFIG._RADIUS * math.sin(math.radians(angle_in_degrees)))
            button_pos_y = int(self.height() / 2 - offset_y - CONFIG._RADIUS * math.cos(math.radians(angle_in_degrees)))

            button_name = "Pie_Button" + str(i)  # name of the button not used
            # self.btn = create_button(name, button_name, pos=(button_pos_x, button_pos_y))

            self.btn = PieButton(
                object_name=button_name,
                index=i,
                text_1=pie_button_text,
                text_2="",
                icon_path="",
                action=None,
                pos=(button_pos_x, button_pos_y),
                parent=self)

            self.pie_buttons.append(self.btn)

    def showEvent(self, event):
        super().showEvent(event)  # Call the parent class's method
        for button in self.pie_buttons:
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
        size_animation.setStartValue(QSize(CONFIG._BUTTON_WIDTH // 4, CONFIG._BUTTON_HEIGHT // 4))  # Initial size (small)
        size_animation.setEndValue(QSize(CONFIG._BUTTON_WIDTH, CONFIG._BUTTON_HEIGHT))  # Final size (target size)
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

        # TODO: Give all the Pie Menus the update, which give the buttons their updates
        #       This can then probably go into PieMenu instead

        for update in button_updates:
            button_index = update["index"]
            button_text_1 = update["properties"]["text_1"]
            button_text_2 = update["properties"]["text_2"]
            window_handle = update["properties"]["window_handle"]
            app_icon_path = update["properties"]["app_icon_path"]
            exe_name = update["properties"]["exe_name"]

            # Determine task switcher and index
            task_switcher, index = self.pie_window.get_pie_menu_and_index(button_index, PieMenuType.TASK_SWITCHER)

            # Update button text and icon
            self.pie_window.pie_button_texts[index] = button_text_1
            task_switcher.pie_buttons[index].update_content(button_text_1, button_text_2, app_icon_path)

            # Disconnect any previous connections
            try:
                task_switcher.pie_buttons[index].clicked.disconnect()
            except TypeError:
                pass  # No connections to disconnect

            # Handle reserved button actions
            if window_handle == 0:
                exe_path = app_info_cache.get(exe_name, {}).get("exe_path")
                if exe_path:
                    task_switcher.pie_buttons[index].set_left_click_action(
                        lambda captured_exe_path=exe_path: (
                            self.pie_window.hide(),
                            QTimer.singleShot(0, lambda: launch_app(captured_exe_path)),
                        )
                    )
                continue

            # Handle window actions
            task_switcher.pie_buttons[index].set_left_click_action(
                lambda hwnd=window_handle: (
                    self.pie_window.hide(),
                    QTimer.singleShot(0, lambda: focus_window_by_handle(hwnd)),
                )
            )
            task_switcher.pie_buttons[index].set_middle_click_action(
                lambda hwnd=window_handle: (
                    QTimer.singleShot(0, lambda: close_window_by_handle(hwnd)),
                    QTimer.singleShot(100, lambda: self.pie_window.auto_refresh()),
                )
            )
            task_switcher.pie_buttons[index].setEnabled(True)

        # Clear attributes when button index not among updates
        for i in range(CONFIG._MAX_BUTTONS * CONFIG._NUM_PIE_TASK_SWITCHERS):
            if i not in [update["index"] for update in button_updates]:
                task_switcher, index = self.pie_window.get_pie_menu_and_index(i, PieMenuType.TASK_SWITCHER)

                # Disable the button
                self.pie_window.pie_button_texts[index] = "Empty"
                task_switcher.pie_buttons[index].clear()
