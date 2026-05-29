# Домовой

Telegram-бот помощник по двум доменам: **кулинария** и **бытовые ситуации**.
Голос или текст → определение домена → multi-agent система → конкретный практический ответ.

Подробности архитектуры и продуктовые принципы — в [CLAUDE.md](CLAUDE.md).

## Запуск локально

```bash
# 1. Зависимости
uv sync

# 2. Конфигурация
cp .env.example .env
# Заполнить: BOT_TOKEN, GROQ_API_KEY, OPENROUTER_API_KEY, DATABASE_URL

# 3. БД
docker compose up -d postgres
uv run alembic upgrade head

# 4. Локальная разработка (polling вместо webhook)
uv run python -m src.dev

# 5. Production-режим (webhook)
uv run uvicorn src.main:app --host 0.0.0.0 --port 8000
```

## Статус

v0.1 — closed beta. Скелет: webhook, БД, Router agent, кулинарный и бытовой пайплайны.
