from __future__ import annotations

from io import BytesIO
import math
import random

from PIL import Image, ImageDraw, ImageFont, ImageFilter


def font(size, bold=False):
    paths = [
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf",
    ]
    for path in paths:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            pass
    return ImageFont.load_default()


def color(value, default):
    try:
        value = str(value).strip().lstrip("#")
        if len(value) == 6:
            return tuple(bytes.fromhex(value))
    except ValueError:
        pass
    return default


def generate_local_campaign(
    *,
    specification=None,
    business_name="BrandAI",
    industry="Coffee",
    style="Premium",
    **kwargs,
):
    specification = specification or {}

    primary = color(specification.get("primary_color"), (46, 29, 23))
    accent = color(specification.get("accent_color"), (205, 137, 76))

    W = H = 1024
    image = Image.new("RGB", (W, H))
    pixels = image.load()

    # Warm photographic-style gradient background
    for y in range(H):
        for x in range(W):
            glow = max(0, 1 - math.hypot(x - 730, y - 410) / 900)
            pixels[x, y] = tuple(
                min(255, int(primary[i] * (0.75 + 0.25 * y / H) + glow * (45 if i == 0 else 22)))
                for i in range(3)
            )

    draw = ImageDraw.Draw(image)

    # Ambient lighting
    lighting = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(lighting)
    ld.ellipse((340, 100, 1160, 900), fill=(229, 135, 59, 55))
    lighting = lighting.filter(ImageFilter.GaussianBlur(105))
    image = Image.alpha_composite(image.convert("RGBA"), lighting)
    draw = ImageDraw.Draw(image)

    # Decorative framing
    draw.line((75, 95, 949, 95), fill=accent + (190,), width=3)
    draw.line((75, 925, 949, 925), fill=accent + (190,), width=3)

    # Brand name
    name = str(business_name).strip() or "Your Brand"
    draw.text((75, 125), name, font=font(63, True), fill=(255, 239, 220, 255))

    draw.text(
        (78, 220),
        "BREWED WITH PURPOSE",
        font=font(38, True),
        fill=accent + (255,),
    )

    draw.text(
        (80, 280),
        "Every cup has a story.",
        font=font(29),
        fill=(240, 219, 196, 255),
    )

    # Cup shadow
    draw.ellipse((320, 785, 875, 870), fill=(12, 7, 5, 120))

    # Saucer
    draw.ellipse((325, 745, 865, 850), fill=(205, 185, 164, 255))
    draw.ellipse((365, 753, 825, 823), fill=(110, 71, 48, 255))

    # Cup handle
    draw.ellipse((715, 455, 945, 725), fill=(224, 207, 185, 255))
    draw.ellipse((770, 515, 890, 670), fill=(72, 43, 31, 255))

    # Main cup body
    draw.rounded_rectangle(
        (370, 420, 785, 780),
        radius=65,
        fill=(234, 220, 199, 255),
        outline=(255, 244, 224, 255),
        width=9,
    )

    # Coffee surface
    draw.ellipse((380, 398, 775, 475), fill=(79, 43, 27, 255))
    draw.ellipse((410, 414, 745, 459), fill=(139, 80, 43, 255))

    # Cup highlight
    draw.arc(
        (390, 445, 760, 750),
        105,
        235,
        fill=(255, 250, 236, 175),
        width=12,
    )

    # Steam
    for offset in (-85, 0, 85):
        points = []
        for i in range(90):
            y = 390 - i * 1.5
            x = 575 + offset + math.sin(i / 12) * 21
            points.append((int(x), int(y)))

        draw.line(points, fill=(248, 225, 192, 125), width=7, joint="curve")

    # Coffee beans
    rng = random.Random(42)
    for _ in range(13):
        x = rng.randint(120, 850)
        y = rng.randint(680, 900)

        if 320 < x < 850 and y < 835:
            continue

        draw.ellipse(
            (x, y, x + 35, y + 22),
            fill=(87, 47, 29, 255),
            outline=(187, 120, 68, 255),
            width=2,
        )
        draw.arc(
            (x + 10, y + 3, x + 25, y + 19),
            45,
            225,
            fill=(211, 146, 91, 255),
            width=2,
        )

    draw.text(
        (80, 855),
        "CRAFTED FOR YOUR MOMENTS",
        font=font(25, True),
        fill=(255, 239, 220, 255),
    )

    output = BytesIO()
    image.convert("RGB").save(output, format="PNG")
    return output.getvalue()

