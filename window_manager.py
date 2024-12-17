class WindowManager:
    _instance = None
    window_titles_to_hwnds_map = {}

    @staticmethod
    def get_instance():
        if WindowManager._instance is None:
            WindowManager._instance = WindowManager()
        return WindowManager._instance

    def update_window_titles_to_hwnds_map(self, new_map):
        """Update the global map with a new window titles to hwnds mapping."""

        # Remove keys that are not in new_map
        keys_to_remove = [key for key in self.window_titles_to_hwnds_map if key not in new_map]
        for key in keys_to_remove:
            del self.window_titles_to_hwnds_map[key]

        # Update or add new keys from new_map
        self.window_titles_to_hwnds_map.update(new_map)

    def get_window_titles_to_hwnds_map(self):
        """Return the current map."""
        return self.window_titles_to_hwnds_map
