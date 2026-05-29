from sqlalchemy.ext.asyncio import AsyncSession

from src.db.repositories.conversation_repo import ConversationRepository
from src.domain.conversation import Role


class ConversationService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = ConversationRepository(session)

    async def record_user_message(
        self, user_id: int, content: str, is_voice: bool = False
    ) -> int:
        """Сохраняет сообщение пользователя в активном диалоге. Возвращает conversation_id."""
        conversation = await self.repo.get_or_create_active(user_id)
        await self.repo.add_message(
            conversation, role=Role.USER, content=content, is_voice=is_voice
        )
        await self.session.commit()
        return conversation.id

    async def record_assistant_message(self, user_id: int, content: str) -> None:
        conversation = await self.repo.get_or_create_active(user_id)
        await self.repo.add_message(conversation, role=Role.ASSISTANT, content=content)
        await self.session.commit()

    async def set_domain(self, user_id: int, domain: str) -> None:
        conversation = await self.repo.get_or_create_active(user_id)
        if conversation.domain is None:
            conversation.domain = domain
            await self.session.commit()

    async def history(self, user_id: int, limit: int = 10) -> list[dict[str, str]]:
        conversation = await self.repo.get_active(user_id)
        if conversation is None:
            return []
        messages = await self.repo.recent_messages(conversation.id, limit=limit)
        return [{"role": m.role, "content": m.content} for m in messages]

    async def reset(self, user_id: int) -> None:
        await self.repo.end_active(user_id)
        await self.session.commit()
