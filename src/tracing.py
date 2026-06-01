import logging
import os

from src.config import settings

logger = logging.getLogger("domovoy")


def setup_tracing() -> None:
    """Включает трейсинг LangGraph через LangSmith, если задан ключ.

    LangGraph читает LANGCHAIN_* из окружения — выставляем их из настроек.
    """
    if not (settings.langchain_tracing_v2 and settings.langsmith_api_key):
        return

    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"] = settings.langsmith_api_key
    os.environ["LANGCHAIN_PROJECT"] = settings.langsmith_project
    logger.info("LangSmith tracing enabled (project=%s)", settings.langsmith_project)
