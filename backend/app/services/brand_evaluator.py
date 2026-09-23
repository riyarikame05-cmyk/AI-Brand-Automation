import json
import re
from typing import Any

import requests


# =========================================================
# LOCAL OLLAMA
# =========================================================

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
OLLAMA_MODEL = "qwen2.5:3b"


# =========================================================
# HELPERS
# =========================================================

def _clamp_score(
    value: Any,
    default: int = 75,
) -> int:
    """
    Convert an arbitrary value to an integer score between
    0 and 100.
    """

    try:
        score = int(float(value))
    except (TypeError, ValueError):
        score = default

    return max(
        0,
        min(100, score),
    )


def _safe_text(
    value: Any,
) -> str:

    if value is None:
        return ""

    return str(value).strip()


def _safe_list(
    value: Any,
) -> list[str]:

    if not isinstance(
        value,
        list,
    ):
        return []

    result = []

    for item in value:

        text = _safe_text(
            item
        )

        if text:
            result.append(
                text
            )

    return result


def _valid_hex_color(
    color: str,
) -> bool:

    return bool(
        re.fullmatch(
            r"#[0-9A-Fa-f]{6}",
            _safe_text(color),
        )
    )


# =========================================================
# DETERMINISTIC BASELINE
# =========================================================

def _calculate_baseline_scores(
    *,
    business_name: str,
    industry: str,
    description: str,
    style: str,
    slogan: str,
    personality: list[str],
    tone: str,
    target_audience: str,
    marketing_message: str,
    heading_font: str,
    body_font: str,
    primary_color: str,
    secondary_color: str,
    accent_color: str,
    has_selected_logo: bool,
) -> dict[str, int]:
    """
    Produce a reliable baseline without AI.

    This means Brand Score still works when Ollama is not
    running.
    """

    # -----------------------------------------------------
    # MEMORABILITY
    # -----------------------------------------------------

    memorability = 58

    name_length = len(
        business_name.split()
    )

    if business_name:
        memorability += 8

    if 1 <= name_length <= 3:
        memorability += 7

    if slogan:
        memorability += 8

    if has_selected_logo:
        memorability += 10

    if personality:
        memorability += 4

    # -----------------------------------------------------
    # SIMPLICITY
    # -----------------------------------------------------

    simplicity = 64

    if has_selected_logo:
        simplicity += 8

    if slogan:

        slogan_words = len(
            slogan.split()
        )

        if 2 <= slogan_words <= 7:
            simplicity += 8

    if heading_font:
        simplicity += 4

    if body_font:
        simplicity += 4

    if len(personality) == 3:
        simplicity += 5

    # -----------------------------------------------------
    # INDUSTRY FIT
    # -----------------------------------------------------

    industry_fit = 55

    if industry:
        industry_fit += 10

    if style:
        industry_fit += 8

    if tone:
        industry_fit += 8

    if has_selected_logo:
        industry_fit += 7

    if description:
        industry_fit += 5

    if personality:
        industry_fit += 4

    # -----------------------------------------------------
    # VISUAL CONSISTENCY
    # -----------------------------------------------------

    visual_consistency = 52

    valid_colors = sum(
        [
            _valid_hex_color(
                primary_color
            ),
            _valid_hex_color(
                secondary_color
            ),
            _valid_hex_color(
                accent_color
            ),
        ]
    )

    visual_consistency += (
        valid_colors * 7
    )

    if has_selected_logo:
        visual_consistency += 10

    if heading_font:
        visual_consistency += 5

    if body_font:
        visual_consistency += 5

    if style:
        visual_consistency += 4

    # -----------------------------------------------------
    # COLOR EFFECTIVENESS
    # -----------------------------------------------------

    color_effectiveness = 55

    colors = [
        color.upper()
        for color in [
            primary_color,
            secondary_color,
            accent_color,
        ]
        if _valid_hex_color(
            color
        )
    ]

    color_effectiveness += (
        len(colors) * 7
    )

    if len(
        set(colors)
    ) == 3:
        color_effectiveness += 10

    if has_selected_logo:
        color_effectiveness += 5

    # -----------------------------------------------------
    # AUDIENCE FIT
    # -----------------------------------------------------

    audience_fit = 52

    if target_audience:
        audience_fit += 15

    if tone:
        audience_fit += 8

    if marketing_message:
        audience_fit += 8

    if personality:
        audience_fit += 5

    if description:
        audience_fit += 5

    # -----------------------------------------------------
    # NORMALIZE
    # -----------------------------------------------------

    return {
        "memorability":
            _clamp_score(
                memorability
            ),

        "simplicity":
            _clamp_score(
                simplicity
            ),

        "industry_fit":
            _clamp_score(
                industry_fit
            ),

        "visual_consistency":
            _clamp_score(
                visual_consistency
            ),

        "color_effectiveness":
            _clamp_score(
                color_effectiveness
            ),

        "audience_fit":
            _clamp_score(
                audience_fit
            ),
    }


