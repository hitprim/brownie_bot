from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import User
from src.db.repositories.user_repo import UserRepository
from src.domain.user import UserDTO, UserPreferencesDTO


class UserService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = UserRepository(session)

    async def get_or_create(
        self,
        telegram_id: int,
        username: str | None = None,
        first_name: str | None = None,
        language_code: str = "ru",
    ) -> User:
        user = await self.repo.get_or_create(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            language_code=language_code,
        )
        await self.repo.touch(user)
        await self.session.commit()
        return user

    @staticmethod
    def to_dto(user: User) -> UserDTO:
        prefs = user.preferences
        prefs_dto = (
            UserPreferencesDTO(
                dietary_restrictions=prefs.dietary_restrictions,
                disliked_ingredients=prefs.disliked_ingredients,
                default_portions=prefs.default_portions,
                cooking_skill=prefs.cooking_skill,
                preferred_language=prefs.preferred_language,
            )
            if prefs is not None
            else UserPreferencesDTO()
        )
        return UserDTO(
            id=user.id,
            telegram_id=user.telegram_id,
            username=user.username,
            first_name=user.first_name,
            language_code=user.language_code,
            preferences=prefs_dto,
        )
