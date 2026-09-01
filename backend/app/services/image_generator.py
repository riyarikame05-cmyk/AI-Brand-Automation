from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import math
import random


# =========================================================
# COLOR PALETTES
# =========================================================

PALETTES = {
    "minimalist": [
        ("#111827", "#4F46E5", "#FFFFFF"),
        ("#0F172A", "#64748B", "#FFFFFF"),
        ("#18181B", "#52525B", "#FAFAFA"),
    ],

    "modern": [
        ("#4F46E5", "#06B6D4", "#FFFFFF"),
        ("#7C3AED", "#EC4899", "#FFFFFF"),
        ("#2563EB", "#14B8A6", "#FFFFFF"),
    ],

    "luxury": [
        ("#111111", "#C9A227", "#FFFFFF"),
        ("#1C1917", "#D4AF37", "#FAFAF9"),
        ("#171717", "#B8860B", "#FFFFFF"),
    ],

    "playful": [
        ("#7C3AED", "#F59E0B", "#FFFFFF"),
        ("#EC4899", "#06B6D4", "#FFFFFF"),
        ("#F97316", "#8B5CF6", "#FFFFFF"),
    ],

    "futuristic": [
        ("#0F172A", "#06B6D4", "#FFFFFF"),
        ("#111827", "#8B5CF6", "#FFFFFF"),
        ("#172554", "#22D3EE", "#FFFFFF"),
    ],

    "corporate": [
        ("#16324F", "#2563EB", "#FFFFFF"),
        ("#0F3D69", "#38BDF8", "#FFFFFF"),
        ("#1E3A5F", "#3B82F6", "#FFFFFF"),
    ],

    "professional": [
        ("#16324F", "#4EA5D9", "#FFFFFF"),
        ("#1E3A5F", "#64748B", "#FFFFFF"),
        ("#172554", "#2563EB", "#FFFFFF"),
    ],
}


# =========================================================
# FONT
# =========================================================

