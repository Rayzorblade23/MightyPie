import sys

from PyQt6.QtCore import Qt, QTimer, QTime, QDate
from PyQt6.QtGui import QFont, QPainter
from PyQt6.QtWidgets import QApplication, QLabel, QGraphicsScene, QGraphicsView, QFrame, QVBoxLayout, QHBoxLayout

from config import CONFIG


class TransparentClock(QFrame):
    """A clock with no seconds and a 50% transparent background."""

    def __init__(self, obj_name: str = "", parent=None):
        super().__init__(parent)
        self.obj_name = obj_name

        layout = QVBoxLayout(self)

        self.scene = QGraphicsScene(self)
        self.view = QGraphicsView(self.scene, self)
        self.view.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.view.setObjectName(self.obj_name)
        self.setObjectName(self.obj_name)
        self.setup_window()

        # Create a horizontal layout to hold both the date and time labels
        date_time_layout = QHBoxLayout()

        # Date label (left aligned)
        self.date_label = QLabel(self)
        self.date_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        date_time_layout.addWidget(self.date_label)

        # Time label (left aligned)
        self.time_label = QLabel(self)
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        date_time_layout.addWidget(self.time_label)

        layout.addLayout(date_time_layout)
        self.date_label.setObjectName("ClockLabel")
        self.time_label.setObjectName("ClockLabel")


        self.setLayout(layout)

        # Timer to update the clock
        timer = QTimer(self)
        timer.timeout.connect(self.update_time)
        timer.start(1000)
        self.update_time()

        # Set initial size and move to the upper right corner
        self.resize(145, 30)

        # Set a minimum size or use resize() to adjust window size
        self.view.setGeometry(0, 0, self.width(), self.height())
        self.scene.setSceneRect(0, 0, self.width(), self.height())
        self.move_to_top_right()

    def setup_window(self):
        """Set up the main window properties."""
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)  # Make the window click-through
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)

    def move_to_top_right(self):
        """Move the clock to the upper right corner of the primary screen."""
        screen_geometry = QApplication.primaryScreen().availableGeometry()
        x = screen_geometry.width() - self.width()
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


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Load the QSS template
    with open("style.qss", "r") as file:
        qss_template = file.read()

    qss = (qss_template
           .replace("{{accent_color}}", CONFIG.ACCENT_COLOR)
           .replace("{{accent_muted}}", CONFIG.ACCENT_COLOR_MUTED)
           .replace("{{bg_color}}", CONFIG.BG_COLOR))

    app.setStyleSheet(qss)

    clock = TransparentClock("Clock")
    clock.show()  # Explicitly show the clock widget

    sys.exit(app.exec())
