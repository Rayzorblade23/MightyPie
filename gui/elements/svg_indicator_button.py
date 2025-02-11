import os
from typing import *
import math
from pathlib import Path

from PyQt6.QtCore import QPointF, QSize, Qt, QRectF, QPoint, QByteArray
from PyQt6.QtGui import QPainter, QTransform
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtWidgets import QPushButton

from data.config import CONFIG
from functions.file_handling_utils import get_resource_path


class SVGIndicatorButton(QPushButton):
    def __init__(self,
                 object_name: str,
                 size: int,
                 action: Optional[Callable] = None,
                 pos: Tuple[int, int] = (0, 0),
                 *args, **kwargs):
        """Initialize the SVG indicator button."""
        super().__init__(*args, **kwargs)
        self.setObjectName(object_name)
        self.button_size = size

        # Load the SVG
        svg_path = get_resource_path(CONFIG._INDICATOR_SVG_PATH)

        svg = Path(svg_path).read_text()
        svg = (svg.replace("{indicator}", CONFIG.ACCENT_COLOR_MUTED).
               replace("{ring_fill}", CONFIG.RING_FILL).
               replace("{ring_stroke}", CONFIG.RING_STROKE))


        # self.svg_renderer = QSvgRenderer(str(svg_path))
        self.svg_renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))

        # Initialize rotation angle with the starting offset
        self.rotation_angle = 22.5

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

    def turn_towards_cursor(self, cursor_pos: QPoint):
        """Rotate the SVG to point towards the cursor position."""
        # Convert cursor_pos to QPointF
        cursor_pos_f = QPointF(cursor_pos)
        center = QPointF(self.button_size / 2, self.button_size / 2)
        cursor_vector = cursor_pos_f - center

        # Calculate angle in degrees (0 = right, increases counter-clockwise)
        # Add 22.5 degrees to account for the starting angle
        angle = math.degrees(math.atan2(cursor_vector.y(), cursor_vector.x())) + 22.5
        self.rotation_angle = angle
        self.update()

    def paintEvent(self, event):
        """Paint the SVG with the current rotation."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)


        # Set up transform for rotation
        transform = QTransform()
        transform.translate(self.button_size / 2, self.button_size / 2)
        transform.rotate(self.rotation_angle)
        transform.translate(-self.button_size / 2, -self.button_size / 2)
        painter.setTransform(transform)

        # Convert QRect to QRectF for the render call
        bounds = QRectF(self.rect())
        self.svg_renderer.render(painter, bounds)

        painter.end()

    def default_action(self):
        """Default action when no external action is provided."""
        print(f"There was only the default action assigned for {self.objectName()}")