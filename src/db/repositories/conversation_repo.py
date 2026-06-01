from datetime import UTC, datetime

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Conversation, Message


class ConversationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_active(self, user_id: int) -> Conversation | None:
        """Последний незакрытый диалог пользователя."""
        result = await self.session.execute(
            select(Conversation)
            .where(Conversation.user_id == user_id, Conversation.ended_at.is_(None))
            .order_by(desc(Conversation.started_at))
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def create(self, user_id: int, domain: str | None = None) -> Conversation:
        conversation = Conversation(user_id=user_id, domain=domain)
        self.session.add(conversation)
        await self.session.flush()
        return conversation

    async def get_or_create_active(self, user_id: int) -> Conversation:
        conversation = await self.get_active(user_id)
        if conversation is None:
            conversation = await self.create(user_id)
        return conversation

    async def end(self, conversation: Conversation) -> None:
        conversation.ended_at = datetime.now(UTC)
        await self.session.flush()

    async def end_active(self, user_id: int) -> None:
        conversation = await self.get_active(user_id)
        if conversation is not None:
            await self.end(conversation)

    async def add_message(
        self,
        conversation: Conversation,
        role: str,
        content: str,
        is_voice: bool = False,
    ) -> Message:
        message = Message(
            conversation_id=conversation.id,
            role=role,
            content=content,
            is_voice=is_voice,
        )
        self.session.add(message)
        conversation.messages_count += 1
        await self.session.flush()
        return message

    async def count_user_messages_since(self, user_id: int, since: datetime) -> int:
        """Сколько сообщений пользователь отправил с момента `since` (для лимитов)."""
        result = await self.session.execute(
            select(func.count())
            .select_from(Message)
            .join(Conversation, Message.conversation_id == Conversation.id)
            .where(
                Conversation.user_id == user_id,
                Message.role == "user",
                Message.created_at >= since,
            )
        )
        return int(result.scalar_one())

    async def recent_messages(self, conversation_id: int, limit: int = 10) -> list[Message]:
        result = await self.session.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(desc(Message.created_at))
            .limit(limit)
        )
        return list(reversed(result.scalars().all()))
