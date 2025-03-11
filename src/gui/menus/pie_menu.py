import math
from typing import Optional, TYPE_CHECKING

from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QSize, QTimer, QPoint, QAbstractAnimation
from PyQt6.QtGui import QPainter
from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QWidget, QGraphicsOpacityEffect

from src.data.config import CONFIG
from src.gui.buttons.area_button import AreaButton
from src.gui.buttons.pie_button import PieButton, BUTTON_TYPES
from src.gui.buttons.pie_menu_middle_button import PieMenuMiddleButton
from src.gui.elements.svg_indicator_button import SVGIndicatorButton

if TYPE_CHECKING:
    from src.gui.pie_window import PieWindow

ANIMATION_DURATION = 150


class PieMenu(QWidget):

    def __init__(self, pie_menu_index: int, obj_name: str = "", parent: 'PieWindow' = None):
        super().__init__(parent)

        # Initialize these attributes BEFORE calling setup methods
        self.pie_menu_index: int = pie_menu_index
        self.obj_name: str = obj_name
        self.parent: "PieWindow" = parent
        self.indicator: Optional[SVGIndicatorButton] = None
        self.scene = None
        self.view = None
        self.btn = None
        self.pie_buttons: dict[int, PieButton] = {}
        self.animations: list[QAbstractAnimation] = []

        self.hotkey = CONFIG.HOTKEY_PRIMARY

        self.middle_button: Optional[PieMenuMiddleButton] = None
        self.area_button: Optional[AreaButton] = None

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
            pos=(self.rect().center().x() - CONFIG.INTERNAL_INNER_RADIUS, self.rect().center().y() - CONFIG.INTERNAL_INNER_RADIUS),
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
        # Configure button animations
        for button in self.pie_buttons.values():
            button.setVisible(False)
        # Ensure window geometry is set before animations
        self.setGeometry(self.x(), self.y(), self.width(), self.height())

        # Add a small delay before starting animations
        QTimer.singleShot(10, self.initiate_animations)
        super().showEvent(event)

    def initiate_animations(self) -> None:
        """Start animations for all buttons after a short delay."""
        # Set up animations but don't start them yet
        self.setup_animations()

        # Start the timer to trigger showing and animating the buttons
        if self.timer.isActive():
            self.timer.stop()
        self.timer.start(CONFIG.PIE_MENU_VIS_DELAY)

    def setup_animations(self) -> None:
        """Set up all animations for buttons and indicator."""
        self.animations = []  # Clear any previous animations
        center = self.rect().center()

        # Configure button animations
        for button in self.pie_buttons.values():
            # Set initial state (hidden and transparent)
            button.opacity_effect.setOpacity(0.0)

            # Configure start values
            start_x = center.x() - (CONFIG.INTERNAL_BUTTON_WIDTH // 8)
            start_y = center.y() - (CONFIG.INTERNAL_BUTTON_HEIGHT // 8)
            end_pos = self.button_initial_states.get(button.index)["pos"]

            # Add position animation
            pos_animation = QPropertyAnimation(button, b"pos")
            pos_animation.setDuration(ANIMATION_DURATION)
            pos_animation.setStartValue(QPoint(start_x, start_y))
            pos_animation.setEndValue(end_pos)
            pos_animation.setEasingCurve(QEasingCurve.Type.OutCirc)

            # Add size animation
            size_animation = QPropertyAnimation(button, b"size")
            size_animation.setDuration(ANIMATION_DURATION)
            size_animation.setStartValue(QSize(CONFIG.INTERNAL_BUTTON_WIDTH // 4, CONFIG.INTERNAL_BUTTON_HEIGHT // 4))
            size_animation.setEndValue(QSize(CONFIG.INTERNAL_BUTTON_WIDTH, CONFIG.INTERNAL_BUTTON_HEIGHT))
            size_animation.setEasingCurve(QEasingCurve.Type.OutCurve)

            # Add opacity animation
            opacity_animation = QPropertyAnimation(button.opacity_effect, b"opacity")
            opacity_animation.setDuration(ANIMATION_DURATION // 4)
            opacity_animation.setStartValue(0.0)
            opacity_animation.setEndValue(1.0)
            opacity_animation.setEasingCurve(QEasingCurve.Type.Linear)

            # Store animations
            self.animations.extend([pos_animation, size_animation, opacity_animation])

        # Add indicator animation
        indicator_animation = self.create_opacity_animation(self.indicator)
        middle_button_animation = self.create_opacity_animation(self.middle_button)

        self.animations.append(indicator_animation)
        self.animations.append(middle_button_animation)

    def show_buttons(self) -> None:
        """Timer callback: show buttons and start animations."""
        self.timer.stop()

        # Make buttons visible first
        for button in self.pie_buttons.values():
            button.setVisible(True)

        # Then start all animations
        self.start_animations()

    def start_animations(self):
        """Start all stored animations."""
        for animation in self.animations:
            animation.start()

    @staticmethod
    def create_opacity_animation(widget: QWidget) -> QAbstractAnimation:
        """Create and return an opacity animation for the given widget."""
        # Create an opacity effect if not already present
        if not hasattr(widget, 'opacity_effect'):
            opacity_effect = QGraphicsOpacityEffect(widget)
            widget.setGraphicsEffect(opacity_effect)
            widget.opacity_effect = opacity_effect

        # Set initial opacity
        widget.opacity_effect.setOpacity(0.0)

        # Create animation
        opacity_animation = QPropertyAnimation(widget.opacity_effect, b"opacity")
        opacity_animation.setDuration(ANIMATION_DURATION // 4)  # duration // 4
        opacity_animation.setStartValue(0.0)
        opacity_animation.setEndValue(1.0)
        opacity_animation.setEasingCurve(QEasingCurve.Type.Linear)

        return opacity_animation

    def update_button_ui(self, updated_button_config):
        """Update button UI in the main thread."""
        was_visible = self.isVisible()

        # Directly update each pie_button with the properties from updates
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
