from pathlib import Path

from app.services.color_extractor import extract_dominant_colors


generated_folder = (
    Path(__file__).resolve().parent / "generated"
)


images = list(
    generated_folder.glob("*.png")
)


if not images:
    raise ValueError(
        "No PNG images found in backend/generated"
    )


# Use the most recently modified image.
latest_image = max(
    images,
    key=lambda image: image.stat().st_mtime,
)


print("Analyzing:")
print(latest_image)


colors = extract_dominant_colors(
    latest_image
)


print("\nDominant colors:")

for color in colors:
    print(color)