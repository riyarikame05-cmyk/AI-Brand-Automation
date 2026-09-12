import json
import uuid
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .database import get_db
from .models import Asset, BrandKit, Project
from .services.brand_intelligence import generate_brand_intelligence
from .services.brand_package import create_brand_package
from .services.color_extractor import extract_dominant_colors
from .services.image_generator import generate_logo_image
from .services.image_provider import generate_image
from .services.video_generator import generate_promotional_video


# =========================================================
# APPLICATION
# =========================================================

app = FastAPI(
    title="AI Brand Automation API",
    description="Local AI-powered brand automation system",
    version="5.0.0",
)


# =========================================================
# GENERATED FILES
# =========================================================

GENERATED_DIR = (
    Path(__file__).resolve().parent.parent
    / "generated"
)

GENERATED_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

app.mount(
    "/generated",
    StaticFiles(
        directory=str(GENERATED_DIR)
    ),
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


class CampaignImageRequest(BaseModel):
    prompt: str = ""
    provider: str = "auto"


# =========================================================
# SERIALIZATION HELPERS
# =========================================================

def project_to_dict(
    project: Project,
):

    return {
        "id":
            str(project.id),

        "business_name":
            project.business_name,

        "description":
            project.description,

        "industry":
            project.industry,

        "style":
            project.style,

        "created_at":
            project.created_at,
    }


def asset_to_dict(
    asset: Asset,
):

    return {
        "id":
            str(asset.id),

        "project_id":
            str(asset.project_id),

        "asset_type":
            asset.asset_type,

        "url":
            asset.url,

        "prompt":
            asset.prompt,

        "is_selected":
            bool(asset.is_selected),

        "created_at":
            asset.created_at,
    }


def brand_kit_to_dict(
    brand_kit: BrandKit,
):

    try:

        personality = (
            json.loads(
                brand_kit.personality
            )
            if brand_kit.personality
            else []
        )

        if not isinstance(
            personality,
            list,
        ):
            personality = []

    except Exception:

        personality = []


    return {
        "id":
            str(brand_kit.id),

        "project_id":
            str(brand_kit.project_id),

        "primary_color":
            brand_kit.primary_color,

        "secondary_color":
            brand_kit.secondary_color,

        "accent_color":
            brand_kit.accent_color,

        "slogan":
            brand_kit.slogan,

        "personality":
            personality,

        "tone":
            brand_kit.tone,

        "target_audience":
            brand_kit.target_audience,

        "marketing_message":
            brand_kit.marketing_message,

        "heading_font":
            brand_kit.heading_font,

        "body_font":
            brand_kit.body_font,

        "created_at":
            brand_kit.created_at,
    }


# =========================================================
# FILE HELPERS
# =========================================================

def get_local_path(
    asset: Asset,
):

    if not asset.url:

        return None


    if "/generated/" not in asset.url:

        return None


    filename = (
        asset.url
        .split("/generated/")[-1]
    )


    return (
        GENERATED_DIR
        / filename
    )


# =========================================================
# COLOR HELPER
# =========================================================

def extract_palette(
    file_path: Path,
):

    colors = (
        extract_dominant_colors(
            file_path,
            number_of_colors=3,
        )
    )


    if not colors:

        raise ValueError(
            "No colors were extracted."
        )


    # Make extraction resilient in case the
    # image contains fewer than three colors.
    colors = list(colors)


    while len(colors) < 3:

        colors.append(
            colors[-1]
        )


    return {
        "primary_color":
            colors[0],

        "secondary_color":
            colors[1],

        "accent_color":
            colors[2],
    }


# =========================================================
# LOGO GENERATION HELPER
# =========================================================

def create_logo_concepts(
    project: Project,
    db: Session,
    count: int = 3,
):

    concepts = []

    created_files = []


    try:

        for number in range(count):

            print(
                f"[LOGO] Generating "
                f"{number + 1}/{count} "
                f"for {project.business_name}"
            )


            # =============================================
            # GENERATE IMAGE
            # =============================================

            image_bytes = (
                generate_logo_image(
                    business_name=(
                        project.business_name
                    ),

                    industry=(
                        project.industry
                    ),

                    style=(
                        project.style
                    ),

                    description=(
                        project.description
                    ),
                )
            )


            if not isinstance(
                image_bytes,
                (bytes, bytearray),
            ):

                raise RuntimeError(
                    "Logo generator returned "
                    "invalid image data."
                )


            if len(image_bytes) < 1000:

                raise RuntimeError(
                    "Generated logo image "
                    "is too small or invalid."
                )


            # =============================================
            # SAVE IMAGE
            # =============================================

            filename = (
                f"{project.id}-"
                f"{uuid.uuid4()}.png"
            )


            file_path = (
                GENERATED_DIR
                / filename
            )


            file_path.write_bytes(
                bytes(image_bytes)
            )


            created_files.append(
                file_path
            )


            image_url = (
                "http://127.0.0.1:8000"
                f"/generated/{filename}"
            )


            # =============================================
            # EXTRACT COLORS
            # =============================================

            try:

                palette = (
                    extract_palette(
                        file_path
                    )
                )


            except Exception as error:

                print(
                    "[COLOR] Extraction failed:",
                    repr(error),
                )


                # Palette extraction should not destroy
                # an otherwise valid generated logo.
                palette = {
                    "primary_color":
                        "#111827",

                    "secondary_color":
                        "#6366F1",

                    "accent_color":
                        "#8B5CF6",
                }


            # =============================================
            # SAVE DATABASE ASSET
            # =============================================

            asset = Asset(
                project_id=(
                    project.id
                ),

                asset_type="logo",

                url=(
                    image_url
                ),

                prompt=(
                    f"Logo concept "
                    f"{number + 1} for "
                    f"{project.business_name}"
                ),

                is_selected=False,
            )


            db.add(
                asset
            )

            db.flush()


            concepts.append({
                "asset":
                    asset,

                "palette":
                    palette,
            })


            print(
                f"[LOGO] Completed "
                f"{number + 1}/{count}"
            )


        return concepts


    except Exception:

        # SQLAlchemy rollback happens in the
        # route calling this helper.
        #
        # Delete generated files so failed
        # generations do not leave orphan files.

        for file_path in created_files:

            try:

                if file_path.exists():

                    file_path.unlink()

            except OSError:

                pass


        raise


# =========================================================
# HOME
# =========================================================

@app.get("/")
def home():

    return {
        "message":
            "AI Brand Automation API is running",

        "version":
            "5.0.0",
    }


# =========================================================
# HEALTH
# =========================================================

@app.get("/health")
def health():

    return {
        "status":
            "ok",

        "version":
            "5.0.0",
    }


# =========================================================
# CREATE BRAND PROJECT
#
# IMPORTANT:
# This does NOT generate logos.
# Logo generation has its own endpoint.
# =========================================================

@app.post("/brand")
def create_brand(
    brand: BrandRequest,
    db: Session = Depends(get_db),
):

    # =====================================================
    # VALIDATION
    # =====================================================

    business_name = (
        brand.business_name.strip()
    )

    description = (
        brand.description.strip()
    )

    industry = (
        brand.industry.strip()
    )

    style = (
        brand.style.strip()
    )


    if not business_name:

        raise HTTPException(
            status_code=400,
            detail=(
                "Business name is required."
            ),
        )


    if not description:

        raise HTTPException(
            status_code=400,
            detail=(
                "Business description is required."
            ),
        )


    if not industry:

        raise HTTPException(
            status_code=400,
            detail=(
                "Industry is required."
            ),
        )


    if not style:

        raise HTTPException(
            status_code=400,
            detail=(
                "Brand style is required."
            ),
        )


    # =====================================================
    # CREATE AND SAVE PROJECT FIRST
    # =====================================================

    try:

        project = Project(
            business_name=(
                business_name
            ),

            description=(
                description
            ),

            industry=(
                industry
            ),

            style=(
                style
            ),
        )


        db.add(
            project
        )


        db.commit()


        db.refresh(
            project
        )


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
            detail=(
                "Could not create project."
            ),
        )


    # =====================================================
    # BRAND INTELLIGENCE
    # =====================================================

    try:

        print(
            "[AI] Generating brand intelligence..."
        )


        intelligence = (
            generate_brand_intelligence(
                business_name=(
                    project.business_name
                ),

                industry=(
                    project.industry
                ),

                description=(
                    project.description
                ),

                style=(
                    project.style
                ),
            )
        )


        if not isinstance(
            intelligence,
            dict,
        ):

            raise RuntimeError(
                "Brand intelligence returned "
                "invalid data."
            )


        print(
            "[AI] Brand intelligence complete."
        )


    except Exception as error:

        print(
            "[AI] Ollama error:",
            repr(error),
        )


        # =============================================
        # FALLBACK BRAND INTELLIGENCE
        # =============================================

        intelligence = {
            "slogan":
                "Built For What Comes Next",

            "personality": [
                "Professional",
                "Modern",
                "Reliable",
            ],

            "tone":
                (
                    "Clear, confident "
                    "and professional"
                ),

            "target_audience":
                (
                    "Customers seeking "
                    "quality and reliability"
                ),

            "marketing_message":
                (
                    "A modern brand built "
                    "around quality, trust "
                    "and customer value."
                ),

            "typography": {
                "heading":
                    "Montserrat",

                "body":
                    "Inter",
            },
        }


    # =====================================================
    # NORMALIZE AI RESPONSE
    # =====================================================

    typography = (
        intelligence.get(
            "typography",
            {},
        )
    )


    if not isinstance(
        typography,
        dict,
    ):

        typography = {}


    personality = (
        intelligence.get(
            "personality",
            [],
        )
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
            project_id=(
                project.id
            ),

            # Temporary colors.
            # These are replaced when the
            # user selects a logo.

            primary_color=(
                "#111827"
            ),

            secondary_color=(
                "#6366F1"
            ),

            accent_color=(
                "#8B5CF6"
            ),

            slogan=(
                intelligence.get(
                    "slogan",
                    ""
                )
                or ""
            ),

            personality=(
                json.dumps(
                    personality
                )
            ),

            tone=(
                intelligence.get(
                    "tone",
                    ""
                )
                or ""
            ),

            target_audience=(
                intelligence.get(
                    "target_audience",
                    ""
                )
                or ""
            ),

            marketing_message=(
                intelligence.get(
                    "marketing_message",
                    ""
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


        db.add(
            brand_kit
        )


        db.commit()


        db.refresh(
            brand_kit
        )


        print(
            "[BRAND] Brand kit saved."
        )


    except Exception as error:

        db.rollback()


        print(
            "[BRAND] Brand kit error:",
            repr(error),
        )


        raise HTTPException(
            status_code=500,
            detail=(
                "Project was created, but "
                "brand kit creation failed."
            ),
        )


    # =====================================================
    # RETURN WITHOUT WAITING FOR IMAGE GENERATION
    # =====================================================

    return {
        "message":
            "Brand project created",

        "project":
            project_to_dict(
                project
            ),

        "brand_kit":
            brand_kit_to_dict(
                brand_kit
            ),

        "concepts":
            [],
    }


# =========================================================
# GET ALL PROJECTS
# =========================================================

@app.get("/projects")
def get_projects(
    db: Session = Depends(get_db),
):

    projects = (
        db.query(Project)
        .order_by(
            Project.created_at.desc()
        )
        .all()
    )


    return {
        "projects": [
            project_to_dict(
                project
            )

            for project
            in projects
        ]
    }


# =========================================================
# GET PROJECT
# =========================================================

@app.get(
    "/projects/{project_id}"
)
def get_project(
    project_id: str,
    db: Session = Depends(get_db),
):

    project = (
        db.query(Project)
        .filter(
            Project.id
            == project_id
        )
        .first()
    )


    if not project:

        raise HTTPException(
            status_code=404,
            detail=(
                "Project not found."
            ),
        )


    return {
        "project":
            project_to_dict(
                project
            )
    }


# =========================================================
# GENERATE 3 LOGO CONCEPTS
# =========================================================

@app.post(
    "/projects/{project_id}/generate-logo"
)
def generate_more_logos(
    project_id: str,
    db: Session = Depends(get_db),
):

    project = (
        db.query(Project)
        .filter(
            Project.id
            == project_id
        )
        .first()
    )


    if not project:

        raise HTTPException(
            status_code=404,
            detail=(
                "Project not found."
            ),
        )


    try:

        print(
            "[LOGO] Starting generation "
            f"for project {project.id}"
        )


        concepts = (
            create_logo_concepts(
                project=(
                    project
                ),

                db=(
                    db
                ),

                count=3,
            )
        )


        db.commit()


        for concept in concepts:

            db.refresh(
                concept["asset"]
            )


        print(
            "[LOGO] Batch completed."
        )


        return {
            "message":
                "3 logo concepts generated",

            "concepts": [
                {
                    **asset_to_dict(
                        concept["asset"]
                    ),

                    "palette":
                        concept["palette"],
                }

                for concept
                in concepts
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
            detail=(
                "Logo generation failed."
            ),
        )


# =========================================================
# SELECT LOGO + UPDATE COLORS + GENERATE VIDEO
# =========================================================

@app.post(
    "/projects/{project_id}"
    "/logos/{asset_id}/select"
)
def select_logo(
    project_id: str,
    asset_id: str,
    db: Session = Depends(get_db),
):

    # =====================================================
    # PROJECT
    # =====================================================

    project = (
        db.query(Project)
        .filter(
            Project.id
            == project_id
        )
        .first()
    )


    if not project:

        raise HTTPException(
            status_code=404,
            detail=(
                "Project not found."
            ),
        )


    # =====================================================
    # LOGO
    # =====================================================

    logo = (
        db.query(Asset)
        .filter(
            Asset.id
            == asset_id,

            Asset.project_id
            == project.id,

            Asset.asset_type
            == "logo",
        )
        .first()
    )


    if not logo:

        raise HTTPException(
            status_code=404,
            detail=(
                "Logo not found."
            ),
        )


    logo_path = (
        get_local_path(
            logo
        )
    )


    if (
        logo_path is None
        or not logo_path.exists()
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "Logo file not found."
            ),
        )


    try:

        # =================================================
        # SELECT LOGO
        # =================================================

        (
            db.query(Asset)
            .filter(
                Asset.project_id
                == project.id,

                Asset.asset_type
                == "logo",
            )
            .update(
                {
                    Asset.is_selected:
                        False
                },

                synchronize_session=False,
            )
        )


        logo.is_selected = True


        # =================================================
        # EXTRACT FINAL COLORS
        # =================================================

        palette = (
            extract_palette(
                logo_path
            )
        )


        # =================================================
        # LOAD BRAND KIT
        # =================================================

        brand_kit = (
            db.query(BrandKit)
            .filter(
                BrandKit.project_id
                == project.id
            )
            .first()
        )


        if not brand_kit:

            brand_kit = BrandKit(
                project_id=(
                    project.id
                ),

                primary_color=(
                    palette[
                        "primary_color"
                    ]
                ),

                secondary_color=(
                    palette[
                        "secondary_color"
                    ]
                ),

                accent_color=(
                    palette[
                        "accent_color"
                    ]
                ),

                slogan="",

                personality=(
                    json.dumps([])
                ),

                tone="",

                target_audience="",

                marketing_message="",

                heading_font=(
                    "Montserrat"
                ),

                body_font=(
                    "Inter"
                ),
            )


            db.add(
                brand_kit
            )


        else:

            brand_kit.primary_color = (
                palette[
                    "primary_color"
                ]
            )


            brand_kit.secondary_color = (
                palette[
                    "secondary_color"
                ]
            )


            brand_kit.accent_color = (
                palette[
                    "accent_color"
                ]
            )


        # =================================================
        # PERSONALITY
        # =================================================

        try:

            personality = (
                json.loads(
                    brand_kit.personality
                )
                if brand_kit.personality
                else []
            )


            if not isinstance(
                personality,
                list,
            ):

                personality = []


        except Exception:

            personality = []


        # =================================================
        # GENERATE VIDEO
        # =================================================

        print(
            "[VIDEO] Generating video..."
        )


        video_path = (
            generate_promotional_video(
                logo_path=(
                    logo_path
                ),

                output_directory=(
                    GENERATED_DIR
                ),

                business_name=(
                    project.business_name
                ),

                slogan=(
                    brand_kit.slogan
                    or ""
                ),

                personality=(
                    personality
                ),

                marketing_message=(
                    brand_kit.marketing_message
                    or ""
                ),

                primary_color=(
                    brand_kit.primary_color
                ),

                secondary_color=(
                    brand_kit.secondary_color
                ),

                accent_color=(
                    brand_kit.accent_color
                ),
            )
        )


        if not video_path:

            raise RuntimeError(
                "Video generator did not "
                "return a file."
            )


        video_path = (
            Path(video_path)
        )


        if not video_path.exists():

            raise RuntimeError(
                "Generated video file "
                "does not exist."
            )


        # =================================================
        # VIDEO ASSET
        # =================================================

        video_url = (
            "http://127.0.0.1:8000"
            f"/generated/{video_path.name}"
        )


        video = Asset(
            project_id=(
                project.id
            ),

            asset_type="video",

            url=(
                video_url
            ),

            prompt=(
                "Automatic promotional "
                "video from selected logo "
                "and brand intelligence"
            ),

            is_selected=False,
        )


        db.add(
            video
        )


        db.commit()


        db.refresh(
            logo
        )

        db.refresh(
            brand_kit
        )

        db.refresh(
            video
        )


        print(
            "[VIDEO] Video completed."
        )


        return {
            "message":
                "Brand identity finalized",

            "logo":
                asset_to_dict(
                    logo
                ),

            "brand_kit":
                brand_kit_to_dict(
                    brand_kit
                ),

            "video":
                asset_to_dict(
                    video
                ),
        }


    except Exception as error:

        db.rollback()


        print(
            "[SELECT] Error:",
            repr(error),
        )


        raise HTTPException(
            status_code=500,
            detail=(
                "Could not finalize brand."
            ),
        )


# =========================================================
# GET PROJECT ASSETS
# =========================================================

@app.get(
    "/projects/{project_id}/assets"
)
def get_assets(
    project_id: str,
    db: Session = Depends(get_db),
):

    project = (
        db.query(Project)
        .filter(
            Project.id
            == project_id
        )
        .first()
    )


    if not project:

        raise HTTPException(
            status_code=404,
            detail=(
                "Project not found."
            ),
        )


    assets = (
        db.query(Asset)
        .filter(
            Asset.project_id
            == project.id
        )
        .order_by(
            Asset.created_at.desc()
        )
        .all()
    )


    result = []


    for asset in assets:

        data = (
            asset_to_dict(
                asset
            )
        )


        # =================================================
        # ADD PALETTE TO LOGOS
        # =================================================

        if (
            asset.asset_type
            == "logo"
        ):

            file_path = (
                get_local_path(
                    asset
                )
            )


            if (
                file_path
                and file_path.exists()
            ):

                try:

                    data["palette"] = (
                        extract_palette(
                            file_path
                        )
                    )


                except Exception as error:

                    print(
                        "[COLOR] Asset palette error:",
                        repr(error),
                    )


                    data["palette"] = None


            else:

                data["palette"] = None


        result.append(
            data
        )


    return {
        "assets":
            result
    }


# =========================================================
# GET BRAND KIT
# =========================================================

@app.get(
    "/projects/{project_id}/brand-kit"
)
def get_brand_kit(
    project_id: str,
    db: Session = Depends(get_db),
):

    project = (
        db.query(Project)
        .filter(
            Project.id
            == project_id
        )
        .first()
    )


    if not project:

        raise HTTPException(
            status_code=404,
            detail=(
                "Project not found."
            ),
        )


    brand_kit = (
        db.query(BrandKit)
        .filter(
            BrandKit.project_id
            == project.id
        )
        .first()
    )


    if not brand_kit:

        return {
            "brand_kit":
                None
        }


    return {
        "brand_kit":
            brand_kit_to_dict(
                brand_kit
            )
    }


# =========================================================
# GENERATE CAMPAIGN IMAGE
# =========================================================

@app.post(
    "/projects/{project_id}/generate-image"
)
def generate_campaign_image(
    project_id: str,
    request: CampaignImageRequest,
    db: Session = Depends(get_db),
):

    file_path = None


    # =====================================================
    # PROJECT
    # =====================================================

    project = (
        db.query(Project)
        .filter(
            Project.id
            == project_id
        )
        .first()
    )


    if not project:

        raise HTTPException(
            status_code=404,
            detail=(
                "Project not found."
            ),
        )


    try:

        # =================================================
        # BRAND KIT
        # =================================================

        brand_kit = (
            db.query(BrandKit)
            .filter(
                BrandKit.project_id
                == project.id
            )
            .first()
        )


        primary_color = (
            brand_kit.primary_color
            if brand_kit
            else "#111827"
        )


        secondary_color = (
            brand_kit.secondary_color
            if brand_kit
            else "#4F46E5"
        )


        accent_color = (
            brand_kit.accent_color
            if brand_kit
            else "#06B6D4"
        )


        # =================================================
        # PROMPT
        # =================================================

        custom_prompt = (
            request.prompt.strip()
        )


        if custom_prompt:

            concept = (
                custom_prompt
            )


        else:

            concept = (
                "premium marketing campaign "
                f"visual for "
                f"{project.business_name}, "
                f"{project.description}"
            )


        specification = {
            "concept":
                concept,

            "logo_type":
                "abstract",

            "shape":
                "dynamic",

            "primary_color":
                primary_color,

            "secondary_color":
                secondary_color,

            "accent_color":
                accent_color,
        }


        # =================================================
        # GENERATE IMAGE
        # =================================================

        image_bytes = (
            generate_image(
                provider=(
                    request.provider
                ),

                purpose=(
                    "campaign"
                ),

                specification=(
                    specification
                ),

                industry=(
                    project.industry
                ),

                style=(
                    project.style
                ),
            )
        )


        if not isinstance(
            image_bytes,
            (bytes, bytearray),
        ):

            raise RuntimeError(
                "Image provider returned "
                "invalid image data."
            )


        if len(image_bytes) < 1000:

            raise RuntimeError(
                "Generated image is invalid."
            )


        # =================================================
        # SAVE FILE
        # =================================================

        filename = (
            f"{project.id}-"
            f"campaign-"
            f"{uuid.uuid4()}.png"
        )


        file_path = (
            GENERATED_DIR
            / filename
        )


        file_path.write_bytes(
            bytes(image_bytes)
        )


        image_url = (
            "http://127.0.0.1:8000"
            f"/generated/{filename}"
        )


        # =================================================
        # DATABASE ASSET
        # =================================================

        asset = Asset(
            project_id=(
                project.id
            ),

            asset_type=(
                "campaign_image"
            ),

            url=(
                image_url
            ),

            prompt=(
                concept
            ),

            is_selected=False,
        )


        db.add(
            asset
        )


        db.commit()


        db.refresh(
            asset
        )


        return {
            "message":
                (
                    "Campaign image "
                    "generated successfully."
                ),

            "provider":
                request.provider,

            "asset":
                asset_to_dict(
                    asset
                ),
        }


    except HTTPException:

        db.rollback()

        raise


    except Exception as error:

        db.rollback()


        # =================================================
        # DELETE ORPHAN FILE
        # =================================================

        if (
            file_path is not None
            and file_path.exists()
        ):

            try:

                file_path.unlink()

            except OSError:

                pass


        print(
            "[CAMPAIGN] Generation error:",
            repr(error),
        )


        raise HTTPException(
            status_code=500,
            detail=(
                "Campaign image "
                "generation failed."
            ),
        )


# =========================================================
# DOWNLOAD COMPLETE BRAND PACKAGE
# =========================================================

@app.get(
    "/projects/{project_id}/download-package"
)
def download_brand_package(
    project_id: str,
    db: Session = Depends(get_db),
):

    # =====================================================
    # PROJECT
    # =====================================================

    project = (
        db.query(Project)
        .filter(
            Project.id
            == project_id
        )
        .first()
    )


    if not project:

        raise HTTPException(
            status_code=404,
            detail=(
                "Project not found."
            ),
        )


    # =====================================================
    # BRAND KIT
    # =====================================================

    brand_kit = (
        db.query(BrandKit)
        .filter(
            BrandKit.project_id
            == project.id
        )
        .first()
    )


    if not brand_kit:

        raise HTTPException(
            status_code=400,
            detail=(
                "Brand kit has not "
                "been generated."
            ),
        )


    # =====================================================
    # SELECTED LOGO
    # =====================================================

    selected_logo = (
        db.query(Asset)
        .filter(
            Asset.project_id
            == project.id,

            Asset.asset_type
            == "logo",

            Asset.is_selected.is_(
                True
            ),
        )
        .first()
    )


    if not selected_logo:

        raise HTTPException(
            status_code=400,
            detail=(
                "Select a logo first."
            ),
        )


    logo_path = (
        get_local_path(
            selected_logo
        )
    )


    if (
        logo_path is None
        or not logo_path.exists()
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "Selected logo file "
                "was not found."
            ),
        )


    # =====================================================
    # LATEST VIDEO
    # =====================================================

    latest_video = (
        db.query(Asset)
        .filter(
            Asset.project_id
            == project.id,

            Asset.asset_type
            == "video",
        )
        .order_by(
            Asset.created_at.desc()
        )
        .first()
    )


    video_path = None


    if latest_video:

        candidate = (
            get_local_path(
                latest_video
            )
        )


        if (
            candidate
            and candidate.exists()
        ):

            video_path = (
                candidate
            )


    # =====================================================
    # CREATE ZIP PACKAGE
    # =====================================================

    try:

        package_path = (
            create_brand_package(
                project=(
                    project
                ),

                brand_kit=(
                    brand_kit
                ),

                logo_path=(
                    logo_path
                ),

                video_path=(
                    video_path
                ),

                output_directory=(
                    GENERATED_DIR
                ),
            )
        )


        package_path = (
            Path(package_path)
        )


        if not package_path.exists():

            raise RuntimeError(
                "Brand package was not created."
            )


        return FileResponse(
            path=str(
                package_path
            ),

            filename=(
                package_path.name
            ),

            media_type=(
                "application/zip"
            ),
        )


    except Exception as error:

        print(
            "[PACKAGE] Error:",
            repr(error),
        )


        raise HTTPException(
            status_code=500,
            detail=(
                "Could not create "
                "brand package."
            ),
        )