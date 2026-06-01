from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.db.repositories.event_repo import EventRepository


class EventService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = EventRepository(session)

    async def log(
        self,
        *,
        user_id: int | None,
        event_type: str,
        domain: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        await self.repo.add(
            user_id=user_id,
            event_type=event_type,
            domain=domain,
            metadata=metadata,
        )
        await self.session.commit()
