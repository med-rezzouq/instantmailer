from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.routers.auth import get_current_user
from app.models.user import User
from app.models.contact import Contact
from app.services.ai_service import generate_email_content, list_ollama_models

router = APIRouter(prefix="/ai", tags=["AI"])

class GenerateRequest(BaseModel):
    prompt: str
    context: Optional[str] = ""
    contact_id: Optional[int] = None
    preview_data: Optional[dict] = {}

class GenerateResponse(BaseModel):
    result: str

@router.get("/models")
async def get_models():
    try:
        models = await list_ollama_models()
        return {"models": models}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Ollama not reachable: {str(e)}")

@router.post("/generate", response_model=GenerateResponse)
async def generate(
    data: GenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    contact_data = data.preview_data or {}

    if data.contact_id:
        result = await db.execute(
            select(Contact).where(Contact.id == data.contact_id, Contact.user_id == current_user.id)
        )
        contact = result.scalar_one_or_none()
        if contact:
            contact_data = {
                "first_name": contact.first_name,
                "last_name": contact.last_name,
                "email": contact.email,
                "name": f"{contact.first_name or ''} {contact.last_name or ''}".strip()
            }

    try:
        result = await generate_email_content(data.prompt, contact_data, data.context)
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"AI generation failed: {str(e)}")