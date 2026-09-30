"""Brand Kit V2 deterministic production assets."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from PIL import Image, ImageChops, ImageOps


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
        int(round(sum(pixel[i] for pixel in samples) / len(samples)))
        for i in range(3)
    )


def _foreground_mask(
    image: Image.Image,
    threshold: int = 26,
) -> Image.Image:
    rgb = image.convert("RGB")
    background = _corner_background(rgb)
    reference = Image.new("RGB", rgb.size, background)
    difference = ImageChops.difference(rgb, reference).convert("L")

    return difference.point(
        lambda value: 255 if value >= threshold else 0
    )


def _transparent_identity(image: Image.Image) -> Image.Image:
    rgb = image.convert("RGB")
    mask = _foreground_mask(rgb)
    rgba = rgb.convert("RGBA")
    rgba.putalpha(mask)
    return rgba


def _trim(image: Image.Image, padding: int = 28) -> Image.Image:
    alpha = image.getchannel("A")
    box = alpha.getbbox()

    if not box:
        return image

    left, top, right, bottom = box

    left = max(0, left - padding)
    top = max(0, top - padding)
    right = min(image.width, right + padding)
    bottom = min(image.height, bottom + padding)

    return image.crop((left, top, right, bottom))


def _monochrome(
    transparent: Image.Image,
    color: tuple[int, int, int],
) -> Image.Image:
    alpha = transparent.getchannel("A")
    output = Image.new(
        "RGBA",
        transparent.size,
        (*color, 0),
    )
    solid = Image.new(
        "RGBA",
        transparent.size,
        (*color, 255),
    )
    output.paste(solid, (0, 0), alpha)
    return output


def _presentation(
    identity: Image.Image,
    background: tuple[int, int, int],
    size: tuple[int, int] = (1600, 1000),
) -> Image.Image:
    canvas = Image.new("RGB", size, background)

    logo = identity.copy()
    logo.thumbnail(
        (
            int(size[0] * 0.66),
            int(size[1] * 0.62),
        ),
        Image.Resampling.LANCZOS,
    )

    x = (size[0] - logo.width) // 2
    y = (size[1] - logo.height) // 2

    canvas.paste(
        logo,
        (x, y),
        logo.getchannel("A"),
    )

    return canvas


def build_brand_kit_assets(
    *,
    logo_path: Path,
    output_directory: Path,
) -> dict[str, Any]:
    """
    Create deterministic variants from the exact selected logo.

    Does not invent icon-only or alternate lockups when the selected asset
    does not contain a separately addressable master symbol.
    """
    output_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    with Image.open(logo_path) as source:
        source.load()
        original = source.convert("RGB")

    primary_path = output_directory / "primary.png"
    original.save(
        primary_path,
        format="PNG",
        optimize=True,
    )

    transparent = _trim(
        _transparent_identity(original)
    )

    transparent_path = (
        output_directory
        / "primary-transparent.png"
    )
    transparent.save(
        transparent_path,
        format="PNG",
        optimize=True,
    )

    black = _monochrome(
        transparent,
        (17, 17, 17),
    )
    black_path = output_directory / "black.png"
    black.save(
        black_path,
        format="PNG",
        optimize=True,
    )

    white = _monochrome(
        transparent,
        (255, 255, 255),
    )
    white_path = output_directory / "white.png"
    white.save(
        white_path,
        format="PNG",
        optimize=True,
    )

    light = _presentation(
        transparent,
        (248, 250, 252),
    )
    light_path = output_directory / "on-light.png"
    light.save(
        light_path,
        format="PNG",
        optimize=True,
    )

    dark = _presentation(
        white,
        (17, 24, 39),
    )
    dark_path = output_directory / "on-dark.png"
    dark.save(
        dark_path,
        format="PNG",
        optimize=True,
    )

    return {
        "primary": primary_path,
        "primary_transparent": transparent_path,
        "black": black_path,
        "white": white_path,
        "on_light": light_path,
        "on_dark": dark_path,
        "icon": None,
        "secondary_horizontal": None,
    }


def derive_extended_palette(
    primary: str,
    secondary: str,
    accent: str,
) -> dict[str, str]:
    return {
        "primary": primary,
        "secondary": secondary,
        "accent": accent,
        "background": "#F8FAFC",
        "text": "#111827",
    }
