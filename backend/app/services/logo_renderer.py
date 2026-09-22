from __future__ import annotations

import html
import math
import random
from io import BytesIO

from PIL import Image, ImageDraw, ImageEnhance, ImageFont, ImageOps


WIDTH = 1200
HEIGHT = 1200
BACKGROUND = "#FFFFFF"

SYMBOL_X = 600
SYMBOL_Y = 385


# =========================================================
# FONTS
# =========================================================

def get_font(size: int, style: str = "modern"):
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

    for path in fonts.get(str(style).lower(), fonts["modern"]):
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue

    return ImageFont.load_default()


# =========================================================
# HELPERS
# =========================================================

def safe_color(specification, key, fallback):
    value = str(specification.get(key, fallback)).strip()

    if len(value) == 7 and value.startswith("#"):
        try:
            int(value[1:], 16)
            return value.upper()
        except ValueError:
            pass

    return fallback


def initials(business_name):
    words = [
        w for w in str(business_name).strip().split()
        if w
    ]

    if not words:
        return "B"

    if len(words) == 1:
        return words[0][:2].upper()

    return (words[0][0] + words[-1][0]).upper()


def polygon_points(cx, cy, radius, sides, rotation=0):
    result = []

    for index in range(sides):
        angle = math.radians(
            rotation - 90 + index * (360 / sides)
        )

        result.append(
            (
                cx + radius * math.cos(angle),
                cy + radius * math.sin(angle),
            )
        )

    return result


def svg_points(points):
    return " ".join(
        f"{x:.2f},{y:.2f}"
        for x, y in points
    )


def text_size(draw, text, font):
    box = draw.textbbox((0, 0), str(text), font=font)

    return (
        box[2] - box[0],
        box[3] - box[1],
    )


def draw_centered_text(draw, text, x, y, font, fill):
    width, height = text_size(draw, text, font)

    draw.text(
        (
            x - width / 2,
            y - height / 2,
        ),
        str(text),
        font=font,
        fill=fill,
    )


def fit_name_font(
    draw,
    business_name,
    style,
    maximum_width=900,
    start_size=82,
):
    name = str(business_name).strip().upper()

    size = start_size

    while size >= 34:
        font = get_font(size, style)

        width, _ = text_size(
            draw,
            name,
            font,
        )

        if width <= maximum_width:
            return font

        size -= 2

    return get_font(34, style)


def build_parameters(specification):
    return {
        "rotation": int(specification.get("rotation", 0)),
        "layers": int(specification.get("layers", 2)),
        "stroke": int(specification.get("stroke_width", 18)),
        "offset": random.randint(34, 64),
        "secondary_rotation": random.randint(18, 55),
    }


# =========================================================
# SVG SYMBOLS
# =========================================================

