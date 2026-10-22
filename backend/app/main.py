import json
import uuid
import threading
from uuid import UUID
from pathlib import Path

from dotenv import load_dotenv

# =========================================================
# PATHS + ENVIRONMENT
# =========================================================

BACKEND_DIR = Path(__file__).resolve().parent.parent

ENV_FILE = BACKEND_DIR / ".env"

load_dotenv(ENV_FILE)


# =========================================================
# IMPORTS AFTER .ENV IS LOADED
# =========================================================

from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
)

from fastapi.middleware.cors import (
    CORSMiddleware,
)

from fastapi.responses import (
    FileResponse,
)

from fastapi.staticfiles import (
    StaticFiles,
)

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from .database import get_db, SessionLocal
from .models import (
    Asset,
    BrandKit,
    LogoGenerationJob,
    Project,
)

from .services.brand_evaluator import (
    evaluate_brand,
)

from .services.brand_intelligence import (
    generate_brand_intelligence,
)

from .services.brand_package import (
    create_brand_package,
)

from .services.brand_memory import (
    get_brand_memory as load_brand_memory,
    sync_brand_memory,
)

from .services.color_extractor import (
    extract_dominant_colors,
)

from .services.image_generator import (
    generate_logo_image,
)

from .services.image_provider import (
    generate_image,
)

from .services.logo_renderer import (
    render_logo,
)

from .services.logo_quality import (
    evaluate_candidate,
    select_diverse_candidates,
)

from .services.logo_raster_quality import (
    analyze_logo_png,
)

from .services.video_provider import (
    generate_video,
)

# =========================================================
# APPLICATION
# =========================================================

app = FastAPI(
    title="AI Brand Automation API",
    description=("Hybrid cloud and local " "AI-powered brand automation system"),
    version="6.0.0",
)


# =========================================================
# GENERATED FILES
# =========================================================

GENERATED_DIR = BACKEND_DIR / "generated"

GENERATED_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


app.mount(
    "/generated",
    StaticFiles(directory=str(GENERATED_DIR)),
    name="generated",
)


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# REQUEST MODELS
# =========================================================


class BrandRequest(BaseModel):
    business_name: str
    description: str
    industry: str
    style: str


class LogoGenerationRequest(BaseModel):
    count: int = 3
    logo_style: str = ""
    palette: str = ""
    custom_colors: list[str] = Field(default_factory=list)
    creative_prompt: str = ""


class CampaignImageRequest(BaseModel):
    prompt: str = ""
    provider: str = "auto"


class LogoRefinementRequest(BaseModel):
    primary_color: str = ""
    secondary_color: str = ""
    accent_color: str = ""
    typography_personality: str = ""
    presentation_layout: str = ""
    background_mode: str = ""
    treatment: str = ""
    instruction: str = ""


# =========================================================
# PROJECT SERIALIZER
# =========================================================


def project_to_dict(
    project: Project,
):

    return {
        "id": str(project.id),
        "business_name": project.business_name,
        "description": project.description,
        "industry": project.industry,
        "style": project.style,
        "generation_palette": project.generation_palette or "",
        "generation_custom_colors": (
            json.loads(project.generation_custom_colors)
            if project.generation_custom_colors
            else []
        ),
        "generation_logo_style": project.generation_logo_style or "",
        "generation_creative_prompt": project.generation_creative_prompt or "",
        "created_at": project.created_at,
    }


# =========================================================
# ASSET SERIALIZER
# =========================================================


def asset_to_dict(
    asset: Asset,
):

    return {
        "id": str(asset.id),
        "project_id": str(asset.project_id),
        "asset_type": asset.asset_type,
        "url": asset.url,
        "prompt": asset.prompt,
        "specification": (
            json.loads(asset.specification)
            if asset.specification
            else None
        ),
        "is_selected": bool(asset.is_selected),
        "created_at": asset.created_at,
    }


# =========================================================
# BRAND KIT SERIALIZER
# =========================================================


def brand_kit_to_dict(
    brand_kit: BrandKit,
):

    try:

        personality = json.loads(brand_kit.personality) if brand_kit.personality else []

        if not isinstance(
            personality,
            list,
        ):

            personality = []

    except Exception:

        personality = []

    return {
        "id": str(brand_kit.id),
        "project_id": str(brand_kit.project_id),
        "primary_color": brand_kit.primary_color,
        "secondary_color": brand_kit.secondary_color,
        "accent_color": brand_kit.accent_color,
        "slogan": brand_kit.slogan,
        "personality": personality,
        "tone": brand_kit.tone,
        "target_audience": brand_kit.target_audience,
        "marketing_message": brand_kit.marketing_message,
        "heading_font": brand_kit.heading_font,
        "body_font": brand_kit.body_font,
        "created_at": brand_kit.created_at,
    }


# =========================================================
# GET LOCAL ASSET PATH
# =========================================================


def get_local_path(
    asset: Asset,
):

    if not asset.url:

        return None

    if "/generated/" not in asset.url:

        return None

    filename = asset.url.split("/generated/")[-1]

    # Avoid accepting paths such as ../../file.

    filename = Path(filename).name

    return GENERATED_DIR / filename


# =========================================================
# COLOR EXTRACTION
# =========================================================


def extract_palette(
    file_path: Path,
):

    colors = extract_dominant_colors(
        file_path,
        number_of_colors=3,
    )

    if not colors:

        raise ValueError("No colors were extracted.")

    colors = list(colors)

    while len(colors) < 3:

        colors.append(colors[-1])

    return {
        "primary_color": colors[0],
        "secondary_color": colors[1],
        "accent_color": colors[2],
    }


# =========================================================
# CREATE LOGO CONCEPTS
# =========================================================


def clean_extracted_palette(
    palette: dict,
) -> dict:
    """
    Remove near-white background colors from an extracted
    logo palette.
    """

    fallback_colors = [
        "#111827",
        "#6366F1",
        "#8B5CF6",
    ]

    keys = [
        "primary_color",
        "secondary_color",
        "accent_color",
    ]

    def is_near_white(value) -> bool:
        if not isinstance(value, str):
            return True

        value = value.strip().lstrip("#")

        if len(value) != 6:
            return True

        try:
            red = int(value[0:2], 16)
            green = int(value[2:4], 16)
            blue = int(value[4:6], 16)
        except ValueError:
            return True

        return red >= 240 and green >= 240 and blue >= 240

    cleaned = {}

    for index, key in enumerate(keys):
        color = palette.get(key)

        if not color or is_near_white(color):
            color = fallback_colors[index]

        cleaned[key] = color

    return cleaned


from app.services.logo_ai_engine import create_semantic_portfolio_with_gemini


