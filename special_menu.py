import sys

from PyQt6.QtCore import Qt, QEvent, QTimer, pyqtSignal
from PyQt6.QtGui import QPainter, QKeyEvent, QCursor
from PyQt6.QtWidgets import QApplication, QGraphicsView, QGraphicsScene, QWidget, QVBoxLayout, QHBoxLayout

from GUI.toggle_switch import ToggleSwitch
from clock import Clock
from config import CONFIG
from events import taskbar_event
from functions.taskbar_hide_utils import toggle_taskbar, is_taskbar_visible
from invisible_ui import InvisibleUI
from windows_shortcuts_menu import WindowsSettingsMenu


class SpecialMenu(QWidget):
    taskbar_visibility_changed = pyqtSignal(bool)  # Custom signal

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

        # Taskbar toggle switch
        self.taskbar_toggle = ToggleSwitch(
            "TaskbarToggle",
            label_text="Toggle Taskbar",
            on_action=self.toggle_taskbar_action,
            off_action=self.toggle_taskbar_action,
            parent=self
        )
        layout.addWidget(self.taskbar_toggle)

        # Initialize the taskbar visibility based on current state
        self.initialize_taskbar_toggle()

        # Subscribe to the taskbar visibility event
        taskbar_event.visibility_changed.connect(self.update_taskbar_toggle)

        self.clock = Clock()
        self.clock_toggle = ToggleSwitch("ClockToggle",
                                         label_text="Clock!",
                                         on_action=lambda: (self.clock.show(),
                                                            self.clock_bg_toggle.setDisabled(False)),

                                         off_action=lambda: (self.clock.hide(),
                                                             self.clock_bg_toggle.setDisabled(True)),
                                         parent=self)

        self.clock_bg_toggle = ToggleSwitch("ClockBgToggle",
                                            label_text="Clock: Opaque Background",
                                            on_action=lambda: self.clock.toggle_background(),
                                            off_action=lambda: self.clock.toggle_background(),
                                            parent=self)
        QTimer.singleShot(0, self.trigger_toggle)

        self.invisible_UI = InvisibleUI()
        self.invisible_UI_toggle = ToggleSwitch("InvisibleUIToggle",
                                                label_text="Invisible UI",
                                                on_action=lambda: (self.invisible_UI.show(),
                                                                   self.invisible_UI_visibility_toggle.setDisabled(False),
                                                                   self.invisible_UI_visibility_toggle.update()),

                                                off_action=lambda: (self.invisible_UI.hide(),
                                                                    self.invisible_UI_visibility_toggle.setDisabled(True),
                                                                    self.invisible_UI_visibility_toggle.update()),
                                                parent=self)

        self.invisible_UI_visibility_toggle = ToggleSwitch("InvisibleUIVisibilityToggle",
                                                           label_text="Make visible",
                                                           on_action=lambda: self.invisible_UI.setStyleSheet("background-color: red;"),
                                                           off_action=lambda: self.invisible_UI.setStyleSheet(
                                                               "background-color: rgba(20, 20, 255, 2);"),
                                                           parent=self)

        # self.tray_icon_menu = TrayIconButtonsWindow(parent=self)
        # layout.addWidget(self.tray_icon_menu)

        self.windows_settings_shortcuts = WindowsSettingsMenu(parent=self)

        # Create toggles for Clock
        layout_clock = QHBoxLayout()
        layout_clock.addWidget(self.clock_toggle)
        layout_clock.addWidget(self.clock_bg_toggle)
        layout.addLayout(layout_clock)

        # Create toggles for Invisible UI
        layout_invisUI = QHBoxLayout()
        layout_invisUI.addWidget(self.invisible_UI_toggle)
        layout_invisUI.addWidget(self.invisible_UI_visibility_toggle)
        layout.addLayout(layout_invisUI)

        layout.addWidget(self.windows_settings_shortcuts)

        self.setLayout(layout)

        # Set a minimum size or use resize() to adjust window size
        self.resize(self.sizeHint())  # Resize based on the sizeHint of the widget
        self.view.setGeometry(0, 0, self.width(), self.height())
        self.scene.setSceneRect(0, 0, self.width(), self.height())

        # Set the widget to accept focus
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        # Install the event filter
        QApplication.instance().installEventFilter(self)

    def initialize_taskbar_toggle(self):
        """Initialize the taskbar toggle based on the current visibility state."""
        if is_taskbar_visible():  # Check if the taskbar is visible
            self.taskbar_toggle.toggle.setCheckedWithoutAction(True)  # Taskbar is visible, toggle should be on
        else:
            self.taskbar_toggle.toggle.setCheckedWithoutAction(False)  # Taskbar is hidden, toggle should be off

    def toggle_taskbar_action(self):
        """Action to toggle the taskbar visibility."""
        toggle_taskbar()  # Call the function that toggles the taskbar visibility

    def update_taskbar_toggle(self, is_visible):
        """Update the taskbar toggle based on visibility."""
        if is_visible:
            self.taskbar_toggle.toggle.setCheckedWithoutAction(True)
        else:
            self.taskbar_toggle.toggle.setCheckedWithoutAction(False)

    def trigger_toggle(self):
        self.clock_toggle.toggle.setChecked(True)  # or False
        self.clock_toggle.toggle.toggle_switch()
        self.invisible_UI_toggle.toggle.setChecked(True)  # or False
        self.invisible_UI_toggle.toggle.toggle_switch()

    def setup_window(self):
        """Set up the main window properties."""
        self.setWindowTitle("Special Menu")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)

    def closeEvent(self, event):
        """Hide the window instead of closing it."""
        self.hide()
        event.ignore()  # Prevent the default close behavior

    def focusOutEvent(self, event):
        """Hide the window when it loses focus, but not if the focus is from clicking inside the menu."""
        # Check if the mouse is still inside the window when the event occurs
        if not self.rect().contains(self.mapFromGlobal(QCursor.pos())):
            self.hide()
        else:
            event.ignore()  # Ignore the event so the menu doesn't hide

    def keyPressEvent(self, event: QKeyEvent):
        """Hide the window when pressing the Escape key."""
        if event.key() == Qt.Key.Key_Escape:
            self.hide()
        else:
            super().keyPressEvent(event)  # Pass other key events to the parent

    def eventFilter(self, obj, event):
        """Event filter to track mouse clicks outside the window."""
        if event.type() == QEvent.Type.MouseButtonPress:
            if self.isVisible() and not self.rect().contains(event.pos()):
                self.hide()  # Hide the window if clicked outside
        return super().eventFilter(obj, event)


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
