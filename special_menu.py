import sys

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QGraphicsView, QGraphicsScene,
    QPushButton, QWidget, QVBoxLayout
)

from config import CONFIG
from toggle_switch import ToggleSwitch


class SpecialMenu(QWidget):
    def __init__(self, obj_name: str = "", parent=None):
        super().__init__(parent)
        self.obj_name = obj_name

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.scene = QGraphicsScene(self)
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.view.setObjectName(self.obj_name)

        self.taskbar_toggle = ToggleSwitch("TaskbarToggle",
                                           label_text="Hide the Taskbar",
                                           on_action=lambda: print("Taskbar disappears."),
                                           off_action=lambda: print("Taskbar re-appears."),
                                           parent=self)

        buttons = ["Short", "Medium Button", "Long Button Text"]
        for i, text in enumerate(buttons):
            button = QPushButton(text)
            layout.addWidget(button)
        layout.addWidget(self.taskbar_toggle)

        self.setLayout(layout)

        # Set a minimum size or use resize() to adjust window size
        self.resize(self.sizeHint())  # Resize based on the sizeHint of the widget


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Load the QSS template
    with open("style.qss", "r") as file:
        qss_template = file.read()

    # inserting style attributes from the config.py file
    qss = (qss_template
           .replace("{{accent_color}}", CONFIG.ACCENT_COLOR)
           .replace("{{accent_muted}}", CONFIG.ACCENT_COLOR_MUTED)
           .replace("{{bg_color}}", CONFIG.BG_COLOR))

    # Apply the QSS to the application or widgets
    app.setStyleSheet(qss)

    window = QMainWindow()
    special_menu = SpecialMenu("special_menu")
    window.setCentralWidget(special_menu)

    # Resize window based on content
    window.resize(special_menu.sizeHint())
    window.show()

    sys.exit(app.exec())