def create_logo_concepts(
    project: Project,
    db: Session,
    count: int = 3,
    logo_style: str = "",
    palette_name: str = "",
    custom_colors: list[str] | None = None,
    creative_prompt: str = "",
    horde_execution_context: dict | None = None,
):
    """
    Generate a bounded internal candidate pool, measure rendered output,
    reject weak candidates, select a diverse top set, and persist only
    the requested number of winners.

    Expensive generation happens before any Asset writer transaction.
    """

    custom_colors = custom_colors or []

    effective_style = (
        logo_style.strip()
        if logo_style.strip()
        else project.style
    )

    existing_logo_count = (
        db.query(Asset)
        .filter(
            Asset.project_id == project.id,
            Asset.asset_type == "logo",
        )
        .count()
    )

    project_id = project.id
    business_name = project.business_name
    industry = project.industry
    description = project.description

    # Start with only the requested number of semantic territories.
    # Rejected actual pixels trigger bounded replacement territories.
    initial_pool_size = count
    max_concept_budget = max(count, count * 2)

    semantic_portfolio = create_semantic_portfolio_with_gemini(
        business_name=business_name,
        industry=industry,
        description=description,
        style=effective_style,
        creative_prompt=creative_prompt,
        count=initial_pool_size,
    )

    rejection_history = []
    accepted_visual_history = []
    pool_size = initial_pool_size

    print(
        "[LOGO] Gemini semantic portfolio:",
        [
            territory.get("territory_name", "")
            for territory in semantic_portfolio
        ],
    )

    print("")
    print("========================================")
    print("[LOGO] STARTING QUALITY-GATED BATCH")
    print(f"[LOGO] Project: {project_id}")
    print(f"[LOGO] Business: {business_name}")
    print(f"[LOGO] Existing concepts: {existing_logo_count}")
    print(f"[LOGO] Winners requested: {count}")
    print(
        "[LOGO] Initial candidate pool: "
        f"{initial_pool_size}"
    )
    print(
        "[LOGO] Maximum adaptive concept budget: "
        f"{max_concept_budget}"
    )
    print(f"[LOGO] Logo style: {effective_style}")
    print(f"[LOGO] Palette: {palette_name}")
    print(
        "[LOGO] Custom colors: "
        f"{custom_colors if custom_colors else 'none'}"
    )
    print(
        "[LOGO] Creative prompt: "
        f"{creative_prompt if creative_prompt else 'none'}"
    )
    print("========================================")

    candidates = []

    try:
        pool_index = 0

        while (
            pool_index < len(semantic_portfolio)
            and pool_index < max_concept_budget
        ):
            absolute_index = (
                existing_logo_count
                + pool_index
            )
            direction_index = absolute_index % 9

            print("")
            print("----------------------------------------")
            print(
                "[LOGO] Building internal candidate "
                f"{pool_index + 1}/{max_concept_budget}"
            )
            print(
                "[LOGO] Creative direction: "
                f"{direction_index}"
            )
            print("----------------------------------------")

            generation_result = generate_logo_image(
                business_name=business_name,
                industry=industry,
                style=effective_style,
                description=description,
                direction_index=direction_index,
                provider="gemini_flux",
                palette_name=palette_name,
                custom_colors=custom_colors,
                creative_prompt=creative_prompt,
                use_ai_specification=False,
                semantic_territory=semantic_portfolio[
                    pool_index
                ],
                accepted_visual_history=(
                    accepted_visual_history
                ),
                horde_execution_context=(
                    horde_execution_context
                ),
            )

            if not isinstance(generation_result, dict):
                raise RuntimeError(
                    "Logo generator returned invalid result data."
                )

            image_bytes = generation_result.get(
                "image_bytes"
            )
            specification = generation_result.get(
                "specification"
            )

            vision_passed = bool(
                generation_result.get(
                    "vision_passed",
                    False,
                )
            )

            try:
                vision_score = float(
                    generation_result.get(
                        "vision_score",
                        0.0,
                    )
                )
            except (TypeError, ValueError):
                vision_score = 0.0

            if not isinstance(specification, dict):
                raise RuntimeError(
                    "Logo generator returned invalid specification."
                )

            if not isinstance(
                image_bytes,
                (bytes, bytearray),
            ):
                raise RuntimeError(
                    "Logo generator returned invalid image data."
                )

            image_bytes = bytes(image_bytes)

            if len(image_bytes) < 1000:
                raise RuntimeError(
                    "Generated logo is too small or invalid."
                )

            raster = analyze_logo_png(image_bytes)

            semantic_relevance = 0.72
            if specification.get("semantic_territory"):
                semantic_relevance += 0.08
            if specification.get("industry_form"):
                semantic_relevance += 0.06

            distinctiveness = 0.68
            if specification.get("identity_strategy"):
                distinctiveness += 0.06
            if specification.get("identity_construction"):
                distinctiveness += 0.05
            if specification.get("negative_space_idea"):
                distinctiveness += 0.04

            initial_role = str(
                specification.get(
                    "initial_role",
                    "",
                )
            ).strip().lower()

            # Initials are not a quality criterion. The AI symbol path
            # intentionally avoids letters unless the user explicitly asks.
            initial_integration = 0.70

            element_count = int(
                specification.get(
                    "element_count",
                    4,
                )
                or 4
            )

            quality = evaluate_candidate(
                element_count=element_count,
                max_elements=8,
                occupancy=raster["bbox_occupancy"],
                contrast=raster["contrast"],
                small_size_survival=(
                    raster["small_size_survival"]
                ),
                balance=raster["balance"],
                silhouette_strength=(
                    raster["silhouette_strength"]
                ),
                semantic_relevance=min(
                    1.0,
                    semantic_relevance,
                ),
                distinctiveness=min(
                    1.0,
                    distinctiveness,
                ),
                initial_integration=initial_integration,
                disconnected_fragments=0,
                cliche_detected=False,
            )

            if raster["edge_clipped"]:
                quality["accepted"] = False
                quality["reasons"] = tuple(
                    list(quality.get("reasons", ()))
                    + ["edge-clipped"]
                )

            strategy = str(
                specification.get(
                    "identity_strategy",
                    "",
                )
            )
            construction = str(
                specification.get(
                    "identity_construction",
                    "",
                )
            )
            industry_form = str(
                specification.get(
                    "industry_form",
                    "",
                )
            )
            variant_key = str(
                specification.get(
                    "v5_variant_key",
                    specification.get(
                        "variant_seed",
                        pool_index,
                    ),
                )
            )

            features = {
                "occupancy": raster[
                    "bbox_occupancy"
                ],
                "balance": raster["balance"],
                "silhouette_strength": raster[
                    "silhouette_strength"
                ],
                "semantic_relevance": min(
                    1.0,
                    semantic_relevance,
                ),
                "initial_integration": (
                    initial_integration
                ),
                # Neutral legacy slot retained for compatibility with
                # the existing diversity-distance feature vector.
                "angularity": 0.50,
                "openness": raster[
                    "aspect_balance"
                ],
                "symmetry": min(
                    1.0,
                    raster["ink_occupancy"] * 2.0,
                ),
            }

            specification["quality_gate"] = {
                "raster": raster,
                "quality": quality,
                "internal_pool_index": pool_index,
                "strategy": strategy,
                "construction": construction,
                "industry_form": industry_form,
            }

            # Gemini Vision judges the actual generated pixels.
            # A deterministic raster score must never override a
            # semantic/creative Vision rejection.
            specification["vision_gate"] = {
                "passed": vision_passed,
                "score": vision_score,
            }

            candidates.append(
                {
                    "image_bytes": image_bytes,
                    "specification": specification,
                    "quality": quality,
                    "features": features,
                    "variant_key": variant_key,
                    "vision_passed": vision_passed,
                    "vision_score": vision_score,
                }
            )

            print(
                "[LOGO] Candidate score: "
                f"{quality['score']:.4f} "
                f"accepted={quality['accepted']}"
            )

            ai_concept = specification.get("ai_concept", {})
            if not isinstance(ai_concept, dict):
                ai_concept = {}

            vision_review = ai_concept.get(
                "vision_review",
                {},
            )
            if not isinstance(vision_review, dict):
                vision_review = {}

            if vision_passed:
                accepted_record = {
                    "territory_name": str(
                        semantic_portfolio[pool_index].get(
                            "territory_name",
                            "",
                        )
                    ).strip(),
                    "concept_name": str(
                        ai_concept.get(
                            "concept_name",
                            "",
                        )
                    ).strip(),
                    "looks_like": str(
                        vision_review.get(
                            "looks_like",
                            "",
                        )
                    ).strip(),
                    "visual_metaphor": str(
                        ai_concept.get(
                            "visual_metaphor",
                            "",
                        )
                    ).strip(),
                    "physical_construction": str(
                        ai_concept.get(
                            "physical_construction",
                            "",
                        )
                    ).strip(),
                }

                accepted_visual_history.append(
                    accepted_record
                )

                print(
                    "[LOGO] Reserved accepted visual topology:",
                    accepted_record,
                )

            if not vision_passed:
                ai_concept = specification.get("ai_concept", {})
                if not isinstance(ai_concept, dict):
                    ai_concept = {}

                vision_review = ai_concept.get(
                    "vision_review",
                    {},
                )
                if not isinstance(vision_review, dict):
                    vision_review = {}

                rejection_record = {
                    "territory_name": str(
                        semantic_portfolio[pool_index].get(
                            "territory_name",
                            "",
                        )
                    ).strip(),
                    "looks_like": str(
                        vision_review.get(
                            "looks_like",
                            "",
                        )
                    ).strip(),
                    "failed_visual_family": str(
                        vision_review.get(
                            "failed_visual_family",
                            "",
                        )
                    ).strip(),
                    "primary_failure": str(
                        vision_review.get(
                            "primary_failure",
                            "",
                        )
                    ).strip(),
                }

                rejection_history.append(
                    rejection_record
                )

                print(
                    "[LOGO] Recorded batch rejection:",
                    rejection_record,
                )

            pool_index += 1

            passed_so_far = sum(
                1
                for candidate in candidates
                if candidate.get("vision_passed") is True
            )

            if passed_so_far >= count:
                print(
                    "[LOGO] Required Vision PASS count reached; "
                    "stopping adaptive generation."
                )
                break

            remaining_queued = (
                len(semantic_portfolio) - pool_index
            )
            passes_still_needed = count - passed_so_far

            if (
                remaining_queued < passes_still_needed
                and len(semantic_portfolio)
                < max_concept_budget
            ):
                replacements_allowed = (
                    max_concept_budget
                    - len(semantic_portfolio)
                )
                replacements_needed = min(
                    passes_still_needed
                    - remaining_queued,
                    replacements_allowed,
                )

                if replacements_needed > 0:
                    print(
                        "[LOGO] Requesting adaptive replacement "
                        f"territory count={replacements_needed}"
                    )

                    replacement_territories = (
                        create_semantic_portfolio_with_gemini(
                            business_name=business_name,
                            industry=industry,
                            description=description,
                            style=effective_style,
                            creative_prompt=creative_prompt,
                            count=replacements_needed,
                            existing_territories=(
                                semantic_portfolio
                            ),
                            rejection_history=(
                                rejection_history
                            ),
                        )
                    )

                    semantic_portfolio.extend(
                        replacement_territories
                    )
                    pool_size = len(
                        semantic_portfolio
                    )

                    print(
                        "[LOGO] Adaptive territories added:",
                        [
                            territory.get(
                                "territory_name",
                                "",
                            )
                            for territory
                            in replacement_territories
                        ],
                    )

        vision_passed_candidates = [
            candidate
            for candidate in candidates
            if candidate.get("vision_passed") is True
        ]

        vision_rejected_candidates = [
            candidate
            for candidate in candidates
            if candidate.get("vision_passed") is not True
        ]

        print(
            "[LOGO] Vision-qualified candidates: "
            f"{len(vision_passed_candidates)}/{len(candidates)}"
        )

        # Only Vision-approved pixels participate in normal winner
        # selection. Rejected artwork is reserved strictly for the
        # final emergency fallback.
        selected = select_diverse_candidates(
            vision_passed_candidates,
            count=count,
            minimum_distance=0.055,
        )

        # The objective gate should improve ranking without making
        # generation brittle while the legacy V4 renderer remains the
        # local fallback. Fill any missing slots from the highest-scoring
        # non-selected candidates, but record that fallback explicitly.
        if len(selected) < count:
            selected_ids = {
                id(candidate)
                for candidate in selected
            }

            remaining = sorted(
                (
                    candidate
                    for candidate in vision_passed_candidates
                    if id(candidate)
                    not in selected_ids
                ),
                key=lambda candidate: (
                    -float(
                        candidate.get(
                            "quality",
                            {},
                        ).get("score", 0.0)
                    ),
                    str(
                        candidate.get(
                            "variant_key",
                            "",
                        )
                    ),
                ),
            )

            for candidate in remaining:
                candidate["specification"][
                    "quality_gate"
                ]["fallback_selection"] = True

                selected.append(candidate)

                if len(selected) >= count:
                    break

        if len(selected) < count:
            print(
                "[LOGO] WARNING: insufficient Vision PASS candidates. "
                "Using highest Vision-scoring rejected candidates only "
                "to keep generation non-fatal."
            )

            selected_ids = {
                id(candidate)
                for candidate in selected
            }

            emergency = sorted(
                (
                    candidate
                    for candidate in vision_rejected_candidates
                    if id(candidate) not in selected_ids
                ),
                key=lambda candidate: (
                    -float(candidate.get("vision_score", 0.0)),
                    -float(
                        candidate.get(
                            "quality",
                            {},
                        ).get("score", 0.0)
                    ),
                ),
            )

            for candidate in emergency:
                candidate["specification"][
                    "vision_gate"
                ]["emergency_fallback"] = True

                selected.append(candidate)

                if len(selected) >= count:
                    break

        if len(selected) < count:
            raise RuntimeError(
                "Logo generation produced fewer candidates "
                "than requested."
            )

        concepts = []

        for winner_index, candidate in enumerate(
            selected[:count]
        ):
            concept_number = (
                existing_logo_count
                + winner_index
                + 1
            )

            specification = candidate[
                "specification"
            ]
            image_bytes = candidate["image_bytes"]

            filename = (
                f"{project_id}-"
                f"logo-{concept_number}-"
                f"{uuid.uuid4()}.png"
            )
            file_path = GENERATED_DIR / filename

            file_path.write_bytes(image_bytes)

            image_url = (
                "http://127.0.0.1:8000"
                f"/generated/{filename}"
            )

            palette = {
                "primary_color": specification.get(
                    "primary_color",
                    "#111827",
                ),
                "secondary_color": specification.get(
                    "secondary_color",
                    "#6366F1",
                ),
                "accent_color": specification.get(
                    "accent_color",
                    "#8B5CF6",
                ),
            }

            try:
                asset = Asset(
                    project_id=project_id,
                    asset_type="logo",
                    url=image_url,
                    prompt=(
                        f"Quality-selected logo concept "
                        f"{concept_number} for "
                        f"{business_name}"
                    ),
                    specification=json.dumps(
                        specification
                    ),
                    is_selected=False,
                )

                db.add(asset)
                db.commit()
                db.refresh(asset)

            except Exception:
                db.rollback()

                try:
                    if file_path.exists():
                        file_path.unlink()
                except OSError:
                    pass

                raise

            concepts.append(
                {
                    "asset": asset,
                    "palette": palette,
                }
            )

            print(
                "[LOGO] Persisted winner "
                f"{winner_index + 1}/{count} "
                f"score="
                f"{candidate['quality']['score']:.4f}"
            )

        print("")
        print("========================================")
        print(
            f"[LOGO] Selected {len(concepts)} "
            f"winners from {pool_size} candidates."
        )
        print("========================================")

        return concepts

    except Exception as error:
        db.rollback()

        print(
            "[LOGO] Batch failed:",
            repr(error),
        )

        raise


