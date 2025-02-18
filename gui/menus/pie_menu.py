import math
from typing import Optional

from PyQt6.QtCore import Qt, QPropertyAnimation, QRect, QEasingCurve, QSize, pyqtSignal, pyqtSlot, QTimer
from PyQt6.QtGui import QPainter
from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QWidget

from data.button_info import ButtonInfo
from data.config import CONFIG
from gui.buttons.area_button import AreaButton
from gui.buttons.pie_button import PieButton, BUTTON_TYPES
from gui.buttons.pie_menu_middle_button import PieMenuMiddleButton
from gui.elements.svg_indicator_button import SVGIndicatorButton


class PieMenu(QWidget):
    update_buttons_signal = pyqtSignal(dict)

    def __init__(self, pie_menu_index: int, obj_name: str = "", parent: 'PieWindow' = None):
        super().__init__(parent)

        # Initialize these attributes BEFORE calling setup methods
        self.pie_menu_index: int = pie_menu_index
        self.obj_name: str = obj_name
        self.indicator: Optional[SVGIndicatorButton] = None
        self.scene = None
        self.view = None
        self.btn = None
        self.pie_buttons: dict[int, PieButton] = {}
        self.animations = []

        self.hotkey = CONFIG.HOTKEY_PRIMARY

        self.button_info: ButtonInfo = ButtonInfo.get_instance()

        self.middle_button: Optional[PieMenuMiddleButton] = None
        self.area_button: Optional[AreaButton] = None

        self.update_buttons_signal.connect(self.update_button_ui)

        self.setup_window()
        # Create scene and graphical elements
        self.setup_scene_and_view()
        # Create all buttons
        self.setup_ui()

    def setup_window(self):
        """Set up the main main_window properties."""
        # Non-resizable window
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

    def calculate_offsets(self, i: int, button_width: int, button_height: int) -> tuple[float, float]:
        """Calculate the offset for button position based on its index."""
        nudge_x = button_width / 2 - button_height / 2
        nudge_y = button_height / 2

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

        return offset_x, offset_y

    def calculate_button_pos(self, index, num_buttons, offset_x, offset_y, radius):
        angle_in_rad = math.radians(index / num_buttons * 360)
        button_pos_x = int(self.width() / 2 + offset_x + radius * math.sin(angle_in_rad))
        button_pos_y = int(self.height() / 2 - offset_y - radius * math.cos(angle_in_rad))
        return button_pos_x, button_pos_y

    def replace_pie_button(self, index: int, new_button_class):
        """Replace a pie button with a new button class."""
        old_button = self.pie_buttons.get(index)
        if old_button:
            old_button.deleteLater()  # Remove the old button completely

        # Get the necessary parameters for the new button
        num_buttons = CONFIG.INTERNAL_NUM_BUTTONS_IN_PIE_MENU
        button_width = CONFIG.INTERNAL_BUTTON_WIDTH
        button_height = CONFIG.INTERNAL_BUTTON_HEIGHT
        radius = CONFIG.INTERNAL_RADIUS

        # Calculate button position and offsets
        offset_x, offset_y = self.calculate_offsets(index, button_width, button_height)
        button_pos_x, button_pos_y = self.calculate_button_pos(index, num_buttons, offset_x, offset_y, radius)

        # Create the new button using the new_button_class and the calculated position
        button_name = "Pie_Button" + str(index)
        button_index = CONFIG.INTERNAL_NUM_BUTTONS_IN_PIE_MENU * self.pie_menu_index + index
        new_button = new_button_class(button_name, button_index, pos=(button_pos_x, button_pos_y), parent=self)

        # Update the pie_buttons list with the new button
        self.pie_buttons[index] = new_button

        # # Check if the replacement was successful
        # if self.pie_buttons.get(index) == new_button:
        #     print(f"Button at index {index} replaced successfully.")
        # else:
        #     print(f"Failed to replace button of type {new_button_class} at index {index}.")

    def create_pie_buttons(self):
        """Create pie menu buttons in a circular pattern."""
        num_buttons = CONFIG.INTERNAL_NUM_BUTTONS_IN_PIE_MENU
        button_width = CONFIG.INTERNAL_BUTTON_WIDTH
        button_height = CONFIG.INTERNAL_BUTTON_HEIGHT
        radius = CONFIG.INTERNAL_RADIUS

        for i in range(num_buttons):
            # Calculate button position and offsets using the calculate_offsets function
            offset_x, offset_y = self.calculate_offsets(i, button_width, button_height)
            button_pos_x, button_pos_y = self.calculate_button_pos(i, num_buttons, offset_x, offset_y, radius)

            button_name = "Pie_Button" + str(i)
            button_index = CONFIG.INTERNAL_NUM_BUTTONS_IN_PIE_MENU * self.pie_menu_index + i

            # Create the pie button
            self.btn = PieButton(button_name, button_index, pos=(button_pos_x, button_pos_y), parent=self)

            # Store the button in the dictionary
            self.pie_buttons[i] = self.btn

    def showEvent(self, event):
        super().showEvent(event)  # Call the parent class's method
        for button in self.pie_buttons.values():
            self.animate_button(button, button.geometry())

    def animate_button_with_delay(self, button: PieButton, rect: QRect, delay=50):  # Use MyButton
        QTimer.singleShot(delay, lambda: self.animate_button(button, rect))

    def animate_button(self, button: PieButton, rect: QRect):  # Use MyButton
        # Now, we ONLY work with the existing effect

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
        opacity_animation = QPropertyAnimation(button.opacity_effect, b"opacity")
        opacity_animation.setDuration(duration // 4)  # Duration in milliseconds
        opacity_animation.setStartValue(0.0)  # Start from fully transparent
        opacity_animation.setEndValue(1.0)  # End at fully opaque
        opacity_animation.setEasingCurve(QEasingCurve.Type.Linear)  # Easing curve for opacity

        # Append animations to the list to avoid garbage collection
        self.animations.extend([pos_animation, size_animation, opacity_animation])
        #
        # if button.index % CONFIG.INTERNAL_NUM_BUTTONS_IN_PIE_MENU == 0:
        #     print(f"  Starting animations:")
        #     print(
        #         f"    pos: start=({pos_animation.startValue().x()}, {pos_animation.startValue().y()}) end=({pos_animation.endValue().x()}, {pos_animation.endValue().y()}) - Button {button.index}")
        #     print(
        #         f"    size: start=({size_animation.startValue().width()}, {size_animation.startValue().height()}) end=({size_animation.endValue().width()}, {size_animation.endValue().height()}) - Button {button.index}")
        #     print(f"    opacity: start={opacity_animation.startValue()} end={opacity_animation.endValue()} - Button {button.index}")

        # Start both animations
        pos_animation.start()
        size_animation.start()
        opacity_animation.start()

    @pyqtSlot(dict)
    def update_button_ui(self, updated_button_config):
        """Update button UI in the main thread."""
        was_visible = self.isVisible()

        self.button_info.button_info_dict = updated_button_config
        self.button_info.has_unsaved_changes = True
        self.button_info.save_to_json()

        # print("BUTTON THINGS")
        # for i in range(0, 8):
        #     print(f"Update {i}:")
        #     print(updated_button_config[i]['task_type'])
        #     print("  Properties:")
        #     for prop_name, prop_value in updated_button_config[i]['properties'].items():
        #         print(f"  {prop_name}: {prop_value}")

        # Directly update each pie_button with the properties from button_info
        for pie_button in list(self.pie_buttons.values()):
            if updated_button_config[pie_button.index]["task_type"] in BUTTON_TYPES.keys():
                button_type = updated_button_config[pie_button.index]["task_type"]
                if pie_button.button_type != button_type:
                    # Hide the menu if it's visible during replacement
                    was_visible = self.isVisible()
                    if was_visible:
                        self.hide()
                    self.replace_pie_button(pie_button.index % 8, BUTTON_TYPES[button_type])

        # Show the menu again if it was visible before
        if was_visible:
            self.show()

        for pie_button in self.pie_buttons.values():
            pie_button.update_button(updated_button_config[pie_button.index]['properties'])


class PrimaryPieMenu(PieMenu):
    def __init__(self, pie_menu_index: int, obj_name: str = "", parent=None):
        super().__init__(pie_menu_index, obj_name, parent)

        self.hotkey = CONFIG.HOTKEY_PRIMARY


class SecondaryPieMenu(PieMenu):
    def __init__(self, pie_menu_index: int, obj_name: str = "", parent=None):
        super().__init__(pie_menu_index, obj_name, parent)

        self.hotkey = CONFIG.HOTKEY_SECONDARY
