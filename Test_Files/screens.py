from PyQt6.QtGui import QGuiApplication
from PyQt6.QtCore import QObject
import sys


class ScreenChangeMonitor(QObject):
    def __init__(self, app):
        super().__init__()
        self.app = app

        # Keep track of the screens
        self.screens = {screen: screen.geometry() for screen in self.app.screens()}

        # Connect geometryChanged signal for each screen to handle_geometry_change method
        for screen in self.app.screens():
            screen.geometryChanged.connect(self.handle_geometry_change)

        # Initial state: print the initial geometry for each screen
        self.print_screen_info()

    def print_screen_info(self):
        """Prints the name and geometry of all screens."""
        for screen in self.app.screens():
            print(f"Screen {screen.name()} initial geometry: {screen.geometry()}")

    def handle_geometry_change(self):
        """Handle when the geometry of a screen changes."""
        screen = self.sender()  # Get the screen that emitted the signal
        if screen:
            geometry = screen.geometry()
            print(f"Screen {screen.name()} geometry changed: {geometry}")

            # If the geometry has changed, update the internal state
            if self.screens.get(screen) != geometry:
                print(f"Updated screen geometry for {screen.name()} : {geometry}")
                self.screens[screen] = geometry


if __name__ == "__main__":
    app = QGuiApplication(sys.argv)

    # Set up the monitor
    monitor = ScreenChangeMonitor(app)

    # Enter the event loop
    sys.exit(app.exec())
