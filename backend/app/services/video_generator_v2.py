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
    ImageClip,
    VideoClip,
    concatenate_videoclips,
)


# =========================================================
# SETTINGS
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
# COLOR
# =========================================================

def hex_to_rgb(
    value,
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

    return tuple(
        int(
            color_a[index]
            * (1 - amount)
            + color_b[index]
            * amount
        )

        for index in range(3)
    )


def contrast_color(
    color,
):

    luminance = (
        0.299 * color[0]
        + 0.587 * color[1]
        + 0.114 * color[2]
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
# TEXT
# =========================================================

def text_width(
    draw,
    text,
    font,
):

    box = draw.textbbox(
        (0, 0),
        text,
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
        str(
            text or ""
        )
        .split()
    )


    lines = []

    current = ""


    for word in words:

        candidate = (
            f"{current} {word}"
            .strip()
        )


        if (
            text_width(
                draw,
                candidate,
                font,
            )
            <= max_width
        ):

            current = candidate


        else:

            if current:

                lines.append(
                    current
                )


            current = word


    if current:

        lines.append(
            current
        )


    return lines


def draw_wrapped(
    draw,
    text,
    y,
    font,
    fill,
    max_width=780,
    line_height=65,
):

    lines = wrap_text(
        draw,
        text,
        font,
        max_width,
    )


    for line in lines:

        draw_centered(
            draw,
            line,
            y,
            font,
            fill,
        )


        y += line_height


# =========================================================
# BACKGROUND
# =========================================================

def gradient_background(
    start,
    end,
):

    image = Image.new(
        "RGB",
        (
            WIDTH,
            HEIGHT,
        ),
    )


    pixels = image.load()


    for y in range(
        HEIGHT
    ):

        amount = (
            y
            / max(
                1,
                HEIGHT - 1,
            )
        )


        color = mix(
            start,
            end,
            amount,
        )


        for x in range(
            WIDTH
        ):

            pixels[
                x,
                y,
            ] = color


    return image


# =========================================================
# DECORATIVE BRAND ELEMENTS
# =========================================================

def add_brand_shapes(
    image,
    primary,
    secondary,
    accent,
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


    draw.ellipse(
        (
            -170,
            -120,
            340,
            390,
        ),
        fill=(
            secondary[0],
            secondary[1],
            secondary[2],
            45,
        ),
    )


    draw.ellipse(
        (
            780,
            720,
            1250,
            1190,
        ),
        fill=(
            accent[0],
            accent[1],
            accent[2],
            50,
        ),
    )


    draw.rounded_rectangle(
        (
            830,
            80,
            1000,
            95,
        ),
        radius=8,
        fill=(
            accent[0],
            accent[1],
            accent[2],
            160,
        ),
    )


    overlay = (
        overlay.filter(
            ImageFilter.GaussianBlur(
                5
            )
        )
    )


    return Image.alpha_composite(
        image.convert(
            "RGBA"
        ),
        overlay,
    ).convert(
        "RGB"
    )


# =========================================================
# LOGO
# =========================================================

def load_logo(
    logo_path,
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
            420,
            420,
        ),
        Image.Resampling.LANCZOS,
    )


    return logo


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
# SCENE 1 — BRAND REVEAL
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
            3,
            7,
            18,
        ),
        0.55,
    )


    image = gradient_background(
        dark,
        primary,
    )


    image = add_brand_shapes(
        image,
        primary,
        secondary,
        accent,
    )


    paste_logo(
        image,
        logo,
        500,
    )


    return image


# =========================================================
# SCENE 2 — BRAND STATEMENT
# =========================================================

