from __future__ import annotations

import base64
import json
import os
import time
from urllib.parse import quote

import requests
from dotenv import load_dotenv


load_dotenv()


GEMINI_API_KEY = os.getenv(
    "GEMINI_API_KEY",
    "",
).strip()

GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.5-flash-lite",
).strip()

GEMINI_API_BASE = os.getenv(
    "GEMINI_API_BASE",
    "https://generativelanguage.googleapis.com/v1beta",
).rstrip("/")

CONCEPT_LEVELS = [
    {
        "name": "recognizable",
        "instruction": """
Create a RECOGNIZABLE concept.

The industry/domain should be identifiable, but do not simply draw
its most obvious stock icon.

Start from an authentic domain cue and transform it using something
specific about this company's process, value or customer outcome.

Target balance:
about 60 percent domain recognition,
40 percent business-specific transformation.
""",
    },
    {
        "name": "balanced",
        "instruction": """
Create a BALANCED concept.

Industry/domain relevance and the company's unique transformation
should have approximately equal importance.

A knowledgeable viewer should feel that the symbol belongs in this
business domain, while the construction should still contain a
specific idea about what this company does.

Target balance:
about 50 percent domain recognition,
50 percent business-specific transformation.
""",
    },
    {
        "name": "conceptual",
        "instruction": """
Create a CONCEPTUAL concept.

Lead with the company's transformation, process or customer outcome.

Industry relevance should still be present, but it may be encoded
through behavior, structure, material logic, process or relationship
rather than a literal object.

Target balance:
about 30 percent domain recognition,
70 percent business-specific transformation.
""",
    },
]


def _require_configuration() -> None:

    if not GEMINI_API_KEY:
        raise RuntimeError(
            "GEMINI_API_KEY is not configured."
        )



def _extract_json(text: str) -> dict:

    cleaned = str(text or "").strip()

    if cleaned.startswith("```"):

        lines = cleaned.splitlines()

        if lines:
            lines = lines[1:]

        if (
            lines
            and lines[-1].strip().startswith("```")
        ):
            lines = lines[:-1]

        cleaned = "\n".join(lines).strip()

        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].strip()

    start = cleaned.find("{")
    end = cleaned.rfind("}")

    if (
        start == -1
        or end == -1
        or end <= start
    ):
        raise RuntimeError(
            "Gemini did not return a JSON object."
        )

    return json.loads(
        cleaned[start:end + 1]
    )


