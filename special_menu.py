import sys

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QKeyEvent
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QGraphicsView, QGraphicsScene,
    QWidget, QVBoxLayout
)

from config import CONFIG
from toggle_switch import ToggleSwitch
from tray_menu import TrayIconButtonsWindow


class SpecialMenu(QWidget):
    def __init__(self, obj_name: str = "", parent=None):
        super().__init__(parent)
        self.obj_name = obj_name


        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.scene = QGraphicsScene(self)
        self.view = QGraphicsView(self.scene, self)
        self.view.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.view.setObjectName(self.obj_name)
        self.setObjectName(self.obj_name)
        self.setup_window()

        self.taskbar_toggle = ToggleSwitch("TaskbarToggle",
                                           label_text="Hide the Taskbar",
                                           on_action=lambda: print("Taskbar disappears."),
                                           off_action=lambda: print("Taskbar re-appears."),
                                           parent=self)

        self.tray_icon_menu = TrayIconButtonsWindow(parent=self)

        layout.addWidget(self.taskbar_toggle)
        layout.addWidget(self.tray_icon_menu)

        self.setLayout(layout)

        # Set a minimum size or use resize() to adjust window size
        self.resize(self.sizeHint())  # Resize based on the sizeHint of the widget
        self.view.setGeometry(0, 0, self.width(), self.height())
        self.scene.setSceneRect(0, 0, self.width(), self.height())

    def setup_window(self):
        """Set up the main main_window properties."""
        self.setWindowTitle("Special Menu")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)

    def closeEvent(self, event):
        """Hide the main_window instead of closing it."""
        print("Closing Time")
        self.hide()
        event.ignore()  # Prevent the default close behavior

    def focusOutEvent(self, event):
        """Close the window when it loses focus."""
        self.hide()  # This triggers the closeEvent
        super().focusOutEvent(event)  # Ensure the base class implementation is called

    def keyPressEvent(self, event: QKeyEvent):
        """Close the main_window on pressing the Escape key."""
        if event.key() == Qt.Key.Key_Escape:
            self.hide()
        else:
            super().keyPressEvent(event)  # Pass other key events to the parent


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

    special_menu = SpecialMenu("SpecialMenu")
    special_menu.show()  # Show SpecialMenu as a standalone window

    sys.exit(app.exec())

