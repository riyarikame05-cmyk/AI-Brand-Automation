"""
V5 Premium Identity Engine.

Transforms semantic brand information into diversified identity-construction
briefs. This module chooses design logic; it does not render pixels.

The renderer remains deterministic and exact.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, asdict
from typing import Iterable


STRATEGIES = (
    "bespoke-monogram",
    "negative-space-glyph",
    "abstract-semantic",
    "continuous-line",
    "modular-geometry",
    "signature-emblem",
    "motion-ribbon",
    "typography-led",
    "experimental-fusion",
)


FAMILY_TERRITORIES = {
    "technology": (
        "precision",
        "connection",
        "systems",
        "progress",
        "intelligence",
        "modularity",
    ),
    "cybersecurity": (
        "protection",
        "trust",
        "boundary",
        "verification",
        "resilience",
        "signal",
    ),
    "finance": (
        "trust",
        "stability",
        "progress",
        "structure",
        "value",
        "clarity",
    ),
    "legal": (
        "authority",
        "foundation",
        "balance",
        "clarity",
        "heritage",
        "structure",
    ),
    "healthcare": (
        "care",
        "renewal",
        "wellbeing",
        "protection",
        "humanity",
        "growth",
    ),
    "coffee": (
        "ritual",
        "warmth",
        "craft",
        "origin",
        "roast",
        "hospitality",
    ),
    "food-beverage": (
        "nourishment",
        "gathering",
        "freshness",
        "craft",
        "abundance",
        "rhythm",
    ),
    "music-audio": (
        "rhythm",
        "frequency",
        "resonance",
        "tempo",
        "expression",
        "energy",
    ),
    "education": (
        "discovery",
        "knowledge",
        "progress",
        "curiosity",
        "clarity",
        "growth",
    ),
    "real-estate": (
        "space",
        "threshold",
        "structure",
        "permanence",
        "place",
        "community",
    ),
    "travel-hospitality": (
        "journey",
        "horizon",
        "discovery",
        "welcome",
        "movement",
        "destination",
    ),
    "automotive": (
        "performance",
        "precision",
        "velocity",
        "engineering",
        "control",
        "motion",
    ),
    "logistics": (
        "flow",
        "route",
        "reliability",
        "forward-motion",
        "network",
        "efficiency",
    ),
    "fashion-beauty": (
        "expression",
        "elegance",
        "signature",
        "detail",
        "confidence",
        "transformation",
    ),
    "fitness-sports": (
        "energy",
        "strength",
        "momentum",
        "discipline",
        "performance",
        "progress",
    ),
    "nature-agriculture": (
        "growth",
        "stewardship",
        "cycle",
        "origin",
        "renewal",
        "balance",
    ),
    "water": (
        "purity",
        "flow",
        "continuity",
        "clarity",
        "renewal",
        "balance",
    ),
    "energy": (
        "power",
        "renewal",
        "radiance",
        "transition",
        "momentum",
        "efficiency",
    ),
    "gaming-entertainment": (
        "play",
        "energy",
        "world-building",
        "challenge",
        "motion",
        "character",
    ),
    "creative-media": (
        "expression",
        "frame",
        "perspective",
        "story",
        "contrast",
        "originality",
    ),
    "manufacturing-engineering": (
        "precision",
        "assembly",
        "strength",
        "systems",
        "craft",
        "reliability",
    ),
    "retail-ecommerce": (
        "discovery",
        "exchange",
        "access",
        "choice",
        "momentum",
        "connection",
    ),
    "nonprofit-community": (
        "belonging",
        "support",
        "connection",
        "uplift",
        "humanity",
        "purpose",
    ),
    "professional-services": (
        "clarity",
        "expertise",
        "trust",
        "partnership",
        "structure",
        "progress",
    ),
    "other": (
        "distinctiveness",
        "clarity",
        "character",
        "connection",
        "progress",
        "confidence",
    ),
}


STRATEGY_GRAMMARS = {
    "bespoke-monogram": {
        "construction": "shared-stroke",
        "semantic_method": "counter-or-junction",
        "silhouette": "compact",
        "max_elements": 4,
    },
    "negative-space-glyph": {
        "construction": "boolean-subtraction",
        "semantic_method": "meaningful-void",
        "silhouette": "solid",
        "max_elements": 3,
    },
    "abstract-semantic": {
        "construction": "semantic-modules",
        "semantic_method": "abstract-metaphor",
        "silhouette": "distinct",
        "max_elements": 5,
    },
    "continuous-line": {
        "construction": "single-path",
        "semantic_method": "path-behaviour",
        "silhouette": "open",
        "max_elements": 2,
    },
    "modular-geometry": {
        "construction": "grid-modules",
        "semantic_method": "spatial-relation",
        "silhouette": "architectural",
        "max_elements": 5,
    },
    "signature-emblem": {
        "construction": "custom-emblem",
        "semantic_method": "central-idea",
        "silhouette": "contained",
        "max_elements": 5,
    },
    "motion-ribbon": {
        "construction": "ribbon-path",
        "semantic_method": "direction-and-fold",
        "silhouette": "dynamic",
        "max_elements": 3,
    },
    "typography-led": {
        "construction": "custom-letter-detail",
        "semantic_method": "letter-intervention",
        "silhouette": "word-led",
        "max_elements": 3,
    },
    "experimental-fusion": {
        "construction": "hybrid-boolean",
        "semantic_method": "dual-reading",
        "silhouette": "unexpected",
        "max_elements": 4,
    },
}


CLICHE_FORBIDDEN = {
    "technology": ("generic-circuit-board", "random-nodes", "stock-cube"),
    "cybersecurity": ("generic-padlock", "generic-shield"),
    "finance": ("dollar-sign", "coin-stack", "generic-bar-chart"),
    "legal": ("gavel", "generic-scales"),
    "healthcare": ("generic-medical-cross", "heartbeat-only"),
    "coffee": ("literal-cup", "literal-bean-alone"),
    "food-beverage": ("fork-and-knife", "chef-hat"),
    "music-audio": ("music-note-alone", "headphones-alone"),
    "education": ("open-book-alone", "graduation-cap"),
    "real-estate": ("house-outline", "roofline-alone", "key-icon"),
    "travel-hospitality": ("airplane-alone", "location-pin-alone"),
    "automotive": ("car-silhouette", "speedometer-alone"),
    "logistics": ("truck-icon", "box-and-arrow"),
    "fashion-beauty": ("hanger-icon", "lipstick-icon"),
    "fitness-sports": ("dumbbell-alone", "generic-athlete"),
    "nature-agriculture": ("leaf-alone", "generic-tree"),
    "water": ("droplet-alone", "generic-wave"),
    "energy": ("lightning-bolt-alone", "sun-alone"),
    "gaming-entertainment": ("controller-alone", "joystick-alone"),
    "creative-media": ("camera-alone", "play-button-alone"),
    "manufacturing-engineering": ("gear-alone", "factory-icon"),
    "retail-ecommerce": ("shopping-cart", "shopping-bag-alone"),
    "nonprofit-community": ("generic-hands", "generic-heart"),
    "professional-services": ("generic-bars", "generic-arrow"),
    "other": (),
}


@dataclass(frozen=True)
class IdentityBrief:
    concept_index: int
    strategy: str
    territory: str
    secondary_territory: str
    construction: str
    semantic_method: str
    silhouette: str
    max_elements: int
    initial_role: str
    geometry_character: str
    avoid: tuple[str, ...]
    variant_key: str

    def to_dict(self):
        return asdict(self)


def _stable_int(*parts: object) -> int:
    payload = "|".join(str(part) for part in parts)
    return int(hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16], 16)


def _normalise_family(value: str) -> str:
    value = (value or "other").strip().lower()
    aliases = {
        "music": "music-audio",
        "real estate": "real-estate",
        "travel": "travel-hospitality",
        "fitness": "fitness-sports",
        "agriculture": "nature-agriculture",
        "fashion": "fashion-beauty",
        "creative": "creative-media",
        "manufacturing": "manufacturing-engineering",
        "retail": "retail-ecommerce",
        "professional": "professional-services",
    }
    value = aliases.get(value, value)
    return value if value in FAMILY_TERRITORIES else "other"


def _initial_role(strategy: str) -> str:
    return {
        "bespoke-monogram": "primary",
        "negative-space-glyph": "hidden-structural",
        "abstract-semantic": "optional-secondary",
        "continuous-line": "structural",
        "modular-geometry": "abstracted",
        "signature-emblem": "integrated",
        "motion-ribbon": "suggested",
        "typography-led": "wordmark-primary",
        "experimental-fusion": "dual-reading",
    }[strategy]


def _geometry_character(territory: str, strategy: str) -> str:
    organic = {
        "care", "renewal", "wellbeing", "warmth", "ritual", "growth",
        "flow", "continuity", "humanity", "welcome", "expression",
        "belonging", "nourishment", "stewardship",
    }
    dynamic = {
        "rhythm", "frequency", "tempo", "velocity", "movement",
        "momentum", "energy", "journey", "forward-motion", "performance",
    }

    if territory in organic:
        base = "controlled-organic"
    elif territory in dynamic:
        base = "directional-dynamic"
    else:
        base = "precise-geometric"

    if strategy == "signature-emblem":
        return base + "-balanced"
    if strategy == "motion-ribbon":
        return base + "-flowing"
    if strategy == "negative-space-glyph":
        return base + "-subtractive"
    return base


def generate_identity_briefs(
    business_name: str,
    industry_family: str,
    description: str = "",
    personality: str = "",
    count: int = 9,
    variant_seed: str = "",
) -> list[dict]:
    """
    Return deliberately diverse construction briefs.

    New variant_seed -> fresh controlled choices.
    Same inputs + same variant_seed -> exactly reproducible briefs.
    """
    if count not in {3, 6, 9}:
        raise ValueError("Identity concept count must be 3, 6, or 9.")

    family = _normalise_family(industry_family)
    territories = FAMILY_TERRITORIES[family]

    seed = variant_seed or "v5-default"
    rotation = _stable_int(
        business_name,
        family,
        description,
        personality,
        seed,
        "strategy-rotation",
    ) % len(STRATEGIES)

    ordered_strategies = (
        STRATEGIES[rotation:] + STRATEGIES[:rotation]
    )

    results: list[IdentityBrief] = []

    for index, strategy in enumerate(ordered_strategies[:count]):
        grammar = STRATEGY_GRAMMARS[strategy]

        t_index = _stable_int(
            business_name,
            description,
            personality,
            seed,
            strategy,
            "territory-primary",
        ) % len(territories)

        secondary_offset = 1 + (
            _stable_int(seed, strategy, "territory-secondary")
            % (len(territories) - 1)
        )

        territory = territories[t_index]
        secondary = territories[
            (t_index + secondary_offset) % len(territories)
        ]

        variant_key = hashlib.sha256(
            (
                f"{business_name}|{family}|{description}|{personality}|"
                f"{seed}|{strategy}|{territory}|{secondary}"
            ).encode("utf-8")
        ).hexdigest()[:16]

        results.append(
            IdentityBrief(
                concept_index=index,
                strategy=strategy,
                territory=territory,
                secondary_territory=secondary,
                construction=grammar["construction"],
                semantic_method=grammar["semantic_method"],
                silhouette=grammar["silhouette"],
                max_elements=grammar["max_elements"],
                initial_role=_initial_role(strategy),
                geometry_character=_geometry_character(
                    territory,
                    strategy,
                ),
                avoid=CLICHE_FORBIDDEN.get(family, ()),
                variant_key=variant_key,
            )
        )

    return [brief.to_dict() for brief in results]


def strategy_diversity(briefs: Iterable[dict]) -> float:
    briefs = list(briefs)
    if not briefs:
        return 0.0
    unique = len({brief.get("strategy") for brief in briefs})
    return unique / len(briefs)
