from copy import deepcopy
from threading import Lock
from typing import Dict, Tuple, Set, Any

from src.data.config import CONFIG


class WindowManager:
    _instance = None
    _lock = Lock()

    def __init__(self):
        if WindowManager._instance is not None:
            raise RuntimeError("Use get_instance() to access the singleton instance.")
        self._window_hwnd_mapping: Dict[int, Tuple[str, str, int]] = {}
        self.last_window_handles = []
        self.windowHandles_To_buttonIndexes_map = {}
        self._app_info_cache: Dict[str, Dict[str, str]] = {}
        self.windows_info: Dict[int, Tuple[str, str, int]] = {}

    @staticmethod
    def get_instance() -> "WindowManager":
        if WindowManager._instance is None:
            with WindowManager._lock:
                if WindowManager._instance is None:
                    WindowManager._instance = WindowManager()
        return WindowManager._instance

    def set_app_info_cache(self, cache: Dict[str, Dict[str, str]]) -> None:
        """Updates the application info cache."""
        with self._lock:
            self._app_info_cache = deepcopy(cache)

    def update_open_windows_info(self, new_map: Dict[int, Tuple[str, str, int]]) -> None:
        """
        Atomically update the mapping with the new data.
        Replaces the current mapping to ensure consistency for readers.
        
        This is the window info, where:
        - The key is the HWND (int).
        - The values are a tuple containing:
            1. Window title (str): The title of the window.
            2. Exe Name (str): The human-friendly name of the executable.
            3. Instance number (int): A unique instance number for this window.

        Args:
            new_map: A dictionary mapping HWNDs to their corresponding window info.

        Raises:
            ValueError: If any value in the new_map is not a tuple of (str, str, int).
        """
        with self._lock:
            # Validate the input to ensure all values are tuples of the correct form
            for key, value in new_map.items():
                if not (isinstance(value, tuple) and len(value) == 3 and
                        isinstance(value[0], str) and isinstance(value[1], str) and isinstance(value[2], int)):
                    raise ValueError("Each value in the dictionary must be a tuple of (str, str, int).")

            # Atomically replace the entire dictionary
            self._window_hwnd_mapping = new_map.copy()

    def get_open_windows_info(self) -> Dict[int, Tuple[str, str, int]]:
        """
        Return a copy of the current mapping.
        Ensures readers always get a consistent and stable view of the data.

        This is the window info, where:
        - The key is the HWND (int).
        - The values are a tuple containing:
            1. Window title (str): The title of the window.
            2. Exe Name (str): The human-friendly name of the executable.
            3. Instance number (int): A unique instance number for this window.

        Returns:
            A copy of the HWND mapping dictionary.
        """
        return self._window_hwnd_mapping.copy()

    def update_button_window_assignment(self, pie_window, button_info, reassign_all_buttons: bool = True) -> None:
        """Updates button info with current window information."""

        # Create working copy of button configurations
        updated_button_config: Dict[int, Dict[str, Any]] = deepcopy(button_info.get_all_tasks())

        # Get current windows info
        self.windows_info = self.get_open_windows_info()

        # Track processed buttons
        processed_buttons: Set[int] = set()

        # Get filtered button sets by type
        show_program_window_buttons = button_info.filter_buttons("task_type", "show_program_window")
        show_any_window_buttons = button_info.filter_buttons("task_type", "show_any_window")
        launch_program_buttons = button_info.filter_buttons("task_type", "launch_program")

        # Process Launch Program Buttons
        self._update_launch_program_windows(launch_program_buttons)

        # Process Show (specific) Program Buttons
        self._update_existing_handles(show_program_window_buttons, processed_buttons, reassign_all_buttons,True)
        self._assign_free_windows_for_show_program_window_buttons(show_program_window_buttons, processed_buttons)

        # Process Show Any Window Buttons
        self._update_existing_handles(show_any_window_buttons, processed_buttons, reassign_all_buttons)
        self._assign_free_windows_for_show_any_window_buttons(show_any_window_buttons, processed_buttons)

        # Update final configuration
        updated_button_config.update(show_any_window_buttons)
        updated_button_config.update(show_program_window_buttons)
        updated_button_config.update(launch_program_buttons)

        self._emit_button_updates(updated_button_config, pie_window)

    def _update_launch_program_windows(self, buttons: Dict[int, Dict[str, Any]]) -> None:
        for _, button in buttons.items():
            exe_name = button['properties']['exe_name']
            self._update_button_with_window_info(button, "", exe_name, 0, True)

    def _update_existing_handles(
            self,
            buttons: Dict[int, Dict[str, Any]],
            processed_buttons: Set[int] = None,
            reassign_all: bool = False,
            is_show_program_button: bool = False

    ) -> None:
        """Checks buttons with existing window handles and clears invalid ones."""
        for button_id, button in buttons.items():
            hwnd: int = button['properties']['window_handle']
            if (hwnd in self.windows_info and
                    # if reassign_all, only do it for certain IDs
                    not (reassign_all and button_id > CONFIG.REASSIGN_BTN_IDS_HIGHER_THAN)):
                title, exe_name, instance = self.windows_info[hwnd]
                self.windows_info.pop(hwnd)
                self._update_button_with_window_info(button, title, exe_name, instance, True)
                processed_buttons.add(button_id)
            else:
                if not is_show_program_button:
                    self._clear_button_properties(button)

    def _assign_free_windows_for_show_program_window_buttons(
            self,
            buttons: Dict[int, Dict[str, Any]],
            processed_buttons: Set[int]
    ) -> None:
        """Maps program-specific windows to their designated buttons."""
        for button_id, button in buttons.items():
            if button_id in processed_buttons:
                continue

            exe_name = button['properties']['exe_name']
            if exe_name not in self._app_info_cache:
                button['properties'].update({
                    'window_handle': -1,
                    'app_name': exe_name.rstrip(".exe").capitalize()
                })
                continue

            matching_window = None
            for hwnd, (window_title, exe_name_from_window, instance_id) in self.windows_info.items():
                if exe_name_from_window == exe_name:
                    self.windows_info.pop(hwnd)
                    matching_window = (hwnd, window_title, exe_name_from_window, instance_id)
                    processed_buttons.add(button_id)
                    break

            if matching_window:
                hwnd, title, _, instance = matching_window
                button['properties']['window_handle'] = hwnd
                self._update_button_with_window_info(
                    button, title, exe_name, instance, True)
            else:
                button['properties']['window_handle'] = 0
                self._update_button_with_window_info(
                    button, "", exe_name, 0, True)

    def _assign_free_windows_for_show_any_window_buttons(
            self,
            buttons: Dict[int, Dict[str, Any]],
            processed_buttons: Set[int]
    ) -> None:
        """Assigns remaining windows to buttons that have no window handle."""
        for button_id, button in buttons.items():
            if button_id in processed_buttons:
                continue

            if button['properties']['window_handle'] == -1 and self.windows_info:
                hwnd, (title, exe_name, instance) = self.windows_info.popitem()
                button['properties']['window_handle'] = hwnd
                self._update_button_with_window_info(button, title, exe_name, instance)
                processed_buttons.add(button_id)

    def _update_button_with_window_info(self,
                                        button: Dict[str, Any],
                                        title: str,
                                        exe_name: str,
                                        instance: int,
                                        include_exe_path: bool = False
                                        ) -> None:
        """Updates button properties with window information and app cache data."""
        button['properties'].update({
            'window_title': f"{title} ({instance})" if instance != 0 else title,
            'app_name': self._app_info_cache.get(exe_name, {}).get('app_name', ''),
            'app_icon_path': self._app_info_cache.get(exe_name, {}).get('icon_path', ''),
            **({'exe_path': self._app_info_cache.get(exe_name, {}).get('exe_path', '')} if include_exe_path else {})
        })

    @staticmethod
    def _clear_button_properties(button: Dict[str, Any]) -> None:
        """Clears all properties of a button."""
        button['properties'].update({
            'window_handle': -1,
            'window_title': '',
            'app_name': '',
            'app_icon_path': '',
        })

    @staticmethod
    def _emit_button_updates(updated_config: Dict[int, Dict[str, Any]], pie_window) -> None:
        if pie_window:
            for pie_menu in pie_window.pie_menus_primary + pie_window.pie_menus_secondary:
                pie_menu.update_buttons_signal.emit(updated_config)
