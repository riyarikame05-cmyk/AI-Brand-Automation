import json
import shutil
from PIL import Image
from pathlib import Path

from app.models import Asset


def persist_hybrid_checkpoints(
    db,
    project,
    job_id,
    generated_dir,
):
    """
    Save completed hybrid checkpoints as selectable BrandAI assets.

    Safe to call repeatedly:
    - Existing assets are not duplicated.
    - Existing selected logos remain unchanged.
    - No image-generation requests are made.
    """

    generated_dir = Path(generated_dir)

    checkpoint_dir = (
        Path(__file__).resolve().parents[2]
        / "generated"
        / "hybrid_checkpoints"
        / str(job_id)
    )

    providers = [
        (1, "local"),
        (2, "huggingface"),
        (2, "pollinations"),
        (2, "local"),
        (3, "local"),
        (3, "pollinations"),
    ]

    saved = []

    for index, provider in providers:
        checkpoint = (
            checkpoint_dir / f"{index}_{provider}.png"
        )

        if not checkpoint.is_file():
            continue

        metadata_path = checkpoint.with_suffix(".json")

        if not metadata_path.is_file():
            print(
                f"[HYBRID] Skipping incomplete "
                f"{provider} checkpoint: metadata missing"
            )
            continue

        try:
            with Image.open(checkpoint) as image:
                image.verify()
        except Exception as exc:
            print(
                f"[HYBRID] Skipping invalid "
                f"{provider} checkpoint: {exc}"
            )
            continue

        filename = (
            f"{project.id}-hybrid-{job_id}-"
            f"{index}-{provider}.png"
        )

        destination = generated_dir / filename

        image_url = (
            f"http://127.0.0.1:8000/generated/{filename}"
        )

        existing = (
            db.query(Asset)
            .filter(
                Asset.project_id == project.id,
                Asset.asset_type == "logo",
                Asset.url == image_url,
            )
            .first()
        )

        if existing:
            saved.append(existing)
            continue

        generated_dir.mkdir(parents=True, exist_ok=True)

        if not destination.exists():
            shutil.copy2(checkpoint, destination)

        metadata = json.loads(
            metadata_path.read_text(encoding="utf-8")
        )

        specification = dict(
            metadata.get("specification") or {}
        )

        specification.update({
            "hybrid_generation": True,
            "generation_provider": provider,
            "hybrid_job_id": str(job_id),
            "concept_number": index,
        })

        asset = Asset(
            project_id=project.id,
            asset_type="logo",
            url=image_url,
            prompt=(
                f"Hybrid logo concept {index} "
                f"generated using {provider}"
            ),
            specification=json.dumps(specification),
            is_selected=False,
        )

        try:
            db.add(asset)
            db.commit()
            db.refresh(asset)
        except Exception:
            db.rollback()
            raise

        saved.append(asset)

    return saved
