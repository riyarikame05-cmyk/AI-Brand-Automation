from __future__ import annotations

import hashlib
import html
import json
import math
import re
from io import BytesIO
from typing import Any

from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageOps


WIDTH = 1200
HEIGHT = 1200
BACKGROUND = "#FFFFFF"

# Local logos are constructed at 2x resolution and downsampled at the end.
SCALE = 2
WORK_WIDTH = WIDTH * SCALE
WORK_HEIGHT = HEIGHT * SCALE

HEX_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")

DEFAULT_PRIMARY = "#172554"
DEFAULT_SECONDARY = "#2563EB"
DEFAULT_ACCENT = "#60A5FA"

DIRECTIONS = {
    "minimal-geometric",
    "negative-space",
    "monogram",
    "abstract-motion",
    "wordmark",
    "brand-emblem",
}


def safe_color(value: Any, fallback: str) -> str:
    value = str(value or "").strip()
    if HEX_RE.fullmatch(value):
        return value.upper()
    return fallback.upper()


def _resample_lanczos():
    return Image.Resampling.LANCZOS


def _scaled(value: float) -> int:
    return max(1, int(round(value * SCALE)))


def _stable_payload(specification: dict) -> str:
    try:
        return json.dumps(
            specification or {},
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
            default=str,
        )
    except TypeError:
        return repr(specification)


def _stable_seed(specification: dict) -> int:
    payload = _stable_payload(specification)
    digest = hashlib.sha256(payload.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big", signed=False)


def _variant(seed: int, slot: int, choices: int) -> int:
    if choices <= 0:
        return 0
    shifted = seed >> ((slot % 8) * 8)
    return shifted % choices


def get_font(size: int, style: str = "modern"):
    size = max(8, int(size))
    style = str(style or "modern").lower()

    if style in {"serif", "classic", "luxury", "elegant"}:
        candidates = [
            "C:/Windows/Fonts/georgiab.ttf",
            "C:/Windows/Fonts/georgia.ttf",
            "C:/Windows/Fonts/timesbd.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
            "/usr/share/fonts/truetype/liberation2/LiberationSerif-Bold.ttf",
        ]
    elif style in {"rounded", "friendly", "soft"}:
        candidates = [
            "C:/Windows/Fonts/arialbd.ttf",
            "C:/Windows/Fonts/calibrib.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
        ]
    else:
        candidates = [
            "C:/Windows/Fonts/seguisb.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
            "C:/Windows/Fonts/calibrib.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
        ]

    for path in candidates:
        try:
            return ImageFont.truetype(path, size=size)
        except (OSError, IOError):
            continue

    return ImageFont.load_default()


def _get_regular_font(size: int, style: str = "modern"):
    size = max(8, int(size))
    style = str(style or "modern").lower()

    if style in {"serif", "classic", "luxury", "elegant"}:
        candidates = [
            "C:/Windows/Fonts/georgia.ttf",
            "C:/Windows/Fonts/times.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
        ]
    else:
        candidates = [
            "C:/Windows/Fonts/segoeui.ttf",
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/calibri.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
        ]

    for path in candidates:
        try:
            return ImageFont.truetype(path, size=size)
        except (OSError, IOError):
            continue

    return get_font(size, style)


def initials(business_name: str) -> str:
    name = str(business_name or "").strip()

    # Separate ordinary words first.
    words = re.findall(r"[A-Za-z0-9]+", name)
    if not words:
        return "AI"

    if len(words) > 1:
        return (words[0][0] + words[-1][0]).upper()

    word = words[0]

    # Preserve meaningful CamelCase boundaries:
    # NovaCraft -> NC, LuminaGrid -> LG, PulseArc -> PA.
    camel_parts = re.findall(
        r"[A-Z]+(?=[A-Z][a-z]|\d|\b)|[A-Z]?[a-z]+|\d+",
        word,
    )

    alpha_parts = [
        part
        for part in camel_parts
        if any(char.isalpha() for char in part)
    ]

    if len(alpha_parts) >= 2:
        return (
            alpha_parts[0][0]
            + alpha_parts[-1][0]
        ).upper()

    letters = re.sub(r"[^A-Za-z0-9]", "", word).upper()
    return letters[:2] if len(letters) > 1 else letters


def polygon_points(
    cx: float,
    cy: float,
    radius: float,
    sides: int,
    rotation: float = -90,
):
    sides = max(3, int(sides))
    return [
        (
            cx + radius * math.cos(math.radians(rotation + i * 360 / sides)),
            cy + radius * math.sin(math.radians(rotation + i * 360 / sides)),
        )
        for i in range(sides)
    ]


def svg_points(points) -> str:
    return " ".join(f"{x:.1f},{y:.1f}" for x, y in points)


def text_size(draw: ImageDraw.ImageDraw, text: str, font) -> tuple[int, int]:
    if not text:
        return 0, 0
    box = draw.textbbox((0, 0), text, font=font)
    return box[2] - box[0], box[3] - box[1]


def _fit_font(
    draw: ImageDraw.ImageDraw,
    text: str,
    max_width: int,
    start_size: int,
    minimum: int,
    style: str,
    regular: bool = False,
):
    size = int(start_size)
    while size > minimum:
        font = (
            _get_regular_font(size, style)
            if regular
            else get_font(size, style)
        )
        width, _ = text_size(draw, text, font)
        if width <= max_width:
            return font
        size -= 2
    return (
        _get_regular_font(minimum, style)
        if regular
        else get_font(minimum, style)
    )


def fit_name_font(
    draw: ImageDraw.ImageDraw,
    business_name: str,
    max_width: int = 980,
    start_size: int = 112,
    minimum: int = 54,
    style: str = "modern",
):
    return _fit_font(
        draw,
        business_name,
        max_width,
        start_size,
        minimum,
        style,
    )


def draw_centered_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    y: int,
    font,
    fill: str,
    canvas_width: int = WIDTH,
):
    width, _ = text_size(draw, text, font)
    x = int((canvas_width - width) / 2)
    draw.text((x, y), text, font=font, fill=fill)
    return x


