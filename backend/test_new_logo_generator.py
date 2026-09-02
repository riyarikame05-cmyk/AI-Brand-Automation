from app.services.image_generator import (
    generate_logo_image,
)


for number in range(1, 4):

    print(
        f"Generating logo {number}..."
    )


    image = generate_logo_image(
        business_name="Nexora",
        industry="technology",
        style="modern",
        description=(
            "Modern technology solutions "
            "for growing businesses"
        ),
    )


    filename = (
        f"new-logo-{number}.png"
    )


    with open(
        filename,
        "wb",
    ) as file:

        file.write(
            image
        )


    print(
        "Saved:",
        filename
    )


print(
    "Finished."
)