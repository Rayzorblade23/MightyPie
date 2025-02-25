import sys
from typing import Optional

import mouse
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QRect
from PyQt6.QtGui import QPainter
from PyQt6.QtWidgets import QApplication, QGraphicsView, QGraphicsScene, QWidget, QVBoxLayout, QHBoxLayout

from data.config import CONFIG
from events import taskbar_event
from gui.elements.toggle_switch import ToggleSwitch
from gui.invisible_ui import InvisibleUI
from gui.menus.special_menu_DF_monitor_selector import MonitorSetupMenu
from gui.menus.special_menu_app_shortcuts import AppSettingsMenu
from gui.menus.special_menu_windows_shortcuts import WindowsSettingsMenu
from utils.program_utils import position_window_at_cursor
from utils.special_menu_utils import setup_startup_section, create_folder_buttons, add_separator_line, create_label
from utils.taskbar_hide_utils import toggle_taskbar, is_taskbar_visible


class SpecialMenu(QWidget):
    taskbar_visibility_changed = pyqtSignal(bool)  # Custom signal

    def __init__(self, obj_name: str = "", parent=None):
        super().__init__(parent)
        self.obj_name = obj_name

        self.scene: Optional[QGraphicsScene] = None
        self.view: Optional[QGraphicsView] = None

        # Initialize the window and layout
        self.setup_window()
        layout = QVBoxLayout(self)

        self.toggles_layout = QVBoxLayout()

        # Taskbar toggle
        self.taskbar_toggle = self.setup_taskbar_toggle()
        self.toggles_layout.addWidget(self.taskbar_toggle)

        # Initialize the taskbar visibility based on current state
        self.initialize_taskbar_toggle()

        # Subscribe to the taskbar visibility event
        taskbar_event.visibility_changed.connect(self.update_taskbar_toggle)

        # Invisible UI toggle
        self.setup_invisible_ui_toggle()

        QTimer.singleShot(0, self.trigger_toggle)

        # Startup section layout
        self.setup_startup_section()

        # Folder buttons layout
        self.setup_folder_buttons()

        self.windows_settings_shortcuts = WindowsSettingsMenu(parent=self)

        # Invisible UI layout
        self.setup_invisible_ui_layout()

        layout.addLayout(self.toggles_layout)

        add_separator_line(layout)

        windows_shortcuts_label = create_label("Windows Shortcuts")
        layout.addWidget(windows_shortcuts_label)
        layout.addWidget(self.windows_settings_shortcuts)

        add_separator_line(layout)

        if CONFIG.SHOW_MONITOR_SECTION:
            self.setup_monitor_shortcuts(layout)

        self.app_shortcuts = AppSettingsMenu(parent=self)
        app_shortcuts_label = create_label("Mighty Pie Shortcuts")
        layout.addWidget(app_shortcuts_label)
        layout.addWidget(self.app_shortcuts)

        self.setLayout(layout)

        # Set a minimum size or use resize() to adjust window size
        self.resize(self.sizeHint())  # Resize based on the sizeHint of the widget
        self.view.setGeometry(0, 0, self.width(), self.height())
        self.scene.setSceneRect(0, 0, self.width(), self.height())

        self.mouse_hook_active = False  # Track hook state

    def setup_taskbar_toggle(self) -> ToggleSwitch:
        """Sets up the taskbar toggle switch."""
        taskbar_toggle = ToggleSwitch(
            "TaskbarToggle",
            label_text="Toggle Taskbar Visibility",
            on_action=self.toggle_taskbar_action,
            off_action=self.toggle_taskbar_action,
            parent=self
        )
        return taskbar_toggle

    def setup_invisible_ui_toggle(self):
        """Sets up the invisible UI toggle and related visibility toggle."""
        self.invisible_UI = InvisibleUI()
        self.invisible_UI_toggle = ToggleSwitch("InvisibleUIToggle",
                                                label_text="Invisible UI",
                                                on_action=self.show_invisible_ui,
                                                off_action=self.hide_invisible_ui,
                                                parent=self)

        self.invisible_UI_visibility_toggle = ToggleSwitch("InvisibleUIVisibilityToggle",
                                                           label_text="Make visible",
                                                           on_action=self.make_invisible_ui_visible,
                                                           off_action=self.make_invisible_ui_invisible,
                                                           parent=self)

    def show_invisible_ui(self):
        """Show the invisible UI and enable the visibility toggle."""
        self.invisible_UI.show()
        self.invisible_UI_visibility_toggle.setDisabled(False)
        self.invisible_UI_visibility_toggle.update()

    def hide_invisible_ui(self):
        """Hide the invisible UI and disable the visibility toggle."""
        self.invisible_UI.hide()
        self.invisible_UI_visibility_toggle.setDisabled(True)
        self.invisible_UI_visibility_toggle.update()

    def make_invisible_ui_visible(self):
        """Set the invisible UI's background color to red."""
        self.invisible_UI.setStyleSheet("background-color: red;")

    def make_invisible_ui_invisible(self):
        """Reset the invisible UI's background color."""
        self.invisible_UI.setStyleSheet("background-color: rgba(20, 20, 255, 2);")

    def setup_startup_section(self):
        """Sets up the startup section layout and adds it to the main layout."""
        layout_startup = setup_startup_section(self)
        self.toggles_layout.addLayout(layout_startup)

    def setup_folder_buttons(self):
        """Sets up the folder buttons layout and adds it to the main layout."""
        layout_app_folders = create_folder_buttons(self)
        self.toggles_layout.addLayout(layout_app_folders)

    def setup_invisible_ui_layout(self):
        """Sets up the Invisible UI toggle layout and adds it to the main layout."""
        layout_invisUI = QHBoxLayout()
        layout_invisUI.addWidget(self.invisible_UI_toggle)
        layout_invisUI.addWidget(self.invisible_UI_visibility_toggle)
        self.toggles_layout.addLayout(layout_invisUI)

    def setup_monitor_shortcuts(self, layout: QVBoxLayout):
        """Sets up the monitor shortcuts section and adds it to the layout."""
        monitor_shortcuts = MonitorSetupMenu(parent=self)
        monitors_label = create_label("Monitor Switching")
        layout.addWidget(monitors_label)
        layout.addWidget(monitor_shortcuts)
        add_separator_line(layout)

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
        # self.clock_toggle.toggle.setChecked(False)  # Clock turned off by default
        # self.clock_toggle.toggle.toggle_switch()
        self.invisible_UI_toggle.toggle.setChecked(True)  # or False
        self.invisible_UI_toggle.toggle.toggle_switch()

    def setup_window(self):
        """Set up the window as a popup so it hides when clicked outside."""
        self.scene = QGraphicsScene(self)
        self.view = QGraphicsView(self.scene, self)
        self.view.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.view.setObjectName(self.obj_name)
        self.setObjectName(self.obj_name)

        self.setWindowTitle("Special Menu")
        # For a popup, do not assign a parent (i.e. parent should be None)
        self.setWindowFlags(
            # Qt.WindowType.Popup |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    def show_menu(self) -> None:
        """Show the menu centered at the cursor."""
        position_window_at_cursor(self)
        self.show()
        self.raise_()
        self.activateWindow()

    def closeEvent(self, event):
        """Hide the window instead of closing it."""
        self.deactivate_mouse_hook()
        self.hide()
        event.ignore()  # Prevent the default close behavior

    def hideEvent(self, event):
        self.deactivate_mouse_hook()
        super().hideEvent(event)
        print("HIDE!")

    def is_click_within_bounds(self, mouse_x: int, mouse_y: int) -> bool:
        """Check if the click coordinates are within the bounds of the widget."""
        widget_rect = self.rect()  # Get the widget's bounding rectangle
        widget_x, widget_y = self.mapToGlobal(widget_rect.topLeft()).x(), self.mapToGlobal(widget_rect.topLeft()).y()
        # Check if the mouse click is within the widget's bounds
        return QRect(widget_x, widget_y, widget_rect.width(), widget_rect.height()).contains(mouse_x, mouse_y)

    def showEvent(self, event):
        """Called when the widget is shown (activates mouse hook)."""
        if not self.mouse_hook_active:
            mouse.hook(self.on_mouse_event)
            self.mouse_hook_active = True

    def on_mouse_event(self, event):
        """Handles global mouse events (only if active)."""
        if isinstance(event, mouse.ButtonEvent):
            # Get current mouse position for ButtonEvent
            current_x, current_y = mouse.get_position()

            if event.event_type in ['down', 'up', 'double']:  # Check for down, up, or double events
                # Check if the click happened inside the widget's bounds
                if not self.is_click_within_bounds(current_x, current_y):
                    # Defer hiding the widget to allow event processing to finish
                    QTimer.singleShot(0, self.hide)  # Delay hiding

    def deactivate_mouse_hook(self):
        """Deactivate mouse hook manually."""
        if self.mouse_hook_active:
            mouse.unhook(self.on_mouse_event)
            print("UNHOOKED")
            self.mouse_hook_active = False


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

    special_menu = SpecialMenu("SpecialMenu")
    special_menu.show()  # Show SpecialMenu as a standalone window

    sys.exit(app.exec())
