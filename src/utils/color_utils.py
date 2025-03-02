import colorsys


def adjust_saturation(hex_color, saturation_factor=0.8):
    """Adjust the saturation of a hex color."""
    # Convert hex to RGB
    r, g, b = int(hex_color[1:3], 16), int(hex_color[3:5], 16), int(hex_color[5:7], 16)

    # Normalize RGB to [0, 1]
    r, g, b = r / 255.0, g / 255.0, b / 255.0

    # Convert RGB to HSL
    h, l, s = colorsys.rgb_to_hls(r, g, b)

    # Adjust saturation
    s = max(0.0, min(1.0, s * saturation_factor))  # Ensure saturation stays within [0, 1]

    # Convert HSL back to RGB
    r, g, b = colorsys.hls_to_rgb(h, l, s)

    # Convert RGB back to hex
    return f'#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}'