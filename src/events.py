from PyQt6.QtCore import QEvent, pyqtSignal, QObject


class ShowWindowEvent(QEvent):
    def __init__(self, window, child_window=None):
        super().__init__(QEvent.Type(1000))  # Custom filtered_event type
        self.window = window
        self.child_window = child_window  # Store the child_window parameter


class HotkeyReleaseEvent(QEvent):
    def __init__(self, window, child_window=None):
        super().__init__(QEvent.Type(QEvent.registerEventType()))
        self.window = window
        self.child_window = child_window  # Store the child_window parameter


class TaskbarVisibilityEvent(QObject):
    visibility_changed = pyqtSignal(bool)  # Signal to notify visibility change


taskbar_event = TaskbarVisibilityEvent()