def build_parameters(specification):
    specification = specification or {}
    seed = _stable_seed(specification)

    primary = safe_color(
        specification.get("primary_color"),
        DEFAULT_PRIMARY,
    )
    secondary = safe_color(
        specification.get("secondary_color"),
        DEFAULT_SECONDARY,
    )
    accent = safe_color(
        specification.get("accent_color"),
        DEFAULT_ACCENT,
    )

    direction = str(
        specification.get("creative_direction")
        or specification.get("logo_type")
        or "minimal-geometric"
    ).strip().lower()

    aliases = {
        "geometric": "minimal-geometric",
        "minimal": "minimal-geometric",
        "negative": "negative-space",
        "abstract": "abstract-motion",
        "motion": "abstract-motion",
        "emblem": "brand-emblem",
    }
    direction = aliases.get(direction, direction)
    if direction not in DIRECTIONS:
        direction = "minimal-geometric"

    try:
        rotation = float(specification.get("rotation", 0) or 0)
    except (TypeError, ValueError):
        rotation = 0.0

    try:
        layers = int(specification.get("layers", 2) or 2)
    except (TypeError, ValueError):
        layers = 2

    try:
        complexity = int(specification.get("complexity", 2) or 2)
    except (TypeError, ValueError):
        complexity = 2

    try:
        stroke_width = int(specification.get("stroke_width", 14) or 14)
    except (TypeError, ValueError):
        stroke_width = 14

    return {
        "seed": seed,
        "direction": direction,
        "primary": primary,
        "secondary": secondary,
        "accent": accent,
        "rotation": rotation,
        "layers": max(1, min(layers, 5)),
        "complexity": max(1, min(complexity, 5)),
        "stroke_width": max(6, min(stroke_width, 40)),
        "font_style": str(
            specification.get("font_style") or "modern"
        ).strip().lower(),
        "geometry_style": str(
            specification.get("geometry_style") or "sharp"
        ).strip().lower(),
        "shape": str(
            specification.get("shape") or "geometric"
        ).strip().lower(),
        "layout": str(
            specification.get("layout") or "symbol-top"
        ).strip().lower(),
        "visual_metaphor": str(
            specification.get("visual_metaphor") or ""
        ).strip(),
        "composition": str(
            specification.get("composition") or ""
        ).strip(),
        "symbol_family": str(
            specification.get("symbol_family") or ""
        ).strip().lower(),
        "treatment": str(
            specification.get("treatment") or "flat"
        ).strip().lower(),
        "background_mode": str(
            specification.get("background_mode") or "light"
        ).strip().lower(),
        "wordmark_emphasis": str(
            specification.get("wordmark_emphasis") or "single"
        ).strip().lower(),
    }


def _new_work_canvas():
    return Image.new(
        "RGB",
        (WORK_WIDTH, WORK_HEIGHT),
        BACKGROUND,
    )


def _work_draw(canvas):
    return ImageDraw.Draw(canvas)


def _line(draw, points, fill, width, joint="curve"):
    draw.line(
        [(_scaled(x), _scaled(y)) for x, y in points],
        fill=fill,
        width=_scaled(width),
        joint=joint,
    )


def _ellipse(draw, box, fill=None, outline=None, width=1):
    draw.ellipse(
        tuple(_scaled(v) for v in box),
        fill=fill,
        outline=outline,
        width=_scaled(width),
    )


def _rectangle(draw, box, fill=None, outline=None, width=1, radius=0):
    scaled_box = tuple(_scaled(v) for v in box)
    if radius:
        draw.rounded_rectangle(
            scaled_box,
            radius=_scaled(radius),
            fill=fill,
            outline=outline,
            width=_scaled(width),
        )
    else:
        draw.rectangle(
            scaled_box,
            fill=fill,
            outline=outline,
            width=_scaled(width),
        )


def _polygon(draw, points, fill):
    draw.polygon(
        [(_scaled(x), _scaled(y)) for x, y in points],
        fill=fill,
    )


def _arc(draw, box, start, end, fill, width):
    draw.arc(
        tuple(_scaled(v) for v in box),
        start=start,
        end=end,
        fill=fill,
        width=_scaled(width),
    )


def _draw_minimal_geometric(canvas, p):
    draw = _work_draw(canvas)
    cx, cy = 600, 370
    seed = p["seed"]
    variant = _variant(seed, 0, 4)
    primary = p["primary"]
    secondary = p["secondary"]
    accent = p["accent"]

    if variant == 0:
        # Segmented hexagonal network: a strong outer silhouette with
        # deliberately disconnected colored modules and a central hub.
        outer = polygon_points(cx, cy, 218, 6, -90)
        inner = polygon_points(cx, cy, 128, 6, -90)

        for i in range(6):
            color = (
                primary
                if i in {0, 3}
                else secondary
                if i in {1, 4}
                else accent
            )
            quad = [
                outer[i],
                outer[(i + 1) % 6],
                inner[(i + 1) % 6],
                inner[i],
            ]
            _polygon(draw, quad, color)

        for i in (0, 2, 4):
            _line(draw, [inner[i], (cx, cy)], primary, 20)

        _ellipse(
            draw,
            (cx - 40, cy - 40, cx + 40, cy + 40),
            fill=BACKGROUND,
            outline=accent,
            width=16,
        )
        _ellipse(
            draw,
            (cx - 13, cy - 13, cx + 13, cy + 13),
            fill=accent,
        )

    elif variant == 1:
        # Two linked diamonds with a shared illuminated center.
        left = polygon_points(cx - 72, cy, 168, 4, 45)
        right = polygon_points(cx + 72, cy, 168, 4, 45)

        _line(
            draw,
            left + [left[0]],
            primary,
            28,
        )
        _line(
            draw,
            right + [right[0]],
            secondary,
            28,
        )

        _rectangle(
            draw,
            (cx - 82, cy - 26, cx + 82, cy + 26),
            fill=BACKGROUND,
            radius=13,
        )
        _rectangle(
            draw,
            (cx - 57, cy - 15, cx + 57, cy + 15),
            fill=accent,
            radius=14,
        )

    elif variant == 2:
        # Grid/network construction for technology and infrastructure brands.
        nodes = [
            (cx - 160, cy - 105),
            (cx, cy - 175),
            (cx + 160, cy - 105),
            (cx + 160, cy + 95),
            (cx, cy + 175),
            (cx - 160, cy + 95),
        ]

        for a, b in [
            (0, 1),
            (1, 2),
            (2, 3),
            (3, 4),
            (4, 5),
            (5, 0),
            (0, 3),
            (1, 4),
        ]:
            _line(
                draw,
                [nodes[a], nodes[b]],
                primary if (a + b) % 2 else secondary,
                22,
            )

        for index, (x, y) in enumerate(nodes):
            radius = 27 if index % 2 else 32
            color = accent if index in {1, 3, 4} else primary
            _ellipse(
                draw,
                (x - radius, y - radius, x + radius, y + radius),
                fill=color,
            )

        _ellipse(
            draw,
            (cx - 45, cy - 45, cx + 45, cy + 45),
            fill=BACKGROUND,
            outline=secondary,
            width=18,
        )
        _ellipse(
            draw,
            (cx - 14, cy - 14, cx + 14, cy + 14),
            fill=accent,
        )

    else:
        # A compact stepped lattice. Unlike the old triple-chevron, the
        # separate modules lock together into a single ownable silhouette.
        modules = [
            (
                [
                    (cx - 190, cy - 95),
                    (cx - 70, cy - 95),
                    (cx + 15, cy - 10),
                    (cx - 70, cy + 75),
                    (cx - 190, cy + 75),
                    (cx - 105, cy - 10),
                ],
                primary,
            ),
            (
                [
                    (cx - 38, cy - 155),
                    (cx + 82, cy - 155),
                    (cx + 177, cy - 60),
                    (cx + 92, cy + 25),
                    (cx + 7, cy - 60),
                    (cx - 38, cy - 60),
                ],
                secondary,
            ),
            (
                [
                    (cx + 8, cy + 45),
                    (cx + 90, cy - 37),
                    (cx + 183, cy + 56),
                    (cx + 183, cy + 126),
                    (cx + 90, cy + 33),
                    (cx + 8, cy + 115),
                ],
                accent,
            ),
        ]
        for points, color in modules:
            _polygon(draw, points, color)


