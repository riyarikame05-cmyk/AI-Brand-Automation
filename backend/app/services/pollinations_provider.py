import random
from urllib.parse import quote

import requests


POLLINATIONS_URL = (
    "https://image.pollinations.ai/prompt"
)


def generate_creative_logo_symbol(
    concept: str,
    style: str,
) -> bytes:
    """
    Generate a creative logo symbol using Pollinations.

    This function deliberately asks for a symbol only.
    Company typography is NOT generated here.
    """

    seed = random.randint(
        1,
        2_000_000_000,
    )

    prompt = (
        "professional corporate vector logo symbol, "
        f"{concept}, "
        f"{style} visual identity, "
        "single isolated brand mark, "
        "simple memorable geometry, "
        "clean flat vector design, "
        "strong negative space, "
        "two or three solid colors, "
        "centered composition, "
        "plain white background, "
        "professional branding agency quality"
    )

    encoded_prompt = quote(
        prompt,
        safe="",
    )

    url = (
        f"{POLLINATIONS_URL}/"
        f"{encoded_prompt}"
    )

    params = {
        "width": 1024,
        "height": 1024,
        "seed": seed,
        "model": "flux",
        "enhance": "false",
        "nologo": "true",
    }

    print("")
    print(
        "================================="
    )
    print(
        "POLLINATIONS CREATIVE CONCEPT"
    )
    print(
        "================================="
    )
    print(
        "Seed:",
        seed,
    )
    print(
        "Concept:",
        concept,
    )

    try:

        response = requests.get(
            url,
            params=params,
            timeout=120,
        )

        response.raise_for_status()

        content_type = (
            response.headers.get(
                "content-type",
                "",
            )
            .lower()
        )

        if not content_type.startswith(
            "image/"
        ):

            raise RuntimeError(
                "Pollinations did not return an image."
            )

        if len(
            response.content
        ) < 1000:

            raise RuntimeError(
                "Returned image was invalid."
            )

        print(
            "Creative image generated successfully."
        )

        return response.content

    except Exception as error:

        print(
            "Pollinations generation failed:",
            repr(error),
        )

        raise