# =========================================================
# HOME
# =========================================================


@app.get("/")
def home():

    return {
        "message": ("AI Brand Automation " "API is running"),
        "version": "6.0.0",
    }


# =========================================================
# HEALTH
# =========================================================


@app.get("/health")
def health():

    return {
        "status": "ok",
        "version": "6.0.0",
    }


# =========================================================
# CREATE BRAND PROJECT
#
# This creates:
#
# Project
# Brand intelligence
# BrandKit
#
# It intentionally does NOT wait for logo generation.
# =========================================================


@app.post("/brand")
def create_brand(
    brand: BrandRequest,
    db: Session = Depends(get_db),
):

    # =====================================================
    # VALIDATE INPUT
    # =====================================================

    business_name = brand.business_name.strip()

    description = brand.description.strip()

    industry = brand.industry.strip()

    style = brand.style.strip()

    if not business_name:

        raise HTTPException(
            status_code=400,
            detail=("Business name is required."),
        )

    if not description:

        raise HTTPException(
            status_code=400,
            detail=("Business description " "is required."),
        )

    if not industry:

        raise HTTPException(
            status_code=400,
            detail=("Industry is required."),
        )

    if not style:

        raise HTTPException(
            status_code=400,
            detail=("Brand style is required."),
        )

    # =====================================================
    # CREATE PROJECT
    # =====================================================

    try:

        project = Project(
            business_name=(business_name),
            description=(description),
            industry=(industry),
            style=(style),
        )

        db.add(project)

        db.commit()

        db.refresh(project)

        print(
            "[BRAND] Project created:",
            project.id,
        )

    except Exception as error:

        db.rollback()

        print(
            "[BRAND] Project creation error:",
            repr(error),
        )

        raise HTTPException(
            status_code=500,
            detail=("Could not create project."),
        )

    # =====================================================
    # BRAND INTELLIGENCE
    # =====================================================

    try:

        print("[AI] Generating " "brand intelligence...")

        intelligence = generate_brand_intelligence(
            business_name=(project.business_name),
            industry=(project.industry),
            description=(project.description),
            style=(project.style),
        )

        if not isinstance(
            intelligence,
            dict,
        ):

            raise RuntimeError("Brand intelligence " "returned invalid data.")

        print("[AI] Brand intelligence complete.")

    except Exception as error:

        print(
            "[AI] Ollama unavailable:",
            repr(error),
        )

        # =============================================
        # SAFE FALLBACK STRATEGY
        # =============================================

        intelligence = {
            "slogan": "Built For What Comes Next",
            "personality": [
                "Professional",
                "Modern",
                "Reliable",
            ],
            "tone": ("Clear, confident " "and professional"),
            "target_audience": ("Customers seeking " "quality and reliability"),
            "marketing_message": (
                "A modern brand built " "around quality, trust " "and customer value."
            ),
            "typography": {
                "heading": "Montserrat",
                "body": "Inter",
            },
        }

    # =====================================================
    # NORMALIZE INTELLIGENCE
    # =====================================================

    typography = intelligence.get(
        "typography",
        {},
    )

    if not isinstance(
        typography,
        dict,
    ):

        typography = {}

    personality = intelligence.get(
        "personality",
        [],
    )

    if not isinstance(
        personality,
        list,
    ):

        personality = []

    # =====================================================
    # CREATE BRAND KIT
    # =====================================================

    try:

        brand_kit = BrandKit(
            project_id=(project.id),
            # Temporary palette until
            # a logo is selected.
            primary_color=("#111827"),
            secondary_color=("#6366F1"),
            accent_color=("#8B5CF6"),
            slogan=(
                intelligence.get(
                    "slogan",
                    "",
                )
                or ""
            ),
            personality=(json.dumps(personality)),
            tone=(
                intelligence.get(
                    "tone",
                    "",
                )
                or ""
            ),
            target_audience=(
                intelligence.get(
                    "target_audience",
                    "",
                )
                or ""
            ),
            marketing_message=(
                intelligence.get(
                    "marketing_message",
                    "",
                )
                or ""
            ),
            heading_font=(
                typography.get(
                    "heading",
                    "Montserrat",
                )
                or "Montserrat"
            ),
            body_font=(
                typography.get(
                    "body",
                    "Inter",
                )
                or "Inter"
            ),
        )

        db.add(brand_kit)

        db.commit()

        db.refresh(brand_kit)

        print("[BRAND] Brand kit saved.")

    except Exception as error:

        db.rollback()

        print(
            "[BRAND] Brand kit error:",
            repr(error),
        )

        raise HTTPException(
            status_code=500,
            detail=("Project was created, " "but brand kit creation failed."),
        )

    return {
        "message": "Brand project created",
        "project": project_to_dict(project),
        "brand_kit": brand_kit_to_dict(brand_kit),
        "concepts": [],
    }


