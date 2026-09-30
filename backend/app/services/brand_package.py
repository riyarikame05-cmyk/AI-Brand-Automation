import json
import re
import shutil
import zipfile
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from .brand_kit_v2 import (
    build_brand_kit_assets,
    derive_extended_palette,
)


def safe_filename(value: str) -> str:
    value = value.strip()

    value = re.sub(
        r"[^a-zA-Z0-9_-]+",
        "-",
        value,
    )

    value = value.strip("-")

    return value or "brand"


def draw_wrapped_text(
    pdf,
    text,
    x,
    y,
    max_width,
    font_name="Helvetica",
    font_size=10,
    line_height=15,
):
    """
    Draw basic wrapped text and return the new Y position.
    """

    if not text:
        return y

    pdf.setFont(
        font_name,
        font_size,
    )

    words = str(text).split()

    line = ""

    for word in words:

        candidate = (
            f"{line} {word}".strip()
        )

        width = pdf.stringWidth(
            candidate,
            font_name,
            font_size,
        )

        if width <= max_width:
            line = candidate

        else:

            if line:
                pdf.drawString(
                    x,
                    y,
                    line,
                )

                y -= line_height

            line = word

    if line:

        pdf.drawString(
            x,
            y,
            line,
        )

        y -= line_height

    return y


def create_brand_guide_pdf(
    output_path: Path,
    logo_path: Path,
    project,
    brand_kit,
):
    """
    Create a simple professional brand guidelines PDF.
    """

    pdf = canvas.Canvas(
        str(output_path),
        pagesize=A4,
    )

    page_width, page_height = A4

    margin = 55

    # =====================================================
    # TITLE
    # =====================================================

    pdf.setFillColor(
        colors.HexColor("#111827")
    )

    pdf.setFont(
        "Helvetica-Bold",
        24,
    )

    pdf.drawString(
        margin,
        page_height - 60,
        project.business_name,
    )

    pdf.setFillColor(
        colors.HexColor("#6B7280")
    )

    pdf.setFont(
        "Helvetica",
        11,
    )

    pdf.drawString(
        margin,
        page_height - 80,
        "Brand Identity Guidelines",
    )

    # =====================================================
    # LOGO
    # =====================================================

    y = page_height - 120

    try:

        logo = ImageReader(
            str(logo_path)
        )

        pdf.drawImage(
            logo,
            margin,
            y - 190,
            width=190,
            height=190,
            preserveAspectRatio=True,
            mask="auto",
        )

    except Exception as error:

        print(
            "PDF logo error:",
            repr(error),
        )

    # =====================================================
    # SLOGAN
    # =====================================================

    pdf.setFillColor(
        colors.HexColor("#111827")
    )

    pdf.setFont(
        "Helvetica-Bold",
        12,
    )

    pdf.drawString(
        275,
        y - 15,
        "SLOGAN",
    )

    pdf.setFont(
        "Helvetica-Bold",
        16,
    )

    slogan = (
        brand_kit.slogan
        or "Brand slogan"
    )

    y_text = draw_wrapped_text(
        pdf,
        f'"{slogan}"',
        275,
        y - 42,
        250,
        "Helvetica-Bold",
        14,
        19,
    )

    # =====================================================
    # INDUSTRY / STYLE
    # =====================================================

    pdf.setFont(
        "Helvetica",
        10,
    )

    pdf.setFillColor(
        colors.HexColor("#6B7280")
    )

    pdf.drawString(
        275,
        y_text - 15,
        f"Industry: {project.industry}",
    )

    pdf.drawString(
        275,
        y_text - 33,
        f"Brand style: {project.style}",
    )

    # =====================================================
    # COLOR PALETTE
    # =====================================================

    y = y - 235

    pdf.setFillColor(
        colors.HexColor("#111827")
    )

    pdf.setFont(
        "Helvetica-Bold",
        13,
    )

    pdf.drawString(
        margin,
        y,
        "COLOR PALETTE",
    )

    palette = [
        (
            "Primary",
            brand_kit.primary_color,
        ),
        (
            "Secondary",
            brand_kit.secondary_color,
        ),
        (
            "Accent",
            brand_kit.accent_color,
        ),
    ]

    palette_y = y - 50

    for index, (
        label,
        hex_color,
    ) in enumerate(palette):

        x = (
            margin
            + index * 165
        )

        try:
            fill = colors.HexColor(
                hex_color
            )
        except Exception:
            fill = colors.grey

        pdf.setFillColor(fill)

        pdf.roundRect(
            x,
            palette_y,
            120,
            45,
            5,
            fill=1,
            stroke=0,
        )

        pdf.setFillColor(
            colors.HexColor("#111827")
        )

        pdf.setFont(
            "Helvetica-Bold",
            9,
        )

        pdf.drawString(
            x,
            palette_y - 16,
            label,
        )

        pdf.setFont(
            "Helvetica",
            9,
        )

        pdf.drawString(
            x,
            palette_y - 30,
            hex_color,
        )

    # =====================================================
    # STRATEGY
    # =====================================================

    y = palette_y - 75

    pdf.setFont(
        "Helvetica-Bold",
        13,
    )

    pdf.drawString(
        margin,
        y,
        "BRAND STRATEGY",
    )

    y -= 30

    sections = [
        (
            "Brand Personality",
            brand_kit.personality
            or "",
        ),
        (
            "Target Audience",
            brand_kit.target_audience
            or "",
        ),
        (
            "Tone of Voice",
            brand_kit.tone
            or "",
        ),
        (
            "Marketing Message",
            brand_kit.marketing_message
            or "",
        ),
    ]

    for title, text in sections:

        if y < 100:

            pdf.showPage()

            y = page_height - margin

        pdf.setFillColor(
            colors.HexColor("#111827")
        )

        pdf.setFont(
            "Helvetica-Bold",
            10,
        )

        pdf.drawString(
            margin,
            y,
            title,
        )

        y -= 17

        pdf.setFillColor(
            colors.HexColor("#4B5563")
        )

        y = draw_wrapped_text(
            pdf,
            text,
            margin,
            y,
            page_width - (margin * 2),
            "Helvetica",
            9,
            14,
        )

        y -= 14

    # =====================================================
    # TYPOGRAPHY
    # =====================================================

    if y < 130:

        pdf.showPage()

        y = page_height - margin

    pdf.setFillColor(
        colors.HexColor("#111827")
    )

    pdf.setFont(
        "Helvetica-Bold",
        13,
    )

    pdf.drawString(
        margin,
        y,
        "TYPOGRAPHY",
    )

    y -= 25

    pdf.setFont(
        "Helvetica",
        10,
    )

    pdf.drawString(
        margin,
        y,
        (
            "Heading: "
            f"{brand_kit.heading_font or 'Montserrat'}"
        ),
    )

    y -= 18

    pdf.drawString(
        margin,
        y,
        (
            "Body: "
            f"{brand_kit.body_font or 'Inter'}"
        ),
    )

    # =====================================================
    # FOOTER
    # =====================================================

    pdf.setFillColor(
        colors.HexColor("#9CA3AF")
    )

    pdf.setFont(
        "Helvetica",
        8,
    )

    pdf.drawString(
        margin,
        30,
        "Generated by BrandAI",
    )

    pdf.save()


