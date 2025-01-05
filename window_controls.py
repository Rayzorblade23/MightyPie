from PyQt6.QtWidgets import QWidget, QHBoxLayout, QApplication
from config import CONFIG

from expanded_button import ExpandedButton


def create_window_controls(main_window):
    """Create minimize, maximize, and close buttons."""
    # Create main_window control buttons with fixed sizes and actions
    minimize_button = ExpandedButton(
        "_",
        "minimizeButton",
        fixed_size=True,
        size=(CONFIG.CONTROL_BUTTON_SIZE, CONFIG.CONTROL_BUTTON_SIZE),
    )
    close_button = ExpandedButton(
        "X",
        "closeButton",
        fixed_size=True,
        size=(CONFIG.CONTROL_BUTTON_SIZE, CONFIG.CONTROL_BUTTON_SIZE),
    )

    minimize_button.left_clicked.connect(main_window.showMinimized)
    close_button.left_clicked.connect(QApplication.quit)


    # Set up button layout
    button_layout = QHBoxLayout()
    button_layout.addWidget(minimize_button)
    button_layout.addWidget(close_button)
    button_layout.setSpacing(5)  # space between the elements
    button_layout.setContentsMargins(5, 5, 5, 5)  # space around the elements

    # Create a QWidget to hold the buttons and set the layout
    button_widget = QWidget(main_window)
    button_widget.setLayout(button_layout)
    button_widget.setObjectName("controlButtonWidget")
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
