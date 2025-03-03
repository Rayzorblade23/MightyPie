# Define the icon file paths (use appropriate file paths)

from collections import defaultdict

from PyQt6.QtGui import QPixmap, QIcon

from src.data.icon_paths import EXTERNAL_ICON_PATHS

# Cache to hold icons
icon_cache = defaultdict(dict)


def get_icon(icon_name: str, is_inverted: bool = False):
    """
    Load the icon based on the inverted_icons flag, with caching.
    """
    # Check if the icon is already cached
    if is_inverted:
        if icon_name in icon_cache["inverted"]:
            print(f"Returning cached inverted icon for {icon_name}")
            return icon_cache["inverted"][icon_name]
        else:
            icon_path = EXTERNAL_ICON_PATHS.get(icon_name)
            if icon_path:
                inverted_icon = invert_icon(icon_path)
                icon_cache["inverted"][icon_name] = inverted_icon
                return inverted_icon
    else:
        if icon_name in icon_cache["original"]:
            print(f"Returning cached original icon for {icon_name}")
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
    print(f"inverting icon {icon_path}")
    # Load the icon as QPixmap
    pixmap = QPixmap(icon_path)

    # Convert QPixmap to QImage for manipulation
    image = pixmap.toImage()

    # Access the raw pixel data using QImage.bits()
    image_bits = image.bits()
    image_bits.setsize(image.sizeInBytes())

    # Create a memoryview of the image bits cast as unsigned bytes.
    data = memoryview(image_bits).cast("B")

    width, height = image.width(), image.height()
    for y in range(height):
        for x in range(width):
            # Calculate the index of the pixel in the data array (each pixel is 4 bytes: RGBA)
            pixel_index = (y * width + x) * 4

            # Get the RGBA values (as integers)
            r = data[pixel_index]
            g = data[pixel_index + 1]
            b = data[pixel_index + 2]
            a = data[pixel_index + 3]

            # Skip fully transparent pixels
            if a == 0:
                continue

            # Invert the RGB values
            data[pixel_index] = 255 - r
            data[pixel_index + 1] = 255 - g
            data[pixel_index + 2] = 255 - b
            # Alpha remains unchanged

    # Convert the modified QImage back to QPixmap
    inverted_pixmap = QPixmap.fromImage(image)
    if return_pixmap:
        return inverted_pixmap
    return QIcon(inverted_pixmap)
