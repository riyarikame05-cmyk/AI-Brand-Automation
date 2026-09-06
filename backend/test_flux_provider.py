from pathlib import Path

from app.services.flux_provider import generate_flux_symbol


specification = {
    "logo_type": "abstract",
    "shape": "interlocking",
    "primary_color": "#111827",
    "secondary_color": "#4F46E5",
    "accent_color": "#06B6D4",
    "concept": (
        "two interconnected forms representing "
        "intelligence and continuous growth"
    ),
}


image = generate_flux_symbol(
    specification=specification,
    industry="Artificial Intelligence",
    style="modern premium technology",
)


output = Path("flux-test.png")

output.write_bytes(image)

print(
    "Generated:",
    output.resolve(),
)