# OpenAI OCR Cleaner for Poker Data

This tool uses the OpenAI API to clean and process OCR data from poker broadcasts, extracting player names and chip counts with high accuracy.

## Why Use OpenAI for Cleaning OCR Data?

Traditional rule-based approaches have limitations when processing OCR data from poker broadcasts:

1. **Strict pattern matching** often fails with OCR errors
2. **Fixed distance thresholds** don't adapt to different broadcast layouts
3. **Complex validation rules** become brittle as edge cases accumulate

OpenAI's GPT models provide several advantages:

1. **Context-aware processing** - understands the typical structure of poker broadcasts
2. **Robust to OCR errors** - can recognize player names even with slight OCR mistakes
3. **Spatial understanding** - can infer relationships between text based on position
4. **Domain knowledge** - leverages knowledge of poker terminology and player names
5. **Adaptability** - works across different broadcast layouts and formats

## Setup

1. Install the OpenAI Python package:
   ```
   pip install openai
   ```

2. Set your OpenAI API key as an environment variable:
   ```
   # For Windows (Command Prompt)
   set OPENAI_API_KEY=your_api_key_here
   
   # For Windows (PowerShell)
   $env:OPENAI_API_KEY="your_api_key_here"
   
   # For Linux/macOS
   export OPENAI_API_KEY=your_api_key_here
   ```

## Usage

Run the OpenAI cleaner on your raw OCR data:

```
python openai_cleaner.py
```

This will:
1. Read the raw OCR data from `raw_output.jsonl`
2. Process each frame using the OpenAI API
3. Save the cleaned data to `openai_out.jsonl`

## Cost Considerations

Using the OpenAI API will incur costs based on the number of tokens processed. Each frame's OCR data will typically use 500-1000 tokens for the prompt, with responses using an additional 100-300 tokens.

For the GPT-4 model (as of 2024):
- Input tokens: ~$0.01 per 1000 tokens
- Output tokens: ~$0.03 per 1000 tokens

Processing 100 frames would cost approximately $1-3 USD.

## Tips for Optimizing Results

1. **Provide context**: The prompt includes details about poker broadcasts. You can enhance it with specific information about your broadcasts.

2. **Adjust temperature**: The script uses a low temperature (0.2) for consistent results. Increase for more creativity.

3. **Rate limiting**: The script includes a small delay between API calls to avoid rate limits. Adjust if needed.

4. **Model selection**: The script uses GPT-4. You can switch to GPT-3.5-Turbo for lower cost (with potentially lower accuracy).

## Comparison with Rule-Based Approach

The OpenAI-based cleaner is likely to outperform the rule-based approach in:

- Correctly identifying player names despite OCR errors
- Associating the right chip counts with player names
- Handling edge cases like two-letter names or unconventional layouts
- Filtering out irrelevant UI elements
- Processing frames with overlapping text or unusual positioning

However, the rule-based approach has advantages in:
- Cost (no API fees)
- Speed
- Privacy (no data sent to external services)
- Deterministic behavior

You may want to use both approaches and compare results, or use the rule-based approach for initial processing and OpenAI for handling difficult cases. 