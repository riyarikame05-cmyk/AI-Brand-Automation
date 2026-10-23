from __future__ import annotations

from .local_campaign_generator import generate_local_campaign

import os
from io import BytesIO

from PIL import Image, ImageFilter, ImageStat

from .flux_provider import (
    generate_flux_campaign,
    generate_flux_symbol,
)

from .replicate_provider import (
    generate_replicate_image,
)
from .logo_ai_engine import (
    create_art_direction_with_gemini,
    audit_art_direction_with_gemini,
    review_generated_symbol_with_gemini,
    generate_symbol_with_ai_horde,
    generate_symbol_with_ai_horde_persistent,
    PersistentHordeStateError,
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
# CLOUD LOGO QUALITY GATE
# =========================================================

def _check_cloud_logo_quality(
    image_bytes: bytes,
) -> None:
    """
    Reject cloud symbol artwork that behaves more like a
    photographic, shaded, gradient-heavy, or mockup render
    than a flat logo.

    This gate is used only for cloud-generated logo symbols.
    Campaign images bypass it.
    """

    try:
        image = Image.open(BytesIO(image_bytes))
        image.load()
        image = image.convert("RGB")

        image.thumbnail(
            (256, 256),
            Image.Resampling.LANCZOS,
        )

        grayscale = image.convert("L")
        edges = grayscale.filter(ImageFilter.FIND_EDGES)

        edge_mean = ImageStat.Stat(edges).mean[0]
        tonal_stddev = ImageStat.Stat(grayscale).stddev[0]

        # Measure broad color complexity.
        quantized_64 = image.quantize(
            colors=64,
            method=Image.Quantize.MEDIANCUT,
        )

        color_counts = quantized_64.getcolors(maxcolors=64) or []

        significant_colors = sum(
            1
            for count, _ in color_counts
            if count >= 20
        )

        # Measure how well the artwork survives aggressive
        # reduction to a small, flat color palette.
        quantized_8 = image.quantize(
            colors=8,
            method=Image.Quantize.MEDIANCUT,
        ).convert("RGB")

        original_pixels = list(image.getdata())
        flat_pixels = list(quantized_8.getdata())

        total_error = 0.0

        for original, reduced in zip(
            original_pixels,
            flat_pixels,
        ):
            dr = original[0] - reduced[0]
            dg = original[1] - reduced[1]
            db = original[2] - reduced[2]

            total_error += (
                abs(dr)
                + abs(dg)
                + abs(db)
            ) / 3.0

        pixel_count = max(
            1,
            len(original_pixels),
        )

        flatness_error = total_error / pixel_count

        print(
            "[IMAGE QUALITY] "
            f"colors={significant_colors}, "
            f"tonal_stddev={tonal_stddev:.1f}, "
            f"edge_mean={edge_mean:.1f}, "
            f"flatness_error={flatness_error:.1f}"
        )

        strongly_photographic = (
            significant_colors >= 45
            and tonal_stddev >= 45
            and edge_mean >= 12
        )

        # JPEG compression and anti-aliased vector-style artwork can
        # easily contain 50+ quantized colors even when the underlying
        # symbol is visually flat. Do not reject on color count plus
        # moderate tonal variation alone. Require stronger evidence of
        # rendered/shaded imagery.
        heavily_rendered = (
            significant_colors >= 50
            and (
                flatness_error >= 7.0
                or (
                    tonal_stddev >= 65
                    and edge_mean >= 9
                )
            )
        )

        if strongly_photographic or heavily_rendered:
            reasons = []

            if strongly_photographic:
                reasons.append("photographic complexity")

            if heavily_rendered:
                reasons.append("gradient/rendered shading")

            raise RuntimeError(
                "Cloud artwork rejected by logo quality gate: "
                + ", ".join(reasons)
                + "."
            )

    except RuntimeError:
        raise

    except Exception as error:
        print(
            "[IMAGE QUALITY] Check skipped:",
            repr(error),
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


    _check_cloud_logo_quality(
        image_bytes
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
# GEMINI ART DIRECTOR + ANONYMOUS AI HORDE
# =========================================================
def generate_gemini_flux_image(
    **kwargs,
) -> bytes:
    purpose = _get_purpose(kwargs)

    if purpose != "symbol":
        raise RuntimeError(
            "Gemini+Flux currently supports logo symbols only."
        )

    business_name = (
        str(kwargs.get("business_name", "Brand")).strip()
        or "Brand"
    )
    industry = (
        str(kwargs.get("industry", "Business")).strip()
        or "Business"
    )
    description = str(
        kwargs.get("description", "")
    ).strip()
    style = (
        str(kwargs.get("style", "modern")).strip()
        or "modern"
    )

    direction_index = kwargs.get("direction_index", 0)
    if direction_index is None:
        direction_index = 0
    direction_index = int(direction_index)

    custom_colors = kwargs.get("custom_colors") or []
    palette_name = str(
        kwargs.get("palette_name", "")
    ).strip()
    user_prompt = str(
        kwargs.get("creative_prompt", "")
    ).strip()

    color_direction = ""

    if custom_colors:
        color_direction = (
            "Use the requested brand colors: "
            + ", ".join(
                str(c) for c in custom_colors
            )
            + "."
        )
    elif palette_name:
        color_direction = (
            "Requested color palette: "
            + palette_name
            + "."
        )

    creative_prompt = " ".join(
        value
        for value in [
            user_prompt,
            color_direction,
        ]
        if value
    )

    seed = 91373 + direction_index * 7919

    print(
        "[IMAGE] Gemini+Horde business description:",
        description[:160],
    )

    # Create exactly one semantic concept for this logo.
    direction = create_art_direction_with_gemini(
        business_name=business_name,
        industry=industry,
        description=description,
        style=style,
        creative_prompt=creative_prompt,
        concept_index=direction_index,
        semantic_territory=kwargs.get(
            "semantic_territory"
        ),
        accepted_visual_history=kwargs.get(
            "accepted_visual_history"
        ),
    )

    print(
        "[IMAGE] Gemini concept:",
        direction.get("concept_name", ""),
    )
    print(
        "[IMAGE] Gemini metaphor:",
        direction.get("visual_metaphor", ""),
    )

    # Audit the concept before Flux sees it.
    direction = audit_art_direction_with_gemini(
        direction=direction,
        business_name=business_name,
        industry=industry,
        description=description,
        style=style,
        creative_prompt=creative_prompt,
    )

    print(
        "[IMAGE] Audited concept:",
        direction.get("concept_name", ""),
    )

    prompt = str(
        direction.get("image_prompt", "")
    ).strip()

    if not prompt:
        raise RuntimeError(
            "Gemini returned an empty image prompt."
        )

    best_raw_image = None
    best_score = float("-inf")
    best_review = None
    best_direction = None
    last_error = None

    # Remember visual families already rejected during this concept
    # so later retries cannot simply rotate through stock logo forms.
    failed_visual_families = []

    # Keep the concept fixed. Flux renders it, then Vision judges
    # what was actually produced and can redesign the construction.
    for attempt in range(3):
        attempt_seed = seed + attempt * 104729

        print(
            f"[IMAGE] Gemini+Horde Vision candidate "
            f"{attempt + 1}/3, seed={attempt_seed}"
        )

        try:
            horde_context = kwargs.get("horde_execution_context")

            if isinstance(horde_context, dict):
                raw_image = generate_symbol_with_ai_horde_persistent(
                    prompt=prompt,
                    seed=attempt_seed,
                    attempt_index=attempt,
                    context=horde_context,
                )
            else:
                raw_image = generate_symbol_with_ai_horde(
                    prompt=prompt,
                    seed=attempt_seed,
                )

            raw_image = _validate_image(
                raw_image,
                "gemini-horde",
            )

            _check_cloud_logo_quality(
                raw_image
            )

            print(
                "[IMAGE] Candidate passed "
                "technical quality gate."
            )

            review = review_generated_symbol_with_gemini(
                image_bytes=raw_image,
                business_name=business_name,
                industry=industry,
                description=description,
                direction=direction,
                accepted_visual_history=kwargs.get(
                    "accepted_visual_history"
                ),
            )

            try:
                score = float(
                    review.get("average_score", 0)
                )
            except (TypeError, ValueError):
                score = 0.0

            decision = str(
                review.get("decision", "REJECT")
            ).strip().upper()

            print(
                "[IMAGE] Vision sees:",
                review.get("looks_like", ""),
            )
            print(
                "[IMAGE] Vision decision:",
                decision,
                "score=",
                round(score, 2),
            )

            # Save all technically valid candidates. If none earns
            # PASS, production can still use the strongest candidate.
            if (
                best_raw_image is None
                or score > best_score
            ):
                best_raw_image = raw_image
                best_score = score
                best_review = review
                best_direction = dict(direction)

            if decision == "PASS":
                print(
                    "[IMAGE] Candidate passed Gemini Vision."
                )

                generation_metadata = kwargs.get(
                    "generation_metadata"
                )
                if isinstance(generation_metadata, dict):
                    selected_direction = dict(direction)
                    selected_direction["vision_review"] = dict(
                        review
                    )
                    selected_direction[
                        "selected_by_vision"
                    ] = True
                    generation_metadata[
                        "ai_concept"
                    ] = selected_direction

                return _compose_if_symbol(
                    raw_image,
                    "gemini-horde",
                    **kwargs,
                )

            print(
                "[IMAGE] Vision rejection:",
                review.get("primary_failure", ""),
            )

            failed_family = str(
                review.get(
                    "failed_visual_family",
                    "",
                )
            ).strip()

            if (
                failed_family
                and failed_family not in failed_visual_families
            ):
                failed_visual_families.append(
                    failed_family
                )

            if failed_visual_families:
                print(
                    "[IMAGE] Rejected visual families:",
                    ", ".join(failed_visual_families),
                )

            revised_prompt = str(
                review.get("revised_image_prompt", "")
            ).strip()

            if revised_prompt:
                prompt = revised_prompt

                # Preserve the revised construction in the context
                # supplied to Vision on the next iteration.
                direction = dict(direction)
                direction["image_prompt"] = prompt

                redesign = str(
                    review.get("redesign_strategy", "")
                ).strip()

                if redesign:
                    direction[
                        "vision_redesign_strategy"
                    ] = redesign

                direction[
                    "vision_failed_families"
                ] = list(failed_visual_families)

                print(
                    "[IMAGE] Using Vision-revised "
                    "construction for next Flux attempt."
                )
            else:
                print(
                    "[IMAGE] Vision supplied no revised "
                    "prompt; retaining previous construction."
                )

        except PersistentHordeStateError:
            # Persistence/identity failures are orchestration failures,
            # not stochastic image-quality failures. Never burn later
            # attempts trying to work around uncertain remote state.
            raise

        except Exception as error:
            last_error = error

            print(
                "[IMAGE] Gemini+Horde candidate error:",
                repr(error),
            )

    # Vision rejection alone must not crash /create. A candidate
    # reaching here has already passed technical validation.
    if best_raw_image is not None:
        print(
            "[IMAGE] No candidate fully passed Vision. "
            "Using highest-scoring technically valid "
            f"candidate. Vision score={best_score:.2f}"
        )

        if best_review:
            print(
                "[IMAGE] Fallback looks like:",
                best_review.get("looks_like", ""),
            )
            print(
                "[IMAGE] Fallback failure:",
                best_review.get("primary_failure", ""),
            )

        generation_metadata = kwargs.get(
            "generation_metadata"
        )
        if (
            isinstance(generation_metadata, dict)
            and isinstance(best_direction, dict)
        ):
            selected_direction = dict(best_direction)

            if isinstance(best_review, dict):
                selected_direction["vision_review"] = dict(
                    best_review
                )

            selected_direction["selected_by_vision"] = False
            selected_direction[
                "vision_fallback_score"
            ] = best_score

            generation_metadata[
                "ai_concept"
            ] = selected_direction

        return _compose_if_symbol(
            best_raw_image,
            "gemini-horde",
            **kwargs,
        )

    raise RuntimeError(
        "Gemini+Flux failed to produce any technically valid "
        "logo symbol after 3 attempts. "
        f"Last error: {last_error}"
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
          -> deterministic local logo renderer

    Pollinations is intentionally skipped for master-logo
    artwork in auto mode because its output is not reliable
    enough for flat, unbranded production logo symbols.

    Successful Replicate logo artwork is passed through
    compose_cloud_logo(), which applies the cloud-logo
    quality gate and adds the exact business name with
    deterministic typography.

    For campaign images:

        auto
          -> Replicate when configured
          -> FLUX/Pollinations

    Local campaign rendering is not currently implemented.

    Explicit provider selection remains available. In
    particular, provider="flux" still calls Pollinations,
    but auto mode will not use it for master-logo symbols.
    """

    selected = provider or DEFAULT_PROVIDER or "local"
    selected = str(selected).strip().lower()

    purpose = _get_purpose(kwargs)

    print(f"[IMAGE] Selected provider: {selected}")
    print(f"[IMAGE] Purpose: {purpose}")

    # =====================================================
    # EXPLICIT LOCAL
    # =====================================================

    if selected == "local":
        if purpose == "symbol":
            print(
                "[IMAGE] Using deterministic "
                "local logo renderer."
            )
            return generate_local_image(**kwargs)

        raise RuntimeError(
            "Local campaign image generation "
            "is not currently available."
        )

    # =====================================================
    # EXPLICIT FLUX / POLLINATIONS
    # =====================================================

    if selected == "flux":
        print("[IMAGE] Using FLUX/Pollinations.")
        return generate_flux_image(**kwargs)

    # =====================================================
    # EXPLICIT GEMINI + FLUX
    # =====================================================
    if selected in {"gemini_flux", "gemini-flux"}:
        print(
            "[IMAGE] Using Gemini art direction "
            "+ FREE ANONYMOUS AI Horde."
        )
        return generate_gemini_flux_image(
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

        print("[IMAGE] Using Replicate.")
        return generate_replicate_provider_image(**kwargs)

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
                print("[IMAGE] Trying Replicate...")

                result = generate_replicate_provider_image(
                    **kwargs
                )

                print("[IMAGE] Replicate succeeded.")
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
            print("[IMAGE] Replicate not configured.")

        # -------------------------------------------------
        # 2A. MASTER LOGO: LOCAL FALLBACK
        # -------------------------------------------------

        if purpose == "symbol":
            print(
                "[IMAGE] Pollinations skipped for "
                "master-logo symbols in auto mode."
            )

            try:
                print(
                    "[IMAGE] Falling back to deterministic "
                    "local logo renderer..."
                )

                result = generate_local_image(**kwargs)

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

            raise RuntimeError(
                "Logo generation failed. "
                + " | ".join(errors)
            )

        # -------------------------------------------------
        # 2B. CAMPAIGN: FLUX / POLLINATIONS
        # -------------------------------------------------

        if purpose == "campaign":
            try:
                print("[IMAGE] Trying FLUX/Pollinations for campaign image...")
                result = generate_flux_image(**kwargs)
                print("[IMAGE] Campaign generation succeeded.")
                return result
            except Exception as error:
                print("[IMAGE] Remote campaign generation failed:", repr(error))
                print("[IMAGE] Using offline campaign fallback.")
                return generate_local_campaign(**kwargs)
        raise ValueError(
            f"Unknown image purpose: {purpose}"
        )

    raise ValueError(
        f"Unknown image provider: {selected}"
    )


