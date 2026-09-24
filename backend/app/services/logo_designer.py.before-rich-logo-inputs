import json
import random
import uuid

import requests


# =========================================================
# OLLAMA SETTINGS
# =========================================================

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
OLLAMA_MODEL = "qwen2.5:3b"


# =========================================================
# ALLOWED DESIGN VALUES
# =========================================================

LOGO_TYPES = [
    "monogram",
    "lettermark",
    "abstract",
    "geometric",
    "emblem",
    "combination",
    "negative-space",
    "wordmark",
]

SHAPES = [
    "circle",
    "diamond",
    "hexagon",
    "triangle",
    "square",
    "rings",
    "arcs",
    "lines",
    "waves",
    "interlocking",
]

LAYOUTS = [
    "symbol-top",
    "symbol-left",
    "emblem",
    "wordmark",
]

FONT_STYLES = [
    "bold",
    "modern",
    "elegant",
    "minimal",
]

GEOMETRY_STYLES = [
    "sharp",
    "rounded",
    "mixed",
]

SYMMETRY_TYPES = [
    "none",
    "bilateral",
    "radial",
]


# =========================================================
# PROFESSIONAL CREATIVE DIRECTIONS
# =========================================================
#
# IMPORTANT:
# Each direction has a deliberately different structural
# identity. This prevents batches from collapsing into
# repeated polygon logos.
#
# =========================================================

CREATIVE_DIRECTIONS = [
    {
        "name": "minimal-geometric",
        "description": (
            "Create a highly minimal geometric identity with one strong "
            "silhouette. Use one dominant primitive or a disciplined "
            "combination of at most two forms. Prioritize clarity, balance, "
            "recognition and excellent small-size performance."
        ),
        "preferred_types": [
            "geometric",
            "abstract",
        ],
        "preferred_shapes": [
            "hexagon",
            "diamond",
            "square",
        ],
        "preferred_layout": "symbol-top",
    },

    {
        "name": "negative-space",
        "description": (
            "Create a clever negative-space identity where empty space is "
            "an intentional part of the symbol. The hidden visual idea must "
            "connect to the business, service, customer result or initials. "
            "Keep the idea immediately understandable rather than decorative."
        ),
        "preferred_types": [
            "negative-space",
            "combination",
        ],
        "preferred_shapes": [
            "circle",
            "arcs",
            "triangle",
        ],
        "preferred_layout": "symbol-left",
    },

    {
        "name": "monogram",
        "description": (
            "Create a typography-led monogram based on one or two meaningful "
            "initials from the business name. The letters should become the "
            "identity themselves. Keep surrounding geometry secondary and "
            "avoid placing ordinary text inside an unrelated generic shape."
        ),
        "preferred_types": [
            "monogram",
            "lettermark",
        ],
        "preferred_shapes": [
            "lines",
            "square",
            "circle",
        ],
        "preferred_layout": "symbol-top",
    },

    {
        "name": "abstract-motion",
        "description": (
            "Create a distinctive abstract symbol expressing movement, "
            "progress, transformation, momentum or flow. Use a dynamic "
            "silhouette rather than a static badge. Avoid generic arrows "
            "unless movement is fundamental to the business."
        ),
        "preferred_types": [
            "abstract",
            "combination",
        ],
        "preferred_shapes": [
            "waves",
            "arcs",
            "lines",
        ],
        "preferred_layout": "symbol-left",
    },

    {
        "name": "wordmark",
        "description": (
            "Create a typography-first wordmark identity. The company name "
            "must be the main visual asset. Use proportion, spacing, weight "
            "and restrained geometric modifications to make the name feel "
            "distinctive. Do not rely on a large separate icon."
        ),
        "preferred_types": [
            "wordmark",
            "lettermark",
        ],
        "preferred_shapes": [
            "lines",
            "arcs",
            "square",
        ],
        "preferred_layout": "wordmark",
    },

    {
        "name": "brand-emblem",
        "description": (
            "Create a compact emblem or badge with a memorable silhouette. "
            "Integrate symbol and identity into a unified mark suitable for "
            "avatars, packaging, app icons and social profiles. Keep it "
            "modern and simple rather than ornamental."
        ),
        "preferred_types": [
            "emblem",
            "combination",
        ],
        "preferred_shapes": [
            "circle",
            "rings",
            "diamond",
        ],
        "preferred_layout": "emblem",
    },
]


