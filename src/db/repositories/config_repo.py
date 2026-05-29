from typing import Any

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Config


class ConfigRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, key: str, default: Any = None) -> Any:
        result = await self.session.execute(select(Config.value).where(Config.key == key))
        row = result.scalar_one_or_none()
        return row if row is not None else default

    async def set(self, key: str, value: Any) -> None:
        stmt = (
            insert(Config)
            .values(key=key, value=value)
            .on_conflict_do_update(index_elements=["key"], set_={"value": value})
        )
        await self.session.execute(stmt)
        await self.session.flush()
