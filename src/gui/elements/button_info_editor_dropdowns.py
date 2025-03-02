# gui/menus/button_info_dropdowns.py
from typing import Dict, List, Tuple, TYPE_CHECKING

from PyQt6.QtWidgets import QComboBox

from src.data.button_functions import ButtonFunctions
from src.data.config import CONFIG
from src.gui.buttons.pie_button import BUTTON_TYPES
from src.utils.json_utils import JSONManager

if TYPE_CHECKING:
    from src.gui.menus.button_info_editor import ButtonInfoEditor


class ButtonDropdowns:
    def __init__(self, editor: 'ButtonInfoEditor'):
        self.editor = editor
        self.task_types = list(BUTTON_TYPES.keys())
        self.apps_info = self._load_apps_info()
        self.exe_names = self._get_sorted_exe_names()

    @staticmethod
    def _load_apps_info() -> Dict:
        """Load applications info from cache."""
        return JSONManager.load(CONFIG.INTERNAL_PROGRAM_NAME, "apps_info_cache.json", default={})

    def _get_sorted_exe_names(self) -> List[Tuple[str, str]]:
        """Get sorted list of executable names and their display names."""
        return sorted([
            (exe_name, app_info["app_name"])
            for exe_name, app_info in self.apps_info.items()
        ])

    def update_apps_info(self) -> None:
        """Update the cached applications info."""
        self.apps_info = self._load_apps_info()
        self.exe_names = self._get_sorted_exe_names()

    def create_dropdowns(self, current_button_info: Dict, index: int) -> Tuple[QComboBox, QComboBox]:
        """Create task type and value dropdowns for a button."""
        task_type_dropdown = self._create_task_type_dropdown(current_button_info, index)
        value_dropdown = self._create_value_dropdown(current_button_info, index)
        return task_type_dropdown, value_dropdown

    def _create_task_type_dropdown(self, current_button_info: Dict, index: int) -> QComboBox:
        """Create the task type dropdown."""
        dropdown = QComboBox()
        for task_type in self.task_types:
            display_text = task_type.replace('_', ' ').title()
            dropdown.addItem(display_text, task_type)

        current_index = self.task_types.index(current_button_info["task_type"])
        dropdown.setCurrentIndex(current_index)
        dropdown.setProperty("button_index", index)
        dropdown.currentTextChanged.connect(
            lambda text: self.editor.on_task_type_changed(
                self.task_types[dropdown.currentIndex()]
            )
        )
        return dropdown

    def _create_value_dropdown(self, current_button_info: Dict, index: int) -> QComboBox:
        """Create the value dropdown (exe name or function)."""
        dropdown = QComboBox()
        dropdown.setProperty("button_index", index)
        task_type = current_button_info["task_type"]

        if task_type == "show_any_window":
            self._setup_any_window_dropdown(dropdown)
        elif task_type == "call_function":
            self._setup_function_dropdown(dropdown, current_button_info)
        else:
            self._setup_program_dropdown(dropdown, current_button_info)

        dropdown.currentIndexChanged.connect(
            lambda idx: self.editor.on_value_index_changed(idx, index, dropdown)
        )
        dropdown.editTextChanged.connect(
            lambda text: self.editor.on_value_changed(text, index)
        )

        return dropdown

    @staticmethod
    def _setup_any_window_dropdown(dropdown: QComboBox) -> None:
        """Setup dropdown for 'show_any_window' type."""
        dropdown.setEnabled(False)
        dropdown.setEditable(True)
        dropdown.clear()
        dropdown.setCurrentText("")

    @staticmethod
    def _setup_function_dropdown(dropdown: QComboBox, current_button_info: Dict) -> None:
        """Setup dropdown for 'call_function' type."""
        functions = ButtonFunctions().functions
        dropdown.setEditable(False)
        dropdown.setEnabled(True)

        for func_name, func_data in functions.items():
            dropdown.addItem(func_data['text_1'], func_name)

        current_function = current_button_info["properties"].get("function_name", "")
        if current_function:
            for i in range(dropdown.count()):
                if dropdown.itemData(i) == current_function:
                    dropdown.setCurrentIndex(i)
                    break

    def _setup_program_dropdown(self, dropdown: QComboBox, current_button_info: Dict) -> None:
        """Setup dropdown for program-related types."""
        dropdown.setEditable(True)
        dropdown.setEnabled(True)

        for exe_name, app_name in self.exe_names:
            display_text = f"({exe_name})" if not app_name.strip() else f"{app_name}"
            dropdown.addItem(display_text, exe_name)

        current_exe = current_button_info["properties"].get("exe_name", "")
        if current_exe:
            for i in range(dropdown.count()):
                if dropdown.itemData(i) == current_exe:
                    dropdown.setCurrentIndex(i)
                    break