def render_svg_symbol(
    specification,
    business_name,
    parameters,
):
    logo_type = specification.get("logo_type", "geometric")
    shape = specification.get("shape", "circle")

    primary = safe_color(
        specification,
        "primary_color",
        "#172554",
    )

    secondary = safe_color(
        specification,
        "secondary_color",
        "#2563EB",
    )

    accent = safe_color(
        specification,
        "accent_color",
        "#38BDF8",
    )

    cx = SYMBOL_X
    cy = SYMBOL_Y

    rotation = parameters["rotation"]
    stroke = max(10, parameters["stroke"])

    mark_initials = html.escape(initials(business_name))

    # -----------------------------------------------------
    # WORDMARK
    # -----------------------------------------------------

    if logo_type == "wordmark":
        return f"""
        <g>
            <text
                x="{cx}"
                y="{cy + 25}"
                text-anchor="middle"
                font-family="Arial, sans-serif"
                font-size="145"
                font-weight="700"
                letter-spacing="2"
                fill="{primary}"
            >{html.escape(str(business_name).upper())}</text>

            <rect
                x="{cx - 115}"
                y="{cy + 78}"
                width="230"
                height="13"
                rx="6"
                fill="{accent}"
            />
        </g>
        """

    # -----------------------------------------------------
    # MONOGRAM / LETTERMARK
    # -----------------------------------------------------

    if logo_type in {"monogram", "lettermark"}:
        font_size = 190 if len(mark_initials) == 1 else 160

        if shape in {"circle", "rings"}:
            frame = f"""
                <circle
                    cx="{cx}"
                    cy="{cy}"
                    r="205"
                    fill="{primary}"
                />

                <circle
                    cx="{cx}"
                    cy="{cy}"
                    r="166"
                    fill="none"
                    stroke="{secondary}"
                    stroke-width="10"
                />
            """
        elif shape == "lines":
            frame = f"""
                <path
                    d="M {cx - 210} {cy + 130}
                       L {cx - 105} {cy - 170}
                       L {cx} {cy + 80}
                       L {cx + 105} {cy - 170}
                       L {cx + 210} {cy + 130}"
                    fill="none"
                    stroke="{primary}"
                    stroke-width="{stroke}"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                />
            """
        else:
            sides = {
                "triangle": 3,
                "square": 4,
                "diamond": 4,
                "hexagon": 6,
            }.get(shape, 4)

            points = polygon_points(
                cx,
                cy,
                215,
                sides,
                rotation + (45 if shape == "diamond" else 0),
            )

            frame = f"""
                <polygon
                    points="{svg_points(points)}"
                    fill="{primary}"
                />
            """

        return f"""
            {frame}

            <text
                x="{cx}"
                y="{cy + 55}"
                text-anchor="middle"
                font-family="Arial, sans-serif"
                font-size="{font_size}"
                font-weight="700"
                fill="#FFFFFF"
            >{mark_initials}</text>
        """

    # -----------------------------------------------------
    # NEGATIVE SPACE
    # -----------------------------------------------------

    if logo_type == "negative-space":
        if shape in {"circle", "arcs"}:
            return f"""
                <circle
                    cx="{cx}"
                    cy="{cy}"
                    r="215"
                    fill="{primary}"
                />

                <path
                    d="
                    M {cx - 130} {cy + 80}
                    L {cx + 135} {cy - 105}
                    L {cx + 70} {cy + 115}
                    Z"
                    fill="#FFFFFF"
                />

                <circle
                    cx="{cx - 88}"
                    cy="{cy - 58}"
                    r="31"
                    fill="{accent}"
                />
            """

        outer = polygon_points(
            cx,
            cy,
            220,
            4 if shape == "square" else 6,
            rotation,
        )

        return f"""
            <polygon
                points="{svg_points(outer)}"
                fill="{primary}"
            />

            <path
                d="
                M {cx - 120} {cy + 70}
                L {cx + 130} {cy - 115}
                L {cx + 80} {cy + 110}
                Z"
                fill="#FFFFFF"
            />

            <circle
                cx="{cx - 80}"
                cy="{cy - 62}"
                r="28"
                fill="{accent}"
            />
        """

    # -----------------------------------------------------
    # EMBLEM
    # -----------------------------------------------------

    if logo_type == "emblem":
        return f"""
            <circle
                cx="{cx}"
                cy="{cy}"
                r="220"
                fill="{primary}"
            />

            <circle
                cx="{cx}"
                cy="{cy}"
                r="177"
                fill="none"
                stroke="{accent}"
                stroke-width="11"
            />

            <circle
                cx="{cx}"
                cy="{cy}"
                r="145"
                fill="{secondary}"
            />

            <text
                x="{cx}"
                y="{cy + 52}"
                text-anchor="middle"
                font-family="Arial, sans-serif"
                font-size="145"
                font-weight="700"
                fill="#FFFFFF"
            >{mark_initials}</text>
        """

    # -----------------------------------------------------
    # ABSTRACT
    # -----------------------------------------------------

    if logo_type == "abstract":
        if shape == "waves":
            return f"""
                <path
                    d="
                    M {cx - 225} {cy + 45}
                    C {cx - 120} {cy - 150},
                      {cx - 35} {cy + 155},
                      {cx + 70} {cy - 45}
                    C {cx + 125} {cy - 145},
                      {cx + 175} {cy - 90},
                      {cx + 225} {cy - 125}"
                    fill="none"
                    stroke="{primary}"
                    stroke-width="{stroke + 22}"
                    stroke-linecap="round"
                />

                <path
                    d="
                    M {cx - 185} {cy + 135}
                    C {cx - 75} {cy - 25},
                      {cx + 20} {cy + 150},
                      {cx + 185} {cy - 65}"
                    fill="none"
                    stroke="{accent}"
                    stroke-width="{stroke}"
                    stroke-linecap="round"
                />
            """

        if shape in {"arcs", "rings"}:
            return f"""
                <path
                    d="M {cx - 180} {cy + 80}
                       A 195 195 0 0 1 {cx + 75} {cy - 180}"
                    fill="none"
                    stroke="{primary}"
                    stroke-width="65"
                    stroke-linecap="round"
                />

                <path
                    d="M {cx - 70} {cy + 185}
                       A 195 195 0 0 0 {cx + 180} {cy - 65}"
                    fill="none"
                    stroke="{secondary}"
                    stroke-width="65"
                    stroke-linecap="round"
                />

                <circle
                    cx="{cx + 110}"
                    cy="{cy + 105}"
                    r="38"
                    fill="{accent}"
                />
            """

        return f"""
            <path
                d="
                M {cx - 210} {cy + 120}
                L {cx - 55} {cy - 185}
                L {cx + 30} {cy - 20}
                L {cx + 205} {cy - 150}
                L {cx + 105} {cy + 170}
                L {cx - 35} {cy + 75}
                Z"
                fill="{primary}"
            />

            <path
                d="
                M {cx - 50} {cy + 72}
                L {cx + 55} {cy - 75}
                L {cx + 115} {cy + 110}
                Z"
                fill="{accent}"
            />
        """

    # -----------------------------------------------------
    # COMBINATION
    # -----------------------------------------------------

    if logo_type == "combination":
        return f"""
            <circle
                cx="{cx - 75}"
                cy="{cy}"
                r="145"
                fill="{primary}"
            />

            <circle
                cx="{cx + 75}"
                cy="{cy}"
                r="145"
                fill="{secondary}"
            />

            <path
                d="
                M {cx - 40} {cy + 90}
                L {cx + 75} {cy - 110}
                L {cx + 120} {cy + 105}
                Z"
                fill="#FFFFFF"
            />

            <circle
                cx="{cx}"
                cy="{cy}"
                r="27"
                fill="{accent}"
            />
        """

    # -----------------------------------------------------
    # GEOMETRIC
    # -----------------------------------------------------

    sides = {
        "triangle": 3,
        "square": 4,
        "diamond": 4,
        "hexagon": 6,
    }.get(shape, 6)

    outer = polygon_points(
        cx,
        cy,
        220,
        sides,
        rotation + (45 if shape == "diamond" else 0),
    )

    inner = polygon_points(
        cx,
        cy,
        120,
        sides,
        rotation + 22 + (45 if shape == "diamond" else 0),
    )

    return f"""
        <polygon
            points="{svg_points(outer)}"
            fill="{primary}"
        />

        <polygon
            points="{svg_points(inner)}"
            fill="#FFFFFF"
        />

        <circle
            cx="{cx}"
            cy="{cy}"
            r="46"
            fill="{accent}"
        />
    """