def create_brand_package(
    project,
    brand_kit,
    logo_path: Path,
    video_path: Path | None,
    output_directory: Path,
) -> Path:
    """
    Build Brand Kit V2.

    The package preserves the exact selected identity and creates only
    deterministic production variants. It never invents a different symbol.
    """

    safe_name = safe_filename(
        project.business_name
    )

    work_directory = (
        output_directory
        / f"package-{project.id}"
    )

    if work_directory.exists():
        shutil.rmtree(work_directory)

    work_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    logos_directory = (
        work_directory
        / "logos"
    )

    logo_assets = build_brand_kit_assets(
        logo_path=logo_path,
        output_directory=logos_directory,
    )

    if (
        video_path
        and video_path.exists()
    ):
        media_directory = (
            work_directory
            / "media"
        )
        media_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        shutil.copy2(
            video_path,
            media_directory
            / "promotional-video.mp4",
        )

    try:
        personality = (
            json.loads(
                brand_kit.personality
            )
            if brand_kit.personality
            else []
        )
    except Exception:
        personality = (
            brand_kit.personality
            or ""
        )

    palette = derive_extended_palette(
        brand_kit.primary_color,
        brand_kit.secondary_color,
        brand_kit.accent_color,
    )

    brand_data = {
        "version": 2,
        "business_name": project.business_name,
        "description": project.description,
        "industry": project.industry,
        "style": project.style,
        "slogan": brand_kit.slogan,
        "personality": personality,
        "target_audience": brand_kit.target_audience,
        "tone": brand_kit.tone,
        "marketing_message": brand_kit.marketing_message,
        "typography": {
            "heading": (
                brand_kit.heading_font
                or "Montserrat"
            ),
            "body": (
                brand_kit.body_font
                or "Inter"
            ),
        },
        "colors": palette,
        "logo_system": {
            "primary": "logos/primary.png",
            "primary_transparent": (
                "logos/primary-transparent.png"
            ),
            "black": "logos/black.png",
            "white": "logos/white.png",
            "on_light": "logos/on-light.png",
            "on_dark": "logos/on-dark.png",
            "icon": None,
            "secondary_horizontal": None,
        },
        "usage": {
            "clear_space": (
                "Keep clear space around the identity "
                "equal to at least the cap height of the wordmark."
            ),
            "minimum_size": {
                "digital_width_px": 160,
                "print_width_mm": 35,
            },
            "backgrounds": (
                "Use the primary or black identity on light "
                "backgrounds and the white identity on dark "
                "backgrounds."
            ),
            "do_not": [
                "Do not distort or stretch the identity.",
                "Do not change colors outside the approved palette.",
                "Do not add shadows, outlines, or unapproved effects.",
                "Do not rearrange the symbol and wordmark.",
            ],
        },
        "availability": {
            "icon": (
                "Requires an approved separately addressable "
                "symbol master."
            ),
            "secondary_horizontal": (
                "Requires an approved alternate lockup or "
                "master-symbol composition."
            ),
        },
    }

    json_path = (
        work_directory
        / "brand-data.json"
    )

    json_path.write_text(
        json.dumps(
            brand_data,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    pdf_path = (
        work_directory
        / "brand-guide.pdf"
    )

    create_brand_guide_pdf(
        output_path=pdf_path,
        logo_path=logo_assets["primary"],
        project=project,
        brand_kit=brand_kit,
    )

    zip_path = (
        output_directory
        / f"{safe_name}-Brand-Package.zip"
    )

    if zip_path.exists():
        zip_path.unlink()

    with zipfile.ZipFile(
        zip_path,
        "w",
        zipfile.ZIP_DEFLATED,
    ) as zip_file:
        for file_path in sorted(
            work_directory.rglob("*")
        ):
            if not file_path.is_file():
                continue

            zip_file.write(
                file_path,
                arcname=file_path.relative_to(
                    work_directory
                ).as_posix(),
            )

    shutil.rmtree(work_directory)

    return zip_path
