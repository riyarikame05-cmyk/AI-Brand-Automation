from __future__ import annotations

from pathlib import Path
from PIL import Image

BACKEND_DIR = Path(__file__).resolve().parents[2]
GENERATED_DIR = BACKEND_DIR / "generated"


def generate_logo_variations(
    source_path: str | Path,
    project_id: str,
) -> list[dict]:
    """
    Generate three local PNG logo variations.
    No external API requests are made.
    """

    source_path = Path(source_path)

    if not source_path.is_file():
        raise FileNotFoundError(
            f"Logo file not found: {source_path}"
        )

    output_dir = GENERATED_DIR / "logo_variations" / project_id
    output_dir.mkdir(parents=True, exist_ok=True)

    with Image.open(source_path) as image:
        logo = image.convert("RGBA")

    variations = []

    configurations = [
        ("original", None),
        ("light", "#FFFFFF"),
        ("dark", "#18181B"),
    ]

    for variation_type, background in configurations:
        canvas = Image.new(
            "RGBA",
            (1024, 1024),
            background if background else (0, 0, 0, 0),
        )

        resized = logo.copy()
        resized.thumbnail((780, 780), Image.Resampling.LANCZOS)

        x = (1024 - resized.width) // 2
        y = (1024 - resized.height) // 2

        canvas.alpha_composite(resized, (x, y))

        filename = f"{variation_type}.png"
        output_path = output_dir / filename

        canvas.convert("RGB").save(output_path) if background else canvas.save(output_path)

        variations.append(
            {
                "type": variation_type,
                "filename": filename,
                "url": f"/generated/logo_variations/{project_id}/{filename}",
            }
        )

    return variations
