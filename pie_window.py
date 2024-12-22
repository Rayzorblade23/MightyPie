from PyQt6.QtCore import Qt
from PyQt6.QtGui import QMouseEvent, QKeyEvent, QCursor
from PyQt6.QtWidgets import QMainWindow, QGraphicsScene, QGraphicsView, QApplication, QScrollArea, QWidget, QVBoxLayout

from events import ShowWindowEvent
from pie_menu_task_switcher import PieMenuTaskSwitcher
from window_controls import create_window_controls
from window_functions import show_pie_window


class PieWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Set the default cursor (normal arrow cursor)
        self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))  # Set the normal cursor

        # Create the scene and view for the left part of the screen
        self.scene = QGraphicsScene(self)
        self.view = QGraphicsView(self.scene, self)

        # Get the primary screen geometry
        screen_geometry = QApplication.primaryScreen().geometry()
        screen_width = screen_geometry.width()
        screen_height = screen_geometry.height()

        # Set the main_window size to take the full screen
        self.setGeometry(0, 0, screen_width, screen_height)

        # Set the geometry of the QGraphicsView to take the left half
        self.view.setGeometry(0, 0, screen_width, screen_height)
        self.view.setObjectName("PieWindow")
        self.scene.setSceneRect(0, 0, screen_width, screen_height)

        self.setup_window()

        # Create PieMenuTaskSwitcher with this main_window as parent
        self.pm_task_switcher = PieMenuTaskSwitcher(parent=self)

        # Create main_window control buttons with fixed sizes and actions
        button_widget, minimize_button, close_button = create_window_controls(main_window=self)

    def closeEvent(self, event):
        """Hide the main_window instead of closing it."""
        self.hide()
        event.ignore()  # Prevent the default close behavior

    def mousePressEvent(self, event: QMouseEvent):
        """Close the main_window on any mouse button press."""
        if event.button() in (Qt.MouseButton.LeftButton, Qt.MouseButton.RightButton):
            self.hide()

    def keyPressEvent(self, event: QKeyEvent):
        """Close the main_window on pressing the Escape key."""
        if event.key() == Qt.Key.Key_Escape:
            self.hide()
        else:
            super().keyPressEvent(event)  # Pass other key events to the parent

    def setup_window(self):
        """Set up the main main_window properties."""
        self.setWindowTitle("Main Window with Graphics View and Task Switcher Pie")
        # Non-resizable main_window
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)

    def customEvent(self, event):
        """Handle the custom filtered_event to show the main_window."""
        if isinstance(event, ShowWindowEvent):
            self.pm_task_switcher.refresh()
            show_pie_window(event.window, self.pm_task_switcher)  # Safely call show_pie_window when the filtered_event is posted
