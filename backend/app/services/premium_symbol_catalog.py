"""Premium symbol catalog loading, validation, and matching."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


CATALOG_DIR = Path(__file__).resolve().parent.parent / "assets" / "premium_symbols"
CATALOG_PATH = CATALOG_DIR / "catalog.json"

REQUIRED_FIELDS = {
    "id",
    "path",
    "license",
    "source",
    "tags",
    "industries",
    "personalities",
    "strategies",
    "complexity",
    "symmetry",
    "small_size_score",
    "family",
    "transformations",
}

ALLOWED_COMPLEXITY = {"low", "medium", "high"}
ALLOWED_SYMMETRY = {"none", "vertical", "horizontal", "radial"}
ALLOWED_FAMILIES = {
    "monogram",
    "negative-space",
    "abstract-geometric",
    "organic-crafted",
    "editorial-luxury",
    "architectural",
    "motion-resonance",
}
ALLOWED_TRANSFORMATIONS = {
    "palette",
    "rotation",
    "reflection",
    "proportion",
    "stroke-weight",
    "negative-space",
    "initials",
}


def load_symbol_catalog() -> dict[str, Any]:
    """Load the premium symbol catalog from disk."""
    with CATALOG_PATH.open("r", encoding="utf-8-sig") as handle:
        catalog = json.load(handle)

    if not isinstance(catalog, dict):
        raise ValueError("Premium symbol catalog must be a JSON object.")

    symbols = catalog.get("symbols")
    if not isinstance(symbols, list):
        raise ValueError("Premium symbol catalog must contain a symbols list.")

    return catalog


def validate_symbol(symbol: dict[str, Any]) -> list[str]:
    """Return validation errors for one catalog entry."""
    errors: list[str] = []

    missing = sorted(REQUIRED_FIELDS - set(symbol))
    if missing:
        errors.append(f"missing fields: {', '.join(missing)}")
        return errors

    symbol_id = str(symbol["id"]).strip()

    if not symbol_id:
        errors.append("id must not be empty")

    relative_path = Path(str(symbol["path"]))

    if relative_path.is_absolute() or ".." in relative_path.parts:
        errors.append("path must stay inside the premium symbol directory")
    else:
        asset_path = CATALOG_DIR / relative_path
        if not asset_path.is_file():
            errors.append(f"SVG file does not exist: {relative_path}")

    if relative_path.suffix.lower() != ".svg":
        errors.append("path must reference an SVG file")

    for field in ("tags", "industries", "personalities", "strategies"):
        value = symbol[field]
        if not isinstance(value, list) or not value:
            errors.append(f"{field} must be a non-empty list")

    if symbol["family"] not in ALLOWED_FAMILIES:
        errors.append(f"unsupported family: {symbol['family']}")

    transformations = symbol["transformations"]
    if not isinstance(transformations, list):
        errors.append("transformations must be a list")
    else:
        unknown = sorted(set(transformations) - ALLOWED_TRANSFORMATIONS)
        if unknown:
            errors.append(
                f"unsupported transformations: {', '.join(unknown)}"
            )

    if symbol["complexity"] not in ALLOWED_COMPLEXITY:
        errors.append("complexity must be low, medium, or high")

    if symbol["symmetry"] not in ALLOWED_SYMMETRY:
        errors.append(
            "symmetry must be none, vertical, horizontal, or radial"
        )

    score = symbol["small_size_score"]
    if (
        isinstance(score, bool)
        or not isinstance(score, (int, float))
        or not 0 <= score <= 1
    ):
        errors.append("small_size_score must be between 0 and 1")

    if not str(symbol["license"]).strip():
        errors.append("license must not be empty")

    if not str(symbol["source"]).strip():
        errors.append("source must not be empty")

    return errors


def validate_catalog() -> list[str]:
    """Validate the complete catalog and return human-readable errors."""
    catalog = load_symbol_catalog()
    errors: list[str] = []
    seen_ids: set[str] = set()

    for index, symbol in enumerate(catalog["symbols"]):
        if not isinstance(symbol, dict):
            errors.append(f"symbol #{index + 1}: entry must be an object")
            continue

        symbol_id = str(symbol.get("id", "")).strip() or f"#{index + 1}"

        if symbol_id in seen_ids:
            errors.append(f"{symbol_id}: duplicate id")
        seen_ids.add(symbol_id)

        for error in validate_symbol(symbol):
            errors.append(f"{symbol_id}: {error}")

    return errors


def find_symbols(
    *,
    industry: str = "",
    personality: str = "",
    strategy: str = "",
    limit: int = 12,
) -> list[dict[str, Any]]:
    """Rank catalog symbols against V5 identity metadata."""
    catalog = load_symbol_catalog()

    industry = industry.strip().lower()
    personality = personality.strip().lower()
    strategy = strategy.strip().lower()

    ranked: list[tuple[float, dict[str, Any]]] = []

    for symbol in catalog["symbols"]:
        industries = {str(v).lower() for v in symbol["industries"]}
        personalities = {str(v).lower() for v in symbol["personalities"]}
        strategies = {str(v).lower() for v in symbol["strategies"]}

        score = float(symbol["small_size_score"])

        if industry and industry in industries:
            score += 4.0
        elif "other" in industries or "all" in industries:
            score += 0.25

        if personality and personality in personalities:
            score += 2.0

        if strategy and strategy in strategies:
            score += 3.0

        ranked.append((score, symbol))

    ranked.sort(key=lambda item: (-item[0], str(item[1]["id"])))
    return [symbol for _, symbol in ranked[: max(0, limit)]]

