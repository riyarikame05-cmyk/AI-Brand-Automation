from __future__ import annotations

import html
import math
import random
from io import BytesIO

from PIL import (
    Image,
    ImageChops,
    ImageDraw,
    ImageEnhance,
    ImageFont,
    ImageOps,
)


WIDTH = 1200
HEIGHT = 1200
BACKGROUND = "#FFFFFF"


# =========================================================
# FONTS
# =========================================================

def get_font(
    size: int,
    style: str = "modern",
):
    fonts = {
        "modern": [
            "C:/Windows/Fonts/segoeuib.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        ],
        "bold": [
            "C:/Windows/Fonts/arialbd.ttf",
            "C:/Windows/Fonts/segoeuib.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        ],
        "elegant": [
            "C:/Windows/Fonts/georgiab.ttf",
            "C:/Windows/Fonts/timesbd.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
        ],
        "minimal": [
            "C:/Windows/Fonts/segoeui.ttf",
            "C:/Windows/Fonts/arial.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ],
    }

    paths = fonts.get(
        str(style).lower(),
        fonts["modern"],
    )

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

def safe_color(
    specification,
    key,
    fallback,
):
    value = str(
        specification.get(
            key,
            fallback,
        )
    ).strip()

    if (
        len(value) == 7
        and value.startswith("#")
    ):
        try:
            int(
                value[1:],
                16,
            )

            return value.upper()

        except ValueError:
            pass

    return fallback


# =========================================================
# GEOMETRY
# =========================================================

def polygon_points(
    cx,
    cy,
    radius,
    sides,
    rotation=0,
):
    points = []

    for index in range(sides):
        angle = math.radians(
            rotation
            - 90
            + index
            * (
                360 / sides
            )
        )

        points.append(
            (
                cx
                + radius
                * math.cos(
                    angle
                ),
                cy
                + radius
                * math.sin(
                    angle
                ),
            )
        )

    return points


def svg_points(
    points,
):
    return " ".join(
        f"{round(x, 2)},{round(y, 2)}"
        for x, y in points
    )


def initials(
    business_name,
):
    words = [
        word
        for word in str(
            business_name
        )
        .strip()
        .split()
        if word
    ]

    if not words:
        return "B"

    if len(words) == 1:
        return (
            words[0][:2]
            .upper()
        )

    return (
        words[0][0]
        + words[-1][0]
    ).upper()


# =========================================================
# TEXT HELPERS
# =========================================================

def text_size(
    draw,
    text,
    font,
):
    bbox = draw.textbbox(
        (
            0,
            0,
        ),
        str(text),
        font=font,
    )

    return (
        bbox[2] - bbox[0],
        bbox[3] - bbox[1],
    )


def draw_centered_text(
    draw,
    text,
    x,
    y,
    font,
    fill,
):
    text = str(
        text
    )

    width, _ = text_size(
        draw,
        text,
        font,
    )

    draw.text(
        (
            x
            - width / 2,
            y,
        ),
        text,
        font=font,
        fill=fill,
    )


def fit_name_font(
    draw,
    business_name,
    style,
    maximum_width=900,
):
    name = (
        str(
            business_name
        )
        .strip()
        .upper()
    )

    if len(name) <= 10:
        size = 90

    elif len(name) <= 16:
        size = 76

    elif len(name) <= 22:
        size = 62

    else:
        size = 50

    while size >= 36:
        font = get_font(
            size,
            style,
        )

        width, _ = text_size(
            draw,
            name,
            font,
        )

        if width <= maximum_width:
            return font

        size -= 2

    return get_font(
        36,
        style,
    )


# =========================================================
# RANDOM LOCAL DESIGN PARAMETERS
# =========================================================

def build_parameters(
    specification,
):
    return {
        "rotation":
        specification.get(
            "rotation",
            random.randint(
                0,
                180,
            ),
        ),

        "layers":
        specification.get(
            "layers",
            random.randint(
                2,
                5,
            ),
        ),

        "stroke":
        specification.get(
            "stroke_width",
            random.randint(
                12,
                30,
            ),
        ),

        "offset":
        random.randint(
            25,
            80,
        ),

        "scale":
        random.uniform(
            0.75,
            1.15,
        ),

        "curve":
        random.randint(
            45,
            140,
        ),

        "secondary_rotation":
        random.randint(
            15,
            90,
        ),
    }


# =========================================================
# SVG SYMBOL — LOCAL FALLBACK
# =========================================================

def render_svg_symbol(
    specification,
    business_name,
    parameters,
):
    logo_type = specification[
        "logo_type"
    ]

    shape = specification[
        "shape"
    ]

    primary = safe_color(
        specification,
        "primary_color",
        "#111827",
    )

    secondary = safe_color(
        specification,
        "secondary_color",
        "#4F46E5",
    )

    accent = safe_color(
        specification,
        "accent_color",
        "#06B6D4",
    )

    rotation = parameters[
        "rotation"
    ]

    stroke = parameters[
        "stroke"
    ]

    cx = 600
    cy = 395

    elements = []

    # -----------------------------------------------------
    # MONOGRAM / LETTERMARK
    # -----------------------------------------------------

    if logo_type in [
        "monogram",
        "lettermark",
    ]:
        text = html.escape(
            initials(
                business_name
            )
        )

        if shape in [
            "circle",
            "rings",
        ]:
            elements.append(
                f"""
                <circle
                    cx="{cx}"
                    cy="{cy}"
                    r="190"
                    fill="none"
                    stroke="{primary}"
                    stroke-width="{stroke}"
                />
                """
            )

        else:
            sides = {
                "triangle": 3,
                "square": 4,
                "diamond": 4,
                "hexagon": 6,
            }.get(
                shape,
                6,
            )

            points = polygon_points(
                cx,
                cy,
                190,
                sides,
                rotation,
            )

            elements.append(
                f"""
                <polygon
                    points="{svg_points(points)}"
                    fill="none"
                    stroke="{primary}"
                    stroke-width="{stroke}"
                    stroke-linejoin="round"
                />
                """
            )

        elements.append(
            f"""
            <text
                x="{cx}"
                y="{cy + 45}"
                text-anchor="middle"
                font-family="Arial, sans-serif"
                font-size="145"
                font-weight="700"
                fill="{accent}"
            >{text}</text>
            """
        )

    # -----------------------------------------------------
    # ABSTRACT / COMBINATION
    # -----------------------------------------------------

    elif logo_type in [
        "abstract",
        "combination",
    ]:
        layers = max(
            1,
            int(
                parameters[
                    "layers"
                ]
            ),
        )

        colors = [
            primary,
            secondary,
            accent,
        ]

        for index in range(
            layers
        ):
            radius = max(
                45,
                190
                - index * 30,
            )

            sides = [
                3,
                4,
                5,
                6,
            ][index % 4]

            x = (
                cx
                + (
                    index
                    - layers / 2
                )
                * parameters[
                    "offset"
                ]
                * 0.45
            )

            points = polygon_points(
                x,
                cy,
                radius,
                sides,
                rotation
                + index
                * parameters[
                    "secondary_rotation"
                ],
            )

            color = colors[
                index % 3
            ]

            opacity = max(
                0.35,
                0.92
                - index * 0.10,
            )

            elements.append(
                f"""
                <polygon
                    points="{svg_points(points)}"
                    fill="{color}"
                    fill-opacity="{opacity}"
                />
                """
            )

    # -----------------------------------------------------
    # NEGATIVE SPACE
    # -----------------------------------------------------

    elif logo_type == "negative-space":
        points = polygon_points(
            cx,
            cy,
            215,
            6,
            rotation,
        )

        cutout = polygon_points(
            cx + 25,
            cy,
            110,
            3,
            rotation + 30,
        )

        elements.append(
            f"""
            <polygon
                points="{svg_points(points)}"
                fill="{primary}"
            />
            """
        )

        elements.append(
            f"""
            <polygon
                points="{svg_points(cutout)}"
                fill="{BACKGROUND}"
            />
            """
        )

        elements.append(
            f"""
            <circle
                cx="{cx}"
                cy="{cy}"
                r="34"
                fill="{accent}"
            />
            """
        )

    # -----------------------------------------------------
    # EMBLEM
    # -----------------------------------------------------

    elif logo_type == "emblem":
        text = html.escape(
            initials(
                business_name
            )
        )

        elements.append(
            f"""
            <circle
                cx="{cx}"
                cy="{cy}"
                r="220"
                fill="{primary}"
            />

            <circle
                cx="{cx}"
                cy="{cy}"
                r="170"
                fill="none"
                stroke="{accent}"
                stroke-width="{stroke}"
            />

            <text
                x="{cx}"
                y="{cy + 42}"
                text-anchor="middle"
                font-family="Arial, sans-serif"
                font-size="130"
                font-weight="700"
                fill="#FFFFFF"
            >{text}</text>
            """
        )

    # -----------------------------------------------------
    # GEOMETRIC
    # -----------------------------------------------------

    else:
        outer = polygon_points(
            cx,
            cy,
            215,
            6,
            rotation,
        )

        inner = polygon_points(
            cx,
            cy,
            120,
            3,
            rotation
            + parameters[
                "secondary_rotation"
            ],
        )

        elements.append(
            f"""
            <polygon
                points="{svg_points(outer)}"
                fill="none"
                stroke="{primary}"
                stroke-width="{stroke}"
                stroke-linejoin="round"
            />

            <polygon
                points="{svg_points(inner)}"
                fill="{secondary}"
            />

            <circle
                cx="{cx}"
                cy="{cy}"
                r="32"
                fill="{accent}"
            />
            """
        )

    return "\n".join(
        elements
    )


# =========================================================
# COMPLETE SVG — LOCAL FALLBACK
# =========================================================

def render_svg(
    business_name,
    industry,
    specification,
    parameters,
):
    symbol = render_svg_symbol(
        specification,
        business_name,
        parameters,
    )

    safe_name = html.escape(
        str(
            business_name
        )
        .strip()
        .upper()
    )

    safe_industry = html.escape(
        str(
            industry
        )
        .replace(
            "_",
            " ",
        )
        .replace(
            "-",
            " ",
        )
        .upper()
    )

    primary = safe_color(
        specification,
        "primary_color",
        "#111827",
    )

    secondary = safe_color(
        specification,
        "secondary_color",
        "#4F46E5",
    )

    return f"""
<svg
    xmlns="http://www.w3.org/2000/svg"
    width="{WIDTH}"
    height="{HEIGHT}"
    viewBox="0 0 {WIDTH} {HEIGHT}"
>
    <rect
        width="{WIDTH}"
        height="{HEIGHT}"
        fill="{BACKGROUND}"
    />

    {symbol}

    <text
        x="600"
        y="770"
        text-anchor="middle"
        font-family="Arial, sans-serif"
        font-size="82"
        font-weight="700"
        fill="{primary}"
    >{safe_name}</text>

    <rect
        x="530"
        y="825"
        width="140"
        height="8"
        rx="4"
        fill="{secondary}"
    />

    <text
        x="600"
        y="895"
        text-anchor="middle"
        font-family="Arial, sans-serif"
        font-size="28"
        letter-spacing="4"
        fill="{secondary}"
    >{safe_industry}</text>
</svg>
""".strip()


# =========================================================
# PNG SYMBOL — LOCAL FALLBACK
# =========================================================

def render_png_symbol(
    draw,
    specification,
    business_name,
    parameters,
):
    logo_type = specification[
        "logo_type"
    ]

    shape = specification.get(
        "shape",
        "hexagon",
    )

    primary = safe_color(
        specification,
        "primary_color",
        "#111827",
    )

    secondary = safe_color(
        specification,
        "secondary_color",
        "#4F46E5",
    )

    accent = safe_color(
        specification,
        "accent_color",
        "#06B6D4",
    )

    rotation = parameters[
        "rotation"
    ]

    stroke = max(
        4,
        int(
            parameters[
                "stroke"
            ]
        ),
    )

    cx = 600
    cy = 395

    # -----------------------------------------------------
    # MONOGRAM / LETTERMARK
    # -----------------------------------------------------

    if logo_type in [
        "monogram",
        "lettermark",
    ]:
        if shape in [
            "circle",
            "rings",
        ]:
            draw.ellipse(
                (
                    cx - 190,
                    cy - 190,
                    cx + 190,
                    cy + 190,
                ),
                outline=primary,
                width=stroke,
            )

        else:
            sides = {
                "triangle": 3,
                "square": 4,
                "diamond": 4,
                "hexagon": 6,
            }.get(
                shape,
                6,
            )

            points = polygon_points(
                cx,
                cy,
                190,
                sides,
                rotation,
            )

            draw.line(
                points
                + [points[0]],
                fill=primary,
                width=stroke,
                joint="curve",
            )

        font = get_font(
            140,
            specification.get(
                "font_style",
                "modern",
            ),
        )

        draw_centered_text(
            draw,
            initials(
                business_name
            ),
            cx,
            cy - 85,
            font,
            accent,
        )

    # -----------------------------------------------------
    # ABSTRACT / COMBINATION
    # -----------------------------------------------------

    elif logo_type in [
        "abstract",
        "combination",
    ]:
        colors = [
            primary,
            secondary,
            accent,
        ]

        layers = max(
            1,
            int(
                parameters[
                    "layers"
                ]
            ),
        )

        for index in range(
            layers
        ):
            points = polygon_points(
                cx
                + (
                    index
                    - 1
                )
                * 30,
                cy,
                max(
                    45,
                    190
                    - index
                    * 30,
                ),
                [
                    3,
                    4,
                    5,
                    6,
                ][index % 4],
                rotation
                + index * 35,
            )

            draw.polygon(
                points,
                fill=colors[
                    index % 3
                ],
            )

    # -----------------------------------------------------
    # NEGATIVE SPACE
    # -----------------------------------------------------

    elif logo_type == "negative-space":
        outer = polygon_points(
            cx,
            cy,
            215,
            6,
            rotation,
        )

        draw.polygon(
            outer,
            fill=primary,
        )

        cut = polygon_points(
            cx + 25,
            cy,
            110,
            3,
            rotation + 30,
        )

        draw.polygon(
            cut,
            fill=BACKGROUND,
        )

        draw.ellipse(
            (
                cx - 34,
                cy - 34,
                cx + 34,
                cy + 34,
            ),
            fill=accent,
        )

    # -----------------------------------------------------
    # EMBLEM
    # -----------------------------------------------------

    elif logo_type == "emblem":
        draw.ellipse(
            (
                cx - 220,
                cy - 220,
                cx + 220,
                cy + 220,
            ),
            fill=primary,
        )

        draw.ellipse(
            (
                cx - 170,
                cy - 170,
                cx + 170,
                cy + 170,
            ),
            outline=accent,
            width=stroke,
        )

        font = get_font(
            125,
            "bold",
        )

        draw_centered_text(
            draw,
            initials(
                business_name
            ),
            cx,
            cy - 75,
            font,
            "#FFFFFF",
        )

    # -----------------------------------------------------
    # GEOMETRIC
    # -----------------------------------------------------

    else:
        outer = polygon_points(
            cx,
            cy,
            215,
            6,
            rotation,
        )

        draw.line(
            outer
            + [outer[0]],
            fill=primary,
            width=stroke,
            joint="curve",
        )

        inner = polygon_points(
            cx,
            cy,
            115,
            3,
            rotation + 35,
        )

        draw.polygon(
            inner,
            fill=secondary,
        )

        draw.ellipse(
            (
                cx - 32,
                cy - 32,
                cx + 32,
                cy + 32,
            ),
            fill=accent,
        )


# =========================================================
# COMMON BRAND TYPOGRAPHY
# =========================================================

def draw_brand_typography(
    image,
    business_name,
    industry,
    specification,
):
    draw = ImageDraw.Draw(
        image
    )

    primary = safe_color(
        specification,
        "primary_color",
        "#111827",
    )

    secondary = safe_color(
        specification,
        "secondary_color",
        "#4F46E5",
    )

    accent = safe_color(
        specification,
        "accent_color",
        "#06B6D4",
    )

    style = specification.get(
        "font_style",
        "modern",
    )

    name = (
        str(
            business_name
        )
        .strip()
        .upper()
    )

    industry_text = (
        str(
            industry
        )
        .replace(
            "_",
            " ",
        )
        .replace(
            "-",
            " ",
        )
        .strip()
        .upper()
    )

    name_font = fit_name_font(
        draw,
        name,
        style,
        maximum_width=900,
    )

    industry_font = get_font(
        27,
        "minimal",
    )

    # Company name
    draw_centered_text(
        draw,
        name,
        WIDTH // 2,
        760,
        name_font,
        primary,
    )

    # Brand accent divider
    divider_width = 150

    draw.rounded_rectangle(
        (
            WIDTH // 2
            - divider_width // 2,
            866,
            WIDTH // 2
            + divider_width // 2,
            876,
        ),
        radius=5,
        fill=accent,
    )

    # Industry
    draw_centered_text(
        draw,
        industry_text,
        WIDTH // 2,
        915,
        industry_font,
        secondary,
    )


# =========================================================
# COMPLETE PNG — LOCAL FALLBACK
# =========================================================

def render_png(
    business_name,
    industry,
    specification,
    parameters,
):
    image = Image.new(
        "RGB",
        (
            WIDTH,
            HEIGHT,
        ),
        BACKGROUND,
    )

    draw = ImageDraw.Draw(
        image
    )

    render_png_symbol(
        draw,
        specification,
        business_name,
        parameters,
    )

    draw_brand_typography(
        image,
        business_name,
        industry,
        specification,
    )

    output = BytesIO()

    image.save(
        output,
        format="PNG",
        optimize=True,
    )

    output.seek(
        0
    )

    return output.getvalue()


# =========================================================
# CLOUD IMAGE PREPARATION
# =========================================================

def _trim_near_white_edges(
    image,
    threshold=246,
):
    """
    Attempt to remove large near-white margins around
    cloud-generated artwork.

    This does not perform full AI background removal.
    It simply detects non-white visual content.
    """

    rgb = image.convert(
        "RGB"
    )

    pixels = rgb.load()

    min_x = rgb.width
    min_y = rgb.height
    max_x = -1
    max_y = -1

    for y in range(
        rgb.height
    ):
        for x in range(
            rgb.width
        ):
            r, g, b = pixels[
                x,
                y,
            ]

            if (
                r < threshold
                or g < threshold
                or b < threshold
            ):
                min_x = min(
                    min_x,
                    x,
                )

                min_y = min(
                    min_y,
                    y,
                )

                max_x = max(
                    max_x,
                    x,
                )

                max_y = max(
                    max_y,
                    y,
                )

    if (
        max_x < min_x
        or max_y < min_y
    ):
        return rgb

    # Add some safe breathing room.
    padding_x = max(
        20,
        int(
            (
                max_x - min_x
            )
            * 0.08
        ),
    )

    padding_y = max(
        20,
        int(
            (
                max_y - min_y
            )
            * 0.08
        ),
    )

    left = max(
        0,
        min_x - padding_x,
    )

    top = max(
        0,
        min_y - padding_y,
    )

    right = min(
        rgb.width,
        max_x
        + padding_x
        + 1,
    )

    bottom = min(
        rgb.height,
        max_y
        + padding_y
        + 1,
    )

    return rgb.crop(
        (
            left,
            top,
            right,
            bottom,
        )
    )


def _prepare_cloud_symbol(
    cloud_image_bytes,
):
    """
    Convert the provider image into a symbol panel suitable
    for deterministic composition.
    """

    if not isinstance(
        cloud_image_bytes,
        (
            bytes,
            bytearray,
        ),
    ):
        raise RuntimeError(
            "Cloud image must be binary image data."
        )

    source = Image.open(
        BytesIO(
            cloud_image_bytes
        )
    )

    source.load()

    source = ImageOps.exif_transpose(
        source
    )

    source = source.convert(
        "RGB"
    )

    # Remove excessive white border where possible.
    source = _trim_near_white_edges(
        source
    )

    # Slight contrast improvement. Keep it conservative
    # because we do not want to destroy cloud artwork.
    source = ImageEnhance.Contrast(
        source
    ).enhance(
        1.04
    )

    return source


# =========================================================
# CLOUD + DETERMINISTIC COMPOSITOR
# =========================================================

def compose_cloud_logo(
    cloud_image_bytes: bytes,
    business_name: str,
    industry: str,
    specification: dict,
) -> bytes:
    """
    Turn a cloud-generated symbol/image into a finished
    brand logo with exact deterministic typography.

    The cloud provider controls the creative visual.
    This compositor controls:
        - final canvas
        - company-name spelling
        - typography
        - industry label
        - spacing
        - consistent dimensions
    """

    print(
        "[LOGO RENDERER] Composing cloud artwork "
        "with deterministic typography."
    )

    symbol = _prepare_cloud_symbol(
        cloud_image_bytes
    )

    # -----------------------------------------------------
    # SYMBOL PRESENTATION AREA
    # -----------------------------------------------------

    # Keep the cloud artwork above the typography.
    max_symbol_width = 620
    max_symbol_height = 620

    symbol.thumbnail(
        (
            max_symbol_width,
            max_symbol_height,
        ),
        Image.Resampling.LANCZOS,
    )

    canvas = Image.new(
        "RGB",
        (
            WIDTH,
            HEIGHT,
        ),
        BACKGROUND,
    )

    # Center artwork in upper presentation region.
    symbol_center_x = (
        WIDTH // 2
    )

    symbol_center_y = 375

    x = int(
        symbol_center_x
        - symbol.width / 2
    )

    y = int(
        symbol_center_y
        - symbol.height / 2
    )

    canvas.paste(
        symbol,
        (
            x,
            y,
        ),
    )

    # -----------------------------------------------------
    # TYPOGRAPHY
    # -----------------------------------------------------

    draw_brand_typography(
        canvas,
        business_name,
        industry,
        specification,
    )

    # -----------------------------------------------------
    # EXPORT
    # -----------------------------------------------------

    output = BytesIO()

    canvas.save(
        output,
        format="PNG",
        optimize=True,
    )

    output.seek(
        0
    )

    result = output.getvalue()

    if len(result) < 1000:
        raise RuntimeError(
            "Cloud logo compositor produced invalid PNG data."
        )

    return result


# =========================================================
# PUBLIC LOCAL RENDERER
# =========================================================

def render_logo(
    business_name,
    industry,
    specification,
):
    """
    Fully deterministic/local logo renderer.

    Used as the final offline fallback.
    """

    parameters = build_parameters(
        specification
    )

    svg = render_svg(
        business_name,
        industry,
        specification,
        parameters,
    )

    png = render_png(
        business_name,
        industry,
        specification,
        parameters,
    )

    return {
        "svg": svg,
        "png": png,
        "parameters": parameters,
    }