# =========================================================
# FALLBACK PALETTES
# =========================================================

FALLBACK_PALETTES = [
    {
        "primary": "#172554",
        "secondary": "#2563EB",
        "accent": "#60A5FA",
    },
    {
        "primary": "#3B0764",
        "secondary": "#7C3AED",
        "accent": "#C084FC",
    },
    {
        "primary": "#064E3B",
        "secondary": "#059669",
        "accent": "#34D399",
    },
    {
        "primary": "#431407",
        "secondary": "#EA580C",
        "accent": "#FDBA74",
    },
    {
        "primary": "#18181B",
        "secondary": "#52525B",
        "accent": "#A1A1AA",
    },
    {
        "primary": "#164E63",
        "secondary": "#0891B2",
        "accent": "#67E8F9",
    },
]


# =========================================================
# MAIN AI LOGO DESIGNER
# =========================================================

def generate_logo_specification(
    business_name: str,
    industry: str,
    style: str,
    description: str = "",
    direction_index: int | None = None,
) -> dict:

    if direction_index is None:
        direction_index = random.randrange(len(CREATIVE_DIRECTIONS))

    direction_index = direction_index % len(CREATIVE_DIRECTIONS)
    direction = CREATIVE_DIRECTIONS[direction_index]

    generation_id = str(uuid.uuid4())

    prompt = f"""
You are a senior brand identity designer creating a professional
commercial logo system.

Your job is to create ONE vector logo specification.

A deterministic SVG renderer will turn your JSON into artwork.
Therefore describe a design that can actually be constructed from
simple clean vector geometry.

==================================================
BUSINESS
==================================================

Business name:
{business_name}

Industry:
{industry}

Requested style:
{style}

Business description and user preferences:
{description}

==================================================
ASSIGNED CREATIVE DIRECTION
==================================================

Direction:
{direction["name"]}

Objective:
{direction["description"]}

Preferred logo families:
{", ".join(direction["preferred_types"])}

Preferred geometric vocabulary:
{", ".join(direction["preferred_shapes"])}

Preferred layout:
{direction["preferred_layout"]}

Generation ID:
{generation_id}

==================================================
DESIGN THINKING
==================================================

First infer:

1. What does this business actually offer?
2. What should customers feel about it?
3. What is one meaningful idea that could represent that value?
4. How can that idea become a simple recognizable vector mark?

The symbol must have a reason to exist.

Possible conceptual themes include:

- precision
- progress
- confidence
- discovery
- protection
- connection
- transformation
- craftsmanship
- intelligence
- speed
- stability
- simplicity
- growth

Only use a theme when it makes sense for this particular business.

==================================================
DISTINCTIVENESS
==================================================

This logo is part of a batch containing other logo concepts.

This specific concept MUST follow the assigned creative direction.

Do not drift toward a generic technology hexagon.
Do not create arbitrary overlapping polygons.
Do not make every business look like a software startup.
Do not default to blue unless blue genuinely suits the brand.

The logo should be distinguishable from the other concepts even
when viewed only as a black silhouette.

==================================================
TYPOGRAPHY
==================================================

The business name must remain clear and readable.

For monogram and lettermark concepts:
derive the mark from meaningful business initials.

For wordmarks:
the company name is the dominant design element.

For geometric or abstract concepts:
the symbol should complement the wordmark rather than overwhelm it.

Do not use extremely thin or low-contrast lettering.

==================================================
VECTOR PRODUCTION RULES
==================================================

The design must:

- work as clean SVG
- scale to small sizes
- have a recognizable silhouette
- remain meaningful in one color
- use simple vector-friendly geometry
- contain limited visual detail
- use no more than three brand colors
- maintain strong foreground/background contrast
- work on a white background

Never use:

- photography
- realistic images
- humans
- mascots
- 3D effects
- gradients
- shadows
- glow
- glass effects
- metallic effects
- texture
- stock-logo clichés
- tiny decorative details
- generic AI brain graphics
- generic network-node graphics
- meaningless polygon clusters

==================================================
ALLOWED VALUES
==================================================

logo_type:
{", ".join(LOGO_TYPES)}

shape:
{", ".join(SHAPES)}

layout:
{", ".join(LAYOUTS)}

font_style:
{", ".join(FONT_STYLES)}

geometry_style:
{", ".join(GEOMETRY_STYLES)}

symmetry:
{", ".join(SYMMETRY_TYPES)}

==================================================
COLOR STRATEGY
==================================================

Choose colors for THIS business.

Consider:

- industry
- requested style
- audience
- emotional tone
- positioning
- readability

The primary color should carry most of the identity.

The secondary and accent colors must complement the primary color.

Avoid three colors with nearly identical brightness.

Avoid very pale primary colors because the logo is displayed
on a white background.

Do not automatically select blue for technology businesses.

==================================================
OUTPUT
==================================================

Return valid JSON ONLY.

Use exactly this schema:

{{
    "logo_type": "<allowed value>",
    "shape": "<allowed value>",
    "layout": "<allowed value>",
    "font_style": "<allowed value>",

    "visual_metaphor": "<specific business-related visual idea>",

    "composition": "<clear description of geometry arrangement>",

    "geometry_style": "<sharp, rounded, or mixed>",
    "symmetry": "<none, bilateral, or radial>",

    "complexity": <1, 2, or 3>,

    "primary_color": "<6-digit HEX>",
    "secondary_color": "<6-digit HEX>",
    "accent_color": "<6-digit HEX>",

    "rotation": <integer 0-180>,
    "layers": <integer 1-4>,
    "stroke_width": <integer 8-35>,

    "concept": "<one concise explanation connecting design to business>"
}}

==================================================
FINAL RULES
==================================================

Return JSON only.
Do not return Markdown.
Do not explain the JSON.

Follow the assigned creative direction.

Prefer:
{", ".join(direction["preferred_types"])}

Prefer geometry from:
{", ".join(direction["preferred_shapes"])}

Prefer layout:
{direction["preferred_layout"]}

Use meaningful business-specific symbolism.

Every HEX value must contain exactly six hexadecimal digits.

complexity must be 1, 2, or 3.
rotation must be 0 through 180.
layers must be 1 through 4.
stroke_width must be 8 through 35.
"""

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "format": "json",
                "options": {
                    "temperature": 0.78,
                    "seed": random.randint(1, 2_000_000_000),
                },
            },
            timeout=120,
        )

        response.raise_for_status()

        result = response.json()
        raw_response = result.get("response", "{}")

        specification = json.loads(raw_response)

    except Exception as error:
        print("Logo designer AI error:", repr(error))
        specification = {}

    return sanitize_specification(
        specification=specification,
        direction=direction,
        direction_index=direction_index,
    )


