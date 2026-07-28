"""
Calls Gemini 2.5 Flash (multimodal) via Google AI Studio to classify the
fill/overflow severity of a bin photo. Kept as a single, simple function so
it's easy to test from the Gemini CLI before wiring it into the backend.
"""
import json
import os

from dotenv import load_dotenv

load_dotenv()

import google.generativeai as genai
from PIL import Image

genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

MODEL_NAME = "gemini-flash-latest"

CLASSIFICATION_PROMPT = """
You are a civic waste-management inspector. Look at this photo of a public
waste bin and classify it.

Respond ONLY with strict JSON, no markdown fences, in this exact shape:
{
  "status": "empty" | "half_full" | "full" | "overflowing",
  "confidence": <float 0-1>,
  "reasoning": "<one short sentence>"
}
"""


def classify_bin_image(image_path: str) -> dict:
    """Returns {"status": ..., "confidence": ..., "reasoning": ...}."""
    model = genai.GenerativeModel(MODEL_NAME)
    image = Image.open(image_path)

    response = model.generate_content([CLASSIFICATION_PROMPT, image])
    raw_text = response.text.strip()

    # Gemini occasionally wraps JSON in ```json fences despite instructions;
    # strip them defensively.
    if raw_text.startswith("```"):
        raw_text = raw_text.strip("`")
        raw_text = raw_text.replace("json\n", "", 1)

    try:
        result = json.loads(raw_text)
    except json.JSONDecodeError:
        # Fail safe: treat unparseable output as "needs human review"
        result = {
            "status": "full",
            "confidence": 0.0,
            "reasoning": "Could not parse model output; flagged for review.",
        }
    return result


if __name__ == "__main__":
    # Quick manual test: python gemini_service.py path/to/photo.jpg
    import sys

    print(classify_bin_image(sys.argv[1]))