# =========================================================
# GET ALL PROJECTS
# =========================================================


@app.get("/projects")
def get_projects(
    db: Session = Depends(get_db),
):

    projects = db.query(Project).order_by(Project.created_at.desc()).all()

    return {"projects": [project_to_dict(project) for project in projects]}


# =========================================================
# GET PROJECT
# =========================================================


@app.get("/projects/{project_id}")
def get_project(
    project_id: UUID,
    db: Session = Depends(get_db),
):

    project = db.query(Project).filter(Project.id == project_id).first()

    if not project:

        raise HTTPException(
            status_code=404,
            detail=("Project not found."),
        )

    return {"project": project_to_dict(project)}


# =========================================================
# GENERATE LOGO CONCEPTS
# Supports 3 / 6 / 9 concepts
# =========================================================


def _logo_job_to_dict(job: LogoGenerationJob) -> dict:
    try:
        state = (
            json.loads(job.state_json)
            if job.state_json
            else {}
        )
    except Exception:
        state = {}

    return {
        "id": str(job.id),
        "project_id": str(job.project_id),
        "status": job.status,
        "requested_count": int(job.requested_count or 3),
        "progress_message": job.progress_message or "",
        "error_message": job.error_message or "",
        "state": state,
        "created_at": job.created_at,
        "updated_at": job.updated_at,
    }




def _run_hybrid_logo_generation_job(job_id: UUID) -> None:
    """
    New hybrid jobs only.
    Old Horde jobs never enter this worker.
    """
    from app.services.hybrid_logo_service import (
        get_config,
        prepare_hybrid_concepts,
        generate_hybrid_batch,
    )
    from app.services.hybrid_asset_persistence import (
        persist_hybrid_checkpoints,
    )

    db = SessionLocal()

    try:
        job = (
            db.query(LogoGenerationJob)
            .filter(LogoGenerationJob.id == job_id)
            .first()
        )

        if job is None:
            return

        settings = json.loads(job.settings_json or "{}")

        if settings.get("generation_mode") != "hybrid_v1":
            raise RuntimeError("Not a hybrid generation job.")

        if int(job.requested_count or 0) != 3:
            raise RuntimeError("Hybrid mode requires exactly 3 logos.")

        get_config()

        project = (
            db.query(Project)
            .filter(Project.id == job.project_id)
            .first()
        )

        if project is None:
            raise RuntimeError("Project not found.")

        job.status = "running"
        job.progress_message = "Preparing hybrid logo concepts."
        db.commit()

        colors = list(settings.get("custom_colors") or [])

        # Reuse the project's existing BrandKit palette when the
        # generation request does not include custom colors.
        if len(colors) < 2:
            brand_kit = (
                db.query(BrandKit)
                .filter(BrandKit.project_id == project.id)
                .first()
            )

            if brand_kit:
                saved_colors = [
                    brand_kit.primary_color,
                    brand_kit.secondary_color,
                ]

                if all(saved_colors):
                    colors = saved_colors

        if len(colors) < 2:
            raise RuntimeError(
                "Hybrid generation requires two selected brand colors. "
                "Choose two brand colors before generating logos."
            )

        business = {
            "name": project.business_name,
            "industry": project.industry,
            "description": project.description,
            "style": settings.get("logo_style") or project.style,
            "creative_prompt": settings.get("creative_prompt") or "",
            "colors": colors[:2],
        }

        # Save anything already completed.
        persist_hybrid_checkpoints(
            db, project, job.id, GENERATED_DIR
        )

        # A restarted job must NOT submit remote requests again.
        state = json.loads(job.state_json or "{}")

        if state.get("hybrid_started"):
            raise RuntimeError(
                "Hybrid job was previously started. "
                "Existing checkpoints were recovered. "
                "Automatic regeneration is blocked."
            )

        state["hybrid_started"] = True
        job.state_json = json.dumps(state)
        db.commit()

        concepts = prepare_hybrid_concepts(business)

        job.progress_message = (
            "Generating three logos using Local AI and Hugging Face with local fallback."
        )
        db.commit()

        generate_hybrid_batch(
            business=business,
            job_id=job.id,
            concepts=concepts,
        )

        assets = persist_hybrid_checkpoints(
            db, project, job.id, GENERATED_DIR
        )

        if len(assets) != 3:
            raise RuntimeError(
                f"Expected 3 hybrid logos, saved {len(assets)}."
            )

        job.status = "completed"
        job.progress_message = (
            f"{len(assets)} hybrid logos saved."
        )
        job.error_message = None
        db.commit()

    except Exception as error:
        db.rollback()

        try:
            job = (
                db.query(LogoGenerationJob)
                .filter(LogoGenerationJob.id == job_id)
                .first()
            )

            if job is not None:
                project = (
                    db.query(Project)
                    .filter(Project.id == job.project_id)
                    .first()
                )

                if project is not None:
                    from app.services.hybrid_asset_persistence import (
                        persist_hybrid_checkpoints,
                    )

                    persist_hybrid_checkpoints(
                        db, project, job.id, GENERATED_DIR
                    )

                job.status = "failed"
                job.error_message = str(error)[:2000]
                job.progress_message = (
                    "Hybrid generation stopped. "
                    "Completed logos were preserved."
                )
                db.commit()

        except Exception:
            db.rollback()

        print("[HYBRID JOB] Failed:", repr(error))

    finally:
        db.close()


