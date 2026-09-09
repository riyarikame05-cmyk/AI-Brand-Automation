from pathlib import Path

from app.services.video_generator_v2 import (
    generate_promotional_video_v2,
)


# =========================================================
# PATHS
# =========================================================

BACKEND_DIR = Path(__file__).resolve().parent

GENERATED_DIR = (
    BACKEND_DIR
    / "generated"
)


# =========================================================
# FIND AN EXISTING LOGO
# =========================================================

png_files = list(
    GENERATED_DIR.glob(
        "*.png"
    )
)


if not png_files:

    raise FileNotFoundError(
        "No PNG logo was found inside "
        f"{GENERATED_DIR}"
    )


# Use newest PNG.
logo_path = max(
    png_files,
    key=lambda path:
    path.stat().st_mtime,
)


print(
    "Using logo:"
)

print(
    logo_path
)


# =========================================================
# GENERATE VIDEO V2
# =========================================================

output_path = (
    generate_promotional_video_v2(

        logo_path=logo_path,

        output_directory=(
            GENERATED_DIR
        ),

        business_name=(
            "Nova Intelligence"
        ),

        slogan=(
            "Intelligence without complexity."
        ),

        personality=[
            "Precise",
            "Modern",
            "Effortless",
        ],

        marketing_message=(
            "Transform complex workflows "
            "into intelligent automated systems."
        ),

        primary_color=(
            "#0F172A"
        ),

        secondary_color=(
            "#2563EB"
        ),

        accent_color=(
            "#38BDF8"
        ),
    )
)


# =========================================================
# RESULT
# =========================================================

print("")
print(
    "======================================"
)

print(
    "VIDEO V2 GENERATED"
)

print(
    "======================================"
)

print(
    output_path.resolve()
)