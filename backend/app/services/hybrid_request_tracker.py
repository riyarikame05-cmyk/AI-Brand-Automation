import json
import os
import re
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
TRACKER_DIR = ROOT / "generated" / "hybrid_request_tracker"
TRACKER_DIR.mkdir(parents=True, exist_ok=True)


def claim_generation(job_id, provider, concept_index=None):
    if provider not in {"huggingface", "pollinations"}:
        raise ValueError("Only remote providers require claims.")

    safe_job = str(job_id)

    if not re.fullmatch(r"[A-Za-z0-9_-]+", safe_job):
        raise ValueError("Unsafe generation job identifier.")

    if provider == "pollinations":
        if concept_index not in {2, 3}:
            raise ValueError(
                "Pollinations requires concept index 2 or 3."
            )

        budget_path = ROOT / "pollinations_logo_budget.json"

        budget = json.loads(
            budget_path.read_text(encoding="utf-8-sig")
        )

        if budget.get("generation_enabled") is not True:
            raise RuntimeError("Pollinations is disabled.")

        if budget.get("max_generation_requests") != 2:
            raise RuntimeError(
                "Pollinations must be limited to two requests."
            )

        if budget.get("automatic_retries") is not False:
            raise RuntimeError(
                "Automatic Pollinations retries are prohibited."
            )

        # Historical tracker: do not retry a previously attempted
        # job under the new per-concept naming convention.
        legacy = TRACKER_DIR / f"{safe_job}_pollinations.json"

        if legacy.exists():
            raise RuntimeError(
                "Historical Pollinations attempt exists. "
                "Retry blocked."
            )

        path = (
            TRACKER_DIR
            / f"{safe_job}_pollinations_{concept_index}.json"
        )

    else:
        path = TRACKER_DIR / f"{safe_job}_huggingface.json"

    record = {
        "job_id": safe_job,
        "provider": provider,
        "concept_index": concept_index,
        "status": "attempted",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    try:
        with os.fdopen(
            os.open(
                path,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                0o600,
            ),
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(record, file, indent=2)

    except FileExistsError:
        raise RuntimeError(
            "Remote generation already attempted. "
            "Automatic retry blocked."
        )

    return path
