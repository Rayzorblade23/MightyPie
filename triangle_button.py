import math
from typing import *

from PyQt6.QtCore import QPointF, QSize, Qt
from PyQt6.QtGui import QPainter, QPolygonF, QPainterPath, QRegion
from PyQt6.QtWidgets import QWidget, QPushButton


class TriangleButton(QPushButton):
    def __init__(self,
                 object_name: str,
                 width: int,
                 top_angle=45,
                 action: Optional[Callable] = None,
                 pos: Tuple[int, int] = (0, 0),
                 *args, **kwargs):
        """Initialize the triangle button with triangle_width and top angle for the triangle."""
        super().__init__(*args, **kwargs)
        self.setObjectName(object_name)
        self.top_angle = top_angle
        self.top_angle_rad = math.radians(self.top_angle)
        self.triangle_width = width
        self.triangle_height = int((self.triangle_width / 2) / math.tan(self.top_angle_rad / 2))

        # Check if action is provided and is callable
        if callable(action):
            self.clicked.connect(action)
        else:
            self.clicked.connect(self.default_action)

        # Set position if provided
        x, y = pos
        # Set position using `move()`, not `setGeometry()`
        self.move(x - self.triangle_width // 2, y - self.triangle_height)
        # self.lower()  # Send the button to the back

        # Set the size of the button to match the triangle
        self.setFixedSize(self.triangle_width, int(self.triangle_height))
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent)

        # print(f"Button size: {self.rect()}")
        # print(f"{self.triangle_width} wide and {self.triangle_height} high")

    def sizeHint(self):
        """Override sizeHint to ensure the button is the correct size for the triangle."""
        return QSize(self.triangle_width, int(self.triangle_height))

    def paintEvent(self, event):
        """Custom paint event to draw an isosceles triangle based on triangle_width and top angle."""
        # Ensure QPushButton's style is applied first
        super().paintEvent(event)

        # Define points for the triangle using QPointF
        top = QPointF(self.triangle_width / 2, self.triangle_height)  # top vertex of the triangle
        left = QPointF(0, 0)  # bottom-left vertex
        right = QPointF(self.triangle_width, 0)  # bottom-right vertex

        # Create a polygon to define the triangle
        triangle = QPolygonF([top, left, right])

        # Create a QPainterPath from the triangle polygon
        path = QPainterPath()
        path.addPolygon(triangle)

        # Paint the triangle using QPainter
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)  # No border
        painter.setBrush(Qt.BrushStyle.NoBrush)  # No brush

        # Draw the triangle
        painter.drawPolygon(triangle)

        painter.end()

        # Set the clickable area to the triangle
        region = QRegion(path.toFillPolygon().toPolygon())
        self.setMask(region)

    def default_action(self):
        """Default action when no external action is provided."""
        print(f"There was only the default action assigned for {self.objectName()}")
