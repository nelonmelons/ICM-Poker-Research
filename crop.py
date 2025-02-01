#!/usr/bin/env python3
"""Crop images from a directory and store them in a new folder."""

from __future__ import annotations

import os
from typing import Optional

from PIL import Image


def crop_image(
    input_path: str,
    output_path: str,
    left: int,
    top: int,
    width: int,
    height: int,
) -> None:
    """
    Crop an image based on the given bounding box and save it to the output path.

    :param input_path: Path to the input image.
    :param output_path: Path to save the cropped image.
    :param left: Left coordinate of the crop area.
    :param top: Top coordinate of the crop area.
    :param width: Width of the crop area.
    :param height: Height of the crop area.
    """
    with Image.open(input_path) as img:
        right = left + width
        bottom = top + height
        cropped_img = img.crop((left, top, right, bottom))
        cropped_img.save(output_path)


# Hardcoded directories (update these paths as needed):
input_dir = "screenshots"
output_dir = "cropped"

# Ensure output directory exists
os.makedirs(output_dir, exist_ok=True)

# Iterate through all files in the input directory
for filename in os.listdir(input_dir):
    lower_name = filename.lower()
    if lower_name.endswith((".png", ".jpg", ".jpeg")):
        input_path = os.path.join(input_dir, filename)
        output_path = os.path.join(output_dir, filename)

        # Replace or define these crop coordinates
        x1, y1 = 0, 90
        x2, y2 = 1600, 200

        with Image.open(input_path) as img:
            cropped_img = img.crop((x1, y1, x2, y2))
            cropped_img.save(output_path)
