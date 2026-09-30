from __future__ import annotations

import json
import random
import uuid

import requests
from app.services.logo_identity_engine import generate_identity_briefs
from app.services.logo_industry_design import choose_design_language
from app.services.logo_industry_resolver import resolve_industry



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
# NAMED UI PALETTES
# =========================================================
#
# These names should correspond to the palette IDs used by
# the frontend. Ollama still sees the semantic palette name,
# but the sanitizer guarantees predictable colors.
# =========================================================

NAMED_PALETTES = {
    "professional": {
        "primary": "#172554",
        "secondary": "#2563EB",
        "accent": "#60A5FA",
    },
    "technology": {
        "primary": "#312E81",
        "secondary": "#6366F1",
        "accent": "#22D3EE",
    },
    "luxury": {
        "primary": "#171717",
        "secondary": "#B68D40",
        "accent": "#D4AF37",
    },
    "nature": {
        "primary": "#14532D",
        "secondary": "#16A34A",
        "accent": "#84CC16",
    },
    "energetic": {
        "primary": "#9A3412",
        "secondary": "#F97316",
        "accent": "#FACC15",
    },
    "ocean": {
        "primary": "#164E63",
        "secondary": "#0891B2",
        "accent": "#67E8F9",
    },
    "warm": {
        "primary": "#7C2D12",
        "secondary": "#EA580C",
        "accent": "#FDBA74",
    },
    "monochrome": {
        "primary": "#18181B",
        "secondary": "#52525B",
        "accent": "#A1A1AA",
    },
}


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

def sanitize_flat_logo_specification(specification: dict) -> dict:
    """
    Remove rendering/effect language that is unsuitable for
    master logo artwork before cloud or local rendering.
    """
    if not isinstance(specification, dict):
        return {}

    replacements = {
        "uncontrolled gradients": "controlled palette gradient",
        "3d effects": "flat vector forms",
        "3d effect": "flat vector form",
        "3d render": "flat vector artwork",
        "3d": "flat vector",
        "drop shadows": "clean separation",
        "drop shadow": "clean separation",
        "shadows": "clean contrast",
        "shadow": "clean contrast",
        "metallic effects": "solid color treatment",
        "metallic effect": "solid color treatment",
        "metallic": "solid color",
        "glass effects": "flat geometric forms",
        "glass effect": "flat geometric form",
        "glass": "flat geometric",
        "photorealistic": "vector-like",
        "realistic": "simplified vector",
        "textures": "solid fills",
        "texture": "solid fill",
        "glowing": "high-contrast",
        "glow": "contrast",
        "studio lighting": "flat color contrast",
        "lighting": "color contrast",
        "embossed": "flat",
        "embossing": "flat geometry",
        "mockup": "logo artwork",
        "shading": "flat solid color separation",
        "shaded": "flat solid color",
        "depth": "flat geometric layering",
        "dimensional": "flat geometric",
        "dimension": "flat geometry",
        "beveled": "flat-edged",
        "bevel": "flat edge",
        "glossy": "matte flat",
        "gloss": "matte flat finish",
        "reflective": "solid color",
        "reflection": "clean negative space",
        "isometric": "front-facing flat",
    }

    for key in ("composition", "concept", "visual_metaphor"):
        value = specification.get(key)

        if not isinstance(value, str):
            continue

        cleaned = value

        for source, replacement in replacements.items():
            cleaned = cleaned.replace(source, replacement)
            cleaned = cleaned.replace(source.title(), replacement)
            cleaned = cleaned.replace(source.upper(), replacement)

        specification[key] = cleaned

    return specification