def create_statement_scene(
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
        0.4,
    )


    image = gradient_background(
        primary,
        dark,
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


    foreground = contrast_color(
        dark
    )


    small = get_font(
        25,
        False,
    )


    title = get_font(
        (
            70
            if len(
                business_name
            ) <= 18
            else 52
        ),
        True,
    )


    slogan_font = get_font(
        38,
        False,
    )


    draw_centered(
        draw,
        "INTRODUCING",
        275,
        small,
        accent,
    )


    draw_centered(
        draw,
        business_name.upper(),
        360,
        title,
        foreground,
    )


    draw.rounded_rectangle(
        (
            450,
            475,
            630,
            483,
        ),
        radius=4,
        fill=accent,
    )


    draw_wrapped(
        draw,
        slogan,
        550,
        slogan_font,
        foreground,
        max_width=780,
        line_height=55,
    )


    return image


# =========================================================
# SCENE 3 — PERSONALITY
# =========================================================

def create_personality_scene(
    personality,
    primary,
    secondary,
    accent,
):

    image = gradient_background(
        (
            248,
            250,
            252,
        ),
        (
            232,
            238,
            247,
        ),
    )


    draw = ImageDraw.Draw(
        image
    )


    label_font = get_font(
        24,
        True,
    )


    main_font = get_font(
        52,
        True,
    )


    draw_centered(
        draw,
        "BRAND CHARACTER",
        245,
        label_font,
        secondary,
    )


    words = (
        personality[:3]
        if personality
        else [
            "Modern",
            "Professional",
            "Reliable",
        ]
    )


    y = 365


    colors = [
        primary,
        secondary,
        accent,
    ]


    for index, word in enumerate(
        words
    ):

        draw_centered(
            draw,
            str(
                word
            ).upper(),
            y,
            main_font,
            colors[
                index
                % len(colors)
            ],
        )


        y += 120


    return image


# =========================================================
# SCENE 4 — MARKETING MESSAGE
# =========================================================

def create_message_scene(
    marketing_message,
    primary,
    secondary,
    accent,
):

    dark = (
        8,
        15,
        30,
    )


    image = gradient_background(
        dark,
        mix(
            primary,
            dark,
            0.55,
        ),
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


    label = get_font(
        23,
        True,
    )


    message = get_font(
        45,
        True,
    )


    draw_centered(
        draw,
        "OUR PURPOSE",
        270,
        label,
        accent,
    )


    draw_wrapped(
        draw,
        marketing_message,
        390,
        message,
        (
            255,
            255,
            255,
        ),
        max_width=820,
        line_height=67,
    )


    return image


# =========================================================
# SCENE 5 — OUTRO
# =========================================================

def create_outro_scene(
    logo,
    business_name,
    primary,
    secondary,
    accent,
):

    image = gradient_background(
        (
            255,
            255,
            255,
        ),
        (
            240,
            244,
            250,
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
            320,
            320,
        ),
        Image.Resampling.LANCZOS,
    )


    paste_logo(
        image,
        small_logo,
        380,
    )


    name_font = get_font(
        (
            55
            if len(
                business_name
            ) <= 18
            else 43
        ),
        True,
    )


    draw_centered(
        draw,
        business_name.upper(),
        610,
        name_font,
        primary,
    )


    draw.rounded_rectangle(
        (
            485,
            710,
            595,
            718,
        ),
        radius=4,
        fill=accent,
    )


    tagline = get_font(
        27,
        False,
    )


    draw_centered(
        draw,
        "BUILT FOR WHAT COMES NEXT.",
        770,
        tagline,
        (
            71,
            85,
            105,
        ),
    )


    return image


# =========================================================
# MOTION
# =========================================================

def animated_image_clip(
    pil_image,
    duration,
    zoom_start=1.0,
    zoom_end=1.04,
):

    base = (
        pil_image
        .convert(
            "RGB"
        )
    )


    def frame_function(t):

        progress = (
            t
            / duration
            if duration
            else 0
        )


        scale = (
            zoom_start
            + (
                zoom_end
                - zoom_start
            )
            * progress
        )


        new_width = int(
            WIDTH * scale
        )


        new_height = int(
            HEIGHT * scale
        )


        frame = base.resize(
            (
                new_width,
                new_height,
            ),
            Image.Resampling.LANCZOS,
        )


        left = (
            new_width
            - WIDTH
        ) // 2


        top = (
            new_height
            - HEIGHT
        ) // 2


        frame = frame.crop(
            (
                left,
                top,
                left + WIDTH,
                top + HEIGHT,
            )
        )


        return np.array(
            frame
        )


    return (
        VideoClip(
            frame_function,
            duration=duration,
        )
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
        )
    )


    # -----------------------------------------------------
    # BUILD SCENES
    # -----------------------------------------------------

    scenes = [

        (
            create_intro_scene(
                logo,
                primary,
                secondary,
                accent,
            ),
            2.5,
            1.00,
            1.06,
        ),

        (
            create_statement_scene(
                business_name,
                slogan,
                primary,
                secondary,
                accent,
            ),
            3.0,
            1.03,
            1.00,
        ),

        (
            create_personality_scene(
                personality,
                primary,
                secondary,
                accent,
            ),
            3.0,
            1.00,
            1.035,
        ),

        (
            create_message_scene(
                marketing_message,
                primary,
                secondary,
                accent,
            ),
            3.5,
            1.035,
            1.00,
        ),

        (
            create_outro_scene(
                logo,
                business_name,
                primary,
                secondary,
                accent,
            ),
            2.5,
            1.00,
            1.04,
        ),
    ]


    clips = []


    for (
        image,
        duration,
        zoom_start,
        zoom_end,
    ) in scenes:

        clip = animated_image_clip(
            image,
            duration,
            zoom_start,
            zoom_end,
        )


        clips.append(
            clip
        )


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

                # Good quality without making
                # the file unnecessarily huge.
                "-crf",
                "18",
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