def _run_logo_generation_job(job_id: UUID) -> None:
    """
    Local background worker.

    Uses its own SQLAlchemy session. The existing creative pipeline
    remains unchanged; the HTTP request is no longer held open while
    anonymous AI Horde waits in the volunteer queue.

    No paid image fallback is introduced here.
    """
    db = SessionLocal()

    try:
        job = (
            db.query(LogoGenerationJob)
            .filter(LogoGenerationJob.id == job_id)
            .first()
        )

        if job is None:
            print(
                "[LOGO JOB] Job disappeared before worker start:",
                job_id,
            )
            return

        project = (
            db.query(Project)
            .filter(Project.id == job.project_id)
            .first()
        )

        if project is None:
            job.status = "failed"
            job.error_message = "Project not found."
            job.progress_message = "Generation failed."
            db.commit()
            return

        try:
            settings = (
                json.loads(job.settings_json)
                if job.settings_json
                else {}
            )
        except Exception:
            settings = {}

        # Preserve persistent Horde execution state when this worker
        # is being recovered after a backend restart. In particular,
        # never erase the attempt seed/identity associated with an
        # already-submitted anonymous Horde UUID.
        try:
            worker_state = (
                json.loads(job.state_json)
                if job.state_json
                else {}
            )
        except Exception:
            worker_state = {}

        if not isinstance(worker_state, dict):
            worker_state = {}

        has_active_horde_job = bool(
            str(job.active_horde_job_id or "").strip()
        )

        job.status = "running"
        job.error_message = None

        if has_active_horde_job:
            worker_state["phase"] = (
                worker_state.get("phase") or "queued"
            )
            job.progress_message = (
                "Resuming existing free anonymous AI Horde "
                "generation after backend restart."
            )
        else:
            worker_state["phase"] = "generating"
            job.progress_message = (
                "Gemini is preparing concepts and anonymous "
                "AI Horde is generating artwork."
            )

        worker_state.setdefault("completed", 0)
        worker_state["requested"] = int(
            job.requested_count or 3
        )
        worker_state["free_image_provider"] = (
            "ai_horde_anonymous"
        )
        worker_state["paid_fallback"] = False

        job.state_json = json.dumps(worker_state)
        db.commit()

        print(
            "[LOGO JOB] Started persistent background job:",
            job.id,
        )

        concepts = create_logo_concepts(
            project=project,
            db=db,
            count=int(job.requested_count or 3),
            logo_style=str(
                settings.get("logo_style") or ""
            ),
            palette_name=str(
                settings.get("palette") or ""
            ),
            custom_colors=list(
                settings.get("custom_colors") or []
            ),
            creative_prompt=str(
                settings.get("creative_prompt") or ""
            ),
            horde_execution_context={
                "db": db,
                "job": job,
            },
        )

        job.status = "completed"
        job.progress_message = (
            f"{len(concepts)} logo concepts generated."
        )
        job.error_message = None
        job.state_json = json.dumps(
            {
                "phase": "completed",
                "completed": len(concepts),
                "requested": int(job.requested_count or 3),
                "free_image_provider": "ai_horde_anonymous",
                "paid_fallback": False,
                "asset_ids": [
                    str(concept["asset"].id)
                    for concept in concepts
                ],
            }
        )
        db.commit()

        print(
            "[LOGO JOB] Completed:",
            job.id,
        )

    except Exception as error:
        db.rollback()

        try:
            job = (
                db.query(LogoGenerationJob)
                .filter(LogoGenerationJob.id == job_id)
                .first()
            )

            if job is not None:
                job.status = "failed"
                job.progress_message = "Logo generation failed."
                job.error_message = str(error)[:2000]
                try:
                    failed_state = (
                        json.loads(job.state_json)
                        if job.state_json
                        else {}
                    )
                except Exception:
                    failed_state = {}

                if not isinstance(failed_state, dict):
                    failed_state = {}

                failed_state["phase"] = "failed"
                failed_state["free_image_provider"] = (
                    "ai_horde_anonymous"
                )
                failed_state["paid_fallback"] = False

                job.state_json = json.dumps(failed_state)
                db.commit()
        except Exception:
            db.rollback()

        print(
            "[LOGO JOB] Failed:",
            job_id,
            repr(error),
        )

    finally:
        db.close()



@app.on_event("startup")
def recover_logo_generation_jobs() -> None:
    """
    Resume unfinished local logo orchestration after backend restart.

    Recovery starts a local worker for each queued/running database job.
    If that job has an active anonymous Horde UUID, the persistent Horde
    layer checks/collects that exact remote job rather than submitting a
    replacement solely because the backend restarted.
    """
    db = SessionLocal()

    try:
        jobs = (
            db.query(LogoGenerationJob)
            .filter(
                LogoGenerationJob.status.in_(
                    ["queued", "running"]
                )
            )
            .all()
        )

        if not jobs:
            print("[LOGO JOB] Startup recovery: no unfinished jobs.")
            return

        print(
            "[LOGO JOB] Startup recovery found",
            len(jobs),
            "unfinished job(s).",
        )

        for job in jobs:
            job_id = job.id

            try:
                recovered_settings = json.loads(
                    job.settings_json or "{}"
                )
            except (TypeError, ValueError):
                recovered_settings = {}

            if recovered_settings.get("generation_mode") == "hybrid_v1":
                print(
                    "[HYBRID JOB] Startup recovery: "
                    "remote resubmission blocked for",
                    job_id,
                )

                # Preserve partial results and mark the interrupted job
                # as failed. Do not restart any remote request.
                try:
                    from app.services.hybrid_asset_persistence import (
                        persist_hybrid_checkpoints,
                    )

                    recovered_project = (
                        db.query(Project)
                        .filter(Project.id == job.project_id)
                        .first()
                    )

                    if recovered_project is not None:
                        persist_hybrid_checkpoints(
                            db,
                            recovered_project,
                            job.id,
                            GENERATED_DIR,
                        )

                    job.status = "failed"
                    job.progress_message = (
                        "Hybrid generation interrupted. "
                        "Completed logos preserved."
                    )
                    job.error_message = (
                        "Backend restarted; automatic remote "
                        "generation is blocked."
                    )
                    db.commit()

                except Exception as recovery_error:
                    db.rollback()
                    print(
                        "[HYBRID JOB] Checkpoint recovery failed:",
                        repr(recovery_error),
                    )

                continue

            print(
                "[LOGO JOB] Recovering:",
                job_id,
                "status=",
                job.status,
                "horde=",
                job.active_horde_job_id,
            )

            thread = threading.Thread(
                target=_run_logo_generation_job,
                args=(job_id,),
                daemon=True,
                name=f"logo-job-recovery-{job_id}",
            )
            thread.start()

    finally:
        db.close()


@app.post(
    "/projects/{project_id}/generate-logo",
    status_code=202,
)
def generate_more_logos(
    project_id: UUID,
    request: LogoGenerationRequest,
    db: Session = Depends(get_db),
):
    if request.count not in {3, 6, 9}:
        raise HTTPException(
            status_code=400,
            detail="Logo count must be 3, 6, or 9.",
        )

    project = (
        db.query(Project)
        .filter(Project.id == project_id)
        .first()
    )

    if not project:
        raise HTTPException(
            status_code=404,
            detail="Project not found.",
        )

    # Never submit another batch while this project already has
    # active free generation work.
    active_job = (
        db.query(LogoGenerationJob)
        .filter(
            LogoGenerationJob.project_id == project.id,
            LogoGenerationJob.status.in_(
                ["queued", "running"]
            ),
        )
        .order_by(
            LogoGenerationJob.created_at.desc()
        )
        .first()
    )

    if active_job is not None:
        print(
            "[LOGO JOB] Returning existing active job:",
            active_job.id,
        )
        return {
            "message": "Logo generation is already in progress.",
            "job": _logo_job_to_dict(active_job),
        }

    from app.services.hybrid_logo_service import CONFIG_PATH

    hybrid_config = json.loads(
        CONFIG_PATH.read_text(encoding="utf-8-sig")
    )

    hybrid_enabled = hybrid_config.get("enabled") is True

    if hybrid_enabled and request.count != 3:
        raise HTTPException(
            status_code=400,
            detail="Hybrid mode currently supports exactly 3 logos.",
        )

    # Persist the same user settings the previous synchronous
    # endpoint persisted.
    if request.palette.strip():
        project.generation_palette = request.palette.strip()

    if request.custom_colors:
        project.generation_custom_colors = json.dumps(
            request.custom_colors
        )
    elif not project.generation_custom_colors:
        project.generation_custom_colors = json.dumps([])

    if request.logo_style.strip():
        project.generation_logo_style = (
            request.logo_style.strip()
        )
    elif not project.generation_logo_style:
        project.generation_logo_style = project.style

    if request.creative_prompt.strip():
        project.generation_creative_prompt = (
            request.creative_prompt.strip()
        )

    settings = {
        "logo_style": request.logo_style,
        "palette": request.palette,
        "custom_colors": request.custom_colors,
        "creative_prompt": request.creative_prompt,
    }

    job = LogoGenerationJob(
        project_id=project.id,
        status="queued",
        requested_count=str(request.count),
        settings_json=json.dumps(settings),
        state_json=json.dumps(
            {
                "phase": "queued",
                "completed": 0,
                "requested": request.count,
                "free_image_provider": "ai_horde_anonymous",
                "paid_fallback": False,
            }
        ),
        progress_message=(
            "Logo generation queued using free anonymous AI Horde."
        ),
        error_message=None,
    )

    db.add(job)
    db.commit()
    db.refresh(job)

    if hybrid_enabled:
        settings["generation_mode"] = "hybrid_v1"
        job.settings_json = json.dumps(settings)

        state = json.loads(job.state_json or "{}")
        state["generation_mode"] = "hybrid_v1"
        job.state_json = json.dumps(state)
        job.progress_message = "Hybrid logo generation queued."
        db.commit()

    worker = threading.Thread(
        target=(
            _run_hybrid_logo_generation_job
            if hybrid_enabled
            else _run_logo_generation_job
        ),
        args=(job.id,),
        daemon=True,
        name=f"logo-job-{job.id}",
    )
    worker.start()

    print(
        "[LOGO JOB] Queued:",
        job.id,
    )

    return {
        "message": "Logo generation queued.",
        "job": _logo_job_to_dict(job),
    }


