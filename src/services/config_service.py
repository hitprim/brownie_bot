from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.db.repositories.config_repo import ConfigRepository

DEFAULTS: dict[str, Any] = {
    "beta_mode": True,
    "free_requests_per_day": 20,
    "voice_enabled": True,
    "max_conversation_turns": 10,
}


class ConfigService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = ConfigRepository(session)

    async def get(self, key: str) -> Any:
        return await self.repo.get(key, default=DEFAULTS.get(key))

    async def set(self, key: str, value: Any) -> None:
        await self.repo.set(key, value)
        await self.session.commit()
