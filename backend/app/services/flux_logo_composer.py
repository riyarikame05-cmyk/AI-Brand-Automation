from io import BytesIO

from PIL import Image, ImageDraw, ImageFont


SIZE = 1400
BACKGROUND = "#FFFFFF"


def _get_font(size: int):
    paths = [
        "C:/Windows/Fonts/segoeuib.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]

    for path in paths:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue

    return ImageFont.load_default()


def compose_flux_logo(
    symbol_bytes: bytes,
    business_name: str,
) -> bytes:

    symbol = Image.open(
        BytesIO(symbol_bytes)
    ).convert("RGB")

    symbol.thumbnail(
        (850, 850),
        Image.Resampling.LANCZOS,
    )

    canvas = Image.new(
        "RGB",
        (SIZE, SIZE),
        BACKGROUND,
    )

    # Position FLUX symbol.
    symbol_x = (SIZE - symbol.width) // 2
    symbol_y = 100

    canvas.paste(
        symbol,
        (symbol_x, symbol_y),
    )

    draw = ImageDraw.Draw(canvas)

    name = business_name.strip().upper()

    if len(name) <= 12:
        font_size = 100
    elif len(name) <= 20:
        font_size = 75
    else:
        font_size = 55

    font = _get_font(font_size)

    bbox = draw.textbbox(
        (0, 0),
        name,
        font=font,
    )

    text_width = bbox[2] - bbox[0]

    draw.text(
        (
            (SIZE - text_width) / 2,
            1075,
        ),
        name,
        font=font,
        fill="#111827",
    )

    buffer = BytesIO()

    canvas.save(
        buffer,
        format="PNG",
        optimize=True,
    )

    return buffer.getvalue()