def generate_logo_specification(
    business_name: str,
    industry: str,
    style: str,
    description: str = "",
    direction_index: int | None = None,
    palette_name: str = "",
    custom_colors: list[str] | None = None,
    creative_prompt: str = "",
    use_ai: bool = True,
) -> dict:
    """
    Generate one structured logo specification with Ollama.

    User choices from the Create page are real generation
    requirements:

    - style
    - named palette
    - custom HEX colors
    - creative prompt

    Explicit custom colors have the highest color priority.
    """

    if direction_index is None:
        direction_index = random.randrange(
            len(CREATIVE_DIRECTIONS)
        )

    # V5 preserves the caller's raw concept position so 3 / 6 / 9
    # generations can use distinct identity strategies even though the
    # legacy V4 creative-direction system contains six directions.
    v5_concept_index = int(direction_index)

    direction_index = (
        direction_index
        % len(CREATIVE_DIRECTIONS)
    )

    direction = (
        CREATIVE_DIRECTIONS[
            direction_index
        ]
    )

    generation_id = str(
        uuid.uuid4()
    )

    custom_colors = (
        custom_colors
        or []
    )

    palette_name = (
        str(palette_name)
        .strip()
        .lower()
    )

    creative_prompt = (
        str(creative_prompt)
        .strip()
    )

    palette_instruction = (
        palette_name
        if palette_name
        else "designer-selected"
    )

    custom_color_instruction = (
        ", ".join(custom_colors)
        if custom_colors
        else "none"
    )

    creative_instruction = (
        creative_prompt
        if creative_prompt
        else "No additional user direction."
    )

    prompt = f"""
You are a senior brand identity designer creating a professional
commercial logo system.

Your job is to create ONE vector logo specification.

A deterministic SVG renderer can turn your JSON into artwork.
A cloud image provider may also use the same specification to
generate symbol artwork before deterministic typography is added.

Therefore create a strong, practical design specification that works
for both clean vector construction and professional symbol generation.

==================================================
BUSINESS
==================================================

Business name:
{business_name}

Industry:
{industry}

Requested logo style:
{style}

Business description:
{description}

Selected color palette:
{palette_instruction}

User-selected custom HEX colors:
{custom_color_instruction}

Additional creative direction:
{creative_instruction}

==================================================
USER REQUIREMENTS
==================================================

The requested logo style, selected palette, custom colors and
additional creative direction are REAL USER REQUIREMENTS.

They are not optional metadata.

Respect the requested logo style while still following the assigned
creative direction.

If custom HEX colors are provided:
- use them as the basis of the logo palette
- preserve their intended visual hierarchy
- do not replace them with unrelated colors

If no custom colors are provided:
- interpret the selected palette name semantically
- select colors appropriate to that palette
- keep strong contrast on a white background

Use the additional creative direction to influence:
- visual metaphor
- composition
- geometry
- personality
- typography feeling

Do not follow a creative instruction that would violate basic logo
production requirements such as readability or scalability.

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

Infer:

1. What does this business actually offer?
2. What should customers feel about it?
3. What meaningful idea can represent that value?
4. How can that idea become a simple recognizable mark?
5. How should the requested style influence that mark?

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

This logo belongs to a batch containing other concepts.

This concept MUST follow its assigned creative direction.

Do not drift toward a generic technology hexagon.
Do not create arbitrary overlapping polygons.
Do not make every business look like a software startup.
Do not default to blue unless the selected palette or brand
requirements call for blue.

The logo should be distinguishable from other concepts even when
viewed only as a black silhouette.

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

For luxury or elegant styles:
prefer refined proportions, controlled spacing and sophisticated
geometry rather than excessive ornament.

For playful styles:
allow friendlier proportions and rounded geometry while preserving
professional readability.

For corporate styles:
prioritize stability, clarity and confidence.

For futuristic styles:
use disciplined contemporary geometry rather than generic sci-fi
decoration.

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
- work on the requested light or dark presentation background
- remain identifiable when converted to one-color artwork

Never use:

- photography
- realistic images
- humans
- mascots
- 3D effects
- uncontrolled rainbow gradients
- shadows
- glow
- glass effects
- metallic effects
- texture
- stock-logo cliches
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

Choose colors that respect the user's explicit palette choice.

Consider:

- selected palette
- custom colors
- industry
- requested style
- audience
- emotional tone
- positioning
- readability

The primary color should carry most of the identity.

The secondary and accent colors must complement the primary color.

Avoid three colors with nearly identical brightness.

Avoid very pale primary colors because logos are previewed on a
white background.

Do not automatically select blue for technology businesses unless
the user's selected palette calls for it.

==================================================
OUTPUT
==================================================

Return valid JSON ONLY.

Use exactly this schema:

{{
    "logo_type": "<allowed value>",
    "symbol_family": "<ribbon-monogram, fused-lettermark, negative-space, geometric-network, orbital-motion, or structured-emblem>",
    "construction": "<ribbon-fusion, sharp-fusion, negative-space-letter, folded-letter, modular-symbol, orbital-spark, continuous-flow, infinity-loop, technical-ring, structured-badge, concept-pictogram, or swoosh-wordmark>",
    "accent_motif": "<spark, node, arc, cut, leaf, light, growth, connection, motion, or none>",
    "industry_family": "<best matching business sector>",
    "industry_subtype": "<specific supplied or inferred sub-industry>",
    "semantic_motif": "<specific business-relevant motif such as bean, steam, wave, route, pulse, structure, leaf, sun, drop, etc.>",
    "secondary_motif": "<second complementary business-relevant motif>",
    "metaphor_mode": "<industry-symbol, initial-fusion, negative-space, abstract-motion, conceptual, emblem, or typography-led>",
    "avoid_cliches": ["<cliche to avoid>", "<optional second cliche>"],
    "typography_personality": "<modern, geometric, elegant, classic, or bold>",
    "presentation_layout": "<stacked, horizontal, emblem, or typography-led>",
    "treatment": "<flat or premium-gradient>",
    "background_mode": "<light or dark>",
    "wordmark_emphasis": "<single, split, or accent-terminal>",
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

Respect requested style:
{style}

Respect selected palette:
{palette_instruction}

Respect custom colors:
{custom_color_instruction}

Respect creative direction from user:
{creative_instruction}

Prefer logo family:
{", ".join(direction["preferred_types"])}

Prefer geometry from:
{", ".join(direction["preferred_shapes"])}

Prefer layout:
{direction["preferred_layout"]}

Use meaningful business-specific symbolism.

Choose symbol_family according to the actual business concept rather
than selecting one arbitrarily.

Choose construction according to both the assigned creative direction
and the meaning of the business. A batch must contain materially
different construction systems rather than cosmetic variations of one
symbol.

Construction guidance:

- ribbon-fusion: flowing or interwoven monogram
- sharp-fusion: angular fused initials
- negative-space-letter: initials revealed through cutout geometry
- folded-letter: folded geometric letter construction
- modular-symbol: connected modular geometric identity
- orbital-spark: circular/orbital identity with purposeful accent
- continuous-flow: one flowing abstract path
- infinity-loop: interwoven continuous loop
- technical-ring: precise circular technical identity
- structured-badge: authoritative contained emblem
- concept-pictogram: simple business-specific conceptual symbol
- swoosh-wordmark: motion element integrated with the company name

Choose accent_motif only when it reinforces the business concept.
Do not add a spark, leaf, node or arc merely as decoration.

Choose typography_personality according to brand positioning:

- modern: clean contemporary sans serif
- geometric: disciplined geometric appearance
- elegant: refined high-contrast or serif appearance
- classic: established traditional typography
- bold: strong contemporary display typography

Choose presentation_layout according to the concept:

- stacked: symbol above wordmark
- horizontal: symbol beside wordmark
- emblem: contained badge-oriented identity
- typography-led: wordmark is the primary identity element

Use premium-gradient only when it improves the requested identity.
A premium gradient must use ONLY the selected primary, secondary and
accent brand colors as gradient stops. Never invent rainbow colors.

Use dark background presentation only when it strengthens contrast
and the requested identity. The underlying symbol must remain usable
on light backgrounds as well.

For split or accent-terminal wordmarks, color emphasis must reinforce
readability. Never split the company name into misleading words.

Every HEX value must contain exactly six hexadecimal digits.

complexity must be 1, 2, or 3.
rotation must be 0 through 180.
layers must be 1 through 4.
stroke_width must be 8 through 35.
"""

    specification = {}

    if use_ai:
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

            if not isinstance(
                specification,
                dict,
            ):
                specification = {}

        except Exception as error:
            print(
                "Logo designer AI error:",
                repr(error),
            )

            specification = {}
    else:
        print(
            "[LOGO DESIGNER] Fast deterministic "
            "specification mode."
        )

    specification = sanitize_flat_logo_specification(
        specification
    )

    # -----------------------------------------------------
    # CUSTOM COLOR OVERRIDE
    # -----------------------------------------------------
    #
    # Explicit user HEX colors are stronger than the model's
    # choices. This guarantees that the custom-color UI is
    # functional rather than merely advisory.
    # -----------------------------------------------------

    valid_custom_colors = []

    for color in custom_colors:
        cleaned = clean_hex(
            color,
            "",
        )

        if cleaned:
            valid_custom_colors.append(
                cleaned
            )

    if valid_custom_colors:
        specification[
            "primary_color"
        ] = valid_custom_colors[0]

        specification[
            "secondary_color"
        ] = (
            valid_custom_colors[1]
            if len(valid_custom_colors) > 1
            else valid_custom_colors[0]
        )

        specification[
            "accent_color"
        ] = (
            valid_custom_colors[2]
            if len(valid_custom_colors) > 2
            else (
                valid_custom_colors[1]
                if len(valid_custom_colors) > 1
                else valid_custom_colors[0]
            )
        )

    sanitized = sanitize_specification(
        specification=specification,
        direction=direction,
        direction_index=direction_index,
        palette_name=palette_name,
        custom_colors=valid_custom_colors,
        industry=industry,
        business_description=description,
    )

    # Persist one unique generation identity with the specification.
    # Rendering remains deterministic for saved assets, while a new logo
    # generation request receives a fresh identity and therefore can produce
    # a different local construction variant even for the same business.

    # -----------------------------------------------------
    # V5 PREMIUM IDENTITY INTELLIGENCE
    # -----------------------------------------------------
    #
    # V4.2 remains fully compatible. These fields enrich the persisted
    # specification so the next renderer milestone can execute premium,
    # industry-specific construction rather than infer meaning again.
    semantic_profile = infer_industry_semantics(
        industry=industry,
        description=description,
    )

    v5_family = semantic_profile["industry_family"]

    v5_briefs = generate_identity_briefs(
        business_name=business_name,
        industry_family=v5_family,
        description=description,
        personality=style,
        count=9,
        variant_seed=generation_id,
    )

    v5_brief = v5_briefs[
        v5_concept_index % len(v5_briefs)
    ]

    v5_language = choose_design_language(
        family=industry,
        business_name=business_name,
        description=description,
        strategy=v5_brief["strategy"],
        variant_seed=v5_brief["variant_key"],
    )

    sanitized["identity_strategy"] = v5_brief["strategy"]
    sanitized["semantic_territory"] = v5_brief["territory"]
    sanitized["secondary_territory"] = (
        v5_brief["secondary_territory"]
    )
    sanitized["identity_construction"] = (
        v5_brief["construction"]
    )
    sanitized["semantic_method"] = (
        v5_brief["semantic_method"]
    )
    sanitized["silhouette_target"] = (
        v5_brief["silhouette"]
    )
    sanitized["initial_role"] = (
        v5_brief["initial_role"]
    )
    sanitized["geometry_character"] = (
        v5_brief["geometry_character"]
    )

    sanitized["industry_family"] = (
        v5_language["industry_family"]
    )

    sanitized["industry_label"] = (
        v5_language["industry_label"]
    )

    sanitized["logo_elements"] = list(
        v5_language["logo_elements"]
    )

    sanitized["industry_form"] = (
        v5_language["form"]
    )

    sanitized["negative_space_idea"] = (
        v5_language["negative_space"]
    )

    sanitized["motion_language"] = (
        v5_language["motion"]
    )

    sanitized["geometry_language"] = (
        v5_language["geometry"]
    )

    sanitized["avoid_cliches"] = list(
        dict.fromkeys(
            list(semantic_profile.get("avoid_cliches", ()))
            + list(v5_language.get("avoid", ()))
        )
    )

    sanitized["v5_variant_key"] = (
        v5_brief["variant_key"]
    )

    sanitized["variant_seed"] = generation_id

    return sanitized


