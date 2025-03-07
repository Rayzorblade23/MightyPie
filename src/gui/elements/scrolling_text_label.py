import logging

from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QFontMetrics
from PyQt6.QtWidgets import QLabel, QHBoxLayout, QSizePolicy, QWidget

from src.data.config import CONFIG
from src.data.font_styles import FontStyle

logger = logging.getLogger(__name__)


class ScrollingLabel(QWidget):
    """Label with scrolling text for long content."""

    def __init__(self, text: str = "", font_style: FontStyle = FontStyle.Normal, h_align: Qt.AlignmentFlag = Qt.AlignmentFlag.AlignLeft,
                 v_offset: int = 0, font_size: int = 12,
                 parent: QWidget = None):
        super().__init__(parent)

        # Initialize attributes for scrolling
        self.text_scroll_pos = 0
        self.text_scroll_active = False
        self.timer = QTimer(self)
        self.label_margins = CONFIG.INTERNAL_PIE_TEXT_LABEL_MARGINS
        self.scroll_speed = CONFIG.INTERNAL_PIE_TEXT_LABEL_SCROLL_SPEED
        self.scroll_update_interval = CONFIG.INTERNAL_PIE_TEXT_LABEL_SCROLL_INTERVAL  # in ms
        self.h_align = h_align
        self.v_offset = v_offset
        self.font_size = font_size

        # Pause parameters
        self.pause_state = 1
        self.pause_counter = 0
        self.PAUSE_DURATION_AT_START = 40  # Reduced from 60 to start scrolling sooner
        self.PAUSE_DURATION_AT_END = 40  # Reduced from 60 to restart scrolling sooner

        # UI initialization
        self._container = QWidget(self)
        self.label = QLabel(self._container)

        self._initialize_ui()

        self.label.setText(text)
        self._set_font_style(font_style)  # Set font before checking fit
        self._check_text_fit()

        # Configure timer
        self.timer.timeout.connect(self._scroll_text)
        self.timer.setInterval(self.scroll_update_interval)  # Timer interval for smoother scrolling

    def _initialize_ui(self):
        """Set up the container and layout."""
        self._container.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        # Label to display text
        self.label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        # Allow label to expand beyond container width
        self.label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.label.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        # Layout for QLabel
        self.layout = QHBoxLayout(self._container)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        self.layout.addWidget(self.label)
        self.layout.setAlignment(self.label, self.h_align | Qt.AlignmentFlag.AlignVCenter)  # Align label to the left

    def resizeEvent(self, event):
        """Adjust container size on resize."""
        super().resizeEvent(event)
        rect = self.rect()
        rect.setWidth(rect.width() - self.label_margins * 2)
        rect.moveLeft((self.rect().width() - rect.width()) // 2)
        rect.moveTop(-self.v_offset)
        self._container.setGeometry(rect)
        self._check_text_fit()  # Re-check text fit on resize

    def update_text(self, new_text: str):
        """Update the text of the scrolling label."""
        self.label.setText(new_text)
        self.text_scroll_pos = 0  # Reset scroll position
        self.pause_state = 1  # Reset to initial pause state
        self.pause_counter = 0  # Reset pause counter
        self._check_text_fit()  # Re-evaluate if scrolling is needed

    def update_v_offset(self, new_offset: int):
        """Update the vertical offset of the label and refresh its position."""
        self.v_offset = new_offset
        rect = self.rect()
        rect.setWidth(rect.width() - self.label_margins * 2)
        rect.moveLeft((self.rect().width() - rect.width()) // 2)
        rect.moveTop(-self.v_offset)
        self._container.setGeometry(rect)

    def _set_font_style(self, font_style: FontStyle):
        """Set the font style based on the font_styles.py enum."""
        font = self.label.font()  # Get the current font
        if font_style == FontStyle.Bold:
            font.setBold(True)
            font.setItalic(False)
        elif font_style == FontStyle.Italic:
            font.setItalic(True)
            font.setBold(False)
        elif font_style == FontStyle.BoldItalic:
            font.setBold(True)
            font.setItalic(True)
        else:  # font_styles.py.Normal
            font.setBold(False)
            font.setItalic(False)

        font.setPixelSize(self.font_size)  # Set the font size to 20
        self.label.setFont(font)  # Apply the font style to the label

    def _check_text_fit(self):
        """Determine if text needs scrolling."""
        font_metrics = QFontMetrics(self.label.font())
        text_width = font_metrics.horizontalAdvance(self.label.text())

        # Adjust width if the font is italic
        if self.label.font().italic():
            text_width = int(text_width * 1.1)  # Adjust for italic fonts

        # Calculate the available width
        label_width = self.rect().width() - 2 * self.label_margins

        logger.debug(f"Text: {self.label.text()}")
        logger.debug(f"Label width: {label_width}, Text width: {text_width}")

        # Set the label width to the text width
        self.label.setFixedWidth(text_width)

        # Activate scrolling if text is wider than available space
        if text_width > label_width:
            if not self.text_scroll_active:
                self.text_scroll_active = True
                logger.debug("Scrolling activated")
                self.pause_state = 1
                self.pause_counter = 0
                self.timer.start()
        else:
            if self.text_scroll_active:
                self.text_scroll_active = False
                logger.debug("Scrolling deactivated")
                self.timer.stop()
                self._center_y_move_to_x(0)  # Reset position

    def _scroll_text(self):
        """Animate scrolling text with pauses."""
        if not self.text_scroll_active:
            return

        font_metrics = QFontMetrics(self.label.font())
        text_width = font_metrics.horizontalAdvance(self.label.text())

        # Adjust width if the font is italic
        if self.label.font().italic():
            text_width = int(text_width * 1.1)

        # Calculate the available width
        label_width = self.width() - 2 * self.label_margins

        # Handle pause states
        if self.pause_state == 1:  # Pause at start
            self.pause_counter += 1
            if self.pause_counter < self.PAUSE_DURATION_AT_START:
                return
            self.pause_state = 0  # Move to scrolling state
            self.pause_counter = 0

        elif self.pause_state == 2:  # Pause at end
            self.pause_counter += 1
            if self.pause_counter < self.PAUSE_DURATION_AT_END:
                return
            # Reset for next cycle
            self.text_scroll_pos = 0
            self.pause_state = 1  # Back to start pause
            self.pause_counter = 0
            self._center_y_move_to_x(0)  # Reset position
            return

        # Update scroll position during scrolling state
        self.text_scroll_pos += self.scroll_speed

        # Check if we've reached the end of the text
        if self.text_scroll_pos > text_width - label_width:
            self.pause_state = 2  # Switch to end pause
            self.pause_counter = 0
            return

        # Update label position
        self._center_y_move_to_x(-self.text_scroll_pos)

    def _center_y_move_to_x(self, pos_x: int = 0):
        """Center the label vertically within the container and set horizontal position."""
        vertical_center = (self.height() - self.label.height()) // 2
        self.label.move(pos_x, vertical_center)

    def sizeHint(self):
        """Return a sensible size hint for the widget."""
        return self.label.sizeHint()
