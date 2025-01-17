from config import CONFIG


class ButtonInfo:
    def __init__(self):
        # Initialize the task dictionary
        self.tasks_dict = {}

        # Fill the dictionary with initial tasks, including default tasks
        self._initialize_tasks()

    def _initialize_tasks(self):
        # Pre-defined tasks (example data)
        self.tasks_dict = {
            0: {
                "task_type": "program_window_fixed",
                "properties": {
                    "app_name": "Vivaldi",
                    "text_1": "",
                    "text_2": "",
                    "window_handle": -1,
                    "app_icon_path": "",
                    "exe_name": "vivaldi.exe"
                }
            },
            4: {
                "task_type": "program_window_fixed",
                "properties": {
                    "app_name": "Spotify",
                    "text_1": "",
                    "text_2": "",
                    "window_handle": -1,
                    "app_icon_path": "",
                    "exe_name": "spotify.exe"
                }
            },
            6: {
                "task_type": "program_window_fixed",
                "properties": {
                    "app_name": "Telegram Desktop",
                    "text_1": "",
                    "text_2": "Telegram Desktop",
                    "window_handle": -1,
                    "app_icon_path": "",
                    "exe_name": "telegram.exe"
                }
            }
        }

        # Fill in missing tasks where there are gaps in the indices
        for i in range(CONFIG.MAX_BUTTONS * 2):
            if i not in self.tasks_dict:  # If there's no task at this index
                self.tasks_dict[i] = {
                    "task_type": "program_window_any",  # Only assign "program_window_any" for missing slots
                    "properties": {
                        "app_name": "",
                        "text_1": "",
                        "text_2": "",
                        "window_handle": -1,
                        "app_icon_path": "",
                        "exe_name": ""
                    }
                }

    def __getitem__(self, index):
        """Allow direct access to tasks via index like task[index]."""
        return self.tasks_dict.get(index, None)

    def get_task_indexes(self):
        """
        Returns a list of all task indexes.
        """
        return list(self.tasks_dict.keys())

    def filter_buttons(self, attribute, value):
        """
        Filters tasks based on a given attribute and value.

        :param attribute: Attribute to check (can be nested, e.g., 'properties.text_2')
        :param value: The value to match
        :return: A list of tasks matching the criteria
        """
        filtered = []
        for task_id, task in self.tasks_dict.items():

            # Handle nested attributes using split('.')
            keys = attribute.split('.')
            temp = task
            try:
                # Navigate through the nested attribute chain
                for key in keys:
                    temp = temp[key]
                if temp == value:
                    filtered.append(task)
            except KeyError:
                continue  # If attribute doesn't exist, skip this task
        return filtered

    def get_all_tasks(self):
        """Returns all tasks."""
        return self.tasks_dict
