#!/usr/bin/env python3
"""Clean OCR output using OpenAI API to extract player information."""

import json
import os
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import openai

# Configure OpenAI API key
openai.api_key = os.environ.get("OPENAI_API_KEY")
if not openai.api_key:
    raise ValueError("OpenAI API key not found. Set the OPENAI_API_KEY environment variable.")

def process_frame_with_openai(filepath: str, raw_text_items: List[Dict]) -> Dict:
    """Use OpenAI API to extract player information from OCR data."""
    # Convert raw OCR data to a format that's easier for the model to understand
    ocr_data = []
    for item in raw_text_items:
        ocr_data.append({
            "text": item.get("text", "").strip(),
            "confidence": item.get("confidence", 0),
            "x": item.get("x", 0),
            "y": item.get("y", 0)
        })
    
    # Prepare a more structured prompt for GPT-3.5-Turbo
    prompt = f"""
You are analyzing OCR data from a poker broadcast screenshot. Your task is to extract player names and their chip counts.

Rules for identifying valid data:
1. Player names:
   - Must be in ALL CAPS
   - Can be 2 or more letters (e.g. "VU" is valid)
   - Common examples: "SMITH", "NEGREANU", "VU"
   - Ignore UI elements like "BLINDS", "ANTE", "BB", "SB"

2. Chip counts:
   - Must be numbers with commas (e.g. "1,234,000")
   - Or abbreviated (e.g. "1.2M" = 1,200,000)
   - Must be close to their player name
   - Must be non-zero

3. Layout:
   - Player names and their chip counts are typically vertically aligned
   - Names usually appear above their chip counts
   - Chip counts are usually within 80 pixels vertically of their name

OCR data (format: text, confidence, x-pos, y-pos):
{json.dumps(ocr_data, indent=2)}

Return ONLY a JSON array of valid players and their chip counts:
[
    {{"name": "PLAYER_NAME", "chips": CHIP_COUNT}},
    ...
]

If you can't confidently match a name with its chip count, exclude it entirely.
If there are any unmatched chip counts, return an empty array.
"""

    # Call OpenAI API with GPT-3.5-Turbo
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # Using the cheaper model
            messages=[
                {"role": "system", "content": "You are a specialized poker broadcast data extractor. You only output valid JSON arrays containing player data."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,  # Reduced since we expect shorter outputs
            temperature=0.1  # Lower temperature for more consistent outputs
        )
        
        result_text = response.choices[0].message.content.strip()
        
        # Extract the JSON part from the response
        json_start = result_text.find("[")
        json_end = result_text.rfind("]") + 1
        
        if json_start >= 0 and json_end > json_start:
            json_str = result_text[json_start:json_end]
            players = json.loads(json_str)
        else:
            players = []
        
        # Calculate total chips
        total_chips = sum(player.get("chips", 0) for player in players)
        
        # Add confidence to each player (using average of 0.85 for GPT-3.5-Turbo)
        for player in players:
            player["confidence"] = 0.85
        
        return {
            "filepath": filepath,
            "players": players,
            "total_chips": total_chips,
            "expected_total": None,
            "is_valid": None
        }
    
    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        return {
            "filepath": filepath,
            "players": [],
            "total_chips": 0,
            "expected_total": None,
            "is_valid": None
        }

def process_file(input_file: str, output_file: str) -> None:
    """Process raw OCR output file with OpenAI and write cleaned data to output file."""
    with open(input_file, "r", encoding="utf-8") as f_in, open(output_file, "w", encoding="utf-8") as f_out:
        line_count = 0
        for line in f_in:
            try:
                line_count += 1
                print(f"Processing line {line_count}...")
                
                data = json.loads(line.strip())
                filepath = data.get("filepath", "")
                raw_text = data.get("raw_text", [])
                
                # Process with OpenAI
                result = process_frame_with_openai(filepath, raw_text)
                
                # Write to output file
                json.dump(result, f_out)
                f_out.write("\n")
                
                # Add a small delay to avoid hitting rate limits
                time.sleep(0.5)
                
            except json.JSONDecodeError:
                print(f"Error decoding JSON: {line}")
            except Exception as e:
                print(f"Error processing line: {e}")

def main():
    """Main function to process raw OCR output with OpenAI."""
    input_file = "raw_output.jsonl"
    output_file = "openai_out.jsonl"
    
    process_file(input_file, output_file)
    print(f"Processed OCR data written to {output_file}")

if __name__ == "__main__":
    main() 