import subprocess
import uuid
from pathlib import Path


def generate_promotional_video(
    logo_path: Path,
    output_directory: Path,
) -> Path:
    """
    Create a 4-second promotional MP4 from a logo
    using FFmpeg.
    """

    output_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    filename = (
        f"promo-{uuid.uuid4()}.mp4"
    )

    output_path = (
        output_directory / filename
    )

    video_filter = (
        "scale=700:700:"
        "force_original_aspect_ratio=decrease,"
        "pad=1080:1080:"
        "(ow-iw)/2:(oh-ih)/2:"
        "color=0x0f172a,"
        "zoompan="
        "z='min(zoom+0.0015,1.15)':"
        "d=120:"
        "x='iw/2-(iw/zoom/2)':"
        "y='ih/2-(ih/zoom/2)':"
        "s=1080x1080:"
        "fps=30,"
        "fade=t=in:st=0:d=1,"
        "fade=t=out:st=3:d=1"
    )

    command = [
        "ffmpeg",
        "-y",

        "-loop",
        "1",

        "-i",
        str(logo_path),

        "-vf",
        video_filter,

        "-t",
        "4",

        "-c:v",
        "libx264",

        "-pix_fmt",
        "yuv420p",

        "-movflags",
        "+faststart",

        str(output_path),
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"FFmpeg failed: {result.stderr}"
        )

    return output_path