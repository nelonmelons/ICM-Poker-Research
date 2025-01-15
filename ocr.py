#!/usr/bin/env python3
"""Parse integer values from a folder of cropped images via OCR and save to a CSV."""

from __future__ import annotations

import argparse
import csv
import os
import re
from typing import List

from PIL import Image
import pytesseract


def extract_numbers_from_image(image_path: str) -> List[int]:
    """
    Extract integers found in the OCR text of an image.

    :param image_path: The path to the image file.
    :return: A list of integers extracted from the image.
    """
    with Image.open(image_path) as img:
        text = pytesseract.image_to_string(img)
    # Find all sequences of digits in the text
    matches = re.findall(r"\d+", text)
    return [int(m) for m in matches]


def main() -> None:
    """
    Parse OCR values from a directory of images and store them in a CSV.
    """
    parser = argparse.ArgumentParser(
        description="Parse integer values from a folder of images (via OCR) and save them into a CSV."
    )
    parser.add_argument(
        "--input_dir",
        type=str,
        required=True,
        help="Path to the directory containing cropped images.",
    )
    parser.add_argument(
        "--output_csv",
        type=str,
        required=True,
        help="Path to the output CSV file to store results.",
    )
    args: argparse.Namespace = parser.parse_args()

    # Create output directory if it doesn't exist (for the CSV file's parent dir)
    os.makedirs(os.path.dirname(os.path.abspath(args.output_csv)), exist_ok=True)

    # Gather images
    image_files = [
        f
        for f in os.listdir(args.input_dir)
        if f.lower().endswith((".png", ".jpg", ".jpeg"))
    ]

    with open(args.output_csv, mode="w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["filename", "numbers"])

        for image_name in image_files:
            image_path = os.path.join(args.input_dir, image_name)
            numbers = extract_numbers_from_image(image_path)
            # Store the numbers as a comma-separated string, or leave them as a list
            writer.writerow([image_name, ", ".join(map(str, numbers))])


if __name__ == "__main__":
    main()
