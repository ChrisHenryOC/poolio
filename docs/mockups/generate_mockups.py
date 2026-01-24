#!/usr/bin/env python3
"""
Display Node UI Mockup Generator

Generates PNG mockups for the Poolio Display Node at 240x320 resolution.
Based on specifications in docs/display-node-ui-design.md
"""

from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import math

# Display dimensions
WIDTH = 240
HEIGHT = 320

# Color palette (from design doc)
COLORS = {
    "background": (0, 0, 0),           # Black
    "text_primary": (255, 255, 255),   # White
    "text_secondary": (255, 248, 220), # Cornsilk
    "accent": (127, 255, 212),         # Aqua
    "value": (255, 255, 0),            # Yellow
    "alert": (255, 48, 48),            # Firebrick
    "success": (0, 255, 0),            # Green
    "status_active": (0, 0, 255),      # Blue
    "warning": (255, 170, 0),          # Orange
    "button_bg": (50, 50, 50),         # Dark gray for buttons
    "button_disabled": (80, 80, 80),   # Lighter gray
    "dialog_bg": (30, 30, 30),         # Dialog background
    "stale_bg": (60, 40, 0),           # Dark orange/amber background for stale
}


def get_font(size):
    """Get a font at the specified size. Uses default if TrueType not available."""
    try:
        return ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", size)
    except (OSError, IOError):
        try:
            return ImageFont.truetype("/System/Library/Fonts/SFNSText.ttf", size)
        except (OSError, IOError):
            return ImageFont.load_default()


def create_base_image(nonprod=False):
    """Create a base image with black background and optional nonprod border."""
    img = Image.new("RGB", (WIDTH, HEIGHT), COLORS["background"])
    if nonprod:
        draw = ImageDraw.Draw(img)
        # 1px orange border around entire screen
        draw.rectangle([0, 0, WIDTH-1, HEIGHT-1], outline=COLORS["warning"], width=1)
    return img


def draw_text_right_aligned(draw, text, x_right, y, font, fill):
    """Draw text right-aligned to the given x coordinate."""
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    draw.text((x_right - text_width, y), text, font=font, fill=fill)


def draw_header(draw, date_str, time_str, ampm, fill_status=None):
    """Draw the header zone with date, time, and optional fill status."""
    # Date (centered, aqua) - font10
    font_date = get_font(10)
    date_bbox = draw.textbbox((0, 0), date_str, font=font_date)
    date_width = date_bbox[2] - date_bbox[0]
    date_x = (WIDTH - date_width) // 2
    draw.text((date_x, 8), date_str, font=font_date, fill=COLORS["accent"])

    # Time (centered, cornsilk) - font22, also serves as settings tap zone
    font_time = get_font(22)
    time_bbox = draw.textbbox((0, 0), time_str, font=font_time)
    time_width = time_bbox[2] - time_bbox[0]
    time_x = (WIDTH - time_width) // 2 - 15
    draw.text((time_x, 25), time_str, font=font_time, fill=COLORS["text_secondary"])

    # AM/PM (after time) - font10
    font_ampm = get_font(10)
    ampm_x = time_x + time_width + 3
    draw.text((ampm_x, 38), ampm, font=font_ampm, fill=COLORS["text_secondary"])

    # Fill status (if active) - font10
    if fill_status:
        font_status = get_font(10)
        draw.text((5, 45), fill_status, font=font_status, fill=COLORS["status_active"])


def draw_settings_icon(draw, x, y):
    """Draw a simple settings gear icon."""
    center_x, center_y = x + 12, y + 12
    draw.ellipse([center_x-10, center_y-10, center_x+10, center_y+10],
                 outline=COLORS["text_secondary"], width=2)
    draw.ellipse([center_x-4, center_y-4, center_x+4, center_y+4],
                 fill=COLORS["text_secondary"])
    for angle in range(0, 360, 45):
        rad = math.radians(angle)
        x1 = center_x + int(8 * math.cos(rad))
        y1 = center_y + int(8 * math.sin(rad))
        x2 = center_x + int(12 * math.cos(rad))
        y2 = center_y + int(12 * math.sin(rad))
        draw.line([(x1, y1), (x2, y2)], fill=COLORS["text_secondary"], width=2)


