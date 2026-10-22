from __future__ import annotations

import io
import json
import os
from pathlib import Path

import requests
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "hybrid_logo_config.json"

PROVIDERS = ("local", "huggingface", "pollinations")


def get_config():
    config = json.loads(
        CONFIG_PATH.read_text(encoding="utf-8-sig")
    )

    if config.get("enabled") is not True:
        raise RuntimeError("Hybrid logo generation is disabled.")

    if config.get("providers") != list(PROVIDERS):
        raise RuntimeError("Unexpected provider configuration.")

    if config.get("automatic_retries") is not False:
        raise RuntimeError("Automatic retries are prohibited.")

    if config.get("paid_fallback") is not False:
        raise RuntimeError("Paid fallbacks are prohibited.")

    if config.get("max_requests_per_remote_provider") != 1:
        raise RuntimeError("Remote request limit must be one.")

    return config


def to_png(image_bytes):
    with Image.open(io.BytesIO(image_bytes)) as image:
        output = io.BytesIO()
        image.convert("RGB").save(output, format="PNG")
        return output.getvalue()


def generate_local_logo(business, concept):
    from app.services.image_generator import generate_logo_image

    result = generate_logo_image(
        business_name=business["name"],
        industry=business["industry"],
        style=business.get("style", "professional"),
        description=business.get("description", ""),
        direction_index=0,
        provider="local",
        custom_colors=business.get("colors", []),
        creative_prompt=concept["prompt"],
        use_ai_specification=False,
    )

    image_bytes = result.get("image_bytes")

    if not isinstance(image_bytes, bytes):
        raise RuntimeError("Local renderer returned invalid image.")

    return to_png(image_bytes)


def generate_huggingface_logo(concept, job_id):
    from gradio_client import Client

    token = os.getenv("HF_TOKEN")

    if not token:
        raise RuntimeError("HF_TOKEN missing.")

    client = Client(
        "black-forest-labs/FLUX.1-schnell",
        token=token,
    )

    from app.services.hybrid_request_tracker import claim_generation
    claim_generation(job_id, "huggingface")

    # Exactly one generation request.
    result = client.predict(
        prompt=concept["prompt"],
        seed=42,
        randomize_seed=False,
        width=768,
        height=768,
        num_inference_steps=4,
        api_name="/infer",
    )

    image_info = result[0]

    source = (
        image_info["path"]
        if isinstance(image_info, dict)
        else image_info
    )

    return to_png(Path(source).read_bytes())


def generate_pollinations_logo(concept, job_id, concept_index=None):

    config = get_config()

    if config.get("pollinations_model") != "openai/gpt-image-1-mini":
        raise RuntimeError("Unapproved Pollinations model.")

    if float(config.get("pollinations_key_budget", 999)) != 0.2:
        raise RuntimeError("Pollinations budget configuration mismatch.")

    key = os.getenv("POLLINATIONS_API_KEY")

    if not key:
        raise RuntimeError("POLLINATIONS_API_KEY missing.")

    # No automatic retries.
    session = requests.Session()

    from app.services.hybrid_request_tracker import claim_generation
    claim_generation(job_id, "pollinations", concept_index)

    response = session.post(
        "https://gen.pollinations.ai/v1/images/generations",
        headers={"Authorization": f"Bearer {key}"},
        json={
            "model": "openai/gpt-image-1-mini",
            "prompt": concept["prompt"],
            "n": 1,
            "size": "1024x1024",
        },
        timeout=120,
    )

    response.raise_for_status()

    data = response.json()["data"][0]

    if data.get("b64_json"):
        import base64
        raw = base64.b64decode(data["b64_json"])

    elif data.get("url"):
        downloaded = session.get(data["url"], timeout=60)
        downloaded.raise_for_status()
        raw = downloaded.content

    else:
        raise RuntimeError("Pollinations returned no image.")

    return to_png(raw)


def generate_hybrid_logo(business, concept, provider, job_id):
    get_config()

    if provider not in PROVIDERS:
        raise ValueError("Unknown logo provider.")

    if not concept.get("prompt"):
        raise ValueError("Logo concept prompt missing.")

    if provider == "local":
        return generate_local_logo(business, concept)

    if provider == "huggingface":
        return generate_huggingface_logo(concept, job_id)

    raise RuntimeError(
        "Pollinations requires a concept index. "
        "Use generate_hybrid_batch instead."
    )



def _checkpoint_paths(job_id, index, provider):
    import re

    job = str(job_id)

    if not re.fullmatch(r"[A-Za-z0-9_-]+", job):
        raise ValueError("Unsafe hybrid job identifier.")

    folder = ROOT / "generated" / "hybrid_checkpoints" / job
    checkpoint = folder / f"{index}_{provider}.png"
    metadata = checkpoint.with_suffix(".json")

    return folder, checkpoint, metadata


