from pathlib import Path

path = Path("app/main.py")
text = path.read_text(encoding="utf-8")

start_marker = """# =========================================================
# HOME
# =========================================================
def clean_extracted_palette("""
end_marker = """# =========================================================
# HOME
# =========================================================

@app.get("/")"""

if start_marker not in text:
    raise SystemExit("START MARKER NOT FOUND - file not changed")

if end_marker not in text:
    raise SystemExit("END MARKER NOT FOUND - file not changed")

replacement = '''# =========================================================
# CREATE LOGO CONCEPTS
# =========================================================

def clean_extracted_palette(
    palette: dict,
) -> dict:
    """
    Remove near-white background colors from an extracted
    logo palette.
    """

    fallback_colors = [
        "#111827",
        "#6366F1",
        "#8B5CF6",
    ]

    keys = [
        "primary_color",
        "secondary_color",
        "accent_color",
    ]

    def is_near_white(value) -> bool:
        if not isinstance(value, str):
            return True

        value = value.strip().lstrip("#")

        if len(value) != 6:
            return True

        try:
            red = int(value[0:2], 16)
            green = int(value[2:4], 16)
            blue = int(value[4:6], 16)
        except ValueError:
            return True

        return (
            red >= 240
            and green >= 240
            and blue >= 240
        )

    cleaned = {}

    for index, key in enumerate(keys):
        color = palette.get(key)

        if not color or is_near_white(color):
            color = fallback_colors[index]

        cleaned[key] = color

    return cleaned


def create_logo_concepts(
    project: Project,
    db: Session,
    count: int = 3,
):
    """
    Generate logo concepts and commit each completed concept
    independently so SQLite does not retain a writer lock
    while the next AI generation is running.
    """

    concepts = []

    existing_logo_count = (
        db.query(Asset)
        .filter(
            Asset.project_id == project.id,
            Asset.asset_type == "logo",
        )
        .count()
    )

    project_id = project.id
    business_name = project.business_name
    industry = project.industry
    style = project.style
    description = project.description

    print("")
    print("========================================")
    print("[LOGO] STARTING LOGO BATCH")
    print(f"[LOGO] Project: {project_id}")
    print(f"[LOGO] Business: {business_name}")
    print(f"[LOGO] Existing concepts: {existing_logo_count}")
    print(f"[LOGO] New concepts requested: {count}")
    print("========================================")

    try:
        for number in range(count):
            absolute_index = (
                existing_logo_count
                + number
            )

            direction_index = (
                absolute_index % 6
            )

            concept_number = (
                absolute_index + 1
            )

            print("")
            print("----------------------------------------")
            print(
                f"[LOGO] Generating concept "
                f"{concept_number}"
            )
            print(
                f"[LOGO] Creative direction: "
                f"{direction_index}"
            )
            print("----------------------------------------")

            # Keep local rendering enabled while validating
            # SQLite persistence. Hybrid auto routing is the
            # next controlled change.
            image_bytes = generate_logo_image(
                business_name=business_name,
                industry=industry,
                style=style,
                description=description,
                direction_index=direction_index,
                provider="local",
            )

            if not isinstance(
                image_bytes,
                (bytes, bytearray),
            ):
                raise RuntimeError(
                    "Logo generator returned invalid image data."
                )

            if len(image_bytes) < 1000:
                raise RuntimeError(
                    "Generated logo is too small or invalid."
                )

            filename = (
                f"{project_id}-"
                f"logo-{concept_number}-"
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

            try:
                palette = extract_palette(
                    file_path
                )

                palette = clean_extracted_palette(
                    palette
                )

            except Exception as error:
                print(
                    "[COLOR] Extraction failed:",
                    repr(error),
                )

                palette = {
                    "primary_color": "#111827",
                    "secondary_color": "#6366F1",
                    "accent_color": "#8B5CF6",
                }

            try:
                asset = Asset(
                    project_id=project_id,
                    asset_type="logo",
                    url=image_url,
                    prompt=(
                        f"Logo concept {concept_number} "
                        f"for {business_name} "
                        f"(direction {direction_index})"
                    ),
                    is_selected=False,
                )

                db.add(asset)

                # Commit immediately to release SQLite's
                # writer lock before the next AI operation.
                db.commit()
                db.refresh(asset)

            except Exception:
                db.rollback()

                try:
                    if file_path.exists():
                        file_path.unlink()
                except OSError:
                    pass

                raise

            concepts.append(
                {
                    "asset": asset,
                    "palette": palette,
                }
            )

            print(
                f"[LOGO] Concept "
                f"{concept_number} complete."
            )

        print("")
        print("========================================")
        print(
            f"[LOGO] Generated "
            f"{len(concepts)} concepts successfully."
        )
        print("========================================")

        return concepts

    except Exception as error:
        db.rollback()

        print(
            "[LOGO] Batch failed:",
            repr(error),
        )

        raise


# =========================================================
# HOME
# =========================================================

@app.get("/")'''

before, remainder = text.split(start_marker, 1)
_, after = remainder.split(end_marker, 1)

path.write_text(
    before + replacement + after,
    encoding="utf-8",
)

print("LOGO SECTION REPAIRED")
