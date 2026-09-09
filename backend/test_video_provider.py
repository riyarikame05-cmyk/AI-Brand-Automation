from pathlib import Path

from app.services.video_provider import (
    generate_video,
)


BACKEND = (
    Path(__file__)
    .resolve()
    .parent
)

GENERATED = (
    BACKEND
    / "generated"
)


logos = list(
    GENERATED.glob(
        "*.png"
    )
)


if not logos:

    raise RuntimeError(
        "No PNG available for testing."
    )


logo = max(
    logos,
    key=lambda p:
    p.stat().st_mtime,
)


print(
    "Using:",
    logo
)


video = generate_video(

    # Important:
    # Wan/LTX aren't configured yet,
    # so auto should safely fall back.
    provider="auto",

    logo_path=logo,

    output_directory=GENERATED,

    business_name="Nova Intelligence",

    slogan=(
        "Intelligence without complexity."
    ),

    personality=[
        "Precise",
        "Modern",
        "Effortless",
    ],

    marketing_message=(
        "Transform complex workflows into "
        "intelligent automated systems."
    ),

    primary_color="#0F172A",

    secondary_color="#2563EB",

    accent_color="#38BDF8",
)


print(
    "Created:",
    video.resolve()
)