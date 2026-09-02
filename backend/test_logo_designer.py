from pprint import pprint

from app.services.logo_designer import (
    generate_logo_specification,
)


for number in range(3):

    print()
    print(
        f"========== CONCEPT {number + 1} =========="
    )

    result = generate_logo_specification(
        business_name="Nexora",
        industry="technology",
        style="modern",
        description=(
            "Technology solutions for modern businesses"
        ),
    )

    pprint(
        result
    )