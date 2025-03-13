import logging

from PyQt6.QtCore import Qt, QEvent
from PyQt6.QtGui import QColor, QKeySequence
from PyQt6.QtWidgets import (QMainWindow, QVBoxLayout, QHBoxLayout, QGridLayout,
                             QLabel, QLineEdit, QCheckBox, QSpinBox, QWidget,
                             QPushButton, QScrollArea, QMessageBox, QSizePolicy, QColorDialog, QComboBox)

from src.data.config import CONFIG, DefaultConfig
from src.gui.buttons.pie_menu_middle_button import PieMenuMiddleButton
from src.utils.icon_utils import get_icon
from src.utils.program_utils import restart_program

logger = logging.getLogger(__name__)


class NoScrollSpinBox(QSpinBox):
    """QScrollSpinBox that ignores mouse wheel scrolling."""

    def wheelEvent(self, event):
        event.ignore()  # Prevents the wheel from changing the selection


class NoScrollComboBox(QComboBox):
    """QComboBox that ignores mouse wheel scrolling."""

    def wheelEvent(self, event) -> None:
        """Disables scrolling in the dropdown box."""
        event.ignore()


class ConfigSettingsWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{CONFIG.INTERNAL_PROGRAM_NAME} Settings")
        self.setMinimumWidth(400)

        self._temp_hotkey = {}  # Initialize as a dictionary

        # Central widget and main layout
        central_widget = QWidget()
        main_layout = QVBoxLayout()

        # Scroll area for settings
        scroll_area = QScrollArea()
        scroll_content = QWidget()

        # Use a grid layout for uniform columns
        settings_layout = QGridLayout()
        settings_layout.setColumnStretch(0, 1)  # Label column
        settings_layout.setColumnStretch(1, 2)  # Input field column
        settings_layout.setColumnStretch(2, 0)  # Reset button column (minimal width)

        # Dynamic settings generation
        self.setting_widgets = {}
        for row, setting in enumerate(CONFIG.get_settings_for_ui()):
            self._create_setting_input(setting, settings_layout, row)

        scroll_content.setLayout(settings_layout)
        scroll_area.setWidget(scroll_content)
        scroll_area.setWidgetResizable(True)

        # Button layout
        button_layout = QHBoxLayout()

        # Save button
        save_button = QPushButton("Save Settings")
        save_button.clicked.connect(self.save_settings)

        # Save and Restart button
        save_and_restart_button = QPushButton("Save && Restart")
        save_and_restart_button.clicked.connect(self.save_settings_and_restart)

        # Reset button
        reset_button = QPushButton("Reset to Defaults")
        reset_button.clicked.connect(self.reset_to_defaults)

        # Assemble button layout
        button_layout.addWidget(save_button)
        button_layout.addWidget(save_and_restart_button)
        button_layout.addWidget(reset_button)

        # Version label
        version_label = QLabel(f"Version: {CONFIG.VERSION}")
        version_label.setAlignment(Qt.AlignmentFlag.AlignRight)

        # Assemble main layout
        main_layout.addWidget(version_label)
        main_layout.addWidget(scroll_area)
        main_layout.addLayout(button_layout)

        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)

    def _create_setting_input(self, setting, layout: QGridLayout, row):
        # Label
        label = QLabel(CONFIG.INTERNAL_SETTING_DISPLAY_NAMES.get(setting['name'], setting['name']))
        label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout.addWidget(label, row, 0)

        # Input based on type
        if setting['type'] == "<class 'bool'>":
            input_widget = QCheckBox()
            input_widget.setChecked(setting['value'])
            layout.addWidget(input_widget, row, 1)

        elif setting['type'] in ["<class 'int'>", "<class 'float'>"]:
            input_widget = NoScrollSpinBox()
            input_widget.setRange(1, 9999)  # Set appropriate min/max range
            input_widget.setValue(setting['value'])
            layout.addWidget(input_widget, row, 1)

        elif setting['name'] == "CENTER_BUTTON":  # Check if the setting is CENTER_BUTTON
            input_widget = NoScrollComboBox()
            for action in PieMenuMiddleButton.button_map.keys():
                input_widget.addItem(action)
            input_widget.setCurrentText(setting['value'])  # Set the current value
            layout.addWidget(input_widget, row, 1)

        elif setting['name'] == "HOTKEY_PRIMARY":
            input_widget = QLineEdit(str(setting['value']))
            input_widget.setPlaceholderText("Press key...")
            input_widget.installEventFilter(self)  # Capture key events

            # Temporarily store the hotkey input for HOTKEY_PRIMARY
            self._temp_hotkey["HOTKEY_PRIMARY"] = setting['value']
            layout.addWidget(input_widget, row, 1)

        elif setting['name'] == "HOTKEY_SECONDARY":
            input_widget = QLineEdit(str(setting['value']))
            input_widget.setPlaceholderText("Press key...")
            input_widget.installEventFilter(self)  # Capture key events

            # Temporarily store the hotkey input for HOTKEY_SECONDARY
            self._temp_hotkey["HOTKEY_SECONDARY"] = setting['value']
            layout.addWidget(input_widget, row, 1)

        elif setting['type'] == "<class 'str'>":  # Handle string type (color hex code)
            if str(setting['value']).startswith("#"):  # It's a color
                # Create a horizontal layout for color field and picker button
                color_field_layout = QHBoxLayout()
                color_field_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins

                input_widget = QLineEdit(str(setting['value']))
                color_palette_icon = get_icon("palette", is_inverted=True)

                # Create a color picker button
                color_picker_button = QPushButton()
                color_picker_button.setToolTip("Pick Color")
                color_picker_button.setFixedSize(24, 20)
                color_picker_button.setIcon(color_palette_icon)
                color_picker_button.setObjectName("buttonConfigSingleResetButton")
                color_picker_button.clicked.connect(lambda: self.pick_color(input_widget, color_picker_button))

                # Update the color preview
                color_picker_button.setStyleSheet(f"background-color: {input_widget.text()};")

                # Connect the QLineEdit to update the color picker button
                input_widget.textChanged.connect(lambda: self.update_color_preview(input_widget, color_picker_button))

                color_field_layout.addWidget(input_widget)
                color_field_layout.addWidget(color_picker_button)

                # Add the layout to the grid
                color_widget = QWidget()
                color_widget.setLayout(color_field_layout)
                layout.addWidget(color_widget, row, 1)
            else:
                input_widget = QLineEdit(str(setting['value']))
                layout.addWidget(input_widget, row, 1)
        else:
            input_widget = QLineEdit(str(setting['value']))
            layout.addWidget(input_widget, row, 1)

        input_widget.setObjectName(setting['name'])
        input_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setting_widgets[setting['name']] = input_widget

        # Reset button for this specific setting
        reset_button = QPushButton()
        reset_button.setToolTip("Reset")
        reset_button.setIcon(get_icon("restart", is_inverted=True))
        reset_button.setFixedSize(24, 20)
        reset_button.setObjectName("buttonConfigSingleResetButton")
        reset_button.clicked.connect(
            lambda _, widget=input_widget, setting_name=setting['name']: self.reset_single_setting(widget, setting_name))
        layout.addWidget(reset_button, row, 2)

    @staticmethod
    def update_color_preview(input_widget, color_picker_button):
        """Updates the color preview button when the QLineEdit text changes."""
        color_text = input_widget.text()
        if color_text.startswith("#"):  # Only update if the text is a valid hex code
            color_picker_button.setStyleSheet(f"background-color: {color_text};")

    def pick_color(self, input_widget, color_picker_button):
        """Opens a color picker and sets the selected color as a hex code in the QLineEdit."""
        initial_color = QColor(input_widget.text()) if input_widget.text().startswith("#") else QColor()
        color = QColorDialog.getColor(initial_color, self, "Pick a Color")

        if color.isValid():
            # Set the color as a hex string (e.g., #RRGGBB)
            hex_color = color.name()
            input_widget.setText(hex_color)

            # Update the color picker button's background color to match the selected color
            color_picker_button.setStyleSheet(f"background-color: {hex_color};")

    def save_settings(self):
        for name, widget in self.setting_widgets.items():
            value = self._get_widget_value(widget)

            # Handle saving hotkey correctly (store the hotkey as a string)
            if isinstance(widget, QLineEdit) and name in {'HOTKEY_PRIMARY', 'HOTKEY_SECONDARY'}:
                hotkey_string = self._temp_hotkey.get(name)  # Correctly fetch the hotkey string from _temp_hotkey
                if hotkey_string is None:
                    hotkey_string = value  # Fallback to the original value if no temp hotkey is set
                CONFIG.update_setting(name, hotkey_string)  # Save the hotkey string in the configuration
            else:
                CONFIG.update_setting(name, value)

        self.close()

    def save_settings_and_restart(self):
        for name, widget in self.setting_widgets.items():
            if isinstance(widget, QLineEdit) and name in {'HOTKEY_PRIMARY', 'HOTKEY_SECONDARY'}:
                value = self._temp_hotkey.get(name, widget.text())
            else:
                value = self._get_widget_value(widget)
            CONFIG.update_setting(name, value)
        restart_program()

    def reset_to_defaults(self):
        # Create a confirmation dialog
        reply = QMessageBox.question(
            self, 'Reset Confirmation',
            'Are you sure you want to reset all settings to default values?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Get default values from the original TaskPieSwitcherConfig
            default_config = DefaultConfig()

            # Update widgets with default values
            for name, widget in self.setting_widgets.items():
                default_value = getattr(default_config, name)

                if isinstance(widget, QCheckBox):
                    widget.setChecked(default_value)
                elif isinstance(widget, NoScrollSpinBox):
                    widget.setValue(default_value)
                elif isinstance(widget, QLineEdit):
                    widget.setText(str(default_value))
                    if name in {"HOTKEY_PRIMARY", "HOTKEY_SECONDARY"}:
                        self._temp_hotkey[name] = default_value
                elif isinstance(widget, NoScrollComboBox):
                    widget.setCurrentText(str(default_value))

                # Update the actual configuration
                CONFIG.update_setting(name, default_value)

            CONFIG.save_config()  # Save the config after resetting

            QMessageBox.information(self, 'Reset Complete', 'Settings have been reset to default values.')

    def reset_single_setting(self, widget, setting_name):
        """Resets the given setting to its default value."""
        default_config = DefaultConfig()
        default_value = getattr(default_config, setting_name)

        if isinstance(widget, QCheckBox):
            widget.setChecked(default_value)
        elif isinstance(widget, NoScrollSpinBox):
            widget.setValue(default_value)
        elif isinstance(widget, QLineEdit):
            widget.setText(str(default_value))
            # Update the temporary hotkey for hotkey fields
            if setting_name in {"HOTKEY_PRIMARY", "HOTKEY_SECONDARY"}:
                self._temp_hotkey[setting_name] = default_value
        elif isinstance(widget, NoScrollComboBox):
            widget.setCurrentText(str(default_value))

        CONFIG.update_setting(setting_name, default_value)
        CONFIG.save_config()

    @staticmethod
    def _get_widget_value(widget):
        if isinstance(widget, QCheckBox):
            return widget.isChecked()
        elif isinstance(widget, NoScrollSpinBox):
            return widget.value()
        elif isinstance(widget, QLineEdit):
            return widget.text()
        elif isinstance(widget, NoScrollComboBox):  # Handle NoScrollComboBox
            return widget.currentText()  # Get the current selected text of the combo box
        return None

    def eventFilter(self, obj, event):
        """Capture key press events for hotkey input and update QLineEdit."""
        if event.type() == QEvent.Type.KeyPress:
            if isinstance(obj, QLineEdit) and obj.placeholderText() == "Press key...":
                setting_name = obj.objectName()  # Get the setting name from the QLineEdit object

                # Get the integer value of the modifiers and combine with the key
                modifiers = event.modifiers().value  # Use .value to get an int from the KeyboardModifiers
                key = event.key()  # event.key() is already an int
                key_combination = modifiers | key

                key_sequence = QKeySequence(key_combination)
                hotkey_string = key_sequence.toString()

                # Remove the "Num" part from Numpad keys (e.g., Num+7 becomes 7)
                if "Num" in hotkey_string:
                    hotkey_string = hotkey_string.replace("Num", "")

                # Clean up extra "+" signs
                hotkey_string = hotkey_string.replace("++", "+").lstrip("+")

                obj.setText(hotkey_string)
                self._temp_hotkey[setting_name] = hotkey_string

                # Suppress the event so system actions aren't triggered
                event.accept()

                return True  # Prevent further processing of the event
        return super().eventFilter(obj, event)
