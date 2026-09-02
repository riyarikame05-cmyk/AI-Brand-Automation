import json
import random
import uuid

import requests


OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
OLLAMA_MODEL = "qwen2.5:3b"


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


def generate_logo_specification(
    business_name: str,
    industry: str,
    style: str,
    description: str,
) -> dict:

    generation_id = str(
        uuid.uuid4()
    )

    requested_type = random.choice(
        LOGO_TYPES
    )

    requested_shape = random.choice(
        SHAPES
    )

    prompt = f"""
You are designing a professional vector company logo.

Business:
{business_name}

Industry:
{industry}

Brand style:
{style}

Business description:
{description}

Creative generation ID:
{generation_id}

Create ONE unique logo design specification.

Required logo family:
{requested_type}

Starting geometric idea:
{requested_shape}

The generation ID is unique. Create a new composition rather than
repeating a common template.

The final logo will be rendered by Python, so return ONLY JSON.

Allowed logo_type values:
monogram
lettermark
abstract
geometric
emblem
combination
negative-space
wordmark

Allowed shape values:
circle
diamond
hexagon
triangle
square
rings
arcs
lines
waves
interlocking

Allowed layout values:
symbol-top
symbol-left
emblem
wordmark

Allowed font_style values:
bold
modern
elegant
minimal

Return exactly:

{{
    "logo_type": "{requested_type}",
    "shape": "{requested_shape}",
    "layout": "symbol-top",
    "font_style": "modern",
    "primary_color": "#112233",
    "secondary_color": "#445566",
    "accent_color": "#778899",
    "rotation": 20,
    "layers": 3,
    "stroke_width": 18,
    "concept": "short explanation of the visual idea"
}}

Rules:
- Return valid JSON only.
- Colors must be valid 6-digit HEX colors.
- rotation must be an integer from 0 to 180.
- layers must be an integer from 1 to 5.
- stroke_width must be an integer from 8 to 35.
- Make colors suitable for {style} professional branding.
- Do not request photographs.
- Do not request humans.
- Do not request detailed illustrations.
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
                    "temperature": 1.0,
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

        specification = json.loads(
            result.get(
                "response",
                "{}",
            )
        )

    except Exception as error:

        print(
            "Logo designer AI error:",
            repr(error),
        )

        specification = {}


    return sanitize_specification(
        specification,
        requested_type,
        requested_shape,
    )


def sanitize_specification(
    specification: dict,
    fallback_type: str,
    fallback_shape: str,
) -> dict:

    logo_type = specification.get(
        "logo_type",
        fallback_type,
    )

    if logo_type not in LOGO_TYPES:
        logo_type = fallback_type


    shape = specification.get(
        "shape",
        fallback_shape,
    )

    if shape not in SHAPES:
        shape = fallback_shape


    layout = specification.get(
        "layout",
        "symbol-top",
    )

    if layout not in [
        "symbol-top",
        "symbol-left",
        "emblem",
        "wordmark",
    ]:
        layout = "symbol-top"


    font_style = specification.get(
        "font_style",
        "modern",
    )

    if font_style not in [
        "bold",
        "modern",
        "elegant",
        "minimal",
    ]:
        font_style = "modern"


    return {
        "logo_type": logo_type,
        "shape": shape,
        "layout": layout,
        "font_style": font_style,

        "primary_color": clean_hex(
            specification.get(
                "primary_color",
                "#111827",
            ),
            "#111827",
        ),

        "secondary_color": clean_hex(
            specification.get(
                "secondary_color",
                "#4F46E5",
            ),
            "#4F46E5",
        ),

        "accent_color": clean_hex(
            specification.get(
                "accent_color",
                "#06B6D4",
            ),
            "#06B6D4",
        ),

        "rotation": clamp_integer(
            specification.get(
                "rotation",
                random.randint(
                    0,
                    180,
                ),
            ),
            0,
            180,
            0,
        ),

        "layers": clamp_integer(
            specification.get(
                "layers",
                random.randint(
                    1,
                    5,
                ),
            ),
            1,
            5,
            3,
        ),

        "stroke_width": clamp_integer(
            specification.get(
                "stroke_width",
                18,
            ),
            8,
            35,
            18,
        ),

        "concept": str(
            specification.get(
                "concept",
                "Unique geometric brand identity",
            )
        ),
    }


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

    if not value.startswith("#"):
        return fallback

    if len(value) != 7:
        return fallback

    try:

        int(
            value[1:],
            16,
        )

        return value.upper()

    except ValueError:

        return fallback


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