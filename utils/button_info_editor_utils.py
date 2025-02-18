# button_info_editor_utils.py

import logging
from typing import Callable, Tuple, Any

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton, QFrame, QScrollArea

logging.basicConfig(level=logging.DEBUG)


def create_scroll_area() -> Tuple[QScrollArea, QHBoxLayout]:
    """Creates a scroll area with a layout."""
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll_widget = QWidget()
    scroll_layout = QHBoxLayout(scroll_widget)
    scroll.setWidget(scroll_widget)
    return scroll, scroll_layout


def create_column(col: int, num_buttons: int, create_button_frame: Callable[[int, int], QWidget]) -> Tuple[QWidget, QVBoxLayout]:
    """Creates a column with buttons and a title label."""
    column_widget = QWidget()
    column_layout = QVBoxLayout(column_widget)

    title_label = QLabel(f"Pie Menu {col + 1}")
    title_label.setObjectName("titleLabel")
    title_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
    column_layout.addWidget(title_label)

    if col > 0:
        line = QFrame()
        line.setFrameStyle(QFrame.Shape.VLine.value)
        line.setLineWidth(1)
        column_layout.addWidget(line)

    for row in range(num_buttons):
        index = row + (col * num_buttons)
        button_frame = create_button_frame(index, row)
        column_layout.addWidget(button_frame)

    column_layout.addStretch()
    return column_widget, column_layout


def create_button_container(reset_to_defaults: Callable[[], None], save_changes: Callable[[], None]) -> QHBoxLayout:
    """Creates the layout for the button container with reset and save buttons."""
    button_container = QHBoxLayout()
    reset_button = QPushButton("Reset to Defaults")
    reset_button.setObjectName("buttonConfigButton")
    reset_button.clicked.connect(reset_to_defaults)
    button_container.addWidget(reset_button)

    save_button = QPushButton("Save Changes")
    save_button.setObjectName("buttonConfigButton")
    save_button.clicked.connect(save_changes)
    button_container.addWidget(save_button)
    return button_container


def get_direction(row: int) -> str:
    """Returns the direction symbol for the specified row."""
    directions = ["⭡", "⭧", "⭢", "⭨", "⭣", "⭩", "⭠", "⭦"]
    return directions[row] if row < len(directions) else ""


def update_window_title(config: Any, window: QWidget) -> None:
    """Updates the window title based on unsaved changes."""
    title = "Button Info Editor"
    if hasattr(config, 'has_changes') and config.has_changes():
        title += " *"
    elif hasattr(config, 'has_unsaved_changes') and config.has_unsaved_changes:
        title += " *"
    window.setWindowTitle(title)


def create_texts_layout() -> QVBoxLayout:
    """Creates the layout for task type and program labels."""
    texts_layout = QVBoxLayout()
    texts_layout.addWidget(QLabel("Task Type:"))
    texts_layout.addWidget(QLabel("Program:"))
    return texts_layout


def create_dropdowns_layout(task_type_dropdown: QComboBox, exe_name_dropdown: QComboBox) -> QVBoxLayout:
    """Creates the layout for task type and exe name dropdowns."""
    dropdowns_layout = QVBoxLayout()
    dropdowns_layout.addWidget(task_type_dropdown)
    dropdowns_layout.addWidget(exe_name_dropdown)
    return dropdowns_layout