@app.get(
    "/projects/{project_id}/logo-generation/{job_id}"
)
def get_logo_generation_job(
    project_id: UUID,
    job_id: UUID,
    db: Session = Depends(get_db),
):
    job = (
        db.query(LogoGenerationJob)
        .filter(
            LogoGenerationJob.id == job_id,
            LogoGenerationJob.project_id == project_id,
        )
        .first()
    )

    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Logo generation job not found.",
        )

    payload = _logo_job_to_dict(job)

    if job.status == "completed":
        assets = (
            db.query(Asset)
            .filter(
                Asset.project_id == project_id,
                Asset.asset_type == "logo",
            )
            .order_by(Asset.created_at.desc())
            .limit(int(job.requested_count or 3))
            .all()
        )

        payload["concepts"] = [
            asset_to_dict(asset)
            for asset in reversed(assets)
        ]

    return {
        "job": payload,
    }


# =========================================================
# SELECT LOGO + PALETTE + VIDEO
# =========================================================


# =========================================================
# REFINE LOGO
# =========================================================


@app.post(
    "/projects/{project_id}/logos/{asset_id}/refine"
)
def refine_logo(
    project_id: UUID,
    asset_id: UUID,
    request: LogoRefinementRequest,
    db: Session = Depends(get_db),
):
    """
    Create a controlled revision of an existing logo.

    The source asset is never modified. The revision inherits the complete
    persisted specification, applies only validated refinement controls,
    rerenders deterministically, and is saved as a new logo Asset.
    """

    project = (
        db.query(Project)
        .filter(Project.id == project_id)
        .first()
    )

    if project is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found.",
        )

    source = (
        db.query(Asset)
        .filter(
            Asset.id == asset_id,
            Asset.project_id == project.id,
            Asset.asset_type == "logo",
        )
        .first()
    )

    if source is None:
        raise HTTPException(
            status_code=404,
            detail="Source logo not found.",
        )

    try:
        specification = (
            json.loads(source.specification)
            if source.specification
            else {}
        )
    except Exception as error:
        raise HTTPException(
            status_code=400,
            detail="Source logo specification is invalid.",
        ) from error

    if not isinstance(specification, dict):
        raise HTTPException(
            status_code=400,
            detail="Source logo specification is invalid.",
        )

    # -----------------------------------------------------
    # VALIDATED REFINEMENT CONTROLS
    # -----------------------------------------------------

    def validated_hex(
        value: str,
        field_name: str,
    ) -> str:
        cleaned = str(value or "").strip().upper()

        if not cleaned:
            return ""

        if (
            len(cleaned) != 7
            or cleaned[0] != "#"
            or any(
                character not in "0123456789ABCDEF"
                for character in cleaned[1:]
            )
        ):
            raise HTTPException(
                status_code=400,
                detail=(
                    f"{field_name} must be a "
                    "6-digit HEX color."
                ),
            )

        return cleaned

    color_updates = {
        "primary_color": validated_hex(
            request.primary_color,
            "primary_color",
        ),
        "secondary_color": validated_hex(
            request.secondary_color,
            "secondary_color",
        ),
        "accent_color": validated_hex(
            request.accent_color,
            "accent_color",
        ),
    }

    for key, value in color_updates.items():
        if value:
            specification[key] = value

    typography = (
        str(request.typography_personality or "")
        .strip()
        .lower()
    )

    allowed_typography = {
        "modern",
        "geometric",
        "elegant",
        "classic",
        "bold",
    }

    if typography:
        if typography not in allowed_typography:
            raise HTTPException(
                status_code=400,
                detail="Unsupported typography personality.",
            )
        specification["typography_personality"] = typography

    layout = (
        str(request.presentation_layout or "")
        .strip()
        .lower()
    )

    allowed_layouts = {
        "stacked",
        "horizontal",
        "emblem",
        "typography-led",
    }

    if layout:
        if layout not in allowed_layouts:
            raise HTTPException(
                status_code=400,
                detail="Unsupported presentation layout.",
            )
        specification["presentation_layout"] = layout

    background_mode = (
        str(request.background_mode or "")
        .strip()
        .lower()
    )

    if background_mode:
        if background_mode not in {"light", "dark"}:
            raise HTTPException(
                status_code=400,
                detail="background_mode must be light or dark.",
            )
        specification["background_mode"] = background_mode

    treatment = (
        str(request.treatment or "")
        .strip()
        .lower()
    )

    if treatment:
        if treatment not in {
            "flat",
            "premium-gradient",
        }:
            raise HTTPException(
                status_code=400,
                detail="Unsupported logo treatment.",
            )
        specification["treatment"] = treatment

    instruction = str(
        request.instruction or ""
    ).strip()

    if len(instruction) > 500:
        raise HTTPException(
            status_code=400,
            detail="Refinement instruction is too long.",
        )

    # -----------------------------------------------------
    # REVISION LINEAGE
    # -----------------------------------------------------

    refinement = specification.get("refinement")
    if not isinstance(refinement, dict):
        refinement = {}

    try:
        previous_revision = int(
            refinement.get("revision_number", 0)
        )
    except (TypeError, ValueError):
        previous_revision = 0

    root_asset_id = str(
        refinement.get("root_asset_id")
        or source.id
    )

    specification["refinement"] = {
        "root_asset_id": root_asset_id,
        "parent_asset_id": str(source.id),
        "revision_number": previous_revision + 1,
        "instruction": instruction,
        "controls": {
            "primary_color": color_updates["primary_color"],
            "secondary_color": color_updates["secondary_color"],
            "accent_color": color_updates["accent_color"],
            "typography_personality": typography,
            "presentation_layout": layout,
            "background_mode": background_mode,
            "treatment": treatment,
        },
    }

    # A revision must be deterministic but should have its own persisted
    # identity rather than silently changing the source specification.
    revision_id = uuid.uuid4()
    specification["refinement_revision_id"] = str(
        revision_id
    )

    try:
        rendered = render_logo(
            project.business_name,
            project.industry,
            specification,
        )

        png = rendered.get("png")

        if not isinstance(
            png,
            (bytes, bytearray),
        ) or len(png) < 1000:
            raise RuntimeError(
                "Logo renderer returned invalid PNG data."
            )

        filename = (
            f"logo_refinement_"
            f"{project.id.hex}_"
            f"{revision_id.hex}.png"
        )

        output_path = GENERATED_DIR / filename
        output_path.write_bytes(bytes(png))

        url = (
            f"http://127.0.0.1:8000"
            f"/generated/{filename}"
        )

        revision = Asset(
            project_id=project.id,
            asset_type="logo",
            url=url,
            prompt=(
                instruction
                or "Controlled logo refinement"
            ),
            specification=json.dumps(
                specification,
                ensure_ascii=False,
            ),
            is_selected=False,
        )

        db.add(revision)
        db.commit()
        db.refresh(revision)

    except HTTPException:
        raise
    except Exception as error:
        db.rollback()

        try:
            if "output_path" in locals():
                output_path.unlink(
                    missing_ok=True
                )
        except Exception:
            pass

        print(
            "[LOGO REFINEMENT] Error:",
            repr(error),
        )

        raise HTTPException(
            status_code=500,
            detail="Could not create logo refinement.",
        ) from error

    return {
        "message": "Logo refinement created.",
        "source_logo_id": str(source.id),
        "revision_number": (
            specification["refinement"][
                "revision_number"
            ]
        ),
        "logo": asset_to_dict(revision),
    }


