# gui/menus/button_info_components.py
import logging
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QVBoxLayout, QLabel,
    QComboBox, QPushButton, QMessageBox
)

from src.utils.button_info_editor_utils import (
    get_direction, create_texts_layout,
    create_dropdowns_layout, update_window_title
)
from src.utils.icon_utils import get_icon

if TYPE_CHECKING:
    from src.gui.menus.button_info_editor import ButtonInfoEditor


class ButtonFrame(QFrame):
    class ButtonFrame(QFrame):
        """Frame containing configuration for a single button in the pie menu."""

    def __init__(self, index: int, row: int, editor: 'ButtonInfoEditor'):
        super().__init__()
        self.index = index
        self.row = row
        self.editor = editor
        self.setObjectName("buttonConfigFrame")
        self.init_ui()

    def init_ui(self) -> None:
        """Initialize the user interface components."""
        layout = QHBoxLayout(self)

        # Left side with index and direction
        index_layout = self._create_index_section()
        layout.addLayout(index_layout)

        # Content area with dropdowns
        content_layout = self._create_content_section()
        layout.addLayout(content_layout)

    def _create_index_section(self) -> QVBoxLayout:
        """Create the left section containing direction and reset button."""
        layout = QVBoxLayout()

        # Header with direction
        header_layout = QHBoxLayout()
        direction = get_direction(self.row)
        header_label = QLabel(f" {direction} ")
        header_label.setObjectName("buttonConfigFrameHeader")
        header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_label.setFixedSize(40, 40)
        header_layout.addStretch()
        header_layout.addWidget(header_label)
        header_layout.addStretch()

        # Reset button
        reset_button = self._create_reset_button()
        reset_layout = QVBoxLayout()
        reset_layout.addStretch()
        reset_layout.addWidget(reset_button, alignment=Qt.AlignmentFlag.AlignCenter)
        reset_layout.addStretch()

        layout.addLayout(header_layout)
        layout.addLayout(reset_layout)
        return layout

    def _create_reset_button(self) -> QPushButton:
        """Create a reset button with icon and tooltip."""
        reset_button = QPushButton()
        reset_button.setToolTip("Reset")
        reset_button.setIcon(get_icon("restart", is_inverted=True))
        reset_button.setFixedSize(24, 20)
        reset_button.setObjectName("buttonConfigSingleResetButton")
        reset_button.setProperty("button_index", self.index)
        reset_button.clicked.connect(self._on_reset_clicked)
        return reset_button

    def _create_content_section(self) -> QHBoxLayout:
        """Create the main content section with dropdowns."""
        content_layout = QHBoxLayout()
        current_button_info = self.editor.config_manager.get_current_config(self.index)

        task_type_dropdown, exe_name_dropdown = self.editor.create_dropdowns(
            current_button_info, self.index
        )

        content_layout.addLayout(create_texts_layout())
        content_layout.addLayout(create_dropdowns_layout(task_type_dropdown, exe_name_dropdown))
        return content_layout

    def _on_reset_clicked(self) -> None:
        """Handles reset button click."""
        try:
            # Reset in config manager
            self.editor.config_manager.reset_button(self.index)

            # Find and update dropdowns
            dropdowns = self.findChildren(QComboBox)
            if len(dropdowns) >= 2:
                task_type_dropdown = dropdowns[0]
                value_dropdown = dropdowns[1]

                # Update task type dropdown
                task_type_dropdown.blockSignals(True)
                task_type_dropdown.setCurrentText("Show Any Window")
                task_type_dropdown.blockSignals(False)

                # Update value dropdown
                value_dropdown.blockSignals(True)
                value_dropdown.clear()
                value_dropdown.setEnabled(False)
                value_dropdown.setCurrentText("")
                value_dropdown.blockSignals(False)

            # Update window title
            update_window_title(self.editor.config_manager, self.editor)

        except Exception as e:
            logging.error(f"Error resetting button {self.index}: {str(e)}")
            QMessageBox.critical(self.editor, "Error", f"Failed to reset button: {str(e)}")
