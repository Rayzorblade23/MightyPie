# Define the icon file paths (use appropriate file paths)
import os

from PyQt6.QtGui import QIcon, QPixmap, QColor

from functions.file_handling_functions import get_resource_path

EXTERNAL_ICON_PATHS = {
    "windows_key": get_resource_path(os.path.join("external_icons", "brand-windows.png")),
    "audio": get_resource_path(os.path.join("external_icons", "volume.png")),
    "network": get_resource_path(os.path.join("external_icons", "network.png")),
    "action_center": get_resource_path(os.path.join("external_icons", "layout-sidebar-right-inactive.png")),
    "projection": get_resource_path(os.path.join("external_icons", "device-desktop.png")),
    "touch_keyboard": get_resource_path(os.path.join("external_icons", "keyboard.png")),
    "folder": get_resource_path(os.path.join("external_icons", "folder.png")),
    "folders": get_resource_path(os.path.join("external_icons", "folders.png")),
    "folder-up": get_resource_path(os.path.join("external_icons", "folder-up.png")),
    "folder-settings": get_resource_path(os.path.join("external_icons", "folder-settings.png")),
    "folder-star": get_resource_path(os.path.join("external_icons", "folder-star.png")),
    "folder-exclamation": get_resource_path(os.path.join("external_icons", "folder-exclamation.png")),
    "taskman": get_resource_path(os.path.join("external_icons", "subtask.png")),
    "browser_maximize": get_resource_path(os.path.join("external_icons", "browser-maximize.png")),
    "square_x": get_resource_path(os.path.join("external_icons", "square-x.png")),
    "window_maximize": get_resource_path(os.path.join("external_icons", "window-maximize.png")),
    "window_minimize": get_resource_path(os.path.join("external_icons", "window-minimize.png")),
    "quit": get_resource_path(os.path.join("external_icons", "playstation-x.png")),
    "restart": get_resource_path(os.path.join("external_icons", "restore.png")),
    "shredder": get_resource_path(os.path.join("external_icons", "file-shredder.png")),
    "settings": get_resource_path(os.path.join("external_icons", "settings.png")),
    "adjustments": get_resource_path(os.path.join("external_icons", "adjustments.png")),
    "circles": get_resource_path(os.path.join("external_icons", "circles.png")),
    "dots-circle": get_resource_path(os.path.join("external_icons", "dots-circle.png")),
    "palette": get_resource_path(os.path.join("external_icons", "palette.png")),
    "arrow-right": get_resource_path(os.path.join("external_icons", "arrow-right.png")),
    "change": get_resource_path(os.path.join("external_icons", "change.png")),
    "cake": get_resource_path(os.path.join("external_icons", "cake.png")),
    "schedule-time": get_resource_path(os.path.join("external_icons", "schedule-time.png")),
}

# Load the icon based on the inverted_icons flag
def get_icon(icon_name: str, is_inverted: bool = False):
    icon_path = EXTERNAL_ICON_PATHS.get(icon_name)

    if icon_path:
        if is_inverted:
            return invert_icon(icon_path)  # Return inverted icon
        else:
            return QIcon(icon_path)  # Return original icon
    return None  # In case icon name doesn't match


def invert_icon(icon_path, return_pixmap=False):
    """Invert the colors of the icon, preserving the alpha channel."""
    # Load the icon as QPixmap
    pixmap = QPixmap(icon_path)

    # Convert QPixmap to QImage for manipulation
    image = pixmap.toImage()

    # Loop through each pixel and invert its color (keep alpha intact)
    for x in range(image.width()):
        for y in range(image.height()):
            color = image.pixelColor(x, y)

            # Skip pixels with full transparency (alpha = 0)
            if color.alpha() == 0:
                continue

            # Invert RGB, but keep the alpha channel intact
            inverted_color = QColor(255 - color.red(), 255 - color.green(), 255 - color.blue(), color.alpha())
            image.setPixelColor(x, y, inverted_color)

    # Convert the QImage back to QPixmap
    inverted_pixmap = QPixmap.fromImage(image)

    # Return QPixmap or QIcon based on the flag
    if return_pixmap:
        return inverted_pixmap
    return QIcon(inverted_pixmap)



