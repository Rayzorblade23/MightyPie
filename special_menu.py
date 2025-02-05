import os
import sys
from pathlib import Path

from PyQt6.QtCore import Qt, QEvent, QTimer, pyqtSignal, QProcess
from PyQt6.QtGui import QPainter, QKeyEvent, QCursor
from PyQt6.QtWidgets import QApplication, QGraphicsView, QGraphicsScene, QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton

from GUI.toggle_switch import ToggleSwitch
from config import CONFIG
from events import taskbar_event
from functions.icon_functions_and_paths import get_icon
from functions.taskbar_hide_utils import toggle_taskbar, is_taskbar_visible
from invisible_ui import InvisibleUI
from special_menu_DF_monitor_selector import MonitorSetupMenu
from special_menu_app_shortcuts import AppSettingsMenu
from special_menu_windows_shortcuts import WindowsSettingsMenu


class SpecialMenu(QWidget):
    taskbar_visibility_changed = pyqtSignal(bool)  # Custom signal

    def __init__(self, obj_name: str = "", parent=None, main_window=None):

        super().__init__(parent)
        self.obj_name = obj_name

        self.main_window = main_window

        layout = QVBoxLayout(self)

        self.scene = QGraphicsScene(self)
        self.view = QGraphicsView(self.scene, self)
        self.view.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.view.setObjectName(self.obj_name)
        self.setObjectName(self.obj_name)
        self.setup_window()

        toggles_layout = QVBoxLayout()

        # Taskbar toggle switch
        self.taskbar_toggle = ToggleSwitch(
            "TaskbarToggle",
            label_text="Toggle Taskbar",
            on_action=self.toggle_taskbar_action,
            off_action=self.toggle_taskbar_action,
            parent=self
        )
        toggles_layout.addWidget(self.taskbar_toggle)

        # Initialize the taskbar visibility based on current state
        self.initialize_taskbar_toggle()

        # Subscribe to the taskbar visibility event
        taskbar_event.visibility_changed.connect(self.update_taskbar_toggle)

        # self.clock = Clock()
        # self.clock_toggle = ToggleSwitch("ClockToggle",
        #                                  label_text="Clock!",
        #                                  on_action=lambda: (self.clock.show(),
        #                                                     self.clock_bg_toggle.setDisabled(False)),
        #
        #                                  off_action=lambda: (self.clock.hide(),
        #                                                      self.clock_bg_toggle.setDisabled(True)),
        #                                  parent=self)
        #
        # self.clock_bg_toggle = ToggleSwitch("ClockBgToggle",
        #                                     label_text="Clock: Opaque BG",
        #                                     on_action=lambda: self.clock.toggle_background(),
        #                                     off_action=lambda: self.clock.toggle_background(),
        #                                     parent=self)

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
        QTimer.singleShot(0, self.trigger_toggle)

        # Settings for Startup
        self.startup_toggle = ToggleSwitch(
            "StartupToggle",
            label_text="Start with Windows",
            on_action=None,
            off_action=None,
            parent=self)

        if getattr(sys, 'frozen', False):
            self.startup_toggle = ToggleSwitch(
                "StartupToggle",
                label_text="Start with Windows",
                on_action=SpecialMenu.add_to_startup,
                off_action=SpecialMenu.remove_from_startup,
                parent=self
            )
            toggles_layout.addWidget(self.startup_toggle)
            self.startup_toggle.toggle.setCheckedWithoutAction(SpecialMenu.is_in_startup())

        layout_startup = QHBoxLayout()
        layout_startup.setAlignment(Qt.AlignmentFlag.AlignLeft)  # Ensure left alignment

        if self.startup_toggle:
            layout_startup.addWidget(self.startup_toggle)
        toggles_layout.addLayout(layout_startup)

        # Button to open Startup Folder
        self.startup_folder_button = QPushButton(" Startup", self)
        self.startup_folder_button.setToolTip("Open Startup Folder")
        self.startup_folder_button.setIcon(get_icon("folder-up", is_inverted=True))
        self.startup_folder_button.clicked.connect(self.open_startup_folder)

        # Button to open App Data Folder
        self.app_config_folder_button = QPushButton(" App Data", self)
        self.app_config_folder_button.setToolTip(f"Open {CONFIG._PROGRAM_NAME} App Data Folder")
        self.app_config_folder_button.setIcon(get_icon("folder-settings", is_inverted=True))
        self.app_config_folder_button.clicked.connect(self.open_app_data_directory)

        # Button to open the Program Folder
        self.program_folder_button = QPushButton(" Program", self)
        self.program_folder_button.setToolTip(f"Open {CONFIG._PROGRAM_NAME} Program Folder")
        self.program_folder_button.setIcon(get_icon("folder-star", is_inverted=True))
        self.program_folder_button.clicked.connect(self.open_program_folder)

        layout_app_folders = QHBoxLayout()
        layout_app_folders.setAlignment(Qt.AlignmentFlag.AlignLeft)  # Ensure left alignment
        layout_app_folders.addWidget(self.startup_folder_button)
        layout_app_folders.addWidget(self.app_config_folder_button)
        layout_app_folders.addWidget(self.program_folder_button)
        toggles_layout.addLayout(layout_app_folders)

        # self.tray_icon_menu = TrayIconButtonsWindow(parent=self)
        # layout.addWidget(self.tray_icon_menu)

        self.windows_settings_shortcuts = WindowsSettingsMenu(parent=self)

        self.app_shortcuts = AppSettingsMenu(parent=self)

        # # Create toggles for Clock
        # layout_clock = QHBoxLayout()
        # layout_clock.addWidget(self.clock_toggle)
        # layout_clock.addWidget(self.clock_bg_toggle)
        # toggles_layout.addLayout(layout_clock)

        # Create toggles for Invisible UI
        layout_invisUI = QHBoxLayout()
        layout_invisUI.addWidget(self.invisible_UI_toggle)
        layout_invisUI.addWidget(self.invisible_UI_visibility_toggle)
        toggles_layout.addLayout(layout_invisUI)

        layout.addLayout(toggles_layout)

        line = QFrame()
        line.setFrameStyle(QFrame.Shape.HLine.value)
        line.setLineWidth(1)
        layout.addWidget(line)

        windows_shortcuts_label = QLabel(f"Windows Shortcuts")
        windows_shortcuts_label.setObjectName("titleLabel")
        windows_shortcuts_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(windows_shortcuts_label)
        layout.addWidget(self.windows_settings_shortcuts)

        line = QFrame()
        line.setFrameStyle(QFrame.Shape.HLine.value)
        line.setLineWidth(1)
        layout.addWidget(line)

        if CONFIG.SHOW_MONITOR_SECTION:
            self.monitor_shortcuts = MonitorSetupMenu(parent=self)

            monitors_label = QLabel(f"Monitor Switching")
            monitors_label.setObjectName("titleLabel")
            monitors_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
            layout.addWidget(monitors_label)
            layout.addWidget(self.monitor_shortcuts)

            line = QFrame()
            line.setFrameStyle(QFrame.Shape.HLine.value)
            line.setLineWidth(1)
            layout.addWidget(line)

        app_shortcuts_label = QLabel(f"Mighty Pie Shortcuts")
        app_shortcuts_label.setObjectName("titleLabel")
        app_shortcuts_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(app_shortcuts_label)
        layout.addWidget(self.app_shortcuts)

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
        # self.clock_toggle.toggle.setChecked(False)  # Clock turned off by default
        # self.clock_toggle.toggle.toggle_switch()
        self.invisible_UI_toggle.toggle.setChecked(True)  # or False
        self.invisible_UI_toggle.toggle.toggle_switch()

    def setup_window(self):
        """Set up the main window properties."""
        self.setWindowTitle("Special Menu")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)

    @staticmethod
    def is_portable():
        if not getattr(sys, 'frozen', False):
            return False
        exe_path = Path(sys.executable)
        program_files = os.environ.get('PROGRAMFILES', '')
        return not str(exe_path).startswith(program_files)

    @staticmethod
    def get_startup_folder():
        return os.path.join(os.getenv('APPDATA'), 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup')

    @staticmethod
    def add_to_startup():
        if not getattr(sys, 'frozen', False):
            return

        startup_path = os.path.join(SpecialMenu.get_startup_folder(), 'MightyPie.lnk')

        from win32com.client import Dispatch

        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(startup_path)
        shortcut.Targetpath = sys.executable
        shortcut.WorkingDirectory = os.path.dirname(sys.executable)
        shortcut.save()

    @staticmethod
    def remove_from_startup():
        if not getattr(sys, 'frozen', False):
            return

        startup_path = os.path.join(SpecialMenu.get_startup_folder(), 'MightyPie.lnk')
        try:
            os.remove(startup_path)
        except (OSError, WindowsError):
            pass

    @staticmethod
    def is_in_startup():
        if not getattr(sys, 'frozen', False):
            return False
        return os.path.exists(os.path.join(SpecialMenu.get_startup_folder(), 'MightyPie.lnk'))

    @staticmethod
    def _get_os_open_command():
        """Returns the appropriate file explorer command for the current OS."""
        os_commands = {
            "nt": "explorer",
            "posix": "xdg-open",
            "darwin": "open"
        }
        return os_commands.get(os.name, "xdg-open")

    @staticmethod
    def _open_folder(path):
        """Generic function to open a folder in the system's file explorer."""
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)

        command = SpecialMenu._get_os_open_command()
        QProcess.startDetached(command, [path])

    @staticmethod
    def open_program_folder():
        """Opens the folder where the program is located."""
        if getattr(sys, 'frozen', False):
            # Running in PyInstaller bundle
            program_dir = os.path.dirname(sys.executable)
        else:
            # Running in development
            program_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        SpecialMenu._open_folder(program_dir)

    @staticmethod
    def open_startup_folder():
        """Opens the system startup folder."""
        if os.name == "nt":
            startup_folder = os.path.join(os.getenv("APPDATA"), "Microsoft", "Windows", "Start Menu", "Programs", "Startup")
        else:
            # For macOS and Linux, you might want to implement their specific startup folder paths
            startup_folder = os.path.expanduser("~")
        SpecialMenu._open_folder(startup_folder)

    @staticmethod
    def open_app_data_directory():
        """Opens the application data directory where configs are saved."""
        base_dirs = {
            "nt": os.path.join(os.environ.get('APPDATA', ''), CONFIG._PROGRAM_NAME),
            "darwin": os.path.join(os.path.expanduser('~'), 'Library', 'Application Support', CONFIG._PROGRAM_NAME),
            "linux": os.path.join(os.path.expanduser('~'), '.config', CONFIG._PROGRAM_NAME)
        }
        config_dir = base_dirs.get(os.name, os.path.abspath('.'))
        SpecialMenu._open_folder(config_dir)

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
