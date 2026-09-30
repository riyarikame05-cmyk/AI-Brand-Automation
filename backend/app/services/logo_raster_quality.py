"""Deterministic raster QA measurements for rendered logo candidates."""

from __future__ import annotations

from io import BytesIO
from typing import Any

from PIL import Image, ImageChops, ImageStat


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _luminance(rgb: tuple[int, int, int]) -> float:
    red, green, blue = rgb
    return (
        0.2126 * red
        + 0.7152 * green
        + 0.0722 * blue
    ) / 255.0


def _corner_background(image: Image.Image) -> tuple[int, int, int]:
    rgb = image.convert("RGB")
    width, height = rgb.size

    points = (
        (0, 0),
        (width - 1, 0),
        (0, height - 1),
        (width - 1, height - 1),
    )

    samples = [rgb.getpixel(point) for point in points]

    return tuple(
        int(round(sum(pixel[channel] for pixel in samples) / 4))
        for channel in range(3)
    )


def _foreground_mask(
    image: Image.Image,
    background: tuple[int, int, int],
    threshold: int = 28,
) -> Image.Image:
    rgb = image.convert("RGB")
    background_image = Image.new("RGB", rgb.size, background)
    difference = ImageChops.difference(rgb, background_image)
    grayscale = difference.convert("L")

    return grayscale.point(
        lambda value: 255 if value >= threshold else 0,
        mode="1",
    )


def _bbox_metrics(
    mask: Image.Image,
) -> tuple[float, float, float, float, bool]:
    width, height = mask.size
    bbox = mask.getbbox()

    if not bbox or width <= 0 or height <= 0:
        return 0.0, 0.0, 0.0, 0.0, False

    left, top, right, bottom = bbox
    box_width = max(1, right - left)
    box_height = max(1, bottom - top)

    bbox_area = box_width * box_height
    canvas_area = width * height

    bbox_occupancy = bbox_area / canvas_area

    center_x = (left + right) / 2.0
    center_y = (top + bottom) / 2.0

    x_offset = abs(center_x - width / 2.0) / (width / 2.0)
    y_offset = abs(center_y - height / 2.0) / (height / 2.0)

    balance = 1.0 - min(
        1.0,
        (x_offset + y_offset) / 2.0,
    )

    margin = max(1, round(min(width, height) * 0.01))

    clipped = (
        left <= margin
        or top <= margin
        or right >= width - margin
        or bottom >= height - margin
    )

    aspect = min(box_width, box_height) / max(box_width, box_height)

    return (
        _clamp(bbox_occupancy),
        _clamp(balance),
        _clamp(aspect),
        bbox_area,
        clipped,
    )


def _ink_occupancy(mask: Image.Image) -> float:
    histogram = mask.convert("L").histogram()
    foreground = sum(histogram[128:])
    total = mask.width * mask.height

    if total <= 0:
        return 0.0

    return _clamp(foreground / total)


def _contrast(
    image: Image.Image,
    mask: Image.Image,
    background: tuple[int, int, int],
) -> float:
    rgb = image.convert("RGB")
    mask_l = mask.convert("L")

    inverted = ImageChops.invert(mask_l)

    foreground_stats = ImageStat.Stat(rgb, mask=mask_l)
    background_stats = ImageStat.Stat(rgb, mask=inverted)

    foreground_count = sum(mask_l.histogram()[128:])
    background_count = sum(inverted.histogram()[128:])

    if foreground_count <= 0 or background_count <= 0:
        return 0.0

    foreground_rgb = tuple(
        int(round(value))
        for value in foreground_stats.mean[:3]
    )

    background_rgb = tuple(
        int(round(value))
        for value in background_stats.mean[:3]
    )

    measured = abs(
        _luminance(foreground_rgb)
        - _luminance(background_rgb)
    )

    corner_reference = abs(
        _luminance(foreground_rgb)
        - _luminance(background)
    )

    return _clamp(max(measured, corner_reference))


def _small_size_survival(
    image: Image.Image,
    background: tuple[int, int, int],
) -> float:
    small = image.convert("RGB")
    small.thumbnail((64, 64), Image.Resampling.LANCZOS)

    canvas = Image.new("RGB", (64, 64), background)

    left = (64 - small.width) // 2
    top = (64 - small.height) // 2

    canvas.paste(small, (left, top))

    mask = _foreground_mask(
        canvas,
        background,
        threshold=24,
    )

    bbox = mask.getbbox()

    if not bbox:
        return 0.0

    ink = _ink_occupancy(mask)

    # At icon size, both vanishingly thin and nearly solid marks
    # are poor performers.
    if ink < 0.015:
        return _clamp(ink / 0.015)

    if ink > 0.72:
        return _clamp(1.0 - (ink - 0.72) / 0.28)

    target = 0.22
    distance = abs(ink - target)

    return _clamp(1.0 - distance / 0.50)


def analyze_logo_png(image_bytes: bytes) -> dict[str, Any]:
    """Measure objective visual properties from a rendered PNG."""
    if not isinstance(image_bytes, (bytes, bytearray)):
        raise TypeError("image_bytes must contain PNG bytes")

    with Image.open(BytesIO(bytes(image_bytes))) as source:
        source.load()
        image = source.convert("RGBA")

    if image.width < 32 or image.height < 32:
        raise ValueError("logo raster is too small for QA")

    rgb = image.convert("RGB")
    background = _corner_background(rgb)
    mask = _foreground_mask(rgb, background)

    (
        bbox_occupancy,
        balance,
        aspect,
        bbox_area,
        clipped,
    ) = _bbox_metrics(mask)

    ink_occupancy = _ink_occupancy(mask)
    contrast = _contrast(rgb, mask, background)
    small_size = _small_size_survival(rgb, background)

    silhouette_strength = _clamp(
        small_size * 0.50
        + contrast * 0.30
        + aspect * 0.20
    )

    return {
        "width": image.width,
        "height": image.height,
        "background_rgb": background,
        "bbox_occupancy": round(bbox_occupancy, 4),
        "ink_occupancy": round(ink_occupancy, 4),
        "balance": round(balance, 4),
        "contrast": round(contrast, 4),
        "small_size_survival": round(small_size, 4),
        "silhouette_strength": round(silhouette_strength, 4),
        "aspect_balance": round(aspect, 4),
        "bbox_area": int(bbox_area),
        "edge_clipped": bool(clipped),
    }
