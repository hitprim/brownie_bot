from pydantic import BaseModel, Field


class UserPreferencesDTO(BaseModel):
    dietary_restrictions: list[str] = Field(default_factory=list)
    disliked_ingredients: list[str] = Field(default_factory=list)
    default_portions: int = 2
    cooking_skill: str = "beginner"
    preferred_language: str = "ru"


class UserDTO(BaseModel):
    id: int
    telegram_id: int
    username: str | None = None
    first_name: str | None = None
    language_code: str = "ru"
    preferences: UserPreferencesDTO = Field(default_factory=UserPreferencesDTO)
