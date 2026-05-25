from uuid import UUID
from datetime import datetime, timezone, timedelta
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.intelligence.infrastructure.models import AIConversationModel, AIMessageModel


class SQLAlchemyConversationRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    def _conversation_to_dict(self, m: AIConversationModel) -> dict:
        return {
            "id": str(m.id),
            "user_id": str(m.user_id),
            "title": m.title,
            "model": m.model,
            "created_at": m.created_at,
            "updated_at": m.updated_at,
        }

    def _message_to_dict(self, m: AIMessageModel) -> dict:
        return {
            "id": str(m.id),
            "conversation_id": str(m.conversation_id),
            "role": m.role,
            "content": m.content,
            "tokens_used": m.tokens_used,
            "created_at": m.created_at,
        }

    async def get_by_id(self, conversation_id: UUID) -> dict | None:
        r = await self._session.execute(
            select(AIConversationModel).where(
                AIConversationModel.id == conversation_id
            )
        )
        m = r.scalar_one_or_none()
        return self._conversation_to_dict(m) if m else None

    async def list_by_user(
        self,
        user_id: UUID,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[list[dict], int]:
        q = select(AIConversationModel).where(
            AIConversationModel.user_id == user_id
        )
        cq = select(func.count()).select_from(AIConversationModel).where(
            AIConversationModel.user_id == user_id
        )

        q = q.order_by(AIConversationModel.updated_at.desc())

        total = (await self._session.execute(cq)).scalar() or 0
        r = await self._session.execute(q.offset((page - 1) * limit).limit(limit))
        items = [self._conversation_to_dict(m) for m in r.scalars().all()]
        return items, total

    async def create(self, data: dict) -> dict:
        m = AIConversationModel(
            user_id=data["user_id"],
            title=data.get("title", "New Chat"),
            model=data.get("model", "gpt-4"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )
        self._session.add(m)
        await self._session.flush()
        return self._conversation_to_dict(m)

    async def delete(self, conversation_id: UUID) -> bool:
        r = await self._session.execute(
            select(AIConversationModel).where(
                AIConversationModel.id == conversation_id
            )
        )
        m = r.scalar_one_or_none()
        if not m:
            return False
        await self._session.delete(m)
        await self._session.flush()
        return True

    async def add_message(self, data: dict) -> dict:
        m = AIMessageModel(
            conversation_id=data["conversation_id"],
            role=data["role"],
            content=data["content"],
            tokens_used=data.get("tokens_used", 0),
            created_at=data.get("created_at"),
        )
        self._session.add(m)

        r = await self._session.execute(
            select(AIConversationModel).where(
                AIConversationModel.id == data["conversation_id"]
            )
        )
        conv = r.scalar_one_or_none()
        if conv:
            conv.updated_at = datetime.now(timezone.utc).isoformat()

        await self._session.flush()
        return self._message_to_dict(m)

    async def get_messages(
        self,
        conversation_id: UUID,
    ) -> list[dict]:
        r = await self._session.execute(
            select(AIMessageModel)
            .where(AIMessageModel.conversation_id == conversation_id)
            .order_by(AIMessageModel.created_at.asc())
        )
        return [self._message_to_dict(m) for m in r.scalars().all()]

    async def count_messages_last_hour(self, user_id: UUID) -> int:
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        r = await self._session.execute(
            select(func.count())
            .select_from(AIMessageModel)
            .join(
                AIConversationModel,
                AIMessageModel.conversation_id == AIConversationModel.id,
            )
            .where(
                and_(
                    AIConversationModel.user_id == user_id,
                    AIMessageModel.role == "user",
                    AIMessageModel.created_at >= cutoff,
                )
            )
        )
        return r.scalar() or 0
