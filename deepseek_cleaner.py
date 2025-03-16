#!/usr/bin/env python3
"""Clean OCR output using DeepSeek API to extract player information."""

import json
import os
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
import requests
import argparse
from tqdm import tqdm

# Configure DeepSeek API key
DEEPSEEK_API_KEY = "sk-87442b8542574602abe06f7084f7198a"  # Your API key
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"  # Updated endpoint

def process_frame_with_deepseek(filepath: str, raw_text_items: List[Dict]) -> Dict:
    """Use DeepSeek API to extract player information from OCR data."""
    # Convert raw OCR data to a format that's easier for the model to understand
    ocr_data = []
    for item in raw_text_items:
        ocr_data.append({
            "text": item.get("text", "").strip(),
            "confidence": item.get("confidence", 0),
            "x": item.get("x", 0),
            "y": item.get("y", 0)
        })
    
    print("\nSending OCR data to API:")
    print(json.dumps(ocr_data, indent=2))
    
    # Prepare the prompt for DeepSeek-V3
    prompt = f"""
You are analyzing OCR data from a poker broadcast screenshot. Your task is to extract player names (last name) and their chip counts.

Rules for identifying valid data:
1. Player names:
   - Can be 2 or more letters (e.g. "VU" is valid)
   - Common examples: "SMITH", "NEGREANU", "VU"
   - Ignore UI elements like "BLINDS", "ANTE", "BB", "SB", etc.
   - use your best judgement and knowledge of poker tournaments to determine if the name is a player or not
   - sometimes the letters may be lower case (due to ocr), so correct the name as you see fit

2. Chip counts:
   - Must be numbers with commas (e.g. "1,234,000")
   - Or abbreviated (e.g. "1.2M" = 1,200,000)
   - Must be close to their player name
   - Must be non-zero
   - sometimes zeroes may be read as "o", so adjust as you see fit

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

If you can't confidently match a name with its chip count, exclude the frame/entry entirely.
If there are any unmatched chip counts, return an empty array.
"""

    # Call DeepSeek API
    try:
        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "deepseek-chat",  # Updated model name
            "messages": [
                {"role": "system", "content": "You are a specialized poker broadcast data extractor. You only output valid JSON arrays containing player data."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 500,
            "temperature": 0.1,
            "stream": False
        }
        
        print("\nSending request to DeepSeek API...")
        response = requests.post(DEEPSEEK_API_URL, headers=headers, json=data)
        print("\nAPI Response Status:", response.status_code)
        print("\nRaw API Response:")
        print(response.text)
        
        response.raise_for_status()  # Raise an exception for bad status codes
        
        result = response.json()
        result_text = result["choices"][0]["message"]["content"].strip()
        
        print("\nExtracted content:")
        print(result_text)
        
        # Extract the JSON part from the response
        json_start = result_text.find("[")
        json_end = result_text.rfind("]") + 1
        
        if json_start >= 0 and json_end > json_start:
            json_str = result_text[json_start:json_end]
            print("\nExtracted JSON:")
            print(json_str)
            players = json.loads(json_str)
        else:
            print("\nNo JSON array found in response")
            players = []
        
        # Calculate total chips
        total_chips = sum(player.get("chips", 0) for player in players)
        
        # Add confidence to each player (using average of 0.95 for DeepSeek)
        for player in players:
            player["confidence"] = 0.95
        
        return {
            "filepath": filepath,
            "players": players,
            "total_chips": total_chips,
            "expected_total": None,
            "is_valid": None
        }
    
    except Exception as e:
        print(f"Error calling DeepSeek API: {e}")
        return {
            "filepath": filepath,
            "players": [],
            "total_chips": 0,
            "expected_total": None,
            "is_valid": None
        }

def process_file(input_file: str, output_file: str) -> None:
    """Process raw OCR output file with DeepSeek and write cleaned data to output file."""
    # First count total lines
    with open(input_file, "r", encoding="utf-8") as f:
        total_lines = sum(1 for _ in f)
    
    # Process files with progress bar
    with open(input_file, "r", encoding="utf-8") as f_in, \
         open(output_file, "w", encoding="utf-8") as f_out, \
         tqdm(total=total_lines, desc="Processing frames") as pbar:
        
        for line in f_in:
            try:
                data = json.loads(line.strip())
                filepath = data.get("filepath", "")
                raw_text = data.get("raw_text", [])
                
                # Process with DeepSeek
                result = process_frame_with_deepseek(filepath, raw_text)
                
                # Write to output file
                json.dump(result, f_out)
                f_out.write("\n")
                
                # Add a small delay to avoid hitting rate limits
                time.sleep(0.1)  # DeepSeek has higher rate limits, so we can reduce the delay
                
                # Update progress bar
                pbar.update(1)
                
            except json.JSONDecodeError:
                print(f"Error decoding JSON: {line}")
            except Exception as e:
                print(f"Error processing line: {e}")

def test_single_frame():
    """Test the DeepSeek API with a single frame."""
    # Read the first frame from raw_output.jsonl
    with open("raw_output.jsonl", "r", encoding="utf-8") as f:
        first_frame = json.loads(f.readline().strip())
        
    print("Testing with frame:", first_frame["filepath"])
    result = process_frame_with_deepseek(first_frame["filepath"], first_frame["raw_text"])
    print("\nResult:")
    print(json.dumps(result, indent=2))

def main():
    """Main function to process raw OCR output with DeepSeek."""
    # Add command line argument parsing
    parser = argparse.ArgumentParser(description="Process OCR data with DeepSeek API")
    parser.add_argument("--test", action="store_true", help="Run test on single frame")
    args = parser.parse_args()
    
    if args.test:
        test_single_frame()
    else:
        input_file = "raw_output.jsonl"
        output_file = "deepseek_out.jsonl"
        process_file(input_file, output_file)
        print(f"Processed OCR data written to {output_file}")

if __name__ == "__main__":
    main() 