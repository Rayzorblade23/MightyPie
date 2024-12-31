from typing import Dict, Tuple

class WindowManager:
    _instance = None

    def __init__(self):
        self.window_hwnd_mapping: Dict[int, Tuple[str, str, int]] = {}

    @staticmethod
    def get_instance() -> "WindowManager":
        """Get the singleton instance of WindowManager."""
        if WindowManager._instance is None:
            WindowManager._instance = WindowManager()
        return WindowManager._instance

    def update_window_hwnd_mapping(self, new_map: Dict[int, Tuple[str, str, int]]) -> None:
        """
        Update the global map with a new mapping of HWND to window info.

        This is the window info, where:
        - The key is the HWND (int).
        - The values are a tuple containing:
            1. Window title (str): The title of the window.
            2. Exe name (str): The human-friendly name of the executable.
            3. Instance number (int): A unique instance number for this window.

        Args:
            new_map: A dictionary mapping HWNDs to their corresponding window info.

        Raises:
            ValueError: If any value in the new_map is not a tuple of (str, str, int).
        """
        # Remove keys that are not in new_map
        keys_to_remove = [key for key in self.window_hwnd_mapping if key not in new_map]
        for key in keys_to_remove:
            del self.window_hwnd_mapping[key]

        # Update or add new keys from new_map
        for key, value in new_map.items():
            if isinstance(value, tuple) and len(value) == 3:
                self.window_hwnd_mapping[key] = value
            else:
                raise ValueError("Each entry must be a tuple of (str, str, int)")

    def get_window_hwnd_mapping(self) -> Dict[int, Tuple[str, str, int]]:
        """Return the current map of HWND to window info."""
        return self.window_hwnd_mapping
