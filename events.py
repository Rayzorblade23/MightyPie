from PyQt6.QtCore import QEvent

class ShowWindowEvent(QEvent):
    def __init__(self, window):
        super().__init__(QEvent.Type(1000))  # Custom event type
        self.window = window