@app.post("/projects/{project_id}" "/logos/{asset_id}/select")
def select_logo(
    project_id: UUID,
    asset_id: UUID,
    db: Session = Depends(get_db),
):

    # =====================================================
    # PROJECT
    # =====================================================

    project = db.query(Project).filter(Project.id == project_id).first()

    if not project:

        raise HTTPException(
            status_code=404,
            detail=("Project not found."),
        )

    # =====================================================
    # LOGO
    # =====================================================

    logo = (
        db.query(Asset)
        .filter(
            Asset.id == asset_id,
            Asset.project_id == project.id,
            Asset.asset_type == "logo",
        )
        .first()
    )

    if not logo:

        raise HTTPException(
            status_code=404,
            detail=("Logo not found."),
        )

    logo_path = get_local_path(logo)

    if logo_path is None or not logo_path.exists():

        raise HTTPException(
            status_code=400,
            detail=("Logo file not found."),
        )

    try:

        # =================================================
        # SELECT LOGO
        # =================================================

        (
            db.query(Asset)
            .filter(
                Asset.project_id == project.id,
                Asset.asset_type == "logo",
            )
            .update(
                {Asset.is_selected: False},
                synchronize_session=False,
            )
        )

        logo.is_selected = True

        # =================================================
        # FINAL COLOR PALETTE
        # =================================================
        # Logo specifications are authoritative. Do not
        # infer official brand colors from rendered pixels.

        try:
            specification = (
                json.loads(logo.specification)
                if logo.specification
                else {}
            )

            palette = {
                "primary_color": specification[
                    "primary_color"
                ],
                "secondary_color": specification[
                    "secondary_color"
                ],
                "accent_color": specification[
                    "accent_color"
                ],
            }

        except Exception as error:
            # Legacy logos created before specification
            # persistence can still use pixel extraction.
            print(
                "[COLOR] Stored specification unavailable; "
                "using legacy extraction:",
                repr(error),
            )

            palette = clean_extracted_palette(
                extract_palette(logo_path)
            )

        # =================================================
        # BRAND KIT
        # =================================================

        brand_kit = db.query(BrandKit).filter(BrandKit.project_id == project.id).first()

        if not brand_kit:

            brand_kit = BrandKit(
                project_id=(project.id),
                primary_color=(palette["primary_color"]),
                secondary_color=(palette["secondary_color"]),
                accent_color=(palette["accent_color"]),
                slogan="",
                personality=(json.dumps([])),
                tone="",
                target_audience="",
                marketing_message="",
                heading_font=("Montserrat"),
                body_font=("Inter"),
            )

            db.add(brand_kit)

        else:

            brand_kit.primary_color = palette["primary_color"]

            brand_kit.secondary_color = palette["secondary_color"]

            brand_kit.accent_color = palette["accent_color"]

        # =================================================
        # PERSONALITY
        # =================================================

        try:

            personality = (
                json.loads(brand_kit.personality) if brand_kit.personality else []
            )

            if not isinstance(
                personality,
                list,
            ):

                personality = []

        except Exception:

            personality = []

        # Logo approval is intentionally fast. Campaign/video generation
        # belongs to the dedicated advertising workflow and must not block
        # selection or refinement approval.
        db.commit()
        db.refresh(logo)
        db.refresh(brand_kit)

        return {
            "message": "Brand identity finalized.",
            "logo": asset_to_dict(logo),
            "brand_kit": brand_kit_to_dict(brand_kit),
            "video": None,
        }

    except Exception as error:

        db.rollback()

        print(
            "[SELECT] Error:",
            repr(error),
        )

        raise HTTPException(
            status_code=500,
            detail=("Could not finalize brand."),
        )


# =========================================================
# GET PROJECT ASSETS
# =========================================================


@app.get("/projects/{project_id}/assets")
def get_assets(
    project_id: UUID,
    db: Session = Depends(get_db),
):

    project = db.query(Project).filter(Project.id == project_id).first()

    if not project:

        raise HTTPException(
            status_code=404,
            detail=("Project not found."),
        )

    assets = (
        db.query(Asset)
        .filter(Asset.project_id == project.id)
        .order_by(Asset.created_at.desc())
        .all()
    )

    result = []

    for asset in assets:

        data = asset_to_dict(asset)

        if asset.asset_type == "logo":

            file_path = get_local_path(asset)

            if file_path and file_path.exists():

                try:
                    specification = (
                        json.loads(asset.specification)
                        if asset.specification
                        else {}
                    )

                    if all(
                        specification.get(key)
                        for key in (
                            "primary_color",
                            "secondary_color",
                            "accent_color",
                        )
                    ):
                        data["palette"] = {
                            "primary_color": specification[
                                "primary_color"
                            ],
                            "secondary_color": specification[
                                "secondary_color"
                            ],
                            "accent_color": specification[
                                "accent_color"
                            ],
                        }
                    else:
                        # Compatibility for logos generated
                        # before specification persistence.
                        data["palette"] = clean_extracted_palette(
                            extract_palette(file_path)
                        )

                except Exception as error:

                    print(
                        "[COLOR] Asset palette error:",
                        repr(error),
                    )

                    data["palette"] = None

            else:

                data["palette"] = None

        result.append(data)

    return {"assets": result}


# =========================================================
# BRAND MEMORY
# =========================================================


@app.get("/projects/{project_id}/brand-memory")
def read_brand_memory(
    project_id: UUID,
    db: Session = Depends(get_db),
):
    project = db.query(Project).filter(Project.id == project_id).first()

    if not project:
        raise HTTPException(
            status_code=404,
            detail="Project not found.",
        )

    memory = load_brand_memory(
        db=db,
        project_id=project.id,
    )

    return {
        "brand_memory": memory,
    }


@app.post("/projects/{project_id}/brand-memory/sync")
def synchronize_brand_memory(
    project_id: UUID,
    db: Session = Depends(get_db),
):
    project = db.query(Project).filter(Project.id == project_id).first()

    if not project:
        raise HTTPException(
            status_code=404,
            detail="Project not found.",
        )

    brand_kit = (
        db.query(BrandKit)
        .filter(BrandKit.project_id == project.id)
        .first()
    )

    if not brand_kit:
        raise HTTPException(
            status_code=400,
            detail="Brand kit has not been generated.",
        )

    try:
        asset, memory = sync_brand_memory(
            db=db,
            project=project,
            brand_kit=brand_kit,
        )
    except ValueError as error:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error
    except Exception:
        db.rollback()
        raise

    return {
        "message": "Brand Memory synchronized.",
        "asset_id": str(asset.id),
        "brand_memory": memory,
    }


# =========================================================
# GET BRAND KIT
# =========================================================


@app.get("/projects/{project_id}/brand-kit")
def get_brand_kit(
    project_id: UUID,
    db: Session = Depends(get_db),
):

    project = db.query(Project).filter(Project.id == project_id).first()

    if not project:

        raise HTTPException(
            status_code=404,
            detail=("Project not found."),
        )

    brand_kit = db.query(BrandKit).filter(BrandKit.project_id == project.id).first()

    if not brand_kit:

        return {"brand_kit": None}

    return {"brand_kit": brand_kit_to_dict(brand_kit)}


# =========================================================
# GENERATE CAMPAIGN IMAGE
# =========================================================


@app.post("/projects/{project_id}/generate-image")
def generate_campaign_image(
    project_id: UUID,
    request: CampaignImageRequest,
    db: Session = Depends(get_db),
):

    file_path = None

    # =====================================================
    # PROJECT
    # =====================================================

    project = db.query(Project).filter(Project.id == project_id).first()

    if not project:

        raise HTTPException(
            status_code=404,
            detail=("Project not found."),
        )

    try:

        # =================================================
        # BRAND KIT
        # =================================================

        brand_kit = db.query(BrandKit).filter(BrandKit.project_id == project.id).first()

        primary_color = brand_kit.primary_color if brand_kit else "#111827"

        secondary_color = brand_kit.secondary_color if brand_kit else "#4F46E5"

        accent_color = brand_kit.accent_color if brand_kit else "#06B6D4"

        # =================================================
        # CAMPAIGN CONCEPT
        # =================================================

        custom_prompt = request.prompt.strip()

        if custom_prompt:

            concept = custom_prompt

        else:

            concept = (
                "Premium marketing campaign "
                f"visual for "
                f"{project.business_name}. "
                f"{project.description}"
            )

        specification = {
            "concept": concept,
            "logo_type": "abstract",
            "shape": "dynamic",
            "primary_color": primary_color,
            "secondary_color": secondary_color,
            "accent_color": accent_color,
        }

        # =================================================
        # HYBRID IMAGE GENERATION
        # =================================================

        image_bytes = generate_image(
            provider=(request.provider),
            purpose=("campaign"),
            specification=(specification),
            business_name=(project.business_name),
            industry=(project.industry),
            style=(project.style),
        )

        if not isinstance(
            image_bytes,
            (
                bytes,
                bytearray,
            ),
        ):

            raise RuntimeError("Image provider returned " "invalid data.")

        if len(image_bytes) < 1000:

            raise RuntimeError("Generated campaign image " "is invalid.")

        # =================================================
        # SAVE IMAGE
        # =================================================

        filename = f"{project.id}-" f"campaign-" f"{uuid.uuid4()}.png"

        file_path = GENERATED_DIR / filename

        file_path.write_bytes(bytes(image_bytes))

        image_url = "http://127.0.0.1:8000" f"/generated/{filename}"

        # =================================================
        # SAVE ASSET
        # =================================================

        asset = Asset(
            project_id=(project.id),
            asset_type=("campaign_image"),
            url=(image_url),
            prompt=(concept),
            is_selected=False,
        )

        db.add(asset)

        db.commit()

        db.refresh(asset)

        return {
            "message": ("Campaign image " "generated successfully."),
            "provider": request.provider,
            "asset": asset_to_dict(asset),
        }

    except HTTPException:

        db.rollback()

        raise

    except Exception as error:

        db.rollback()

        # =================================================
        # DELETE ORPHAN FILE
        # =================================================

        if file_path is not None and file_path.exists():

            try:

                file_path.unlink()

            except OSError:

                pass

        print(
            "[CAMPAIGN] Error:",
            repr(error),
        )

        raise HTTPException(
            status_code=500,
            detail=("Campaign image " "generation failed."),
        )