def _draw_negative_space(canvas, p):
    seed = p["seed"]
    primary = p["primary"]
    secondary = p["secondary"]
    accent = p["accent"]

    # Construct on masks. The white region is genuinely removed from the
    # foreground mask rather than merely painted as decorative artwork.
    mark = Image.new("L", (WORK_WIDTH, WORK_HEIGHT), 0)
    cut = Image.new("L", (WORK_WIDTH, WORK_HEIGHT), 0)
    md = ImageDraw.Draw(mark)
    cd = ImageDraw.Draw(cut)

    variant = _variant(seed, 2, 3)
    cx, cy = 600, 370

    if variant == 0:
        md.ellipse(
            (
                _scaled(cx - 210),
                _scaled(cy - 190),
                _scaled(cx + 210),
                _scaled(cy + 190),
            ),
            fill=255,
        )
        cut_poly = [
            (cx - 95, cy + 110),
            (cx + 15, cy - 118),
            (cx + 118, cy + 110),
            (cx + 54, cy + 110),
            (cx + 10, cy + 18),
            (cx - 40, cy + 110),
        ]
        cd.polygon(
            [(_scaled(x), _scaled(y)) for x, y in cut_poly],
            fill=255,
        )

    elif variant == 1:
        outer = polygon_points(cx, cy, 218, 6, -90)
        md.polygon(
            [(_scaled(x), _scaled(y)) for x, y in outer],
            fill=255,
        )
        cd.rounded_rectangle(
            (
                _scaled(cx - 58),
                _scaled(cy - 220),
                _scaled(cx + 58),
                _scaled(cy + 85),
            ),
            radius=_scaled(30),
            fill=255,
        )
        cd.polygon(
            [
                (_scaled(cx - 60), _scaled(cy + 20)),
                (_scaled(cx + 180), _scaled(cy + 20)),
                (_scaled(cx + 180), _scaled(cy + 100)),
                (_scaled(cx - 60), _scaled(cy + 100)),
            ],
            fill=255,
        )

    else:
        md.rounded_rectangle(
            (
                _scaled(cx - 205),
                _scaled(cy - 175),
                _scaled(cx + 205),
                _scaled(cy + 175),
            ),
            radius=_scaled(84),
            fill=255,
        )
        cd.ellipse(
            (
                _scaled(cx - 92),
                _scaled(cy - 92),
                _scaled(cx + 92),
                _scaled(cy + 92),
            ),
            fill=255,
        )
        cd.polygon(
            [
                (_scaled(cx - 5), _scaled(cy - 175)),
                (_scaled(cx + 205), _scaled(cy - 175)),
                (_scaled(cx + 205), _scaled(cy - 45)),
                (_scaled(cx + 72), _scaled(cy + 25)),
            ],
            fill=255,
        )

    final_mask = ImageChops.subtract(mark, cut)
    ink = Image.new("RGB", (WORK_WIDTH, WORK_HEIGHT), primary)
    canvas.paste(ink, (0, 0), final_mask)

    draw = _work_draw(canvas)
    if variant == 0:
        _ellipse(
            draw,
            (cx + 128, cy - 154, cx + 184, cy - 98),
            fill=accent,
        )
        _line(draw, [(cx + 105, cy + 126), (cx + 180, cy + 126)], secondary, 24)
    elif variant == 1:
        _ellipse(
            draw,
            (cx + 104, cy - 145, cx + 166, cy - 83),
            fill=accent,
        )
    else:
        _rectangle(
            draw,
            (cx - 168, cy + 111, cx - 30, cy + 137),
            fill=secondary,
            radius=13,
        )
        _ellipse(
            draw,
            (cx + 122, cy + 91, cx + 176, cy + 145),
            fill=accent,
        )


