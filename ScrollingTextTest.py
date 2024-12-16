from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFontMetrics
from PyQt6.QtWidgets import QLabel, QHBoxLayout, QSpacerItem, QSizePolicy, QPushButton


class AnimatedButton(QPushButton):
    """Custom Button with text animation for long text."""

    def __init__(self, text="", parent=None):
        super().__init__(parent)

        # Initialize attributes
        self.text_scroll_pos = 0  # Tracks current scroll position
        self.text_scroll_active = False  # Indicates if scrolling is active
        self.timer = QTimer(self)  # Timer for animation
        self.margin = 10

        # Scrolling parameters
        self.scroll_speed = 1  # Pixel movement

        # Pause parameters
        self.pause_state = 1  # 0: scrolling, 1: start pause, 2: end pause
        self.pause_counter = 0
        self.start_pause_duration = 60  # 1 second (60 * 16ms)
        self.end_pause_duration = 60  # 0.5 seconds (30 * 16ms)

        # UI initialization
        self._container = QWidget(self)
        self.label = QLabel(self._container)

        self._initialize_ui()
        self.setText(text)  # Set initial text

        # Configure timer
        self.timer.timeout.connect(self._scroll_text)
        self.timer.setInterval(16)  # Smoother animation

    def _initialize_ui(self):
        """Set up the container and layout."""
        self.setText("")  # QPushButton text is empty; QLabel handles display.

        # Internal widget for layout
        self._container.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        # self._container.setStyleSheet("background: black;")

        # Label to display text
        self.label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        self.label.setStyleSheet("font-size: 16px; color: black;")
        self.label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        # Allow label to expand beyond button width
        self.label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

        # Layout for QLabel
        self.layout = QHBoxLayout(self._container)
        self.layout.setContentsMargins(0, 0, 0, 0)

        # create spacers to have margins for the scrolling
        self.spacer_left = QSpacerItem(self.margin, 0, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        self.spacer_right = QSpacerItem(self.margin, 0, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        self.layout.addSpacerItem(self.spacer_left)  # Add the label
        self.layout.addWidget(self.label)  # Add the label
        self.layout.addSpacerItem(self.spacer_right)  # Add the label

    def resizeEvent(self, event):
        """Adjust container size on resize."""
        super().resizeEvent(event)
        rect = self.rect()
        rect.setWidth(rect.width() - self.margin * 2)
        rect.moveLeft((self.rect().width() - rect.width()) // 2)
        self._container.setGeometry(rect)
        self._check_text_fit()

    def setText(self, text):
        """Update the label text."""
        self.label.setText(text)
        self.text_scroll_pos = 0
        self.pause_state = 1
        self.pause_counter = 0

        # Reset the label's position to ensure no jump
        vertical_center = (self.height() - self.label.height()) // 2
        self.label.move(-self.text_scroll_pos, vertical_center)

        self._check_text_fit()

    def _check_text_fit(self):
        """Determine if text needs scrolling."""
        font_metrics = QFontMetrics(self.label.font())
        text_width = font_metrics.horizontalAdvance(self.label.text())

        # Manually calculate the available width
        button_width = self.width() - 20  # Subtracting fixed padding (5px on each side)

        if text_width > button_width:
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
        button_width = self.width() - 2 * self.margin

        if text_width > button_width:
            # Handle pauses
            if self.pause_state == 1:  # Start pause
                self.pause_counter += 1
                if self.pause_counter < self.start_pause_duration:
                    # Align label during pause
                    vertical_center = (self.height() - self.label.height()) // 2
                    self.label.move(-self.text_scroll_pos, vertical_center)
                    return
                self.pause_state = 0
                self.pause_counter = 0

            if self.pause_state == 2:  # End pause
                self.pause_counter += 1
                if self.pause_counter < self.end_pause_duration:
                    # Align label during pause
                    vertical_center = (self.height() - self.label.height()) // 2
                    self.label.move(-self.text_scroll_pos, vertical_center)
                    return
                self.text_scroll_pos = 0
                self.pause_state = 1
                self.pause_counter = 0

            # Update scroll position
            self.text_scroll_pos += self.scroll_speed

            # Check direction change conditions
            if self.text_scroll_pos > text_width - button_width:
                self.pause_state = 2

            # Calculate vertical center
            vertical_center = (self.height() - self.label.height()) // 2

            # Move label (keeping it vertically centered)
            self.label.move(-self.text_scroll_pos, vertical_center)
        else:
            # Reset position if no scrolling is needed
            vertical_center = (self.height() - self.label.height()) // 2
            self.label.move(0, vertical_center)


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

    button = AnimatedButton("This is a very long text that should scroll smoothly if it doesn't fit in the button.")
    button.setFixedSize(300, 50)
    layout.addWidget(button)

    button2 = AnimatedButton("Short text.")
    button2.setFixedSize(300, 50)
    layout.addWidget(button2)

    window.show()
    sys.exit(app.exec())
