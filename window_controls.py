from PyQt6.QtWidgets import QWidget, QHBoxLayout, QApplication
from config import CONFIG


def create_window_controls(main_window, create_button):
    """Create minimize, maximize, and close buttons."""
    # Create window control buttons with fixed sizes and actions
    minimize_button = create_button(
        "_",
        "minimizeButton",
        action=main_window.showMinimized,
        fixed_size=True,
        size=(CONFIG.CONTROL_BUTTON_SIZE, CONFIG.CONTROL_BUTTON_SIZE),
    )
    close_button = create_button(
        "X",
        "closeButton",
        action=QApplication.quit,
        fixed_size=True,
        size=(CONFIG.CONTROL_BUTTON_SIZE, CONFIG.CONTROL_BUTTON_SIZE),
    )

    # Set up button layout
    button_layout = QHBoxLayout()
    button_layout.addWidget(minimize_button)
    button_layout.addWidget(close_button)
    button_layout.setSpacing(5)  # space between the elements
    button_layout.setContentsMargins(5, 5, 5, 5)  # space around the elements

    # Create a QWidget to hold the buttons and set the layout
    button_widget = QWidget(main_window)
    button_widget.setLayout(button_layout)
    button_widget.setObjectName("buttonWidget")
    button_widget.adjustSize()

    # Position the button container widget
    control_button_width = button_widget.width()
    control_button_height = button_widget.height()
    spacing = 0
    button_widget.setGeometry(
        main_window.width() - control_button_width - spacing,
        spacing,
        control_button_width,
        control_button_height,
    )

    return button_widget, minimize_button, close_button
