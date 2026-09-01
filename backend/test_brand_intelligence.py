from app.services.brand_intelligence import (
    generate_brand_intelligence,
)


print("Testing local brand AI...\n")


try:
    result = generate_brand_intelligence(
        business_name="Nexora",
        industry="technology",
        description=(
            "AI-powered business tools for "
            "small and growing companies."
        ),
        style="modern",
    )

    print("SUCCESS\n")

    print("Slogan:")
    print(result["slogan"])

    print("\nPersonality:")
    print(result["personality"])

    print("\nTone:")
    print(result["tone"])

    print("\nTarget Audience:")
    print(result["target_audience"])

    print("\nMarketing Message:")
    print(result["marketing_message"])

    print("\nTypography:")
    print(result["typography"])


except Exception as error:
    print("FAILED")
    print(repr(error))