# =========================================================
# SVG DOCUMENT
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
        str(business_name).strip().upper()
    )

    safe_industry = html.escape(
        str(industry)
        .replace("_", " ")
        .replace("-", " ")
        .strip()
        .upper()
    )

    primary = safe_color(
        specification,
        "primary_color",
        "#172554",
    )

    secondary = safe_color(
        specification,
        "secondary_color",
        "#2563EB",
    )

    accent = safe_color(
        specification,
        "accent_color",
        "#38BDF8",
    )

    # Wordmark already contains the company name in its mark.
    # Don't duplicate it with another huge line underneath.
    if specification.get("logo_type") == "wordmark":
        brand_y = 720
    else:
        brand_y = 760

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
        y="{brand_y}"
        text-anchor="middle"
        font-family="Arial, sans-serif"
        font-size="78"
        font-weight="700"
        fill="{primary}"
    >{safe_name}</text>

    <rect
        x="525"
        y="{brand_y + 55}"
        width="150"
        height="9"
        rx="4.5"
        fill="{accent}"
    />

    <text
        x="600"
        y="{brand_y + 125}"
        text-anchor="middle"
        font-family="Arial, sans-serif"
        font-size="28"
        letter-spacing="4"
        fill="{secondary}"
    >{safe_industry}</text>
