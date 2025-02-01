#!/usr/bin/env python3
"""Parse player names and chip counts from WSOP screenshots."""

import os
import csv
import re
import easyocr
from PIL import Image
import numpy as np
from pathlib import Path

def clean_number(text):
    """Clean and convert text to a proper number."""
    try:
        # Remove any non-digit or non-comma characters
        clean = ''.join(c for c in text if c.isdigit() or c == ',')
        # Remove any leading/trailing commas
        clean = clean.strip(',')
        # Convert to integer
        return int(clean.replace(',', ''))
    except ValueError:
        return None

def is_valid_chip_count(num):
    """Check if a number is likely to be a valid chip count."""
    return 100_000 <= num <= 200_000_000  # Adjusted range based on observed values

def is_valid_name(text):
    """Check if text looks like a player name."""
    # Remove common OCR artifacts and spaces
    text = text.strip(' |-')
    
    # Skip common non-name text
    skip_words = {'BLINDS', 'ANTE', 'BB', 'SB', 'OH', 'MLA'}
    if text.upper() in skip_words:
        return False
        
    # Must be at least 2 chars
    if len(text) < 2:
        return False
        
    # Must be mostly letters (allow some special chars)
    letter_count = sum(c.isalpha() for c in text)
    if letter_count / len(text) < 0.7:  # At least 70% letters
        return False
        
    return True

def extract_info(image_path: str, reader):
    """Extract text from WSOP screenshot."""
    try:
        # Load and process image
        with Image.open(image_path) as img:
            img_np = np.array(img)
            if len(img_np.shape) == 3 and img_np.shape[2] == 4:
                img = img.convert('RGB')
                img_np = np.array(img)
            
            # Get OCR results with position information
            results = reader.readtext(img_np)
            
            print("\nRaw OCR output:")
            for _, text, _ in results:
                print(f"  {text}")
            
            # First pass: collect all valid numbers and names
            valid_numbers = {}  # x_pos -> number
            valid_names = {}    # x_pos -> name
            
            for bbox, text, _ in results:
                x_pos = (bbox[0][0] + bbox[2][0]) / 2
                y_pos = (bbox[0][1] + bbox[2][1]) / 2
                
                # Check for chip counts
                matches = re.findall(r'[\d,]+', text)
                for match in matches:
                    num = clean_number(match)
                    if num and is_valid_chip_count(num):
                        valid_numbers[x_pos] = num
                
                # Check for names
                # Remove the number part if present
                name_part = re.sub(r'[\d,]+', '', text)
                if is_valid_name(name_part):
                    valid_names[x_pos] = name_part.strip()
            
            print("\nValid names found:", list(valid_names.values()))
            print("Valid numbers found:", [f"{n:,}" for n in valid_numbers.values()])
            
            # Second pass: match names with numbers based on proximity
            players = []
            name_positions = sorted(valid_names.keys())
            number_positions = sorted(valid_numbers.keys())
            
            # Try to match each name with the closest number
            for name_x in name_positions:
                name = valid_names[name_x]
                # Find closest number position
                if number_positions:
                    closest_num_x = min(number_positions, 
                                      key=lambda x: abs(x - name_x))
                    players.append({
                        'name': name,
                        'chips': valid_numbers[closest_num_x],
                        'x_pos': name_x
                    })
            
            # Sort players by x position (left to right)
            players.sort(key=lambda p: p['x_pos'])
            
            return players, sorted(valid_numbers.values())
            
    except Exception as e:
        print(f"Error processing image: {str(e)}")
        return [], []

# Initialize EasyOCR reader
print("Initializing EasyOCR (this may take a moment)...")
reader = easyocr.Reader(['en'])

# Process images and write to CSV
with open("output.csv", mode="w", newline="", encoding="utf-8") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["filename", "player_name", "chip_count", "all_chip_counts"])

    for image_path in sorted(Path("cropped").glob("*.png")):
        try:
            print(f"\nProcessing: {image_path.name}")
            
            # Get player-chip pairs and all chip counts
            players, all_chips = extract_info(str(image_path), reader)
            
            # Write results
            if players:
                for player in players:
                    writer.writerow([
                        image_path.name,
                        player['name'],
                        f"{player['chips']:,}",
                        " | ".join(f"{num:,}" for num in all_chips)
                    ])
                    print(f"Found: {player['name']} - {player['chips']:,}")
            else:
                writer.writerow([
                    image_path.name,
                    "",
                    "",
                    " | ".join(f"{num:,}" for num in all_chips) if all_chips else ""
                ])
            
            # Debug output
            print(f"Players found: {len(players)}")
            for p in players:
                print(f"  {p['name']}: {p['chips']:,}")
            print("-" * 80)
            
        except Exception as e:
            print(f"Error processing {image_path.name}: {str(e)}")
            writer.writerow([image_path.name, "ERROR", str(e), ""])

print(f"Processed images saved to output.csv")
