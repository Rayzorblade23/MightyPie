# MightyPie - Your Customizable Pie Menu

MightyPie is a customizable pie menu application designed to enhance your workflow by providing quick access to applications, window management, and custom functions through intuitive radial menus.

## Features

*   **Multiple Pie Menus:** Organize your actions into multiple distinct pie menus, accessible via different hotkeys.
*   **Customizable Buttons:** Define actions for each button in your pie menu, including launching applications, focusing windows, and executing custom functions.
*   **Dynamic Window Management:**  Quickly switch between open windows, close them, or bring them to the foreground.
*   **Programmable Functions:** Execute custom Python functions with the click of a button.  Configure text, icons, and actions easily.
*   **Hotkeys:** Trigger pie menus using configurable hotkeys.
*   **Clean UI:** A visually appealing and unobtrusive interface.
*   **Configuration Persistence:** Settings are saved and loaded automatically, ensuring consistency across sessions.
*   **Multi-monitor Support:** Works seamlessly across multiple monitors.
*   **DPI Awareness:** Automatically detects DPI changes and restarts to ensure proper scaling.

## Installation

1.  **Prerequisites:**
    *   Python 3.7+
    *   Windows Operating System

2.  **Clone the repository:**

    ```bash
    git clone [your_repository_url]
    cd [your_repository_name]
    ```

3.  **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Run the application:**

    ```bash
    python main.py
    ```

## Configuration

MightyPie is configured via two primary files:

*   `data/config.py`: This Python file contains various settings, including hotkeys, colors, UI element sizes, and the number of pie menus.
*   `data/button_config.json`: This JSON file stores the configuration for each button in your pie menus, including the associated application, window, or function.

**Important Considerations:**

*   **Editing `config.py`:** Modify the values in this file to customize the application's behavior to your liking.
*   **Editing `button_config.json`:** Use the application's UI (currently in development, coming soon!) or directly edit this file to assign applications, windows, or functions to specific buttons.

**Configuration Notes:**

*   **Changing the Number of Pie Menus:** If you modify the number of pie menus (primary or secondary) in `data/config.py`, you **must** also update the `INTERNAL_NUM_PIE_MENUS_PRIMARY` and `INTERNAL_NUM_PIE_MENUS_SECONDARY` values in the `app_settings.json` file. After doing so, **delete the `data/button_config.json` file (or manually adjust the button indexes within the file).** This ensures that the button configurations are correctly re-initialized based on the new number of menus.
*   **Button Indexes:** Button indexes are assigned sequentially across all pie menus. Understanding this is crucial when manually editing `button_config.json`.  For example, if you have 2 primary pie menus with 8 buttons each, the buttons will be numbered 0-15.

## Usage

1.  **Run the application:** Execute `python main.py`. The application will run in the background (system tray).
2.  **Trigger the Pie Menu:** Press the configured hotkey (default is `Ctrl+Shift+A` for the primary menu).
3.  **Select an Action:** Use the mouse to select a button in the pie menu.
4.  **Customize:**  Modify `data/config.py` and `data/button_config.json` to personalize MightyPie to your workflow.

## Planned Features (Roadmap)

*   **GUI Configuration Tool:** A user-friendly graphical interface for configuring buttons, actions, and settings, eliminating the need to directly edit JSON files.
*   **Icon Picker:** An integrated tool for selecting icons for your buttons directly from files.
*   **More Button Action Types:** Expand the types of actions that can be assigned to buttons (e.g., system commands, clipboard management).
*   **Advanced Window Filtering:** More granular control over how windows are filtered and displayed in the pie menu.

## Contributing

Contributions are welcome!  Please fork the repository and submit a pull request with your changes.  For major changes, please open an issue first to discuss your proposed changes.

**Third-Party Licenses:**

MightyPie incorporates the Tabler Icons library. These icons are licensed under the MIT License, and the license text can be found in the [`licenses/TABLER_LICENSE`](licenses/Tabler_MIT_License.txt) file.