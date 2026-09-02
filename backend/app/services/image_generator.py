import math
import random
from io import BytesIO

from PIL import (
    Image,
    ImageDraw,
    ImageFont,
)

from .logo_designer import (
    generate_logo_specification,
)


# =========================================================
# SETTINGS
# =========================================================

WIDTH = 1200
HEIGHT = 1200
BACKGROUND = "#FFFFFF"


# =========================================================
# FONT LOADER
# =========================================================

def get_font(
    size: int,
    font_style: str = "modern",
):

    font_map = {

        "bold": [
            "C:/Windows/Fonts/arialbd.ttf",
            "C:/Windows/Fonts/segoeuib.ttf",
        ],

        "modern": [
            "C:/Windows/Fonts/segoeuib.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
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


    paths = font_map.get(
        font_style,
        font_map["modern"],
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
# HELPERS
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
            + index
            * (360 / sides)
            - 90
        )


        x = (
            cx
            + radius
            * math.cos(angle)
        )


        y = (
            cy
            + radius
            * math.sin(angle)
        )


        points.append(
            (
                x,
                y,
            )
        )


    return points


def draw_center_text(
    draw,
    text,
    center_x,
    y,
    font,
    color,
):

    box = draw.textbbox(
        (
            0,
            0,
        ),
        text,
        font=font,
    )


    width = (
        box[2]
        - box[0]
    )


    draw.text(
        (
            center_x
            - width / 2,
            y,
        ),
        text,
        font=font,
        fill=color,
    )


def initials_from_name(
    business_name: str,
):

    words = [
        word
        for word
        in business_name.strip().split()
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
# BASIC SHAPE
# =========================================================

def draw_shape(
    draw,
    shape,
    cx,
    cy,
    radius,
    color,
    rotation,
    stroke_width,
    outline_only=False,
):

    if shape == "circle":

        box = (
            cx - radius,
            cy - radius,
            cx + radius,
            cy + radius,
        )


        if outline_only:

            draw.ellipse(
                box,
                outline=color,
                width=stroke_width,
            )

        else:

            draw.ellipse(
                box,
                fill=color,
            )


    elif shape == "square":

        points = polygon_points(
            cx,
            cy,
            radius,
            4,
            rotation + 45,
        )


        if outline_only:

            draw.line(
                points + [points[0]],
                fill=color,
                width=stroke_width,
                joint="curve",
            )

        else:

            draw.polygon(
                points,
                fill=color,
            )


    elif shape == "diamond":

        points = polygon_points(
            cx,
            cy,
            radius,
            4,
            rotation,
        )


        if outline_only:

            draw.line(
                points + [points[0]],
                fill=color,
                width=stroke_width,
                joint="curve",
            )

        else:

            draw.polygon(
                points,
                fill=color,
            )


    elif shape == "triangle":

        points = polygon_points(
            cx,
            cy,
            radius,
            3,
            rotation,
        )


        if outline_only:

            draw.line(
                points + [points[0]],
                fill=color,
                width=stroke_width,
                joint="curve",
            )

        else:

            draw.polygon(
                points,
                fill=color,
            )


    elif shape == "hexagon":

        points = polygon_points(
            cx,
            cy,
            radius,
            6,
            rotation,
        )


        if outline_only:

            draw.line(
                points + [points[0]],
                fill=color,
                width=stroke_width,
                joint="curve",
            )

        else:

            draw.polygon(
                points,
                fill=color,
            )


    elif shape == "rings":

        for offset in [
            0,
            45,
            90,
        ]:

            r = max(
                25,
                radius - offset,
            )


            draw.ellipse(
                (
                    cx - r,
                    cy - r,
                    cx + r,
                    cy + r,
                ),
                outline=color,
                width=max(
                    8,
                    stroke_width,
                ),
            )


    elif shape == "arcs":

        draw.arc(
            (
                cx - radius,
                cy - radius,
                cx + radius,
                cy + radius,
            ),
            start=20 + rotation,
            end=170 + rotation,
            fill=color,
            width=stroke_width,
        )


        inner = int(
            radius * 0.65
        )


        draw.arc(
            (
                cx - inner,
                cy - inner,
                cx + inner,
                cy + inner,
            ),
            start=200 + rotation,
            end=350 + rotation,
            fill=color,
            width=stroke_width,
        )


    elif shape == "lines":

        count = 5


        for index in range(count):

            offset = (
                index - 2
            ) * 45


            draw.line(
                (
                    cx - radius,
                    cy + offset,
                    cx + radius,
                    cy - offset,
                ),
                fill=color,
                width=stroke_width,
            )


    elif shape == "waves":

        points = []


        for x in range(
            int(cx - radius),
            int(cx + radius) + 1,
            10,
        ):

            relative = (
                x - cx
            )


            y = (
                cy
                + math.sin(
                    relative / 45
                )
                * radius
                * 0.35
            )


            points.append(
                (
                    x,
                    y,
                )
            )


        draw.line(
            points,
            fill=color,
            width=stroke_width,
        )


        second = [
            (
                x,
                y + 65,
            )
            for x, y
            in points
        ]


        draw.line(
            second,
            fill=color,
            width=max(
                8,
                stroke_width - 5,
            ),
        )


    elif shape == "interlocking":

        r = (
            radius * 0.7
        )


        draw.ellipse(
            (
                cx - r - 55,
                cy - r,
                cx + r - 55,
                cy + r,
            ),
            outline=color,
            width=stroke_width,
        )


        draw.ellipse(
            (
                cx - r + 55,
                cy - r,
                cx + r + 55,
                cy + r,
            ),
            outline=color,
            width=stroke_width,
        )


    else:

        draw.ellipse(
            (
                cx - radius,
                cy - radius,
                cx + radius,
                cy + radius,
            ),
            fill=color,
        )


# =========================================================
# MONOGRAM
# =========================================================

def render_monogram(
    draw,
    specification,
    business_name,
    cx,
    cy,
):

    primary = (
        specification[
            "primary_color"
        ]
    )


    accent = (
        specification[
            "accent_color"
        ]
    )


    initials = (
        initials_from_name(
            business_name
        )
    )


    shape = (
        specification[
            "shape"
        ]
    )


    draw_shape(
        draw,
        shape,
        cx,
        cy,
        190,
        primary,
        specification[
            "rotation"
        ],
        specification[
            "stroke_width"
        ],
        outline_only=True,
    )


    font = get_font(
        135,
        specification[
            "font_style"
        ],
    )


    draw_center_text(
        draw,
        initials,
        cx,
        cy - 85,
        font,
        accent,
    )


# =========================================================
# LETTERMARK
# =========================================================

def render_lettermark(
    draw,
    specification,
    business_name,
    cx,
    cy,
):

    initials = (
        initials_from_name(
            business_name
        )
    )


    font = get_font(
        210,
        "bold",
    )


    primary = (
        specification[
            "primary_color"
        ]
    )


    accent = (
        specification[
            "accent_color"
        ]
    )


    # First copy
    draw_center_text(
        draw,
        initials,
        cx - 20,
        cy - 145,
        font,
        primary,
    )


    # Offset accent creates
    # a custom overlapping lettermark.
    draw_center_text(
        draw,
        initials,
        cx + 20,
        cy - 115,
        font,
        accent,
    )


# =========================================================
# ABSTRACT
# =========================================================

def render_abstract(
    draw,
    specification,
    cx,
    cy,
):

    primary = (
        specification[
            "primary_color"
        ]
    )


    secondary = (
        specification[
            "secondary_color"
        ]
    )


    accent = (
        specification[
            "accent_color"
        ]
    )


    layers = (
        specification[
            "layers"
        ]
    )


    for index in range(
        layers
    ):

        radius = (
            190
            - index * 35
        )


        color = [
            primary,
            secondary,
            accent,
        ][
            index % 3
        ]


        rotation = (
            specification[
                "rotation"
            ]
            + index * 28
        )


        # Offset layers to make
        # abstract compositions.
        offset_x = (
            (index - layers / 2)
            * 20
        )


        offset_y = (
            math.sin(index)
            * 25
        )


        draw_shape(
            draw,
            specification[
                "shape"
            ],
            cx + offset_x,
            cy + offset_y,
            radius,
            color,
            rotation,
            specification[
                "stroke_width"
            ],
            outline_only=(
                index % 2 == 1
            ),
        )


# =========================================================
# GEOMETRIC
# =========================================================

def render_geometric(
    draw,
    specification,
    cx,
    cy,
):

    primary = (
        specification[
            "primary_color"
        ]
    )


    secondary = (
        specification[
            "secondary_color"
        ]
    )


    accent = (
        specification[
            "accent_color"
        ]
    )


    draw_shape(
        draw,
        specification[
            "shape"
        ],
        cx,
        cy,
        205,
        primary,
        specification[
            "rotation"
        ],
        specification[
            "stroke_width"
        ],
        outline_only=True,
    )


    inner_shape = (
        random.choice(
            [
                "circle",
                "diamond",
                "triangle",
                "hexagon",
            ]
        )
    )


    draw_shape(
        draw,
        inner_shape,
        cx,
        cy,
        115,
        secondary,
        specification[
            "rotation"
        ] + 30,
        specification[
            "stroke_width"
        ],
    )


    draw.ellipse(
        (
            cx - 35,
            cy - 35,
            cx + 35,
            cy + 35,
        ),
        fill=accent,
    )


# =========================================================
# EMBLEM
# =========================================================

def render_emblem(
    draw,
    specification,
    business_name,
    cx,
    cy,
):

    primary = (
        specification[
            "primary_color"
        ]
    )


    accent = (
        specification[
            "accent_color"
        ]
    )


    draw.ellipse(
        (
            cx - 215,
            cy - 215,
            cx + 215,
            cy + 215,
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
        width=(
            specification[
                "stroke_width"
            ]
        ),
    )


    initials = (
        initials_from_name(
            business_name
        )
    )


    font = get_font(
        125,
        "bold",
    )


    draw_center_text(
        draw,
        initials,
        cx,
        cy - 80,
        font,
        "#FFFFFF",
    )


# =========================================================
# NEGATIVE SPACE
# =========================================================

def render_negative_space(
    draw,
    specification,
    cx,
    cy,
):

    primary = (
        specification[
            "primary_color"
        ]
    )


    accent = (
        specification[
            "accent_color"
        ]
    )


    draw_shape(
        draw,
        specification[
            "shape"
        ],
        cx,
        cy,
        205,
        primary,
        specification[
            "rotation"
        ],
        specification[
            "stroke_width"
        ],
    )


    # White geometric cutout
    draw_shape(
        draw,
        "triangle",
        cx + 25,
        cy - 10,
        105,
        BACKGROUND,
        specification[
            "rotation"
        ] + 20,
        12,
    )


    draw.ellipse(
        (
            cx - 35,
            cy - 35,
            cx + 35,
            cy + 35,
        ),
        fill=accent,
    )


# =========================================================
# COMBINATION SYMBOL
# =========================================================

def render_combination(
    draw,
    specification,
    business_name,
    cx,
    cy,
):

    render_abstract(
        draw,
        specification,
        cx,
        cy,
    )


    initials = (
        initials_from_name(
            business_name
        )
    )


    font = get_font(
        90,
        "bold",
    )


    draw_center_text(
        draw,
        initials,
        cx,
        cy - 55,
        font,
        BACKGROUND,
    )


# =========================================================
# WORDMARK
# =========================================================

def render_wordmark(
    draw,
    specification,
    business_name,
):

    primary = (
        specification[
            "primary_color"
        ]
    )


    accent = (
        specification[
            "accent_color"
        ]
    )


    name = (
        business_name
        .strip()
        .upper()
    )


    font_size = 110


    if len(name) > 12:

        font_size = 80


    if len(name) > 20:

        font_size = 58


    font = get_font(
        font_size,
        specification[
            "font_style"
        ],
    )


    draw_center_text(
        draw,
        name,
        WIDTH // 2,
        430,
        font,
        primary,
    )


    # Decorative brand stroke
    line_width = min(
        400,
        max(
            150,
            len(name) * 25,
        ),
    )


    draw.rounded_rectangle(
        (
            WIDTH // 2
            - line_width // 2,

            590,

            WIDTH // 2
            + line_width // 2,

            604,
        ),
        radius=7,
        fill=accent,
    )


# =========================================================
# COMPANY NAME
# =========================================================

def render_company_name(
    draw,
    business_name,
    specification,
    y=740,
):

    name = (
        business_name
        .strip()
        .upper()
    )


    if len(name) <= 10:

        font_size = 88


    elif len(name) <= 16:

        font_size = 70


    elif len(name) <= 22:

        font_size = 57


    else:

        font_size = 45


    font = get_font(
        font_size,
        specification[
            "font_style"
        ],
    )


    draw_center_text(
        draw,
        name,
        WIDTH // 2,
        y,
        font,
        specification[
            "primary_color"
        ],
    )


# =========================================================
# MAIN LOGO GENERATOR
# =========================================================

def generate_logo_image(
    business_name: str,
    industry: str,
    style: str,
    description: str = "",
) -> bytes:

    # =====================================================
    # GET UNIQUE AI DESIGN SPECIFICATION
    # =====================================================

    specification = (
        generate_logo_specification(
            business_name=business_name,
            industry=industry,
            style=style,
            description=description,
        )
    )


    print("")
    print(
        "======================================"
    )
    print(
        "AI LOGO SPECIFICATION"
    )
    print(
        "======================================"
    )
    print(
        specification
    )


    # =====================================================
    # CANVAS
    # =====================================================

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


    logo_type = (
        specification[
            "logo_type"
        ]
    )


    layout = (
        specification[
            "layout"
        ]
    )


    # =====================================================
    # WORDMARK
    # =====================================================

    if logo_type == "wordmark":

        render_wordmark(
            draw,
            specification,
            business_name,
        )


    # =====================================================
    # SYMBOL LEFT
    # =====================================================

    elif layout == "symbol-left":

        cx = 320
        cy = 520


        render_logo_symbol(
            draw,
            logo_type,
            specification,
            business_name,
            cx,
            cy,
        )


        name = (
            business_name
            .strip()
            .upper()
        )


        font_size = (
            65
            if len(name) <= 14
            else 48
        )


        font = get_font(
            font_size,
            specification[
                "font_style"
            ],
        )


        draw.text(
            (
                570,
                470,
            ),
            name,
            font=font,
            fill=(
                specification[
                    "primary_color"
                ]
            ),
        )


    # =====================================================
    # STANDARD / EMBLEM
    # =====================================================

    else:

        cx = (
            WIDTH // 2
        )

        cy = 415


        render_logo_symbol(
            draw,
            logo_type,
            specification,
            business_name,
            cx,
            cy,
        )


        if logo_type not in [
            "wordmark",
        ]:

            render_company_name(
                draw,
                business_name,
                specification,
                y=720,
            )


    # =====================================================
    # INDUSTRY LABEL
    # =====================================================

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


    small_font = get_font(
        27,
        "minimal",
    )


    draw_center_text(
        draw,
        industry_text,
        WIDTH // 2,
        860,
        small_font,
        specification[
            "secondary_color"
        ],
    )


    # =====================================================
    # EXPORT PNG
    # =====================================================

    buffer = BytesIO()


    image.save(
        buffer,
        format="PNG",
        optimize=True,
    )


    buffer.seek(
        0
    )


    return buffer.getvalue()


# =========================================================
# SYMBOL ROUTER
# =========================================================

def render_logo_symbol(
    draw,
    logo_type,
    specification,
    business_name,
    cx,
    cy,
):

    if logo_type == "monogram":

        render_monogram(
            draw,
            specification,
            business_name,
            cx,
            cy,
        )


    elif logo_type == "lettermark":

        render_lettermark(
            draw,
            specification,
            business_name,
            cx,
            cy,
        )


    elif logo_type == "abstract":

        render_abstract(
            draw,
            specification,
            cx,
            cy,
        )


    elif logo_type == "geometric":

        render_geometric(
            draw,
            specification,
            cx,
            cy,
        )


    elif logo_type == "emblem":

        render_emblem(
            draw,
            specification,
            business_name,
            cx,
            cy,
        )


    elif logo_type == "negative-space":

        render_negative_space(
            draw,
            specification,
            cx,
            cy,
        )


    elif logo_type == "combination":

        render_combination(
            draw,
            specification,
            business_name,
            cx,
            cy,
        )


    else:

        render_abstract(
            draw,
            specification,
            cx,
            cy,
        )