def _draw_monogram(canvas, p, business_name):
    draw = _work_draw(canvas)
    seed = p["seed"]
    letters = initials(business_name)
    if len(letters) == 1:
        letters += letters

    a, b = letters[0], letters[1]
    primary = p["primary"]
    secondary = p["secondary"]
    accent = p["accent"]
    style = p["font_style"]
    variant = _variant(seed, 3, 3)
    cx, cy = 600, 365

    font = get_font(_scaled(205), style)

    # Render each initial to its own mask so the overlap can be deliberately
    # controlled instead of looking like two unrelated pieces of text.
    def letter_mask(letter, x_center, y_top):
        mask = Image.new("L", (WORK_WIDTH, WORK_HEIGHT), 0)
        md = ImageDraw.Draw(mask)
        box = md.textbbox((0, 0), letter, font=font)
        width = box[2] - box[0]
        md.text(
            (_scaled(x_center) - width // 2, _scaled(y_top)),
            letter,
            font=font,
            fill=255,
        )
        return mask

    if variant == 0:
        _rectangle(
            draw,
            (cx - 214, cy - 194, cx + 214, cy + 194),
            outline=primary,
            width=18,
            radius=58,
        )

        mask_a = letter_mask(a, cx - 48, cy - 122)
        mask_b = letter_mask(b, cx + 48, cy - 122)

        ink_a = Image.new("RGB", canvas.size, primary)
        ink_b = Image.new("RGB", canvas.size, secondary)
        canvas.paste(ink_a, (0, 0), mask_a)
        canvas.paste(ink_b, (0, 0), mask_b)

        overlap = ImageChops.multiply(mask_a, mask_b)
        overlap_ink = Image.new("RGB", canvas.size, accent)
        canvas.paste(overlap_ink, (0, 0), overlap)

        # Shared baseline visually binds the two characters.
        _rectangle(
            draw,
            (cx - 115, cy + 111, cx + 115, cy + 132),
            fill=accent,
            radius=10,
        )

    elif variant == 1:
        # Offset initials share a vertical structural spine.
        _line(
            draw,
            [(cx - 168, cy - 168), (cx - 168, cy + 155), (cx - 18, cy + 155)],
            primary,
            24,
        )
        _line(
            draw,
            [(cx + 168, cy - 155), (cx + 168, cy + 168), (cx + 18, cy - 168)],
            secondary,
            24,
        )
        _line(
            draw,
            [(cx, cy - 137), (cx, cy + 137)],
            accent,
            20,
        )

        mask_a = letter_mask(a, cx - 43, cy - 115)
        mask_b = letter_mask(b, cx + 43, cy - 115)
        canvas.paste(Image.new("RGB", canvas.size, primary), (0, 0), mask_a)
        canvas.paste(Image.new("RGB", canvas.size, secondary), (0, 0), mask_b)

    else:
        diamond = polygon_points(cx, cy, 222, 4, 45)
        inner = polygon_points(cx, cy, 186, 4, 45)
        _polygon(draw, diamond, primary)
        _polygon(draw, inner, BACKGROUND)

        mask_a = letter_mask(a, cx - 45, cy - 118)
        mask_b = letter_mask(b, cx + 45, cy - 118)
        canvas.paste(Image.new("RGB", canvas.size, primary), (0, 0), mask_a)
        canvas.paste(Image.new("RGB", canvas.size, secondary), (0, 0), mask_b)

        overlap = ImageChops.multiply(mask_a, mask_b)
        canvas.paste(Image.new("RGB", canvas.size, accent), (0, 0), overlap)

        _ellipse(
            draw,
            (cx - 25, cy + 139, cx + 25, cy + 189),
            fill=accent,
        )


def _draw_abstract_motion(canvas, p):
    draw = _work_draw(canvas)
    seed = p["seed"]
    primary = p["primary"]
    secondary = p["secondary"]
    accent = p["accent"]
    variant = _variant(seed, 4, 3)
    cx, cy = 600, 370

    if variant == 0:
        # Nested orbital paths all follow the same rotational logic.
        _arc(
            draw,
            (cx - 218, cy - 175, cx + 218, cy + 175),
            205,
            510,
            primary,
            42,
        )
        _arc(
            draw,
            (cx - 166, cy - 128, cx + 166, cy + 128),
            28,
            330,
            secondary,
            38,
        )
        _arc(
            draw,
            (cx - 104, cy - 78, cx + 104, cy + 78),
            205,
            505,
            accent,
            28,
        )
        _ellipse(
            draw,
            (cx + 154, cy - 128, cx + 204, cy - 78),
            fill=accent,
        )

    elif variant == 1:
        # Three parallel Bezier bands create one directional flow instead of
        # unrelated crossing strokes.
        paths = [
            (
                [
                    (cx - 225, cy + 78),
                    (cx - 80, cy - 158),
                    (cx + 95, cy + 40),
                    (cx + 220, cy - 100),
                ],
                primary,
                48,
            ),
            (
                [
                    (cx - 215, cy + 135),
                    (cx - 60, cy - 90),
                    (cx + 105, cy + 105),
                    (cx + 225, cy - 35),
                ],
                secondary,
                42,
            ),
            (
                [
                    (cx - 180, cy + 182),
                    (cx - 35, cy + 2),
                    (cx + 115, cy + 152),
                    (cx + 195, cy + 55),
                ],
                accent,
                28,
            ),
        ]
        for points, color, width in paths:
            _smooth_polyline(draw, points, color, width)

    else:
        # Continuous spiral/orbit motif with a distinct destination node.
        _arc(
            draw,
            (cx - 220, cy - 205, cx + 220, cy + 205),
            168,
            468,
            primary,
            46,
        )
        _arc(
            draw,
            (cx - 157, cy - 145, cx + 157, cy + 145),
            348,
            655,
            secondary,
            38,
        )
        _arc(
            draw,
            (cx - 91, cy - 82, cx + 91, cy + 82),
            165,
            465,
            accent,
            28,
        )
        _ellipse(
            draw,
            (cx + 154, cy + 73, cx + 210, cy + 129),
            fill=accent,
        )


def _smooth_polyline(draw, points, color, width):
    if len(points) < 4:
        _line(draw, points, color, width)
        return

    p0, p1, p2, p3 = points[:4]
    samples = []
    for i in range(41):
        t = i / 40
        one = 1 - t
        x = (
            one**3 * p0[0]
            + 3 * one**2 * t * p1[0]
            + 3 * one * t**2 * p2[0]
            + t**3 * p3[0]
        )
        y = (
            one**3 * p0[1]
            + 3 * one**2 * t * p1[1]
            + 3 * one * t**2 * p2[1]
            + t**3 * p3[1]
        )
        samples.append((x, y))

    _line(draw, samples, color, width)
    radius = width / 2
    for x, y in (samples[0], samples[-1]):
        _ellipse(
            draw,
            (x - radius, y - radius, x + radius, y + radius),
            fill=color,
        )


def _draw_wordmark(canvas, p, business_name):
    draw = _work_draw(canvas)
    seed = p["seed"]
    primary = p["primary"]
    secondary = p["secondary"]
    accent = p["accent"]
    style = p["font_style"]
    variant = _variant(seed, 5, 3)

    name = str(business_name or "BRAND").strip()
    font = _fit_font(
        draw,
        name,
        _scaled(1000),
        _scaled(152),
        _scaled(74),
        style,
    )
    box = draw.textbbox((0, 0), name, font=font)
    width = box[2] - box[0]
    x = (WORK_WIDTH - width) // 2
    y = _scaled(315)

    draw.text((x, y), name, font=font, fill=primary)

    if variant == 0:
        _rectangle(
            draw,
            (350, 515, 850, 533),
            fill=secondary,
            radius=9,
        )
        _rectangle(
            draw,
            (535, 515, 665, 533),
            fill=accent,
            radius=9,
        )
    elif variant == 1:
        _ellipse(draw, (392, 507, 426, 541), fill=accent)
        _rectangle(
            draw,
            (445, 516, 808, 532),
            fill=secondary,
            radius=8,
        )
    else:
        _polygon(
            draw,
            [(448, 527), (478, 501), (508, 527), (478, 553)],
            accent,
        )
        _rectangle(
            draw,
            (526, 518, 760, 534),
            fill=secondary,
            radius=8,
        )


def _draw_emblem(canvas, p, business_name):
    draw = _work_draw(canvas)
    seed = p["seed"]
    primary = p["primary"]
    secondary = p["secondary"]
    accent = p["accent"]
    style = p["font_style"]
    mark = initials(business_name)
    variant = _variant(seed, 6, 3)
    cx, cy = 600, 370

    if variant == 0:
        outer = polygon_points(cx, cy, 230, 6, -90)
        inner = polygon_points(cx, cy, 190, 6, -90)
        _polygon(draw, outer, primary)
        _polygon(draw, inner, BACKGROUND)

        # Side divisions stop before the central identity field.
        _line(draw, [(cx - 174, cy), (cx - 122, cy)], secondary, 18)
        _line(draw, [(cx + 122, cy), (cx + 174, cy)], secondary, 18)

        _ellipse(
            draw,
            (cx - 121, cy - 121, cx + 121, cy + 121),
            outline=secondary,
            width=16,
        )

    elif variant == 1:
        _ellipse(
            draw,
            (cx - 225, cy - 225, cx + 225, cy + 225),
            fill=primary,
        )
        _ellipse(
            draw,
            (cx - 190, cy - 190, cx + 190, cy + 190),
            fill=BACKGROUND,
        )
        _ellipse(
            draw,
            (cx - 128, cy - 128, cx + 128, cy + 128),
            outline=secondary,
            width=17,
        )

        for angle in (-90, 90):
            rad = math.radians(angle)
            x = cx + math.cos(rad) * 164
            y = cy + math.sin(rad) * 164
            _ellipse(
                draw,
                (x - 17, y - 17, x + 17, y + 17),
                fill=accent,
            )

    else:
        shield = [
            (cx, cy - 225),
            (cx + 188, cy - 145),
            (cx + 155, cy + 105),
            (cx, cy + 222),
            (cx - 155, cy + 105),
            (cx - 188, cy - 145),
        ]
        inner = [
            (cx, cy - 180),
            (cx + 145, cy - 118),
            (cx + 117, cy + 78),
            (cx, cy + 170),
            (cx - 117, cy + 78),
            (cx - 145, cy - 118),
        ]
        _polygon(draw, shield, primary)
        _polygon(draw, inner, BACKGROUND)

        # Architectural side rails frame rather than strike through the mark.
        _line(
            draw,
            [(cx - 128, cy - 92), (cx - 92, cy + 92)],
            secondary,
            18,
        )
        _line(
            draw,
            [(cx + 128, cy - 92), (cx + 92, cy + 92)],
            secondary,
            18,
        )

    font = get_font(_scaled(124), style)
    box = draw.textbbox((0, 0), mark, font=font)
    tw = box[2] - box[0]

    draw.text(
        (_scaled(cx) - tw // 2, _scaled(cy - 78)),
        mark,
        font=font,
        fill=primary,
    )

    if variant == 2:
        _polygon(
            draw,
            [
                (cx, cy + 126),
                (cx + 27, cy + 153),
                (cx, cy + 180),
                (cx - 27, cy + 153),
            ],
            accent,
        )
    else:
        _ellipse(
            draw,
            (cx - 22, cy + 137, cx + 22, cy + 181),
            fill=accent,
        )


def _draw_local_typography(
    canvas,
    business_name,
    industry,
    specification,
    parameters,
):
    # Wordmark construction already contains the one allowed primary name.
    # It receives only the descriptor below, avoiding the previous duplicated
    # LUMINAGRID / LUMINAGRID problem.
    draw = _work_draw(canvas)
    direction = parameters["direction"]
    style = parameters["font_style"]
    primary = parameters["primary"]
    secondary = parameters["secondary"]

    business_name = str(business_name or "Brand").strip()
    industry = str(industry or "").strip()

    if direction != "wordmark":
        font = _fit_font(
            draw,
            business_name,
            _scaled(1000),
            _scaled(108),
            _scaled(54),
            style,
        )
        width, _ = text_size(draw, business_name, font)
        draw.text(
            ((WORK_WIDTH - width) // 2, _scaled(690)),
            business_name,
            font=font,
            fill=primary,
        )
        descriptor_y = 830
    else:
        descriptor_y = 625

    if industry:
        descriptor = industry.upper()
        descriptor_font = _fit_font(
            draw,
            descriptor,
            _scaled(840),
            _scaled(38),
            _scaled(25),
            style,
            regular=True,
        )
        width, _ = text_size(draw, descriptor, descriptor_font)
        draw.text(
            ((WORK_WIDTH - width) // 2, _scaled(descriptor_y)),
            descriptor,
            font=descriptor_font,
            fill=secondary,
        )

        # Small restrained divider strengthens the lockup without decoration.
        line_width = min(230, max(90, width // (SCALE * 3)))
        y = descriptor_y + 70
        _rectangle(
            draw,
            (600 - line_width / 2, y, 600 + line_width / 2, y + 5),
            fill=parameters["accent"],
            radius=2,
        )


def draw_brand_typography(
    canvas,
    business_name,
    industry,
    specification,
):
    """
    Deterministic 1200x1200 typography used by the cloud compositor.

    This intentionally remains independent of cloud-generated text so provider
    artwork can stay symbol-only while the exact business name is rendered
    locally.
    """
    specification = specification or {}
    p = build_parameters(specification)
    draw = ImageDraw.Draw(canvas)

    business_name = str(business_name or "Brand").strip()
    industry = str(industry or "").strip()
    style = p["font_style"]

    name_font = fit_name_font(
        draw,
        business_name,
        max_width=980,
        start_size=106,
        minimum=50,
        style=style,
    )
    name_width, _ = text_size(draw, business_name, name_font)
    draw.text(
        ((WIDTH - name_width) // 2, 705),
        business_name,
        font=name_font,
        fill=p["primary"],
    )

    if industry:
        industry_text = industry.upper()
        industry_font = _fit_font(
            draw,
            industry_text,
            820,
            34,
            22,
            style,
            regular=True,
        )
        industry_width, _ = text_size(
            draw,
            industry_text,
            industry_font,
        )
        draw.text(
            ((WIDTH - industry_width) // 2, 830),
            industry_text,
            font=industry_font,
            fill=p["secondary"],
        )

        draw.rounded_rectangle(
            (505, 895, 695, 900),
            radius=2,
            fill=p["accent"],
        )


def _prepare_cloud_symbol(cloud_image_bytes: bytes):
    if not cloud_image_bytes:
        raise ValueError("Cloud symbol image is empty.")

    with Image.open(BytesIO(cloud_image_bytes)) as source:
        image = ImageOps.exif_transpose(source).convert("RGBA")

    # Composite transparency against white. This preserves provider artwork
    # without watermark removal, inpainting, cropping tricks, or modification
    # intended to conceal provider branding.
    white = Image.new("RGBA", image.size, "white")
    white.alpha_composite(image)
    image = white.convert("RGB")

    # Keep the complete artwork in a square symbol area.
    side = max(image.width, image.height)
    square = Image.new("RGB", (side, side), BACKGROUND)
    x = (side - image.width) // 2
    y = (side - image.height) // 2
    square.paste(image, (x, y))
    return square


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


def _svg_text(value: str) -> str:
    return html.escape(str(value or ""), quote=True)


def _svg_symbol(business_name: str, p: dict) -> str:
    """
    Produce a valid, deterministic vector representation of the same
    construction family. PNG is the authoritative production renderer, while
    SVG remains available for compatibility/export.
    """
    direction = p["direction"]
    primary = p["primary"]
    secondary = p["secondary"]
    accent = p["accent"]
    seed = p["seed"]
    mark = _svg_text(initials(business_name))

    if direction == "negative-space":
        variant = _variant(seed, 2, 3)
        if variant == 1:
            base = (
                '<polygon points="600,152 789,261 789,479 600,588 '
                '411,479 411,261" fill="{p}"/>'
            ).format(p=primary)
            cut = (
                '<rect x="542" y="150" width="116" height="305" rx="30" '
                'fill="white"/><rect x="540" y="390" width="240" height="80" '
                'fill="white"/>'
            )
        elif variant == 2:
            base = (
                '<rect x="395" y="195" width="410" height="350" rx="84" '
                'fill="{p}"/>'
            ).format(p=primary)
            cut = (
                '<circle cx="600" cy="370" r="92" fill="white"/>'
                '<path d="M595 195 H805 V325 L672 395 Z" fill="white"/>'
            )
        else:
            base = (
                '<ellipse cx="600" cy="370" rx="210" ry="190" fill="{p}"/>'
            ).format(p=primary)
            cut = (
                '<path d="M505 480 L615 252 L718 480 H654 L610 388 '
                'L560 480 Z" fill="white"/>'
            )
        return base + cut + (
            f'<circle cx="755" cy="240" r="25" fill="{accent}"/>'
        )

    if direction == "monogram":
        return (
            f'<rect x="395" y="180" width="410" height="380" rx="56" '
            f'fill="none" stroke="{primary}" stroke-width="18"/>'
            f'<text x="600" y="430" text-anchor="middle" '
            f'font-family="Arial, sans-serif" font-size="190" '
            f'font-weight="700" fill="{secondary}">{mark}</text>'
            f'<rect x="565" y="515" width="70" height="24" rx="12" '
            f'fill="{accent}"/>'
        )

    if direction == "abstract-motion":
        return (
            f'<path d="M390 430 C470 180 650 175 790 270" fill="none" '
            f'stroke="{primary}" stroke-width="48" stroke-linecap="round"/>'
            f'<path d="M390 350 C500 520 670 490 810 355" fill="none" '
            f'stroke="{secondary}" stroke-width="42" stroke-linecap="round"/>'
            f'<path d="M420 245 C530 345 665 345 775 485" fill="none" '
            f'stroke="{accent}" stroke-width="30" stroke-linecap="round"/>'
        )

    if direction == "wordmark":
        name = _svg_text(business_name)
        return (
            f'<text x="600" y="455" text-anchor="middle" '
            f'font-family="Arial, sans-serif" font-size="145" '
            f'font-weight="700" fill="{primary}">{name}</text>'
            f'<rect x="420" y="515" width="360" height="18" rx="9" '
            f'fill="{secondary}"/>'
            f'<rect x="550" y="515" width="100" height="18" rx="9" '
            f'fill="{accent}"/>'
        )

    if direction == "brand-emblem":
        points = svg_points(polygon_points(600, 370, 225, 6, -90))
        inner = svg_points(polygon_points(600, 370, 185, 6, -90))
        return (
            f'<polygon points="{points}" fill="{primary}"/>'
            f'<polygon points="{inner}" fill="white"/>'
            f'<circle cx="600" cy="370" r="120" fill="none" '
            f'stroke="{secondary}" stroke-width="18"/>'
            f'<text x="600" y="410" text-anchor="middle" '
            f'font-family="Arial, sans-serif" font-size="110" '
            f'font-weight="700" fill="{primary}">{mark}</text>'
            f'<circle cx="600" cy="525" r="22" fill="{accent}"/>'
        )

    # minimal-geometric
    variant = _variant(seed, 0, 4)
    if variant == 2:
        return (
            f'<path d="M455 265 L605 195 L750 290 L735 475 L590 545 '
            f'L445 455 Z" fill="none" stroke="{primary}" stroke-width="28"/>'
            f'<path d="M455 265 L735 475 M605 195 L590 545" '
            f'stroke="{secondary}" stroke-width="24"/>'
            f'<circle cx="605" cy="195" r="28" fill="{accent}"/>'
            f'<circle cx="735" cy="475" r="28" fill="{accent}"/>'
        )

    points = svg_points(polygon_points(600, 370, 218, 6, -90))
    inner = svg_points(polygon_points(600, 370, 112, 6, -60))
    return (
        f'<polygon points="{points}" fill="{primary}"/>'
        f'<polygon points="{inner}" fill="white"/>'
        f'<circle cx="600" cy="370" r="22" fill="{accent}"/>'
    )


def render_svg(
    business_name: str,
    industry: str,
    specification: dict,
    parameters: dict | None = None,
) -> str:
    p = parameters or build_parameters(specification)
    direction = p["direction"]

    symbol = _svg_symbol(business_name, p)
    name = _svg_text(business_name)
    industry_text = _svg_text(str(industry or "").upper())

    if direction == "wordmark":
        name_markup = ""
        industry_y = 625
    else:
        name_markup = (
            f'<text x="600" y="780" text-anchor="middle" '
            f'font-family="Arial, sans-serif" font-size="92" '
            f'font-weight="700" fill="{p["primary"]}">{name}</text>'
        )
        industry_y = 855

    industry_markup = ""
    if industry_text:
        industry_markup = (
            f'<text x="600" y="{industry_y}" text-anchor="middle" '
            f'font-family="Arial, sans-serif" font-size="32" '
            f'letter-spacing="2" fill="{p["secondary"]}">'
            f'{industry_text}</text>'
            f'<rect x="505" y="{industry_y + 45}" width="190" height="5" '
            f'rx="2" fill="{p["accent"]}"/>'
        )

    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<svg xmlns="http://www.w3.org/2000/svg" '
        'width="1200" height="1200" viewBox="0 0 1200 1200">'
        '<rect width="1200" height="1200" fill="#FFFFFF"/>'
        f'{symbol}{name_markup}{industry_markup}</svg>'
    )



def _hex_rgb(color: str) -> tuple[int, int, int]:
    color = safe_color(color, DEFAULT_PRIMARY).lstrip("#")
    return tuple(int(color[i:i + 2], 16) for i in (0, 2, 4))


def _mix_rgb(a, b, amount: float):
    amount = max(0.0, min(1.0, amount))
    return tuple(
        round(a[i] + (b[i] - a[i]) * amount)
        for i in range(3)
    )


def _premium_gradient(size, colors, horizontal=False):
    width, height = size
    result = Image.new("RGB", size)
    pixels = result.load()

    rgb = [_hex_rgb(color) for color in colors]

    for index in range(width if horizontal else height):
        t = index / max(1, (width if horizontal else height) - 1)

        if len(rgb) >= 3:
            if t <= 0.5:
                color = _mix_rgb(rgb[0], rgb[1], t * 2)
            else:
                color = _mix_rgb(rgb[1], rgb[2], (t - 0.5) * 2)
        else:
            color = _mix_rgb(rgb[0], rgb[-1], t)

        if horizontal:
            for y in range(height):
                pixels[index, y] = color
        else:
            for x in range(width):
                pixels[x, index] = color

    return result


def _premium_background(parameters):
    if parameters["background_mode"] == "dark":
        primary = _hex_rgb(parameters["primary"])
        dark = tuple(max(5, int(channel * 0.12)) for channel in primary)
        return dark
    return (255, 255, 255)


def _premium_ink(parameters):
    if parameters["background_mode"] == "dark":
        return "#F8FAFC"
    return parameters["primary"]


def _paste_gradient_mask(canvas, mask, parameters, horizontal=False):
    gradient = _premium_gradient(
        canvas.size,
        [
            parameters["primary"],
            parameters["secondary"],
            parameters["accent"],
        ],
        horizontal=horizontal,
    )
    canvas.paste(gradient, (0, 0), mask)


def _premium_ribbon_symbol(canvas, parameters, business_name, box):
    x0, y0, x1, y1 = box
    cx = (x0 + x1) / 2
    cy = (y0 + y1) / 2
    width = x1 - x0
    height = y1 - y0

    # Premium folded ribbon constructed from two coherent bands.
    # The crossing remains open and readable rather than producing
    # an accidental dark diamond at the intersection.
    mask_back = Image.new("L", canvas.size, 0)
    mask_front = Image.new("L", canvas.size, 0)

    back = ImageDraw.Draw(mask_back)
    front = ImageDraw.Draw(mask_front)

    band = height * 0.16

    # Rising left-to-right rear band.
    rear_points = [
        (cx - width * 0.34, cy + height * 0.24),
        (cx - width * 0.22, cy - height * 0.28),
        (cx - width * 0.10, cy - height * 0.32),
        (cx + width * 0.09, cy + height * 0.10),
        (cx + width * 0.28, cy - height * 0.25),
        (cx + width * 0.39, cy - height * 0.13),
        (cx + width * 0.08, cy + height * 0.30),
        (cx - width * 0.02, cy + height * 0.27),
        (cx - width * 0.18, cy - height * 0.08),
        (cx - width * 0.25, cy + height * 0.28),
    ]

    back.polygon(
        [(int(x), int(y)) for x, y in rear_points],
        fill=255,
    )

    # Forward fold creates a flowing monogram-like terminal.
    front_points = [
        (cx - width * 0.08, cy - height * 0.10),
        (cx + width * 0.11, cy - height * 0.31),
        (cx + width * 0.32, cy - height * 0.16),
        (cx + width * 0.20, cy - height * 0.06),
        (cx + width * 0.10, cy + height * 0.04),
        (cx + width * 0.25, cy + height * 0.24),
        (cx + width * 0.15, cy + height * 0.30),
        (cx - width * 0.05, cy + height * 0.08),
    ]

    front.polygon(
        [(int(x), int(y)) for x, y in front_points],
        fill=255,
    )

    # Back band: primary -> secondary.
    rear_gradient = _premium_gradient(
        canvas.size,
        [
            parameters["primary"],
            parameters["secondary"],
        ],
        horizontal=True,
    )
    canvas.paste(
        rear_gradient,
        (0, 0),
        mask_back,
    )

    # Front band: secondary -> accent. This creates the fold
    # using palette hierarchy rather than artificial shadowing.
    front_gradient = _premium_gradient(
        canvas.size,
        [
            parameters["secondary"],
            parameters["accent"],
        ],
        horizontal=True,
    )
    canvas.paste(
        front_gradient,
        (0, 0),
        mask_front,
    )

    # Small highlight facet at the fold, intentionally narrow.
    draw = ImageDraw.Draw(canvas)
    fold = [
        (cx - width * 0.055, cy - height * 0.085),
        (cx + width * 0.035, cy + height * 0.025),
        (cx - width * 0.010, cy + height * 0.095),
        (cx - width * 0.095, cy - height * 0.005),
    ]

    draw.polygon(
        [(int(x), int(y)) for x, y in fold],
        fill=parameters["secondary"],
    )

    if parameters["complexity"] >= 2:
        spark_x = cx + width * 0.34
        spark_y = cy - height * 0.34
        r = min(width, height) * 0.034

        spark = [
            (spark_x, spark_y - r * 1.55),
            (spark_x + r * 0.40, spark_y - r * 0.40),
            (spark_x + r * 1.55, spark_y),
            (spark_x + r * 0.40, spark_y + r * 0.40),
            (spark_x, spark_y + r * 1.55),
            (spark_x - r * 0.40, spark_y + r * 0.40),
            (spark_x - r * 1.55, spark_y),
            (spark_x - r * 0.40, spark_y - r * 0.40),
        ]

        draw.polygon(
            [(int(x), int(y)) for x, y in spark],
            fill=parameters["accent"],
        )


def _premium_fused_lettermark(canvas, parameters, business_name, box):
    x0, y0, x1, y1 = box
    cx = int((x0 + x1) / 2)
    cy = int((y0 + y1) / 2)
    letters = initials(business_name)

    font = get_font(
        int(min(x1 - x0, y1 - y0) * 0.48),
        parameters["font_style"],
    )

    mask = Image.new("L", canvas.size, 0)
    draw = ImageDraw.Draw(mask)

    bbox = draw.textbbox((0, 0), letters, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]

    draw.text(
        (cx - tw // 2, cy - th // 2 - bbox[1]),
        letters,
        font=font,
        fill=255,
    )

    # Structural fusion bar turns the initials into a single mark.
    bar_y = cy + int((y1 - y0) * 0.22)
    draw.rounded_rectangle(
        (
            int(x0 + (x1 - x0) * 0.19),
            bar_y,
            int(x1 - (x1 - x0) * 0.19),
            bar_y + max(16, int((y1 - y0) * 0.055)),
        ),
        radius=12,
        fill=255,
    )

    _paste_gradient_mask(canvas, mask, parameters, horizontal=True)


def _premium_orbital_symbol(canvas, parameters, box):
    x0, y0, x1, y1 = box
    draw = ImageDraw.Draw(canvas)

    cx = (x0 + x1) / 2
    cy = (y0 + y1) / 2
    width = x1 - x0
    height = y1 - y0

    colors = [
        parameters["primary"],
        parameters["secondary"],
        parameters["accent"],
    ]

    for index, color in enumerate(colors):
        inset_x = width * (0.07 + index * 0.11)
        inset_y = height * (0.13 + index * 0.10)

        draw.arc(
            (
                int(x0 + inset_x),
                int(y0 + inset_y),
                int(x1 - inset_x),
                int(y1 - inset_y),
            ),
            start=195 + index * 24,
            end=505 + index * 17,
            fill=color,
            width=max(18, int(min(width, height) * (0.085 - index * 0.012))),
        )

    radius = max(12, int(min(width, height) * 0.045))
    draw.ellipse(
        (
            int(cx + width * 0.30 - radius),
            int(cy - height * 0.23 - radius),
            int(cx + width * 0.30 + radius),
            int(cy - height * 0.23 + radius),
        ),
        fill=parameters["accent"],
    )


def _premium_network_symbol(canvas, parameters, box):
    x0, y0, x1, y1 = box
    cx = (x0 + x1) / 2
    cy = (y0 + y1) / 2
    radius = min(x1 - x0, y1 - y0) * 0.37

    mask = Image.new("L", canvas.size, 0)
    draw = ImageDraw.Draw(mask)

    points = polygon_points(cx, cy, radius, 6, -90)

    stroke = max(16, int(radius * 0.12))

    for i in range(6):
        draw.line(
            [points[i], points[(i + 1) % 6]],
            fill=255,
            width=stroke,
        )

    for index in (0, 2, 4):
        draw.line(
            [points[index], (cx, cy)],
            fill=255,
            width=max(12, stroke - 5),
        )

    node_radius = max(18, int(radius * 0.11))
    for px, py in points:
        draw.ellipse(
            (
                int(px - node_radius),
                int(py - node_radius),
                int(px + node_radius),
                int(py + node_radius),
            ),
            fill=255,
        )

    _paste_gradient_mask(canvas, mask, parameters, horizontal=True)


def _premium_emblem_symbol(canvas, parameters, business_name, box):
    x0, y0, x1, y1 = box
    cx = (x0 + x1) / 2
    cy = (y0 + y1) / 2
    radius = min(x1 - x0, y1 - y0) * 0.40

    draw = ImageDraw.Draw(canvas)

    points = polygon_points(cx, cy, radius, 6, -90)
    inner = polygon_points(cx, cy, radius * 0.84, 6, -90)

    mask = Image.new("L", canvas.size, 0)
    md = ImageDraw.Draw(mask)
    md.polygon(points, fill=255)
    md.polygon(inner, fill=0)

    _paste_gradient_mask(canvas, mask, parameters, horizontal=True)

    font = get_font(
        int(radius * 0.65),
        parameters["font_style"],
    )
    mark = initials(business_name)
    bbox = draw.textbbox((0, 0), mark, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]

    draw.text(
        (
            int(cx - tw / 2),
            int(cy - th / 2 - bbox[1]),
        ),
        mark,
        font=font,
        fill=_premium_ink(parameters),
    )

    accent_radius = max(9, int(radius * 0.065))
    draw.ellipse(
        (
            int(cx - accent_radius),
            int(cy + radius * 0.63 - accent_radius),
            int(cx + accent_radius),
            int(cy + radius * 0.63 + accent_radius),
        ),
        fill=parameters["accent"],
    )


def _draw_premium_symbol(canvas, parameters, business_name, box):
    family = parameters["symbol_family"]

    if family == "ribbon-monogram":
        _premium_ribbon_symbol(
            canvas,
            parameters,
            business_name,
            box,
        )
    elif family == "fused-lettermark":
        _premium_fused_lettermark(
            canvas,
            parameters,
            business_name,
            box,
        )
    elif family == "orbital-motion":
        _premium_orbital_symbol(
            canvas,
            parameters,
            box,
        )
    elif family == "structured-emblem":
        _premium_emblem_symbol(
            canvas,
            parameters,
            business_name,
            box,
        )
    elif family == "negative-space":
        # V2.1 already has the genuine mask-based negative-space system.
        # Render that system into a transparent-sized temporary composition
        # rather than replacing it with a fake white overlay.
        temporary = Image.new(
            "RGB",
            canvas.size,
            _premium_background(parameters),
        )
        _draw_negative_space(temporary, parameters)
        canvas.paste(temporary)
    else:
        _premium_network_symbol(
            canvas,
            parameters,
            box,
        )


def _split_wordmark(name: str):
    name = str(name or "").strip()

    if not name:
        return "", ""

    # Prefer a real CamelCase boundary.
    parts = re.findall(
        r"[A-Z]+(?=[A-Z][a-z]|\d|\b)|[A-Z]?[a-z]+|\d+",
        name,
    )

    if len(parts) >= 2:
        first = "".join(parts[:-1])
        second = parts[-1]
        return first, second

    # For multiword brands keep the final word as the emphasis.
    words = name.split()
    if len(words) >= 2:
        return " ".join(words[:-1]) + " ", words[-1]

    # Do not arbitrarily split short names.
    if len(name) < 7:
        return name, ""

    split_at = max(3, len(name) // 2)
    return name[:split_at], name[split_at:]


def _draw_premium_wordmark(
    canvas,
    parameters,
    business_name,
    industry,
    position,
    max_width,
    stacked=True,
):
    draw = ImageDraw.Draw(canvas)

    name = str(business_name or "Brand").strip()
    style = parameters["font_style"]
    ink = _premium_ink(parameters)

    start_size = 158 if stacked else 120
    minimum = 70 if stacked else 48

    font = _fit_font(
        draw,
        name,
        max_width,
        start_size,
        minimum,
        style,
    )

    emphasis = parameters["wordmark_emphasis"]

    # Measure using one common baseline/bounding box.
    full_box = draw.textbbox(
        (0, 0),
        name,
        font=font,
    )
    name_height = full_box[3] - full_box[1]

    if emphasis == "single":
        tw = full_box[2] - full_box[0]
        name_x = position[0] - tw // 2

        draw.text(
            (name_x, position[1]),
            name,
            font=font,
            fill=ink,
        )

    else:
        first, second = _split_wordmark(name)

        first_box = draw.textbbox(
            (0, 0),
            first,
            font=font,
        )
        second_box = draw.textbbox(
            (0, 0),
            second,
            font=font,
        )

        w1 = first_box[2] - first_box[0]
        w2 = second_box[2] - second_box[0]
        total = w1 + w2
        x = position[0] - total // 2

        draw.text(
            (x, position[1]),
            first,
            font=font,
            fill=ink,
        )

        if second:
            emphasis_color = (
                parameters["accent"]
                if emphasis == "accent-terminal"
                else parameters["secondary"]
            )

            draw.text(
                (x + w1, position[1]),
                second,
                font=font,
                fill=emphasis_color,
            )

    if not industry:
        return

    # Descriptor spacing is derived from the actual wordmark metrics.
    # This prevents collision with descenders/large fonts.
    descriptor = str(industry).upper()

    descriptor_font = _fit_font(
        draw,
        descriptor,
        int(max_width * 0.82),
        25 if stacked else 23,
        17,
        style,
        regular=True,
    )

    descriptor_box = draw.textbbox(
        (0, 0),
        descriptor,
        font=descriptor_font,
    )
    descriptor_width = descriptor_box[2] - descriptor_box[0]

    gap = 46 if stacked else 38

    descriptor_y = (
        position[1]
        + name_height
        + gap
    )

    descriptor_color = (
        "#CBD5E1"
        if parameters["background_mode"] == "dark"
        else parameters["secondary"]
    )

    draw.text(
        (
            position[0] - descriptor_width // 2,
            descriptor_y,
        ),
        descriptor,
        font=descriptor_font,
        fill=descriptor_color,
    )

    rule_width = min(
        190,
        max(
            80,
            descriptor_width // 4,
        ),
    )

    descriptor_height = (
        descriptor_box[3]
        - descriptor_box[1]
    )

    rule_y = (
        descriptor_y
        + descriptor_height
        + 25
    )

    draw.rounded_rectangle(
        (
            position[0] - rule_width // 2,
            rule_y,
            position[0] + rule_width // 2,
            rule_y + 5,
        ),
        radius=2,
        fill=parameters["accent"],
    )


def _render_premium_png(
    business_name,
    industry,
    specification,
    parameters,
):
    background = _premium_background(parameters)

    canvas = Image.new(
        "RGB",
        (WIDTH, HEIGHT),
        background,
    )

    layout = parameters["layout"]
    horizontal = layout == "symbol-left"

    if horizontal:
        symbol_box = (65, 285, 515, 735)

        _draw_premium_symbol(
            canvas,
            parameters,
            business_name,
            symbol_box,
        )

        _draw_premium_wordmark(
            canvas,
            parameters,
            business_name,
            industry,
            position=(830, 415),
            max_width=675,
            stacked=False,
        )

    else:
        # Increase stacked identity width from ~53% toward a premium
        # 65-75% visual footprint while keeping generous clear space.
        symbol_box = (235, 55, 965, 620)

        _draw_premium_symbol(
            canvas,
            parameters,
            business_name,
            symbol_box,
        )

        _draw_premium_wordmark(
            canvas,
            parameters,
            business_name,
            industry,
            position=(600, 625),
            max_width=1060,
            stacked=True,
        )

    output = BytesIO()

    canvas.save(
        output,
        format="PNG",
        optimize=True,
    )

    result = output.getvalue()

    if len(result) < 1000:
        raise RuntimeError(
            "Premium renderer produced invalid PNG data."
        )

    return result

def render_png(
    business_name: str,
    industry: str,
    specification: dict,
    parameters: dict | None = None,
) -> bytes:
    p = parameters or build_parameters(specification)

    if p.get("treatment") == "premium-gradient":
        try:
            return _render_premium_png(
                business_name,
                industry,
                specification,
                p,
            )
        except Exception as error:
            print(
                "[LOGO RENDERER] Premium rendering failed; "
                "using flat deterministic fallback:",
                repr(error),
            )

    canvas = _new_work_canvas()
    direction = p["direction"]

    if direction == "minimal-geometric":
        _draw_minimal_geometric(canvas, p)
    elif direction == "negative-space":
        _draw_negative_space(canvas, p)
    elif direction == "monogram":
        _draw_monogram(canvas, p, business_name)
    elif direction == "abstract-motion":
        _draw_abstract_motion(canvas, p)
    elif direction == "wordmark":
        _draw_wordmark(canvas, p, business_name)
    elif direction == "brand-emblem":
        _draw_emblem(canvas, p, business_name)
    else:
        _draw_minimal_geometric(canvas, p)

    _draw_local_typography(
        canvas,
        business_name,
        industry,
        specification,
        p,
    )

    canvas = canvas.resize(
        (WIDTH, HEIGHT),
        _resample_lanczos(),
    )

    output = BytesIO()
    canvas.save(
        output,
        format="PNG",
        optimize=True,
    )
    result = output.getvalue()

    if len(result) < 1000:
        raise RuntimeError("Local logo renderer produced invalid PNG data.")

    return result


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
