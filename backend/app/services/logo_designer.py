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
# CREATIVE DIRECTIONS
# =========================================================

CREATIVE_DIRECTIONS = [

    # -----------------------------------------------------
    # CONCEPT 1
    # SIMPLE / GEOMETRIC
    # -----------------------------------------------------

    {
        "name": "minimal-geometric",

        "description": (
            "Create a highly minimal geometric identity. "
            "Use one dominant primitive or a clever combination "
            "of at most two forms. The symbol must have a strong "
            "silhouette and remain recognizable at very small sizes. "
            "Avoid decorative complexity."
        ),

        "preferred_types": [
            "geometric",
            "abstract",
        ],

        "preferred_shapes": [
            "circle",
            "diamond",
            "hexagon",
            "square",
            "arcs",
        ],
    },


    # -----------------------------------------------------
    # CONCEPT 2
    # SYMBOLIC / NEGATIVE SPACE
    # -----------------------------------------------------

    {
        "name": "symbolic-negative-space",

        "description": (
            "Create a conceptual symbol based on a meaningful visual "
            "metaphor or negative space. The hidden idea must connect "
            "directly to the business, product, customer benefit or "
            "industry. Do not simply overlap generic polygons."
        ),

        "preferred_types": [
            "negative-space",
            "combination",
        ],

        "preferred_shapes": [
            "arcs",
            "waves",
            "lines",
            "circle",
            "triangle",
        ],
    },


    # -----------------------------------------------------
    # CONCEPT 3
    # TYPOGRAPHIC
    # -----------------------------------------------------

    {
        "name": "typographic",

        "description": (
            "Create a typography-led identity using the company's "
            "initials or name. Geometry should support the letterform "
            "rather than dominate it. The result should feel custom, "
            "recognizable and suitable for professional branding."
        ),

        "preferred_types": [
            "monogram",
            "lettermark",
            "wordmark",
        ],

        "preferred_shapes": [
            "circle",
            "square",
            "diamond",
            "lines",
        ],
    },
]


# =========================================================
# DEFAULT PALETTES
# Used only if Ollama does not provide valid colors.
# =========================================================

