"""Selection layer for approved premium symbol masters."""

from __future__ import annotations

from typing import Any

from .premium_symbol_catalog import find_symbols, validate_catalog


def _industry_key(specification: dict, industry: str) -> str:
    family = str(
        specification.get("industry_family", "")
    ).strip().lower()

    if family:
        return family

    return str(industry or "").strip().lower()


def select_premium_symbol(
    *,
    specification: dict,
    industry: str,
    candidate_index: int = 0,
) -> dict[str, Any] | None:
    """
    Select one approved catalog master for a structured logo specification.

    Returns None when the catalog is empty or has no valid candidate.
    Existing local rendering remains the fallback.
    """
    errors = validate_catalog()

    if errors:
        print(
            "[PREMIUM CATALOG] Invalid catalog; "
            "using renderer fallback."
        )
        return None

    strategy = str(
        specification.get("identity_strategy", "")
    ).strip().lower()

    personality = str(
        specification.get(
            "typography_personality",
            "",
        )
    ).strip().lower()

    matches = find_symbols(
        industry=_industry_key(
            specification,
            industry,
        ),
        personality=personality,
        strategy=strategy,
        limit=12,
    )

    if not matches:
        print(
            "[PREMIUM CATALOG] No approved masters; "
            "using renderer fallback."
        )
        return None

    index = max(0, int(candidate_index)) % len(matches)
    selected = matches[index]

    print(
        "[PREMIUM CATALOG] Selected master: "
        f"{selected['id']}"
    )

    return selected


def attach_symbol_provenance(
    specification: dict,
    symbol: dict[str, Any] | None,
) -> dict:
    """Return a copy with explicit catalog/fallback provenance."""
    result = dict(specification)

    if symbol is None:
        result["symbol_provider"] = {
            "type": "local-renderer-fallback",
            "catalog_master_id": None,
        }
        return result

    result["symbol_provider"] = {
        "type": "premium-catalog",
        "catalog_master_id": symbol["id"],
        "catalog_path": symbol["path"],
        "family": symbol["family"],
        "license": symbol["license"],
        "source": symbol["source"],
        "transformations": list(
            symbol["transformations"]
        ),
        "small_size_score": symbol[
            "small_size_score"
        ],
    }

    return result
