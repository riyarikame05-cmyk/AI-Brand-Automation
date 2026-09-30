import json
import uuid
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

from .database import get_db
from .models import (
    Asset,
    BrandKit,
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

from .services.logo_art_director import (
    generate_art_directions,
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


def create_logo_concepts(
    project: Project,
    db: Session,
    count: int = 3,
    logo_style: str = "",
    palette_name: str = "",
    custom_colors: list[str] | None = None,
    creative_prompt: str = "",
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

    pool_sizes = {
        3: 6,
        6: 10,
        9: 14,
    }
    pool_size = pool_sizes.get(count, count)

    art_directions = generate_art_directions(
        business_name=business_name,
        industry=industry,
        description=description,
        style=effective_style,
        count=pool_size,
        creative_prompt=creative_prompt,
    )

    print("")
    print("========================================")
    print("[LOGO] STARTING QUALITY-GATED BATCH")
    print(f"[LOGO] Project: {project_id}")
    print(f"[LOGO] Business: {business_name}")
    print(f"[LOGO] Existing concepts: {existing_logo_count}")
    print(f"[LOGO] Winners requested: {count}")
    print(f"[LOGO] Internal candidate pool: {pool_size}")
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
        for pool_index in range(pool_size):
            absolute_index = (
                existing_logo_count
                + pool_index
            )
            direction_index = absolute_index % 9

            print("")
            print("----------------------------------------")
            print(
                "[LOGO] Building internal candidate "
                f"{pool_index + 1}/{pool_size}"
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
                provider="auto",
                palette_name=palette_name,
                custom_colors=custom_colors,
                creative_prompt=creative_prompt,
                use_ai_specification=False,
                art_direction=art_directions[
                    pool_index % len(art_directions)
                ],
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

            initial_integration = (
                0.78
                if initial_role
                and initial_role
                not in {"none", "avoid", "unused"}
                else 0.58
            )

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

            strategy_codes = {
                "bespoke-monogram": 0.10,
                "negative-space-glyph": 0.22,
                "abstract-semantic": 0.34,
                "continuous-line": 0.46,
                "modular-geometry": 0.58,
                "signature-emblem": 0.70,
                "motion-ribbon": 0.82,
                "typography-led": 0.91,
                "experimental-fusion": 1.00,
            }

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
                "angularity": strategy_codes.get(
                    strategy,
                    0.50,
                ),
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

            candidates.append(
                {
                    "image_bytes": image_bytes,
                    "specification": specification,
                    "quality": quality,
                    "features": features,
                    "variant_key": variant_key,
                }
            )

            print(
                "[LOGO] Candidate score: "
                f"{quality['score']:.4f} "
                f"accepted={quality['accepted']}"
            )

        selected = select_diverse_candidates(
            candidates,
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
                    for candidate in candidates
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
            raise RuntimeError(
                "Logo quality gate could not produce "
                f"{count} usable concepts."
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


@app.post("/projects/{project_id}/generate-logo")
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

    project = db.query(Project).filter(Project.id == project_id).first()

    if not project:

        raise HTTPException(
            status_code=404,
            detail=("Project not found."),
        )

    try:

        print("[LOGO] Starting logo batch " f"for project {project.id}")

        # Persist the user's logo generation settings.
        # Empty values from Explore More must not erase the
        # original identity preferences.
        if request.palette.strip():
            project.generation_palette = (
                request.palette.strip()
            )

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

        db.commit()
        db.refresh(project)

        concepts = create_logo_concepts(
            project=(project),
            db=(db),
            count=request.count,
            logo_style=(request.logo_style),
            palette_name=(request.palette),
            custom_colors=(request.custom_colors),
            creative_prompt=(request.creative_prompt),
        )

        db.commit()

        for concept in concepts:

            db.refresh(concept["asset"])

        print("[LOGO] Batch complete.")

        return {
            "message": (f"{len(concepts)} logo concepts " "generated"),
            "concepts": [
                {
                    **asset_to_dict(concept["asset"]),
                    "palette": concept["palette"],
                }
                for concept in concepts
            ],
        }

    except Exception as error:

        db.rollback()

        print(
            "[LOGO] Generation error:",
            repr(error),
        )

        raise HTTPException(
            status_code=500,
            detail=("Logo generation failed."),
        )


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
