import os

from .flux_provider import (
    generate_flux_symbol,
)


DEFAULT_PROVIDER = os.getenv(
    "IMAGE_PROVIDER",
    "local",
).lower()


# =========================================================
# LOCAL PROVIDER
# =========================================================

def generate_local_image(
    **kwargs,
):

    raise RuntimeError(
        "Local campaign image provider "
        "has not been configured."
    )


# =========================================================
# FLUX PROVIDER
# =========================================================

def generate_flux_image(
    **kwargs,
):

    specification = kwargs.get(
        "specification",
        {},
    )

    industry = kwargs.get(
        "industry",
        "",
    )

    style = kwargs.get(
        "style",
        "",
    )


    return generate_flux_symbol(
        specification=specification,
        industry=industry,
        style=style,
    )


# =========================================================
# STUDENT / CLOUD PROVIDER
# =========================================================

def generate_student_image(
    **kwargs,
):

    # We'll implement this when your GitHub
    # Student partner benefits activate.

    raise RuntimeError(
        "Student image provider "
        "is not configured."
    )


# =========================================================
# ROUTER
# =========================================================

def generate_image(
    provider=None,
    **kwargs,
):

    selected = (
        provider
        or DEFAULT_PROVIDER
    ).lower()


    if selected == "local":

        return generate_local_image(
            **kwargs
        )


    if selected == "flux":

        return generate_flux_image(
            **kwargs
        )


    if selected == "student":

        return generate_student_image(
            **kwargs
        )


    if selected == "auto":

        providers = [
            (
                "student",
                generate_student_image,
            ),

            (
                "flux",
                generate_flux_image,
            ),
        ]


        for name, generator in providers:

            try:

                print(
                    f"Trying image provider: {name}"
                )


                return generator(
                    **kwargs
                )


            except Exception as error:

                print(
                    f"{name} unavailable:",
                    repr(error),
                )


        return generate_local_image(
            **kwargs
        )


    raise ValueError(
        f"Unknown image provider: {selected}"
    )