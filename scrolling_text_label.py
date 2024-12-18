from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QFontMetrics
from PyQt6.QtWidgets import QLabel, QHBoxLayout, QSizePolicy, QWidget

from config import CONFIG
from font_styles import FontStyle


class ScrollingLabel(QWidget):
    """Label with scrolling text for long content."""

    def __init__(self, text: str = "", font_style: FontStyle = FontStyle.Normal, h_align: Qt.AlignmentFlag = Qt.AlignmentFlag.AlignLeft, v_offset: int = 0,
                 parent: QWidget = None):
        super().__init__(parent)

        # Initialize attributes for scrolling
        self.text_scroll_pos = 0
        self.text_scroll_active = False
        self.timer = QTimer(self)
        self.label_margins = CONFIG.PIE_TEXT_LABEL_MARGINS
        self.scroll_speed = CONFIG.PIE_TEXT_LABEL_SCROLL_SPEED
        self.scroll_update_interval = CONFIG.PIE_TEXT_LABEL_SCROLL_INTERVAL  # in ms
        self.h_align = h_align
        self.v_offset = v_offset

        # Pause parameters
        self.pause_state = 1
        self.pause_counter = 0
        self.PAUSE_DURATION_AT_START = 60
        self.PAUSE_DURATION_AT_END = 60

        # UI initialization
        self._container = QWidget(self)
        self.label = QLabel(self._container)

        self._initialize_ui()
        self.label.setText(text)
        self._check_text_fit()

        # Set the font style (based on the font_styles.py enum)
        self._set_font_style(font_style)

        # Configure timer
        self.timer.timeout.connect(self._scroll_text)
        self.timer.setInterval(self.scroll_update_interval)  # Timer interval for smoother scrolling

    def _initialize_ui(self):
        """Set up the container and layout."""
        self._container.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        # self.setStyleSheet("background-color: lightblue;")  # Set background color

        # Label to display text
        self.label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        # Allow label to expand beyond container width
        self.label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.label.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        # Layout for QLabel
        self.layout = QHBoxLayout(self._container)
        self.layout.setContentsMargins(0, 0, 0, 0)

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
        self._check_text_fit()

    def update_text(self, new_text: str):
        """Update the text of the scrolling label."""
        self.label.setText(new_text)
        self.text_scroll_pos = 0  # Reset scroll position
        self._check_text_fit()  # Re-evaluate if scrolling is needed

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
        self.label.setFont(font)  # Apply the font style to the label

    def _check_text_fit(self):
        """Determine if text needs scrolling."""
        font_metrics = QFontMetrics(self.label.font())
        text_width = font_metrics.horizontalAdvance(self.label.text())

        # Manually calculate the available width
        label_width = self.width() - 2 * self.label_margins

        if text_width > label_width:
            if not self.text_scroll_active:
                self.text_scroll_active = True
                self.timer.start()

                # Ensure label is wide enough to show full text
                self.label.setFixedWidth(text_width)
        else:
            if self.text_scroll_active:
                self.text_scroll_active = False
                self.timer.stop()

            # Reset label width and position
            self.label.setFixedWidth(text_width)

    def _scroll_text(self):
        """Animate scrolling text with pauses."""
        font_metrics = QFontMetrics(self.label.font())
        text_width = font_metrics.horizontalAdvance(self.label.text())

        # Manually calculate the available width
        label_width = self.width() - 2 * self.label_margins

        if text_width > label_width:
            # Handle pauses
            if self.pause_state == 1:  # Pause at start
                self.pause_counter += 1
                if self.pause_counter < self.PAUSE_DURATION_AT_START:
                    self._center_y_move_to_x(-self.text_scroll_pos)
                    return
                self.pause_state = 0
                self.pause_counter = 0

            if self.pause_state == 2:  # Pause at End
                self.pause_counter += 1
                if self.pause_counter < self.PAUSE_DURATION_AT_END:
                    self._center_y_move_to_x(-self.text_scroll_pos)
                    return
                self.text_scroll_pos = 0
                self.pause_state = 1
                self.pause_counter = 0

            # Update scroll position
            self.text_scroll_pos += self.scroll_speed

            # Check if scrolling needs to stop (text has moved out of view)
            if self.text_scroll_pos > text_width - label_width:
                self.pause_state = 2

            self._center_y_move_to_x(-self.text_scroll_pos)

        else:
            # Reset position if no scrolling is needed
            self._center_y_move_to_x(0)

    def _center_y_move_to_x(self, pos_x: int = 0):
        """Center the label vertically within the container."""
        vertical_center = (self.height() - self.label.height()) // 2
        self.label.move(pos_x, vertical_center)


# Example usage
if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication, QVBoxLayout, QWidget

    app = QApplication(sys.argv)

    # Load the stylesheet
    with open("style.qss", "r") as file:
        app.setStyleSheet(file.read())

    window = QWidget()
    layout = QVBoxLayout(window)

    label = ScrollingLabel("This is a very long text that should scroll smoothly if it doesn't fit in the label.",
                           FontStyle.Bold, h_align=Qt.AlignmentFlag.AlignLeft)
    label.setFixedSize(300, 50)
    layout.addWidget(label)

    label2 = ScrollingLabel("Short text or something.", font_style=FontStyle.Italic, h_align=Qt.AlignmentFlag.AlignLeft)
    label2.setFixedSize(300, 50)
    layout.addWidget(label2)

    label3 = ScrollingLabel("short is not what you'Re reading here this is super long man!", h_align=Qt.AlignmentFlag.AlignHCenter)
    label3.setFixedSize(300, 50)
    layout.addWidget(label3)

    window.show()
    sys.exit(app.exec())
