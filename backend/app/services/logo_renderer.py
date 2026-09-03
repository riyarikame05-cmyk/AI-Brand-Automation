import html
import math
import random
from io import BytesIO

from PIL import Image, ImageDraw, ImageFont


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
        ],

        "bold": [
            "C:/Windows/Fonts/arialbd.ttf",
            "C:/Windows/Fonts/segoeuib.ttf",
        ],

        "elegant": [
            "C:/Windows/Fonts/georgiab.ttf",
            "C:/Windows/Fonts/timesbd.ttf",
        ],

        "minimal": [
            "C:/Windows/Fonts/segoeui.ttf",
            "C:/Windows/Fonts/arial.ttf",
        ],
    }

    for path in fonts.get(
        style,
        fonts["modern"],
    ):

        try:

            return ImageFont.truetype(
                path,
                size,
            )

        except OSError:

            continue

    return ImageFont.load_default()


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
            * (360 / sides)
        )

        points.append(
            (
                cx
                + radius
                * math.cos(angle),

                cy
                + radius
                * math.sin(angle),
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
        for word
        in business_name
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
# PNG TEXT
# =========================================================

def draw_centered_text(
    draw,
    text,
    x,
    y,
    font,
    fill,
):

    bbox = draw.textbbox(
        (0, 0),
        text,
        font=font,
    )

    width = (
        bbox[2]
        - bbox[0]
    )

    draw.text(
        (
            x - width / 2,
            y,
        ),
        text,
        font=font,
        fill=fill,
    )


# =========================================================
# RANDOM DESIGN PARAMETERS
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
# SVG SYMBOL
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

    primary = specification[
        "primary_color"
    ]

    secondary = specification[
        "secondary_color"
    ]

    accent = specification[
        "accent_color"
    ]

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
    # MONOGRAM
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
    # ABSTRACT
    # -----------------------------------------------------

    elif logo_type in [
        "abstract",
        "combination",
    ]:

        layers = parameters[
            "layers"
        ]

        colors = [
            primary,
            secondary,
            accent,
        ]

        for index in range(
            layers
        ):

            radius = (
                190
                - index * 30
            )

            sides = [
                3,
                4,
                5,
                6,
            ][
                index % 4
            ]

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

            opacity = (
                0.92
                - index * 0.10
            )

            elements.append(
                f"""
                <polygon
                    points="{svg_points(points)}"
                    fill="{color}"
                    fill-opacity="{max(0.35, opacity)}"
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
            random.choice(
                [
                    4,
                    5,
                    6,
                ]
            ),
            rotation,
        )

        inner = polygon_points(
            cx,
            cy,
            120,
            random.choice(
                [
                    3,
                    4,
                    6,
                ]
            ),
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
# COMPLETE SVG
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
        business_name
        .strip()
        .upper()
    )

    safe_industry = html.escape(
        industry
        .replace(
            "_",
            " "
        )
        .replace(
            "-",
            " "
        )
        .upper()
    )

    primary = specification[
        "primary_color"
    ]

    secondary = specification[
        "secondary_color"
    ]

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
# PNG SYMBOL
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

    primary = specification[
        "primary_color"
    ]

    secondary = specification[
        "secondary_color"
    ]

    accent = specification[
        "accent_color"
    ]

    rotation = parameters[
        "rotation"
    ]

    stroke = parameters[
        "stroke"
    ]

    cx = 600
    cy = 395


    if logo_type in [
        "monogram",
        "lettermark",
    ]:

        points = polygon_points(
            cx,
            cy,
            190,
            random.choice(
                [
                    4,
                    5,
                    6,
                ]
            ),
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
            specification[
                "font_style"
            ],
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


    elif logo_type in [
        "abstract",
        "combination",
    ]:

        colors = [
            primary,
            secondary,
            accent,
        ]

        for index in range(
            parameters[
                "layers"
            ]
        ):

            points = polygon_points(
                cx
                + (
                    index
                    - 1
                )
                * 30,
                cy,
                190
                - index * 30,
                [
                    3,
                    4,
                    5,
                    6,
                ][
                    index % 4
                ],
                rotation
                + index * 35,
            )

            draw.polygon(
                points,
                fill=colors[
                    index % 3
                ],
            )


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
# COMPLETE PNG
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

    name = (
        business_name
        .strip()
        .upper()
    )

    if len(name) <= 10:
        size = 86

    elif len(name) <= 16:
        size = 70

    elif len(name) <= 22:
        size = 56

    else:
        size = 44

    name_font = get_font(
        size,
        specification[
            "font_style"
        ],
    )

    draw_centered_text(
        draw,
        name,
        600,
        720,
        name_font,
        specification[
            "primary_color"
        ],
    )

    draw.rounded_rectangle(
        (
            530,
            825,
            670,
            833,
        ),
        radius=4,
        fill=specification[
            "secondary_color"
        ],
    )

    industry_text = (
        industry
        .replace(
            "_",
            " "
        )
        .replace(
            "-",
            " "
        )
        .upper()
    )

    industry_font = get_font(
        27,
        "minimal",
    )

    draw_centered_text(
        draw,
        industry_text,
        600,
        860,
        industry_font,
        specification[
            "secondary_color"
        ],
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
# PUBLIC FUNCTION
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