import json
import requests


OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
OLLAMA_MODEL = "qwen2.5:3b"


def generate_brand_intelligence(
    business_name: str,
    industry: str,
    description: str,
    style: str,
) -> dict:
    """
    Generate structured brand strategy using
    the locally running Ollama model.
    """

    prompt = f"""
You are a professional brand strategist.

Create a concise brand identity for this business.

Business name: {business_name}
Industry: {industry}
Business description: {description}
Brand style: {style}

Return ONLY valid JSON.

Use exactly this structure:

{{
    "slogan": "short professional slogan",
    "personality": [
        "trait 1",
        "trait 2",
        "trait 3"
    ],
    "tone": "short tone of voice description",
    "target_audience": "short target audience description",
    "marketing_message": "one short professional marketing message",
    "typography": {{
        "heading": "font recommendation",
        "body": "font recommendation"
    }}
}}

Rules:
- slogan must be 2 to 7 words
- do not include markdown
- do not include explanations
- do not invent factual claims
- personality must contain exactly 3 traits
- typography should use common professional fonts
"""

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {
                "temperature": 0.7,
            },
        },
        timeout=120,
    )

    response.raise_for_status()

    result = response.json()

    generated_text = result.get(
        "response",
        "{}",
    )

    intelligence = json.loads(
        generated_text
    )

    return {
        "slogan": intelligence.get(
            "slogan",
            ""
        ),
        "personality": intelligence.get(
            "personality",
            []
        ),
        "tone": intelligence.get(
            "tone",
            ""
        ),
        "target_audience": intelligence.get(
            "target_audience",
            ""
        ),
        "marketing_message": intelligence.get(
            "marketing_message",
            ""
        ),
        "typography": intelligence.get(
            "typography",
            {
                "heading": "Montserrat",
                "body": "Inter",
            },
        ),
    }