from __future__ import annotations

import os

from .flux_provider import (
    generate_flux_campaign,
    generate_flux_symbol,
)

from .replicate_provider import (
    generate_replicate_image,
)

from .logo_renderer import (
    compose_cloud_logo,
    render_logo,
)


# =========================================================
# CONFIGURATION
# =========================================================

# Local is now the default because master logo generation
# must work completely offline.
DEFAULT_PROVIDER = (
    os.getenv(
        "IMAGE_PROVIDER",
        "local",
    )
    .strip()
    .lower()
)


# =========================================================
# VALIDATION
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

    return bytes(image_bytes)


# =========================================================
# PURPOSE
# =========================================================

def _get_purpose(
    kwargs,
) -> str:

    return (
        str(
            kwargs.get(
                "purpose",
                "symbol",
            )
        )
        .strip()
        .lower()
    )


# =========================================================
# CLOUD LOGO COMPOSITION
# =========================================================

def _compose_if_symbol(
    image_bytes: bytes,
    provider_name: str,
    **kwargs,
) -> bytes:

    image_bytes = _validate_image(
        image_bytes,
        provider_name,
    )

    purpose = _get_purpose(
        kwargs
    )

    if purpose != "symbol":
        return image_bytes

    specification = kwargs.get(
        "specification",
        {},
    )

    business_name = (
        str(
            kwargs.get(
                "business_name",
                "Brand",
            )
        )
        .strip()
        or "Brand"
    )

    industry = (
        str(
            kwargs.get(
                "industry",
                "Business",
            )
        )
        .strip()
        or "Business"
    )

    if not specification:
        raise RuntimeError(
            "Logo specification is required."
        )

    result = compose_cloud_logo(
        cloud_image_bytes=image_bytes,
        business_name=business_name,
        industry=industry,
        specification=specification,
    )

    return _validate_image(
        result,
        f"{provider_name}-compositor",
    )


# =========================================================
# LOCAL LOGO PROVIDER
# =========================================================

def generate_local_image(
    **kwargs,
) -> bytes:

    purpose = _get_purpose(
        kwargs
    )

    if purpose != "symbol":
        raise RuntimeError(
            "Local image provider currently "
            "supports logo symbols only."
        )

    specification = kwargs.get(
        "specification",
        {},
    )

    business_name = (
        str(
            kwargs.get(
                "business_name",
                "Brand",
            )
        )
        .strip()
        or "Brand"
    )

    industry = (
        str(
            kwargs.get(
                "industry",
                "Business",
            )
        )
        .strip()
        or "Business"
    )

    if not specification:
        raise RuntimeError(
            "Logo specification is required "
            "for local rendering."
        )

    print(
        "[IMAGE] Rendering logo locally."
    )

    result = render_logo(
        business_name=business_name,
        industry=industry,
        specification=specification,
    )

    png = result.get(
        "png"
    )

    return _validate_image(
        png,
        "local",
    )


# =========================================================
# FLUX / POLLINATIONS
# =========================================================

def generate_flux_image(
    **kwargs,
) -> bytes:

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

    purpose = _get_purpose(
        kwargs
    )

    if purpose == "campaign":

        raw_image = generate_flux_campaign(
            specification=specification,
            industry=industry,
            style=style,
        )

    elif purpose == "symbol":

        raw_image = generate_flux_symbol(
            specification=specification,
            industry=industry,
            style=style,
        )

    else:

        raise ValueError(
            f"Unknown image purpose: {purpose}"
        )

    raw_image = _validate_image(
        raw_image,
        "flux",
    )

    return _compose_if_symbol(
        raw_image,
        "flux",
        **kwargs,
    )


# =========================================================
# REPLICATE
# =========================================================

def generate_replicate_provider_image(
    **kwargs,
) -> bytes:

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

    purpose = _get_purpose(
        kwargs
    )

    raw_image = generate_replicate_image(
        specification=specification,
        industry=industry,
        style=style,
        purpose=purpose,
    )

    raw_image = _validate_image(
        raw_image,
        "replicate",
    )

    return _compose_if_symbol(
        raw_image,
        "replicate",
        **kwargs,
    )


# =========================================================
# REPLICATE CONFIGURATION
# =========================================================

def _replicate_configured() -> bool:

    token = (
        os.getenv(
            "REPLICATE_API_TOKEN",
            "",
        )
        .strip()
    )

    model = (
        os.getenv(
            "REPLICATE_IMAGE_MODEL",
            "",
        )
        .strip()
    )

    return bool(
        token
        and model
    )


# =========================================================
# MAIN PROVIDER ROUTER
# =========================================================