def _gemini_json(
    prompt: str,
    temperature: float = 1.0,
) -> dict:

    url = (
        f"{GEMINI_API_BASE}/models/"
        f"{GEMINI_MODEL}:generateContent"
    )

    last_response = None

    for attempt in range(5):

        response = requests.post(
            url,
            headers={
                "x-goog-api-key": GEMINI_API_KEY,
                "Content-Type": "application/json",
            },
            json={
                "contents": [
                    {
                        "parts": [
                            {
                                "text": prompt,
                            }
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": temperature,
                    "responseMimeType": (
                        "application/json"
                    ),
                },
            },
            timeout=120,
        )

        last_response = response

        if response.status_code == 200:
            break

        if response.status_code in (
            429,
            503,
        ):
            time.sleep(
                4 + attempt * 4
            )
            continue

        response.raise_for_status()

    if (
        last_response is None
        or last_response.status_code != 200
    ):
        raise RuntimeError(
            "Gemini failed after retries."
        )

    payload = last_response.json()

    try:
        text = (
            payload["candidates"][0]
            ["content"]["parts"][0]["text"]
        )
    except (
        KeyError,
        IndexError,
        TypeError,
    ) as error:
        raise RuntimeError(
            "Gemini returned an unexpected response."
        ) from error

    return _extract_json(text)



def create_semantic_portfolio_with_gemini(
    business_name: str,
    industry: str,
    description: str,
    style: str = "modern",
    creative_prompt: str = "",
    count: int = 6,
    existing_territories: list[dict] | None = None,
    rejection_history: list[dict] | None = None,
) -> list[dict]:
    """
    Plan mutually distinct business-semantic territories for one batch.

    These are NOT visual-style buckets. Each territory must represent a
    materially different truth about the business before individual symbol
    construction begins.
    """

    _require_configuration()

    count = max(1, int(count))
    existing_territories = existing_territories or []
    rejection_history = rejection_history or []

    existing_context = json.dumps(
        existing_territories,
        ensure_ascii=False,
        indent=2,
    )
    rejection_context = json.dumps(
        rejection_history,
        ensure_ascii=False,
        indent=2,
    )

    prompt = f"""
You are the strategic identity director for a world-class branding studio.

Analyze this company ONCE and create exactly {count} MUTUALLY DISTINCT
semantic territories for logo development.

BUSINESS NAME:
{business_name}

INDUSTRY:
{industry}

BUSINESS DESCRIPTION:
{description or "No detailed description supplied."}

REQUESTED STYLE:
{style}

ADDITIONAL USER DIRECTION:
{creative_prompt or "none"}

SEMANTIC TERRITORIES ALREADY USED IN THIS BATCH:
{existing_context if existing_territories else "none"}

ACTUAL-PIXEL REJECTIONS ALREADY OBSERVED IN THIS BATCH:
{rejection_context if rejection_history else "none"}

When previous territories are supplied, every new territory must be
semantically different from them, not merely renamed.

When actual-pixel rejection history is supplied, treat it as hard evidence
about what the renderer actually produced.

HARD REPLACEMENT RULES:
- do not repeat a failed_visual_family;
- do not reproduce the topology described by looks_like under new wording;
- do not make a cosmetic variation of a rejected construction;
- use primary_failure to understand why the rendered pixels failed;
- move toward a genuinely different semantic and physical opportunity;
- preserve authentic business and industry relevance;
- do not escape a failed construction by becoming arbitrary geometry.

This is NOT a request for {count} visual styles.
Do NOT create buckets such as:
geometric, monogram, negative space, emblem, abstract, wordmark.

Instead identify genuinely different truths about what this business does.

IMPORTANT: distinguish INTERNAL BUSINESS ANALYSIS from BRAND TERRITORY.

You may reason deeply about technical mechanisms internally, but a semantic
territory should normally express a truth that a customer, employee, buyer,
or ordinary viewer can understand and care about.

Do NOT turn supporting technical details into the identity idea merely
because they sound sophisticated.

For example, for a specialty coffee roaster, internal analysis may involve
pyrolysis, moisture desorption, porosity, endothermic/exothermic phases, and
volatile compounds. Those details can inform your reasoning, but territories
should normally elevate them into brand-relevant truths such as controlled
roast transformation, preservation of origin character, small-batch craft,
freshness at peak expression, traceability, or precision serving flavor.

Avoid territory names and central ideas that sound like:
- scientific paper titles;
- engineering subsystems;
- laboratory processes;
- pseudo-technical branding language;
- microscopic mechanisms customers would never identify with;

unless the company actually sells that scientific or engineering mechanism.

Possible dimensions of differentiation include:
- different customer problems solved;
- different customer outcomes or forms of value;
- different authentic craft or operating principles;
- different stages of the customer/product journey;
- different before-to-after transformations;
- provenance, material, place, or source where genuinely important;
- trust, consistency, relief, expression, control, discovery, care, speed,
  access, confidence, or other human-relevant benefits where appropriate;
- different domain-specific behaviors that matter visibly to the customer.

Do not force those examples when they do not fit the business.

PORTFOLIO BALANCE:

Do not create an entire portfolio from microscopic variations of one
mechanism.

Where the business supports it, spread territories across materially
different dimensions such as:
1. customer outcome or experience;
2. distinctive craft/process or company behavior;
3. provenance/domain/material truth;
4. before-to-after transformation;
5. trust, consistency, control, or service value;
6. another genuinely different business truth.

These are reasoning dimensions, NOT fixed visual-style categories.

CRITICAL DIVERSITY RULE:

No two territories may reduce to the same underlying story with different
wording.

For example, these are NOT sufficiently different:
"many paths become one"
"fragments converge"
"separate channels unify"
"multiple inputs become one stream"

Those are the SAME semantic territory.

Likewise, technical synonyms or adjacent stages of one physical mechanism do
not automatically create different brand territories.

For example:
"thermal expansion"
"heat diffusion"
"moisture venting"
"porosity change"
"thermal inflection"

may all collapse into the SAME broader territory if they merely communicate
controlled roast transformation.

Do not spend multiple portfolio slots on such adjacent mechanisms unless they
produce genuinely different customer-facing meanings.

For each territory explain what the other territories must NOT duplicate.

Industry relevance must be authentic, but avoid automatic stock-icon
reasoning.

For digital/process/knowledge companies, prefer authentic behaviors such as
coordination, transfer, state change, routing, continuity, verification,
orchestration, exception handling, synchronization, reduction of effort,
cause-and-effect, and customer outcomes where genuinely relevant.

Do not prescribe a generic logo shape.

Return JSON only:

{{
  "business_understanding": {{
    "domain_type": "",
    "core_customer": "",
    "core_problem": "",
    "core_mechanism": "",
    "core_outcome": ""
  }},
  "territories": [
    {{
      "territory_name": "",
      "business_truth": "",
      "customer_problem": "",
      "business_mechanism": "",
      "customer_transformation": "",
      "customer_value": "",
      "authentic_domain_signal": "",
      "distinctive_semantic_angle": "",
      "must_not_duplicate": ""
    }}
  ]
}}

Return exactly {count} territories.
""".strip()

    data = _gemini_json(prompt, temperature=0.95)

    raw = data.get("territories", [])
    if not isinstance(raw, list):
        raise RuntimeError("Gemini portfolio territories are invalid.")

    territories = []

    keys = (
        "territory_name",
        "business_truth",
        "customer_problem",
        "business_mechanism",
        "customer_transformation",
        "customer_value",
        "authentic_domain_signal",
        "distinctive_semantic_angle",
        "must_not_duplicate",
    )

    for item in raw:
        if not isinstance(item, dict):
            continue

        cleaned = {
            key: str(item.get(key, "")).strip()
            for key in keys
        }

        if (
            cleaned["territory_name"]
            and cleaned["business_truth"]
            and cleaned["distinctive_semantic_angle"]
        ):
            territories.append(cleaned)

    if len(territories) < count:
        raise RuntimeError(
            f"Gemini returned only {len(territories)} usable semantic "
            f"territories; {count} required."
        )

    return territories[:count]


def create_art_direction_with_gemini(
    business_name: str,
    industry: str,
    description: str,
    style: str = "modern",
    creative_prompt: str = "",
    concept_index: int = 0,
    semantic_territory: dict | None = None,
    accepted_visual_history: list[dict] | None = None,
) -> dict:

    _require_configuration()

    level = CONCEPT_LEVELS[
        int(concept_index)
        % len(CONCEPT_LEVELS)
    ]

    accepted_visual_history = accepted_visual_history or []
    accepted_visual_context = json.dumps(
        accepted_visual_history,
        ensure_ascii=False,
        indent=2,
    )

    prompt = f"""
You are the executive creative director of a world-class brand
identity studio.

Create ONE original symbol-only identity direction.

============================================================
BUSINESS
============================================================

Name:
{business_name}

Industry:
{industry}

What this company actually does:
{description or "No detailed description supplied."}

Requested style:
{style}

Additional user direction:
{creative_prompt or "none"}

Concept position:
{concept_index}

Concept abstraction level:
{level["name"]}

{level["instruction"]}

============================================================
ASSIGNED SEMANTIC TERRITORY
============================================================

{json.dumps(semantic_territory or {}, ensure_ascii=False, indent=2)}

This assigned territory is authoritative.

Develop THIS business truth into an original physical symbol construction.
Do not replace it with a more obvious generic interpretation of the
business.

The final concept must visibly communicate this territory's specific:
customer problem, business mechanism, transformation, value, and authentic
domain signal.

Do not collapse back into another common territory such as
"many fragments converge into one flow" unless that is explicitly the
assigned territory.

============================================================
ALREADY ACCEPTED VISUAL CONSTRUCTIONS IN THIS BATCH
============================================================

{accepted_visual_context if accepted_visual_history else "None yet."}

These are successful directions already represented in the batch.

Do NOT reject or avoid an authentic industry object merely because another
concept also relates to that industry. Instead reserve the actual successful
VISUAL TOPOLOGY.

For every accepted construction above:
- do not repeat its dominant silhouette;
- do not repeat its component arrangement;
- do not repeat its defining positive/negative-space relationship;
- do not reproduce the same transformed object with cosmetic changes;
- do not merely rotate, mirror, recolor, widen, narrow, or rename it.

Example:
If an accepted mark is a vertical coffee-seed silhouette with a narrow
central thermal seam, another coffee-related concept is still allowed, but
it must NOT be another vertical/split bean with a central seam.

Remain recognizably relevant to the business. Do not escape duplication by
inventing arbitrary geometry.

============================================================
STEP 1 Ã¢â‚¬â€ CLASSIFY THE DOMAIN
============================================================

Classify this business into the most useful visual-domain type:

physical-product
physical-service
place-environment
process-service
digital-system
knowledge-service
hybrid

This classification controls HOW industry relevance should appear.

For PHYSICAL businesses:
authentic objects, materials, production processes, tools,
transformations and physical phenomena may inform the identity.

For PROCESS / DIGITAL / KNOWLEDGE businesses:
prefer process behavior, relationships, transitions, orchestration,
flow, state change, organization, cause-and-effect or customer
outcomes instead of pretending the industry has a physical object.

============================================================
STEP 2 Ã¢â‚¬â€ DISCOVER AUTHENTIC DOMAIN SIGNALS
============================================================

Identify authentic cues belonging to the industry.

Possible cues include:

materials
processes
mechanisms
relationships
behaviors
tools
states
transformations
structural principles
craft methods
environmental features
customer interactions

Do NOT automatically choose the most famous industry icon.

Examples of weak automatic reasoning:

technology -> circuit
technology -> microchip
bakery -> chef hat
construction -> generic house
healthcare -> medical cross
finance -> dollar sign
education -> generic book

These can be used only when transformed in a genuinely distinctive
way and specifically justified by the company.

============================================================
STEP 3 Ã¢â‚¬â€ UNDERSTAND THIS BUSINESS
============================================================

Determine:

BEFORE:
What problem or condition exists before the customer uses the company?

MECHANISM:
What does this company actually do?

AFTER:
What changes afterward?

VALUE:
What meaningful customer value results?

============================================================
STEP 4 Ã¢â‚¬â€ CROSS DOMAIN + BUSINESS
============================================================

The concept must come from:

AUTHENTIC DOMAIN SIGNAL
+
SPECIFIC BUSINESS TRANSFORMATION
+
DISTINCTIVE VISUAL METAPHOR

Reject both extremes:

A) literal stock industry clipart

and

B) meaningless abstraction that could belong to any company.

============================================================
STEP 5 Ã¢â‚¬â€ CONSTRUCT THE SYMBOL
============================================================

Do not merely say:

"an abstract symbol representing integration"

or:

"a modern icon representing growth."

Describe the physical construction.

Explain:

what components exist
how the components differ
how they interact
what changes
what negative space means
what creates the silhouette
where the industry signal appears
where the business-specific idea appears

The symbol should tell the concept through FORM.

============================================================
LOGO ABSTRACTION TEST
============================================================

Before approving the idea, ask:

Could this work:
- at 32 pixels
- as an app icon
- embroidered at small size
- printed in one color

If the concept requires an engineering scene, landscape,
complex illustration or many small details, SIMPLIFY IT.

The image generator should receive a symbol construction,
not an illustration scene.

============================================================
ORIGINALITY TEST
============================================================

Reject the idea if it primarily resembles:

generic swoosh
generic wave
generic ring
infinity sign
shield
hexagon
random triangle
butterfly
wings
generic leaf
generic star
meaningless network
random polygons
stock technology symbol

unless that resemblance is genuinely essential to the specific
business concept.

Do not create letters or initials unless explicitly requested.

============================================================
IMAGE REQUIREMENTS
============================================================

Generate ONE symbol only.

Our own software handles typography.

Therefore:

NO business name
NO words
NO letters
NO initials
NO slogan
NO typography

Professional commercial identity artwork.

Flat front-facing appearance.

Strong silhouette.

Intentional negative space.

Centered isolated mark.

Pure white background.

Follow the requested color direction.

No:
mockup
wall
stationery
photography
3D extrusion
bevel
glass
metal
texture
dramatic lighting
drop shadow

============================================================
RETURN JSON ONLY
============================================================

Return:

{{
  "domain_type": "",
  "authentic_domain_cues": [],
  "cliches_to_avoid": [],
  "concept_level": "{level["name"]}",
  "concept_name": "",
  "business_problem": "",
  "business_mechanism": "",
  "business_transformation": "",
  "business_value": "",
  "domain_signal": "",
  "business_signal": "",
  "visual_metaphor": "",
  "physical_construction": "",
  "industry_signal": "",
  "distinctive_idea": "",
  "why_not_generic": "",
  "image_prompt": ""
}}

The image_prompt must be complete and standalone.

It must explain the actual physical construction of the symbol and
must preserve BOTH:

industry/domain relevance
AND
business-specific meaning.
"""

    direction = _gemini_json(
        prompt,
        temperature=1.15,
    )

    image_prompt = str(
        direction.get(
            "image_prompt",
            "",
        )
    ).strip()

    if not image_prompt:
        raise RuntimeError(
            "Gemini returned no image_prompt."
        )

    direction[
        "industry_label"
    ] = industry

    direction[
        "industry_family"
    ] = str(
        direction.get(
            "domain_type",
            "business-semantic",
        )
    )

    direction[
        "logo_elements"
    ] = list(
        direction.get(
            "authentic_domain_cues",
            [],
        )
    )

    if isinstance(semantic_territory, dict):
        direction["semantic_territory"] = dict(
            semantic_territory
        )

    return direction



def audit_art_direction_with_gemini(
    direction: dict,
    business_name: str,
    industry: str,
    description: str,
    style: str = "modern",
    creative_prompt: str = "",
) -> dict:
    """
    Audit Gemini's proposed concept BEFORE image generation.

    The auditor checks whether the concept is actually grounded in
    both the industry/domain and the specific business, and rewrites
    clich? or visually ambiguous directions before Flux sees them.
    """

    concept_json = json.dumps(
        direction,
        ensure_ascii=False,
        indent=2,
    )

    prompt = f"""
You are the design-review director at a world-class identity studio.

Another creative director proposed the following logo concept.

BUSINESS NAME:
{business_name}

INDUSTRY:
{industry}

WHAT THE BUSINESS ACTUALLY DOES:
{description or "No detailed description supplied."}

REQUESTED STYLE:
{style}

USER DIRECTION:
{creative_prompt or "none"}

PROPOSED CONCEPT:

{concept_json}

============================================================
YOUR JOB
============================================================

Audit the concept BEFORE an image generator receives it.

Do not judge how impressive the written explanation sounds.

Judge what the PHYSICAL CONSTRUCTION is likely to look like.

The final symbol must succeed simultaneously at:

1. INDUSTRY / DOMAIN RELEVANCE
2. BUSINESS-SPECIFIC RELEVANCE
3. DISTINCTIVENESS
4. LOGO SIMPLICITY
5. SMALL-SIZE READABILITY
6. NON-CLICHE QUALITY

============================================================
ACCIDENTAL RESEMBLANCE TEST
============================================================

Imagine the proposed construction as a black silhouette.

Ask whether an ordinary viewer is likely to see primarily:

a letter
monogram
anchor
trident
shield
badge
generic swoosh
generic wave
generic ring
infinity symbol
butterfly
wings
leaf
flower
target
orbit
generic arrow
generic checkmark
random polygon
stock technology logo
unrelated object

If yes, the concept must be revised unless that object is genuinely
appropriate and meaningful for this exact business.

============================================================
INDUSTRY TEST
============================================================

The design should belong authentically to the stated domain.

But DO NOT solve this by reverting to stock industry icons.

Examples of weak solutions:

technology -> chip/circuit/cloud
construction -> generic house/building
bakery -> plain chef hat/wheat
healthcare -> plain medical cross
finance -> dollar sign

Instead preserve authentic domain behavior, process, structure,
material, relationship, craft or transformation.

============================================================
BUSINESS TEST
============================================================

The symbol must encode something about what THIS company does.

A symbol that could equally represent 100 unrelated companies is too
generic.

============================================================
CONTRADICTION TEST
============================================================

Check that the proposed construction actually expresses the written
business idea.

Example:

If the business concept says independent systems remain distinct while
becoming coordinated, the construction must not simply fuse all parts
into one anonymous shape.

============================================================
LOGO TEST
============================================================

The construction must be simple enough to:

work at 32px,
work in one color,
be embroidered,
have a memorable silhouette.

Reject illustration scenes or excessive detail.

============================================================
DECISION
============================================================

If the existing concept is excellent, preserve it.

If it has problems, revise its PHYSICAL EXECUTION and production prompt.

CRITICAL SEMANTIC PRESERVATION RULE:

The ASSIGNED SEMANTIC TERRITORY inside PROPOSED CONCEPT is authoritative.
You are an execution auditor, not a second concept generator.

You MUST NOT replace the assigned business truth with another territory.
You MUST NOT turn distinct ideas such as origin, porosity, timing,
volatile release, routing, continuity, verification, or customer relief
into a generic alternate concept merely because that alternate concept
is easier to draw.

The revised construction must still visibly express the SAME:
- business_truth
- business_mechanism
- customer_transformation
- customer_value
- authentic_domain_signal
- distinctive_semantic_angle

You may change topology, component arrangement, silhouette, negative
space, and rendering instructions when needed to make that SAME territory
clearer and more logo-like.

Do NOT throw away a good underlying business idea merely because the
first geometry is weak.

Return ONLY JSON:

{{
  "decision": "APPROVE or REVISE",
  "industry_relevance_score": 0,
  "business_relevance_score": 0,
  "distinctiveness_score": 0,
  "small_size_score": 0,
  "non_cliche_score": 0,
  "accidental_resemblance": "",
  "problems": [],
  "preserved_core_idea": "",
  "revised_concept_name": "",
  "revised_visual_metaphor": "",
  "revised_physical_construction": "",
  "revised_image_prompt": ""
}}

Even when decision is APPROVE, provide a complete
revised_image_prompt suitable for direct image generation.
"""

    audit = _gemini_json(
        prompt,
        temperature=0.55,
    )

    revised_prompt = str(
        audit.get(
            "revised_image_prompt",
            "",
        )
    ).strip()

    if not revised_prompt:
        revised_prompt = str(
            direction.get(
                "image_prompt",
                "",
            )
        ).strip()

    result = dict(direction)

    result["audit"] = audit

    # The auditor may repair physical execution, but it must not become
    # a second creative director and rename/reframe the assigned territory.
    # Preserve concept_name and visual_metaphor from the original direction.
    if audit.get("revised_physical_construction"):
        result["physical_construction"] = str(
            audit["revised_physical_construction"]
        ).strip()

    result["image_prompt"] = revised_prompt

    return result



def review_generated_symbol_with_gemini(
    image_bytes: bytes,
    business_name: str,
    industry: str,
    description: str,
    direction: dict,
    accepted_visual_history: list[dict] | None = None,
) -> dict:
    """
    Gemini Vision reviews what Flux ACTUALLY generated.

    The reviewer judges the visible result rather than trusting the
    intended prompt. It may reject a technically valid image when the
    image has become an unrelated object, clich?, generic mark, or
    weak representation of the business.
    """

    accepted_visual_history = accepted_visual_history or []
    accepted_visual_context = json.dumps(
        accepted_visual_history,
        ensure_ascii=False,
        indent=2,
    )

    encoded = base64.b64encode(
        image_bytes
    ).decode("ascii")

    concept_name = str(
        direction.get(
            "concept_name",
            "",
        )
    )

    intended_metaphor = str(
        direction.get(
            "visual_metaphor",
            "",
        )
    )

    intended_construction = str(
        direction.get(
            "physical_construction",
            "",
        )
    )

    current_image_prompt = str(
        direction.get(
            "image_prompt",
            "",
        )
    )
    previous_redesign = str(
        direction.get(
            "vision_redesign_strategy",
            "",
        )
    )
    failed_families = direction.get(
        "vision_failed_families",
        [],
    )
    if not isinstance(failed_families, list):
        failed_families = []
    failed_families_text = (
        ", ".join(
            str(item)
            for item in failed_families
            if str(item).strip()
        )
        or "None yet."
    )

    prompt = f"""
You are the final visual quality director for a professional
brand-identity system.

You are reviewing the ACTUAL pixels produced by an image model.

You have TWO jobs:
1. judge what the image visibly became;
2. if it fails, engineer a physically different construction for
   the next generation attempt.

BUSINESS NAME:
{business_name}

INDUSTRY:
{industry}

WHAT THE BUSINESS ACTUALLY DOES:
{description or "No detailed description supplied."}

INTENDED CONCEPT:
{concept_name}

INTENDED METAPHOR:
{intended_metaphor}

INTENDED PHYSICAL CONSTRUCTION:
{intended_construction}

CURRENT IMAGE-GENERATION PROMPT:
{current_image_prompt or "No current prompt supplied."}

PREVIOUS VISION REDESIGN:
{previous_redesign or "This is the first Vision review."}

VISUAL FAMILIES ALREADY REJECTED IN THIS GENERATION:
{failed_families_text}

Every family listed above is prohibited in the next redesign.
Do not return to an earlier rejected family under a new description.

ALREADY ACCEPTED VISUAL CONSTRUCTIONS IN THIS BATCH:
{accepted_visual_context if accepted_visual_history else "None yet."}

BATCH DIVERSITY RULE:

Accepted constructions are not "bad" or forbidden industry subjects.
They are RESERVED successful visual territory.

If the ACTUAL pixels substantially duplicate a previously accepted mark's
dominant silhouette + component arrangement + defining internal relationship,
the current candidate must be REJECTED for insufficient batch distinctiveness.

Do not call two marks duplicates merely because both authentically reference
the same industry. Judge construction/topology, not just subject category.

For example, two coffee-related marks may both be valid, but two vertical
split-bean silhouettes with a narrow central seam are the same visual
territory even if their written concepts differ.

============================================================
JUDGE THE ACTUAL IMAGE
============================================================

First determine what an ordinary viewer would say this image
actually looks like.

Do not give credit merely because the intended written concept is
good. Score the visible pixels.

At the same time, do NOT reject an otherwise strong logo merely because
the renderer simplified the intended metaphor or omitted a literal component
from the written construction.

The written prompt is CREATIVE GUIDANCE, not an engineering blueprint.

Judge the ACTUAL MARK primarily as a commercial identity:

- Does it authentically belong to this industry/domain?
- Does it retain a meaningful connection to what this business does?
- Is it visually coherent and professionally usable?
- Does it contain a distinctive treatment beyond a plain stock icon?
- Is it memorable and readable at logo scale?
- Does it avoid strongly resembling an unrelated object?

CRITICAL REVIEW CALIBRATION:

Missing prompt details are NOT by themselves a valid primary reason to
REJECT.

Do not reject merely because:
- a requested bracket is absent;
- a microscopic matrix was simplified;
- an exact thermal zone was not reproduced;
- an intended component count changed;
- the renderer found a simpler expression of the same core idea.

Those are prompt-compliance observations, not automatically logo failures.

Reject when the simplification actually makes the visible mark generic,
misleading, unrelated, clich?d, confusing, or commercially weak.

For example, valid failures include:
- a bar chart instead of a business-relevant symbol;
- generated words or pseudo-text;
- a pharmaceutical-looking mark for a coffee roaster;
- an unrelated building, pillar, spinner, or crypto-like monogram;
- a completely ordinary stock coffee bean with no distinctive intervention.

If the renderer discarded literal details but left a coherent, distinctive,
professional mark that authentically belongs to this business and visibly
retains a meaningful part of its core idea, it may PASS.

A generic symbol usable by hundreds of unrelated businesses should still
score poorly.

Strongly penalize accidental resemblance to unrelated objects or
stock logo families, including:

letter or monogram
anchor or trident
architectural columns
building or gate
generic bridge
bar chart
book
generic leaf or flower
butterfly or wings
shield or badge
hexagon
circle badge
loading spinner
orbit
generic swoosh
generic wave
target
infinity sign
generic arrow
generic checkmark
random polygon
generic nodes/network
circuit/chip
stock technology logo

Also penalize generated words, business names, letters, typography,
watermarks or pseudo-text. This stage must contain SYMBOL ONLY.

RECOGNIZABLE DOMAIN IMAGERY:

Recognizability is NOT itself a clich?.

An authentic domain object can be a strong commercial logo when it receives
a visible business-specific transformation, process cue, internal
relationship, negative-space idea, or distinctive structural treatment.

For a specialty coffee roaster:
- an unchanged stock coffee bean is weak;
- a coffee seed meaningfully transformed by roasting, origin, craft,
  precision, freshness, or flavor expression may be strong.

Judge the treatment and relevance, not merely whether the underlying subject
is recognizable.

============================================================
LOGO QUALITY
============================================================

The visible mark should have:
a memorable silhouette;
professional commercial identity quality;
clear construction;
small-size readability;
limited detail;
no illustration-like complexity;
no dependency on gradients, glow, texture or 3D rendering.

============================================================
SCORING
============================================================

Score each from 0 to 10:

industry_relevance
business_relevance
concept_visibility
distinctiveness
professional_quality
small_size_readability
non_cliche_quality

PASS only if ALL these critical scores are at least 6:

industry_relevance
business_relevance
distinctiveness
professional_quality
non_cliche_quality

concept_visibility must still be scored honestly, but it is NOT an
independent hard-failure threshold when the renderer simplified the intended
metaphor and the resulting mark remains a strong expression of the same core
business/domain idea.

============================================================
STRUCTURAL REDESIGN WHEN REJECTED
============================================================

If the decision is REJECT, do NOT merely add adjectives to the old
prompt.

STEP 1: IDENTIFY THE FAILED VISUAL FAMILY.

Set failed_visual_family to a short concrete classification such as:

amorphous-splash
spinner-ring
swoosh-circle
letter-monogram
architectural-columns
badge-shield
node-network
wave-ribbon
generic-polygon
illustrative-object
generated-text
other

Classify what the ACTUAL IMAGE became, not what was intended.

STEP 2: ABANDON THAT VISUAL FAMILY.

The next construction must not retain the failed silhouette,
topology, component arrangement or dominant visual grammar.

If PREVIOUS VISION REDESIGN is present and it also failed, do not
simply repeat that redesign.

STEP 3: PRESERVE BUSINESS SEMANTICS, NOT FAILED GEOMETRY.

Only reach structural redesign because the ACTUAL visible mark failed as a
brand identity. Do not redesign merely because Flux simplified the written
construction.

Keep the strongest useful business idea, but invent a physically
different way to represent it.

The concept should cross:

AUTHENTIC DOMAIN SIGNAL
+
SPECIFIC BUSINESS TRANSFORMATION
+
DISTINCTIVE PHYSICAL CONSTRUCTION

For digital, process and knowledge businesses, prefer meaningful
system behavior such as:

coordination
handoff
sequencing
state change
dependency
reconciliation
orchestration
convergence
controlled transformation

Do not substitute a stock technology icon.

STEP 4: SPECIFY EXACT TOPOLOGY.

The redesign_strategy MUST concretely state:

- exact number of primary components;
- basic form of those components;
- their spatial arrangement;
- what begins separated;
- where and how interaction occurs;
- what visibly changes after interaction;
- final outer silhouette;
- role of positive and negative space.

Avoid vague language such as:

dynamic geometric forms
innovative abstract mark
modern technology symbol
connected elements
fluid shapes
futuristic logo

The redesign must be drawable from the description.

STEP 5: DO NOT REPLACE ONE CLICHE WITH ANOTHER.

Unless genuinely essential to this exact business, the redesign
must NOT use:

circle or enclosing ring
loading spinner
orbit
swoosh
wave
infinity loop
arrow
checkmark
nodes/network diagram
circuit
chip
hexagon
shield
badge
letter
initial
monogram
architectural columns
building facade
generic bridge
random polygon

A rejection of one stock family is not permission to choose another.

STEP 6: FORCE SYMBOL-ONLY FLAT PRODUCTION.

The revised image prompt must explicitly require:

exactly ONE isolated logo symbol
NO words
NO business name
NO letters
NO typography
NO pseudo-text
NO watermark
NO mockup
plain white background
flat solid brand-color regions
hard clean vector-like edges
no gradients
no glow
no shadows
no 3D
no photorealism
no texture
simple silhouette readable at 32px

The revised prompt must describe what the generator should DRAW,
including topology and interaction, rather than only describing what
the brand should FEEL like.

The revised_image_prompt must be complete and self-contained because
the image generator cannot see this review or the previous image.

Return ONLY JSON:

{{
  "looks_like": "",
  "industry_relevance": 0,
  "business_relevance": 0,
  "concept_visibility": 0,
  "distinctiveness": 0,
  "professional_quality": 0,
  "small_size_readability": 0,
  "non_cliche_quality": 0,
  "decision": "PASS or REJECT",
  "primary_failure": "",
  "failed_visual_family": "",
  "redesign_strategy": "",
  "revised_image_prompt": ""
}}
"""

    url = (
        f"{GEMINI_API_BASE}/models/"
        f"{GEMINI_MODEL}:generateContent"
    )

    last_response = None

    for attempt in range(5):

        response = requests.post(
            url,
            headers={
                "x-goog-api-key": GEMINI_API_KEY,
                "Content-Type": "application/json",
            },
            json={
                "contents": [
                    {
                        "parts": [
                            {
                                "text": prompt,
                            },
                            {
                                "inline_data": {
                                    "mime_type": "image/jpeg",
                                    "data": encoded,
                                }
                            },
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.3,
                    "responseMimeType": (
                        "application/json"
                    ),
                },
            },
            timeout=120,
        )

        last_response = response

        if response.status_code == 200:
            break

        if response.status_code in (
            429,
            503,
        ):
            time.sleep(
                4 + attempt * 4
            )
            continue

        response.raise_for_status()

    if (
        last_response is None
        or last_response.status_code != 200
    ):
        raise RuntimeError(
            "Gemini visual review failed after retries."
        )

    payload = last_response.json()

    try:
        raw = (
            payload["candidates"][0]
            ["content"]["parts"][0]["text"]
        )
    except (
        KeyError,
        IndexError,
        TypeError,
    ) as error:
        raise RuntimeError(
            "Gemini Vision returned an unexpected response."
        ) from error

    review = _extract_json(
        raw
    )

    score_fields = [
        "industry_relevance",
        "business_relevance",
        "concept_visibility",
        "distinctiveness",
        "professional_quality",
        "small_size_readability",
        "non_cliche_quality",
    ]

    numeric_scores = []

    for field in score_fields:
        try:
            numeric_scores.append(
                float(
                    review.get(
                        field,
                        0,
                    )
                )
            )
        except (
            TypeError,
            ValueError,
        ):
            numeric_scores.append(
                0.0
            )

    review["average_score"] = (
        sum(numeric_scores)
        / len(numeric_scores)
    )

    return review


AI_HORDE_BASE = "https://aihorde.net/api/v2"
AI_HORDE_ANONYMOUS_KEY = "0000000000"
AI_HORDE_MODEL = "PixelWave FLUX.1-dev 03"
AI_HORDE_CLIENT_AGENT = "AI-Brand-Automation:0.1:anonymous"


def _ai_horde_headers() -> dict:
    """
    Anonymous AI Horde only.

    Never read a personal Horde token, Pollinations key,
    OmniRoute key, or any paid-provider credential here.
    """
    return {
        "apikey": AI_HORDE_ANONYMOUS_KEY,
        "Client-Agent": AI_HORDE_CLIENT_AGENT,
        "Content-Type": "application/json",
    }


def _build_ai_horde_logo_prompt(
    prompt: str,
) -> str:
    return f"""
{prompt.strip()}
FINAL PRODUCTION INSTRUCTIONS:
Create exactly ONE professional brand identity symbol.
The symbol must preserve the industry/domain signal described above
AND the business-specific concept.
Do not replace the idea with unrelated abstract geometry.
No company name.
No text.
No words.
No letters.
No initials.
No slogan.
No captions.
Pure white background.
Centered isolated symbol.
The symbol should occupy roughly 55 to 65 percent of the square canvas.
Strong clean silhouette.
Controlled contours.
Meaningful negative space when appropriate.
Flat identity artwork.
Use only solid flat colors.
No gradients.
No color blending.
No logo presentation sheet.
No multiple alternatives.
No business card.
No wall mockup.
No photography.
No 3D extrusion.
No bevel.
No glass.
No metal.
No texture.
No dramatic lighting.
No drop shadow.
The result must remain understandable at small logo size.
""".strip()


def submit_ai_horde_symbol(
    prompt: str,
    seed: int,
    width: int = 1024,
    height: int = 1024,
) -> dict:
    """
    Submit exactly one anonymous/free AI Horde image job.

    This function never waits for generation and never performs
    paid/provider fallback. The returned job ID can be persisted.
    """
    render_width = min(max(int(width), 256), 512)
    render_height = min(max(int(height), 256), 512)

    final_prompt = _build_ai_horde_logo_prompt(prompt)

    payload = {
        "prompt": final_prompt,
        "params": {
            "width": render_width,
            "height": render_height,
            "steps": 20,
            "n": 1,
            "seed": str(int(seed)),
        },
        "models": [AI_HORDE_MODEL],
        "nsfw": False,
        "censor_nsfw": True,
        "r2": True,
    }

    print(
        "[logo-ai] Submitting FREE ANONYMOUS AI Horde symbol "
        f"(model={AI_HORDE_MODEL}, seed={seed}, "
        f"size={render_width}x{render_height})"
    )

    try:
        response = requests.post(
            f"{AI_HORDE_BASE}/generate/async",
            headers=_ai_horde_headers(),
            json=payload,
            timeout=30,
        )
    except Exception as exc:
        raise RuntimeError(
            "Anonymous AI Horde submission failed. "
            "Paid fallback is disabled."
        ) from exc

    if not response.ok:
        raise RuntimeError(
            "Anonymous AI Horde rejected generation. "
            f"HTTP {response.status_code}; "
            f"response={response.text[:500]!r}. "
            "Paid fallback is disabled."
        )

    try:
        submitted = response.json()
    except ValueError as exc:
        raise RuntimeError(
            "Anonymous AI Horde returned invalid submission JSON."
        ) from exc

    job_id = str(submitted.get("id") or "").strip()

    if not job_id:
        raise RuntimeError(
            "Anonymous AI Horde did not return a job ID."
        )

    result = {
        "job_id": job_id,
        "model": AI_HORDE_MODEL,
        "reported_kudos": submitted.get("kudos"),
        "width": render_width,
        "height": render_height,
        "seed": int(seed),
    }

    print(
        "[logo-ai] AI Horde job accepted anonymously: "
        f"{job_id}; reported_kudos={submitted.get('kudos')}"
    )

    return result


def check_ai_horde_job(
    job_id: str,
) -> dict:
    """
    Read queue/progress state without submitting another generation.
    """
    clean_job_id = str(job_id or "").strip()

    if not clean_job_id:
        raise ValueError("AI Horde job ID is required.")

    try:
        response = requests.get(
            f"{AI_HORDE_BASE}/generate/check/{clean_job_id}",
            timeout=30,
        )
        response.raise_for_status()
        status = response.json()
    except Exception as exc:
        raise RuntimeError(
            "Anonymous AI Horde status check failed."
        ) from exc

    return {
        "job_id": clean_job_id,
        "done": bool(status.get("done")),
        "faulted": bool(status.get("faulted")),
        "waiting": int(status.get("waiting") or 0),
        "processing": int(status.get("processing") or 0),
        "finished": int(status.get("finished") or 0),
        "queue_position": status.get("queue_position"),
        "wait_time": status.get("wait_time"),
        "raw": status,
    }


def collect_ai_horde_job(
    job_id: str,
) -> bytes:
    """
    Retrieve and download a completed anonymous AI Horde image.

    Does not submit, retry, or fall back to another provider.
    """
    clean_job_id = str(job_id or "").strip()

    if not clean_job_id:
        raise ValueError("AI Horde job ID is required.")

    try:
        response = requests.get(
            f"{AI_HORDE_BASE}/generate/status/{clean_job_id}",
            timeout=30,
        )
        response.raise_for_status()
        completed = response.json()
    except Exception as exc:
        raise RuntimeError(
            "Could not retrieve completed anonymous AI Horde job."
        ) from exc

    if completed.get("faulted"):
        raise RuntimeError(
            "Anonymous AI Horde job faulted. "
            "Paid fallback is disabled."
        )

    if not completed.get("done"):
        raise RuntimeError(
            "Anonymous AI Horde job is not complete yet."
        )

    generations = completed.get("generations")

    if not isinstance(generations, list) or not generations:
        raise RuntimeError(
            "Anonymous AI Horde completed without an image."
        )

    first = generations[0]
    if not isinstance(first, dict):
        raise RuntimeError(
            "Anonymous AI Horde returned invalid generation data."
        )

    image_url = str(first.get("img") or "").strip()

    if not image_url.startswith(("https://", "http://")):
        raise RuntimeError(
            "Anonymous AI Horde returned an invalid image URL."
        )

    try:
        image_response = requests.get(
            image_url,
            timeout=60,
        )
        image_response.raise_for_status()
        image_bytes = image_response.content
    except Exception as exc:
        raise RuntimeError(
            "Could not download anonymous AI Horde image."
        ) from exc

    if len(image_bytes) < 5000:
        raise RuntimeError(
            "Anonymous AI Horde returned unexpectedly small image data."
        )

    print(
        "[logo-ai] FREE ANONYMOUS AI Horde image downloaded: "
        f"{len(image_bytes)} bytes"
    )

    return image_bytes



class PersistentHordeStateError(RuntimeError):
    """Persistent Horde state is unsafe or internally inconsistent."""


def generate_symbol_with_ai_horde_persistent(
    prompt: str,
    seed: int,
    attempt_index: int,
    context: dict,
    width: int = 1024,
    height: int = 1024,
) -> bytes:
    """
    Persistent anonymous AI Horde execution.

    A remote job ID is committed immediately after submission. If this
    process restarts, the same database job can resume checking the same
    Horde UUID instead of submitting another image merely due to queue
    delay or process loss.
    """
    import hashlib
    import json

    db = context.get("db")
    job = context.get("job")

    if db is None or job is None:
        raise RuntimeError(
            "Persistent Horde generation requires database job context."
        )

    prompt_fingerprint = hashlib.sha256(
        prompt.encode("utf-8")
    ).hexdigest()

    try:
        state = json.loads(job.state_json) if job.state_json else {}
    except Exception:
        state = {}

    horde = state.get("horde")
    if not isinstance(horde, dict):
        horde = {}

    active_id = str(job.active_horde_job_id or "").strip()

    # -----------------------------------------------------
    # Resolve the persisted attempt before doing anything.
    # -----------------------------------------------------
    resume_existing = False

    if active_id:
        recorded_seed = horde.get("seed")
        recorded_attempt = horde.get("attempt_index")
        recorded_state = str(
            horde.get("state") or ""
        ).strip().lower()

        same_attempt = (
            str(recorded_seed) == str(int(seed))
            and str(recorded_attempt) == str(int(attempt_index))
        )

        if same_attempt:
            # Restart/re-entry of exactly the same attempt:
            # use the already-submitted anonymous Horde UUID.
            resume_existing = True

        elif recorded_state == "collected":
            # The old attempt completed and returned bytes to the
            # quality/Vision pipeline. Advancing to the next deliberate
            # attempt is legitimate, so archive the old record first.
            history = state.get("horde_history")
            if not isinstance(history, list):
                history = []

            history.append(dict(horde))
            state["horde_history"] = history[-12:]
            state.pop("horde", None)

            job.active_horde_job_id = None
            job.state_json = json.dumps(state)
            db.commit()

            active_id = ""
            horde = {}

            print(
                "[logo-ai] Previous Horde attempt collected; "
                "advancing to the next deliberate attempt."
            )

        else:
            # An unrelated attempt is still queued/rendering/faulted or
            # its identity is incomplete. Never overwrite it or submit
            # another remote image.
            raise PersistentHordeStateError(
                "Persistent Horde attempt identity mismatch; "
                "refusing to submit or reuse another remote job."
            )

    # -----------------------------------------------------
    # Either resume the exact persisted attempt or submit
    # exactly one new anonymous/free job.
    # -----------------------------------------------------
    if resume_existing:
        job_id = active_id

        print(
            "[logo-ai] Resuming persisted FREE ANONYMOUS AI Horde job:",
            job_id,
        )

    else:
        submission = submit_ai_horde_symbol(
            prompt=prompt,
            seed=seed,
            width=width,
            height=height,
        )
        job_id = submission["job_id"]

        job.active_horde_job_id = job_id

        state["phase"] = "queued"
        state["horde"] = {
            "job_id": job_id,
            "attempt_index": int(attempt_index),
            "seed": int(seed),
            "prompt_sha256": prompt_fingerprint,
            "prompt": prompt,
            "model": submission.get("model"),
            "state": "submitted",
            "queue_position": None,
            "wait_time": None,
        }

        job.state_json = json.dumps(state)
        job.progress_message = (
            "Logo artwork submitted to free anonymous AI Horde."
        )
        db.commit()

        print(
            "[logo-ai] Persisted anonymous Horde job before waiting:",
            job_id,
        )

    while True:
        status = check_ai_horde_job(job_id)

        # Refresh in case state changed since the last commit.
        try:
            state = json.loads(job.state_json) if job.state_json else {}
        except Exception:
            state = {}

        horde = state.get("horde")
        if not isinstance(horde, dict):
            horde = {}

        horde.update({
            "job_id": job_id,
            "attempt_index": int(attempt_index),
            "seed": int(seed),
            "prompt_sha256": horde.get(
                "prompt_sha256",
                prompt_fingerprint,
            ),
            "prompt": horde.get("prompt", prompt),
            "queue_position": status.get("queue_position"),
            "wait_time": status.get("wait_time"),
            "waiting": status.get("waiting"),
            "processing": status.get("processing"),
            "finished": status.get("finished"),
        })

        if status["faulted"]:
            horde["state"] = "faulted"
            state["phase"] = "failed"
            state["horde"] = horde
            job.state_json = json.dumps(state)
            job.progress_message = (
                "Anonymous AI Horde reported a generation fault."
            )
            db.commit()

            raise RuntimeError(
                "Anonymous AI Horde job faulted. "
                "Paid fallback is disabled."
            )

        if status["done"]:
            horde["state"] = "downloading"
            state["phase"] = "rendering"
            state["horde"] = horde
            job.state_json = json.dumps(state)
            job.progress_message = (
                "Artwork rendered; downloading for quality review."
            )
            db.commit()

            image_bytes = collect_ai_horde_job(job_id)

            # Mark this exact remote attempt as collected before returning.
            # Keep its identity in state_json as recovery/audit history.
            try:
                state = (
                    json.loads(job.state_json)
                    if job.state_json
                    else {}
                )
            except Exception:
                state = {}

            horde = state.get("horde")
            if not isinstance(horde, dict):
                horde = {}

            horde["state"] = "collected"
            horde["job_id"] = job_id
            state["phase"] = "reviewing"
            state["horde"] = horde

            job.state_json = json.dumps(state)
            job.progress_message = (
                "Artwork received; running technical and Gemini Vision review."
            )

            # Keep the completed UUID associated with this attempt.
            # The next deliberate attempt archives/clears it. If the
            # process dies during Vision review, restart can still
            # identify the exact completed remote render.
            job.active_horde_job_id = job_id
            db.commit()

            return image_bytes

        if status.get("processing"):
            horde["state"] = "rendering"
            state["phase"] = "rendering"
            message = (
                "Free anonymous AI Horde is rendering the logo artwork."
            )
        else:
            horde["state"] = "queued"
            state["phase"] = "queued"

            queue = status.get("queue_position")
            wait = status.get("wait_time")

            details = []
            if queue is not None:
                details.append(f"queue position {queue}")
            if wait is not None:
                details.append(f"estimated wait {wait}s")

            suffix = (
                " (" + ", ".join(details) + ")"
                if details
                else ""
            )
            message = (
                "Waiting for free anonymous AI Horde capacity"
                + suffix
                + "."
            )

        state["horde"] = horde
        job.state_json = json.dumps(state)
        job.progress_message = message
        db.commit()

        print(
            "[logo-ai] Persistent AI Horde wait:",
            job_id,
            status.get("queue_position"),
            status.get("wait_time"),
        )

        time.sleep(10)


def generate_symbol_with_ai_horde(
    prompt: str,
    seed: int,
    width: int = 1024,
    height: int = 1024,
) -> bytes:
    """
    Compatibility wrapper for synchronous callers.

    Unlike the previous implementation, queue delay does NOT trigger
    cancellation or automatic resubmission. It waits for the one
    accepted anonymous job. Persistent orchestration will call the
    submit/check/collect primitives directly.
    """
    submission = submit_ai_horde_symbol(
        prompt=prompt,
        seed=seed,
        width=width,
        height=height,
    )

    job_id = submission["job_id"]

    while True:
        status = check_ai_horde_job(job_id)

        if status["faulted"]:
            raise RuntimeError(
                "Anonymous AI Horde job faulted. "
                "Paid fallback is disabled."
            )

        if status["done"]:
            return collect_ai_horde_job(job_id)

        print(
            "[logo-ai] AI Horde queued asynchronously: "
            f"job={job_id}, "
            f"queue={status.get('queue_position')}, "
            f"wait={status.get('wait_time')}, "
            f"processing={status.get('processing')}"
        )

        time.sleep(10)

def generate_ai_logo_candidate(
    business_name: str,
    industry: str,
    description: str,
    style: str,
    concept_index: int,
    seed: int,
    creative_prompt: str = "",
) -> dict:

    direction = create_art_direction_with_gemini(
        business_name=business_name,
        industry=industry,
        description=description,
        style=style,
        creative_prompt=creative_prompt,
        concept_index=concept_index,
    )

    print(
        "[LOGO AI] Auditing proposed concept before Flux..."
    )

    direction = audit_art_direction_with_gemini(
        direction=direction,
        business_name=business_name,
        industry=industry,
        description=description,
        style=style,
        creative_prompt=creative_prompt,
    )

    audit = direction.get(
        "audit",
        {},
    )

    print(
        "[LOGO AI] Audit decision:",
        audit.get(
            "decision",
            "UNKNOWN",
        ),
    )

    print(
        "[LOGO AI] Accidental resemblance:",
        audit.get(
            "accidental_resemblance",
            "",
        ),
    )

    print(
        "[LOGO AI] Scores:",
        {
            "industry": audit.get(
                "industry_relevance_score"
            ),
            "business": audit.get(
                "business_relevance_score"
            ),
            "distinctiveness": audit.get(
                "distinctiveness_score"
            ),
            "non_cliche": audit.get(
                "non_cliche_score"
            ),
        },
    )

    image_bytes = generate_symbol_with_ai_horde(
        prompt=direction[
            "image_prompt"
        ],
        seed=seed,
    )

    return {
        "generation_engine":
            "aihorde_pixelwave_flux_dev",

        "art_director":
            "gemini",

        "concept_index":
            concept_index,

        "seed":
            seed,

        "industry_label":
            direction[
                "industry_label"
            ],

        "industry_family":
            direction[
                "industry_family"
            ],

        "logo_elements":
            direction[
                "logo_elements"
            ],

        "domain_type":
            direction.get(
                "domain_type",
                "",
            ),

        "concept_level":
            direction.get(
                "concept_level",
                "",
            ),

        "concept_name":
            direction.get(
                "concept_name",
                "",
            ),

        "business_problem":
            direction.get(
                "business_problem",
                "",
            ),

        "business_mechanism":
            direction.get(
                "business_mechanism",
                "",
            ),

        "business_transformation":
            direction.get(
                "business_transformation",
                "",
            ),

        "business_value":
            direction.get(
                "business_value",
                "",
            ),

        "domain_signal":
            direction.get(
                "domain_signal",
                "",
            ),

        "business_signal":
            direction.get(
                "business_signal",
                "",
            ),

        "visual_metaphor":
            direction.get(
                "visual_metaphor",
                "",
            ),

        "physical_construction":
            direction.get(
                "physical_construction",
                "",
            ),

        "industry_signal":
            direction.get(
                "industry_signal",
                "",
            ),

        "distinctive_idea":
            direction.get(
                "distinctive_idea",
                "",
            ),

        "why_not_generic":
            direction.get(
                "why_not_generic",
                "",
            ),

        "image_prompt":
            direction[
                "image_prompt"
            ],

        "image_bytes":
            image_bytes,
    }



