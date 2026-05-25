from uuid import UUID
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.database import get_session
from app.shared.auth.dependencies import get_current_user, require_roles
from app.identity.infrastructure.models import UserModel
from app.intelligence.infrastructure.repositories import SQLAlchemyConversationRepository
from app.intelligence.application.services import AIService

router = APIRouter(prefix="/ai", tags=["AI"])


class CreateConversationRequest(BaseModel):
    title: str = "New Chat"
    model: str = "gpt-4"


class SendMessageRequest(BaseModel):
    content: str


def _svc(db) -> AIService:
    return AIService(SQLAlchemyConversationRepository(db))


@router.get("/conversations")
async def list_conversations(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    u: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    return await _svc(db).list_conversations(user_id=u.id, page=page, limit=limit)


@router.post("/conversations", status_code=201)
async def create_conversation(
    b: CreateConversationRequest,
    u: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    return await _svc(db).create_conversation(
        user_id=u.id, title=b.title, model=b.model
    )


@router.get("/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: UUID,
    u: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    return await _svc(db).get_conversation(
        conversation_id=conversation_id,
        current_user_id=u.id,
        current_user_role=u.role,
    )


@router.post("/conversations/{conversation_id}/messages")
async def send_message(
    conversation_id: UUID,
    b: SendMessageRequest,
    u: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    return await _svc(db).send_message(
        conversation_id=conversation_id,
        user_id=u.id,
        content=b.content,
    )


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: UUID,
    u: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    await _svc(db).delete_conversation(
        conversation_id=conversation_id,
        current_user_id=u.id,
        current_user_role=u.role,
    )
    return {"message": "Conversation deleted successfully"}
