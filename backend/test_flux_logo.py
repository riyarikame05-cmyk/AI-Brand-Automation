from pathlib import Path

from app.services.flux_provider import generate_flux_symbol
from app.services.flux_logo_composer import compose_flux_logo


spec = {
    "logo_type": "abstract",
    "shape": "interlocking",
    "primary_color": "#111827",
    "secondary_color": "#4F46E5",
    "accent_color": "#06B6D4",
    "concept": "connected intelligence and continuous growth",
}


symbol = generate_flux_symbol(
    specification=spec,
    industry="Artificial Intelligence",
    style="premium modern technology",
)


logo = compose_flux_logo(
    symbol_bytes=symbol,
    business_name="NOVA INTELLIGENCE",
)


output = Path("flux-final-test.png")

output.write_bytes(logo)

print("Created:", output.resolve())