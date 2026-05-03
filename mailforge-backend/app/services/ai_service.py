import httpx
from app.config import get_settings

settings = get_settings()

async def generate_email_content(prompt: str, contact: dict, context: str = "") -> str:
    rendered_prompt = prompt
    for key, value in contact.items():
        rendered_prompt = rendered_prompt.replace(f"{{{{{key}}}}}", str(value or ""))

    payload = {
        "model": settings.OLLAMA_MODEL,
        "prompt": f"{context}\n\n{rendered_prompt}" if context else rendered_prompt,
        "stream": False
    }

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(f"{settings.OLLAMA_BASE_URL}/api/generate", json=payload)
        resp.raise_for_status()
        return resp.json()["response"]

async def list_ollama_models() -> list:
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
        resp.raise_for_status()
        return [m["name"] for m in resp.json().get("models", [])]