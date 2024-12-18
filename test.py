import re
import sys

from PyQt6.QtCore import Qt, QEvent, QPointF
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtWidgets import QApplication, QPushButton, QWidget


class MyWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Slice_01")

        # Enable hover events
        self.setAttribute(Qt.WidgetAttribute.WA_Hover)

        self.styles = self.extract_button_styles_from_global_stylesheet()

        # Now you can use these variables to set the styles dynamically
        self.button_style = self.styles["button"]
        self.hover_style = self.styles["hover"]
        self.pressed_style = self.styles["pressed"]

        print("Button Style:", self.button_style)
        print("Hover Style:", self.hover_style)
        print("Pressed Style:", self.pressed_style)
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
        self.is_released_inside_quadrant = False  # To track the release position

    def center_button(self):
        """Centers the button in the window."""
        button_width = 100
        button_height = 50
        self.button.setFixedSize(button_width, button_height)

        # Calculate center position
        center_x = (self.width() - button_width) // 2
        center_y = (self.height() - button_height) // 2

        # Set button geometry
        self.button.setGeometry(center_x // 2, center_y // 2, button_width, button_height)

    def eventFilter(self, watched, event):
        """Handles events globally for the window."""

        if event.type() == QEvent.Type.HoverMove:
            cursor_pos = event.position()

            # Check if the mouse is in the upper-left quadrant
            if cursor_pos.x() < self.width() // 2 and cursor_pos.y() < self.height() // 2:
                if not self.is_hovering:
                    print("Hover enter quadrant.")
                    self.set_hover_inside_style()  # Apply hover style when entering the quadrant
                    self.is_hovering = True  # Mark that we're hovering
                else:
                    print("Hovering in quadrant.")
            else:
                if self.is_hovering:
                    print("Hover leave quadrant.")
                    self.revert_hover_style()  # Revert style if leaving the quadrant
                    self.is_hovering = False  # Mark that we're not hovering anymore

        elif event.type() == QEvent.Type.HoverLeave:
            print("Hover leave (out of window).")
            self.revert_hover_style()  # Revert hover style when leaving
            self.is_hovering = False

        elif event.type() == QEvent.Type.MouseButtonPress:
            cursor_pos = event.position()

            # Check if the mouse press is in the upper-left quadrant
            if cursor_pos.x() < self.width() // 2 and cursor_pos.y() < self.height() // 2:
                print("Quadrant clicked!")
                self.set_clicked_inside_style()  # Set clicked inside style
                self.is_clicked = True
                self.is_released_inside_quadrant = False  # Reset, to track release position
                print("Button style set to clicked.")
                return True  # Block event propagation

        elif event.type() == QEvent.Type.MouseButtonRelease:
            cursor_pos = event.position()

            # Check if the mouse release is in the upper-left quadrant or button
            if cursor_pos.x() < self.width() // 2 and cursor_pos.y() < self.height() // 2:
                print("Quadrant released!")
                self.set_hover_inside_style()  # Revert to hover style
                self.is_released_inside_quadrant = True  # Mark that release happened inside the quadrant
                print("Button reverted to hover after release.")
            else:
                print("Release outside quadrant!")
                self.set_normal_style()  # Revert to held outside style
                self.is_released_inside_quadrant = False  # Reset to mark release happened outside
                print("Button style set to held outside after release outside quadrant.")

            self.is_clicked = False
            return True  # Block event propagation

        return super().eventFilter(watched, event)

    def set_hover_inside_style(self):
        """Set the hover style for inside state."""
        self.is_hovering = True
        self.button.setStyleSheet(self.hover_style)  # Hover inside style
        print("Button style set to hover inside.")

    def revert_hover_style(self):
        """Reverts to the normal style of the button."""
        self.is_hovering = False
        if self.is_clicked:
            self.set_clicked_style()  # If clicked, maintain clicked style
        else:
            self.set_normal_style()  # Normal style if not clicked

    def set_clicked_style(self):
        """Sets the clicked style for the button."""
        self.button.setStyleSheet(self.pressed_style)
        print("Button style set to clicked.")

    def set_normal_style(self):
        """Sets the normal style for the button."""
        self.button.setStyleSheet(self.button_style)
        print("Button style set to normal.")

    def set_clicked_inside_style(self):
        """Set the clicked inside style."""
        self.button.setStyleSheet(self.pressed_style)
        print("Button style set to clicked inside.")
        # Emit a proper click event
        press_event = QMouseEvent(
            QEvent.Type.MouseButtonPress,
            QPointF(self.button.rect().center()),  # Center position of the button
            Qt.MouseButton.LeftButton,  # Left mouse button
            Qt.MouseButton.LeftButton,  # Button state
            Qt.KeyboardModifier.NoModifier  # No keyboard modifiers
        )
        QApplication.sendEvent(self.button, press_event)  # Send press event to the button

        release_event = QMouseEvent(
            QEvent.Type.MouseButtonRelease,
            QPointF(self.button.rect().center()),  # Center position of the button
            Qt.MouseButton.LeftButton,  # Left mouse button
            Qt.MouseButton.LeftButton,  # Button state
            Qt.KeyboardModifier.NoModifier  # No keyboard modifiers
        )
        QApplication.sendEvent(self.button, release_event)  # Send release event to the button

    def print_message(self):
        """Prints a message when the button is clicked."""
        print("Button clicked!")

    def extract_button_styles_from_global_stylesheet(self):
        """Extracts the QPushButton styles (normal, hover, and pressed) from the global application stylesheet."""
        # Access the global stylesheet for the whole app
        global_stylesheet = QApplication.instance().styleSheet()

        # Regular expressions to match the styles for QPushButton, QPushButton:hover, QPushButton:pressed
        button_style_pattern = r"QPushButton\s*{(.*?)}"
        hover_style_pattern = r"QPushButton:hover\s*{(.*?)}"
        pressed_style_pattern = r"QPushButton:pressed\s*{(.*?)}"

        # Extract the content inside the curly braces for each selector using regex
        button_style = re.search(button_style_pattern, global_stylesheet, re.DOTALL)
        hover_style = re.search(hover_style_pattern, global_stylesheet, re.DOTALL)
        pressed_style = re.search(pressed_style_pattern, global_stylesheet, re.DOTALL)

        # Prepare and return a dictionary with the extracted styles or None if not found
        return {
            "button": button_style.group(1).strip() if button_style else None,
            "hover": hover_style.group(1).strip() if hover_style else None,
            "pressed": pressed_style.group(1).strip() if pressed_style else None
        }


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
