import sys
from PyQt6.QtCore import Qt, QEvent, QPointF
from PyQt6.QtGui import QPainter, QMouseEvent
from PyQt6.QtWidgets import QApplication, QGraphicsView, QGraphicsScene, QPushButton, QWidget

class MyWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Stuapoid")

        # Enable hover events
        self.setAttribute(Qt.WidgetAttribute.WA_Hover)

        # Get screen size
        screen = QApplication.primaryScreen()
        size = screen.size()

        # Set window to span half the screen width and full screen height
        self.setGeometry(0, 0, size.width() // 2, size.height())  # Half the screen width, full height

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Create a button
        self.button = QPushButton("Click Me", self)
        self.button.clicked.connect(self.print_message)

        # Center the button in the window
        self.center_button()

        # Install the event filter on the window
        self.installEventFilter(self)

        self.is_hovering = False
        self.is_clicked = False

    def center_button(self):
        """Centers the button in the window."""
        button_width = 100
        button_height = 50
        self.button.setFixedSize(button_width, button_height)

        # Calculate center position
        center_x = (self.width() - button_width) // 2
        center_y = (self.height() - button_height) // 2

        # Set button geometry
        self.button.setGeometry(center_x, center_y, button_width, button_height)

    def eventFilter(self, watched, event):
        """Handles events globally for the window."""

        if event.type() == QEvent.Type.HoverMove:
            cursor_pos = event.position()

            # Check if the mouse is in the upper-left quadrant
            if cursor_pos.x() < self.width() // 2 and cursor_pos.y() < self.height() // 2:
                if not self.is_hovering:
                    self.simulate_hover()  # Apply hover style when entering the quadrant
                    self.is_hovering = True  # Mark that we're hovering
            else:
                if self.is_hovering:
                    self.revert_hover_style()  # Revert style if leaving the quadrant
                    self.is_hovering = False  # Mark that we're not hovering anymore

        elif event.type() == QEvent.Type.HoverLeave:
            self.revert_hover_style()  # Revert hover style when leaving
            self.is_hovering = False

        elif event.type() == QEvent.Type.MouseButtonPress:
            cursor_pos = event.position()

            # Check if the mouse press is in the upper-left quadrant
            if cursor_pos.x() < self.width() // 2 and cursor_pos.y() < self.height() // 2:
                print("Quadrant clicked!")
                self.simulate_click()  # Simulate button click
                self.is_clicking = True
                return True  # Block event propagation

        elif event.type() == QEvent.Type.MouseButtonRelease:
            cursor_pos = event.position()

            # Check if the mouse release is in the upper-left quadrant or button
            if cursor_pos.x() < self.width() // 2 and cursor_pos.y() < self.height() // 2:
                print("Quadrant released!")
                self.simulate_release()  # Simulate release if within the quadrant
            else:
                print("Release outside quadrant!")
                self.revert_hover_style()  # Revert to normal or hover style if outside
            self.is_clicking = False
            return True  # Block event propagation

        return super().eventFilter(watched, event)

    def simulate_hover(self):
        """Simulates a hover event on the button."""
        self.is_hovering = True  # Mark the button as hovered
        self.button.setStyleSheet("QPushButton { background-color: red; color: red; }")  # Hover style

    def revert_hover_style(self):
        """Reverts to the normal style of the button."""
        self.is_hovering = False  # Mark the button as not hovered
        if self.is_clicked:
            self.button.setStyleSheet("QPushButton { background-color: blue; color: white; border: none; }")  # Clicked style
        else:
            self.button.setStyleSheet("QPushButton { background-color: white; color: black; }")  # Normal style

    def simulate_click(self):
        """Simulates a click on the button and changes its style to blue on press."""
        self.is_clicked = True
        self.button.setStyleSheet("QPushButton { background-color: blue; color: white; border: none; }")  # Clicked style

        # Create a mouse press event at the button's center position
        press_event = QMouseEvent(
            QEvent.Type.MouseButtonPress,
            QPointF(self.button.rect().center()),  # Convert QPoint to QPointF
            Qt.MouseButton.LeftButton,  # Left button press
            Qt.MouseButton.LeftButton,  # Left button state
            Qt.KeyboardModifier.NoModifier  # No modifier keys
        )
        QApplication.sendEvent(self.button, press_event)  # Send press event

    def simulate_release(self):
        """Simulates a release on the button and resets the style."""
        self.is_clicked = False

        # Create a mouse release event at the button's center position
        release_event = QMouseEvent(
            QEvent.Type.MouseButtonRelease,
            QPointF(self.button.rect().center()),  # Convert QPoint to QPointF
            Qt.MouseButton.LeftButton,  # Left button release
            Qt.MouseButton.LeftButton,  # Left button state
            Qt.KeyboardModifier.NoModifier  # No modifier keys
        )
        QApplication.sendEvent(self.button, release_event)  # Send release event

        # Revert to hover or normal style after release
        if self.is_hovering:
            self.simulate_hover()  # Reapply hover style
        else:
            self.revert_hover_style()  # Revert to the original style if not hovering

    def print_message(self):
        """Prints a message when the button is clicked."""
        print("Button clicked!")


def clean_up():
    """Cleans up before exiting the application."""
    print("Cleaning up before exit...")
    QApplication.quit()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Set stylesheet (for UI styling)
    with open("style_test.qss", "r") as file:
        qss_template = file.read()

    app.setStyleSheet(qss_template)

    window = MyWindow()
    window.show()

    # Run the application
    sys.exit(app.exec())