</svg>
""".strip()


# =========================================================
# PNG SYMBOL
# =========================================================

def render_png_symbol(
    draw,
    specification,
    business_name,
    parameters,
):
    """
    For PNG, render the same design vocabulary directly
    through Pillow.
    """

    logo_type = specification.get("logo_type", "geometric")
    shape = specification.get("shape", "circle")

    primary = safe_color(
        specification,
        "primary_color",
        "#172554",
    )

    secondary = safe_color(
        specification,
        "secondary_color",
        "#2563EB",
    )

    accent = safe_color(
        specification,
        "accent_color",
        "#38BDF8",
    )

    cx = SYMBOL_X
    cy = SYMBOL_Y

    rotation = parameters["rotation"]
    stroke = max(10, parameters["stroke"])

    mark = initials(business_name)

    if logo_type == "wordmark":
        font = fit_name_font(
            draw,
            business_name,
            specification.get("font_style", "modern"),
            maximum_width=850,
            start_size=130,
        )

        draw_centered_text(
            draw,
            str(business_name).upper(),
            cx,
            cy,
            font,
            primary,
        )

        draw.rounded_rectangle(
            (
                cx - 115,
                cy + 85,
                cx + 115,
                cy + 99,
            ),
            radius=7,
            fill=accent,
        )

        return

    if logo_type in {"monogram", "lettermark"}:
        if shape in {"circle", "rings"}:
            draw.ellipse(
                (
                    cx - 205,
                    cy - 205,
                    cx + 205,
                    cy + 205,
                ),
                fill=primary,
            )

            draw.ellipse(
                (
                    cx - 166,
                    cy - 166,
                    cx + 166,
                    cy + 166,
                ),
                outline=secondary,
                width=10,
            )

        elif shape == "lines":
            points = [
                (cx - 210, cy + 130),
                (cx - 105, cy - 170),
                (cx, cy + 80),
                (cx + 105, cy - 170),
                (cx + 210, cy + 130),
            ]

            draw.line(
                points,
                fill=primary,
                width=stroke,
                joint="curve",
            )

        else:
            sides = {
                "triangle": 3,
                "square": 4,
                "diamond": 4,
                "hexagon": 6,
            }.get(shape, 4)

            points = polygon_points(
                cx,
                cy,
                215,
                sides,
                rotation + (45 if shape == "diamond" else 0),
            )

            draw.polygon(points, fill=primary)

        font = get_font(
            165 if len(mark) <= 2 else 135,
            "bold",
        )

        draw_centered_text(
            draw,
            mark,
            cx,
            cy,
            font,
            "#FFFFFF",
        )

        return

    if logo_type == "negative-space":
        draw.ellipse(
            (
                cx - 215,
                cy - 215,
                cx + 215,
                cy + 215,
            ),
            fill=primary,
        )

        cut = [
            (cx - 130, cy + 80),
            (cx + 135, cy - 105),
            (cx + 70, cy + 115),
        ]

        draw.polygon(
            cut,
            fill=BACKGROUND,
        )

        draw.ellipse(
            (
                cx - 119,
                cy - 89,
                cx - 57,
                cy - 27,
            ),
            fill=accent,
        )

        return

    if logo_type == "emblem":
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
                cx - 177,
                cy - 177,
                cx + 177,
                cy + 177,
            ),
            outline=accent,
            width=11,
        )

        draw.ellipse(
            (
                cx - 145,
                cy - 145,
                cx + 145,
                cy + 145,
            ),
            fill=secondary,
        )

        font = get_font(145, "bold")

        draw_centered_text(
            draw,
            mark,
            cx,
            cy,
            font,
            "#FFFFFF",
        )

        return

    if logo_type == "abstract":
        if shape in {"arcs", "rings", "waves"}:
            draw.arc(
                (
                    cx - 220,
                    cy - 220,
                    cx + 160,
                    cy + 160,
                ),
                205,
                345,
                fill=primary,
                width=55,
            )

            draw.arc(
                (
                    cx - 150,
                    cy - 150,
                    cx + 225,
                    cy + 225,
                ),
                25,
                175,
                fill=secondary,
                width=55,
            )

            draw.ellipse(
                (
                    cx + 72,
                    cy + 72,
                    cx + 142,
                    cy + 142,
                ),
                fill=accent,
            )

        else:
            points = [
                (cx - 210, cy + 120),
                (cx - 55, cy - 185),
                (cx + 30, cy - 20),
                (cx + 205, cy - 150),
                (cx + 105, cy + 170),
                (cx - 35, cy + 75),
            ]

            draw.polygon(
                points,
                fill=primary,
            )

            draw.polygon(
                [
                    (cx - 50, cy + 72),
                    (cx + 55, cy - 75),
                    (cx + 115, cy + 110),
                ],
                fill=accent,
            )

        return

    if logo_type == "combination":
        draw.ellipse(
            (
                cx - 220,
                cy - 145,
                cx + 70,
                cy + 145,
            ),
            fill=primary,
        )

        draw.ellipse(
            (
                cx - 70,
                cy - 145,
                cx + 220,
                cy + 145,
            ),
            fill=secondary,
        )

        draw.polygon(
            [
                (cx - 40, cy + 90),
                (cx + 75, cy - 110),
                (cx + 120, cy + 105),
            ],
            fill=BACKGROUND,
        )

        draw.ellipse(
            (
                cx - 27,
                cy - 27,
                cx + 27,
                cy + 27,
            ),
            fill=accent,
        )

        return

    # GEOMETRIC
    sides = {
        "triangle": 3,
        "square": 4,
        "diamond": 4,
        "hexagon": 6,
    }.get(shape, 6)

    outer = polygon_points(
        cx,
        cy,
        220,
        sides,
        rotation + (45 if shape == "diamond" else 0),
    )

    inner = polygon_points(
        cx,
        cy,
        120,
        sides,
        rotation + 22 + (45 if shape == "diamond" else 0),
    )

    draw.polygon(
        outer,
        fill=primary,
    )

    draw.polygon(
        inner,
        fill=BACKGROUND,
    )

    draw.ellipse(
        (
            cx - 46,
            cy - 46,
            cx + 46,
            cy + 46,
        ),
        fill=accent,
    )


# =========================================================
# BRAND TYPOGRAPHY
# =========================================================

def draw_brand_typography(
    image,
    business_name,
    industry,
    specification,
):
    draw = ImageDraw.Draw(image)

    primary = safe_color(
        specification,
        "primary_color",
        "#172554",
    )

    secondary = safe_color(
        specification,
        "secondary_color",
        "#2563EB",
    )

    accent = safe_color(
        specification,
        "accent_color",
        "#38BDF8",
    )

    style = specification.get(
        "font_style",
        "modern",
    )

    name = str(business_name).strip().upper()

    industry_text = (
        str(industry)
        .replace("_", " ")
        .replace("-", " ")
        .strip()
        .upper()
    )

    name_font = fit_name_font(
        draw,
        name,
        style,
        maximum_width=900,
        start_size=82,
    )

    industry_font = get_font(
        28,
        "minimal",
    )

    draw_centered_text(
        draw,
        name,
        WIDTH // 2,
        765,
        name_font,
        primary,
    )

    draw.rounded_rectangle(
        (
            WIDTH // 2 - 75,
            835,
            WIDTH // 2 + 75,
            845,
        ),
        radius=5,
        fill=accent,
    )

    draw_centered_text(
        draw,
        industry_text,
        WIDTH // 2,
        900,
        industry_font,
        secondary,
    )


# =========================================================
# PNG
# =========================================================

def render_png(
    business_name,
    industry,
    specification,
    parameters,
):
    image = Image.new(
        "RGB",
        (WIDTH, HEIGHT),
        BACKGROUND,
    )

    draw = ImageDraw.Draw(image)

    render_png_symbol(
        draw,
        specification,
        business_name,
        parameters,
    )

    # Wordmark already includes the name. However keeping the
    # consistent brand lockup beneath it makes exported concept
    # cards predictable.
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

    output.seek(0)

    return output.getvalue()


# =========================================================
# EXISTING CLOUD COMPATIBILITY
# =========================================================

def _trim_near_white_edges(
    image,
    threshold=246,
):
    rgb = image.convert("RGB")
    pixels = rgb.load()

    min_x = rgb.width
    min_y = rgb.height
    max_x = -1
    max_y = -1

    for y in range(rgb.height):
        for x in range(rgb.width):
            r, g, b = pixels[x, y]

            if (
                r < threshold
                or g < threshold
                or b < threshold
            ):
                min_x = min(min_x, x)
                min_y = min(min_y, y)
                max_x = max(max_x, x)
                max_y = max(max_y, y)

    if max_x < min_x or max_y < min_y:
        return rgb

    padding_x = max(
        20,
        int((max_x - min_x) * 0.08),
    )

    padding_y = max(
        20,
        int((max_y - min_y) * 0.08),
    )

    return rgb.crop(
        (
            max(0, min_x - padding_x),
            max(0, min_y - padding_y),
            min(rgb.width, max_x + padding_x + 1),
            min(rgb.height, max_y + padding_y + 1),
        )
    )


def _prepare_cloud_symbol(cloud_image_bytes):
    if not isinstance(
        cloud_image_bytes,
        (bytes, bytearray),
    ):
        raise RuntimeError(
            "Cloud image must be binary image data."
        )

    source = Image.open(
        BytesIO(cloud_image_bytes)
    )

    source.load()

    source = ImageOps.exif_transpose(
        source
    ).convert("RGB")

    source = _trim_near_white_edges(
        source
    )

    source = ImageEnhance.Contrast(
        source
    ).enhance(1.04)

    return source


def compose_cloud_logo(
    cloud_image_bytes: bytes,
    business_name: str,
    industry: str,
    specification: dict,
) -> bytes:
    """
    Kept for backward compatibility with the existing backend.
    """

    print(
        "[LOGO RENDERER] Composing provider artwork "
        "with deterministic typography."
    )

    symbol = _prepare_cloud_symbol(
        cloud_image_bytes
    )

    symbol.thumbnail(
        (620, 620),
        Image.Resampling.LANCZOS,
    )

    canvas = Image.new(
        "RGB",
        (WIDTH, HEIGHT),
        BACKGROUND,
    )

    x = int(
        WIDTH / 2 - symbol.width / 2
    )

    y = int(
        375 - symbol.height / 2
    )

    canvas.paste(
        symbol,
        (x, y),
    )

    draw_brand_typography(
        canvas,
        business_name,
        industry,
        specification,
    )

    output = BytesIO()

    canvas.save(
        output,
        format="PNG",
        optimize=True,
    )

    output.seek(0)

    result = output.getvalue()

    if len(result) < 1000:
        raise RuntimeError(
            "Logo compositor produced invalid PNG data."
        )

    return result


# =========================================================
# PUBLIC API
# =========================================================

def render_logo(
    business_name,
    industry,
    specification,
):
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