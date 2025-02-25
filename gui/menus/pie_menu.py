import math
from typing import Optional

from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QSize, pyqtSignal, pyqtSlot, QTimer, QPoint
from PyQt6.QtGui import QPainter
from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QWidget, QGraphicsOpacityEffect

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

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.show_buttons)

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

    @staticmethod
    def calculate_offsets(i: int, button_width: int, button_height: int) -> tuple[float, float]:
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

        # Initialize the dictionary to store the initial positions and sizes
        self.button_initial_states = {}

        # Calculate center position relative to the window
        center_x = self.width() // 2
        center_y = self.height() // 2

        for i in range(num_buttons):
            offset_x, offset_y = self.calculate_offsets(i, button_width, button_height)
            button_pos_x, button_pos_y = self.calculate_button_pos(i, num_buttons, offset_x, offset_y, radius)

            # Make positions relative to center
            button_pos_x = center_x + (button_pos_x - center_x)
            button_pos_y = center_y + (button_pos_y - center_y)

            button_name = "Pie_Button" + str(i)
            button_index = CONFIG.INTERNAL_NUM_BUTTONS_IN_PIE_MENU * self.pie_menu_index + i

            self.btn = PieButton(button_name, button_index, pos=(button_pos_x, button_pos_y), parent=self)
            self.pie_buttons[i] = self.btn

            # Store the initial position and size in the dictionary
            self.button_initial_states[button_index] = {
                "pos": QPoint(button_pos_x, button_pos_y),
                "size": QSize(CONFIG.INTERNAL_BUTTON_WIDTH, CONFIG.INTERNAL_BUTTON_HEIGHT)
            }

    def showEvent(self, event):
        super().showEvent(event)
        # Ensure window geometry is set before animations
        self.setGeometry(self.x(), self.y(), self.width(), self.height())

        # Add a small delay before starting animations
        QTimer.singleShot(10, self.initiate_animations)

    def initiate_animations(self):
        """Start animations for all buttons after a short delay."""
        for button in self.pie_buttons.values():
            button.setVisible(True)

        self.setup_button_animations()
        self.setup_widget_animations(self.indicator)

    def setup_button_animations(self):
        if self.timer.isActive():
            self.timer.stop()

        for button in self.pie_buttons.values():
            duration = 100
            center = self.rect().center()

            # Start position should be at the center of the window
            start_x = center.x() - (CONFIG.INTERNAL_BUTTON_WIDTH // 8)
            start_y = center.y() - (CONFIG.INTERNAL_BUTTON_HEIGHT // 8)

            end_pos = self.button_initial_states.get(button.index)["pos"]

            # Position animation
            pos_animation = QPropertyAnimation(button, b"pos")
            pos_animation.setDuration(duration)
            pos_animation.setStartValue(QPoint(start_x, start_y))
            pos_animation.setEndValue(end_pos)
            pos_animation.setEasingCurve(QEasingCurve.Type.OutCirc)

            # Size animation
            size_animation = QPropertyAnimation(button, b"size")
            size_animation.setDuration(duration)
            size_animation.setStartValue(QSize(CONFIG.INTERNAL_BUTTON_WIDTH // 4, CONFIG.INTERNAL_BUTTON_HEIGHT // 4))
            size_animation.setEndValue(QSize(CONFIG.INTERNAL_BUTTON_WIDTH, CONFIG.INTERNAL_BUTTON_HEIGHT))
            size_animation.setEasingCurve(QEasingCurve.Type.OutCurve)

            # Opacity animation
            opacity_animation = QPropertyAnimation(button.opacity_effect, b"opacity")
            opacity_animation.setDuration(duration // 4)
            opacity_animation.setStartValue(0.0)
            opacity_animation.setEndValue(1.0)
            opacity_animation.setEasingCurve(QEasingCurve.Type.Linear)

            # Set initial opacity to 0 and hide the button to avoid an initial flash
            button.opacity_effect.setOpacity(0.0)
            button.setVisible(False)

            # Store animations
            button.animations = [pos_animation, size_animation, opacity_animation]

            # Connect signals for prints
            pos_animation.finished.connect(lambda: self.print_geometry(button, "Position"))
            size_animation.finished.connect(lambda: self.print_geometry(button, "Size"))

        # First, after the delay, show the button without starting the animation.
        self.timer.start(CONFIG.PIE_MENU_VIS_DELAY)

    def show_buttons(self):
        self.timer.stop()

        for button in self.pie_buttons.values():
            button.setVisible(True)
            self.start_button_animations(button)

    def start_button_animations(self, button: PieButton):
        """Starts the stored animations for a button."""
        for animation in button.animations:
            animation.start()

    def setup_widget_animations(self, widget: SVGIndicatorButton):
        duration = 100  # Duration of the opacity animation

        # Create an opacity effect for the widget
        opacity_effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(opacity_effect)

        # Set the initial opacity to 0 (transparent)
        opacity_effect.setOpacity(0.0)

        # Opacity animation
        opacity_animation = QPropertyAnimation(opacity_effect, b"opacity")
        opacity_animation.setDuration(duration // 4)
        opacity_animation.setStartValue(0.0)  # Start with full transparency
        opacity_animation.setEndValue(1.0)  # Fade in to full opacity
        opacity_animation.setEasingCurve(QEasingCurve.Type.Linear)

        # Store animation to prevent garbage collection
        self.animations.append(opacity_animation)

        # Delay in milliseconds (500ms delay before animation starts)
        delay = CONFIG.PIE_MENU_VIS_DELAY  # 500ms delay before animation starts

        # Start animation after the delay
        QTimer.singleShot(delay, lambda: opacity_animation.start())

    def print_geometry(self, button: PieButton, animation_type: str):
        """Print the geometry of the button after animation."""
        if button.index % 8 == 0:
            print(f"AFTER {animation_type} animation - PM_{self.pie_menu_index} -  {button.index} geometry: {button.geometry()}\n")

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
