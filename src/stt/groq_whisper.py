import logging
from functools import lru_cache

import httpx

from src.config import settings

logger = logging.getLogger(__name__)

GROQ_URL = "https://api.groq.com/openai/v1/audio/transcriptions"


class STTError(Exception):
    pass


class GroqSTTService:
    """Groq Whisper Large v3. ~$0.111 за час аудио; голос в Telegram = копейки."""

    def __init__(
        self,
        api_key: str,
        model: str = "whisper-large-v3",
        timeout: float = 60.0,
    ):
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    async def transcribe(self, audio_data: bytes, language: str = "ru") -> str:
        headers = {"Authorization": f"Bearer {self.api_key}"}
        files = {"file": ("voice.ogg", audio_data, "audio/ogg")}
        data = {"model": self.model, "language": language, "response_format": "text"}

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(
                    GROQ_URL, headers=headers, files=files, data=data
                )
                response.raise_for_status()
            except httpx.HTTPError as exc:
                logger.error("Groq STT failed: %s", exc)
                raise STTError(f"Транскрипция не удалась: {exc}") from exc

        return response.text.strip()


@lru_cache
def get_stt() -> GroqSTTService:
    return GroqSTTService(api_key=settings.groq_api_key)