FALLBACK_PALETTES = [

    {
        "primary": "#0F172A",
        "secondary": "#2563EB",
        "accent": "#38BDF8",
    },

    {
        "primary": "#312E81",
        "secondary": "#7C3AED",
        "accent": "#C084FC",
    },

    {
        "primary": "#064E3B",
        "secondary": "#059669",
        "accent": "#34D399",
    },

    {
        "primary": "#7C2D12",
        "secondary": "#EA580C",
        "accent": "#FDBA74",
    },

    {
        "primary": "#18181B",
        "secondary": "#52525B",
        "accent": "#F59E0B",
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

    # -----------------------------------------------------
    # CHOOSE CREATIVE DIRECTION
    # -----------------------------------------------------

    if direction_index is None:

        direction_index = random.randrange(
            len(CREATIVE_DIRECTIONS)
        )


    direction_index = (
        direction_index
        % len(CREATIVE_DIRECTIONS)
    )


    direction = CREATIVE_DIRECTIONS[
        direction_index
    ]


    generation_id = str(
        uuid.uuid4()
    )


    # -----------------------------------------------------
    # BUILD ART-DIRECTION PROMPT
    # -----------------------------------------------------

    prompt = f"""
You are a senior brand identity designer and logo art director.

Your task is to create ONE professional vector logo design specification.

Do not draw the logo.
A deterministic SVG renderer will construct the final artwork from your JSON.

==================================================
BUSINESS
==================================================

Business name:
{business_name}

Industry:
{industry}

Requested brand style:
{style}

Business description:
{description}

==================================================
CREATIVE DIRECTION
==================================================

Direction:
{direction["name"]}

Design objective:
{direction["description"]}

Preferred logo families:
{", ".join(direction["preferred_types"])}

Preferred geometric vocabulary:
{", ".join(direction["preferred_shapes"])}

Generation ID:
{generation_id}

==================================================
DESIGN PROCESS
==================================================

Understand what the business does before selecting the symbol.

Choose a visual metaphor connected to at least one of:

- the product or service
- the customer's desired outcome
- the company's personality
- movement or transformation
- trust
- growth
- precision
- connection
- speed
- simplicity
- innovation

Do not use a shape simply because it looks technological.

Every major visual decision must support the brand concept.

==================================================
PRODUCTION REQUIREMENTS
==================================================

The logo must:

- work as an SVG
- work at small sizes
- have a recognizable silhouette
- remain understandable in one color
- contain minimal unnecessary detail
- use clean vector-friendly geometry
- avoid photographic imagery
- avoid humans and characters
- avoid realistic objects
- avoid 3D
- avoid gradients
- avoid glow
- avoid shadows
- avoid glass effects
- avoid metallic effects
- avoid generic AI-network imagery
- avoid random overlapping polygons
- use no more than three brand colors

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
COLOR DIRECTION
==================================================

Create the palette specifically for this business.

The palette should reflect:

- industry
- requested style
- brand personality
- target audience
- intended market positioning

Avoid muddy combinations.

Ensure sufficient visual contrast.

Do not automatically use blue just because the business is related to technology.

Do not copy common sample palettes.

==================================================
OUTPUT
==================================================

Return valid JSON ONLY.

Use this schema:

{{
    "logo_type": "<allowed logo type>",
    "shape": "<allowed shape>",
    "layout": "<allowed layout>",
    "font_style": "<allowed font style>",

    "visual_metaphor": "<what the symbol represents>",

    "composition": "<how the symbol geometry should be arranged>",

    "geometry_style": "<sharp, rounded, or mixed>",

    "symmetry": "<none, bilateral, or radial>",

    "complexity": <integer from 1 to 3>,

    "primary_color": "<6-digit HEX>",
    "secondary_color": "<6-digit HEX>",
    "accent_color": "<6-digit HEX>",

    "rotation": <integer from 0 to 180>,

    "layers": <integer from 1 to 4>,

    "stroke_width": <integer from 8 to 35>,

    "concept": "<short explanation connecting the identity to the business>"
}}

==================================================
IMPORTANT RULES
==================================================

- Return JSON only.
- Do not return Markdown.
- Do not include explanations outside JSON.
- Do not copy colors from examples or defaults.
- Choose colors from the actual business context.
- Make this direction visually distinct.
- Avoid "interlocking" unless connectivity is genuinely the strongest metaphor.
- Prefer the logo families assigned to this creative direction.
- Prefer the shapes assigned to this creative direction.
- complexity must be 1, 2, or 3.
- rotation must be between 0 and 180.
- layers must be between 1 and 4.
- stroke_width must be between 8 and 35.
- Every color must be a valid six-digit HEX color.
"""


    # -----------------------------------------------------
    # ASK OLLAMA
    # -----------------------------------------------------

    try:

        response = requests.post(
            OLLAMA_URL,

            json={
                "model": OLLAMA_MODEL,

                "prompt": prompt,

                "stream": False,

                "format": "json",

                "options": {

                    # Enough creativity for variation
                    # without becoming too unpredictable.
                    "temperature": 0.85,

                    "seed": random.randint(
                        1,
                        2_000_000_000,
                    ),
                },
            },

            timeout=120,
        )


        response.raise_for_status()


        result = response.json()


        raw_response = result.get(
            "response",
            "{}",
        )


        specification = json.loads(
            raw_response
        )


    except Exception as error:

        print(
            "Logo designer AI error:",
            repr(error),
        )


        specification = {}


    # -----------------------------------------------------
    # VALIDATE EVERYTHING
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # LOGO TYPE
    # -----------------------------------------------------

    preferred_types = direction[
        "preferred_types"
    ]


    logo_type = specification.get(
        "logo_type",
        preferred_types[0],
    )


    if logo_type not in LOGO_TYPES:

        logo_type = preferred_types[0]


    # Force each concept to remain within
    # its intended creative family.
    if logo_type not in preferred_types:

        logo_type = preferred_types[0]


    # -----------------------------------------------------
    # SHAPE
    # -----------------------------------------------------

    preferred_shapes = direction[
        "preferred_shapes"
    ]


    shape = specification.get(
        "shape",
        preferred_shapes[0],
    )


    # Prevent the model from collapsing all
    # three concepts into the same geometry.
    if shape not in preferred_shapes:

        shape = preferred_shapes[0]


    # -----------------------------------------------------
    # LAYOUT
    # -----------------------------------------------------

    layout = specification.get(
        "layout",
        "symbol-top",
    )


    if layout not in LAYOUTS:

        layout = "symbol-top"


    # Wordmarks should use wordmark layout.
    if logo_type == "wordmark":

        layout = "wordmark"


    # -----------------------------------------------------
    # FONT STYLE
    # -----------------------------------------------------

    font_style = specification.get(
        "font_style",
        "modern",
    )


    if font_style not in FONT_STYLES:

        font_style = "modern"


    # -----------------------------------------------------
    # GEOMETRY STYLE
    # -----------------------------------------------------

    geometry_style = specification.get(
        "geometry_style",
        "rounded",
    )


    if geometry_style not in GEOMETRY_STYLES:

        geometry_style = "rounded"


    # -----------------------------------------------------
    # SYMMETRY
    # -----------------------------------------------------

    symmetry = specification.get(
        "symmetry",
        "bilateral",
    )


    if symmetry not in SYMMETRY_TYPES:

        symmetry = "bilateral"


    # -----------------------------------------------------
    # FALLBACK PALETTE
    # -----------------------------------------------------

    palette = FALLBACK_PALETTES[
        direction_index
        % len(FALLBACK_PALETTES)
    ]


    primary = clean_hex(
        specification.get(
            "primary_color"
        ),

        palette[
            "primary"
        ],
    )


    secondary = clean_hex(
        specification.get(
            "secondary_color"
        ),

        palette[
            "secondary"
        ],
    )


    accent = clean_hex(
        specification.get(
            "accent_color"
        ),

        palette[
            "accent"
        ],
    )


    # -----------------------------------------------------
    # RETURN CLEAN SPECIFICATION
    # -----------------------------------------------------

    return {

        "logo_type":
        logo_type,

        "shape":
        shape,

        "layout":
        layout,

        "font_style":
        font_style,


        "visual_metaphor":
        clean_text(
            specification.get(
                "visual_metaphor"
            ),

            (
                "A simple symbol representing "
                "the brand's core value."
            ),
        ),


        "composition":
        clean_text(
            specification.get(
                "composition"
            ),

            "Balanced centered composition.",
        ),


        "geometry_style":
        geometry_style,


        "symmetry":
        symmetry,


        "complexity":
        clamp_integer(
            specification.get(
                "complexity",
                2,
            ),

            1,
            3,
            2,
        ),


        "primary_color":
        primary,


        "secondary_color":
        secondary,


        "accent_color":
        accent,


        "rotation":
        clamp_integer(
            specification.get(
                "rotation",
                0,
            ),

            0,
            180,
            0,
        ),


        "layers":
        clamp_integer(
            specification.get(
                "layers",
                2,
            ),

            1,
            4,
            2,
        ),


        "stroke_width":
        clamp_integer(
            specification.get(
                "stroke_width",
                18,
            ),

            8,
            35,
            18,
        ),


        "concept":
        clean_text(
            specification.get(
                "concept"
            ),

            (
                "Distinctive professional "
                "brand identity."
            ),
        ),


        "creative_direction":
        direction[
            "name"
        ],
    }


# =========================================================
# HEX VALIDATION
# =========================================================

def clean_hex(
    value,
    fallback,
):

    if not isinstance(
        value,
        str,
    ):

        return fallback


    value = value.strip()


    if len(value) != 7:

        return fallback


    if not value.startswith("#"):

        return fallback


    try:

        int(
            value[1:],
            16,
        )


        return value.upper()


    except ValueError:

        return fallback


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

        value = int(
            value
        )


        return max(
            minimum,
            min(
                maximum,
                value,
            ),
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

    if not isinstance(
        value,
        str,
    ):

        return fallback


    value = value.strip()


    if not value:

        return fallback


    # Prevent extremely verbose local-model outputs
    # from propagating through the renderer.
    return value[:500]