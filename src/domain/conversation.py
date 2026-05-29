from enum import StrEnum

from pydantic import BaseModel


class Domain(StrEnum):
    COOKING = "cooking"
    HOME = "home"
    UNCLEAR = "unclear"


class Role(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"


class ChatMessage(BaseModel):
    role: Role
    content: str
    is_voice: bool = False