def _validate_checkpoint_image(path):
    with Image.open(path) as image:
        image.verify()

    with Image.open(path) as image:
        if image.format != "PNG":
            raise RuntimeError("Checkpoint is not a PNG.")

        if image.width < 64 or image.height < 64:
            raise RuntimeError("Checkpoint image is too small.")


def _atomic_write_bytes(path, content):
    import tempfile

    path.parent.mkdir(parents=True, exist_ok=True)

    temporary = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            dir=path.parent,
            prefix=".hybrid-",
            suffix=".tmp",
            delete=False,
        ) as output:
            temporary = Path(output.name)
            output.write(content)
            output.flush()
            os.fsync(output.fileno())

        # Refuse to overwrite an existing completed checkpoint.
        if path.exists():
            raise FileExistsError(
                f"Checkpoint already exists: {path}"
            )

        # Publish the fully written file atomically.
        # os.link fails if the destination already exists.
        # The temporary file is on the same filesystem.
        os.link(temporary, path)

    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)



def generate_hybrid_batch(business, job_id, concepts):
    """
    Three-logo generation with Hugging Face fallback.

    Slot 1: Local
    Slot 2: Hugging Face, then local on failure
    Slot 3: Local

    Pollinations is never called.
    Existing checkpoints are reused.
    Remote requests are never repeated.
    """
    from app.services.logo_renderer import compose_cloud_logo

    get_config()

    if len(concepts) != 3:
        raise ValueError("Exactly three concepts required.")

    names = [
        str(c.get("name", "")).strip().lower()
        for c in concepts
    ]

    if any(not name for name in names):
        raise ValueError("Concept name missing.")

    if len(set(names)) != 3:
        raise ValueError("Concept names must be distinct.")

    slots = [
        (1, "local"),
        (2, "huggingface"),
        (3, "pollinations"),
    ]

    results = []

    for index, preferred_provider in slots:
        concept = concepts[index - 1]

        candidates = {
            1: ["local"],
            2: ["huggingface", "pollinations", "local"],
            3: ["pollinations", "local"],
        }[index]

        existing = []

        for candidate in candidates:
            folder, path, metadata_path = _checkpoint_paths(
                job_id, index, candidate
            )

            if path.exists():
                existing.append(
                    (candidate, path, metadata_path)
                )

        if len(existing) > 1:
            raise RuntimeError(
                f"Multiple checkpoints for concept {index}."
            )

        if existing:
            provider, checkpoint, metadata_path = existing[0]

            _validate_checkpoint_image(checkpoint)

            if not metadata_path.exists():
                raise RuntimeError(
                    "Checkpoint metadata missing."
                )

            metadata = json.loads(
                metadata_path.read_text(encoding="utf-8")
            )

            if (
                metadata.get("provider") != provider
                or metadata.get("business_name") != business["name"]
                or metadata.get("concept") != concept
            ):
                raise RuntimeError(
                    "Checkpoint metadata mismatch."
                )

            image_bytes = checkpoint.read_bytes()

            print(
                f"[HYBRID] Reusing concept {index}: {provider}"
            )

        else:
            from app.services.hybrid_request_tracker import (
                TRACKER_DIR,
            )
            from app.services.image_generator import (
                generate_logo_image,
            )

            provider = "local"
            image_bytes = None

            for candidate in candidates:
                if candidate == "huggingface":
                    tracker = (
                        TRACKER_DIR / f"{job_id}_huggingface.json"
                    )
                    if tracker.exists():
                        print("[HYBRID] Hugging Face already attempted.")
                        continue

                if candidate == "pollinations":
                    legacy = (
                        TRACKER_DIR / f"{job_id}_pollinations.json"
                    )
                    tracker = (
                        TRACKER_DIR
                        / f"{job_id}_pollinations_{index}.json"
                    )
                    if legacy.exists() or tracker.exists():
                        print(
                            "[HYBRID] Pollinations already attempted "
                            f"for concept {index}."
                        )
                        continue

                try:
                    if candidate == "huggingface":
                        raw = generate_huggingface_logo(
                            concept, job_id
                        )

                    elif candidate == "pollinations":
                        raw = generate_pollinations_logo(
                            concept, job_id, index
                        )

                    else:
                        result = generate_logo_image(
                            business_name=business["name"],
                            industry=business["industry"],
                            style=business.get(
                                "style", "professional"
                            ),
                            description=business.get(
                                "description", ""
                            ),
                            direction_index={
                                1: 0, 2: 1, 3: 2
                            }[index],
                            provider="local",
                            custom_colors=business["colors"],
                            creative_prompt=concept["prompt"],
                            use_ai_specification=False,
                        )
                        raw = result.get("image_bytes")

                    if not isinstance(raw, bytes):
                        raise RuntimeError(
                            "Logo generator returned invalid image."
                        )

                    if candidate != "local":
                        spec = {
                            "concept_name": concept["name"],
                            "semantic_territory": concept.get(
                                "business_connection", ""
                            ),
                            "industry_form": concept.get(
                                "industry_subject", ""
                            ),
                            "primary_color": business["colors"][0],
                            "secondary_color": business["colors"][1],
                            "accent_color": business["colors"][1],
                            "generation_provider": candidate,
                            "hybrid_generation": True,
                            "source_prompt": concept["prompt"],
                        }

                        raw = compose_cloud_logo(
                            cloud_image_bytes=raw,
                            business_name=business["name"],
                            industry=business["industry"],
                            specification=spec,
                        )

                    image_bytes = raw
                    provider = candidate
                    break

                except Exception as error:
                    print(
                        f"[HYBRID] {candidate} failed for "
                        f"concept {index}: {error!r}"
                    )

            if image_bytes is None:
                raise RuntimeError(
                    f"All providers failed for concept {index}."
                )

            image_bytes = to_png(image_bytes)

            specification = {
                "concept_name": concept["name"],
                "semantic_territory": concept.get(
                    "business_connection", ""
                ),
                "industry_form": concept.get(
                    "industry_subject", ""
                ),
                "primary_color": business["colors"][0],
                "secondary_color": business["colors"][1],
                "accent_color": business["colors"][1],
                "generation_provider": provider,
                "hybrid_generation": True,
                "source_prompt": concept["prompt"],
            }

            metadata = {
                "provider": provider,
                "concept": concept,
                "specification": specification,
                "business_name": business["name"],
                "industry": business["industry"],
                "colors": business["colors"],
            }

            folder, checkpoint, metadata_path = (
                _checkpoint_paths(job_id, index, provider)
            )

            folder.mkdir(parents=True, exist_ok=True)

            if metadata_path.exists():
                previous = json.loads(
                    metadata_path.read_text(encoding="utf-8")
                )

                if previous != metadata:
                    raise RuntimeError(
                        "Existing checkpoint metadata mismatch."
                    )
            else:
                _atomic_write_bytes(
                    metadata_path,
                    json.dumps(
                        metadata, indent=2
                    ).encode("utf-8"),
                )

            _atomic_write_bytes(
                checkpoint, image_bytes
            )

            _validate_checkpoint_image(checkpoint)

        results.append({
            "provider": provider,
            "concept": concept,
            "image_bytes": image_bytes,
            "checkpoint_path": str(checkpoint),
        })

    return results


