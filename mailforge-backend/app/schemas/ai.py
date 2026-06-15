from pydantic import BaseModel


class OllamaGenerateIn(BaseModel):
    prompt: str
    model: str = "llama3.2"


class OllamaGenerateOut(BaseModel):
    ok: bool
    model: str
    response: str