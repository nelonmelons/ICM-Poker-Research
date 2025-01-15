#!/usr/bin/env python3
"""
Scrape/clean a CSV file of poker chip values and names using the OpenAI API.

Example usage:
    python parse_chips_openai.py \
        --input_csv data/parsed_chips.csv \
        --output_txt data/openai_summary.txt
"""

from __future__ import annotations

import argparse
import csv
import os
from typing import List

import openai


def load_data(input_csv: str) -> List[dict[str, str]]:
    """
    Load CSV data where each row contains fields like:
    filename, player_name, chip_count
    (Adjust column names based on your actual CSV structure.)

    :param input_csv: Path to the input CSV file.
    :return: List of rows as dictionaries.
    """
    data: List[dict[str, str]] = []
    with open(input_csv, mode="r", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            data.append(dict(row))
    return data


def clean_data(data: List[dict[str, str]]) -> List[dict[str, str]]:
    """
    Remove rows with invalid or missing chip counts (NaN, empty, etc.).
    Also convert chip_count to an integer if possible.

    :param data: List of rows (dictionaries).
    :return: Cleaned list of rows.
    """
    cleaned: List[dict[str, str]] = []

    for row in data:
        # If your CSV has a different field name for chips, adjust below.
        chip_str = row.get("chip_count", "").strip()

        # Basic checks
        if not chip_str:
            continue
        if chip_str.lower() in ("nan", "null", "none"):
            continue

        try:
            # Validate that this is an integer
            int_chip_count = int(chip_str)
        except ValueError:
            continue

        # Overwrite the string with the validated integer as a string
        row["chip_count"] = str(int_chip_count)
        cleaned.append(row)

    return cleaned


def call_openai_api(cleaned_data: List[dict[str, str]]) -> str:
    """
    Call the OpenAI API to process/summarize the cleaned poker chip data.
    Modify the prompt based on your use case.

    :param cleaned_data: Cleaned list of rows (each row has 'player_name' and 'chip_count').
    :return: A string response from OpenAI.
    """
    # Make sure OPENAI_API_KEY is set in your environment.
    openai.api_key = os.environ.get("OPENAI_API_KEY", "")

    # Build a short structured summary of the data to feed into the model.
    # For large amounts of data, you may need a different approach (chunking, embeddings, etc.).
    data_str_list = []
    for row in cleaned_data:
        name = row.get("player_name", "Unknown")
        chips = row.get("chip_count", "0")
        data_str_list.append(f"{name}: {chips} chips")

    data_str = "\n".join(data_str_list)

    # Prompt can be adjusted as needed:
    prompt = (
        "You are given a list of poker players and their chip counts:\n"
        f"{data_str}\n\n"
        "Please provide a brief summary. Include total chips combined and the highest chip count."
    )

    # Using ChatCompletion (gpt-3.5-turbo as an example):
    # (You could also use Completion endpoint for more basic usage.)
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.0,
    )

    # Extract the response text from the API
    return response.choices[0].message.content.strip()


def main() -> None:
    """
    Main entry point: parse arguments, load and clean the data,
    call the OpenAI API, and save the result.
    """
    parser = argparse.ArgumentParser(
        description="Scrape/clean a CSV file of poker chip values and names using the OpenAI API."
    )
    parser.add_argument(
        "--input_csv",
        type=str,
        required=True,
        help="Path to the input CSV file containing poker data.",
    )
    parser.add_argument(
        "--output_txt",
        type=str,
        required=True,
        help="Path to the output text file to store the OpenAI summary.",
    )

    args = parser.parse_args()

    # Load the CSV data
    data = load_data(args.input_csv)

    # Clean the data (remove NaN, invalid, parse chip_count)
    cleaned_data = clean_data(data)

    if not cleaned_data:
        print("No valid chip data found after cleaning. Exiting.")
        return

    # Call OpenAI API to process/summarize
    result = call_openai_api(cleaned_data)

    # Save the OpenAI result
    os.makedirs(os.path.dirname(os.path.abspath(args.output_txt)), exist_ok=True)
    with open(args.output_txt, mode="w", encoding="utf-8") as outfile:
        outfile.write(result + "\n")

    print("Summary written to:", args.output_txt)


if __name__ == "__main__":
    main()
