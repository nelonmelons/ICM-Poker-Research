#!/usr/bin/env python3
"""Create a training dataset from OCR output for fine-tuning language models."""

import json
import os
from pathlib import Path
import argparse
from tqdm import tqdm

def format_for_training(filepath: str, raw_text_items: list) -> dict:
    """Format OCR data as a prompt-completion pair for training."""
    # Format the raw OCR data as a JSON string with proper escaping
    raw_data = {
        "filepath": filepath,
        "raw_text": raw_text_items,
        "success": True
    }
    
    # Create the training example
    training_example = {
        "prompt": f"Extract the player names, chip counts, and total chips from the following raw OCR output:\n\n {json.dumps(raw_data)}\n\nOutput:",
        "completion": ""  # Empty completion as requested
    }
    
    return training_example

def process_file(input_file: str, output_file: str) -> None:
    """Process raw OCR output file and write training data to output file."""
    # First count total lines
    with open(input_file, "r", encoding="utf-8") as f:
        total_lines = sum(1 for _ in f)
    
    # Process files with progress bar
    with open(input_file, "r", encoding="utf-8") as f_in, \
         open(output_file, "w", encoding="utf-8") as f_out, \
         tqdm(total=total_lines, desc="Formatting training data") as pbar:
        
        for line in f_in:
            try:
                data = json.loads(line.strip())
                filepath = data.get("filepath", "")
                raw_text = data.get("raw_text", [])
                
                # Format as training example
                training_example = format_for_training(filepath, raw_text)
                
                # Write to output file
                json.dump(training_example, f_out)
                f_out.write("\n")
                
                # Update progress bar
                pbar.update(1)
                
            except json.JSONDecodeError:
                print(f"Error decoding JSON: {line}")
            except Exception as e:
                print(f"Error processing line: {e}")

def test_single_frame():
    """Test formatting with a single frame."""
    # Read the first frame from raw_output.jsonl
    with open("raw_output.jsonl", "r", encoding="utf-8") as f:
        first_frame = json.loads(f.readline().strip())
        
    print("Testing with frame:", first_frame["filepath"])
    result = format_for_training(first_frame["filepath"], first_frame["raw_text"])
    print("\nFormatted training example:")
    print(json.dumps(result, indent=2))

def main():
    """Main function to convert raw OCR output to training dataset format."""
    # Add command line argument parsing
    parser = argparse.ArgumentParser(description="Convert OCR data to training dataset format")
    parser.add_argument("--test", action="store_true", help="Run test on single frame")
    parser.add_argument("--input", default="raw_output.jsonl", help="Input file path")
    parser.add_argument("--output", default="training_data.jsonl", help="Output file path")
    args = parser.parse_args()
    
    if args.test:
        test_single_frame()
    else:
        process_file(args.input, args.output)
        print(f"Training data written to {args.output}")

if __name__ == "__main__":
    main() 