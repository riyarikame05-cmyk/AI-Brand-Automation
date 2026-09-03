from app.services.pollinations_provider import (
    generate_creative_logo_symbol,
)


concepts = [
    (
        "interlocking angular N symbol representing "
        "technology and forward movement"
    ),
    (
        "abstract orbital network symbol representing "
        "intelligent software"
    ),
]


for index, concept in enumerate(
    concepts,
    start=1,
):

    print(
        f"\nGenerating concept {index}..."
    )

    try:

        image = generate_creative_logo_symbol(
            concept=concept,
            style="modern premium",
        )

        filename = (
            f"creative-logo-{index}.png"
        )

        with open(
            filename,
            "wb",
        ) as file:

            file.write(image)

        print("SUCCESS")
        print("Saved:", filename)

    except Exception as error:

        print("FAILED")
        print(repr(error))