# =========================================================
# OLLAMA EVALUATION
# =========================================================

def _generate_ai_evaluation(
    *,
    business_name: str,
    industry: str,
    description: str,
    style: str,
    slogan: str,
    personality: list[str],
    tone: str,
    target_audience: str,
    marketing_message: str,
    heading_font: str,
    body_font: str,
    primary_color: str,
    secondary_color: str,
    accent_color: str,
    baseline_scores: dict[str, int],
) -> dict:
    """
    Ask local Ollama for qualitative brand critique.

    Baseline scores are supplied so the model refines the
    evaluation rather than inventing completely arbitrary
    scoring.
    """

    prompt = f"""
You are a professional brand identity evaluator.

Evaluate the following brand system.

Business name: {business_name}
Industry: {industry}
Description: {description}
Style: {style}

Slogan: {slogan}
Personality: {json.dumps(personality)}
Tone: {tone}
Target audience: {target_audience}
Marketing message: {marketing_message}

Heading font: {heading_font}
Body font: {body_font}

Primary color: {primary_color}
Secondary color: {secondary_color}
Accent color: {accent_color}

The system calculated these baseline scores:

{json.dumps(baseline_scores)}

Return ONLY valid JSON using exactly this structure:

{{
    "scores": {{
        "memorability": 0,
        "simplicity": 0,
        "industry_fit": 0,
        "visual_consistency": 0,
        "color_effectiveness": 0,
        "audience_fit": 0
    }},
    "strengths": [
        "specific strength",
        "specific strength",
        "specific strength"
    ],
    "recommendations": [
        "specific actionable recommendation",
        "specific actionable recommendation",
        "specific actionable recommendation"
    ],
    "summary": "one concise professional evaluation"
}}

Rules:
- scores must be integers from 0 to 100
- stay reasonably close to the supplied baseline scores
- judge brand strategy, not factual business performance
- strengths must contain exactly 3 short items
- recommendations must contain exactly 3 actionable items
- summary must be concise
- do not include markdown
- do not invent company achievements or factual claims
"""

    response = requests.post(
        OLLAMA_URL,
        json={
            "model":
                OLLAMA_MODEL,

            "prompt":
                prompt,

            "stream":
                False,

            "format":
                "json",

            "options": {
                "temperature":
                    0.35,
            },
        },
        timeout=90,
    )

    response.raise_for_status()

    result = response.json()

    generated_text = result.get(
        "response",
        "{}",
    )

    evaluation = json.loads(
        generated_text
    )

    if not isinstance(
        evaluation,
        dict,
    ):
        raise ValueError(
            "Ollama returned invalid evaluation."
        )

    return evaluation


# =========================================================
# MERGE AI + DETERMINISTIC SCORES
# =========================================================

def _merge_scores(
    baseline_scores: dict[str, int],
    ai_scores: Any,
) -> dict[str, int]:
    """
    Keep deterministic scoring dominant.

    70% deterministic baseline
    30% Ollama refinement
    """

    if not isinstance(
        ai_scores,
        dict,
    ):
        return baseline_scores.copy()

    merged = {}

    for key, baseline in (
        baseline_scores.items()
    ):

        ai_value = _clamp_score(
            ai_scores.get(
                key,
                baseline,
            ),
            baseline,
        )

        score = round(
            (
                baseline * 0.70
            )
            +
            (
                ai_value * 0.30
            )
        )

        merged[key] = (
            _clamp_score(
                score,
                baseline,
            )
        )

    return merged


# =========================================================
# PUBLIC SERVICE
# =========================================================

