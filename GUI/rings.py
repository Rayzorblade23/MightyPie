import math
from typing import *

from PyQt6.QtCore import QPointF, QSize, Qt, QRectF
from PyQt6.QtGui import QPainter, QColor, QRadialGradient, QPainterPath
from PyQt6.QtWidgets import QGraphicsEllipseItem, QWidget


class SmoothCircle(QGraphicsEllipseItem):

    def paint(self, painter: QPainter, option, widget=None):
        # Ensure antialiasing
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(self.brush())
        painter.setPen(self.pen())
        painter.drawEllipse(self.rect())


class GradientCircle(QWidget):
    def __init__(self,
                 object_name: str,
                 outer_radius: int,
                 inner_radius: int,
                 pos: Tuple[int, int] = (0, 0),
                 *args, **kwargs):
        """Initialize the widget for a circular display with radial gradient."""
        super().__init__(*args, **kwargs)
        self.setObjectName(object_name)
        self.outer_radius = outer_radius
        self.inner_radius = inner_radius
        self.start_angle = 0  # 0 = 3 o'clock, increases counter-clockwise
        self.span_angle = 360
        # Calculate size needed to contain the circle
        self.button_size = self.outer_radius * 2

        # Set position if provided
        x, y = pos
        self.move(x - self.outer_radius, y - self.outer_radius)

        # Set the size of the widget
        self.setFixedSize(self.button_size, self.button_size)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent)

    def sizeHint(self):
        """Override sizeHint to ensure the widget is the correct size."""
        return QSize(self.button_size, self.button_size)

    def _calculate_arc_point(self, angle_degrees: float, radius: float) -> QPointF:
        """Calculate point on arc at given angle and radius."""
        angle_rad = math.radians(angle_degrees)
        center_x = self.button_size / 2
        center_y = self.button_size / 2
        x = center_x + radius * math.cos(angle_rad)
        y = center_y - radius * math.sin(angle_rad)
        return QPointF(x, y)

    def paintEvent(self, event):
        """Custom paint event to draw a circle with a radial gradient."""
        # Common setup
        path = QPainterPath()
        center_x = self.button_size / 2
        center_y = self.button_size / 2

        # Calculate arc points and bounding rectangles
        outer_start = self._calculate_arc_point(self.start_angle, self.outer_radius)
        inner_end = self._calculate_arc_point(self.start_angle + self.span_angle, self.inner_radius)

        # Define the rectangles for the arcs
        outer_rect = QRectF(
            center_x - self.outer_radius,
            center_y - self.outer_radius,
            self.outer_radius * 2,
            self.outer_radius * 2
        )
        inner_rect = QRectF(
            center_x - self.inner_radius,
            center_y - self.inner_radius,
            self.inner_radius * 2,
            self.inner_radius * 2
        )

        # Construct the path
        path.moveTo(outer_start)
        path.arcTo(outer_rect, self.start_angle, self.span_angle)
        path.lineTo(inner_end)
        path.arcTo(inner_rect, self.start_angle + self.span_angle, -self.span_angle)
        path.closeSubpath()

        # Begin painting
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        start_point = self.inner_radius / self.outer_radius

        # Gradient painting
        gradient = QRadialGradient(QPointF(self.rect().center()), self.width() / 2)
        gradient.setColorAt(0, QColor(255, 255, 255, 10))  # Edge color
        # gradient.setColorAt(start_point, QColor(255, 255, 255, 0))  # Edge color
        # gradient.setColorAt(1 - ((1 - start_point) / 2), QColor(128, 128, 128, 255))  # Edge color
        # gradient.setColorAt(1, QColor(255, 255, 255, 0))  # Center color

        painter.setBrush(gradient)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawPath(path)


        painter.end()