def generate_image(
    provider=None,
    **kwargs,
) -> bytes:
    """
    Hybrid image provider router.

    For logos/symbols:

        auto
          -> Replicate when configured
          -> FLUX/Pollinations
          -> deterministic local logo renderer

    Successful cloud logo artwork is passed through
    compose_cloud_logo(), which adds the exact business name
    and deterministic typography.

    For campaign images:

        auto
          -> Replicate when configured
          -> FLUX/Pollinations

    Local campaign rendering is not currently implemented.
    """

    selected = (
        provider
        or DEFAULT_PROVIDER
        or "local"
    )

    selected = (
        str(selected)
        .strip()
        .lower()
    )

    purpose = _get_purpose(
        kwargs
    )

    print(
        f"[IMAGE] Selected provider: {selected}"
    )

    print(
        f"[IMAGE] Purpose: {purpose}"
    )

    # =====================================================
    # EXPLICIT LOCAL
    # =====================================================

    if selected == "local":

        if purpose == "symbol":

            print(
                "[IMAGE] Using deterministic "
                "local logo renderer."
            )

            return generate_local_image(
                **kwargs
            )

        raise RuntimeError(
            "Local campaign image generation "
            "is not currently available."
        )

    # =====================================================
    # EXPLICIT FLUX
    # =====================================================

    if selected == "flux":

        print(
            "[IMAGE] Using FLUX/Pollinations."
        )

        return generate_flux_image(
            **kwargs
        )

    # =====================================================
    # EXPLICIT REPLICATE
    # =====================================================

    if selected == "replicate":

        if not _replicate_configured():
            raise RuntimeError(
                "Replicate is not configured."
            )

        print(
            "[IMAGE] Using Replicate."
        )

        return generate_replicate_provider_image(
            **kwargs
        )

    # =====================================================
    # AUTO
    # =====================================================

    if selected == "auto":

        errors = []

        # -------------------------------------------------
        # 1. REPLICATE
        # -------------------------------------------------

        if _replicate_configured():

            try:

                print(
                    "[IMAGE] Trying Replicate..."
                )

                result = (
                    generate_replicate_provider_image(
                        **kwargs
                    )
                )

                print(
                    "[IMAGE] Replicate succeeded."
                )

                return result

            except Exception as error:

                print(
                    "[IMAGE] Replicate failed:",
                    repr(error),
                )

                errors.append(
                    f"replicate: {error}"
                )

        else:

            print(
                "[IMAGE] Replicate not configured."
            )

        # -------------------------------------------------
        # 2. FLUX / POLLINATIONS
        # -------------------------------------------------

        try:

            print(
                "[IMAGE] Trying FLUX/Pollinations..."
            )

            result = generate_flux_image(
                **kwargs
            )

            print(
                "[IMAGE] FLUX/Pollinations succeeded."
            )

            return result

        except Exception as error:

            print(
                "[IMAGE] FLUX/Pollinations failed:",
                repr(error),
            )

            errors.append(
                f"flux: {error}"
            )

        # -------------------------------------------------
        # 3. LOCAL LOGO FALLBACK
        # -------------------------------------------------

        if purpose == "symbol":

            try:

                print(
                    "[IMAGE] Cloud logo providers unavailable."
                )

                print(
                    "[IMAGE] Falling back to deterministic "
                    "local logo renderer..."
                )

                result = generate_local_image(
                    **kwargs
                )

                print(
                    "[IMAGE] Local logo fallback succeeded."
                )

                return result

            except Exception as error:

                print(
                    "[IMAGE] Local logo fallback failed:",
                    repr(error),
                )

                errors.append(
                    f"local: {error}"
                )

        # -------------------------------------------------
        # NOTHING SUCCEEDED
        # -------------------------------------------------

        raise RuntimeError(
            "Image generation failed. "
            + " | ".join(errors)
        )

    raise ValueError(
        f"Unknown image provider: {selected}"
    )

    # =====================================================
    # LOGOS ARE ALWAYS LOCAL
    # =====================================================
    #
    # Master logo generation must be:
    #
    # Ollama
    #   ->
    # structured specification
    #   ->
    # deterministic local renderer
    #
    # This prevents:
    # - online API dependency
    # - image-model watermarks
    # - malformed typography
    # - inconsistent logo styles
    # =====================================================

    if purpose == "symbol":

        print(
            "[IMAGE] Logo symbol requested - "
            "forcing local renderer."
        )

        return generate_local_image(
            **kwargs
        )

    # =====================================================
    # EXPLICIT LOCAL
    # =====================================================

    if selected == "local":

        # Local campaign-image generation is not currently
        # implemented.
        raise RuntimeError(
            "Local campaign image generation "
            "is not currently available."
        )

    # =====================================================
    # EXPLICIT FLUX
    # =====================================================

    if selected == "flux":

        print(
            "[IMAGE] Using FLUX/Pollinations "
            "for campaign image."
        )

        return generate_flux_image(
            **kwargs
        )

    # =====================================================
    # EXPLICIT REPLICATE
    # =====================================================

    if selected == "replicate":

        print(
            "[IMAGE] Using Replicate "
            "for campaign image."
        )

        return (
            generate_replicate_provider_image(
                **kwargs
            )
        )

    # =====================================================
    # AUTO
    # =====================================================

    if selected == "auto":

        errors = []

        # -------------------------------------------------
        # REPLICATE
        # -------------------------------------------------

        if _replicate_configured():

            try:

                print(
                    "[IMAGE] Trying Replicate..."
                )

                result = (
                    generate_replicate_provider_image(
                        **kwargs
                    )
                )

                print(
                    "[IMAGE] Replicate succeeded."
                )

                return result

            except Exception as error:

                print(
                    "[IMAGE] Replicate failed:",
                    repr(error),
                )

                errors.append(
                    f"replicate: {error}"
                )

        else:

            print(
                "[IMAGE] Replicate not configured."
            )

        # -------------------------------------------------
        # FLUX / POLLINATIONS
        # -------------------------------------------------

        try:

            print(
                "[IMAGE] Trying FLUX/Pollinations..."
            )

            result = generate_flux_image(
                **kwargs
            )

            print(
                "[IMAGE] FLUX/Pollinations succeeded."
            )

            return result

        except Exception as error:

            print(
                "[IMAGE] FLUX/Pollinations failed:",
                repr(error),
            )

            errors.append(
                f"flux: {error}"
            )

        raise RuntimeError(
            "Campaign image generation failed. "
            + " | ".join(errors)
        )

    raise ValueError(
        f"Unknown image provider: {selected}"
    )