# =========================================================
# SANITIZE AI OUTPUT
# =========================================================


# =============================================================
# V4.2 INDUSTRY + SEMANTIC IDENTITY ENGINE
# =============================================================

INDUSTRY_SEMANTIC_PROFILES = {
    "technology": {
        "keywords": {
            "technology", "software", "saas", "ai", "artificial intelligence",
            "machine learning", "cloud", "app", "digital", "data",
            "developer", "platform", "automation", "it", "computing",
        },
        "motifs": (
            "circuit", "data-flow", "grid", "connection",
            "spark", "modular", "signal",
        ),
        "constructions": (
            "modular-symbol", "sharp-fusion", "technical-ring",
            "orbital-spark", "continuous-flow",
        ),
        "typography": ("geometric", "modern", "bold"),
        "avoid": (
            "generic AI brain",
            "generic technology hexagon",
            "meaningless network nodes",
        ),
    },
    "cybersecurity": {
        "keywords": {
            "cybersecurity", "cyber security", "security", "infosec",
            "privacy", "encryption", "secure", "zero trust",
        },
        "motifs": (
            "shield", "lock-space", "encrypted-connection",
            "fortress", "precision",
        ),
        "constructions": (
            "negative-space-letter", "structured-badge",
            "technical-ring", "sharp-fusion",
        ),
        "typography": ("geometric", "bold", "modern"),
        "avoid": ("generic padlock clipart", "hacker hoodie imagery"),
    },
    "finance": {
        "keywords": {
            "finance", "fintech", "bank", "banking", "investment",
            "accounting", "wealth", "capital", "insurance",
            "payments", "financial",
        },
        "motifs": (
            "growth", "pillar", "precision", "progress",
            "trust", "upward-motion",
        ),
        "constructions": (
            "structured-badge", "sharp-fusion", "technical-ring",
            "negative-space-letter", "modular-symbol",
        ),
        "typography": ("classic", "geometric", "elegant"),
        "avoid": ("generic dollar sign", "generic stock chart arrow"),
    },
    "legal": {
        "keywords": {
            "legal", "law", "lawyer", "attorney", "advocate",
            "solicitor", "barrister", "legal services",
        },
        "motifs": (
            "balance", "pillar", "structure", "authority",
            "protection", "foundation",
        ),
        "constructions": (
            "structured-badge", "sharp-fusion",
            "negative-space-letter", "technical-ring",
        ),
        "typography": ("classic", "elegant", "geometric"),
        "avoid": ("generic scales clipart", "gavel clipart"),
    },
    "healthcare": {
        "keywords": {
            "health", "healthcare", "medical", "medicine", "clinic",
            "hospital", "doctor", "dental", "dentist", "pharma",
            "pharmacy", "therapy", "wellness",
        },
        "motifs": (
            "care", "pulse", "continuity", "leaf",
            "human", "wellbeing",
        ),
        "constructions": (
            "continuous-flow", "concept-pictogram",
            "infinity-loop", "negative-space-letter",
        ),
        "typography": ("modern", "geometric", "classic"),
        "avoid": ("generic medical cross", "generic heartbeat stock icon"),
    },
    "coffee": {
        "keywords": {
            "coffee", "cafe", "caf?", "espresso", "roastery",
            "roaster", "barista", "coffeehouse",
        },
        "motifs": (
            "bean", "steam", "roast", "warmth",
            "origin", "leaf",
        ),
        "constructions": (
            "concept-pictogram", "continuous-flow",
            "negative-space-letter", "structured-badge",
            "ribbon-fusion",
        ),
        "typography": ("classic", "elegant", "modern", "bold"),
        "avoid": ("generic coffee cup clipart", "generic caf? badge"),
    },
    "food-beverage": {
        "keywords": {
            "food", "restaurant", "beverage", "bakery", "catering",
            "kitchen", "chef", "organic food", "snack", "drink",
            "nutrition", "grocery",
        },
        "motifs": (
            "nourishment", "leaf", "bowl", "grain",
            "freshness", "warmth",
        ),
        "constructions": (
            "concept-pictogram", "structured-badge",
            "continuous-flow", "negative-space-letter",
        ),
        "typography": ("modern", "classic", "bold"),
        "avoid": ("generic fork and knife clipart", "chef hat stock logo"),
    },
    "music-audio": {
        "keywords": {
            "music", "audio", "sound", "recording", "studio",
            "record label", "dj", "musician", "podcast",
            "headphones", "streaming",
        },
        "motifs": (
            "wave", "pulse", "groove", "rhythm",
            "frequency", "resonance", "play",
        ),
        "constructions": (
            "continuous-flow", "orbital-spark",
            "infinity-loop", "ribbon-fusion",
            "swoosh-wordmark",
        ),
        "typography": ("bold", "geometric", "modern", "elegant"),
        "avoid": ("literal music note clipart", "generic headphones icon"),
    },
    "education": {
        "keywords": {
            "education", "school", "academy", "learning", "e-learning",
            "elearning", "university", "college", "training",
            "tutor", "course",
        },
        "motifs": (
            "knowledge", "book", "light", "growth",
            "path", "discovery",
        ),
        "constructions": (
            "concept-pictogram", "structured-badge",
            "negative-space-letter", "orbital-spark",
        ),
        "typography": ("modern", "classic", "geometric"),
        "avoid": ("generic graduation cap clipart", "generic open book"),
    },
    "real-estate": {
        "keywords": {
            "real estate", "realty", "property", "properties",
            "housing", "home", "architecture", "architect",
            "construction", "building", "interior",
        },
        "motifs": (
            "structure", "doorway", "foundation", "roof",
            "space", "skyline",
        ),
        "constructions": (
            "negative-space-letter", "structured-badge",
            "sharp-fusion", "modular-symbol",
        ),
        "typography": ("geometric", "classic", "modern"),
        "avoid": ("generic house roof clipart", "generic skyline stock mark"),
    },
    "travel-hospitality": {
        "keywords": {
            "travel", "tourism", "hotel", "hospitality", "resort",
            "vacation", "tour", "airline", "destination",
        },
        "motifs": (
            "destination", "route", "horizon", "motion",
            "discovery", "journey",
        ),
        "constructions": (
            "continuous-flow", "orbital-spark",
            "swoosh-wordmark", "concept-pictogram",
        ),
        "typography": ("modern", "elegant", "geometric"),
        "avoid": ("generic airplane clipart", "generic map pin"),
    },
    "automotive": {
        "keywords": {
            "automotive", "car", "cars", "vehicle", "vehicles",
            "auto", "motors", "mobility", "garage", "racing",
        },
        "motifs": (
            "speed", "road", "motion", "aerodynamic",
            "precision", "forward",
        ),
        "constructions": (
            "swoosh-wordmark", "sharp-fusion",
            "continuous-flow", "technical-ring",
        ),
        "typography": ("bold", "geometric", "modern"),
        "avoid": ("generic car silhouette", "generic wheel clipart"),
    },
    "logistics": {
        "keywords": {
            "logistics", "delivery", "shipping", "courier",
            "transport", "transportation", "freight",
            "supply chain", "warehouse",
        },
        "motifs": (
            "route", "connection", "destination",
            "movement", "forward", "network",
        ),
        "constructions": (
            "continuous-flow", "modular-symbol",
            "swoosh-wordmark", "orbital-spark",
        ),
        "typography": ("bold", "geometric", "modern"),
        "avoid": ("generic truck clipart", "generic package icon"),
    },
    "fashion-beauty": {
        "keywords": {
            "fashion", "beauty", "cosmetics", "skincare",
            "salon", "style", "lifestyle", "clothing",
            "jewelry", "jewellery", "luxury fashion",
        },
        "motifs": (
            "fold", "petal", "flow", "elegance",
            "craft", "spark",
        ),
        "constructions": (
            "ribbon-fusion", "folded-letter",
            "swoosh-wordmark", "negative-space-letter",
        ),
        "typography": ("elegant", "classic", "modern"),
        "avoid": ("generic crown", "generic diamond stock icon"),
    },
    "fitness-sports": {
        "keywords": {
            "fitness", "gym", "sport", "sports", "athletic",
            "training", "workout", "performance", "yoga",
        },
        "motifs": (
            "energy", "motion", "peak", "strength",
            "pulse", "progress",
        ),
        "constructions": (
            "sharp-fusion", "continuous-flow",
            "swoosh-wordmark", "orbital-spark",
        ),
        "typography": ("bold", "geometric", "modern"),
        "avoid": ("generic dumbbell", "generic flexing person"),
    },
    "nature-agriculture": {
        "keywords": {
            "nature", "agriculture", "farm", "farming", "organic",
            "sustainable", "sustainability", "eco", "green",
            "environment", "environmental", "garden",
        },
        "motifs": (
            "leaf", "growth", "sprout", "sun",
            "earth", "organic-flow",
        ),
        "constructions": (
            "concept-pictogram", "continuous-flow",
            "negative-space-letter", "structured-badge",
        ),
        "typography": ("modern", "classic", "elegant"),
        "avoid": ("generic recycling arrows", "generic globe with leaf"),
    },
    "water": {
        "keywords": {
            "water", "aqua", "aquatic", "purification",
            "filtration", "hydration", "marine",
        },
        "motifs": (
            "drop", "wave", "purity", "flow",
            "renewal", "clarity",
        ),
        "constructions": (
            "continuous-flow", "concept-pictogram",
            "infinity-loop", "negative-space-letter",
        ),
        "typography": ("modern", "geometric", "elegant"),
        "avoid": ("generic blue water-drop stock icon",),
    },
    "energy": {
        "keywords": {
            "energy", "solar", "renewable", "power",
            "electric", "electricity", "battery", "clean energy",
        },
        "motifs": (
            "sun", "ray", "power", "spark",
            "renewal", "growth",
        ),
        "constructions": (
            "orbital-spark", "concept-pictogram",
            "sharp-fusion", "technical-ring",
        ),
        "typography": ("geometric", "bold", "modern"),
        "avoid": ("generic lightning bolt", "generic solar panel icon"),
    },
    "gaming-entertainment": {
        "keywords": {
            "gaming", "game", "games", "esports", "e-sports",
            "entertainment", "streamer", "streaming",
        },
        "motifs": (
            "play", "energy", "portal", "motion",
            "spark", "competition",
        ),
        "constructions": (
            "sharp-fusion", "orbital-spark",
            "folded-letter", "swoosh-wordmark",
        ),
        "typography": ("bold", "geometric", "modern"),
        "avoid": ("generic game controller", "generic esports mascot"),
    },
    "creative-media": {
        "keywords": {
            "creative", "agency", "design", "media", "photography",
            "film", "video", "marketing", "advertising",
            "branding", "content",
        },
        "motifs": (
            "frame", "focus", "light", "spark",
            "story", "transformation",
        ),
        "constructions": (
            "folded-letter", "ribbon-fusion",
            "concept-pictogram", "swoosh-wordmark",
        ),
        "typography": ("modern", "elegant", "bold"),
        "avoid": ("generic camera aperture", "generic magic wand"),
    },
    "manufacturing-engineering": {
        "keywords": {
            "manufacturing", "engineering", "industrial",
            "factory", "machinery", "mechanical",
            "automation engineering", "fabrication",
        },
        "motifs": (
            "precision", "structure", "assembly",
            "motion", "technical", "strength",
        ),
        "constructions": (
            "technical-ring", "modular-symbol",
            "sharp-fusion", "structured-badge",
        ),
        "typography": ("geometric", "bold", "modern"),
        "avoid": ("generic gear stock icon", "generic factory silhouette"),
    },
    "retail-ecommerce": {
        "keywords": {
            "retail", "ecommerce", "e-commerce", "shop",
            "store", "marketplace", "shopping", "commerce",
        },
        "motifs": (
            "choice", "connection", "discovery",
            "movement", "exchange", "spark",
        ),
        "constructions": (
            "ribbon-fusion", "modular-symbol",
            "swoosh-wordmark", "concept-pictogram",
        ),
        "typography": ("modern", "bold", "geometric"),
        "avoid": ("generic shopping cart", "generic shopping bag"),
    },
    "nonprofit-community": {
        "keywords": {
            "nonprofit", "non-profit", "charity", "community",
            "foundation", "ngo", "social impact", "volunteer",
        },
        "motifs": (
            "community", "connection", "care",
            "growth", "human", "hope",
        ),
        "constructions": (
            "concept-pictogram", "infinity-loop",
            "continuous-flow", "structured-badge",
        ),
        "typography": ("modern", "classic", "geometric"),
        "avoid": ("generic holding hands clipart", "generic heart logo"),
    },
    "professional-services": {
        "keywords": {
            "consulting", "consultant", "professional services",
            "business services", "advisory", "strategy",
            "management", "b2b",
        },
        "motifs": (
            "clarity", "progress", "structure",
            "connection", "precision", "confidence",
        ),
        "constructions": (
            "sharp-fusion", "technical-ring",
            "structured-badge", "modular-symbol",
        ),
        "typography": ("geometric", "classic", "modern"),
        "avoid": ("generic handshake", "generic bar chart"),
    },
}

