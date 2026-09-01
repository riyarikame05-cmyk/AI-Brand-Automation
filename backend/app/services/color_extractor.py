from pathlib import Path

import numpy as np
from PIL import Image
from sklearn.cluster import KMeans


def rgb_to_hex(rgb):
    """
    Convert an RGB color into HEX format.
    Example:
    (124, 58, 237) -> #7C3AED
    """

    red = int(rgb[0])
    green = int(rgb[1])
    blue = int(rgb[2])

    return f"#{red:02X}{green:02X}{blue:02X}"


def extract_dominant_colors(
    image_path: Path,
    number_of_colors: int = 3,
):
    """
    Extract dominant colors from an image
    using K-Means clustering.
    """

    image = Image.open(image_path)

    # Remove transparency if the image contains it.
    if image.mode == "RGBA":
        background = Image.new(
            "RGBA",
            image.size,
            (255, 255, 255, 255),
        )

        background.alpha_composite(image)

        image = background.convert("RGB")
    else:
        image = image.convert("RGB")

    # Smaller image = faster clustering.
    image.thumbnail((300, 300))

    pixels = np.array(image)

    # Convert:
    # height x width x RGB
    #
    # into:
    #
    # number_of_pixels x RGB
    pixels = pixels.reshape(-1, 3)

    # Randomly sample pixels if image is large.
    if len(pixels) > 10000:
        random_generator = np.random.default_rng(42)

        indexes = random_generator.choice(
            len(pixels),
            size=10000,
            replace=False,
        )

        pixels = pixels[indexes]

    kmeans = KMeans(
        n_clusters=number_of_colors,
        random_state=42,
        n_init=10,
    )

    labels = kmeans.fit_predict(pixels)

    centers = kmeans.cluster_centers_

    # Count how many pixels belong to each cluster.
    counts = np.bincount(labels)

    # Put most common color first.
    sorted_indexes = np.argsort(counts)[::-1]

    colors = []

    for index in sorted_indexes:
        hex_color = rgb_to_hex(
            centers[index]
        )

        colors.append(hex_color)

    return colors