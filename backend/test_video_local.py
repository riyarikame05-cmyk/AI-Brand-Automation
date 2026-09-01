import subprocess
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parent

GENERATED_DIR = BACKEND_DIR / "generated"


# Find generated PNG images
images = list(
    GENERATED_DIR.glob("*.png")
)


if not images:
    raise ValueError(
        "No PNG logos found in backend/generated"
    )


# Use most recently generated logo
latest_logo = max(
    images,
    key=lambda image: image.stat().st_mtime,
)


output_video = (
    GENERATED_DIR / "test-promo-video.mp4"
)


print("Using logo:")
print(latest_logo)

print("\nGenerating promotional video...")


filter_complex = (
    "scale=700:700:force_original_aspect_ratio=decrease,"
    "pad=1080:1080:(ow-iw)/2:(oh-ih)/2:color=0x0f172a,"
    "zoompan="
    "z='min(zoom+0.0015,1.15)':"
    "d=120:"
    "x='iw/2-(iw/zoom/2)':"
    "y='ih/2-(ih/zoom/2)':"
    "s=1080x1080:fps=30,"
    "fade=t=in:st=0:d=1,"
    "fade=t=out:st=3:d=1"
)


command = [
    "ffmpeg",
    "-y",

    "-loop",
    "1",

    "-i",
    str(latest_logo),

    "-vf",
    filter_complex,

    "-t",
    "4",

    "-c:v",
    "libx264",

    "-pix_fmt",
    "yuv420p",

    "-movflags",
    "+faststart",

    str(output_video),
]


result = subprocess.run(
    command,
    capture_output=True,
    text=True,
)


if result.returncode != 0:

    print("\nVideo generation failed.")

    print(result.stderr)

    raise SystemExit(1)


print("\nVideo generated successfully!")

print("Saved to:")

print(output_video)