SEMANTIC_MOTIFS = {
    "spark", "node", "arc", "cut", "leaf", "light", "growth",
    "connection", "motion", "none",
    "circuit", "data-flow", "grid", "modular", "signal",
    "shield", "lock-space", "encrypted-connection", "fortress",
    "precision", "pillar", "progress", "trust", "upward-motion",
    "balance", "structure", "authority", "protection", "foundation",
    "care", "pulse", "continuity", "human", "wellbeing",
    "bean", "steam", "roast", "warmth", "origin",
    "nourishment", "bowl", "grain", "freshness",
    "wave", "groove", "rhythm", "frequency", "resonance", "play",
    "knowledge", "book", "path", "discovery",
    "doorway", "roof", "space", "skyline",
    "destination", "route", "horizon", "journey",
    "speed", "road", "aerodynamic", "forward",
    "movement", "network", "fold", "petal", "elegance", "craft",
    "energy", "peak", "strength", "sprout", "sun", "earth",
    "organic-flow", "drop", "purity", "flow", "renewal", "clarity",
    "ray", "power", "portal", "competition", "frame", "focus",
    "story", "transformation", "assembly", "technical",
    "choice", "exchange", "community", "hope", "confidence",
}

METAPHOR_MODES = {
    "industry-symbol",
    "initial-fusion",
    "negative-space",
    "abstract-motion",
    "conceptual",
    "emblem",
    "typography-led",
}