# =========================================================
# SANITIZE AI OUTPUT
# =========================================================

def sanitize_specification(
    specification: dict,
    direction: dict,
    direction_index: int,
) -> dict:

    if not isinstance(specification, dict):
        specification = {}

    # -----------------------------------------------------
    # LOGO TYPE
    # -----------------------------------------------------

    preferred_types = direction["preferred_types"]

    logo_type = specification.get(
        "logo_type",
        preferred_types[0],
    )

    if logo_type not in LOGO_TYPES:
        logo_type = preferred_types[0]

    if logo_type not in preferred_types:
        logo_type = preferred_types[0]

    # -----------------------------------------------------
    # SHAPE
    # -----------------------------------------------------

    preferred_shapes = direction["preferred_shapes"]

    shape = specification.get(
        "shape",
        preferred_shapes[0],
    )

    if shape not in SHAPES:
        shape = preferred_shapes[0]

    if shape not in preferred_shapes:
        shape = preferred_shapes[0]

    # -----------------------------------------------------
    # LAYOUT
    # -----------------------------------------------------

    preferred_layout = direction["preferred_layout"]

    layout = specification.get(
        "layout",
        preferred_layout,
    )

    if layout not in LAYOUTS:
        layout = preferred_layout

    # Keep strongly structured directions structurally distinct.
    if logo_type == "wordmark":
        layout = "wordmark"
    elif logo_type == "emblem":
        layout = "emblem"
    elif direction["name"] in {"negative-space", "abstract-motion"}:
        layout = preferred_layout

    # -----------------------------------------------------
    # FONT
    # -----------------------------------------------------

    font_style = specification.get(
        "font_style",
        "modern",
    )

    if font_style not in FONT_STYLES:
        font_style = "modern"

    # -----------------------------------------------------
    # GEOMETRY
    # -----------------------------------------------------

    geometry_style = specification.get(
        "geometry_style",
        "rounded",
    )

    if geometry_style not in GEOMETRY_STYLES:
        geometry_style = "rounded"

    symmetry = specification.get(
        "symmetry",
        "bilateral",
    )

    if symmetry not in SYMMETRY_TYPES:
        symmetry = "bilateral"

    # -----------------------------------------------------
    # COLORS
    # -----------------------------------------------------

    palette = FALLBACK_PALETTES[
        direction_index % len(FALLBACK_PALETTES)
    ]

    primary = clean_hex(
        specification.get("primary_color"),
        palette["primary"],
    )

    secondary = clean_hex(
        specification.get("secondary_color"),
        palette["secondary"],
    )

    accent = clean_hex(
        specification.get("accent_color"),
        palette["accent"],
    )

    # Prevent invisible/pale primary marks on white.
    if is_too_light(primary):
        primary = palette["primary"]

    if primary == secondary:
        secondary = palette["secondary"]

    if secondary == accent:
        accent = palette["accent"]

    # -----------------------------------------------------
    # RESULT
    # -----------------------------------------------------

    return {
        "logo_type": logo_type,
        "shape": shape,
        "layout": layout,
        "font_style": font_style,

        "visual_metaphor": clean_text(
            specification.get("visual_metaphor"),
            "A distinctive symbol representing the brand's core value.",
        ),

        "composition": clean_text(
            specification.get("composition"),
            "Balanced professional vector composition.",
        ),

        "geometry_style": geometry_style,
        "symmetry": symmetry,

        "complexity": clamp_integer(
            specification.get("complexity", 2),
            1,
            3,
            2,
        ),

        "primary_color": primary,
        "secondary_color": secondary,
        "accent_color": accent,

        "rotation": clamp_integer(
            specification.get("rotation", 0),
            0,
            180,
            0,
        ),

        "layers": clamp_integer(
            specification.get("layers", 2),
            1,
            4,
            2,
        ),

        "stroke_width": clamp_integer(
            specification.get("stroke_width", 18),
            8,
            35,
            18,
        ),

        "concept": clean_text(
            specification.get("concept"),
            "Distinctive professional brand identity.",
        ),

        "creative_direction": direction["name"],
    }


