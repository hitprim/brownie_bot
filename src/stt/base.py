from typing import Protocol, runtime_checkable


@runtime_checkable
class STTProvider(Protocol):
    async def transcribe(self, audio_data: bytes, language: str = "ru") -> str:
        """Транскрибирует аудио в текст."""
        ...