V4_CONSTRUCTIONS = {
    "ribbon-fusion",
    "sharp-fusion",
    "negative-space-letter",
    "folded-letter",
    "modular-symbol",
    "orbital-spark",
    "continuous-flow",
    "infinity-loop",
    "technical-ring",
    "structured-badge",
    "concept-pictogram",
    "swoosh-wordmark",
}

V4_TYPOGRAPHY = {
    "modern",
    "geometric",
    "elegant",
    "classic",
    "bold",
}


def infer_industry_semantics(industry="", description=""):
    """
    Return deterministic semantic guidance for the business.

    Exact user-facing industry selections are resolved through the
    shared industry resolver. Existing semantic profiles continue
    supplying motifs, construction and typography guidance.
    """
    raw_industry = str(industry or "").strip()
    raw_description = str(description or "").strip()

    industry_text = raw_industry.lower()
    description_text = raw_description.lower()

    resolved = resolve_industry(raw_industry)

    # Exact selections from the Create page are authoritative.
    if resolved["matched"]:
        best_family = resolved["family"]

    # Preserve the previous keyword classifier for free-form,
    # legacy or otherwise unrecognized industry values.
    else:
        best_family = "other"
        best_score = 0

        for family, profile in INDUSTRY_SEMANTIC_PROFILES.items():
            score = 0

            for keyword in profile["keywords"]:
                keyword = keyword.lower()

                if keyword == industry_text:
                    score += 100
                elif keyword in industry_text:
                    score += 40
                elif keyword in description_text:
                    score += 3

            if score > best_score:
                best_family = family
                best_score = score

    profile = INDUSTRY_SEMANTIC_PROFILES.get(best_family)

    # Some resolver families may not have a legacy semantic profile.
    # Keep the resolved industry data and use safe general guidance.
    if profile is None:
        return {
            "industry_family": resolved["family"],
            "industry_label": resolved["label"],
            "industry_subtype": (
                industry_text
                if industry_text
                else "general"
            ),
            "logo_elements": resolved["elements"],
            "semantic_motifs": (
                "clarity",
                "progress",
                "connection",
                "craft",
                "confidence",
            ),
            "constructions": (
                "concept-pictogram",
                "sharp-fusion",
                "negative-space-letter",
                "swoosh-wordmark",
            ),
            "typography": (
                "modern",
                "geometric",
                "classic",
            ),
            "avoid_cliches": (
                "generic stock icon",
                "meaningless abstract polygon",
            ),
        }

    if resolved["matched"]:
        industry_label = resolved["label"]
        logo_elements = resolved["elements"]
    else:
        family_resolution = resolve_industry(best_family)

        industry_label = (
            raw_industry
            if raw_industry
            else family_resolution["label"]
        )

        logo_elements = family_resolution["elements"]

    return {
        "industry_family": best_family,
        "industry_label": industry_label,
        "industry_subtype": (
            industry_text
            if industry_text
            else best_family
        ),
        "logo_elements": logo_elements,
        "semantic_motifs": profile["motifs"],
        "constructions": profile["constructions"],
        "typography": profile["typography"],
        "avoid_cliches": profile["avoid"],
    }


