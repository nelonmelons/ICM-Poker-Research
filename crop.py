#!/usr/bin/env python3
"""Crop images from a directory and store them in a new folder."""

from __future__ import annotations

import argparse
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


def main() -> None:
    """
    Parse command-line arguments, then crop images in bulk from an input directory
    and save them into an output directory.
    """
    parser = argparse.ArgumentParser(
        description="Crop images from a directory and store them in a new folder."
    )
    parser.add_argument(
        "--input_dir",
        type=str,
        required=True,
        help="Path to the input directory containing images.",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        required=True,
        help="Path to the output directory to store cropped images.",
    )
    parser.add_argument(
        "--left",
        type=int,
        required=True,
        help="Left coordinate of the crop area.",
    )
    parser.add_argument(
        "--top",
        type=int,
        required=True,
        help="Top coordinate of the crop area.",
    )
    parser.add_argument(
        "--width",
        type=int,
        required=True,
        help="Width of the crop area.",
    )
    parser.add_argument(
        "--height",
        type=int,
        required=True,
        help="Height of the crop area.",
    )

    args: argparse.Namespace = parser.parse_args()

    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)

    # Iterate through all files in the input directory
    for filename in os.listdir(args.input_dir):
        lower_name = filename.lower()
        if lower_name.endswith((".png", ".jpg", ".jpeg")):
            input_path = os.path.join(args.input_dir, filename)
            output_path = os.path.join(args.output_dir, filename)

            crop_image(
                input_path=input_path,
                output_path=output_path,
                left=args.left,
                top=args.top,
                width=args.width,
                height=args.height,
            )


if __name__ == "__main__":
    main()
