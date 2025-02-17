# button_info_editor_utils.py

import logging
from functools import partial
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QMessageBox, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton, QFrame, QScrollArea
from typing import Callable, List, Tuple, Dict, Any

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


def reset_single_frame(sender: QWidget, button_info: Any, update_window_title: Callable[[], None]) -> None:
    """Resets the specific button frame to its default state."""
    button_index = sender.property("button_index")
    if button_index is None:
        return

    button_frame = sender.parent()
    task_type_dropdown = button_frame.findChild(QComboBox)
    if task_type_dropdown:
        task_type_dropdown.setCurrentText("show_any_window")
        exe_name_dropdown = button_frame.findChild(QComboBox, None)
        if exe_name_dropdown and exe_name_dropdown != task_type_dropdown:
            exe_name_dropdown.setCurrentText("")
            exe_name_dropdown.setEnabled(False)
        button_info.update_button(button_index, {
            "task_type": "show_any_window",
            "properties": {"exe_name": ""}
        })
    update_window_title()


def reset_to_defaults(parent_widget: QWidget, button_info: Any) -> None:
    """Resets all settings to their default values."""
    reply = QMessageBox.question(
        None, "Reset Confirmation",
        "Are you sure you want to reset all settings to default?\nYou can still discard the changes afterwards.",
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
    )
    if reply == QMessageBox.StandardButton.Yes:
        for button_frame in parent_widget.findChildren(QFrame, "buttonConfigFrame"):
            task_type_combo = button_frame.findChild(QComboBox)
            if task_type_combo:
                button_index = task_type_combo.property("button_index")
                task_type_combo.setCurrentText("show_any_window")
                exe_name_combo = button_frame.findChild(QComboBox, None)
                if exe_name_combo and exe_name_combo != task_type_combo:
                    exe_name_combo.setCurrentText("")
                    exe_name_combo.setEnabled(False)
                button_info.update_button(button_index, {
                    "task_type": "show_any_window",
                    "properties": {"exe_name": ""}
                })
        update_window_title(button_info, parent_widget)


def update_window_title(button_info: Any, window: QWidget) -> None:
    """Updates the window title based on unsaved changes."""
    title = "Button Info Editor"
    if button_info.has_unsaved_changes:
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


def create_task_type_dropdown(task_types: List[str], current_button_info: Dict[str, Any], index: int, on_task_type_changed: Callable[[str], None]) -> QComboBox:
    """Creates a task type dropdown box with the available task types."""
    task_type_dropdown = QComboBox()
    for task_type in task_types:
        display_text = task_type.replace('_', ' ').title()
        task_type_dropdown.addItem(display_text, task_type)
    current_index = task_types.index(current_button_info["task_type"])
    task_type_dropdown.setCurrentIndex(current_index)
    task_type_dropdown.setProperty("button_index", index)
    task_type_dropdown.currentTextChanged.connect(lambda text: on_task_type_changed(task_types[task_type_dropdown.currentIndex()]))
    return task_type_dropdown


def create_value_dropdown(exe_names: List[Tuple[str, str]], current_button_info: Dict[str, Any], index: int,
                         on_value_index_changed: Callable[[Dict[str, Any], QComboBox], None],
                         on_value_changed: Callable[[str, int], None]) -> QComboBox:
    """Creates a dropdown box for selecting either an executable name or a function name."""
    value_dropdown = QComboBox()
    value_dropdown.setProperty("button_index", index)
    value_dropdown.blockSignals(True)

    if current_button_info["task_type"] == "show_any_window":
        value_dropdown.setEnabled(False)
        value_dropdown.setEditable(True)
        value_dropdown.clear()
        value_dropdown.setCurrentText("")
    elif current_button_info["task_type"] == "call_function":
        from data.button_functions import ButtonFunctions
        functions = ButtonFunctions().functions
        value_dropdown.setEditable(False)
        value_dropdown.setEnabled(True)
        for func_name, func_data in functions.items():
            value_dropdown.addItem(func_data['text_1'], func_name)
        current_function = current_button_info["properties"].get("function_name", "")
        if current_function:
            for i in range(value_dropdown.count()):
                if value_dropdown.itemData(i) == current_function:
                    value_dropdown.setCurrentIndex(i)
                    break
    else:
        value_dropdown.setEditable(True)
        value_dropdown.setEnabled(True)
        for exe_name, app_name in exe_names:
            display_text = f"({exe_name})" if not app_name.strip() else f"{app_name}"
            value_dropdown.addItem(display_text, exe_name)
        current_exe_name = current_button_info["properties"].get("exe_name", "")
        if current_exe_name:
            for i in range(value_dropdown.count()):
                if value_dropdown.itemData(i) == current_exe_name:
                    value_dropdown.setCurrentIndex(i)
                    break
        else:
            for i in range(value_dropdown.count()):
                if value_dropdown.itemData(i) == "explorer.exe":
                    value_dropdown.setCurrentIndex(i)
                    break

    value_dropdown.currentIndexChanged.connect(
        partial(on_value_index_changed, button_index=index, dropdown=value_dropdown)
    )
    value_dropdown.editTextChanged.connect(lambda text, idx=index: on_value_changed(text, idx))
    value_dropdown.blockSignals(False)
    return value_dropdown