# =========================================================
# DOWNLOAD BRAND PACKAGE
# =========================================================


@app.get("/projects/{project_id}/download-package")
def download_brand_package(
    project_id: UUID,
    db: Session = Depends(get_db),
):

    # =====================================================
    # PROJECT
    # =====================================================

    project = db.query(Project).filter(Project.id == project_id).first()

    if not project:

        raise HTTPException(
            status_code=404,
            detail=("Project not found."),
        )

    # =====================================================
    # BRAND KIT
    # =====================================================

    brand_kit = db.query(BrandKit).filter(BrandKit.project_id == project.id).first()

    if not brand_kit:

        raise HTTPException(
            status_code=400,
            detail=("Brand kit has not " "been generated."),
        )

    # =====================================================
    # SELECTED LOGO
    # =====================================================

    selected_logo = (
        db.query(Asset)
        .filter(
            Asset.project_id == project.id,
            Asset.asset_type == "logo",
            Asset.is_selected.is_(True),
        )
        .first()
    )

    if not selected_logo:

        raise HTTPException(
            status_code=400,
            detail=("Select a logo first."),
        )

    logo_path = get_local_path(selected_logo)

    if logo_path is None or not logo_path.exists():

        raise HTTPException(
            status_code=400,
            detail=("Selected logo file " "was not found."),
        )

    # =====================================================
    # LATEST VIDEO
    # =====================================================

    latest_video = (
        db.query(Asset)
        .filter(
            Asset.project_id == project.id,
            Asset.asset_type == "video",
        )
        .order_by(Asset.created_at.desc())
        .first()
    )

    video_path = None

    if latest_video:

        candidate = get_local_path(latest_video)

        if candidate and candidate.exists():

            video_path = candidate

    # =====================================================
    # BUILD ZIP
    # =====================================================

    try:

        package_path = create_brand_package(
            project=(project),
            brand_kit=(brand_kit),
            logo_path=(logo_path),
            video_path=(video_path),
            output_directory=(GENERATED_DIR),
        )

        package_path = Path(package_path)

        if not package_path.exists():

            raise RuntimeError("Brand package " "was not created.")

        return FileResponse(
            path=str(package_path),
            filename=(package_path.name),
            media_type=("application/zip"),
        )

    except Exception as error:

        print(
            "[PACKAGE] Error:",
            repr(error),
        )

        raise HTTPException(
            status_code=500,
            detail=("Could not create " "brand package."),
        )
        # =========================================================


# AI BRAND SCORE
# =========================================================


@app.get("/projects/{project_id}/brand-score")
def get_brand_score(
    project_id: UUID,
    db: Session = Depends(get_db),
):

    # =====================================================
    # PROJECT
    # =====================================================

    project = db.query(Project).filter(Project.id == project_id).first()

    if not project:

        raise HTTPException(
            status_code=404,
            detail=("Project not found."),
        )

    # =====================================================
    # BRAND KIT
    # =====================================================

    brand_kit = db.query(BrandKit).filter(BrandKit.project_id == project.id).first()

    if not brand_kit:

        raise HTTPException(
            status_code=400,
            detail=("Brand kit has not " "been generated."),
        )

    # =====================================================
    # SELECTED LOGO
    # =====================================================

    selected_logo = (
        db.query(Asset)
        .filter(
            Asset.project_id == project.id,
            Asset.asset_type == "logo",
            Asset.is_selected.is_(True),
        )
        .first()
    )

    # =====================================================
    # PERSONALITY
    # =====================================================

    try:

        personality = json.loads(brand_kit.personality) if brand_kit.personality else []

        if not isinstance(
            personality,
            list,
        ):

            personality = []

    except Exception:

        personality = []

    # =====================================================
    # EVALUATE
    # =====================================================

    try:

        evaluation = evaluate_brand(
            business_name=(project.business_name),
            industry=(project.industry),
            description=(project.description),
            style=(project.style),
            slogan=(brand_kit.slogan or ""),
            personality=(personality),
            tone=(brand_kit.tone or ""),
            target_audience=(brand_kit.target_audience or ""),
            marketing_message=(brand_kit.marketing_message or ""),
            heading_font=(brand_kit.heading_font or ""),
            body_font=(brand_kit.body_font or ""),
            primary_color=(brand_kit.primary_color or ""),
            secondary_color=(brand_kit.secondary_color or ""),
            accent_color=(brand_kit.accent_color or ""),
            has_selected_logo=(selected_logo is not None),
        )

        return {
            "project_id": str(project.id),
            "business_name": project.business_name,
            "brand_score": evaluation,
        }

    except Exception as error:

        print(
            "[BRAND SCORE] Error:",
            repr(error),
        )

        raise HTTPException(
            status_code=500,
            detail=("Could not evaluate " "brand identity."),
        )

from pathlib import Path
import json

from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from uuid import UUID

from .database import get_db
from .models import Project, Asset, BrandKit
from .services.video_provider import generate_video


@app.post("/projects/{project_id}/generate-video")
def generate_project_video(
    project_id: UUID,
    db: Session = Depends(get_db),
):
    project = (
        db.query(Project)
        .filter(Project.id == project_id)
        .first()
    )

    if not project:
        raise HTTPException(
            status_code=404,
            detail="Project not found.",
        )

    logo = (
        db.query(Asset)
        .filter(
            Asset.project_id == project_id,
            Asset.asset_type == "logo",
            Asset.is_selected == True,
        )
        .first()
    )

    if not logo:
        raise HTTPException(
            status_code=400,
            detail="Select a logo before generating a video.",
        )

    logo_filename = Path(
        logo.url.split("/generated/")[-1]
    ).name

    logo_path = GENERATED_DIR / logo_filename

    if not logo_path or not logo_path.exists():
        raise HTTPException(
            status_code=400,
            detail="Selected logo file is missing.",
        )

    kit = (
        db.query(BrandKit)
        .filter(BrandKit.project_id == project_id)
        .first()
    )

    if not kit:
        raise HTTPException(
            status_code=400,
            detail="Generate the brand identity first.",
        )

    try:
        output_path = generate_video(
            provider="local",
            logo_path=logo_path,
            output_directory=GENERATED_DIR,
            business_name=project.business_name,
            slogan=kit.slogan or "",
            personality=kit.personality or "",
            marketing_message=kit.marketing_message or "",
            primary_color=kit.primary_color,
            secondary_color=kit.secondary_color,
            accent_color=kit.accent_color,
        )

        output_path = Path(output_path)

        video_url = (
            "http://127.0.0.1:8000"
            f"/generated/{output_path.name}"
        )

        asset = Asset(
            project_id=project.id,
            asset_type="video",
            url=video_url,
            prompt="Local promotional brand video",
            specification=json.dumps({
                "provider": "local",
                "generator": "moviepy_v2",
                "logo_asset_id": str(logo.id),
                "duration_seconds": 10,
            }),
            is_selected=False,
        )

        db.add(asset)
        db.commit()
        db.refresh(asset)

        return {
            "message": "Promotional video generated successfully.",
            "asset_id": str(asset.id),
            "video_url": video_url,
        }

    except Exception as error:
        db.rollback()

        print("[VIDEO] Generation failed:", repr(error))

        raise HTTPException(
            status_code=500,
            detail=f"Video generation failed: {error}",
        )


