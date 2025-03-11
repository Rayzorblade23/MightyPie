# Define the icon file paths (use appropriate file paths)
import logging
from collections import defaultdict

from PyQt6.QtGui import QPixmap, QIcon, QImage

from src.data.icon_paths import EXTERNAL_ICON_PATHS

logger = logging.getLogger(__name__)

# Cache to hold icons
icon_cache = defaultdict(dict)


def get_icon(icon_name: str, is_inverted: bool = False):
    """
    Load the icon based on the inverted_icons flag, with caching.
    """
    # Check if the icon is already cached
    if is_inverted:
        if icon_name in icon_cache["inverted"]:
            logger.info(f"Returning cached inverted icon for {icon_name}")
            return icon_cache["inverted"][icon_name]
        else:
            icon_path = EXTERNAL_ICON_PATHS.get(icon_name)
            if icon_path:
                inverted_icon = invert_icon(icon_path)
                icon_cache["inverted"][icon_name] = inverted_icon
                return inverted_icon
    else:
        if icon_name in icon_cache["original"]:
            logger.info(f"Returning cached original icon for {icon_name}")
            return icon_cache["original"][icon_name]
        else:
            icon_path = EXTERNAL_ICON_PATHS.get(icon_name)
            if icon_path:
                original_icon = QIcon(icon_path)
                icon_cache["original"][icon_name] = original_icon
                return original_icon
    return None  # In case icon name doesn't match


def invert_icon(icon_path: str, return_pixmap: bool = False):
    """Invert the colors of the icon more efficiently, preserving the alpha channel."""
    logger.debug(f"inverting icon {icon_path}")

    # Load the icon as QPixmap
    pixmap = QPixmap(icon_path)

    # Convert QPixmap to QImage for manipulation
    image = pixmap.toImage()

    # Convert the image to a format that supports 32-bit color with alpha (RGBA)
    # Use:
    if image.format() != QImage.Format.Format_ARGB32:
        image = image.convertToFormat(QImage.Format.Format_ARGB32)

    # Access the pixel data directly using bits()
    width, height = image.width(), image.height()

    # Get a pointer to the pixel data
    ptr = image.bits()
    ptr.setsize(image.bytesPerLine() * image.height())
    data = memoryview(ptr).cast("B")

    # Iterate over the pixels and modify them
    for y in range(height):
        for x in range(width):
            # Calculate the position of the pixel in the raw data
            pixel_index = (y * width + x) * 4  # 4 bytes per pixel (RGBA)

            # Use:
            r = data[pixel_index]
            g = data[pixel_index + 1]
            b = data[pixel_index + 2]
            a = data[pixel_index + 3]

            if a == 0:  # Skip fully transparent pixels
                continue

            # Invert RGB values
            inverted_r = 255 - r
            inverted_g = 255 - g
            inverted_b = 255 - b

            # Use:
            data[pixel_index] = inverted_r
            data[pixel_index + 1] = inverted_g
            data[pixel_index + 2] = inverted_b
            data[pixel_index + 3] = a

    # Convert the modified QImage back to QPixmap
    inverted_pixmap = QPixmap.fromImage(image)
    if return_pixmap:
        return inverted_pixmap
    return QIcon(inverted_pixmap)
