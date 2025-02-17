# button_info_editor_utils.py

import logging
from functools import partial

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QMessageBox, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton, QFrame, QScrollArea

logging.basicConfig(level=logging.DEBUG)


def create_scroll_area():
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll_widget = QWidget()
    scroll_layout = QHBoxLayout(scroll_widget)
    scroll.setWidget(scroll_widget)
    return scroll, scroll_layout


def create_column(col, num_buttons, get_direction, create_button_frame):
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


def create_button_container(reset_to_defaults, save_changes):
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


def get_direction(row):
    directions = ["⭡", "⭧", "⭢", "⭨", "⭣", "⭩", "⭠", "⭦"]
    return directions[row] if row < len(directions) else ""


def reset_single_frame(sender, button_info, update_window_title):
    button_index = sender.property("button_index")
    if button_index is None:
        return

    button_frame = sender.parent()
    task_type_combo = button_frame.findChild(QComboBox)
    if task_type_combo:
        task_type_combo.setCurrentText("show_any_window")
        exe_name_combo = button_frame.findChild(QComboBox, None)
        if exe_name_combo and exe_name_combo != task_type_combo:
            exe_name_combo.setCurrentText("")
            exe_name_combo.setEnabled(False)
        button_info.update_button(button_index, {
            "task_type": "show_any_window",
            "properties": {"exe_name": ""}
        })
    update_window_title()


def reset_to_defaults(button_info, update_window_title, parent_widget):
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


def update_window_title(button_info, window):
    title = "Button Info Editor"
    if button_info.has_unsaved_changes:
        title += " *"
    window.setWindowTitle(title)


def create_texts_layout():
    texts_layout = QVBoxLayout()
    texts_layout.addWidget(QLabel("Task Type:"))
    texts_layout.addWidget(QLabel("Program:"))
    return texts_layout


def create_dropdowns_layout(task_type_combo, exe_name_combo):
    dropdowns_layout = QVBoxLayout()
    dropdowns_layout.addWidget(task_type_combo)
    dropdowns_layout.addWidget(exe_name_combo)
    return dropdowns_layout


def create_task_type_combo(task_types, current_task, index, on_task_type_changed):
    task_type_combo = QComboBox()
    for task_type in task_types:
        display_text = task_type.replace('_', ' ').title()
        task_type_combo.addItem(display_text, task_type)
    current_index = task_types.index(current_task["task_type"])
    task_type_combo.setCurrentIndex(current_index)
    task_type_combo.setProperty("button_index", index)
    task_type_combo.currentTextChanged.connect(lambda text: on_task_type_changed(task_types[task_type_combo.currentIndex()]))
    return task_type_combo


def create_exe_name_combo(exe_names, current_task, index, on_exe_index_changed, on_exe_name_changed):
    exe_name_combo = QComboBox()
    exe_name_combo.setProperty("button_index", index)
    exe_name_combo.blockSignals(True)

    if current_task["task_type"] == "show_any_window":
        exe_name_combo.setEnabled(False)
        exe_name_combo.setEditable(True)
        exe_name_combo.clear()
        exe_name_combo.setCurrentText("")
    elif current_task["task_type"] == "call_function":
        from data.button_functions import ButtonFunctions
        functions = ButtonFunctions().functions
        exe_name_combo.setEditable(False)
        exe_name_combo.setEnabled(True)
        for func_name, func_data in functions.items():
            exe_name_combo.addItem(func_data['text_1'], func_name)
        current_function = current_task["properties"].get("function_name", "")
        if current_function:
            for i in range(exe_name_combo.count()):
                if exe_name_combo.itemData(i) == current_function:
                    exe_name_combo.setCurrentIndex(i)
                    break
    else:
        exe_name_combo.setEditable(True)
        exe_name_combo.setEnabled(True)
        for exe_name, app_name in exe_names:
            display_text = f"({exe_name})" if not app_name.strip() else f"{app_name}"
            exe_name_combo.addItem(display_text, exe_name)
        current_exe_name = current_task["properties"].get("exe_name", "")
        if current_exe_name:
            for i in range(exe_name_combo.count()):
                if exe_name_combo.itemData(i) == current_exe_name:
                    exe_name_combo.setCurrentIndex(i)
                    break
        else:
            for i in range(exe_name_combo.count()):
                if exe_name_combo.itemData(i) == "explorer.exe":
                    exe_name_combo.setCurrentIndex(i)
                    break

    exe_name_combo.currentIndexChanged.connect(
        partial(on_exe_index_changed, button_index=index, combo=exe_name_combo)
    )
    exe_name_combo.editTextChanged.connect(lambda text, idx=index: on_exe_name_changed(text, idx))
    exe_name_combo.blockSignals(False)
    return exe_name_combo
