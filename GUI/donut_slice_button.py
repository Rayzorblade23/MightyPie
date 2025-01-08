import math
from typing import *

from PyQt6.QtCore import QPointF, QSize, Qt, QRectF
from PyQt6.QtGui import QPainter, QPainterPath, QRegion, QRadialGradient, QColor
from PyQt6.QtWidgets import QPushButton, QStyleOptionButton, QStyle
from pywinauto.handleprops import parent


class DonutSliceButton(QPushButton):
    def __init__(self,
                 object_name: str,
                 outer_radius: int,
                 inner_radius: int,
                 start_angle: float = 0,
                 span_angle: float = 45,
                 action: Optional[Callable] = None,
                 pos: Tuple[int, int] = (0, 0),
                 is_gradient: bool = False,
                 *args, **kwargs):
        """Initialize the donut slice button with inner and outer radius and angles."""
        super().__init__(*args, **kwargs)
        self.setObjectName(object_name)
        self.outer_radius = outer_radius
        self.inner_radius = inner_radius
        self.start_angle = start_angle  # 0 = 3 o'clock, increases counter-clockwise
        self.span_angle = span_angle
        self.use_gradient_painting = is_gradient

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

    def turn_towards_cursor(self, cursor_pos):
        offset = self.button_size // 2, self.button_size // 2
        cursor_pos_x = cursor_pos.x() - offset[0]
        cursor_pos_y = cursor_pos.y() - offset[1]

        # Compute angle in degrees (0 to 360)
        self.start_angle = math.degrees(math.atan2(-cursor_pos_y, cursor_pos_x))
        if self.start_angle < 0:
            self.start_angle += 360

        self.start_angle -= self.span_angle / 2
        self.update()


    def _calculate_arc_point(self, angle_degrees: float, radius: float) -> QPointF:
        """Calculate point on arc at given angle and radius."""
        angle_rad = math.radians(angle_degrees)
        center_x = self.button_size / 2
        center_y = self.button_size / 2
        x = center_x + radius * math.cos(angle_rad)
        y = center_y - radius * math.sin(angle_rad)
        return QPointF(x, y)

    def paintEvent(self, event):
        """Custom paint filtered_event to draw a donut slice with QPushButton styling or gradient."""
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

        if self.use_gradient_painting:
            # Gradient painting
            gradient = QRadialGradient(QPointF(self.rect().center()), self.width() / 2)
            gradient.setColorAt(0, QColor(128, 128, 128, 128))  # Center color
            gradient.setColorAt(1, QColor(255, 255, 255, 0))  # Edge color

            painter.setBrush(gradient)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawPath(path)
        else:
            # QPushButton styling painting
            opt = QStyleOptionButton()
            opt.initFrom(self)
            if self.isDown():
                opt.state |= QStyle.StateFlag.State_Sunken
            elif self.isChecked():
                opt.state |= QStyle.StateFlag.State_On
            elif not self.isFlat() and self.isEnabled():
                opt.state |= QStyle.StateFlag.State_Raised

            painter.setClipPath(path)
            self.style().drawControl(QStyle.ControlElement.CE_PushButton, opt, painter, self)

            # Update clickable area
            region = QRegion(path.toFillPolygon().toPolygon())
            self.setMask(region)

        painter.end()

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
