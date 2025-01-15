from threading import Lock
from typing import Dict, Tuple

class WindowManager:
    _instance = None
    _lock = Lock()

    def __init__(self):
        if WindowManager._instance is not None:
            raise RuntimeError("Use get_instance() to access the singleton instance.")
        self._window_hwnd_mapping: Dict[int, Tuple[str, str, int]] = {}

    @staticmethod
    def get_instance() -> "WindowManager":
        """Get the singleton instance of WindowManager."""
        if WindowManager._instance is None:
            with WindowManager._lock:
                if WindowManager._instance is None:
                    WindowManager._instance = WindowManager()
        return WindowManager._instance

    def update_window_hwnd_mapping(self, new_map: Dict[int, Tuple[str, str, int]]) -> None:
        """
        Atomically update the mapping with the new data.
        Replaces the current mapping to ensure consistency for readers.
        
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
        with self._lock:
            # Validate the input to ensure all values are tuples of the correct form
            for key, value in new_map.items():
                if not (isinstance(value, tuple) and len(value) == 3 and
                        isinstance(value[0], str) and isinstance(value[1], str) and isinstance(value[2], int)):
                    raise ValueError("Each value in the dictionary must be a tuple of (str, str, int).")

            # Atomically replace the entire dictionary
            self._window_hwnd_mapping = new_map.copy()

    def get_window_hwnd_mapping(self) -> Dict[int, Tuple[str, str, int]]:
        """
        Return a copy of the current mapping.
        Ensures readers always get a consistent and stable view of the data.

        This is the window info, where:
        - The key is the HWND (int).
        - The values are a tuple containing:
            1. Window title (str): The title of the window.
            2. Exe name (str): The human-friendly name of the executable.
            3. Instance number (int): A unique instance number for this window.

        Returns:
            A copy of the HWND mapping dictionary.
        """
        return self._window_hwnd_mapping.copy()