def get_font(size, bold=False):

    if bold:
        font_paths = [
            "C:/Windows/Fonts/arialbd.ttf",
            "C:/Windows/Fonts/segoeuib.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        ]

    else:
        font_paths = [
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/segoeui.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]

    for path in font_paths:

        try:
            return ImageFont.truetype(
                path,
                size
            )

        except OSError:
            continue

    return ImageFont.load_default()


# =========================================================
# HELPERS
# =========================================================

def center_text(
    draw,
    text,
    y,
    font,
    color,
    image_width,
):

    bbox = draw.textbbox(
        (0, 0),
        text,
        font=font
    )

    text_width = (
        bbox[2] - bbox[0]
    )

    x = (
        image_width - text_width
    ) / 2

    draw.text(
        (x, y),
        text,
        font=font,
        fill=color
    )


def polygon_points(
    cx,
    cy,
    radius,
    sides,
    rotation=-90,
):

    points = []

    for index in range(sides):

        angle = math.radians(
            rotation
            + index * (360 / sides)
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


# =========================================================
# TECHNOLOGY
# =========================================================

def draw_technology(
    draw,
    cx,
    cy,
    primary,
    accent,
    variant,
):

    if variant == 0:

        outer = polygon_points(
            cx,
            cy,
            135,
            6
        )

        draw.polygon(
            outer,
            fill=primary
        )

        inner = polygon_points(
            cx,
            cy,
            75,
            6
        )

        draw.polygon(
            inner,
            fill="white"
        )

        draw.ellipse(
            (
                cx - 30,
                cy - 30,
                cx + 30,
                cy + 30,
            ),
            fill=accent
        )

    elif variant == 1:

        nodes = [
            (cx, cy - 120),
            (cx - 115, cy + 70),
            (cx + 115, cy + 70),
        ]

        draw.line(
            nodes + [nodes[0]],
            fill=primary,
            width=28,
            joint="curve"
        )

        for x, y in nodes:

            draw.ellipse(
                (
                    x - 32,
                    y - 32,
                    x + 32,
                    y + 32,
                ),
                fill=accent
            )

    else:

        for angle in [
            0,
            90,
            180,
            270,
        ]:

            rad = math.radians(
                angle
            )

            x = (
                cx
                + 100
                * math.cos(rad)
            )

            y = (
                cy
                + 100
                * math.sin(rad)
            )

            draw.line(
                (
                    cx,
                    cy,
                    x,
                    y,
                ),
                fill=primary,
                width=30
            )

            draw.ellipse(
                (
                    x - 28,
                    y - 28,
                    x + 28,
                    y + 28,
                ),
                fill=accent
            )

        draw.ellipse(
            (
                cx - 45,
                cy - 45,
                cx + 45,
                cy + 45,
            ),
            fill=primary
        )


# =========================================================
# CLOTHING / TEXTILE
# =========================================================

def draw_textile(
    draw,
    cx,
    cy,
    primary,
    accent,
    variant,
):

    if variant == 0:

        for offset in [
            -80,
            -25,
            30,
            85,
        ]:

            draw.line(
                (
                    cx - 125,
                    cy + offset,
                    cx,
                    cy + offset - 65,
                    cx + 125,
                    cy + offset,
                ),
                fill=primary,
                width=25,
                joint="curve"
            )

    elif variant == 1:

        draw.arc(
            (
                cx - 140,
                cy - 120,
                cx + 140,
                cy + 140,
            ),
            190,
            350,
            fill=primary,
            width=28
        )

        draw.line(
            (
                cx - 115,
                cy + 55,
                cx,
                cy - 15,
                cx + 115,
                cy + 55,
            ),
            fill=accent,
            width=30
        )

    else:

        for offset in [
            -60,
            0,
            60,
        ]:

            draw.rounded_rectangle(
                (
                    cx - 130 + offset,
                    cy - 130,
                    cx - 70 + offset,
                    cy + 130,
                ),
                radius=25,
                fill=(
                    primary
                    if offset != 0
                    else accent
                )
            )


# =========================================================
# COFFEE
# =========================================================

def draw_coffee(
    draw,
    cx,
    cy,
    primary,
    accent,
    variant,
):

    if variant == 0:

        draw.ellipse(
            (
                cx - 95,
                cy - 135,
                cx + 95,
                cy + 135,
            ),
            fill=primary
        )

        draw.arc(
            (
                cx - 45,
                cy - 120,
                cx + 45,
                cy + 120,
            ),
            80,
            280,
            fill=accent,
            width=18
        )

    elif variant == 1:

        draw.rounded_rectangle(
            (
                cx - 120,
                cy - 70,
                cx + 75,
                cy + 90,
            ),
            radius=35,
            fill=primary
        )

        draw.ellipse(
            (
                cx + 40,
                cy - 30,
                cx + 145,
                cy + 65,
            ),
            outline=accent,
            width=25
        )

    else:

        for offset in [
            -55,
            0,
            55,
        ]:

            draw.arc(
                (
                    cx
                    + offset
                    - 30,
                    cy - 140,
                    cx
                    + offset
                    + 30,
                    cy - 15,
                ),
                180,
                360,
                fill=accent,
                width=16
            )

        draw.ellipse(
            (
                cx - 110,
                cy,
                cx + 110,
                cy + 100,
            ),
            fill=primary
        )


# =========================================================
# FINANCE
# =========================================================

def draw_finance(
    draw,
    cx,
    cy,
    primary,
    accent,
    variant,
):

    if variant == 0:

        heights = [
            80,
            135,
            200,
        ]

        for i, height in enumerate(
            heights
        ):

            x = (
                cx - 130
                + i * 90
            )

            draw.rounded_rectangle(
                (
                    x,
                    cy + 110 - height,
                    x + 55,
                    cy + 110,
                ),
                radius=10,
                fill=primary
            )

    elif variant == 1:

        draw.line(
            (
                cx - 130,
                cy + 80,
                cx - 30,
                cy + 15,
                cx + 50,
                cy - 55,
                cx + 130,
                cy - 125,
            ),
            fill=primary,
            width=35,
            joint="curve"
        )

        draw.polygon(
            [
                (
                    cx + 130,
                    cy - 125
                ),
                (
                    cx + 65,
                    cy - 110
                ),
                (
                    cx + 115,
                    cy - 55
                ),
            ],
            fill=accent
        )

    else:

        draw.ellipse(
            (
                cx - 135,
                cy - 135,
                cx + 135,
                cy + 135,
            ),
            outline=primary,
            width=28
        )

        draw.line(
            (
                cx,
                cy + 75,
                cx,
                cy - 75,
            ),
            fill=accent,
            width=30
        )

        draw.line(
            (
                cx - 55,
                cy - 25,
                cx,
                cy - 75,
                cx + 55,
                cy - 25,
            ),
            fill=accent,
            width=30
        )


# =========================================================
# GENERIC PROFESSIONAL SYMBOL
# =========================================================

def draw_generic(
    draw,
    cx,
    cy,
    primary,
    accent,
    variant,
):

    sides = [
        4,
        5,
        6,
    ][variant]

    outer = polygon_points(
        cx,
        cy,
        140,
        sides
    )

    draw.polygon(
        outer,
        fill=primary
    )

    inner = polygon_points(
        cx,
        cy,
        75,
        sides
    )

    draw.polygon(
        inner,
        fill="white"
    )

    draw.ellipse(
        (
            cx - 32,
            cy - 32,
            cx + 32,
            cy + 32,
        ),
        fill=accent
    )


# =========================================================
# CHOOSE INDUSTRY SYMBOL
# =========================================================

def draw_industry_symbol(
    draw,
    industry,
    cx,
    cy,
    primary,
    accent,
    variant,
):

    industry = (
        industry
        or ""
    ).strip().lower()

    if industry in [
        "technology",
        "ai",
        "gaming",
    ]:

        draw_technology(
            draw,
            cx,
            cy,
            primary,
            accent,
            variant
        )

    elif industry in [
        "clothing",
        "fashion",
        "textile",
    ]:

        draw_textile(
            draw,
            cx,
            cy,
            primary,
            accent,
            variant
        )

    elif industry in [
        "coffee",
        "restaurant",
    ]:

        draw_coffee(
            draw,
            cx,
            cy,
            primary,
            accent,
            variant
        )

    elif industry in [
        "finance",
        "ecommerce",
    ]:

        draw_finance(
            draw,
            cx,
            cy,
            primary,
            accent,
            variant
        )

    else:

        draw_generic(
            draw,
            cx,
            cy,
            primary,
            accent,
            variant
        )


# =========================================================
# MAIN GENERATOR
# =========================================================

def generate_logo_image(
    business_name: str,
    industry: str,
    style: str,
    description: str = "",
) -> bytes:

    width = 1200
    height = 1200

    style_key = (
        style
        or "modern"
    ).strip().lower()

    available_palettes = (
        PALETTES.get(
            style_key,
            PALETTES["modern"]
        )
    )

    # NEW RANDOM CHOICES EVERY GENERATION

    palette = random.choice(
        available_palettes
    )

    primary = palette[0]
    accent = palette[1]
    background = palette[2]

    variant = random.randint(
        0,
        2
    )

    image = Image.new(
        "RGB",
        (
            width,
            height
        ),
        background
    )

    draw = ImageDraw.Draw(
        image
    )

    # -----------------------------------------
    # LOGO SYMBOL
    # -----------------------------------------

    draw_industry_symbol(
        draw=draw,
        industry=industry,
        cx=width // 2,
        cy=380,
        primary=primary,
        accent=accent,
        variant=variant
    )


    # -----------------------------------------
    # COMPANY NAME
    # -----------------------------------------

    name = (
        business_name
        or "BRAND"
    ).strip().upper()


    if len(name) <= 10:

        font_size = 100

    elif len(name) <= 16:

        font_size = 80

    elif len(name) <= 22:

        font_size = 65

    else:

        font_size = 50


    name_font = get_font(
        font_size,
        bold=True
    )


    center_text(
        draw=draw,
        text=name,
        y=675,
        font=name_font,
        color=primary,
        image_width=width
    )


    # -----------------------------------------
    # ACCENT DIVIDER
    # -----------------------------------------

    draw.rounded_rectangle(
        (
            width // 2 - 65,
            815,
            width // 2 + 65,
            823,
        ),
        radius=4,
        fill=accent
    )


    # -----------------------------------------
    # INDUSTRY
    # -----------------------------------------

    industry_text = (
        (industry or "")
        .replace("_", " ")
        .replace("-", " ")
        .upper()
    )


    industry_font = get_font(
        29,
        bold=False
    )


    center_text(
        draw=draw,
        text=industry_text,
        y=855,
        font=industry_font,
        color=accent,
        image_width=width
    )


    # -----------------------------------------
    # EXPORT
    # -----------------------------------------

    buffer = BytesIO()

    image.save(
        buffer,
        format="PNG",
        optimize=True
    )

    buffer.seek(0)

    return buffer.getvalue()