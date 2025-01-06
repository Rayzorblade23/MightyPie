from PyQt6.QtGui import QPainter
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QGraphicsView, QGraphicsScene,
    QPushButton, QWidget, QVBoxLayout
)
from PyQt6.QtCore import Qt
import sys

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

        self.toggle = ToggleSwitch("Something", label_text="Test Text", parent=self)

        buttons = ["Short", "Medium Button", "Long Button Text"]
        for i, text in enumerate(buttons):
            button = QPushButton(text)
            layout.addWidget(button)
        layout.addWidget(self.toggle)

        self.setLayout(layout)

        # Set a minimum size or use resize() to adjust window size
        self.resize(self.sizeHint())  # Resize based on the sizeHint of the widget


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = QMainWindow()
    special_menu = SpecialMenu("special_menu")
    window.setCentralWidget(special_menu)

    # Resize window based on content
    window.resize(special_menu.sizeHint())
    window.show()

    sys.exit(app.exec())
