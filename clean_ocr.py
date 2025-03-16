#!/usr/bin/env python3
"""Clean OCR output to extract player information."""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

# Keywords to filter out (common UI elements and false positives)
KEYWORDS_TO_FILTER = [
    "blinds", "ante", "bb ante", "total pot", "main pot", "side pot", 
    "dealer", "fold", "check", "call", "raise", "all in", 
    "pokergo", "bb", "sb", "play", "morikey", "moikey", "til", "rb"
]

def is_valid_player_name(text: str) -> bool:
    """Check if text is a valid player name."""
    # Check for all-uppercase names (standard in poker broadcasts)
    if re.match(r"^[A-Z][A-Z\s\-'.]{2,}$", text) and not text.isdigit():
        return True
    
    # Also accept mixed-case names (sometimes OCR detects proper case)
    if re.match(r"^[A-Za-z][A-Za-z\s\-'.]{2,}$", text) and not text.isdigit():
        return True
        
    return False

def is_numeric_or_abbreviation(text: str) -> bool:
    """Check if text is a numeric value or abbreviated chip count (e.g., '2M')."""
    # Check if it's a number with optional commas
    if re.match(r"^[\d,]+$", text):
        return True
    
    # Check if it's an abbreviated chip count (e.g., '2M', '1.5K')
    if re.match(r"^(\d+(?:\.\d+)?)\s*[KMB]$", text, re.IGNORECASE):
        return True
        
    return False

def extract_players(raw_text_items: List[Dict]) -> List[Dict]:
    """Extract player information from raw OCR text items."""
    # Use a moderate confidence threshold
    MIN_CONFIDENCE = 0.5
    filtered_items = [item for item in raw_text_items if item.get("confidence", 0) > MIN_CONFIDENCE]
    
    # Skip processing if no items with sufficient confidence
    if not filtered_items:
        return []
    
    # First pass: identify potential player names and chip counts separately
    potential_names = []
    potential_chips = []
    
    for item in filtered_items:
        text = item.get("text", "").strip()
        confidence = item.get("confidence", 0)
        x = item.get("x", 0)
        y = item.get("y", 0)
        
        # Skip empty text
        if not text:
            continue
            
        # Skip common UI elements and irrelevant text
        if text.lower() in KEYWORDS_TO_FILTER:
            continue
        
        # Process chip counts
        if is_numeric_or_abbreviation(text):
            try:
                # Handle abbreviated chip counts (e.g., "2M" for 2 million)
                chip_abbrev_match = re.match(r"^(\d+(?:\.\d+)?)\s*([KMB])$", text, re.IGNORECASE)
                if chip_abbrev_match:
                    value = float(chip_abbrev_match.group(1))
                    unit = chip_abbrev_match.group(2).upper()
                    
                    # Convert to full number
                    if unit == "K":
                        chip_count = int(value * 1000)
                    elif unit == "M":
                        chip_count = int(value * 1000000)
                    elif unit == "B":
                        chip_count = int(value * 1000000000)
                    else:
                        continue
                else:
                    # Handle regular numbers with commas
                    chip_count = int(text.replace(",", "").replace(".", ""))
                
                potential_chips.append({
                    "text": text,
                    "chips": chip_count,
                    "confidence": confidence,
                    "y": y,
                    "x": x
                })
            except (ValueError, AttributeError):
                continue
            continue
        
        # Check if this might be a valid player name
        if is_valid_player_name(text):
            # Less strict name validation 
            if len(text) >= 2:
                potential_names.append({
                    "text": text,
                    "confidence": confidence,
                    "y": y,
                    "x": x
                })
    
    # Sort names by x-coordinate to process left to right
    potential_names.sort(key=lambda x: x["x"])
    
    players = []
    used_chips = set()  # Track which chip counts we've used
    
    # For each player name, find the best matching chip count
    for name_item in potential_names:
        name = name_item["text"]
        name_x = name_item["x"]
        name_y = name_item["y"]
        
        # Find the best matching chip count
        best_match = None
        min_score = float('inf')
        
        for i, chip_item in enumerate(potential_chips):
            if i in used_chips:
                continue
                
            chip_x = chip_item["x"]
            chip_y = chip_item["y"]
            
            # Calculate distances - more permissive distance constraints
            x_distance = abs(chip_x - name_x)
            y_distance = abs(chip_y - name_y)  # Allow chips above or below names
            
            # Use more permissive constraints
            max_x_distance = 100  # Increased horizontal threshold
            max_y_distance = 80   # Increased vertical threshold
            
            if x_distance > max_x_distance or y_distance > max_y_distance:
                continue
            
            # Calculate score (lower is better)
            x_weight = 1.0
            y_weight = 2.0  # Still prioritize vertical alignment but less strictly
            
            score = (x_weight * x_distance) + (y_weight * y_distance)
            
            if score < min_score:
                min_score = score
                best_match = (i, chip_item)
        
        if best_match:
            idx, chip_item = best_match
            # Only add players with non-zero chip counts
            if chip_item["chips"] > 0:
                players.append({
                    "name": name,
                    "chips": chip_item["chips"],
                    "confidence": (name_item["confidence"] + chip_item["confidence"]) / 2
                })
                used_chips.add(idx)
        # If no match found, don't add player - but we still proceed with other players
    
    # If there are any chip counts that weren't matched to a player, drop the entire frame
    if len(used_chips) < len(potential_chips):
        return []
    
    return players

def process_file(input_file: str, output_file: str) -> None:
    """Process raw OCR output file and write cleaned data to output file."""
    with open(input_file, "r", encoding="utf-8") as f_in, open(output_file, "w", encoding="utf-8") as f_out:
        for line in f_in:
            try:
                data = json.loads(line.strip())
                filepath = data.get("filepath", "")
                raw_text = data.get("raw_text", [])
                
                # Extract player information
                players = extract_players(raw_text)
                
                # Calculate total chips
                total_chips = sum(player.get("chips", 0) for player in players)
                
                # Create output record
                output_record = {
                    "filepath": filepath,
                    "players": players,
                    "total_chips": total_chips,
                    "expected_total": None,  # To be filled in later if needed
                    "is_valid": None  # To be filled in later if needed
                }
                
                # Write to output file
                json.dump(output_record, f_out)
                f_out.write("\n")
                
            except json.JSONDecodeError:
                print(f"Error decoding JSON: {line}")
            except Exception as e:
                print(f"Error processing line: {e}")

def main():
    """Main function to process raw OCR output."""
    input_file = "raw_output.jsonl"
    output_file = "out.jsonl"
    
    process_file(input_file, output_file)
    print(f"Processed OCR data written to {output_file}")

if __name__ == "__main__":
    main() 