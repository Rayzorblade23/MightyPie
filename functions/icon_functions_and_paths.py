# Define the icon file paths (use appropriate file paths)

from PyQt6.QtGui import QIcon, QPixmap, QColor

from data.icon_paths import EXTERNAL_ICON_PATHS


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



