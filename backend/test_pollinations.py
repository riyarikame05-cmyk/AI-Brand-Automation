from app.services.image_generator import generate_logo_image


prompt = """
Professional minimalist logo for NovaBrew,
a modern coffee company.
Coffee-inspired geometric symbol.
Black and gold.
No text.
"""


try:
    print("Testing Pollinations...")

    image_bytes = generate_logo_image(prompt)

    with open("pollinations_test.png", "wb") as file:
        file.write(image_bytes)

    print("SUCCESS!")
    print("Image saved as pollinations_test.png")

except Exception as error:
    print("FAILED!")
    print(repr(error))