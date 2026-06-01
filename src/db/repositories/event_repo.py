from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Event


class EventRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(
        self,
        *,
        user_id: int | None,
        event_type: str,
        domain: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Event:
        event = Event(
            user_id=user_id,
            event_type=event_type,
            domain=domain,
            event_metadata=metadata or {},
        )
        self.session.add(event)
        await self.session.flush()
        return event