def evaluate_brand(
    *,
    business_name: str,
    industry: str,
    description: str,
    style: str,
    slogan: str = "",
    personality: list[str] | None = None,
    tone: str = "",
    target_audience: str = "",
    marketing_message: str = "",
    heading_font: str = "",
    body_font: str = "",
    primary_color: str = "",
    secondary_color: str = "",
    accent_color: str = "",
    has_selected_logo: bool = False,
) -> dict:
    """
    Evaluate a complete BrandAI identity.

    The function works fully offline.

    Ollama is used when available. If Ollama fails, BrandAI
    returns a deterministic evaluation instead of breaking
    the project page.
    """

    personality = (
        personality
        if isinstance(
            personality,
            list,
        )
        else []
    )

    baseline_scores = (
        _calculate_baseline_scores(
            business_name=(
                _safe_text(
                    business_name
                )
            ),

            industry=(
                _safe_text(
                    industry
                )
            ),

            description=(
                _safe_text(
                    description
                )
            ),

            style=(
                _safe_text(
                    style
                )
            ),

            slogan=(
                _safe_text(
                    slogan
                )
            ),

            personality=(
                personality
            ),

            tone=(
                _safe_text(
                    tone
                )
            ),

            target_audience=(
                _safe_text(
                    target_audience
                )
            ),

            marketing_message=(
                _safe_text(
                    marketing_message
                )
            ),

            heading_font=(
                _safe_text(
                    heading_font
                )
            ),

            body_font=(
                _safe_text(
                    body_font
                )
            ),

            primary_color=(
                _safe_text(
                    primary_color
                )
            ),

            secondary_color=(
                _safe_text(
                    secondary_color
                )
            ),

            accent_color=(
                _safe_text(
                    accent_color
                )
            ),

            has_selected_logo=(
                bool(
                    has_selected_logo
                )
            ),
        )
    )

    # -----------------------------------------------------
    # SAFE FALLBACK
    # -----------------------------------------------------

    strengths = [
        (
            "A defined visual identity gives the brand "
            "a consistent foundation."
        ),
        (
            "Brand messaging and personality create a "
            "clear communication direction."
        ),
        (
            "The selected palette and typography support "
            "a reusable identity system."
        ),
    ]

    recommendations = [
        (
            "Test the identity at small sizes and across "
            "light and dark backgrounds."
        ),
        (
            "Apply the same colors and typography "
            "consistently across marketing materials."
        ),
        (
            "Validate the messaging with the intended "
            "target audience."
        ),
    ]

    summary = (
        "The identity has a solid brand foundation with "
        "clear opportunities to improve consistency and "
        "real-world application."
    )

    scores = (
        baseline_scores.copy()
    )

    ai_used = False

    # -----------------------------------------------------
    # OPTIONAL LOCAL AI ENRICHMENT
    # -----------------------------------------------------

    try:

        ai_evaluation = (
            _generate_ai_evaluation(
                business_name=(
                    business_name
                ),

                industry=(
                    industry
                ),

                description=(
                    description
                ),

                style=(
                    style
                ),

                slogan=(
                    slogan
                ),

                personality=(
                    personality
                ),

                tone=(
                    tone
                ),

                target_audience=(
                    target_audience
                ),

                marketing_message=(
                    marketing_message
                ),

                heading_font=(
                    heading_font
                ),

                body_font=(
                    body_font
                ),

                primary_color=(
                    primary_color
                ),

                secondary_color=(
                    secondary_color
                ),

                accent_color=(
                    accent_color
                ),

                baseline_scores=(
                    baseline_scores
                ),
            )
        )

        scores = (
            _merge_scores(
                baseline_scores,
                ai_evaluation.get(
                    "scores",
                    {},
                ),
            )
        )

        ai_strengths = (
            _safe_list(
                ai_evaluation.get(
                    "strengths"
                )
            )
        )

        ai_recommendations = (
            _safe_list(
                ai_evaluation.get(
                    "recommendations"
                )
            )
        )

        ai_summary = (
            _safe_text(
                ai_evaluation.get(
                    "summary"
                )
            )
        )

        if ai_strengths:
            strengths = (
                ai_strengths[:3]
            )

        if ai_recommendations:
            recommendations = (
                ai_recommendations[:3]
            )

        if ai_summary:
            summary = (
                ai_summary
            )

        ai_used = True

    except Exception as error:

        print(
            "[BRAND SCORE] "
            "Ollama evaluation unavailable:",
            repr(error),
        )

    # -----------------------------------------------------
    # OVERALL SCORE
    # -----------------------------------------------------

    overall_score = round(
        sum(
            scores.values()
        )
        / max(
            len(scores),
            1,
        )
    )

    return {
        "overall_score":
            _clamp_score(
                overall_score
            ),

        "scores":
            scores,

        "strengths":
            strengths,

        "recommendations":
            recommendations,

        "summary":
            summary,

        "ai_used":
            ai_used,

        "evaluation_mode":
            (
                "Local AI + deterministic analysis"
                if ai_used
                else "Deterministic analysis"
            ),
    }