import json
import uuid
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .database import get_db
from .models import Asset, BrandKit, Project
from .services.brand_intelligence import generate_brand_intelligence
from .services.color_extractor import extract_dominant_colors
from .services.image_generator import generate_logo_image
from .services.video_generator import generate_promotional_video


# =========================================================
# APPLICATION
# =========================================================

app = FastAPI(
    title="AI Brand Automation API",
    description="Local AI-powered brand automation system",
    version="4.0.0",
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


# =========================================================
# SERIALIZATION HELPERS
# =========================================================

def project_to_dict(project: Project):

    return {
        "id": str(project.id),

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


def asset_to_dict(asset: Asset):

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
# FILE / COLOR HELPERS
# =========================================================

def get_local_path(
    asset: Asset,
):

    if "/generated/" not in asset.url:
        return None

    filename = (
        asset.url
        .split("/generated/")[-1]
    )

    return (
        GENERATED_DIR / filename
    )


def extract_palette(
    file_path: Path,
):

    colors = (
        extract_dominant_colors(
            file_path,
            number_of_colors=3,
        )
    )


    if len(colors) < 3:

        raise ValueError(
            "Could not extract 3 colors."
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


    for number in range(count):

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


        filename = (
            f"{project.id}-"
            f"{uuid.uuid4()}.png"
        )


        file_path = (
            GENERATED_DIR
            / filename
        )


        file_path.write_bytes(
            image_bytes
        )


        image_url = (
            "http://127.0.0.1:8000/"
            f"generated/{filename}"
        )


        asset = Asset(
            project_id=(
                project.id
            ),

            asset_type="logo",

            url=image_url,

            prompt=(
                f"Logo concept "
                f"{number + 1} for "
                f"{project.business_name}"
            ),

            is_selected=False,
        )


        db.add(asset)
        db.flush()


        palette = (
            extract_palette(
                file_path
            )
        )


        concepts.append({
            "asset":
            asset,

            "palette":
            palette,
        })


    return concepts


# =========================================================
# 1. HOME
# =========================================================

@app.get("/")
def home():

    return {
        "message":
        "AI Brand Automation API is running"
    }


# =========================================================
# 2. HEALTH
# =========================================================

@app.get("/health")
def health():

    return {
        "status":
        "ok"
    }


# =========================================================
# 3. CREATE COMPLETE BRAND
# =========================================================

@app.post("/brand")
def create_brand(
    brand: BrandRequest,
    db: Session = Depends(get_db),
):

    try:

        # -----------------------------------------
        # CREATE PROJECT
        # -----------------------------------------

        project = Project(
            business_name=(
                brand.business_name.strip()
            ),

            description=(
                brand.description.strip()
            ),

            industry=(
                brand.industry.strip()
            ),

            style=(
                brand.style.strip()
            ),
        )


        db.add(project)
        db.flush()


        # -----------------------------------------
        # LOCAL AI BRAND INTELLIGENCE
        # -----------------------------------------

        try:

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


        except Exception as error:

            print(
                "Ollama generation error:",
                repr(error),
            )


            # System still works if Ollama
            # temporarily isn't available.

            intelligence = {
                "slogan":
                "Built For What Comes Next",

                "personality": [
                    "Professional",
                    "Modern",
                    "Reliable",
                ],

                "tone":
                "Clear, confident and professional",

                "target_audience":
                "Customers seeking quality and reliability",

                "marketing_message":
                (
                    "A modern brand built around "
                    "quality, trust and customer value."
                ),

                "typography": {
                    "heading":
                    "Montserrat",

                    "body":
                    "Inter",
                },
            }


        # -----------------------------------------
        # CREATE INITIAL BRAND KIT
        # -----------------------------------------

        typography = (
            intelligence.get(
                "typography",
                {},
            )
        )


        personality = (
            intelligence.get(
                "personality",
                [],
            )
        )


        brand_kit = BrandKit(
            project_id=(
                project.id
            ),

            # Temporary colours.
            # Replaced when logo is selected.
            primary_color="#111827",
            secondary_color="#6366F1",
            accent_color="#8B5CF6",

            slogan=(
                intelligence.get(
                    "slogan",
                    "",
                )
            ),

            personality=(
                json.dumps(
                    personality
                )
            ),

            tone=(
                intelligence.get(
                    "tone",
                    "",
                )
            ),

            target_audience=(
                intelligence.get(
                    "target_audience",
                    "",
                )
            ),

            marketing_message=(
                intelligence.get(
                    "marketing_message",
                    "",
                )
            ),

            heading_font=(
                typography.get(
                    "heading",
                    "Montserrat",
                )
            ),

            body_font=(
                typography.get(
                    "body",
                    "Inter",
                )
            ),
        )


        db.add(brand_kit)
        db.flush()


        # -----------------------------------------
        # AUTOMATICALLY GENERATE 3 LOGOS
        # -----------------------------------------

        concepts = (
            create_logo_concepts(
                project=project,
                db=db,
                count=3,
            )
        )


        # -----------------------------------------
        # SAVE EVERYTHING
        # -----------------------------------------

        db.commit()

        db.refresh(project)
        db.refresh(brand_kit)


        for concept in concepts:

            db.refresh(
                concept["asset"]
            )


        return {
            "message":
            "Complete brand generated",

            "project":
            project_to_dict(
                project
            ),

            "brand_kit":
            brand_kit_to_dict(
                brand_kit
            ),

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
            "Create brand error:",
            repr(error),
        )


        raise HTTPException(
            status_code=500,
            detail=(
                "Could not generate brand."
            ),
        )


# =========================================================
# 4. PROJECT LIST
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
# 5. GET PROJECT
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
            detail="Project not found",
        )


    return {
        "project":
        project_to_dict(
            project
        )
    }


# =========================================================
# 6. GENERATE 3 MORE LOGOS
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
            detail="Project not found",
        )


    try:

        concepts = (
            create_logo_concepts(
                project=project,
                db=db,
                count=3,
            )
        )


        db.commit()


        for concept in concepts:

            db.refresh(
                concept["asset"]
            )


        return {
            "message":
            "3 new logo concepts generated",

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
            "Logo generation error:",
            repr(error),
        )


        raise HTTPException(
            status_code=500,
            detail=(
                "Logo generation failed."
            ),
        )


# =========================================================
# 7. SELECT LOGO + COLORS + VIDEO
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
            detail="Project not found",
        )


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
            detail="Logo not found",
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

        # -----------------------------------------
        # SELECT LOGO
        # -----------------------------------------

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


        # -----------------------------------------
        # UPDATE FINAL COLORS
        # -----------------------------------------

        palette = (
            extract_palette(
                logo_path
            )
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

            brand_kit = BrandKit(
                project_id=
                project.id,

                primary_color=
                palette[
                    "primary_color"
                ],

                secondary_color=
                palette[
                    "secondary_color"
                ],

                accent_color=
                palette[
                    "accent_color"
                ],
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


        # -----------------------------------------
        # CREATE VIDEO
        # -----------------------------------------

        video_path = (
            generate_promotional_video(
                logo_path=logo_path,

                output_directory=(
                    GENERATED_DIR
                ),
            )
        )


        video_url = (
            "http://127.0.0.1:8000/"
            f"generated/{video_path.name}"
        )


        video = Asset(
            project_id=(
                project.id
            ),

            asset_type="video",

            url=video_url,

            prompt=(
                "Automatic promotional "
                "video from selected logo"
            ),

            is_selected=False,
        )


        db.add(video)


        db.commit()


        db.refresh(logo)
        db.refresh(brand_kit)
        db.refresh(video)


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
            "Select logo error:",
            repr(error),
        )


        raise HTTPException(
            status_code=500,
            detail=(
                "Could not finalize brand."
            ),
        )


# =========================================================
# 8. GET ASSETS
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
            detail="Project not found",
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

                except Exception:

                    data["palette"] = None


        result.append(
            data
        )


    return {
        "assets":
        result
    }


# =========================================================
# 9. GET BRAND KIT + AI STRATEGY
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
            detail="Project not found",
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
            "brand_kit": None
        }


    return {
        "brand_kit":
        brand_kit_to_dict(
            brand_kit
        )
    }