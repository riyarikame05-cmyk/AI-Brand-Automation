from __future__ import annotations

import math
import uuid
from pathlib import Path

import numpy as np

from PIL import (
    Image,
    ImageDraw,
    ImageFont,
    ImageFilter,
)

from moviepy import (
    VideoClip,
    concatenate_videoclips,
)


# =========================================================
# SETTINGS
# =========================================================

WIDTH = 1080
HEIGHT = 1080
FPS = 30

INTRO_DURATION = 2.4
IDENTITY_DURATION = 2.5
MESSAGE_DURATION = 2.8
OUTRO_DURATION = 2.3


# =========================================================
# FONT LOADER
# =========================================================

def get_font(
    size: int,
    bold: bool = False,
):
    if bold:
        paths = [
            "C:/Windows/Fonts/segoeuib.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        ]
    else:
        paths = [
            "C:/Windows/Fonts/segoeui.ttf",
            "C:/Windows/Fonts/arial.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]

    for path in paths:
        try:
            return ImageFont.truetype(
                path,
                size,
            )
        except OSError:
            continue

    return ImageFont.load_default()


# =========================================================
# COLOR HELPERS
# =========================================================

def hex_to_rgb(
    value,
    fallback=(15, 23, 42),
):
    try:
        value = (
            str(value)
            .strip()
            .lstrip("#")
        )

        if len(value) != 6:
            return fallback

        return tuple(
            int(
                value[index:index + 2],
                16,
            )
            for index in (
                0,
                2,
                4,
            )
        )

    except Exception:
        return fallback


def mix(
    color_a,
    color_b,
    amount,
):
    amount = max(
        0.0,
        min(
            1.0,
            amount,
        ),
    )

    return tuple(
        int(
            color_a[index]
            * (1 - amount)
            + color_b[index]
            * amount
        )
        for index in range(3)
    )


def rgba(
    color,
    alpha,
):
    return (
        color[0],
        color[1],
        color[2],
        alpha,
    )


def luminance(
    color,
):
    return (
        0.299 * color[0]
        + 0.587 * color[1]
        + 0.114 * color[2]
    )


def contrast_color(
    color,
):
    if luminance(color) > 165:
        return (
            15,
            23,
            42,
        )

    return (
        255,
        255,
        255,
    )


# =========================================================
# TEXT HELPERS
# =========================================================

def text_width(
    draw,
    text,
    font,
):
    box = draw.textbbox(
        (0, 0),
        str(text),
        font=font,
    )

    return (
        box[2]
        - box[0]
    )


def draw_centered(
    draw,
    text,
    y,
    font,
    fill,
):
    text = str(text)

    width = text_width(
        draw,
        text,
        font,
    )

    draw.text(
        (
            (WIDTH - width) / 2,
            y,
        ),
        text,
        font=font,
        fill=fill,
    )


def wrap_text(
    draw,
    text,
    font,
    max_width,
):
    words = (
        str(text or "")
        .strip()
        .split()
    )

    if not words:
        return []

    lines = []
    current = ""

    for word in words:
        candidate = (
            f"{current} {word}"
            .strip()
        )

        if (
            not current
            or text_width(
                draw,
                candidate,
                font,
            )
            <= max_width
        ):
            current = candidate

        else:
            lines.append(current)
            current = word

    if current:
        lines.append(current)

    return lines


def draw_wrapped_centered(
    draw,
    text,
    center_y,
    font,
    fill,
    max_width=820,
    line_height=64,
    max_lines=4,
):
    lines = wrap_text(
        draw,
        text,
        font,
        max_width,
    )

    lines = lines[:max_lines]

    if not lines:
        return

    total_height = (
        len(lines)
        * line_height
    )

    start_y = (
        center_y
        - total_height / 2
    )

    for index, line in enumerate(lines):
        draw_centered(
            draw,
            line,
            start_y
            + index * line_height,
            font,
            fill,
        )


def fit_title_font(
    draw,
    text,
    maximum_size=74,
    minimum_size=38,
    maximum_width=850,
):
    size = maximum_size

    while size >= minimum_size:
        font = get_font(
            size,
            True,
        )

        if (
            text_width(
                draw,
                text,
                font,
            )
            <= maximum_width
        ):
            return font

        size -= 2

    return get_font(
        minimum_size,
        True,
    )


# =========================================================
# BACKGROUND GENERATION
# =========================================================

def gradient_background(
    start,
    end,
    horizontal=False,
):
    array = np.zeros(
        (
            HEIGHT,
            WIDTH,
            3,
        ),
        dtype=np.uint8,
    )

    if horizontal:
        gradient = np.linspace(
            0.0,
            1.0,
            WIDTH,
        )

        for channel in range(3):
            array[
                :,
                :,
                channel,
            ] = (
                start[channel]
                + (
                    end[channel]
                    - start[channel]
                )
                * gradient
            ).astype(
                np.uint8
            )

    else:
        gradient = np.linspace(
            0.0,
            1.0,
            HEIGHT,
        )

        for channel in range(3):
            array[
                :,
                :,
                channel,
            ] = (
                start[channel]
                + (
                    end[channel]
                    - start[channel]
                )
                * gradient[:, None]
            ).astype(
                np.uint8
            )

    return Image.fromarray(
        array,
        mode="RGB",
    )


# =========================================================
# DECORATIVE BRAND ELEMENTS
# =========================================================

def add_glow(
    image,
    center,
    radius,
    color,
    opacity=80,
):
    overlay = Image.new(
        "RGBA",
        (
            WIDTH,
            HEIGHT,
        ),
        (
            0,
            0,
            0,
            0,
        ),
    )

    draw = ImageDraw.Draw(
        overlay
    )

    cx, cy = center

    draw.ellipse(
        (
            cx - radius,
            cy - radius,
            cx + radius,
            cy + radius,
        ),
        fill=rgba(
            color,
            opacity,
        ),
    )

    overlay = overlay.filter(
        ImageFilter.GaussianBlur(
            radius // 2,
        )
    )

    return Image.alpha_composite(
        image.convert("RGBA"),
        overlay,
    ).convert("RGB")


def add_brand_shapes(
    image,
    primary,
    secondary,
    accent,
):
    image = add_glow(
        image,
        (
            80,
            100,
        ),
        270,
        secondary,
        75,
    )

    image = add_glow(
        image,
        (
            1000,
            940,
        ),
        310,
        accent,
        65,
    )

    overlay = Image.new(
        "RGBA",
        (
            WIDTH,
            HEIGHT,
        ),
        (
            0,
            0,
            0,
            0,
        ),
    )

    draw = ImageDraw.Draw(
        overlay
    )

    # Top-right brand line.
    draw.rounded_rectangle(
        (
            815,
            90,
            980,
            101,
        ),
        radius=6,
        fill=rgba(
            accent,
            190,
        ),
    )

    # Bottom-left subtle line.
    draw.rounded_rectangle(
        (
            100,
            940,
            270,
            949,
        ),
        radius=5,
        fill=rgba(
            secondary,
            150,
        ),
    )

    # Decorative rings.
    draw.ellipse(
        (
            790,
            -100,
            1170,
            280,
        ),
        outline=rgba(
            accent,
            45,
        ),
        width=4,
    )

    draw.ellipse(
        (
            -130,
            760,
            270,
            1160,
        ),
        outline=rgba(
            secondary,
            40,
        ),
        width=4,
    )

    return Image.alpha_composite(
        image.convert("RGBA"),
        overlay,
    ).convert("RGB")


# =========================================================
# LOGO HELPERS
# =========================================================

def load_logo(
    logo_path,
):
    path = Path(
        logo_path
    )

    if not path.exists():
        raise FileNotFoundError(
            f"Logo file does not exist: {path}"
        )

    logo = Image.open(
        path
    ).convert(
        "RGBA"
    )

    return logo


def resize_logo(
    logo,
    maximum_width,
    maximum_height,
):
    result = logo.copy()

    result.thumbnail(
        (
            maximum_width,
            maximum_height,
        ),
        Image.Resampling.LANCZOS,
    )

    return result


def paste_logo(
    image,
    logo,
    center_x,
    center_y,
):
    x = int(
        center_x
        - logo.width / 2
    )

    y = int(
        center_y
        - logo.height / 2
    )

    image.paste(
        logo,
        (
            x,
            y,
        ),
        logo,
    )


def add_logo_card(
    image,
    logo,
    center_y,
    card_size=570,
):
    card_width = card_size
    card_height = card_size

    left = (
        WIDTH
        - card_width
    ) // 2

    top = int(
        center_y
        - card_height / 2
    )

    overlay = Image.new(
        "RGBA",
        (
            WIDTH,
            HEIGHT,
        ),
        (
            0,
            0,
            0,
            0,
        ),
    )

    draw = ImageDraw.Draw(
        overlay
    )

    # Shadow.
    draw.rounded_rectangle(
        (
            left + 12,
            top + 18,
            left + card_width + 12,
            top + card_height + 18,
        ),
        radius=48,
        fill=(
            0,
            0,
            0,
            55,
        ),
    )

    # White presentation card.
    draw.rounded_rectangle(
        (
            left,
            top,
            left + card_width,
            top + card_height,
        ),
        radius=48,
        fill=(
            255,
            255,
            255,
            246,
        ),
    )

    image = Image.alpha_composite(
        image.convert("RGBA"),
        overlay,
    ).convert("RGB")

    logo_display = resize_logo(
        logo,
        int(
            card_width * 0.78
        ),
        int(
            card_height * 0.78
        ),
    )

    paste_logo(
        image,
        logo_display,
        WIDTH // 2,
        center_y,
    )

    return image


# =========================================================
# SCENE 1 — CINEMATIC LOGO REVEAL
# =========================================================

def create_intro_scene(
    logo,
    primary,
    secondary,
    accent,
):
    dark = mix(
        primary,
        (
            2,
            6,
            18,
        ),
        0.68,
    )

    mid = mix(
        primary,
        secondary,
        0.25,
    )

    image = gradient_background(
        dark,
        mid,
    )

    image = add_brand_shapes(
        image,
        primary,
        secondary,
        accent,
    )

    image = add_logo_card(
        image,
        logo,
        center_y=505,
        card_size=590,
    )

    draw = ImageDraw.Draw(
        image
    )

    label_font = get_font(
        24,
        True,
    )

    draw_centered(
        draw,
        "A NEW BRAND IDENTITY",
        875,
        label_font,
        accent,
    )

    return image


# =========================================================
# SCENE 2 — BRAND IDENTITY
# =========================================================

def create_identity_scene(
    business_name,
    slogan,
    primary,
    secondary,
    accent,
):
    dark = mix(
        primary,
        (
            3,
            7,
            18,
        ),
        0.68,
    )

    image = gradient_background(
        primary,
        dark,
        horizontal=True,
    )

    image = add_brand_shapes(
        image,
        primary,
        secondary,
        accent,
    )

    draw = ImageDraw.Draw(
        image
    )

    name = (
        business_name
        .strip()
        .upper()
    )

    title_font = fit_title_font(
        draw,
        name,
        maximum_size=82,
        minimum_size=42,
        maximum_width=850,
    )

    label_font = get_font(
        24,
        True,
    )

    slogan_font = get_font(
        38,
        False,
    )

    draw_centered(
        draw,
        "INTRODUCING",
        280,
        label_font,
        accent,
    )

    draw_centered(
        draw,
        name,
        370,
        title_font,
        (
            255,
            255,
            255,
        ),
    )

    # Accent divider.
    divider_width = 150

    draw.rounded_rectangle(
        (
            WIDTH // 2
            - divider_width // 2,
            505,
            WIDTH // 2
            + divider_width // 2,
            515,
        ),
        radius=5,
        fill=accent,
    )

    draw_wrapped_centered(
        draw,
        slogan,
        center_y=640,
        font=slogan_font,
        fill=(
            235,
            240,
            248,
        ),
        max_width=800,
        line_height=55,
        max_lines=3,
    )

    return image


# =========================================================
# SCENE 3 — MARKETING MESSAGE
# =========================================================

def create_message_scene(
    marketing_message,
    personality,
    primary,
    secondary,
    accent,
):
    light_start = mix(
        (
            255,
            255,
            255,
        ),
        accent,
        0.05,
    )

    light_end = mix(
        (
            244,
            247,
            252,
        ),
        secondary,
        0.07,
    )

    image = gradient_background(
        light_start,
        light_end,
        horizontal=True,
    )

    image = add_glow(
        image,
        (
            930,
            170,
        ),
        260,
        accent,
        50,
    )

    image = add_glow(
        image,
        (
            120,
            890,
        ),
        300,
        secondary,
        35,
    )

    draw = ImageDraw.Draw(
        image
    )

    label_font = get_font(
        23,
        True,
    )

    message_font = get_font(
        46,
        True,
    )

    chip_font = get_font(
        22,
        True,
    )

    draw_centered(
        draw,
        "WHAT WE STAND FOR",
        210,
        label_font,
        primary,
    )

    draw_wrapped_centered(
        draw,
        marketing_message,
        center_y=460,
        font=message_font,
        fill=(
            20,
            30,
            50,
        ),
        max_width=820,
        line_height=64,
        max_lines=4,
    )

    # -----------------------------------------------------
    # Personality chips
    # -----------------------------------------------------

    words = (
        list(personality[:3])
        if personality
        else [
            "Modern",
            "Professional",
            "Reliable",
        ]
    )

    chip_colors = [
        primary,
        secondary,
        accent,
    ]

    chip_y = 760
    gap = 18

    chip_data = []

    for word in words:
        label = str(
            word
        ).upper()

        width = (
            text_width(
                draw,
                label,
                chip_font,
            )
            + 48
        )

        chip_data.append(
            (
                label,
                width,
            )
        )

    total_width = (
        sum(
            width
            for _, width
            in chip_data
        )
        + gap
        * max(
            0,
            len(chip_data) - 1,
        )
    )

    current_x = (
        WIDTH
        - total_width
    ) / 2

    for index, (
        label,
        chip_width,
    ) in enumerate(
        chip_data
    ):
        color = chip_colors[
            index
            % len(chip_colors)
        ]

        text_fill = contrast_color(
            color
        )

        draw.rounded_rectangle(
            (
                current_x,
                chip_y,
                current_x + chip_width,
                chip_y + 58,
            ),
            radius=29,
            fill=color,
        )

        label_width = text_width(
            draw,
            label,
            chip_font,
        )

        draw.text(
            (
                current_x
                + (
                    chip_width
                    - label_width
                )
                / 2,
                chip_y + 14,
            ),
            label,
            font=chip_font,
            fill=text_fill,
        )

        current_x += (
            chip_width
            + gap
        )

    return image


# =========================================================
# SCENE 4 — OUTRO / CALL TO ACTION
# =========================================================

def create_outro_scene(
    logo,
    business_name,
    primary,
    secondary,
    accent,
):
    dark = mix(
        primary,
        (
            2,
            5,
            15,
        ),
        0.72,
    )

    image = gradient_background(
        dark,
        mix(
            dark,
            secondary,
            0.22,
        ),
    )

    image = add_brand_shapes(
        image,
        primary,
        secondary,
        accent,
    )

    image = add_logo_card(
        image,
        logo,
        center_y=380,
        card_size=420,
    )

    draw = ImageDraw.Draw(
        image
    )

    name = (
        business_name
        .strip()
        .upper()
    )

    name_font = fit_title_font(
        draw,
        name,
        maximum_size=60,
        minimum_size=36,
        maximum_width=830,
    )

    tagline_font = get_font(
        30,
        False,
    )

    small_font = get_font(
        21,
        True,
    )

    draw_centered(
        draw,
        name,
        640,
        name_font,
        (
            255,
            255,
            255,
        ),
    )

    draw.rounded_rectangle(
        (
            470,
            735,
            610,
            745,
        ),
        radius=5,
        fill=accent,
    )

    draw_centered(
        draw,
        "CRAFTED WITH PURPOSE.",
        795,
        tagline_font,
        (
            230,
            235,
            245,
        ),
    )

    draw_centered(
        draw,
        "A DISTINCTIVE EXPERIENCE.",
        885,
        small_font,
        accent,
    )

    return image


# =========================================================
# MOTION HELPERS
# =========================================================

def ease_in_out(
    value,
):
    value = max(
        0.0,
        min(
            1.0,
            value,
        ),
    )

    return (
        value
        * value
        * (
            3
            - 2 * value
        )
    )



def premium_motion_overlay(frame, t, duration):
    import math

    image = frame.convert("RGBA")
    layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)

    progress = min(1.0, max(0.0, t / max(duration, 0.01)))

    # Animated copper sweep
    sweep_x = int(-250 + progress * 1550)

    for i in range(12):
        x = sweep_x + i * 7
        draw.line(
            [(x, 0), (x - 340, HEIGHT)],
            fill=(200, 121, 65, 4),
            width=3,
        )

    # Floating particles
    for i in range(20):
        phase = i * 2.4

        x = (
            WIDTH * 0.5
            + math.sin(phase) * WIDTH * 0.44
            + math.sin(t + i) * 18
        )

        y = (i * 173 - t * 30) % HEIGHT
        radius = 2 + i % 3

        draw.ellipse(
            (x-radius, y-radius, x+radius, y+radius),
            fill=(232, 169, 104, 42),
        )

    # Animated steam
    for ribbon in range(3):
        points = []

        for step in range(40):
            p = step / 39

            x = (
                WIDTH * (0.17 + ribbon * 0.32)
                + math.sin(p * 8 + t * 1.7 + ribbon)
                * (16 + p * 25)
            )

            y = HEIGHT * 0.92 - p * HEIGHT * 0.68

            points.append((int(x), int(y)))

        draw.line(
            points,
            fill=(225, 161, 105, 36),
            width=3,
        )

    return Image.alpha_composite(
        image,
        layer,
    ).convert("RGB")


def animated_image_clip(
    pil_image,
    duration,
    zoom_start=1.0,
    zoom_end=1.04,
    pan_x=0,
    pan_y=0,
    fade_duration=0.22,
):
    base = pil_image.convert(
        "RGB"
    )

    fade_duration = min(
        fade_duration,
        duration / 3,
    )

    def frame_function(t):
        raw_progress = (
            t / duration
            if duration
            else 0
        )

        progress = ease_in_out(
            raw_progress
        )

        scale = (
            zoom_start
            + (
                zoom_end
                - zoom_start
            )
            * progress
        )

        new_width = max(
            WIDTH,
            int(
                WIDTH
                * scale
            ),
        )

        new_height = max(
            HEIGHT,
            int(
                HEIGHT
                * scale
            ),
        )

        frame = base.resize(
            (
                new_width,
                new_height,
            ),
            Image.Resampling.LANCZOS,
        )

        extra_x = (
            new_width
            - WIDTH
        )

        extra_y = (
            new_height
            - HEIGHT
        )

        shift_x = (
            pan_x
            * progress
        )

        shift_y = (
            pan_y
            * progress
        )

        left = int(
            extra_x / 2
            + shift_x
        )

        top = int(
            extra_y / 2
            + shift_y
        )

        left = max(
            0,
            min(
                left,
                extra_x,
            ),
        )

        top = max(
            0,
            min(
                top,
                extra_y,
            ),
        )

        frame = frame.crop(
            (
                left,
                top,
                left + WIDTH,
                top + HEIGHT,
            )
        )

        frame = premium_motion_overlay(
            frame,
            t,
            duration,
        )

        frame_array = np.array(
            frame,
            dtype=np.float32,
        )

        # -------------------------------------------------
        # Soft fade-in and fade-out.
        # This gives the scene changes a less abrupt feel
        # without depending on MoviePy version-specific
        # transition APIs.
        # -------------------------------------------------

        opacity = 1.0

        if fade_duration > 0:
            if t < fade_duration:
                opacity = max(
                    0.0,
                    min(
                        1.0,
                        t / fade_duration,
                    ),
                )

            elif t > (
                duration
                - fade_duration
            ):
                opacity = max(
                    0.0,
                    min(
                        1.0,
                        (
                            duration - t
                        )
                        / fade_duration,
                    ),
                )

        # Animated warm cinematic lighting.
        yy, xx = np.ogrid[:HEIGHT, :WIDTH]

        light_x = WIDTH * (0.22 + 0.56 * progress)
        light_y = HEIGHT * (0.18 + 0.22 * progress)

        distance = (
            ((xx - light_x) / (WIDTH * 0.58)) ** 2
            + ((yy - light_y) / (HEIGHT * 0.62)) ** 2
        )

        glow = np.exp(-distance * 3.0).astype(np.float32)

        frame_array[:, :, 0] += glow * 11.0
        frame_array[:, :, 1] += glow * 5.5
        frame_array[:, :, 2] += glow * 1.5

        if opacity < 1.0:
            frame_array *= opacity

        return np.clip(
            frame_array,
            0,
            255,
        ).astype(
            np.uint8
        )

    return VideoClip(
        frame_function,
        duration=duration,
    )


# =========================================================
# MAIN VIDEO GENERATOR V2
# =========================================================

def generate_promotional_video_v2(
    logo_path: Path,
    output_directory: Path,
    business_name: str = "Your Brand",
    slogan: str = "",
    personality=None,
    marketing_message: str = "",
    primary_color: str = "#4F46E5",
    secondary_color: str = "#7C3AED",
    accent_color: str = "#06B6D4",
):
    """
    Generate the local promotional brand video.

    This function intentionally keeps the same public
    signature expected by video_provider.py.

    Approximate duration:
        10 seconds

    Scenes:
        1. Logo reveal
        2. Brand identity + slogan
        3. Marketing message + personality
        4. Final logo / brand outro
    """

    print("")
    print("========================================")
    print("[VIDEO V2] Local promotional video")
    print("========================================")
    print(f"[VIDEO V2] Business: {business_name}")
    print(f"[VIDEO V2] Logo: {logo_path}")

    # -----------------------------------------------------
    # SAFE DEFAULTS
    # -----------------------------------------------------

    business_name = (
        str(
            business_name
            or "Your Brand"
        )
        .strip()
    )

    if personality is None:
        personality = [
            "Modern",
            "Professional",
            "Reliable",
        ]

    elif isinstance(
        personality,
        str,
    ):
        personality = [
            item.strip()
            for item in personality.split(",")
            if item.strip()
        ]

    else:
        personality = [
            str(item).strip()
            for item in personality
            if str(item).strip()
        ]

    if not personality:
        personality = [
            "Modern",
            "Professional",
            "Reliable",
        ]

    if not slogan:
        slogan = (
            "Built for what comes next."
        )

    if not marketing_message:
        marketing_message = (
            "A modern brand built around "
            "quality, trust and customer value."
        )

    # -----------------------------------------------------
    # OUTPUT DIRECTORY
    # -----------------------------------------------------

    output_directory = Path(
        output_directory
    )

    output_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    # -----------------------------------------------------
    # COLORS
    # -----------------------------------------------------

    primary = hex_to_rgb(
        primary_color,
        (
            79,
            70,
            229,
        ),
    )

    secondary = hex_to_rgb(
        secondary_color,
        (
            124,
            58,
            237,
        ),
    )

    accent = hex_to_rgb(
        accent_color,
        (
            6,
            182,
            212,
        ),
    )

    # -----------------------------------------------------
    # LOGO
    # -----------------------------------------------------

    logo = load_logo(
        Path(
            logo_path
        )
    )

    # -----------------------------------------------------
    # BUILD FOUR SCENES
    # -----------------------------------------------------

    print(
        "[VIDEO V2] Building scenes..."
    )

    scenes = [
        (
            create_intro_scene(
                logo,
                primary,
                secondary,
                accent,
            ),
            INTRO_DURATION,
            1.00,
            1.055,
            8,
            8,
        ),

        (
            create_identity_scene(
                business_name,
                slogan,
                primary,
                secondary,
                accent,
            ),
            IDENTITY_DURATION,
            1.045,
            1.005,
            -8,
            5,
        ),

        (
            create_message_scene(
                marketing_message,
                personality,
                primary,
                secondary,
                accent,
            ),
            MESSAGE_DURATION,
            1.00,
            1.035,
            6,
            -6,
        ),

        (
            create_outro_scene(
                logo,
                business_name,
                primary,
                secondary,
                accent,
            ),
            OUTRO_DURATION,
            1.02,
            1.00,
            -5,
            -5,
        ),
    ]

    clips = []

    for (
        image,
        duration,
        zoom_start,
        zoom_end,
        pan_x,
        pan_y,
    ) in scenes:
        clip = animated_image_clip(
            pil_image=image,
            duration=duration,
            zoom_start=zoom_start,
            zoom_end=zoom_end,
            pan_x=pan_x,
            pan_y=pan_y,
        )

        clips.append(
            clip
        )

    # -----------------------------------------------------
    # CONCATENATE VIDEO
    # -----------------------------------------------------

    final_video = (
        concatenate_videoclips(
            clips,
            method="compose",
        )
    )

    filename = (
        f"promo-v2-"
        f"{uuid.uuid4()}.mp4"
    )

    output_path = (
        output_directory
        / filename
    )

    print(
        f"[VIDEO V2] Rendering: {output_path}"
    )

    # -----------------------------------------------------
    # EXPORT
    # -----------------------------------------------------

    try:
        final_video.write_videofile(
            str(
                output_path
            ),
            fps=FPS,
            codec="libx264",
            audio=False,
            preset="medium",
            ffmpeg_params=[
                "-pix_fmt",
                "yuv420p",
                "-crf",
                "18",
                "-movflags",
                "+faststart",
            ],
            logger=None,
        )

    finally:
        try:
            final_video.close()
        except Exception:
            pass

        for clip in clips:
            try:
                clip.close()
            except Exception:
                pass

        try:
            logo.close()
        except Exception:
            pass

    if not output_path.exists():
        raise RuntimeError(
            "Video rendering completed but the MP4 file "
            "was not created."
        )

    if output_path.stat().st_size < 1000:
        raise RuntimeError(
            "Generated MP4 appears to be empty."
        )

    print(
        "[VIDEO V2] Video generated successfully."
    )
    print(
        f"[VIDEO V2] Size: "
        f"{output_path.stat().st_size} bytes"
    )

    return output_path