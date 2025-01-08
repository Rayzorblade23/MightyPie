import math

from PyQt6.QtCore import QRectF, Qt, QPropertyAnimation, QRect, QEasingCurve, QSize
from PyQt6.QtGui import QPainter, QBrush, QPen, QColor
from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QWidget, QPushButton, QGraphicsOpacityEffect
from pynput.mouse import Controller, Button

from area_button import AreaButton
from config import CONFIG
from donut_slice_button import DonutSliceButton
from expanded_button import ExpandedButton
from pie_button import PieButton
from rings import SmoothCircle


class PieMenuTaskSwitcher(QWidget):

    def __init__(self, obj_name: str = "", parent=None):
        super().__init__(parent)

        # Initialize these attributes BEFORE calling setup methods
        self.donut_button = None
        self.inner_circle_main = None
        self.scene = None
        self.view = None
        self.btn = None
        self.pie_button_texts = ["Empty" for _ in range(CONFIG.MAX_BUTTONS)]
        self.pie_buttons = []
        self.animations = []

        self.obj_name = obj_name

        self.setup_window()  # Configure main_window properties
        # Create scene and graphical elements
        self.setup_scene_and_view()
        # Create all buttons (task and main_window controls)
        self.setup_buttons()

    def setup_window(self):
        """Set up the main main_window properties."""
        self.setWindowTitle("PieTaskSwitcher")
        # Non-resizable main_window
        self.setFixedSize(CONFIG.RADIUS * 2 + CONFIG.BUTTON_WIDTH * 2, CONFIG.RADIUS * 2 + CONFIG.BUTTON_HEIGHT * 2)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)

    def setup_scene_and_view(self):
        """Set up the scene and graphical elements."""
        self.scene = QGraphicsScene(self)
        self.view = QGraphicsView(self.scene, self)
        self.view.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        self.view.setGeometry(0, 0, self.width(), self.height())
        self.view.setObjectName(self.obj_name)

        # Use the subclass instead of QGraphicsEllipseItem
        self.inner_circle_main = SmoothCircle(
            QRectF(
                self.rect().center().x() - CONFIG.INNER_RADIUS,  # Adjust for radius
                self.rect().center().y() - CONFIG.INNER_RADIUS,  # Adjust for radius
                CONFIG.INNER_RADIUS * 2,  # Diameter
                CONFIG.INNER_RADIUS * 2  # Diameter
            )
        )
        self.inner_circle_main.setBrush(QBrush(Qt.BrushStyle.NoBrush))
        self.inner_circle_main.setPen(QPen(QColor(30, 30, 30), 7))
        self.scene.addItem(self.inner_circle_main)

        # Create another circle for the outline (slightly thicker)
        self.outline_circle = SmoothCircle(
            QRectF(
                self.rect().center().x() - CONFIG.INNER_RADIUS,  # Adjust for radius
                self.rect().center().y() - CONFIG.INNER_RADIUS,  # Adjust for radius
                CONFIG.INNER_RADIUS * 2,  # Diameter
                CONFIG.INNER_RADIUS * 2  # Diameter
            )
        )
        self.outline_circle.setBrush(QBrush(Qt.BrushStyle.NoBrush))
        self.outline_circle.setPen(QPen(QColor(50, 50, 50), 9))

        self.outline_circle.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        self.inner_circle_main.setAcceptedMouseButtons(Qt.MouseButton.NoButton)

        # Add the circles to the scene
        self.scene.addItem(self.outline_circle)
        self.scene.addItem(self.inner_circle_main)

        # Ensure the inner circle is on top by setting its Z-index higher than the outline circle
        self.inner_circle_main.setZValue(1)  # Higher Z-value to be in front
        self.outline_circle.setZValue(0)  # Lower Z-value to be behind

    def setup_buttons(self):
        """Create and position all buttons."""

        self.donut_button = DonutSliceButton(
            object_name="DonutSlice",
            outer_radius=CONFIG.INNER_RADIUS + 30,
            inner_radius=CONFIG.INNER_RADIUS + 10,
            start_angle=-22.5,
            span_angle=45,
            action=None,
            pos=(self.rect().center().x(), self.rect().center().y()),
            parent=self
        )
        self.donut_button.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        # self.outer_ring = GradientCircle(
        #     object_name="GradientCircle",
        #     outer_radius=CONFIG.INNER_RADIUS + 30,
        #     inner_radius=CONFIG.INNER_RADIUS + 10,
        #     pos=(self.rect().center().x(), self.rect().center().y()),
        #     parent=self
        # )
        # self.outer_ring.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        # self.outer_ring.lower()

        # Create and configure the refresh button
        self.middle_button = ExpandedButton(
            text="",
            object_name="middleButton",
            fixed_size=True,
            # Using size instead of geometry
            size=(CONFIG.INNER_RADIUS * 2, CONFIG.INNER_RADIUS * 2),
            pos=(self.width() // 2 - CONFIG.INNER_RADIUS, self.height() // 2 - CONFIG.INNER_RADIUS)  # Using position for x and y
        )
        self.middle_button.left_clicked.connect(
            lambda: [self.parent().hide(), Controller().press(Button.x2), Controller().release(Button.x2)])
        self.middle_button.right_clicked.connect(lambda: self.parent().hide())
        self.middle_button.middle_clicked.connect(lambda: self.parent().open_special_menu())
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

        # Create 8 buttons in a circular pattern, starting with top middle
        for i, pie_button_text in enumerate(self.pie_button_texts):
            angle_in_degrees = (
                    i / 8 * 360
            )  # Calculate button's position using angle_in_radians

            # the base offset here moves the anchor point from top left to center
            offset_x = -CONFIG.BUTTON_WIDTH / 2
            offset_y = CONFIG.BUTTON_HEIGHT / 2

            # the standard anchor position is the middle of a square area at the side of the button
            # the top and bottom buttons don't need it, they should remain centered
            nudge_x = CONFIG.BUTTON_WIDTH / 2 - CONFIG.BUTTON_HEIGHT / 2
            # some buttons need to be nudged so the distribution looks more circular
            # so we nudge the buttons at 45 degrees closer to the x-axis
            nudge_y = CONFIG.BUTTON_HEIGHT / 2

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
            button_pos_x = int(self.width() / 2 + offset_x + CONFIG.RADIUS * math.sin(math.radians(angle_in_degrees)))
            button_pos_y = int(self.height() / 2 - offset_y - CONFIG.RADIUS * math.cos(math.radians(angle_in_degrees)))

            button_name = "Pie_Button" + str(i)  # name of the button not used
            # self.btn = create_button(name, button_name, pos=(button_pos_x, button_pos_y))

            self.btn = PieButton(
                object_name=button_name,
                text_1=pie_button_text,
                text_2="",
                icon_path="",
                action=None,
                pos=(button_pos_x, button_pos_y),
                parent=self)

            self.pie_buttons.append(self.btn)

    def update_child_button_hover_state(self, button, hovered):
        button.setProperty("hovered", hovered)
        button.style().unpolish(button)
        button.style().polish(button)

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
        size_animation.setStartValue(QSize(CONFIG.BUTTON_WIDTH // 4, CONFIG.BUTTON_HEIGHT // 4))  # Initial size (small)
        size_animation.setEndValue(QSize(CONFIG.BUTTON_WIDTH, CONFIG.BUTTON_HEIGHT))  # Final size (target size)
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
