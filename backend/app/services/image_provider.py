import os

from .flux_provider import (
    generate_flux_campaign,
    generate_flux_symbol,
)

from .replicate_provider import (
    generate_replicate_image,
)


# =========================================================
# CONFIGURATION
# =========================================================

DEFAULT_PROVIDER = (
    os.getenv(
        "IMAGE_PROVIDER",
        "auto",
    )
    .strip()
    .lower()
)


# =========================================================
# VALIDATE RESULT
# =========================================================

def _validate_image(
    image_bytes,
    provider_name: str,
) -> bytes:

    if not isinstance(
        image_bytes,
        (bytes, bytearray),
    ):

        raise RuntimeError(
            f"{provider_name} returned "
            "non-binary image data."
        )


    if len(image_bytes) < 1000:

        raise RuntimeError(
            f"{provider_name} returned "
            "invalid image data."
        )


    return bytes(
        image_bytes
    )


# =========================================================
# LOCAL PROVIDER
# =========================================================

def generate_local_image(
    **kwargs,
):

    raise RuntimeError(
        "Local image provider "
        "has not been configured."
    )


# =========================================================
# FLUX PROVIDER
# =========================================================

def generate_flux_image(
    **kwargs,
):

    specification = (
        kwargs.get(
            "specification",
            {},
        )
    )


    industry = (
        kwargs.get(
            "industry",
            "",
        )
    )


    style = (
        kwargs.get(
            "style",
            "",
        )
    )


    purpose = (
        kwargs.get(
            "purpose",
            "campaign",
        )
        .strip()
        .lower()
    )


    if purpose == "campaign":

        return (
            generate_flux_campaign(
                specification=(
                    specification
                ),

                industry=(
                    industry
                ),

                style=(
                    style
                ),
            )
        )


    if purpose == "symbol":

        return (
            generate_flux_symbol(
                specification=(
                    specification
                ),

                industry=(
                    industry
                ),

                style=(
                    style
                ),
            )
        )


    raise ValueError(
        f"Unknown image purpose: {purpose}"
    )


# =========================================================
# REPLICATE PROVIDER
# =========================================================

def generate_replicate_provider_image(
    **kwargs,
):

    specification = (
        kwargs.get(
            "specification",
            {},
        )
    )


    industry = (
        kwargs.get(
            "industry",
            "",
        )
    )


    style = (
        kwargs.get(
            "style",
            "",
        )
    )


    purpose = (
        kwargs.get(
            "purpose",
            "campaign",
        )
        .strip()
        .lower()
    )


    # IMPORTANT:
    # Purpose is now forwarded correctly.
    #
    # Previously this was missing, which caused
    # symbol generation to use campaign prompts.

    return (
        generate_replicate_image(
            specification=(
                specification
            ),

            industry=(
                industry
            ),

            style=(
                style
            ),

            purpose=(
                purpose
            ),
        )
    )


# =========================================================
# STUDENT PROVIDER
# =========================================================

def generate_student_image(
    **kwargs,
):

    raise RuntimeError(
        "Student image provider "
        "is not configured."
    )


# =========================================================
# PROVIDER AVAILABILITY
# =========================================================

def _replicate_configured():

    return bool(
        os.getenv(
            "REPLICATE_API_TOKEN",
            ""
        ).strip()

        and

        os.getenv(
            "REPLICATE_IMAGE_MODEL",
            ""
        ).strip()
    )


# =========================================================
# MAIN ROUTER
# =========================================================

def generate_image(
    provider=None,
    **kwargs,
):

    selected = (
        provider
        or DEFAULT_PROVIDER
        or "auto"
    )


    selected = (
        selected
        .strip()
        .lower()
    )


    # =====================================================
    # REPLICATE
    # =====================================================

    if selected == "replicate":

        return (
            _validate_image(
                generate_replicate_provider_image(
                    **kwargs
                ),

                "replicate",
            )
        )


    # =====================================================
    # FLUX
    # =====================================================

    if selected == "flux":

        return (
            _validate_image(
                generate_flux_image(
                    **kwargs
                ),

                "flux",
            )
        )


    # =====================================================
    # LOCAL
    # =====================================================

    if selected == "local":

        return (
            _validate_image(
                generate_local_image(
                    **kwargs
                ),

                "local",
            )
        )


    # =====================================================
    # STUDENT
    # =====================================================

    if selected == "student":

        return (
            _validate_image(
                generate_student_image(
                    **kwargs
                ),

                "student",
            )
        )


    # =====================================================
    # AUTO
    # =====================================================

    if selected == "auto":

        providers = []


        # Don't waste time calling Replicate
        # when credentials/model aren't configured.

        if _replicate_configured():

            providers.append(
                (
                    "replicate",
                    generate_replicate_provider_image,
                )
            )


        # FLUX/Pollinations remains our fallback.

        providers.append(
            (
                "flux",
                generate_flux_image,
            )
        )


        errors = []


        for (
            name,
            generator,
        ) in providers:

            try:

                print(
                    f"[IMAGE] Trying provider: {name}"
                )


                result = (
                    generator(
                        **kwargs
                    )
                )


                result = (
                    _validate_image(
                        result,
                        name,
                    )
                )


                print(
                    f"[IMAGE] Provider succeeded: {name}"
                )


                return result


            except Exception as error:

                message = (
                    f"{name}: {error}"
                )


                errors.append(
                    message
                )


                print(
                    f"[IMAGE] Provider failed: {name}",
                    repr(error),
                )


        # =================================================
        # OPTIONAL LOCAL FALLBACK
        # =================================================

        try:

            print(
                "[IMAGE] Trying provider: local"
            )


            result = (
                generate_local_image(
                    **kwargs
                )
            )


            return (
                _validate_image(
                    result,
                    "local",
                )
            )


        except Exception as error:

            errors.append(
                f"local: {error}"
            )


        raise RuntimeError(
            "All image providers failed. "
            + " | ".join(errors)
        )


    # =====================================================
    # UNKNOWN
    # =====================================================

    raise ValueError(
        f"Unknown image provider: {selected}"
    )