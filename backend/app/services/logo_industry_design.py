"""
V5 Industry Design DNA.

Defines premium visual vocabulary per industry. These profiles describe how
meaning should influence construction without reducing brands to stock icons.
"""

from __future__ import annotations
from app.services.logo_industry_resolver import resolve_industry

import hashlib
from app.services.logo_industry_elements import get_industry_logo_elements

INDUSTRY_DESIGN_DNA = {
    "technology": {
        "meanings": ("intelligence", "systems", "connection", "precision", "progress"),
        "forms": ("modular-grid", "signal-path", "data-fold", "precision-node", "system-loop"),
        "negative_space": ("linked-counter", "data-channel", "modular-void"),
        "motion": ("precise-forward", "controlled-expansion"),
        "geometry": ("geometric", "modular", "precise"),
        "avoid": ("stock-cube", "generic-circuit", "random-network"),
    },
    "cybersecurity": {
        "meanings": ("protection", "verification", "resilience", "boundary", "trust"),
        "forms": ("protected-core", "verification-cut", "layered-boundary", "secure-fold", "resilient-loop"),
        "negative_space": ("protected-void", "verification-channel", "boundary-cut"),
        "motion": ("contained", "locking"),
        "geometry": ("compact", "layered", "precise"),
        "avoid": ("padlock", "generic-shield", "keyhole"),
    },
    "finance": {
        "meanings": ("trust", "value", "stability", "growth", "clarity"),
        "forms": ("ascending-structure", "balanced-columns", "value-fold", "stable-axis", "compound-geometry"),
        "negative_space": ("growth-channel", "balanced-counter", "value-gap"),
        "motion": ("measured-upward", "stable-forward"),
        "geometry": ("structured", "balanced", "authoritative"),
        "avoid": ("dollar-sign", "coin-stack", "bar-chart"),
    },
    "legal": {
        "meanings": ("authority", "balance", "foundation", "clarity", "heritage"),
        "forms": ("foundation-mark", "balanced-axis", "column-cut", "formal-monogram", "structured-seal"),
        "negative_space": ("central-balance", "foundation-gap", "formal-counter"),
        "motion": ("stable", "measured"),
        "geometry": ("formal", "architectural", "balanced"),
        "avoid": ("gavel", "scales", "courthouse"),
    },
    "healthcare": {
        "meanings": ("care", "renewal", "humanity", "wellbeing", "protection"),
        "forms": ("care-loop", "renewal-fold", "human-connection", "protective-curve", "wellbeing-petal"),
        "negative_space": ("care-crossing", "renewal-counter", "protected-center"),
        "motion": ("gentle-rising", "supportive"),
        "geometry": ("soft", "organic", "balanced"),
        "avoid": ("medical-cross", "heartbeat-only", "caduceus"),
    },
    "coffee": {
        "meanings": ("ritual", "craft", "warmth", "origin", "roast"),
        "forms": ("roast-ring", "steam-ribbon", "bean-counter", "vessel-arc", "origin-contour"),
        "negative_space": ("bean-counter", "steam-gap", "ritual-counter"),
        "motion": ("slow-rising", "organic-curl"),
        "geometry": ("warm", "crafted", "organic"),
        "avoid": ("coffee-cup", "standalone-bean", "cafe-clipart"),
    },
    "food-beverage": {
        "meanings": ("nourishment", "freshness", "gathering", "craft", "abundance"),
        "forms": ("nourish-bowl", "ingredient-fold", "gathering-ring", "fresh-cut", "crafted-vessel"),
        "negative_space": ("nourish-counter", "ingredient-gap", "gathering-void"),
        "motion": ("welcoming", "organic"),
        "geometry": ("rounded", "crafted", "human"),
        "avoid": ("fork-knife", "chef-hat", "plate-icon"),
    },
    "music-audio": {
        "meanings": ("rhythm", "frequency", "resonance", "tempo", "expression"),
        "forms": ("frequency-ribbon", "groove-ring", "resonance-arc", "rhythm-bars", "pulse-fold"),
        "negative_space": ("waveform-counter", "groove-gap", "resonance-void"),
        "motion": ("rhythmic", "oscillating"),
        "geometry": ("dynamic", "rhythmic", "expressive"),
        "avoid": ("music-note", "headphones", "speaker-icon"),
    },
    "education": {
        "meanings": ("knowledge", "discovery", "progress", "curiosity", "growth"),
        "forms": ("knowledge-fold", "discovery-path", "learning-layers", "progress-frame", "curiosity-window"),
        "negative_space": ("knowledge-gap", "discovery-counter", "open-path"),
        "motion": ("opening", "rising"),
        "geometry": ("clear", "open", "progressive"),
        "avoid": ("open-book", "graduation-cap", "pencil-icon"),
    },
    "real-estate": {
        "meanings": ("space", "threshold", "structure", "permanence", "place"),
        "forms": ("threshold-frame", "floorplan-void", "structural-grid", "interlocking-planes", "spatial-monogram"),
        "negative_space": ("doorway-void", "courtyard-gap", "spatial-counter"),
        "motion": ("anchored", "expanding"),
        "geometry": ("architectural", "spatial", "structured"),
        "avoid": ("house-outline", "roofline", "key-icon"),
    },
    "travel-hospitality": {
        "meanings": ("journey", "horizon", "welcome", "discovery", "destination"),
        "forms": ("horizon-fold", "route-ribbon", "destination-arc", "welcome-gate", "journey-loop"),
        "negative_space": ("route-gap", "horizon-counter", "destination-void"),
        "motion": ("forward", "expansive"),
        "geometry": ("open", "directional", "welcoming"),
        "avoid": ("airplane", "location-pin", "suitcase"),
    },
    "automotive": {
        "meanings": ("performance", "velocity", "precision", "engineering", "control"),
        "forms": ("aero-cut", "speed-channel", "performance-wing", "precision-facet", "torque-ring"),
        "negative_space": ("speed-gap", "aero-channel", "precision-cut"),
        "motion": ("fast-forward", "sweeping"),
        "geometry": ("aerodynamic", "sharp", "engineered"),
        "avoid": ("car-silhouette", "speedometer", "wheel-icon"),
    },
    "logistics": {
        "meanings": ("flow", "route", "reliability", "network", "efficiency"),
        "forms": ("route-fold", "forward-channel", "network-path", "transfer-loop", "efficient-grid"),
        "negative_space": ("route-channel", "forward-gap", "transfer-void"),
        "motion": ("forward", "continuous"),
        "geometry": ("directional", "systematic", "efficient"),
        "avoid": ("truck", "parcel-box", "generic-arrow"),
    },
    "fashion-beauty": {
        "meanings": ("elegance", "expression", "signature", "detail", "transformation"),
        "forms": ("signature-stroke", "fabric-fold", "elegant-counter", "editorial-monogram", "refined-ribbon"),
        "negative_space": ("fashion-counter", "fold-gap", "signature-void"),
        "motion": ("graceful", "flowing"),
        "geometry": ("elegant", "slender", "editorial"),
        "avoid": ("hanger", "lipstick", "dress-icon"),
    },
    "fitness-sports": {
        "meanings": ("strength", "energy", "discipline", "momentum", "performance"),
        "forms": ("power-cut", "momentum-chevron", "strength-frame", "performance-stripe", "active-fold"),
        "negative_space": ("power-gap", "momentum-channel", "active-counter"),
        "motion": ("explosive", "forward"),
        "geometry": ("bold", "dynamic", "athletic"),
        "avoid": ("dumbbell", "athlete-silhouette", "trophy"),
    },
    "nature-agriculture": {
        "meanings": ("growth", "origin", "stewardship", "renewal", "cycle"),
        "forms": ("growth-fold", "field-contour", "seed-counter", "cycle-ring", "stewardship-arc"),
        "negative_space": ("seed-void", "growth-channel", "field-gap"),
        "motion": ("rising", "cyclical"),
        "geometry": ("organic", "grounded", "natural"),
        "avoid": ("leaf-alone", "tree-icon", "farm-clipart"),
    },
    "water": {
        "meanings": ("purity", "flow", "clarity", "continuity", "renewal"),
        "forms": ("fluid-channel", "refraction-cut", "ripple-ring", "flowing-counter", "purity-wave"),
        "negative_space": ("waterline-gap", "flow-counter", "refraction-void"),
        "motion": ("fluid", "continuous"),
        "geometry": ("clean", "fluid", "minimal"),
        "avoid": ("droplet-alone", "generic-wave", "faucet-icon"),
    },
    "energy": {
        "meanings": ("power", "renewal", "transition", "radiance", "efficiency"),
        "forms": ("energy-core", "radiant-cut", "power-loop", "transition-fold", "renewal-orbit"),
        "negative_space": ("energy-channel", "radiant-gap", "power-counter"),
        "motion": ("radiating", "accelerating"),
        "geometry": ("energetic", "precise", "progressive"),
        "avoid": ("lightning-bolt", "sun-alone", "plug-icon"),
    },
    "gaming-entertainment": {
        "meanings": ("play", "challenge", "character", "energy", "world-building"),
        "forms": ("portal-frame", "quest-mark", "character-cut", "play-loop", "world-facet"),
        "negative_space": ("portal-void", "quest-gap", "play-counter"),
        "motion": ("active", "immersive"),
        "geometry": ("bold", "distinctive", "playful"),
        "avoid": ("controller", "joystick", "pixel-heart"),
    },
    "creative-media": {
        "meanings": ("story", "perspective", "expression", "frame", "originality"),
        "forms": ("perspective-frame", "story-fold", "creative-aperture", "editorial-cut", "expression-ribbon"),
        "negative_space": ("frame-void", "perspective-gap", "story-counter"),
        "motion": ("expressive", "revealing"),
        "geometry": ("editorial", "expressive", "composed"),
        "avoid": ("camera", "play-button", "film-reel"),
    },
    "manufacturing-engineering": {
        "meanings": ("precision", "assembly", "strength", "reliability", "systems"),
        "forms": ("assembly-lock", "precision-joint", "engineered-grid", "structural-facet", "system-ring"),
        "negative_space": ("joint-gap", "assembly-counter", "precision-channel"),
        "motion": ("mechanical", "controlled"),
        "geometry": ("engineered", "robust", "precise"),
        "avoid": ("gear-alone", "factory", "wrench-icon"),
    },
    "retail-ecommerce": {
        "meanings": ("exchange", "choice", "discovery", "access", "connection"),
        "forms": ("exchange-loop", "choice-grid", "discovery-fold", "access-frame", "connection-ribbon"),
        "negative_space": ("exchange-gap", "choice-counter", "access-void"),
        "motion": ("accessible", "forward"),
        "geometry": ("friendly", "clear", "contemporary"),
        "avoid": ("shopping-cart", "shopping-bag", "price-tag"),
    },
    "nonprofit-community": {
        "meanings": ("belonging", "support", "uplift", "humanity", "purpose"),
        "forms": ("support-loop", "community-ring", "uplift-fold", "belonging-link", "purpose-arc"),
        "negative_space": ("community-center", "support-gap", "belonging-counter"),
        "motion": ("uplifting", "gathering"),
        "geometry": ("human", "inclusive", "warm"),
        "avoid": ("hands-icon", "heart-alone", "people-circle"),
    },
    "professional-services": {
        "meanings": ("expertise", "trust", "clarity", "partnership", "progress"),
        "forms": ("expertise-frame", "partnership-link", "clarity-cut", "progress-axis", "trust-monogram"),
        "negative_space": ("partnership-gap", "clarity-counter", "trust-void"),
        "motion": ("measured-forward", "stable"),
        "geometry": ("refined", "structured", "professional"),
        "avoid": ("generic-bars", "generic-arrow", "handshake"),
    },
    "other": {
        "meanings": ("distinctiveness", "clarity", "character", "connection", "progress"),
        "forms": ("signature-fold", "custom-counter", "distinctive-loop", "character-cut", "connection-frame"),
        "negative_space": ("custom-void", "signature-gap", "character-counter"),
        "motion": ("controlled", "distinctive"),
        "geometry": ("balanced", "custom", "refined"),
        "avoid": ("stock-symbol",),
    },
}


