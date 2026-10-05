import json, re, httpx
from ..config import settings

STYLES = {
    "very_short": "Body must be 1-2 sentences.",
    "concise": "Body must be one short paragraph.",
    "formal": "Body must be two short formal paragraphs.",
    "detailed": "Body must be two paragraphs with full relevant details (dates, purpose, requirements).",
}

# Prompt is strictly limited to subject + body.
PROMPT = """You are an expert administrative letter writer. Generate:
1. Subject
2. Letter Body

Rules:
- Formal tone
- Concise
- Professional
- Suitable for official college correspondence
- Avoid unnecessary words
- Maximum two short paragraphs
- Do not generate sender or recipient information
- Do not generate salutation, thank-you line, or signatures
- {style}

User Request: {user_prompt}
Return strict JSON:
{{ "subject": "...", "body": "..." }}"""

async def generate(user_prompt: str, style: str) -> dict:
    if not settings.groq_api_key:
        raise RuntimeError("GROQ_API_KEY not configured")
    async with httpx.AsyncClient(timeout=60) as c:
        r = await c.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {settings.groq_api_key}"},
            json={
                "model": settings.groq_model,
                "temperature": 0.3,
                "response_format": {"type": "json_object"},
                "messages": [{"role": "user", "content": PROMPT.format(style=STYLES[style], user_prompt=user_prompt)}],
            },
        )
    r.raise_for_status()
    text = r.json()["choices"][0]["message"]["content"]
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.S).strip()  # Qwen reasoning tags
    data = json.loads(text)
    return {"subject": str(data["subject"]).strip(), "body": str(data["body"]).strip()}
