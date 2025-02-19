#!/usr/bin/env python3
"""Clean and validate OCR results from WSOP screenshots."""

import json
import re
from collections import Counter
from pathlib import Path
from typing import List, Dict, Tuple

def clean_number(text: str) -> int:
    """Clean and convert text to number, handling M/K notation."""
    try:
        # Remove any non-relevant characters
        text = text.upper().strip()
        text = re.sub(r'[^\d.,MK]', '', text)
        
        # Handle M/K notation
        multiplier = 1
        if text.endswith('M'):
            multiplier = 1_000_000
            text = text[:-1]
        elif text.endswith('K'):
            multiplier = 1_000
            text = text[:-1]
            
        # Convert to number
        num = float(text.replace(',', ''))
        return int(num * multiplier)
    except (ValueError, TypeError):
        return None

def is_valid_name(text: str) -> bool:
    """Validate if text is likely a player name."""
    # Remove common OCR artifacts and spaces
    text = text.strip().upper()
    
    # Skip common non-name text
    skip_words = {'BLINDS', 'ANTE', 'BB', 'SB', 'CALL', 'FOLD', 'RAISE', 'ALL-IN', 'QH', 'OH'}
    if text in skip_words:
        return False
    
    # Must be at least 2 characters
    if len(text) < 2:
        return False
    
    # Must be mostly letters
    letter_count = sum(c.isalpha() for c in text)
    if letter_count / len(text) < 0.5:  # Reduced from 0.6 to allow more names
        return False
        
    # Check for repeated characters (likely OCR errors)
    for i in range(len(text)-2):
        if text[i] == text[i+1] == text[i+2]:  # Three same chars in a row
            return False
            
    # Check for common OCR garbage patterns
    garbage_patterns = ['UAA', 'UEA', 'AAA', 'III', '000', '###']
    if any(pattern in text for pattern in garbage_patterns):
        return False
    
    return True

def find_most_common_chip_sum(results: List[Dict]) -> int:
    """Find the most common total chip count across all hands."""
    sums = []
    for result in results:
        if 'players' in result:  # Updated to use players list
            total = sum(p['chips'] for p in result['players'])
            sums.append(total)
    
    if not sums:
        return None
        
    # Use Counter to find most common sum
    sum_counter = Counter(sums)
    return sum_counter.most_common(1)[0][0]

def process_raw_results(input_file: str) -> List[Dict]:
    """Process raw OCR results and create cleaned output."""
    cleaned_results = []
    
    # Read raw results
    with open(input_file, 'r', encoding='utf-8') as f:
        raw_results = [json.loads(line) for line in f]
    
    # First pass: find most common chip sum
    expected_chip_sum = find_most_common_chip_sum(raw_results)
    
    # Process each result
    for raw in raw_results:
        if not raw.get('success', False):
            continue
            
        # First, group items by their approximate y-position (within 10 pixels)
        y_groups = {}
        for item in raw['raw_text']:
            y_group = round(item['y'] / 10) * 10  # Round to nearest 10
            if y_group not in y_groups:
                y_groups[y_group] = []
            y_groups[y_group].append(item)
        
        # Find the two main y-groups (names row and chips row)
        y_values = sorted(y_groups.keys())
        if len(y_values) < 2:
            continue
            
        names_y = y_values[0]  # First row is usually names
        chips_y = y_values[-1]  # Last row is usually chips
        
        # Sort items in each row by x-position
        y_groups[names_y].sort(key=lambda x: x['x'])
        y_groups[chips_y].sort(key=lambda x: x['x'])
        
        # Process all items in order, keeping track of valid names and their positions
        name_positions = []  # List of (index, name, x_pos, confidence) for valid names
        chip_positions = []  # List of (index, value, x_pos, confidence) for valid chips
        
        # Process names row
        for idx, item in enumerate(y_groups[names_y]):
            text = item['text'].upper()
            if is_valid_name(text) and item['confidence'] > 0.5:
                name_positions.append((idx, text, item['x'], item['confidence']))
        
        # Process chips row
        for idx, item in enumerate(y_groups[chips_y]):
            num = clean_number(item['text'])
            if num and 1000 <= num <= 1_000_000_000 and item['confidence'] > 0.5:
                chip_positions.append((idx, num, item['x'], item['confidence']))
        
        # Match names with chips based on their relative positions
        player_pairs = []
        used_chips = set()  # Keep track of which chips have been matched
        
        # Debug output for mismatched counts
        print(f"\nProcessing {raw['filepath']}")
        print(f"Found {len(name_positions)} valid names and {len(chip_positions)} valid chips")
        
        # Match names to closest available chip by x-position
        for name_idx, name, name_x, name_conf in name_positions:
            # Find closest unused chip by x-position
            best_chip = None
            best_distance = float('inf')
            best_chip_data = None
            
            for chip_idx, value, chip_x, chip_conf in chip_positions:
                if chip_idx not in used_chips:
                    # Calculate horizontal distance
                    distance = abs(chip_x - name_x)
                    if distance < best_distance:
                        best_distance = distance
                        best_chip = chip_idx
                        best_chip_data = (value, chip_conf)
            
            # If we found a matching chip within reasonable distance
            if best_chip is not None and best_distance < 500:  # Adjust threshold as needed
                value, chip_conf = best_chip_data
                pair_confidence = (name_conf + chip_conf) / 2
                if pair_confidence >= 0.3:
                    player_pairs.append({
                        'name': name,
                        'chips': value,
                        'confidence': pair_confidence
                    })
                    used_chips.add(best_chip)
        
        # Debug output
        print("Names row y:", names_y)
        print("Chips row y:", chips_y)
        print("Valid names:", [f"{n[1]} (idx: {n[0]}, x: {n[2]:.0f}, conf: {n[3]:.2f})" for n in name_positions])
        print("Valid chips:", [f"{c[1]:,} (idx: {c[0]}, x: {c[2]:.0f}, conf: {c[3]:.2f})" for c in chip_positions])
        print("Matched pairs:", [f"{p['name']}: {p['chips']:,} (conf: {p['confidence']:.2f})" for p in player_pairs])
        
        result = {
            'filepath': raw['filepath'],
            'players': player_pairs,
            'total_chips': sum(p['chips'] for p in player_pairs),
            'expected_total': expected_chip_sum,
            'is_valid': abs(sum(p['chips'] for p in player_pairs) - expected_chip_sum) < 1000000 if expected_chip_sum else None
        }
        
        cleaned_results.append(result)
    
    return cleaned_results

def main():
    # Process and write cleaned results
    raw_file = "raw_output.jsonl"
    cleaned_results = process_raw_results(raw_file)

    with open("out.jsonl", 'w', encoding='utf-8') as f:
        for result in cleaned_results:
            json.dump(result, f)
            f.write('\n')

    print("Cleaning complete. Results saved to out.jsonl")

if __name__ == "__main__":
    main() 