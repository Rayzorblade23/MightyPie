import sys

from PyQt6.QtCore import Qt, QEvent, QTimer
from PyQt6.QtGui import QPainter, QKeyEvent, QCursor
from PyQt6.QtWidgets import QApplication, QGraphicsView, QGraphicsScene, QWidget, QVBoxLayout, QHBoxLayout

from clock import Clock
from config import CONFIG
from invisible_ui import InvisibleUI
from functions.taskbar_hide_utils import toggle_taskbar_autohide, hide_taskbar, show_taskbar
from GUI.toggle_switch import ToggleSwitch
from tray_menu import TrayIconButtonsWindow
from windows_settings_menu import WindowsSettingsMenu


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

        self.is_taskbar_hidden = False

        self.taskbar_toggle = ToggleSwitch("TaskbarToggle",
                                           label_text="Hide the Taskbar (takes 5 secs)",
                                           on_action=lambda: self.toggle_taskbar(True),
                                           off_action=lambda: self.toggle_taskbar(False),
                                           parent=self)

        self.clock = Clock()
        self.clock_toggle = ToggleSwitch("ClockToggle",
                                         label_text="Clock!",
                                         on_action=lambda: self.clock.show(),
                                         off_action=lambda: self.clock.hide(),
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
                                                on_action=lambda: self.invisible_UI.show(),
                                                off_action=lambda: self.invisible_UI.hide(),
                                                parent=self)

        self.invisible_UI_visibility_toggle = ToggleSwitch("InvisibleUIVisibilityToggle",
                                                label_text="Make visible",
                                                on_action=lambda: self.invisible_UI.setStyleSheet("background-color: red;"),
                                                off_action=lambda: self.invisible_UI.setStyleSheet("background-color: rgba(20, 20, 255, 2);"),
                                                parent=self)

        self.tray_icon_menu = TrayIconButtonsWindow(parent=self)

        self.windows_settings_shortcuts = WindowsSettingsMenu()

        layout.addWidget(self.taskbar_toggle)
        # Create toggles for Clock
        layout_clock = QHBoxLayout()
        layout_clock.addWidget(self.clock_toggle)
        layout_clock.addWidget(self.clock_bg_toggle)
        layout.addLayout(layout_clock)

        # Create toggles for Inivisble UI
        layout_invisUI = QHBoxLayout()
        layout_invisUI.addWidget(self.invisible_UI_toggle)
        layout_invisUI.addWidget(self.invisible_UI_visibility_toggle)
        layout.addLayout(layout_invisUI)

        layout.addWidget(self.windows_settings_shortcuts)
        layout.addWidget(self.tray_icon_menu)

        self.setLayout(layout)

        # Set a minimum size or use resize() to adjust window size
        self.resize(self.sizeHint())  # Resize based on the sizeHint of the widget
        self.view.setGeometry(0, 0, self.width(), self.height())
        self.scene.setSceneRect(0, 0, self.width(), self.height())

        # Set the widget to accept focus
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        # Install the event filter
        QApplication.instance().installEventFilter(self)

        self.taskbar_timer = QTimer(self)
        self.taskbar_timer.setInterval(20000)  # 10 seconds
        self.taskbar_timer.timeout.connect(self.periodically_hide_taskbar)

        # Start the timer when the taskbar is hidden
        self.taskbar_timer.start()

    def periodically_hide_taskbar(self):
        """Periodically hide the taskbar if it's supposed to be hidden."""
        if self.is_taskbar_hidden:
            hide_taskbar()  # Hide the taskbar again every 10 seconds

    def trigger_toggle(self):
        self.clock_toggle.toggle.setChecked(True)  # or False
        self.clock_toggle.toggle.toggle_switch()
        self.invisible_UI_toggle.toggle.setChecked(True)  # or False
        self.invisible_UI_toggle.toggle.toggle_switch()

    def toggle_taskbar(self, hide: bool):
        if hide:
            toggle_taskbar_autohide(True)
            hide_taskbar()
            self.is_taskbar_hidden = True
        else:
            show_taskbar()
            toggle_taskbar_autohide(False)
            self.is_taskbar_hidden = False

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
