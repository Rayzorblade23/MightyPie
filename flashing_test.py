import sys
import threading
import time

import keyboard
from PyQt6.QtCore import Qt, QEvent
from PyQt6.QtGui import QCursor, QKeyEvent
from PyQt6.QtWidgets import QMainWindow, QGraphicsScene, QGraphicsView, QPushButton, QWidget, QApplication, QHBoxLayout

from config import CONFIG


class ShowWindowEvent_Test(QEvent):
    def __init__(self, window):
        super().__init__(QEvent.Type(1000))  # Custom filtered_event type
        self.window = window


def listen_for_hotkeys(window: QWidget):
    """Listen for global hotkeys."""

    def on_press():
        print("Hotkey pressed! Opening switcherino...")
        show_event = ShowWindowEvent_Test(window)
        QApplication.postEvent(window, show_event)

    keyboard.on_press_key(CONFIG.HOTKEY_OPEN, lambda _: on_press(), suppress=True)
    keyboard.wait()


class PieWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # Make the window transparent and translucent with no frame
        self.setStyleSheet("background-color: rgba(255,255,255,0.5); border: none;")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)  # Removes the window's title bar and border
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)  # Make background translucent

        # Set the default cursor (normal arrow cursor)
        self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))  # Set the normal cursor

        # Create the scene and view for the left part of the screen
        self.scene = QGraphicsScene(self)
        self.view = QGraphicsView(self.scene, self)

        # Get the primary screen geometry
        screen_geometry = QApplication.primaryScreen().geometry()
        screen_width = screen_geometry.width() // 2
        screen_height = screen_geometry.height()

        # Set the main_window size to take the full screen
        self.setGeometry(0, 0, screen_width, screen_height)

        # Set the geometry of the QGraphicsView to take the left half
        self.view.setGeometry(0, 0, screen_width, screen_height)
        self.view.setObjectName("PieWindow")
        self.scene.setSceneRect(0, 0, screen_width, screen_height)

        # Create and add the child widget to the scene
        self.child = RedWidget()
        self.child.setParent(self)  # Make sure the child widget is a child of the main window
        # Create a green QPushButton

    def do_things_in_sequence(self):
        self.child.move_window()
        self.show()

    def event(self, event):
        """Handle the custom filtered_event to show the main_window."""
        if isinstance(event, ShowWindowEvent_Test):
            self.do_things_in_sequence()
        return super().event(event)

    def keyPressEvent(self, event: QKeyEvent):
        """Close the main_window on pressing the Escape key."""
        if event.key() == Qt.Key.Key_Escape:
            self.hide()
        else:
            super().keyPressEvent(event)  # Pass other key events to the parent


class RedWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Red Widget")
        self.setFixedSize(200, 200)  # Set fixed size to 200x200

        # Set background color of the widget to red using QSS
        self.setStyleSheet("RedWidget {background-color: red;}")  # Set red background using QSS

        # Create a green QPushButton using QSS
        self.button = QPushButton("Green Button", self)  # Create button as a child of RedWidget
        self.button.setStyleSheet("background-color: green; color: white;")  # Green button with white text

        # Create a layout and add the button to the layout
        layout = QHBoxLayout()
        layout.addWidget(self.button)

        # Set the layout for RedWidget
        self.setLayout(layout)

        self.flipflop = True

    def move_window(self):
        if self.flipflop:
            self.move(100, 100)
            self.flipflop = not self.flipflop
        else:
            self.move(500, 700)
            self.flipflop = not self.flipflop


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Create and show the main main_window
    window = PieWindow()

    # Show the main_window briefly and immediately hide it
    window.show()  # Make sure the main_window is part of the filtered_event loop

    event = ShowWindowEvent_Test(window)
    # Post the filtered_event to the main thread
    QApplication.postEvent(window, event)

    # Hotkey Thread
    hotkey_thread = threading.Thread(
        target=listen_for_hotkeys, args=(window,), daemon=True
    )
    hotkey_thread.start()


    sys.exit(app.exec())
