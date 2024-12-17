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
        self.window_titles_to_hwnds_map.update(new_map)

    def get_window_titles_to_hwnds_map(self):
        """Return the current map."""
        return self.window_titles_to_hwnds_map
