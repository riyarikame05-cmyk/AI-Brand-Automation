from __future__ import annotations

from pathlib import Path
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Asset, Project
from app.services.logo_variations import generate_logo_variations


app = FastAPI(
    title="BrandAI Extensions API",
    description="Isolated local tools for BrandAI Studio.",
    version="1.0.0",
)


# ======================================================
# CORS
# ======================================================

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


# ======================================================
# GENERATED FILES
# ======================================================

BACKEND_DIR = Path(__file__).resolve().parents[1]
GENERATED_DIR = BACKEND_DIR / "generated"
GENERATED_DIR.mkdir(parents=True, exist_ok=True)

app.mount(
    "/generated",
    StaticFiles(directory=str(GENERATED_DIR)),
    name="generated",
)


# ======================================================
# HELPERS
# ======================================================

def _resolve_logo_path(url: str) -> Path:
    """
    Convert an existing /generated/... asset URL into its
    corresponding local backend/generated file path.
    """

    filename = Path(url).name

    if not filename:
        raise HTTPException(
            status_code=400,
            detail="Selected logo has no valid file path.",
        )

    path = GENERATED_DIR / filename

    if not path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Selected logo file not found: {filename}",
        )

    return path


def _get_project(
    project_id: UUID,
    db: Session,
) -> Project:
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

    return project


def _get_selected_logo(
    project_id: UUID,
    db: Session,
) -> Asset:
    logo = (
        db.query(Asset)
        .filter(
            Asset.project_id == project_id,
            Asset.asset_type == "logo",
            Asset.is_selected.is_(True),
        )
        .first()
    )

    if logo is None:
        raise HTTPException(
            status_code=400,
            detail="Select a logo before generating variations.",
        )

    return logo


# ======================================================
# HEALTH
# ======================================================

@app.get("/")
def root():
    return {
        "service": "BrandAI Extensions API",
        "status": "ready",
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "features": [
            "logo_variations",
        ],
    }


# ======================================================
# LOGO VARIATIONS
# ======================================================

@app.post("/projects/{project_id}/logo-variations")
def create_logo_variations(
    project_id: UUID,
    db: Session = Depends(get_db),
):
    project = _get_project(
        project_id,
        db,
    )

    logo = _get_selected_logo(
        project_id,
        db,
    )

    source_path = _resolve_logo_path(
        logo.url
    )

    try:
        variations = generate_logo_variations(
            source_path=source_path,
            project_id=str(project_id),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Could not generate logo variations: {exc}",
        ) from exc

    # Convert relative generated URLs into URLs served by this
    # isolated extension API.
    for variation in variations:
        variation["url"] = (
            f"http://127.0.0.1:8001"
            f"{variation['url']}"
        )

    return {
        "project_id": str(project_id),
        "business_name": project.business_name,
        "master_logo": {
            "id": str(logo.id),
            "url": logo.url,
        },
        "variations": variations,
        "count": len(variations),
    }