def _semantic_default_for_direction(profile, direction_name, direction_index):
    motifs = profile["semantic_motifs"]
    constructions = profile["constructions"]
    typography = profile["typography"]

    mode_by_direction = {
        "minimal-geometric": "industry-symbol",
        "negative-space": "negative-space",
        "monogram": "initial-fusion",
        "abstract-motion": "abstract-motion",
        "wordmark": "typography-led",
        "brand-emblem": "emblem",
    }

    construction_by_direction = {
        "negative-space": "negative-space-letter",
        "wordmark": "swoosh-wordmark",
        "brand-emblem": "structured-badge",
    }

    preferred_construction = construction_by_direction.get(direction_name)

    if preferred_construction not in constructions:
        preferred_construction = constructions[
            direction_index % len(constructions)
        ]

    return {
        "semantic_motif": motifs[
            direction_index % len(motifs)
        ],
        "secondary_motif": motifs[
            (direction_index + 1) % len(motifs)
        ],
        "metaphor_mode": mode_by_direction.get(
            direction_name,
            "conceptual",
        ),
        "construction": preferred_construction,
        "typography_personality": typography[
            direction_index % len(typography)
        ],
    }
def sanitize_specification(
    specification: dict,
    direction: dict,
    direction_index: int,
    palette_name: str = "",
    custom_colors: list[str] | None = None,
    industry: str = "",
    business_description: str = "",
) -> dict:
    """
    Validate Ollama's structured result and enforce important
    frontend selections.
    """

    if not isinstance(
        specification,
        dict,
    ):
        specification = {}

    custom_colors = (
        custom_colors
        or []
    )

    # -----------------------------------------------------
    # LOGO TYPE
    # -----------------------------------------------------

    preferred_types = (
        direction[
            "preferred_types"
        ]
    )

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

    preferred_shapes = (
        direction[
            "preferred_shapes"
        ]
    )

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

    preferred_layout = (
        direction[
            "preferred_layout"
        ]
    )

    layout = specification.get(
        "layout",
        preferred_layout,
    )

    if layout not in LAYOUTS:
        layout = preferred_layout

    if logo_type == "wordmark":
        layout = "wordmark"

    elif logo_type == "emblem":
        layout = "emblem"

    elif direction["name"] in {
        "negative-space",
        "abstract-motion",
    }:
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
    # COLOR PALETTE
    # -----------------------------------------------------

    fallback_palette = (
        FALLBACK_PALETTES[
            direction_index
            % len(FALLBACK_PALETTES)
        ]
    )

    named_palette = (
        NAMED_PALETTES.get(
            palette_name
        )
    )

    # Named frontend palette is stronger than random Ollama
    # color choice. Custom colors are stronger still.
    if custom_colors:
        selected_palette = {
            "primary":
                custom_colors[0],

            "secondary":
                (
                    custom_colors[1]
                    if len(custom_colors) > 1
                    else custom_colors[0]
                ),

            "accent":
                (
                    custom_colors[2]
                    if len(custom_colors) > 2
                    else (
                        custom_colors[1]
                        if len(custom_colors) > 1
                        else custom_colors[0]
                    )
                ),
        }

        enforce_palette = True

    elif named_palette:
        selected_palette = (
            named_palette
        )

        enforce_palette = True

    else:
        selected_palette = (
            fallback_palette
        )

        enforce_palette = False

    if enforce_palette:
        primary = selected_palette[
            "primary"
        ]

        secondary = selected_palette[
            "secondary"
        ]

        accent = selected_palette[
            "accent"
        ]

    else:
        primary = clean_hex(
            specification.get(
                "primary_color"
            ),
            selected_palette[
                "primary"
            ],
        )

        secondary = clean_hex(
            specification.get(
                "secondary_color"
            ),
            selected_palette[
                "secondary"
            ],
        )

        accent = clean_hex(
            specification.get(
                "accent_color"
            ),
            selected_palette[
                "accent"
            ],
        )

    # Keep the primary mark visible on white.
    if is_too_light(primary):
        primary = (
            fallback_palette[
                "primary"
            ]
        )

    # Prevent accidental duplicate colors when the user did
    # not explicitly request duplicates.
    if (
        not custom_colors
        and primary == secondary
    ):
        secondary = selected_palette[
            "secondary"
        ]

    if (
        not custom_colors
        and secondary == accent
    ):
        accent = selected_palette[
            "accent"
        ]

    # -----------------------------------------------------
    # PREMIUM V3 PRESENTATION
    # -----------------------------------------------------

    allowed_symbol_families = {
        "ribbon-monogram",
        "fused-lettermark",
        "negative-space",
        "geometric-network",
        "orbital-motion",
        "structured-emblem",
    }

    symbol_family = str(
        specification.get(
            "symbol_family",
            "",
        )
        or ""
    ).strip().lower()

    if symbol_family not in allowed_symbol_families:
        family_defaults = {
            "minimal-geometric": "geometric-network",
            "negative-space": "negative-space",
            "monogram": "fused-lettermark",
            "abstract-motion": "orbital-motion",
            "wordmark": "fused-lettermark",
            "brand-emblem": "structured-emblem",
        }

        symbol_family = family_defaults.get(
            direction["name"],
            "geometric-network",
        )

    treatment = str(
        specification.get(
            "treatment",
            "flat",
        )
        or "flat"
    ).strip().lower()

    if treatment not in {
        "flat",
        "premium-gradient",
    }:
        treatment = "flat"

    background_mode = str(
        specification.get(
            "background_mode",
            "light",
        )
        or "light"
    ).strip().lower()

    if background_mode not in {
        "light",
        "dark",
    }:
        background_mode = "light"

    wordmark_emphasis = str(
        specification.get(
            "wordmark_emphasis",
            "single",
        )
        or "single"
    ).strip().lower()

    if wordmark_emphasis not in {
        "single",
        "split",
        "accent-terminal",
    }:
        wordmark_emphasis = "single"

    # -----------------------------------------------------
    # PREMIUM V4 IDENTITY SYSTEM
    # -----------------------------------------------------

    allowed_constructions = {
        "ribbon-fusion",
        "sharp-fusion",
        "negative-space-letter",
        "folded-letter",
        "modular-symbol",
        "orbital-spark",
        "continuous-flow",
        "infinity-loop",
        "technical-ring",
        "structured-badge",
        "concept-pictogram",
        "swoosh-wordmark",
    }

    direction_construction_defaults = {
        "minimal-geometric": "modular-symbol",
        "negative-space": "negative-space-letter",
        "monogram": "sharp-fusion",
        "abstract-motion": "continuous-flow",
        "wordmark": "swoosh-wordmark",
        "brand-emblem": "structured-badge",
    }

    construction = str(
        specification.get(
            "construction",
            "",
        )
        or ""
    ).strip().lower()

    if construction not in allowed_constructions:
        construction = direction_construction_defaults.get(
            direction["name"],
            "modular-symbol",
        )

    allowed_accent_motifs = {
        "spark",
        "node",
        "arc",
        "cut",
        "leaf",
        "light",
        "growth",
        "connection",
        "motion",
        "none",
    }

    accent_motif = str(
        specification.get(
            "accent_motif",
            "none",
        )
        or "none"
    ).strip().lower()

    if accent_motif not in allowed_accent_motifs:
        accent_motif = "none"

    allowed_typography = {
        "modern",
        "geometric",
        "elegant",
        "classic",
        "bold",
    }

    typography_personality = str(
        specification.get(
            "typography_personality",
            "modern",
        )
        or "modern"
    ).strip().lower()

    if typography_personality not in allowed_typography:
        typography_personality = "modern"

    allowed_presentations = {
        "stacked",
        "horizontal",
        "emblem",
        "typography-led",
    }

    presentation_layout = str(
        specification.get(
            "presentation_layout",
            "",
        )
        or ""
    ).strip().lower()

    if presentation_layout not in allowed_presentations:
        layout_defaults = {
            "symbol-top": "stacked",
            "symbol-left": "horizontal",
            "wordmark": "typography-led",
            "emblem": "emblem",
        }

        presentation_layout = layout_defaults.get(
            layout,
            "stacked",
        )

    # Keep direction identity strong even if the language model returns a
    # presentation that conflicts with the assigned family.
    if direction["name"] == "wordmark":
        presentation_layout = "typography-led"

    if direction["name"] == "brand-emblem":
        presentation_layout = "emblem"


    # -----------------------------------------------------
    # V4.2 INDUSTRY + SEMANTIC IDENTITY
    # -----------------------------------------------------

    semantic_profile = infer_industry_semantics(
        industry=industry,
        description=business_description,
    )

    semantic_defaults = _semantic_default_for_direction(
        semantic_profile,
        direction["name"],
        direction_index,
    )

    industry_family = str(
        specification.get("industry_family")
        or semantic_profile["industry_family"]
    ).strip().lower()

    # The deterministic classifier is authoritative for known industries.
    if semantic_profile["industry_family"] != "other":
        industry_family = semantic_profile["industry_family"]

    industry_subtype = clean_text(
        specification.get("industry_subtype"),
        semantic_profile["industry_subtype"],
    ).lower()

    semantic_motif = str(
        specification.get("semantic_motif")
        or semantic_defaults["semantic_motif"]
    ).strip().lower()

    if semantic_motif not in SEMANTIC_MOTIFS:
        semantic_motif = semantic_defaults["semantic_motif"]

    secondary_motif = str(
        specification.get("secondary_motif")
        or semantic_defaults["secondary_motif"]
    ).strip().lower()

    if secondary_motif not in SEMANTIC_MOTIFS:
        secondary_motif = semantic_defaults["secondary_motif"]

    metaphor_mode = str(
        specification.get("metaphor_mode")
        or semantic_defaults["metaphor_mode"]
    ).strip().lower()

    if metaphor_mode not in METAPHOR_MODES:
        metaphor_mode = semantic_defaults["metaphor_mode"]

    raw_avoid = specification.get("avoid_cliches")
    if isinstance(raw_avoid, list):
        avoid_cliches = [
            clean_text(item, "")
            for item in raw_avoid
            if clean_text(item, "")
        ][:6]
    else:
        avoid_cliches = []

    if not avoid_cliches:
        avoid_cliches = list(
            semantic_profile["avoid_cliches"]
        )

    # -----------------------------------------------------
    # RESULT
    # -----------------------------------------------------

    return {
        "logo_type":
            logo_type,

        "symbol_family":
            symbol_family,

        "construction":
            construction,

        "accent_motif":
            accent_motif,

        "typography_personality":
            typography_personality,

        "presentation_layout":
            presentation_layout,

        "treatment":
            treatment,

        "background_mode":
            background_mode,

        "wordmark_emphasis":
            wordmark_emphasis,

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
                    "A distinctive symbol "
                    "representing the brand's "
                    "core value."
                ),
            ),

        "composition":
            clean_text(
                specification.get(
                    "composition"
                ),
                (
                    "Balanced professional "
                    "vector composition."
                ),
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

        "industry_family":
            industry_family,

        "industry_label":
            semantic_profile.get(
                "industry_label",
                industry,
            ),

        "logo_elements":
            list(
                semantic_profile.get(
                    "logo_elements",
                    (),
                )
            ),

        "industry_subtype":
            industry_subtype,

        "semantic_motif":
            semantic_motif,

        "secondary_motif":
            secondary_motif,

        "metaphor_mode":
            metaphor_mode,

        "avoid_cliches":
            avoid_cliches,

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

    value = (
        value
        .strip()
        .upper()
    )

    if len(value) != 7:
        return fallback

    if not value.startswith("#"):
        return fallback

    try:
        int(
            value[1:],
            16,
        )

        return value

    except ValueError:
        return fallback


# =========================================================
# LIGHTNESS CHECK
# =========================================================

def is_too_light(
    hex_color: str,
) -> bool:
    """
    Reject colors likely to disappear against the white
    logo preview background.
    """

    try:
        value = (
            hex_color
            .lstrip("#")
        )

        red = int(
            value[0:2],
            16,
        )

        green = int(
            value[2:4],
            16,
        )

        blue = int(
            value[4:6],
            16,
        )

        luminance = (
            0.2126 * red
            + 0.7152 * green
            + 0.0722 * blue
        )

        return (
            luminance > 215
        )

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

    value = (
        value.strip()
    )

    if not value:
        return fallback

    return value[:500]

