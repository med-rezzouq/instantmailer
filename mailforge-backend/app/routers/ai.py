from fastapi import APIRouter, Depends

from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.ai import OllamaGenerateIn, OllamaGenerateOut
from app.services.ai_service import generate_with_ollama

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/generate", response_model=OllamaGenerateOut)
async def generate_text(
    payload: OllamaGenerateIn,
    current_user: User = Depends(get_current_user),
):
    response_text = await generate_with_ollama(
        prompt=payload.prompt,
        model=payload.model,
    )

    return OllamaGenerateOut(
        ok=True,
        model=payload.model,
        response=response_text,
    )