import httpx
from fastapi import HTTPException

OLLAMA_URL = "http://ollama:11434/api/generate"

async def generate_with_ollama(prompt: str, model: str = "llama3.2:latest") -> str:
    prompt = prompt.strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="prompt is required")

    try:
        async with httpx.AsyncClient(timeout=120) as client:
            res = await client.post(
                OLLAMA_URL,
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                },
            )
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"Could not reach Ollama: {str(e)}")

    if res.status_code != 200:
        raise HTTPException(status_code=502, detail=f"Ollama error: {res.text}")

    data = res.json()
    return (data.get("response") or "").strip()