ALIASES = {
    "music": "music-audio",
    "real estate": "real-estate",
    "real_estate": "real-estate",
    "travel": "travel-hospitality",
    "hospitality": "travel-hospitality",
    "automotive": "automotive",
    "fitness": "fitness-sports",
    "sports": "fitness-sports",
    "agriculture": "nature-agriculture",
    "nature": "nature-agriculture",
    "fashion": "fashion-beauty",
    "beauty": "fashion-beauty",
    "creative": "creative-media",
    "media": "creative-media",
    "manufacturing": "manufacturing-engineering",
    "engineering": "manufacturing-engineering",
    "retail": "retail-ecommerce",
    "ecommerce": "retail-ecommerce",
    "professional": "professional-services",
}


def normalize_family(family: str) -> str:
    value = str(family or "other").strip().lower()
    value = ALIASES.get(value, value)
    if value not in INDUSTRY_DESIGN_DNA:
        return "other"
    return value


def get_industry_design_dna(family: str) -> dict:
    resolved = resolve_industry(family)
    normalized_family = normalize_family(resolved["family"])

    return {
        "family": normalized_family,
        "industry_label": resolved["label"],
        **INDUSTRY_DESIGN_DNA[normalized_family],
        "logo_elements": resolved["elements"],
    }


def _choice(options, *seed_parts):
    payload = "|".join(str(part) for part in seed_parts)
    value = int(hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16], 16)
    return options[value % len(options)]


def choose_design_language(
    family: str,
    business_name: str,
    description: str,
    strategy: str,
    variant_seed: str,
) -> dict:
    dna = get_industry_design_dna(family)

    primary_meaning = _choice(
        dna["meanings"],
        business_name,
        description,
        strategy,
        variant_seed,
        "meaning",
    )

    form = _choice(
        dna["forms"],
        business_name,
        description,
        strategy,
        variant_seed,
        "form",
    )

    negative_space = _choice(
        dna["negative_space"],
        business_name,
        description,
        strategy,
        variant_seed,
        "negative-space",
    )

    motion = _choice(
        dna["motion"],
        business_name,
        description,
        strategy,
        variant_seed,
        "motion",
    )

    geometry = _choice(
        dna["geometry"],
        business_name,
        description,
        strategy,
        variant_seed,
        "geometry",
    )

    return {
        "industry_family": dna["family"],
        "industry_label": dna["industry_label"],
        "logo_elements": dna["logo_elements"],
        "meaning": primary_meaning,
        "form": form,
        "negative_space": negative_space,
        "motion": motion,
        "geometry": geometry,
        "avoid": dna["avoid"],
    }