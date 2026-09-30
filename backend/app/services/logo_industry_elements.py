"""
Canonical industry-specific logo element vocabulary.

This module only defines which recognizable visual elements are available
for each existing industry family. It does not render logos and does not
modify industry classification.
"""

INDUSTRY_LOGO_ELEMENTS = {
    "technology": (
        "chip",
        "circuit",
        "ai-nodes",
        "code-brackets",
        "laptop",
        "cloud",
    ),
    "cybersecurity": (
        "shield",
        "lock",
        "key",
        "fingerprint",
        "cyber-circuit",
    ),
    "finance": (
        "currency",
        "coins",
        "wallet",
        "bank",
        "graph",
        "arrows",
        "pie-chart",
    ),
    "legal": (
        "scales",
        "courthouse",
        "gavel",
        "pillar",
        "document",
    ),
    "healthcare": (
        "heart",
        "medical-cross",
        "heartbeat",
        "stethoscope",
        "plus",
    ),
    "coffee": (
        "coffee-mug",
        "coffee-cup",
        "coffee-beans",
        "steam",
        "cafe-badge",
    ),
    "food-beverage": (
        "fork-spoon",
        "plate",
        "chef-hat",
        "bottle",
        "burger",
        "food-bowl",
    ),
    "music-audio": (
        "music-note",
        "headphones",
        "microphone",
        "waveform",
        "speaker",
    ),
    "education": (
        "graduation-cap",
        "book",
        "pencil",
        "lightbulb",
        "school",
    ),
    "real-estate": (
        "house",
        "building",
        "roof",
        "key",
        "skyline",
    ),
    "travel-hospitality": (
        "airplane",
        "suitcase",
        "passport",
        "hotel",
        "globe",
        "location-pin",
    ),
    "automotive": (
        "car-silhouette",
        "wheel",
        "steering-wheel",
        "road",
        "speed-lines",
    ),
    "logistics": (
        "box",
        "truck",
        "warehouse",
        "arrows",
        "route-map",
    ),
    "fashion-beauty": (
        "dress",
        "hanger",
        "lipstick",
        "perfume",
        "mirror",
        "beauty-silhouette",
    ),
    "fitness-sports": (
        "dumbbell",
        "running-figure",
        "trophy",
        "ball",
        "muscle",
        "lightning",
    ),
    "nature-agriculture": (
        "leaf",
        "tree",
        "farm",
        "wheat",
        "seed",
        "mountain",
    ),
    "water": (
        "droplet",
        "wave",
        "water-ripple",
        "bottle",
        "ocean",
    ),
    "energy": (
        "lightning",
        "solar-panel",
        "battery",
        "wind-turbine",
        "sun",
    ),
    "gaming-entertainment": (
        "controller",
        "joystick",
        "pixel",
        "dice",
        "play-button",
    ),
    "creative-media": (
        "brush",
        "camera",
        "film",
        "pencil",
        "palette",
        "clapperboard",
    ),
    "manufacturing-engineering": (
        "gear",
        "factory",
        "wrench",
        "blueprint",
        "machine",
    ),
    "retail-ecommerce": (
        "cart",
        "shopping-bag",
        "box",
        "tag",
        "storefront",
    ),
    "nonprofit-community": (
        "hands",
        "people",
        "heart",
        "community-circle",
        "helping-hand",
    ),
    "professional-services": (
        "briefcase",
        "handshake",
        "document",
        "graph",
        "person",
    ),
    "other": (
        "abstract-shapes",
        "initials",
        "globe",
        "geometric-mark",
    ),
}


def get_industry_logo_elements(industry_family: str) -> tuple[str, ...]:
    """Return allowed recognizable elements for a canonical industry."""
    key = str(industry_family or "other").strip().lower()

    return INDUSTRY_LOGO_ELEMENTS.get(
        key,
        INDUSTRY_LOGO_ELEMENTS["other"],
    )