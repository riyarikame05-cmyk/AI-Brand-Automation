import uuid
from pathlib import Path

import numpy as np

from PIL import (
    Image,
    ImageDraw,
    ImageFont,
)

from moviepy import (
    ImageClip,
    concatenate_videoclips,
)


# =========================================================
# VIDEO SETTINGS
# =========================================================

WIDTH = 1080
HEIGHT = 1080
FPS = 30


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
# HEX -> RGB
# =========================================================

def hex_to_rgb(
    value: str,
    fallback=(15, 23, 42),
):

    try:

        value = (
            value
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

            for index
            in (
                0,
                2,
                4,
            )
        )


    except Exception:

        return fallback


# =========================================================
# CONTRAST COLOR
# =========================================================

def text_color_for(
    rgb,
):

    red, green, blue = rgb


    luminance = (
        0.299 * red
        + 0.587 * green
        + 0.114 * blue
    )


    if luminance > 165:

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

    bbox = draw.textbbox(
        (0, 0),
        text,
        font=font,
    )


    return (
        bbox[2]
        - bbox[0]
    )


def draw_centered_text(
    draw,
    text,
    y,
    font,
    fill,
):

    width = text_width(
        draw,
        text,
        font,
    )


    x = (
        WIDTH - width
    ) / 2


    draw.text(
        (
            x,
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
        .split()
    )


    lines = []

    current_line = ""


    for word in words:

        test_line = (
            f"{current_line} {word}"
            .strip()
        )


        width = text_width(
            draw,
            test_line,
            font,
        )


        if width <= max_width:

            current_line = (
                test_line
            )


        else:

            if current_line:

                lines.append(
                    current_line
                )


            current_line = word


    if current_line:

        lines.append(
            current_line
        )


    return lines


def draw_wrapped_center(
    draw,
    text,
    y,
    font,
    fill,
    max_width=850,
    line_height=65,
):

    lines = wrap_text(
        draw,
        text,
        font,
        max_width,
    )


    for line in lines:

        draw_centered_text(
            draw,
            line,
            y,
            font,
            fill,
        )


        y += line_height


# =========================================================
# LOGO LOADER
# =========================================================

def load_logo(
    logo_path: Path,
    max_size=500,
):

    logo = (
        Image.open(
            logo_path
        )
        .convert(
            "RGBA"
        )
    )


    logo.thumbnail(
        (
            max_size,
            max_size,
        ),
        Image.Resampling.LANCZOS,
    )


    return logo


# =========================================================
# LOGO POSITIONING
# =========================================================

def paste_logo(
    image,
    logo,
    center_y,
):

    x = (
        WIDTH
        - logo.width
    ) // 2


    y = (
        center_y
        - logo.height // 2
    )


    image.paste(
        logo,
        (
            x,
            y,
        ),
        logo,
    )


# =========================================================
# SCENE 1
# LOGO REVEAL
# =========================================================

def scene_logo(
    logo,
    primary,
):

    image = Image.new(
        "RGB",
        (
            WIDTH,
            HEIGHT,
        ),
        (
            255,
            255,
            255,
        ),
    )


    draw = ImageDraw.Draw(
        image
    )


    draw.rounded_rectangle(
        (
            WIDTH // 2 - 60,
            110,
            WIDTH // 2 + 60,
            120,
        ),
        radius=5,
        fill=primary,
    )


    paste_logo(
        image,
        logo,
        HEIGHT // 2,
    )


    return image


# =========================================================
# SCENE 2
# COMPANY + SLOGAN
# =========================================================

def scene_slogan(
    business_name,
    slogan,
    primary,
    secondary,
):

    image = Image.new(
        "RGB",
        (
            WIDTH,
            HEIGHT,
        ),
        primary,
    )


    draw = ImageDraw.Draw(
        image
    )


    foreground = (
        text_color_for(
            primary
        )
    )


    company_font = get_font(
        74,
        True,
    )


    slogan_font = get_font(
        38,
        False,
    )


    company_name = (
        business_name
        .strip()
        .upper()
    )


    # Smaller company-name font
    # if the name is very long.
    if len(company_name) > 18:

        company_font = get_font(
            54,
            True,
        )


    draw_centered_text(
        draw,
        company_name,
        350,
        company_font,
        foreground,
    )


    draw.rounded_rectangle(
        (
            WIDTH // 2 - 80,
            465,
            WIDTH // 2 + 80,
            475,
        ),
        radius=5,
        fill=secondary,
    )


    draw_wrapped_center(
        draw,
        slogan,
        535,
        slogan_font,
        foreground,
        max_width=800,
        line_height=55,
    )


    return image


# =========================================================
# SCENE 3
# BRAND PERSONALITY
# =========================================================

def scene_personality(
    personality,
    secondary,
):

    background = (
        15,
        23,
        42,
    )


    image = Image.new(
        "RGB",
        (
            WIDTH,
            HEIGHT,
        ),
        background,
    )


    draw = ImageDraw.Draw(
        image
    )


    heading_font = get_font(
        24,
        True,
    )


    personality_font = get_font(
        48,
        True,
    )


    draw_centered_text(
        draw,
        "OUR BRAND",
        300,
        heading_font,
        secondary,
    )


    if personality:

        text = (
            "  •  ".join(
                personality
            )
            .upper()
        )


    else:

        text = (
            "MODERN • PROFESSIONAL • RELIABLE"
        )


    draw_wrapped_center(
        draw,
        text,
        410,
        personality_font,
        (
            255,
            255,
            255,
        ),
        max_width=880,
        line_height=70,
    )


    return image


# =========================================================
# SCENE 4
# MARKETING MESSAGE
# =========================================================

def scene_marketing(
    marketing_message,
    accent,
):

    background = (
        248,
        250,
        252,
    )


    image = Image.new(
        "RGB",
        (
            WIDTH,
            HEIGHT,
        ),
        background,
    )


    draw = ImageDraw.Draw(
        image
    )


    heading_font = get_font(
        24,
        True,
    )


    message_font = get_font(
        43,
        True,
    )


    draw_centered_text(
        draw,
        "OUR MESSAGE",
        275,
        heading_font,
        accent,
    )


    draw_wrapped_center(
        draw,
        marketing_message,
        380,
        message_font,
        (
            15,
            23,
            42,
        ),
        max_width=850,
        line_height=62,
    )


    return image


# =========================================================
# SCENE 5
# FINAL BRAND
# =========================================================

def scene_outro(
    logo,
    business_name,
    primary,
):

    image = Image.new(
        "RGB",
        (
            WIDTH,
            HEIGHT,
        ),
        (
            255,
            255,
            255,
        ),
    )


    draw = ImageDraw.Draw(
        image
    )


    small_logo = (
        logo.copy()
    )


    small_logo.thumbnail(
        (
            340,
            340,
        ),
        Image.Resampling.LANCZOS,
    )


    paste_logo(
        image,
        small_logo,
        390,
    )


    company_font = get_font(
        55,
        True,
    )


    company_name = (
        business_name
        .strip()
        .upper()
    )


    if len(company_name) > 18:

        company_font = get_font(
            43,
            True,
        )


    draw_centered_text(
        draw,
        company_name,
        650,
        company_font,
        primary,
    )


    tagline_font = get_font(
        24,
        False,
    )


    draw_centered_text(
        draw,
        "Discover the brand.",
        735,
        tagline_font,
        (
            100,
            116,
            139,
        ),
    )


    return image


# =========================================================
# CREATE MOVIEPY CLIP
# MoviePy 2.x uses with_duration()
# =========================================================

def create_clip(
    image,
    duration,
):

    array = np.array(
        image
    )


    clip = ImageClip(
        array
    )


    clip = clip.with_duration(
        duration
    )


    return clip


# =========================================================
# MAIN VIDEO GENERATOR
# =========================================================

def generate_promotional_video(
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

    if personality is None:

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


    output_directory = Path(
        output_directory
    )


    output_directory.mkdir(
        parents=True,
        exist_ok=True,
    )


    primary = hex_to_rgb(
        primary_color
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


    logo = load_logo(
        Path(
            logo_path
        ),
        max_size=500,
    )


    # =====================================================
    # GENERATE SCENES
    # =====================================================

    image1 = scene_logo(
        logo,
        primary,
    )


    image2 = scene_slogan(
        business_name,
        slogan,
        primary,
        secondary,
    )


    image3 = scene_personality(
        personality,
        secondary,
    )


    image4 = scene_marketing(
        marketing_message,
        accent,
    )


    image5 = scene_outro(
        logo,
        business_name,
        primary,
    )


    # =====================================================
    # CLIPS
    # =====================================================

    clips = [
        create_clip(
            image1,
            2.0,
        ),

        create_clip(
            image2,
            3.0,
        ),

        create_clip(
            image3,
            3.0,
        ),

        create_clip(
            image4,
            3.0,
        ),

        create_clip(
            image5,
            2.0,
        ),
    ]


    # =====================================================
    # COMBINE
    # =====================================================

    final_video = (
        concatenate_videoclips(
            clips,
            method="compose",
        )
    )


    filename = (
        f"promo-"
        f"{uuid.uuid4()}.mp4"
    )


    output_path = (
        output_directory
        / filename
    )


    # =====================================================
    # EXPORT
    # =====================================================

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
            ],
            logger=None,
        )


    finally:

        final_video.close()


        for clip in clips:

            try:
                clip.close()

            except Exception:
                pass


    return output_path