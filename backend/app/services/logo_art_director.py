"""Sonnet-powered premium identity art direction via local OmniRoute."""

from __future__ import annotations

import json
from typing import Any

import requests


OMNIROUTE_URL = "http://127.0.0.1:20128/v1/chat/completions"
SONNET_MODEL = "kr/claude-sonnet-4.5"


def _fallback_directions(count: int) -> list[dict[str, Any]]:
    strategies = (
        "bespoke-monogram",
        "negative-space-glyph",
        "abstract-semantic",
        "typography-led",
        "motion-ribbon",
        "signature-emblem",
        "modular-geometry",
        "continuous-line",
        "experimental-fusion",
    )

    layouts = (
        "horizontal",
        "stacked",
        "typography-led",
        "horizontal",
        "emblem",
        "stacked",
    )

    personalities = (
        "geometric",
        "elegant",
        "modern",
        "classic",
        "bold",
        "modern",
    )

    return [
        {
            "strategy": strategies[index % len(strategies)],
            "semantic_territory": "",
            "visual_idea": "",
            "industry_form": "",
            "negative_space_idea": "",
            "typography_personality": personalities[
                index % len(personalities)
            ],
            "presentation_layout": layouts[
                index % len(layouts)
            ],
            "composition_note": "",
        }
        for index in range(max(1, count))
    ]


def _clean_direction(value: Any) -> dict[str, str]:
    value = value if isinstance(value, dict) else {}

    return {
        "strategy": str(value.get("strategy", "")).strip(),
        "semantic_territory": str(
            value.get("semantic_territory", "")
        ).strip(),
        "visual_idea": str(
            value.get("visual_idea", "")
        ).strip(),
        "industry_form": str(
            value.get("industry_form", "")
        ).strip(),
        "negative_space_idea": str(
            value.get("negative_space_idea", "")
        ).strip(),
        "typography_personality": str(
            value.get("typography_personality", "")
        ).strip(),
        "presentation_layout": str(
            value.get("presentation_layout", "")
        ).strip(),
        "composition_note": str(
            value.get("composition_note", "")
        ).strip(),
    }


def generate_art_directions(
    *,
    business_name: str,
    industry: str,
    description: str,
    style: str,
    count: int,
    creative_prompt: str = "",
) -> list[dict[str, str]]:
    """Generate one diverse art-direction plan for an entire logo batch."""

    fallback = _fallback_directions(count)

    prompt = f"""
You are the senior identity art director for a premium branding platform.

Create exactly {count} deliberately different identity directions.

Business name: {business_name}
Industry: {industry}
Business description: {description}
Requested style: {style}
Additional brief: {creative_prompt or "none"}

These directions will guide a deterministic vector identity system.
Do not draw SVG and do not return prose outside JSON.

Design principles:
- industry-aware without stock industry clip-art
- description must materially affect the concepts
- premium identity-studio thinking
- strong silhouette at 64px
- sophisticated negative space where appropriate
- deliberate typography and composition
- avoid generic logo-generator conventions
- concepts must differ in construction, not merely color

Avoid:
generic hexagons, random network nodes, stock cubes, generic shields,
brain icons, standalone leaves, droplets, swooshes, infinity signs,
house roofs, coffee cups, music notes, and decorative initials.

Allowed strategy values:
bespoke-monogram
negative-space-glyph
abstract-semantic
continuous-line
modular-geometry
signature-emblem
motion-ribbon
typography-led
experimental-fusion

Allowed typography_personality values:
modern
geometric
elegant
classic
bold

Allowed presentation_layout values:
stacked
horizontal
emblem
typography-led

Return exactly this JSON shape:
{{
  "directions": [
    {{
      "strategy": "allowed value",
      "semantic_territory": "short conceptual territory",
      "visual_idea": "specific identity construction idea",
      "industry_form": "abstract form language",
      "negative_space_idea": "meaningful void idea or none",
      "typography_personality": "allowed value",
      "presentation_layout": "allowed value",
      "composition_note": "short professional composition instruction"
    }}
  ]
}}
""".strip()

    try:
        response = requests.post(
            OMNIROUTE_URL,
            json={
                "model": SONNET_MODEL,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                "temperature": 0.72,
                "max_tokens": 1800,
            },
            timeout=75,
        )
        response.raise_for_status()

        payload = response.json()
        content = payload["choices"][0]["message"]["content"]

        content = str(content).strip()

        if content.startswith("```"):
            lines = content.splitlines()
            if lines:
                lines = lines[1:]
            if lines and lines[-1].strip().startswith("```"):
                lines = lines[:-1]
            content = "\n".join(lines).strip()

        data = json.loads(content)
        raw_directions = data.get("directions", [])

        if not isinstance(raw_directions, list):
            raise ValueError("directions must be a list")

        cleaned = [
            _clean_direction(item)
            for item in raw_directions
        ]

        cleaned = [
            item
            for item in cleaned
            if item["strategy"]
        ]

        if len(cleaned) < count:
            cleaned.extend(
                fallback[len(cleaned):count]
            )

        print(
            "[SONNET] Premium art directions ready: "
            f"{len(cleaned[:count])}"
        )

        return cleaned[:count]

    except Exception as error:
        print(
            "[SONNET] Art director unavailable, "
            "using local fallback:",
            repr(error),
        )
        return fallback
