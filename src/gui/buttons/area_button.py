import math
from typing import Tuple

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QColor
from PyQt6.QtWidgets import QPushButton, QWidget, QSizePolicy

from src.data.config import CONFIG


class AreaButton(QPushButton):
    def __init__(self,
                 object_name: str,
                 pos: Tuple[int, int] = (0, 0),
                 parent=None):
        super().__init__(parent)
        self.setObjectName(object_name)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover)

        self.in_active_area = 0
        self.is_pressed = False
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setFixedSize(100, 100)

        #######################---Dot Functionality---#######################
        # Initialize hover_pos as None
        self.hover_pos = None

        # Flag to control the visibility of dots (debug mode)
        self.show_dots = False  # Set it to True to show dots by default

        # Store a list of all created dot widgets
        self.dot_widgets = []  # List to keep track of all dots
        #####################################################################

        # Set position if provided
        self.x, self.y = pos
        # Set position using `move()`, not `setGeometry()`
        self.move(self.x - self.width() // 2, self.y - self.height() // 2)

    def paintEvent(self, event):
        super().paintEvent(event)  # Call the base class to handle normal painting

        if self.show_dots and self.hover_pos:
            # Create a new dot widget for each mouse move
            self.create_dot_widget(self.hover_pos)

    def create_dot_widget(self, hover_pos):
        """Creates a new dot widget for each hover position."""
        dot_widget = DotWidget(self.parent())  # Create a new dot widget with PieWindow as parent
        self.dot_widgets.append(dot_widget)  # Add it to the list of dots

        # Convert global position to the parent (PieWindow) coordinate system
        local_pos = self.parent().mapFromGlobal(hover_pos)  # Get position relative to the parent

        dot_widget.move(local_pos)  # Move the dot widget to hover position
        dot_widget.setVisible(True)  # Show the dot widget

    def check_active_area(self, x, y):
        center_x = self.width() // 2
        center_y = self.height() // 2
        dx = x - center_x
        dy = y - center_y

        # Compute angle in degrees (0 to 360)
        theta = math.degrees(math.atan2(dy, dx))
        if theta < 0:
            theta += 360

        # Compute distance and check if smaller than inner radius
        r = math.sqrt(dx ** 2 + dy ** 2)

        if r < CONFIG.INTERNAL_INNER_RADIUS * 2:
            return -1

        # Check if the angle is within the sector
        if 247.5 <= theta < 292.5:
            return 0
        elif 292.5 <= theta < 337.5:
            return 1
        elif (337.5 <= theta < 360) or (0 <= theta < 22.5):
            return 2
        elif 22.5 <= theta < 67.5:
            return 3
        elif 67.5 <= theta < 112.5:
            return 4
        elif 112.5 <= theta < 157.5:
            return 5
        elif 157.5 <= theta < 202.5:
            return 6
        elif 202.5 <= theta < 247.5:
            return 7

    def set_hover_pos(self, pos):
        """Sets the hover position manually from outside the widget."""
        self.hover_pos = pos
        self.update()  # Ensure the widget is repainted when hover_pos changes


class DotWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent)
        self.setAutoFillBackground(False)
        self.setFixedSize(10, 10)  # Size of the dot
        self.raise_()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QColor(255, 0, 0))  # Red color for the dot
        painter.drawEllipse(0, 0, self.width(), self.height())  # Draw a circle
