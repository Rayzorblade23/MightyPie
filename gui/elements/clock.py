import sys

from PyQt6.QtCore import Qt, QTimer, QTime, QDate
from PyQt6.QtGui import QPainter
from PyQt6.QtWidgets import QApplication, QLabel, QGraphicsScene, QGraphicsView, QVBoxLayout, QHBoxLayout, QWidget

from data.config import CONFIG


class Clock(QWidget):
    """A clock with no seconds and a 50% transparent background."""

    def __init__(self, obj_name: str = "Clock", parent=None):
        super().__init__(parent)
        self.obj_name = obj_name

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)  # Add horizontal margins

        self.is_opaque = True

        self.scene = QGraphicsScene(self)
        self.view = QGraphicsView(self.scene, self)
        self.view.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.view.setObjectName(self.obj_name)
        self.setObjectName(self.obj_name)
        self.setWindowTitle(f"{CONFIG.INTERNAL_PROGRAM_NAME} - Clock")  # Set the window title
        self.setup_window()

        # Create a QWidget to hold the labels
        container = QWidget(self)
        date_time_layout = QHBoxLayout(container)
        date_time_layout.setContentsMargins(0, 0, 0, 0)
        date_time_layout.setSpacing(0)

        # # Add a spacer of 10px vertically between the widgets
        # spacer = QSpacerItem(10, 10, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        # date_time_layout.addItem(spacer)  # Add spacer to the layout

        # Date label
        self.date_label = QLabel()
        self.date_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignCenter)
        date_time_layout.addWidget(self.date_label)

        # Time label
        self.time_label = QLabel()
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignCenter)
        date_time_layout.addWidget(self.time_label)

        self.date_label.setObjectName("ClockLabel")
        self.time_label.setObjectName("ClockLabel")

        # Set the width of the labels based on the text width
        self.date_label.setFixedWidth(80)
        self.time_label.setFixedWidth(34)

        # Add container to main layout
        layout.addWidget(container)

        self.setLayout(layout)

        # Timer to update the clock
        timer = QTimer(self)
        timer.timeout.connect(self.update_time)
        timer.start(1000)
        self.update_time()

        # Set initial size and move to the upper right corner
        self.resize(130, 30)

        # Set a minimum size or use resize() to adjust window size
        self.view.setGeometry(0, 0, self.width(), self.height())
        self.scene.setSceneRect(0, 0, self.width(), self.height())
        self.position_clock()
        self.toggle_background()

        screen = QApplication.primaryScreen()
        screen.geometryChanged.connect(self.handle_geometry_change)

    def handle_geometry_change(self):
        screen = QApplication.primaryScreen()
        geometry = screen.geometry()

        x = geometry.width() - self.width() - 25
        y = 0
        self.move(x, y)

    def setup_window(self):
        """Set up the main window properties."""
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)  # Make the window click-through
        # Combine FramelessWindowHint and WindowStaysOnTopHint
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint)

    def position_clock(self):
        """Move the clock to the upper right corner of the primary screen."""
        screen_geometry = QApplication.primaryScreen().geometry()
        x = screen_geometry.width() - self.width() - 25
        y = 0
        self.move(x, y)

    def update_time(self):
        """Update the displayed time (with seconds) and date."""
        current_date = QDate.currentDate()
        weekday_abbr = current_date.toString("ddd")  # Abbreviated weekday (e.g., Mon, Tue)
        day_of_month = current_date.toString("d")  # Day of the month as a number (e.g., 8)
        month_abbr = current_date.toString("MMM")  # Abbreviated month (e.g., Jan)

        # Add suffix for the day (e.g., 1st, 2nd, 3rd, 4th...)
        day_suffix = "th" if 10 <= int(day_of_month) <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(int(day_of_month) % 10, "th")
        day_with_suffix = f"{day_of_month}{day_suffix}"

        # Including seconds in time format: "hh:mm:ss"
        current_time = QTime.currentTime().toString("hh:mm")  # Current time with seconds

        # Set the date and time labels separately
        self.date_label.setText(f"{weekday_abbr} {day_with_suffix} {month_abbr}")
        self.time_label.setText(current_time)

    def toggle_background(self):
        if self.is_opaque:  # If the background is currently opaque, set it to transparent.
            self.set_transparent_background()
        else:  # If the background is currently transparent, set it to opaque.
            self.set_opaque_background()

        # Toggle the background state for next time
        self.is_opaque = not self.is_opaque

    # To set the widget background to opaque (solid color)
    def set_opaque_background(self):
        self.setStyleSheet("""
            QWidget#Clock {
                background-color: #a181dd;  /* Opaque blue background */
            }
        """)

    # To set the widget background to transparent
    def set_transparent_background(self):
        self.setStyleSheet("""
            QWidget#Clock {
                background-color: rgba(255, 255, 0, 0);  /* Fully transparent background */
            }
        """)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Load the QSS template
    with open("../../style.qss", "r") as file:
        qss_template = file.read()

    qss = (qss_template
           .replace("{{accent_color}}", CONFIG.ACCENT_COLOR)
           .replace("{{accent_muted}}", CONFIG.ACCENT_COLOR_MUTED)
           .replace("{{bg_color}}", CONFIG.BG_COLOR))

    app.setStyleSheet(qss)

    clock = Clock("Clock")
    clock.show()  # Explicitly show the clock widget

    sys.exit(app.exec())
