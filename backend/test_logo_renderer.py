from pathlib import Path

from app.services.logo_designer import (
    generate_logo_specification,
)

from app.services.logo_renderer import (
    render_logo,
)


OUTPUT = Path(
    "renderer_tests"
)

OUTPUT.mkdir(
    exist_ok=True
)


for number in range(
    1,
    4
):

    print(
        f"\nGenerating concept {number}..."
    )


    specification = (
        generate_logo_specification(
            business_name="Nexora",
            industry="technology",
            style="modern",
            description=(
                "Cloud automation and "
                "technology solutions "
                "for growing companies"
            ),
        )
    )


    print(
        "Type:",
        specification[
            "logo_type"
        ]
    )

    print(
        "Shape:",
        specification[
            "shape"
        ]
    )


    result = render_logo(
        business_name="Nexora",
        industry="technology",
        specification=specification,
    )


    png_path = (
        OUTPUT
        / f"concept-{number}.png"
    )

    svg_path = (
        OUTPUT
        / f"concept-{number}.svg"
    )


    png_path.write_bytes(
        result["png"]
    )


    svg_path.write_text(
        result["svg"],
        encoding="utf-8",
    )


    print(
        "Created:",
        png_path
    )

    print(
        "Created:",
        svg_path
    )


print(
    "\nFinished."
)