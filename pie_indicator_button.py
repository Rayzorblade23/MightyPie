import math
from typing import *

from PyQt6.QtCore import QPointF, QSize, Qt, QRectF
from PyQt6.QtGui import QPainter, QPainterPath, QRegion, QRadialGradient, QColor, QPen
from PyQt6.QtWidgets import QPushButton, QStyleOptionButton, QStyle


class DonutSliceButton(QPushButton):
    def __init__(self,
                 object_name: str,
                 outer_radius: int,
                 inner_radius: int,
                 start_angle: float = 0,
                 span_angle: float = 45,
                 action: Optional[Callable] = None,
                 pos: Tuple[int, int] = (0, 0),
                 *args, **kwargs):
        """Initialize the donut slice button with inner and outer radius and angles."""
        super().__init__(*args, **kwargs)
        self.setObjectName(object_name)
        self.outer_radius = outer_radius
        self.inner_radius = inner_radius
        self.start_angle = start_angle  # 0 = 3 o'clock, increases counter-clockwise
        self.span_angle = span_angle

        # Calculate size needed to contain the full donut slice
        self.button_size = self.outer_radius * 2

        # Check if action is provided and is callable
        if callable(action):
            self.clicked.connect(action)
        else:
            self.clicked.connect(self.default_action)

        # Set position if provided
        x, y = pos
        self.move(x - self.button_size // 2, y - self.button_size // 2)

        # Set the size of the button
        self.setFixedSize(self.button_size, self.button_size)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent)

    def sizeHint(self):
        """Override sizeHint to ensure the button is the correct size."""
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
        """Custom paint event to draw a donut slice with QPushButton styling."""
        # Set up the style option
        opt = QStyleOptionButton()
        opt.initFrom(self)
        if self.isDown():
            opt.state |= QStyle.StateFlag.State_Sunken
        elif self.isChecked():
            opt.state |= QStyle.StateFlag.State_On
        elif not self.isFlat() and self.isEnabled():
            opt.state |= QStyle.StateFlag.State_Raised

        # Create a radial gradient
        gradient = QRadialGradient(QPointF(self.rect().center()), self.width() / 2)
        gradient.setColorAt(0, QColor(255, 255, 255))  # Center color (white)
        gradient.setColorAt(1, QColor(0, 0, 0))  # Edge color (black)

        # Create the path for the donut slice
        path = QPainterPath()
        center_x = self.button_size / 2
        center_y = self.button_size / 2

        # Define the rectangles for both arcs
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

        # Start from outer arc's starting point
        path.moveTo(self._calculate_arc_point(self.start_angle, self.outer_radius))

        # Draw outer arc
        path.arcTo(outer_rect, self.start_angle, self.span_angle)

        # Draw line to inner arc endpoint
        path.lineTo(self._calculate_arc_point(self.start_angle + self.span_angle, self.inner_radius))

        # Draw inner arc
        path.arcTo(inner_rect, self.start_angle + self.span_angle, -self.span_angle)

        # Close the path
        path.closeSubpath()

        # Begin painting
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Create a clipping region for the button shape
        painter.setClipPath(path)

        # Draw the button's background and frame using the style
        self.style().drawControl(QStyle.ControlElement.CE_PushButton, opt, painter, self)

        painter.end()

    ########################################################################
    ################----Use this paintEvent for Gradient----################
    ########################################################################
    # def paintEvent(self, event):
    #     """Custom paint event to draw a donut slice with QPushButton styling."""
    #     path = QPainterPath()
    #     center_x = self.button_size / 2
    #     center_y = self.button_size / 2
    #
    #     # Calculate the four corner points
    #     outer_start = self._calculate_arc_point(self.start_angle, self.outer_radius)
    #     outer_end = self._calculate_arc_point(self.start_angle + self.span_angle, self.outer_radius)
    #     inner_start = self._calculate_arc_point(self.start_angle, self.inner_radius)
    #     inner_end = self._calculate_arc_point(self.start_angle + self.span_angle, self.inner_radius)
    #
    #     # Start from the outer start point
    #     path.moveTo(outer_start)
    #
    #     # Draw outer arc
    #     outer_rect = QRectF(
    #         center_x - self.outer_radius,
    #         center_y - self.outer_radius,
    #         self.outer_radius * 2,
    #         self.outer_radius * 2
    #     )
    #     path.arcTo(outer_rect, self.start_angle, self.span_angle)
    #
    #     # Draw line to inner arc
    #     path.lineTo(inner_end)
    #
    #     # Draw inner arc
    #     inner_rect = QRectF(
    #         center_x - self.inner_radius,
    #         center_y - self.inner_radius,
    #         self.inner_radius * 2,
    #         self.inner_radius * 2
    #     )
    #     path.arcTo(inner_rect, self.start_angle + self.span_angle, -self.span_angle)
    #
    #     # Close the path by returning to start
    #     path.lineTo(outer_start)
    #
    #     # Paint the donut slice
    #     painter = QPainter(self)
    #     painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    #
    #     # Create a radial gradient
    #     gradient = QRadialGradient(QPointF(self.rect().center()), self.width() / 2)
    #     gradient.setColorAt(0, QColor(128, 128, 128,128))  # Center color (white)
    #     gradient.setColorAt(1, QColor(255, 255, 255, 0))  # Edge color (black)
    #
    #     # Fill the donut area with the radial gradient
    #     painter.setBrush(gradient)
    #     painter.setPen(Qt.PenStyle.NoPen)
    #
    #     # Draw the path
    #     painter.drawPath(path)
    #
    #     painter.end()

        # Set the clickable area to the donut slice
        region = QRegion(path.toFillPolygon().toPolygon())
        self.setMask(region)

    def mousePressEvent(self, event):
        """Handle mouse press events."""
        # Create the path and check if the click is within it
        path = QPainterPath()
        center_x = self.button_size / 2
        center_y = self.button_size / 2

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

        path.moveTo(self._calculate_arc_point(self.start_angle, self.outer_radius))
        path.arcTo(outer_rect, self.start_angle, self.span_angle)
        path.lineTo(self._calculate_arc_point(self.start_angle + self.span_angle, self.inner_radius))
        path.arcTo(inner_rect, self.start_angle + self.span_angle, -self.span_angle)
        path.closeSubpath()

        if path.contains(event.position()):
            super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        """Handle mouse release events."""
        path = QPainterPath()
        center_x = self.button_size / 2
        center_y = self.button_size / 2

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

        path.moveTo(self._calculate_arc_point(self.start_angle, self.outer_radius))
        path.arcTo(outer_rect, self.start_angle, self.span_angle)
        path.lineTo(self._calculate_arc_point(self.start_angle + self.span_angle, self.inner_radius))
        path.arcTo(inner_rect, self.start_angle + self.span_angle, -self.span_angle)
        path.closeSubpath()

        if path.contains(event.position()):
            super().mouseReleaseEvent(event)

    def default_action(self):
        """Default action when no external action is provided."""
        print(f"There was only the default action assigned for {self.objectName()}")