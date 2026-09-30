"""Validation and promotion tooling for premium SVG master artwork."""

from __future__ import annotations

import argparse
import json
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from app.services.premium_symbol_catalog import (
    ALLOWED_COMPLEXITY,
    ALLOWED_FAMILIES,
    ALLOWED_SYMMETRY,
    ALLOWED_TRANSFORMATIONS,
    CATALOG_PATH,
    load_symbol_catalog,
    validate_catalog,
)


ROOT = CATALOG_PATH.parent
INCOMING = ROOT / "incoming"
APPROVED = ROOT / "approved"

REQUIRED_METADATA = {
    "id",
    "file",
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

DRAWABLE_TAGS = {
    "path",
    "rect",
    "circle",
    "ellipse",
    "polygon",
    "polyline",
    "line",
}

FORBIDDEN_TAGS = {
    "script",
    "image",
    "foreignObject",
    "iframe",
    "object",
    "embed",
}


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def load_metadata(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8-sig") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("metadata must be a JSON object")
    return data


def validate_metadata(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    missing = sorted(REQUIRED_METADATA - set(data))
    if missing:
        return [f"missing metadata fields: {', '.join(missing)}"]

    if not str(data["id"]).strip():
        errors.append("id must not be empty")

    file_name = str(data["file"]).strip()
    if not file_name or Path(file_name).name != file_name:
        errors.append("file must be a plain SVG filename")
    elif Path(file_name).suffix.lower() != ".svg":
        errors.append("file must end in .svg")

    for field in ("license", "source"):
        if not str(data[field]).strip():
            errors.append(f"{field} must not be empty")

    for field in ("tags", "industries", "personalities", "strategies"):
        value = data[field]
        if not isinstance(value, list) or not value:
            errors.append(f"{field} must be a non-empty list")

    if data["family"] not in ALLOWED_FAMILIES:
        errors.append(f"unsupported family: {data['family']}")

    if data["complexity"] not in ALLOWED_COMPLEXITY:
        errors.append(f"unsupported complexity: {data['complexity']}")

    if data["symmetry"] not in ALLOWED_SYMMETRY:
        errors.append(f"unsupported symmetry: {data['symmetry']}")

    transformations = data["transformations"]
    if not isinstance(transformations, list):
        errors.append("transformations must be a list")
    else:
        unknown = sorted(set(transformations) - ALLOWED_TRANSFORMATIONS)
        if unknown:
            errors.append(
                f"unsupported transformations: {', '.join(unknown)}"
            )

    score = data["small_size_score"]
    if (
        isinstance(score, bool)
        or not isinstance(score, (int, float))
        or not 0 <= score <= 1
    ):
        errors.append("small_size_score must be between 0 and 1")

    return errors


def validate_svg(path: Path) -> list[str]:
    errors: list[str] = []

    if not path.is_file():
        return [f"SVG does not exist: {path.name}"]

    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        return [f"invalid SVG XML: {exc}"]

    if local_name(root.tag) != "svg":
        errors.append("root element must be svg")

    view_box = root.attrib.get("viewBox", "").strip()
    if not view_box:
        errors.append("SVG must define a viewBox")
    else:
        parts = view_box.replace(",", " ").split()
        if len(parts) != 4:
            errors.append("viewBox must contain four numbers")
        else:
            try:
                numbers = [float(value) for value in parts]
                if numbers[2] <= 0 or numbers[3] <= 0:
                    errors.append("viewBox width and height must be positive")
            except ValueError:
                errors.append("viewBox values must be numeric")

    drawable_count = 0

    for element in root.iter():
        tag = local_name(element.tag)

        if tag in FORBIDDEN_TAGS:
            errors.append(f"forbidden SVG element: {tag}")

        if tag in DRAWABLE_TAGS:
            drawable_count += 1

        for key, value in element.attrib.items():
            key_name = local_name(key).lower()
            value_lower = str(value).strip().lower()

            if key_name.startswith("on"):
                errors.append(f"event attribute is forbidden: {key_name}")

            if key_name == "href":
                if (
                    value_lower.startswith("http:")
                    or value_lower.startswith("https:")
                    or value_lower.startswith("//")
                    or value_lower.startswith("data:")
                ):
                    errors.append("external/data href is forbidden")

    if drawable_count == 0:
        errors.append("SVG has no drawable geometry")

    if drawable_count > 40:
        errors.append(
            f"SVG is too complex for a master symbol: {drawable_count} shapes"
        )

    return sorted(set(errors))


def validate_incoming(metadata_path: Path) -> tuple[dict[str, Any], list[str]]:
    try:
        data = load_metadata(metadata_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return {}, [str(exc)]

    errors = validate_metadata(data)

    file_name = str(data.get("file", "")).strip()
    svg_path = INCOMING / file_name if file_name else INCOMING / "__missing__.svg"
    errors.extend(validate_svg(svg_path))

    catalog = load_symbol_catalog()
    symbol_id = str(data.get("id", "")).strip()
    existing_ids = {str(item.get("id", "")).strip() for item in catalog["symbols"]}

    if symbol_id and symbol_id in existing_ids:
        errors.append(f"catalog already contains id: {symbol_id}")

    return data, sorted(set(errors))


def promote(metadata_path: Path) -> None:
    data, errors = validate_incoming(metadata_path)

    if errors:
        print("REJECTED")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)

    APPROVED.mkdir(parents=True, exist_ok=True)

    source_svg = INCOMING / data["file"]
    destination_svg = APPROVED / data["file"]

    if destination_svg.exists():
        print(f"REJECTED\n- approved file already exists: {data['file']}")
        raise SystemExit(1)

    entry = {
        "id": data["id"],
        "path": f"approved/{data['file']}",
        "license": data["license"],
        "source": data["source"],
        "tags": data["tags"],
        "industries": data["industries"],
        "personalities": data["personalities"],
        "strategies": data["strategies"],
        "complexity": data["complexity"],
        "symmetry": data["symmetry"],
        "small_size_score": data["small_size_score"],
        "family": data["family"],
        "transformations": data["transformations"],
    }

    catalog = load_symbol_catalog()
    updated = dict(catalog)
    updated["symbols"] = [*catalog["symbols"], entry]

    shutil.copy2(source_svg, destination_svg)

    try:
        with CATALOG_PATH.open("w", encoding="utf-8") as handle:
            json.dump(updated, handle, indent=2, ensure_ascii=False)
            handle.write("\n")

        catalog_errors = validate_catalog()
        if catalog_errors:
            raise ValueError("; ".join(catalog_errors))
    except Exception:
        destination_svg.unlink(missing_ok=True)
        raise

    print(f"PROMOTED: {data['id']}")
    print(f"ASSET: approved/{data['file']}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("metadata", help="metadata JSON filename in incoming/")
    parser.add_argument(
        "--promote",
        action="store_true",
        help="copy the approved SVG and register it in catalog.json",
    )
    args = parser.parse_args()

    metadata_path = INCOMING / Path(args.metadata).name

    if args.promote:
        promote(metadata_path)
        return

    _, errors = validate_incoming(metadata_path)

    if errors:
        print("REJECTED")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)

    print("VALID")
    print("Automated checks passed. Visual approval is still required.")


if __name__ == "__main__":
    main()
