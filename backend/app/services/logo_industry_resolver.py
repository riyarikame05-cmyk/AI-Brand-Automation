"""
Resolve user-facing industries into internal logo intelligence.

The user's selected industry is preserved exactly.

This module does NOT render artwork and does NOT modify projects.
"""

from __future__ import annotations

from app.services.logo_industry_elements import (
    get_industry_logo_elements,
)


FRONTEND_INDUSTRY_PROFILES = {
    "Technology / Software": {
        "family": "technology",
        "elements": (
            "chip",
            "circuit",
            "code-brackets",
            "laptop",
            "cloud",
        ),
    },
    "Artificial Intelligence": {
        "family": "technology",
        "elements": (
            "ai-nodes",
            "chip",
            "circuit",
        ),
    },
    "Clothing & Fashion": {
        "family": "fashion-beauty",
        "elements": (
            "dress",
            "hanger",
        ),
    },
    "E-commerce": {
        "family": "retail-ecommerce",
        "elements": (
            "cart",
            "shopping-bag",
            "box",
            "tag",
            "storefront",
        ),
    },
    "Food & Restaurant": {
        "family": "food-beverage",
        "elements": (
            "fork-spoon",
            "plate",
            "chef-hat",
            "bottle",
            "burger",
            "food-bowl",
        ),
    },
    "Coffee & Cafe": {
        "family": "coffee",
        "elements": (
            "coffee-mug",
            "coffee-cup",
            "coffee-beans",
            "steam",
            "cafe-badge",
        ),
    },
    "Healthcare": {
        "family": "healthcare",
        "elements": (
            "heart",
            "medical-cross",
            "heartbeat",
            "stethoscope",
            "plus",
        ),
    },
    "Beauty & Cosmetics": {
        "family": "fashion-beauty",
        "elements": (
            "lipstick",
            "perfume",
            "mirror",
            "beauty-silhouette",
        ),
    },
    "Fitness & Gym": {
        "family": "fitness-sports",
        "elements": (
            "dumbbell",
            "running-figure",
            "trophy",
            "ball",
            "muscle",
            "lightning",
        ),
    },
    "Education": {
        "family": "education",
        "elements": (
            "graduation-cap",
            "book",
            "pencil",
            "lightbulb",
            "school",
        ),
    },
    "Finance & Banking": {
        "family": "finance",
        "elements": (
            "currency",
            "coins",
            "wallet",
            "bank",
            "graph",
            "arrows",
            "pie-chart",
        ),
    },
    "Real Estate": {
        "family": "real-estate",
        "elements": (
            "house",
            "building",
            "roof",
            "key",
            "skyline",
        ),
    },
    "Automotive": {
        "family": "automotive",
        "elements": (
            "car-silhouette",
            "wheel",
            "steering-wheel",
            "road",
            "speed-lines",
        ),
    },
    "Travel & Tourism": {
        "family": "travel-hospitality",
        "elements": (
            "airplane",
            "suitcase",
            "passport",
            "hotel",
            "globe",
            "location-pin",
        ),
    },
    "Music & Entertainment": {
        "family": "music-audio",
        "elements": (
            "music-note",
            "headphones",
            "microphone",
            "waveform",
            "speaker",
        ),
    },
    "Gaming": {
        "family": "gaming-entertainment",
        "elements": (
            "controller",
            "joystick",
            "pixel",
            "dice",
            "play-button",
        ),
    },

    # Construction remains a distinct user-facing subtype.
    # Architectural/structural vocabulary is more appropriate than
    # silently pretending the company is general manufacturing.
    "Construction": {
        "family": "professional-services",
        "elements": (
            "building",
            "structural-beam",
            "blueprint",
            "crane",
            "hard-hat",
        ),
    },
    "Agriculture": {
        "family": "nature-agriculture",
        "elements": (
            "leaf",
            "tree",
            "farm",
            "wheat",
            "seed",
            "mountain",
        ),
    },

    # These are frontend-specific subtypes whose recognizable vocabulary
    # is intentionally more specific than their broad internal family.
    "Jewellery": {
        "family": "fashion-beauty",
        "elements": (
            "diamond",
            "gemstone",
            "ring",
            "necklace",
            "faceted-mark",
        ),
    },
    "Photography": {
        "family": "creative-media",
        "elements": (
            "camera",
            "aperture",
            "lens",
            "frame",
            "shutter",
        ),
    },
    "Marketing & Advertising": {
        "family": "creative-media",
        "elements": (
            "megaphone",
            "target",
            "campaign",
            "media-frame",
            "signal",
        ),
    },
    "Logistics & Transportation": {
        "family": "logistics",
        "elements": (
            "box",
            "truck",
            "warehouse",
            "arrows",
            "route-map",
        ),
    },

    # Supported by backend intelligence and useful for businesses like
    # Veridian Forge. We are not changing the frontend dropdown yet.
    "Manufacturing & Engineering": {
        "family": "manufacturing-engineering",
        "elements": (
            "gear",
            "factory",
            "wrench",
            "blueprint",
            "machine",
        ),
    },
}


def resolve_industry(industry: str) -> dict:
    """
    Preserve the user's label while returning internal design intelligence.
    """
    supplied = str(industry or "").strip()

    for label, profile in FRONTEND_INDUSTRY_PROFILES.items():
        if supplied.casefold() == label.casefold():
            return {
                "label": label,
                "family": profile["family"],
                "elements": profile["elements"],
                "matched": True,
            }

    # Also support callers already using canonical internal family IDs.
    canonical = supplied.lower()

    internal = get_industry_logo_elements(canonical)

    if canonical != "other" and internal != get_industry_logo_elements("other"):
        return {
            "label": supplied,
            "family": canonical,
            "elements": internal,
            "matched": True,
        }

    return {
        "label": supplied or "Other / General",
        "family": "other",
        "elements": get_industry_logo_elements("other"),
        "matched": False,
    }