def draw_warning_icon(draw, x, y, size=12):
    """Draw a warning triangle icon for stale data indication."""
    # Triangle points
    top = (x + size // 2, y)
    bottom_left = (x, y + size)
    bottom_right = (x + size, y + size)

    draw.polygon([top, bottom_left, bottom_right], fill=COLORS["warning"])
    # Exclamation mark
    cx = x + size // 2
    draw.line([(cx, y + 3), (cx, y + size - 5)], fill=(0, 0, 0), width=2)
    draw.ellipse([cx - 1, y + size - 3, cx + 1, y + size - 1], fill=(0, 0, 0))


def draw_stale_row_background(draw, y, height):
    """Draw a subtle amber/orange background to indicate stale data."""
    draw.rectangle([0, y, WIDTH, y + height], fill=COLORS["stale_bg"])


def draw_sparkline(draw, values, x, y, width, height, color):
    """Draw a simple sparkline chart."""
    if not values or len(values) < 2:
        return None, None

    min_val = min(values)
    max_val = max(values)
    value_range = max_val - min_val if max_val != min_val else 1

    points = []
    for i, val in enumerate(values):
        px = x + int(i * width / (len(values) - 1))
        py = y + height - int((val - min_val) * height / value_range)
        points.append((px, py))

    for i in range(len(points) - 1):
        draw.line([points[i], points[i + 1]], fill=color, width=2)

    return min_val, max_val


def draw_whisker_chart(draw, data, x, y, width, height, color):
    """
    Draw a whisker/candlestick chart showing min/max bars for each period.

    data: list of tuples (min_val, max_val) for each period
    """
    if not data:
        return None, None

    # Find global min/max for scaling
    all_mins = [d[0] for d in data]
    all_maxs = [d[1] for d in data]
    global_min = min(all_mins)
    global_max = max(all_maxs)
    value_range = global_max - global_min if global_max != global_min else 1

    num_bars = len(data)
    bar_spacing = width / num_bars
    bar_width = max(4, int(bar_spacing * 0.6))

    for i, (min_val, max_val) in enumerate(data):
        # Calculate x position (centered in slot)
        bar_x = x + int(i * bar_spacing + (bar_spacing - bar_width) / 2)

        # Calculate y positions (inverted - 0 is top)
        min_y = y + height - int((min_val - global_min) * height / value_range)
        max_y = y + height - int((max_val - global_min) * height / value_range)

        # Draw vertical line (whisker) from min to max
        center_x = bar_x + bar_width // 2
        draw.line([(center_x, min_y), (center_x, max_y)], fill=color, width=2)

        # Draw horizontal caps at min and max
        cap_width = bar_width // 2
        draw.line([(center_x - cap_width, max_y), (center_x + cap_width, max_y)], fill=color, width=2)
        draw.line([(center_x - cap_width, min_y), (center_x + cap_width, min_y)], fill=color, width=2)

        # Draw a small marker at the average
        avg_val = (min_val + max_val) / 2
        avg_y = y + height - int((avg_val - global_min) * height / value_range)
        draw.rectangle([center_x - 2, avg_y - 2, center_x + 2, avg_y + 2], fill=color)

    return global_min, global_max


def draw_button(draw, x, y, width, height, text, pressed=False, disabled=False):
    """Draw a button with text."""
    if disabled:
        bg_color = COLORS["button_disabled"]
        text_color = (128, 128, 128)
    elif pressed:
        bg_color = COLORS["text_primary"]
        text_color = (0, 0, 0)
    else:
        bg_color = COLORS["accent"]
        text_color = (0, 0, 0)

    draw.rectangle([x, y, x + width, y + height], fill=bg_color, outline=bg_color)

    font = get_font(10)
    lines = text.split('\n')
    total_height = len(lines) * 12
    start_y = y + (height - total_height) // 2

    for i, line in enumerate(lines):
        text_bbox = draw.textbbox((0, 0), line, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_x = x + (width - text_width) // 2
        draw.text((text_x, start_y + i * 12), line, font=font, fill=text_color)


def draw_back_button(draw):
    """Draw a back button in the top-left corner."""
    draw.text((5, 8), "←", font=get_font(16), fill=COLORS["text_secondary"])


def generate_main_dashboard(nonprod=False, pool_stale=False, valve_stale=False):
    """Generate the main dashboard mockup."""
    img = create_base_image(nonprod=nonprod)
    draw = ImageDraw.Draw(img)

    # Header
    draw_header(draw, "Thu Jan 22, 2026", "6:45", "PM", fill_status="FILLING")

    # Horizontal separator
    draw.line([(0, 70), (WIDTH, 70)], fill=COLORS["button_bg"], width=1)

    # Font sizes matching original implementation
    font_label = get_font(20)  # font20 for "Outside:", "Pool:", "Inside:"
    font_value = get_font(20)  # font20 for temperature values
    font_small = get_font(8)   # font8 for Next Fill, Needs Water, voltage, chart labels

    right_margin = 235  # Right alignment point

    # Outside temperature section (valve node)
    y_outside = 85
    if valve_stale:
        draw_stale_row_background(draw, y_outside - 5, 40)
        draw_warning_icon(draw, 5, y_outside + 5, size=10)
        draw.text((20, y_outside), "Outside:", font=font_label, fill=COLORS["accent"])
    else:
        draw.text((5, y_outside), "Outside:", font=font_label, fill=COLORS["accent"])
    draw.text((120, y_outside), "58°", font=font_value, fill=COLORS["value"])

    # Next fill info (right-aligned) - font8
    draw_text_right_aligned(draw, "Next Fill:", right_margin, y_outside - 5, font_small, COLORS["text_secondary"])
    draw_text_right_aligned(draw, "9:00 AM", right_margin, y_outside + 8, font_small, COLORS["text_secondary"])

    # Pool temperature section
    y_pool = 130
    if pool_stale:
        draw_stale_row_background(draw, y_pool - 5, 45)
        draw_warning_icon(draw, 5, y_pool + 5, size=10)
        draw.text((20, y_pool), "Pool:", font=font_label, fill=COLORS["accent"])
    else:
        draw.text((5, y_pool), "Pool:", font=font_label, fill=COLORS["accent"])
    draw.text((120, y_pool), "55°", font=font_value, fill=COLORS["value"])

    # Right-aligned: Needs Water and voltage - font8
    draw_text_right_aligned(draw, "Needs Water", right_margin, y_pool, font_small, COLORS["text_secondary"])
    draw_text_right_aligned(draw, "3.89 V", right_margin, y_pool + 15, font_small, COLORS["text_secondary"])

    # Inside temperature section
    y_inside = 175
    draw.text((5, y_inside), "Inside:", font=font_label, fill=COLORS["accent"])
    draw.text((120, y_inside), "69°", font=font_value, fill=COLORS["value"])
    # Humidity is part of temps label in original (font20), displayed inline
    draw.text((175, y_inside), "54%", font=font_value, fill=COLORS["value"])

    # Separator before chart
    draw.line([(0, 205), (WIDTH, 205)], fill=COLORS["button_bg"], width=1)

    # Sparkline chart
    sample_data = [54 + 3 * math.sin(i * 0.3) + (i * 0.02) for i in range(50)]
    min_val, max_val = draw_sparkline(draw, sample_data, 10, 215, 200, 85, COLORS["accent"])

    # Chart labels
    if min_val and max_val:
        draw.text((215, 215), f"{int(max_val)}", font=font_small, fill=COLORS["text_secondary"])
        draw.text((215, 290), f"{int(min_val)}", font=font_small, fill=COLORS["text_secondary"])

    return img


def generate_pool_detail():
    """Generate the Pool Node detail screen mockup."""
    img = create_base_image()
    draw = ImageDraw.Draw(img)

    draw_back_button(draw)
    font_title = get_font(12)
    draw.text((30, 10), "Pool Node Status", font=font_title, fill=COLORS["text_primary"])
    draw.line([(0, 35), (WIDTH, 35)], fill=COLORS["button_bg"], width=1)

    font_section = get_font(10)
    font_large = get_font(22)
    font_small = get_font(8)

    # Temperature section
    y = 45
    draw.text((10, y), "Temperature", font=font_section, fill=COLORS["accent"])
    draw.rectangle([10, y + 15, 230, y + 60], outline=COLORS["button_bg"])
    draw.text((70, y + 22), "55.2°F", font=font_large, fill=COLORS["value"])
    draw.text((50, y + 48), "Last: 55.0°F  Δ+0.2°", font=font_small, fill=COLORS["text_secondary"])

    # Water Level section (binary - just text status)
    y = 115
    draw.text((10, y), "Water Level", font=font_section, fill=COLORS["accent"])
    draw.rectangle([10, y + 15, 230, y + 45], outline=COLORS["button_bg"])

    # Binary status: either "OK" or "NEEDS WATER"
    draw.text((20, y + 22), "Status:", font=font_small, fill=COLORS["text_secondary"])
    draw.text((70, y + 22), "NEEDS WATER", font=font_section, fill=COLORS["warning"])

    # Battery section
    y = 170
    draw.text((10, y), "Battery", font=font_section, fill=COLORS["accent"])
    draw.rectangle([10, y + 15, 230, y + 45], outline=COLORS["button_bg"])

    bar_width = 150
    bar_fill = int(bar_width * 0.72)
    draw.rectangle([20, y + 22, 20 + bar_width, y + 35], outline=COLORS["text_secondary"])
    draw.rectangle([20, y + 22, 20 + bar_fill, y + 35], fill=COLORS["success"])
    draw.text((180, y + 22), "72%", font=font_small, fill=COLORS["success"])
    draw.text((180, y + 32), "3.85V", font=font_small, fill=COLORS["text_secondary"])

    # Last update info (moved from main screen) - larger text for detail pages
    y = 220
    font_msg_header = get_font(14)
    font_msg_value = get_font(12)
    draw.text((10, y), "Last Message Received:", font=font_msg_header, fill=COLORS["accent"])
    draw.text((10, y + 20), "01/22/2026 6:45:00 PM", font=font_msg_value, fill=COLORS["text_secondary"])

    draw.text((10, y + 45), "Reporting Interval:", font=font_msg_value, fill=COLORS["text_secondary"])
    draw.text((150, y + 45), "120 sec", font=font_msg_value, fill=COLORS["text_secondary"])

    draw.text((10, y + 65), "Message Age:", font=font_msg_value, fill=COLORS["text_secondary"])
    draw.text((120, y + 65), "45 seconds", font=font_msg_value, fill=COLORS["success"])

    return img


def generate_pool_detail_stale():
    """Generate Pool Node detail with stale data warning."""
    img = create_base_image()
    draw = ImageDraw.Draw(img)

    draw_back_button(draw)
    font_title = get_font(12)
    draw.text((30, 10), "Pool Node Status", font=font_title, fill=COLORS["text_primary"])
    draw.line([(0, 35), (WIDTH, 35)], fill=COLORS["button_bg"], width=1)

    font_section = get_font(10)
    font_large = get_font(22)
    font_small = get_font(8)

    # Stale warning banner
    draw.rectangle([10, 40, 230, 60], fill=COLORS["stale_bg"])
    draw_warning_icon(draw, 15, 44, size=12)
    draw.text((32, 45), "Data may be outdated", font=font_small, fill=COLORS["warning"])

    # Temperature section
    y = 70
    draw.text((10, y), "Temperature", font=font_section, fill=COLORS["accent"])
    draw.rectangle([10, y + 15, 230, y + 60], outline=COLORS["button_bg"])
    draw.text((70, y + 22), "55.2°F", font=font_large, fill=COLORS["value"])
    draw.text((50, y + 48), "Last: 55.0°F  Δ+0.2°", font=font_small, fill=COLORS["text_secondary"])

    # Water Level section
    y = 140
    draw.text((10, y), "Water Level", font=font_section, fill=COLORS["accent"])
    draw.rectangle([10, y + 15, 230, y + 45], outline=COLORS["button_bg"])
    draw.text((20, y + 22), "Status:", font=font_small, fill=COLORS["text_secondary"])
    draw.text((70, y + 22), "NEEDS WATER", font=font_section, fill=COLORS["warning"])

    # Battery section
    y = 195
    draw.text((10, y), "Battery", font=font_section, fill=COLORS["accent"])
    draw.rectangle([10, y + 15, 230, y + 45], outline=COLORS["button_bg"])

    bar_width = 150
    bar_fill = int(bar_width * 0.72)
    draw.rectangle([20, y + 22, 20 + bar_width, y + 35], outline=COLORS["text_secondary"])
    draw.rectangle([20, y + 22, 20 + bar_fill, y + 35], fill=COLORS["success"])
    draw.text((180, y + 22), "72%", font=font_small, fill=COLORS["success"])
    draw.text((180, y + 32), "3.85V", font=font_small, fill=COLORS["text_secondary"])

    # Last update info with stale indication - larger text for detail pages
    y = 250
    font_msg_header = get_font(14)
    font_msg_value = get_font(12)
    draw.text((10, y), "Last Message Received:", font=font_msg_header, fill=COLORS["accent"])
    draw.text((10, y + 20), "01/22/2026 6:35:00 PM", font=font_msg_value, fill=COLORS["warning"])

    draw.text((10, y + 45), "Message Age:", font=font_msg_value, fill=COLORS["text_secondary"])
    draw.text((120, y + 45), "10+ min (STALE)", font=font_msg_value, fill=COLORS["warning"])

    return img


def generate_valve_detail(filling=False):
    """Generate the Valve Node detail screen mockup."""
    img = create_base_image()
    draw = ImageDraw.Draw(img)

    draw_back_button(draw)
    font_title = get_font(12)
    draw.text((30, 10), "Valve Controller", font=font_title, fill=COLORS["text_primary"])
    draw.line([(0, 35), (WIDTH, 35)], fill=COLORS["button_bg"], width=1)

    font_section = get_font(10)
    font_large = get_font(22)
    font_small = get_font(8)

    # Outside Temperature section
    y = 45
    draw.text((10, y), "Outside Temperature", font=font_section, fill=COLORS["accent"])
    draw.rectangle([10, y + 15, 230, y + 50], outline=COLORS["button_bg"])
    draw.text((80, y + 22), "58°F", font=font_large, fill=COLORS["value"])

    # Fill Status section
    y = 105
    draw.text((10, y), "Fill Status", font=font_section, fill=COLORS["accent"])

    if filling:
        draw.rectangle([10, y + 15, 230, y + 85], outline=COLORS["status_active"], width=2)
        draw.ellipse([20, y + 22, 30, y + 32], fill=COLORS["status_active"])
        draw.text((35, y + 22), "FILLING 3:45", font=font_section, fill=COLORS["status_active"])
        draw.text((20, y + 45), "Elapsed: 3 min 45 sec", font=font_small, fill=COLORS["text_secondary"])
        draw.text((20, y + 57), "Max: 9 minutes", font=font_small, fill=COLORS["text_secondary"])
        draw.text((20, y + 69), "Remaining: 5 min 15 sec", font=font_small, fill=COLORS["text_secondary"])
    else:
        draw.rectangle([10, y + 15, 230, y + 85], outline=COLORS["button_bg"])
        draw.ellipse([20, y + 22, 30, y + 32], fill=COLORS["success"])
        draw.text((35, y + 22), "IDLE", font=font_section, fill=COLORS["success"])
        draw.text((20, y + 40), "Next Fill: 9:00 AM", font=font_small, fill=COLORS["text_secondary"])
        draw.text((20, y + 52), "(in 14h 15m)", font=font_small, fill=COLORS["text_secondary"])
        draw.text((20, y + 64), "Window: 9-11 AM", font=font_small, fill=COLORS["text_secondary"])
        draw.text((20, y + 76), "Max: 9 minutes", font=font_small, fill=COLORS["text_secondary"])

    # Manual Control section
    y = 200
    draw.text((10, y), "Manual Control", font=font_section, fill=COLORS["accent"])

    if filling:
        draw_button(draw, 15, y + 18, 100, 40, "START\nFILL", disabled=True)
    else:
        draw_button(draw, 15, y + 18, 100, 40, "START\nFILL")
    draw_button(draw, 125, y + 18, 100, 40, "STOP\nFILL")

    # Last message info (moved from main screen) - larger text for detail pages
    y = 255
    font_msg_header = get_font(14)
    font_msg_value = get_font(12)
    draw.text((10, y), "Last Fill:", font=font_msg_value, fill=COLORS["text_secondary"])
    draw.text((80, y), "01/22 9:05 AM (7 min)", font=font_msg_value, fill=COLORS["text_secondary"])
    draw.text((10, y + 22), "Last Message:", font=font_msg_header, fill=COLORS["accent"])
    draw.text((10, y + 42), "01/22 6:45:57 PM", font=font_msg_value, fill=COLORS["text_secondary"])
    draw.text((160, y + 42), "Age: 3s", font=font_msg_value, fill=COLORS["success"])

    return img


def generate_settings():
    """Generate the Settings screen mockup."""
    img = create_base_image()
    draw = ImageDraw.Draw(img)

    draw_back_button(draw)
    font_title = get_font(12)
    draw.text((80, 10), "Settings", font=font_title, fill=COLORS["text_primary"])
    draw.line([(0, 35), (WIDTH, 35)], fill=COLORS["button_bg"], width=1)

    font_section = get_font(10)
    font_small = get_font(8)

    # System Info section
    y = 45
    draw.text((10, y), "System Info", font=font_section, fill=COLORS["accent"])
    draw.rectangle([10, y + 15, 230, y + 90], outline=COLORS["button_bg"])

    draw.text((15, y + 20), "Environment: PROD", font=font_small, fill=COLORS["text_secondary"])
    draw.text((15, y + 32), "Device ID:", font=font_small, fill=COLORS["text_secondary"])
    draw.text((25, y + 44), "display-node-001", font=font_small, fill=COLORS["text_secondary"])
    draw.text((15, y + 56), "WiFi: Connected (HomeNet)", font=font_small, fill=COLORS["success"])
    draw.text((15, y + 68), "IP: 192.168.1.45", font=font_small, fill=COLORS["text_secondary"])
    draw.text((15, y + 80), "Signal: -65 dBm", font=font_small, fill=COLORS["text_secondary"])

    # Status section
    y = 145
    draw.text((10, y), "Status", font=font_section, fill=COLORS["accent"])
    draw.rectangle([10, y + 15, 230, y + 75], outline=COLORS["button_bg"])

    draw.text((15, y + 20), "Last Sync: 01/22 6:00:00 PM", font=font_small, fill=COLORS["text_secondary"])
    draw.text((15, y + 32), "Uptime: 2d 14h 32m", font=font_small, fill=COLORS["text_secondary"])
    draw.text((15, y + 44), "Errors: 0 since boot", font=font_small, fill=COLORS["success"])
    draw.text((15, y + 56), "Memory: 45,232 bytes free", font=font_small, fill=COLORS["text_secondary"])

    # Actions section
    y = 235
    draw.text((10, y), "Actions", font=font_section, fill=COLORS["accent"])

    draw_button(draw, 15, y + 18, 100, 40, "REFRESH\nALL")
    draw_button(draw, 125, y + 18, 100, 40, "RESET\nDEVICE")

    return img


def generate_confirmation_dialog(title, message, yes_text="Yes", no_text="Cancel"):
    """Generate a confirmation dialog overlay."""
    img = create_base_image()
    draw = ImageDraw.Draw(img)

    draw.rectangle([0, 0, WIDTH, HEIGHT], fill=(20, 20, 20))

    dialog_x, dialog_y = 20, 100
    dialog_w, dialog_h = 200, 120
    draw.rectangle([dialog_x, dialog_y, dialog_x + dialog_w, dialog_y + dialog_h],
                   fill=COLORS["dialog_bg"], outline=COLORS["text_secondary"])

    font_title = get_font(12)
    font_text = get_font(9)

    title_bbox = draw.textbbox((0, 0), title, font=font_title)
    title_width = title_bbox[2] - title_bbox[0]
    draw.text(((WIDTH - title_width) // 2, dialog_y + 15), title, font=font_title, fill=COLORS["text_primary"])

    lines = message.split('\n')
    for i, line in enumerate(lines):
        draw.text((dialog_x + 15, dialog_y + 40 + i * 14), line, font=font_text, fill=COLORS["text_secondary"])

    btn_y = dialog_y + dialog_h - 40
    draw_button(draw, dialog_x + 15, btn_y, 70, 30, yes_text)
    draw_button(draw, dialog_x + dialog_w - 85, btn_y, 70, 30, no_text)

    return img


def generate_historical_view(range_type="24h"):
    """Generate the historical data view mockup."""
    img = create_base_image()
    draw = ImageDraw.Draw(img)

    draw_back_button(draw)
    font_title = get_font(12)
    draw.text((30, 10), "Temperature History", font=font_title, fill=COLORS["text_primary"])
    draw.line([(0, 35), (WIDTH, 35)], fill=COLORS["button_bg"], width=1)

    font_small = get_font(8)
    font_section = get_font(10)

    # Chart area
    chart_x, chart_y = 20, 50
    chart_w, chart_h = 180, 120

    # Generate appropriate sample data based on range
    if range_type == "24h":
        # Sparkline for 24h - continuous line
        sample_data = [60 + 10 * math.sin(i * 0.15) + 5 * math.sin(i * 0.05) for i in range(50)]
        x_labels = ["6AM", "12PM", "6PM", "12AM"]
        stats = ("54°F", "75°F", "62°F")
        use_whisker = False
    elif range_type == "7d":
        # Whisker chart for 7d - min/max per day
        whisker_data = []
        for day in range(7):
            base = 58 + day * 0.5
            day_min = base + 2 * math.sin(day * 1.2) - 6
            day_max = base + 2 * math.sin(day * 1.2) + 8
            whisker_data.append((day_min, day_max))
        x_labels = ["M", "T", "W", "T", "F", "S", "S"]
        stats = ("52°F", "72°F", "61°F")
        use_whisker = True
    else:  # 30d
        # Whisker chart for 30d - min/max per day
        whisker_data = []
        for day in range(30):
            base = 55 + day * 0.3
            variation = 3 * math.sin(day * 0.5)
            day_min = base + variation - 5
            day_max = base + variation + 7
            whisker_data.append((day_min, day_max))
        x_labels = ["1", "8", "15", "22", "30"]
        stats = ("48°F", "68°F", "58°F")
        use_whisker = True

    # Y-axis labels
    draw.text((chart_x + chart_w + 5, chart_y), stats[1], font=font_small, fill=COLORS["text_secondary"])
    draw.text((chart_x + chart_w + 5, chart_y + chart_h - 10), stats[0], font=font_small, fill=COLORS["text_secondary"])

    # Chart border
    draw.rectangle([chart_x, chart_y, chart_x + chart_w, chart_y + chart_h], outline=COLORS["button_bg"])

    # Draw data - sparkline for 24h, whisker for 7d/30d
    if use_whisker:
        draw_whisker_chart(draw, whisker_data, chart_x + 5, chart_y + 5, chart_w - 10, chart_h - 10, COLORS["accent"])
    else:
        draw_sparkline(draw, sample_data, chart_x + 5, chart_y + 5, chart_w - 10, chart_h - 10, COLORS["accent"])

    # X-axis labels
    if range_type == "24h":
        label_positions = [0, 0.33, 0.67, 1.0]
    elif range_type == "7d":
        label_positions = [i / 6 for i in range(7)]
    else:  # 30d
        label_positions = [0, 0.24, 0.48, 0.72, 1.0]

    for i, label in enumerate(x_labels):
        x_pos = chart_x + int(label_positions[i] * (chart_w - 15))
        draw.text((x_pos, chart_y + chart_h + 5), label, font=font_small, fill=COLORS["text_secondary"])

    # Stats
    y = 200
    draw.text((20, y), f"Range: {stats[0]} - {stats[1]}", font=font_small, fill=COLORS["text_secondary"])
    draw.text((20, y + 15), f"Average: {stats[2]}", font=font_small, fill=COLORS["text_secondary"])

    # Range buttons
    y = 245
    draw_button(draw, 20, y, 60, 30, "24h", pressed=(range_type == "24h"))
    draw_button(draw, 90, y, 60, 30, "7d", pressed=(range_type == "7d"))
    draw_button(draw, 160, y, 60, 30, "30d", pressed=(range_type == "30d"))

    # Refresh button
    draw_button(draw, 70, 285, 100, 30, "REFRESH")

    return img


def generate_navigation_flow():
    """Generate a navigation flow diagram showing screen relationships and hotzones."""
    # Larger canvas for the flow diagram
    flow_width = 800
    flow_height = 700
    img = Image.new("RGB", (flow_width, flow_height), (30, 30, 30))
    draw = ImageDraw.Draw(img)

    font_title = get_font(16)
    font_label = get_font(11)
    font_small = get_font(9)

    # Title
    draw.text((flow_width // 2 - 150, 15), "Display Node Navigation Flow", font=font_title, fill=COLORS["text_primary"])

    # Main dashboard (center) with hotzones marked
    main_x, main_y = 280, 100
    main_w, main_h = 240, 320

    # Draw main dashboard frame
    draw.rectangle([main_x, main_y, main_x + main_w, main_y + main_h],
                   outline=COLORS["accent"], width=2)
    draw.text((main_x + 70, main_y + 5), "MAIN DASHBOARD", font=font_label, fill=COLORS["accent"])

    # Draw hotzones on main dashboard
    # Time/Settings hotzone (center header area)
    hz_settings = (main_x + 50, main_y + 20, main_x + 190, main_y + 65)
    draw.rectangle(hz_settings, outline=COLORS["warning"], width=2)
    draw.text((main_x + 85, main_y + 25), "6:45 PM", font=font_label, fill=COLORS["text_secondary"])
    draw.text((main_x + 70, main_y + 42), "tap time →", font=font_small, fill=COLORS["warning"])
    draw.text((main_x + 70, main_y + 53), "Settings", font=font_small, fill=COLORS["warning"])

    # Outside/Valve hotzone
    hz_valve = (main_x + 5, main_y + 80, main_x + main_w - 5, main_y + 120)
    draw.rectangle(hz_valve, outline=COLORS["success"], width=2)
    draw.text((main_x + 10, main_y + 85), "Outside: 58°", font=font_label, fill=COLORS["text_secondary"])
    draw.text((main_x + 10, main_y + 100), "→ Valve Detail", font=font_small, fill=COLORS["success"])

    # Pool hotzone
    hz_pool = (main_x + 5, main_y + 125, main_x + main_w - 5, main_y + 175)
    draw.rectangle(hz_pool, outline=COLORS["status_active"], width=2)
    draw.text((main_x + 10, main_y + 130), "Pool: 55°", font=font_label, fill=COLORS["text_secondary"])
    draw.text((main_x + 10, main_y + 145), "→ Pool Detail", font=font_small, fill=COLORS["status_active"])

    # Inside (no hotzone)
    draw.text((main_x + 10, main_y + 185), "Inside: 69°  54%", font=font_label, fill=COLORS["text_secondary"])
    draw.text((main_x + 10, main_y + 200), "(no navigation)", font=font_small, fill=(100, 100, 100))

    # Chart area
    draw.rectangle([main_x + 10, main_y + 220, main_x + main_w - 10, main_y + main_h - 10],
                   outline=COLORS["button_bg"])
    draw.text((main_x + 80, main_y + 260), "Sparkline", font=font_small, fill=COLORS["text_secondary"])

    # Detail screens
    screen_w, screen_h = 160, 200

    # Pool Detail (left)
    pool_x, pool_y = 40, 450
    draw.rectangle([pool_x, pool_y, pool_x + screen_w, pool_y + screen_h],
                   outline=COLORS["status_active"], width=2)
    draw.text((pool_x + 30, pool_y + 5), "POOL DETAIL", font=font_label, fill=COLORS["status_active"])
    draw.text((pool_x + 10, pool_y + 30), "← Back button", font=font_small, fill=COLORS["text_secondary"])
    draw.text((pool_x + 10, pool_y + 50), "• Temperature", font=font_small, fill=COLORS["text_secondary"])
    draw.text((pool_x + 10, pool_y + 65), "• Water Level", font=font_small, fill=COLORS["text_secondary"])
    draw.text((pool_x + 10, pool_y + 80), "• Battery", font=font_small, fill=COLORS["text_secondary"])
    draw.text((pool_x + 10, pool_y + 95), "• Last Message", font=font_small, fill=COLORS["text_secondary"])
    draw.text((pool_x + 10, pool_y + 120), "60s idle → home", font=font_small, fill=(100, 100, 100))

    # Valve Detail (center)
    valve_x, valve_y = 320, 450
    draw.rectangle([valve_x, valve_y, valve_x + screen_w, valve_y + screen_h],
                   outline=COLORS["success"], width=2)
    draw.text((valve_x + 25, valve_y + 5), "VALVE DETAIL", font=font_label, fill=COLORS["success"])
    draw.text((valve_x + 10, valve_y + 30), "← Back button", font=font_small, fill=COLORS["text_secondary"])
    draw.text((valve_x + 10, valve_y + 50), "• Outside Temp", font=font_small, fill=COLORS["text_secondary"])
    draw.text((valve_x + 10, valve_y + 65), "• Fill Status", font=font_small, fill=COLORS["text_secondary"])
    draw.text((valve_x + 10, valve_y + 80), "• START/STOP btns", font=font_small, fill=COLORS["text_secondary"])
    draw.text((valve_x + 10, valve_y + 95), "• Last Message", font=font_small, fill=COLORS["text_secondary"])
    draw.text((valve_x + 10, valve_y + 120), "START → confirm", font=font_small, fill=COLORS["warning"])
    draw.text((valve_x + 10, valve_y + 140), "60s idle → home", font=font_small, fill=(100, 100, 100))

    # Settings (right)
    settings_x, settings_y = 600, 450
    draw.rectangle([settings_x, settings_y, settings_x + screen_w, settings_y + screen_h],
                   outline=COLORS["warning"], width=2)
    draw.text((settings_x + 40, settings_y + 5), "SETTINGS", font=font_label, fill=COLORS["warning"])
    draw.text((settings_x + 10, settings_y + 30), "← Back button", font=font_small, fill=COLORS["text_secondary"])
    draw.text((settings_x + 10, settings_y + 50), "• System Info", font=font_small, fill=COLORS["text_secondary"])
    draw.text((settings_x + 10, settings_y + 65), "• Status", font=font_small, fill=COLORS["text_secondary"])
    draw.text((settings_x + 10, settings_y + 80), "• REFRESH btn", font=font_small, fill=COLORS["text_secondary"])
    draw.text((settings_x + 10, settings_y + 95), "• RESET btn", font=font_small, fill=COLORS["text_secondary"])
    draw.text((settings_x + 10, settings_y + 120), "RESET → confirm", font=font_small, fill=COLORS["warning"])
    draw.text((settings_x + 10, settings_y + 140), "60s idle → home", font=font_small, fill=(100, 100, 100))

    # Draw arrows from main to detail screens
    # Arrow to Pool Detail
    draw.line([(main_x + 60, main_y + main_h), (pool_x + screen_w // 2, pool_y)],
              fill=COLORS["status_active"], width=2)
    # Arrowhead
    draw.polygon([(pool_x + screen_w // 2, pool_y),
                  (pool_x + screen_w // 2 - 8, pool_y - 12),
                  (pool_x + screen_w // 2 + 8, pool_y - 12)],
                 fill=COLORS["status_active"])

    # Arrow to Valve Detail
    draw.line([(main_x + main_w // 2, main_y + main_h), (valve_x + screen_w // 2, valve_y)],
              fill=COLORS["success"], width=2)
    draw.polygon([(valve_x + screen_w // 2, valve_y),
                  (valve_x + screen_w // 2 - 8, valve_y - 12),
                  (valve_x + screen_w // 2 + 8, valve_y - 12)],
                 fill=COLORS["success"])

    # Arrow to Settings
    draw.line([(main_x + main_w - 20, main_y + main_h), (settings_x + screen_w // 2, settings_y)],
              fill=COLORS["warning"], width=2)
    draw.polygon([(settings_x + screen_w // 2, settings_y),
                  (settings_x + screen_w // 2 - 8, settings_y - 12),
                  (settings_x + screen_w // 2 + 8, settings_y - 12)],
                 fill=COLORS["warning"])

    # Legend
    legend_y = 15
    draw.text((20, legend_y), "Hotzone Colors:", font=font_small, fill=COLORS["text_secondary"])
    draw.rectangle([20, legend_y + 15, 35, legend_y + 25], outline=COLORS["status_active"], width=2)
    draw.text((40, legend_y + 15), "Pool section", font=font_small, fill=COLORS["status_active"])

    draw.rectangle([20, legend_y + 30, 35, legend_y + 40], outline=COLORS["success"], width=2)
    draw.text((40, legend_y + 30), "Valve section", font=font_small, fill=COLORS["success"])

    draw.rectangle([20, legend_y + 45, 35, legend_y + 55], outline=COLORS["warning"], width=2)
    draw.text((40, legend_y + 45), "Time (→Settings)", font=font_small, fill=COLORS["warning"])

    # Hotzone coordinates reference
    ref_x = 560
    draw.text((ref_x, legend_y), "Main Screen Hotzones:", font=font_small, fill=COLORS["text_secondary"])
    draw.text((ref_x, legend_y + 15), "Time→Settings: (50,20)-(190,65)", font=font_small, fill=COLORS["warning"])
    draw.text((ref_x, legend_y + 30), "Valve: (0,80)-(240,125)", font=font_small, fill=COLORS["success"])
    draw.text((ref_x, legend_y + 45), "Pool: (0,125)-(240,175)", font=font_small, fill=COLORS["status_active"])

    return img


def main():
    """Generate all mockups and save to files."""
    output_dir = Path(__file__).parent
    output_dir.mkdir(exist_ok=True)

    mockups = [
        ("01_main_dashboard.png", generate_main_dashboard()),
        ("02_main_dashboard_nonprod.png", generate_main_dashboard(nonprod=True)),
        ("03_main_dashboard_stale.png", generate_main_dashboard(pool_stale=True)),
        ("04_pool_detail.png", generate_pool_detail()),
        ("05_pool_detail_stale.png", generate_pool_detail_stale()),
        ("06_valve_detail.png", generate_valve_detail(filling=False)),
        ("07_valve_detail_filling.png", generate_valve_detail(filling=True)),
        ("08_settings.png", generate_settings()),
        ("09_dialog_fill_confirm.png", generate_confirmation_dialog(
            "Start Fill Now?",
            "This will open the\nfill valve for up to\n9 minutes."
        )),
        ("10_dialog_reset_confirm.png", generate_confirmation_dialog(
            "Reset Device?",
            "The display will\nrestart. This may\ntake 30 seconds."
        )),
        ("11_historical_24h.png", generate_historical_view("24h")),
        ("12_historical_7d.png", generate_historical_view("7d")),
        ("13_historical_30d.png", generate_historical_view("30d")),
    ]

    # Save 2x scaled versions only (better for documentation)
    for filename, img in mockups:
        scaled_img = img.resize((WIDTH * 2, HEIGHT * 2), Image.Resampling.NEAREST)
        filepath = output_dir / filename
        scaled_img.save(filepath)
        print(f"Generated: {filepath}")

    # Generate navigation flow diagram (not scaled, already large)
    nav_flow = generate_navigation_flow()
    nav_path = output_dir / "00_navigation_flow.png"
    nav_flow.save(nav_path)
    print(f"Generated: {nav_path}")

    print(f"\nAll mockups saved to: {output_dir}")


if __name__ == "__main__":
    main()
