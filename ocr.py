#!/usr/bin/env python3
"""Basic extraction of text from WSOP screenshots without validation."""

import json
import easyocr
import numpy as np
from PIL import Image
from pathlib import Path

def convert_to_serializable(obj):
    """Convert numpy types to Python native types for JSON serialization."""
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    return obj

def extract_raw_info(image_path: str, reader) -> dict:
    """Extract all text from image with minimal filtering."""
    try:
        with Image.open(image_path) as img:
            img_np = np.array(img)
            if len(img_np.shape) == 3 and img_np.shape[2] == 4:
                img = img.convert('RGB')
                img_np = np.array(img)
            
            results = reader.readtext(img_np)
            
            # Store all text with position info
            extracted_text = []
            for bbox, text, conf in results:
                # Convert numpy coordinates to native Python types
                bbox = [[float(x) for x in point] for point in bbox]
                x_pos = float((bbox[0][0] + bbox[2][0]) / 2)
                y_pos = float((bbox[0][1] + bbox[2][1]) / 2)
                
                extracted_text.append({
                    'text': text,
                    'x': x_pos,
                    'y': y_pos,
                    'confidence': float(conf),
                    'bbox': bbox
                })
            
            return {
                'filepath': str(image_path),
                'raw_text': extracted_text,
                'success': True
            }
            
    except Exception as e:
        return {
            'filepath': str(image_path),
            'error': str(e),
            'success': False
        }

def main():
    # Initialize EasyOCR
    print("Initializing EasyOCR (this may take a moment)...")
    reader = easyocr.Reader(['en'])

    # Process images and write raw results to JSONL
    with open("raw_output.jsonl", mode="w", encoding="utf-8") as jsonl_file:
        for image_path in sorted(Path("cropped").glob("*.png")):
            print(f"\nProcessing: {image_path.name}")
            result = extract_raw_info(str(image_path), reader)
            # Convert any remaining numpy types to native Python types
            result = json.loads(json.dumps(result, default=convert_to_serializable))
            json.dump(result, jsonl_file)
            jsonl_file.write('\n')

    print("Raw extraction complete. Results saved to raw_output.jsonl")

if __name__ == "__main__":
    main()
