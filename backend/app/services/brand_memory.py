from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from ..models import Asset, BrandKit, Project
from .brand_kit_v2 import derive_extended_palette


BRAND_MEMORY_ASSET_TYPE = "brand_memory"
BRAND_MEMORY_VERSION = 1


def _json_object(value: str | None) -> dict[str, Any]:
    if not value:
        return {}

    try:
        parsed = json.loads(value)
    except (TypeError, ValueError, json.JSONDecodeError):
        return {}

    return parsed if isinstance(parsed, dict) else {}


def _json_list(value: str | None) -> list[Any]:
    if not value:
        return []

    try:
        parsed = json.loads(value)
    except (TypeError, ValueError, json.JSONDecodeError):
        return []

    return parsed if isinstance(parsed, list) else []


def _selected_logo(
    db: Session,
    project_id: Any,
) -> Asset | None:
    return (
        db.query(Asset)
        .filter(
            Asset.project_id == project_id,
            Asset.asset_type == "logo",
            Asset.is_selected.is_(True),
        )
        .order_by(Asset.created_at.desc())
        .first()
    )


def _current_memory_asset(
    db: Session,
    project_id: Any,
) -> Asset | None:
    return (
        db.query(Asset)
        .filter(
            Asset.project_id == project_id,
            Asset.asset_type == BRAND_MEMORY_ASSET_TYPE,
        )
        .order_by(Asset.created_at.desc())
        .first()
    )


def _logo_provenance(
    specification: dict[str, Any],
) -> dict[str, Any]:
    refinement = specification.get("refinement")
    if not isinstance(refinement, dict):
        refinement = {}

    provider = specification.get("provider")
    if not isinstance(provider, dict):
        provider = {}

    return {
        "variant_seed": specification.get("variant_seed"),
        "identity_strategy": specification.get("identity_strategy"),
        "semantic_territory": specification.get("semantic_territory"),
        "identity_construction": specification.get("identity_construction"),
        "catalog_master_id": (
            provider.get("catalog_master_id")
            or specification.get("catalog_master_id")
        ),
        "provider": provider or None,
        "refinement": {
            "root_asset_id": refinement.get("root_asset_id"),
            "parent_asset_id": refinement.get("parent_asset_id"),
            "revision_number": refinement.get("revision_number"),
            "instruction": refinement.get("instruction"),
            "controls": refinement.get("controls"),
        },
    }


def build_brand_memory(
    project: Project,
    brand_kit: BrandKit,
    selected_logo: Asset,
) -> dict[str, Any]:
    specification = _json_object(selected_logo.specification)

    palette = derive_extended_palette(
        primary=brand_kit.primary_color,
        secondary=brand_kit.secondary_color,
        accent=brand_kit.accent_color,
    )

    personality = _json_list(brand_kit.personality)

    now = datetime.now(timezone.utc).isoformat()

    return {
        "version": BRAND_MEMORY_VERSION,
        "project_id": str(project.id),
        "updated_at": now,
        "identity": {
            "business_name": project.business_name,
            "industry": project.industry,
            "description": project.description,
            "style": project.style,
            "slogan": brand_kit.slogan or "",
        },
        "strategy": {
            "personality": personality,
            "tone": brand_kit.tone or "",
            "target_audience": brand_kit.target_audience or "",
            "marketing_message": brand_kit.marketing_message or "",
        },
        "visual_identity": {
            "selected_logo_asset_id": str(selected_logo.id),
            "selected_logo_url": selected_logo.url,
            "palette": palette,
            "typography": {
                "heading": brand_kit.heading_font or "Arial Bold",
                "body": brand_kit.body_font or "Arial",
            },
        },
        "logo": {
            "asset_id": str(selected_logo.id),
            "url": selected_logo.url,
            "specification": specification,
            "provenance": _logo_provenance(specification),
        },
        "usage": {
            "clear_space": (
                "Keep clear space around the identity equal to at least "
                "the cap height of the wordmark."
            ),
            "minimum_size": {
                "digital_width_px": 160,
                "print_width_mm": 35,
            },
            "backgrounds": (
                "Use the primary or black identity on light backgrounds "
                "and the white identity on dark backgrounds."
            ),
            "do_not": [
                "Do not distort or stretch the identity.",
                "Do not change colors outside the approved palette.",
                "Do not add shadows, outlines, or unapproved effects.",
                "Do not rearrange the symbol and wordmark.",
            ],
        },
        "availability": {
            "icon": {
                "available": False,
                "reason": (
                    "Requires an approved separately addressable symbol master."
                ),
            },
            "secondary_horizontal": {
                "available": False,
                "reason": (
                    "Requires an approved alternate lockup or "
                    "master-symbol composition."
                ),
            },
        },
        "campaign_direction": {
            "brand_name": project.business_name,
            "industry": project.industry,
            "personality": personality,
            "tone": brand_kit.tone or "",
            "audience": brand_kit.target_audience or "",
            "message": brand_kit.marketing_message or "",
            "palette": palette,
            "heading_font": brand_kit.heading_font or "Arial Bold",
            "body_font": brand_kit.body_font or "Arial",
            "selected_logo_asset_id": str(selected_logo.id),
        },
    }


def get_brand_memory(
    db: Session,
    project_id: Any,
) -> dict[str, Any] | None:
    asset = _current_memory_asset(db, project_id)

    if asset is None:
        return None

    memory = _json_object(asset.specification)
    if not memory:
        return None

    return memory


def sync_brand_memory(
    db: Session,
    project: Project,
    brand_kit: BrandKit,
) -> tuple[Asset, dict[str, Any]]:
    selected_logo = _selected_logo(db, project.id)

    if selected_logo is None:
        raise ValueError("A selected logo is required to build Brand Memory.")

    memory = build_brand_memory(
        project=project,
        brand_kit=brand_kit,
        selected_logo=selected_logo,
    )

    asset = _current_memory_asset(db, project.id)

    if asset is None:
        asset = Asset(
            project_id=project.id,
            asset_type=BRAND_MEMORY_ASSET_TYPE,
            url=selected_logo.url,
            prompt="Canonical persistent Brand Memory",
            specification=json.dumps(memory, ensure_ascii=False),
            is_selected=True,
        )
        db.add(asset)
    else:
        asset.url = selected_logo.url
        asset.prompt = "Canonical persistent Brand Memory"
        asset.specification = json.dumps(memory, ensure_ascii=False)
        asset.is_selected = True

    db.commit()
    db.refresh(asset)

    return asset, memory
