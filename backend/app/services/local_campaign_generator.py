from __future__ import annotations

from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import textwrap


def _color(value, fallback):
    try:
        value = str(value).strip()
        if len(value) == 7 and value.startswith("#"):
            return tuple(int(value[i:i+2], 16) for i in (1, 3, 5))
    except (ValueError, TypeError):
        pass
    return fallback


def generate_local_campaign(
    *,
    specification=None,
    business_name="BrandAI",
    industry="Business",
    style="Modern",
    **kwargs,
) -> bytes:
    specification = specification or {}

    primary = _color(
        specification.get("primary_color"),
        (24, 24, 32),
    )
    secondary = _color(
        specification.get("secondary_color"),
        (95, 75, 180),
    )
    accent = _color(
        specification.get("accent_color"),
        (230, 160, 90),
    )

    width = height = 1024
    image = Image.new("RGB", (width, height), primary)
    draw = ImageDraw.Draw(image)

    for y in range(height):
        ratio = y / height
        color = tuple(
            int(primary[i] * (1 - ratio) + secondary[i] * ratio)
            for i in range(3)
        )
        draw.line((0, y, width, y), fill=color)

    draw.ellipse(
        (610, -170, 1190, 410),
        outline=accent,
        width=8,
    )
    draw.ellipse(
        (700, -80, 1090, 310),
        outline=accent,
        width=3,
    )

    try:
        font_title = ImageFont.truetype("arialbd.ttf", 90)
        font_sub = ImageFont.truetype("arial.ttf", 36)
        font_small = ImageFont.truetype("arial.ttf", 25)
    except OSError:
        font_title = ImageFont.load_default()
        font_sub = ImageFont.load_default()
        font_small = ImageFont.load_default()

    draw.rounded_rectangle(
        (70, 115, 410, 165),
        radius=20,
        fill=accent,
    )

    draw.text(
        (92, 126),
        str(industry).upper()[:25],
        fill=(20, 20, 25),
        font=font_small,
    )

    title = str(business_name).strip() or "Your Brand"

    wrapped = textwrap.wrap(title, width=17)[:3]

    y = 340
    for line in wrapped:
        draw.text(
            (70, y),
            line,
            fill="white",
            font=font_title,
        )
        y += 112

    draw.line(
        (70, 760, 450, 760),
        fill=accent,
        width=7,
    )

    draw.text(
        (70, 805),
        f"Discover {industry}",
        fill="white",
        font=font_sub,
    )

    draw.text(
        (70, 930),
        f"{style} | BrandAI Campaign",
        fill=(230, 230, 230),
        font=font_small,
    )

    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()