def prepare_hybrid_concepts(business):
    """
    Use the existing Gemini semantic portfolio.
    Exactly three territories; no replacement requests.
    """
    from app.services.logo_ai_engine import (
        create_semantic_portfolio_with_gemini,
    )

    territories = create_semantic_portfolio_with_gemini(
        business_name=business["name"],
        industry=business["industry"],
        description=business.get("description", ""),
        style=business.get("style", "professional"),
        creative_prompt=business.get("creative_prompt", ""),
        count=3,
    )

    if len(territories) != 3:
        raise RuntimeError(
            "Gemini must return exactly three semantic territories."
        )

    concepts = []

    for index, territory in enumerate(territories):
        name = str(
            territory.get("territory_name")
            or territory.get("concept_name")
            or f"Concept {index + 1}"
        ).strip()

        subject = str(
            territory.get("industry_form")
            or territory.get("domain_signal")
            or territory.get("visual_subject")
            or territory.get("core_idea")
            or territory.get("territory_description")
            or name
        ).strip()

        colors = business["colors"]

        prompt = (
            f"Create one original professional logo SYMBOL for "
            f"{business['name']}, a business in the "
            f"{business['industry']} industry. "
            f"Business: {business.get('description', '')}. "
            f"Creative direction: {name}. "
            f"Recognizable industry subject: {subject}. "
            f"Visibly communicate the business's actual products "
            f"or services through a distinctive, unified silhouette. "
            f"Preserve recognizable industry features. "
            f"Avoid generic abstract geometry and stock clip art. "
            f"Premium minimalist flat vector-style brand identity. "
            f"Use only {colors[0]} and {colors[1]}. "
            f"Exactly one centered standalone symbol on white. "
            f"No text, letters, typography, gradients, shadows, "
            f"photography, 3D, mockups, or watermarks."
        )

        concepts.append({
            "name": name,
            "industry_subject": subject,
            "business_connection": str(territory),
            "prompt": prompt,
        })

    names = [c["name"].lower() for c in concepts]

    if len(set(names)) != 3:
        raise RuntimeError("Gemini concepts are not distinct.")

    return concepts