# =========================================================
# HEX VALIDATION
# =========================================================

def clean_hex(value, fallback):

    if not isinstance(value, str):
        return fallback

    value = value.strip()

    if len(value) != 7:
        return fallback

    if not value.startswith("#"):
        return fallback

    try:
        int(value[1:], 16)
        return value.upper()

    except ValueError:
        return fallback


# =========================================================
# LIGHTNESS CHECK
# =========================================================

def is_too_light(hex_color: str) -> bool:
    """
    Reject colors that are likely to disappear against the
    white logo preview background.
    """

    try:
        value = hex_color.lstrip("#")

        red = int(value[0:2], 16)
        green = int(value[2:4], 16)
        blue = int(value[4:6], 16)

        luminance = (
            0.2126 * red
            + 0.7152 * green
            + 0.0722 * blue
        )

        return luminance > 215

    except Exception:
        return False


# =========================================================
# INTEGER VALIDATION
# =========================================================

def clamp_integer(
    value,
    minimum,
    maximum,
    fallback,
):

    try:
        value = int(value)

        return max(
            minimum,
            min(maximum, value),
        )

    except Exception:
        return fallback


# =========================================================
# TEXT VALIDATION
# =========================================================

def clean_text(
    value,
    fallback,
):

    if not isinstance(value, str):
        return fallback

    value = value.strip()

    if not value:
        return fallback

    return value[:500]