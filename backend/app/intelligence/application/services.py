from uuid import UUID
from datetime import datetime, timezone

from app.intelligence.infrastructure.repositories import SQLAlchemyConversationRepository
from app.intelligence.domain import events as domain_events
from app.shared.events.event_bus import event_bus
from app.shared.exceptions import NotFoundError, ForbiddenError, BadRequestError
from app.shared.pagination import paginate
from app.config import get_settings


class AIService:
    def __init__(self, repo: SQLAlchemyConversationRepository):
        self._repo = repo
        self._settings = get_settings()

    async def list_conversations(
        self,
        user_id: UUID,
        page: int = 1,
        limit: int = 20,
    ) -> dict:
        items, total = await self._repo.list_by_user(
            user_id=user_id, page=page, limit=min(limit, 100)
        )
        return paginate(items, total, page, min(limit, 100))

    async def create_conversation(
        self,
        user_id: UUID,
        title: str = "New Chat",
        model: str = "gpt-4",
    ) -> dict:
        now = datetime.now(timezone.utc).isoformat()
        data = {
            "user_id": user_id,
            "title": title,
            "model": model,
            "created_at": now,
            "updated_at": now,
        }
        return await self._repo.create(data)

    async def get_conversation(
        self,
        conversation_id: UUID,
        current_user_id: UUID,
        current_user_role: str,
    ) -> dict:
        conv = await self._repo.get_by_id(conversation_id)
        if not conv:
            raise NotFoundError("Conversation not found")
        if conv["user_id"] != str(current_user_id) and current_user_role not in (
            "admin",
            "super_admin",
        ):
            raise ForbiddenError("You can only access your own conversations")
        messages = await self._repo.get_messages(conversation_id)
        return {**conv, "messages": messages}

    async def send_message(
        self,
        conversation_id: UUID,
        user_id: UUID,
        content: str,
    ) -> dict:
        if not self._settings.OPENAI_API_KEY:
            raise BadRequestError(
                "AI service is not configured. The OPENAI_API_KEY is not set."
            )

        message_count = await self._repo.count_messages_last_hour(user_id)
        if message_count >= 20:
            raise BadRequestError(
                "Rate limit exceeded. You can send a maximum of 20 messages per hour."
            )

        conv = await self._repo.get_by_id(conversation_id)
        if not conv:
            raise NotFoundError("Conversation not found")
        if conv["user_id"] != str(user_id):
            raise ForbiddenError("You can only send messages to your own conversations")

        now = datetime.now(timezone.utc).isoformat()

        user_msg = await self._repo.add_message(
            {
                "conversation_id": conversation_id,
                "role": "user",
                "content": content,
                "tokens_used": 0,
                "created_at": now,
            }
        )

        previous_messages = await self._repo.get_messages(conversation_id)
        openai_messages = [
            {"role": m["role"], "content": m["content"]}
            for m in previous_messages
        ]

        try:
            import httpx

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self._settings.OPENAI_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": conv.get("model", "gpt-4"),
                        "messages": openai_messages,
                    },
                    timeout=60.0,
                )
                response.raise_for_status()
                data = response.json()
                assistant_content = data["choices"][0]["message"]["content"]
                tokens_used = data.get("usage", {}).get("total_tokens", 0)
        except Exception as exc:
            raise BadRequestError(f"AI service error: {str(exc)}")

        assistant_msg = await self._repo.add_message(
            {
                "conversation_id": conversation_id,
                "role": "assistant",
                "content": assistant_content,
                "tokens_used": tokens_used,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        )

        await event_bus.publish(
            domain_events.ai_message_sent(
                str(conversation_id), str(user_id), tokens_used
            )
        )

        return {"user_message": user_msg, "assistant_message": assistant_msg}

    async def delete_conversation(
        self,
        conversation_id: UUID,
        current_user_id: UUID,
        current_user_role: str,
    ) -> None:
        conv = await self._repo.get_by_id(conversation_id)
        if not conv:
            raise NotFoundError("Conversation not found")
        if conv["user_id"] != str(current_user_id) and current_user_role not in (
            "admin",
            "super_admin",
        ):
            raise ForbiddenError("You can only delete your own conversations")
        await self._repo.delete(conversation_id)
