# Домовой

> Telegram-бот помощник по двум доменам: кулинария и бытовые ситуации. Пользователь говорит голосом или пишет текстом - бот определяет домен, задаёт уточняющие вопросы и даёт конкретный практический ответ через multi-agent систему.

**Целевая аудитория:** взрослые люди 25-55 лет. Те кто стоит у холодильника и не знает что приготовить. Те у кого что-то сломалось дома и непонятно что делать. Им нужен конкретный ответ, а не SEO-статья на 10 тысяч слов.

**Главный инсайт:** голосовой ввод снижает порог входа до нуля. Не нужно формулировать запрос - просто говоришь как другу: "у меня есть курица и картошка, что приготовить быстро?" или "кран на кухне капает, как починить".

**Связь с другими проектами автора:** первый из трёх запланированных multi-agent продуктов. После Домового - AI-помощник для изучения языков (ElevenLabs TTS + STT) и AI-помощник для чтения сложных книг.

---

## Что делает

**Домен 1: Кулинария**
- Принимает голос или текст с перечнем продуктов
- Предлагает 2-3 варианта блюд под имеющиеся ингредиенты
- Учитывает время готовки, количество порций, диетические ограничения
- Отвечает на уточняющие вопросы по рецепту
- Предлагает замены недостающих ингредиентов
- Составляет список что докупить для расширения вариантов

**Домен 2: Бытовые ситуации**
- Принимает описание проблемы голосом или текстом
- Классифицирует тип ситуации (сантехника, электрика, уборка, бытовая техника, юридическое)
- Задаёт уточняющие вопросы для диагностики
- Даёт пошаговое решение самому (DIY)
- Говорит когда нужен специалист и какой именно
- Оценивает примерную стоимость ремонта/решения
- Объясняет как избежать в будущем

---

## Принципы продукта

- **Голос как основной режим** - STT через Groq Whisper. Текст тоже работает
- **Конкретность** - не "можно попробовать X или Y", а "вот рецепт, вот шаги"
- **Уточняй прежде чем советовать** - Router agent задаёт 1-2 уточняющих вопроса если ситуация неоднозначна
- **Дисклеймер для серьёзного** - электрика под напряжением, юридические вопросы, медицинские симптомы - всегда предупреждать "здесь лучше специалист"
- **Простой язык** - без кулинарных терминов типа "бланшировать", без строительного жаргона. Как объяснил бы друг
- **Сначала работает, потом красиво** - v0.1 без фото холодильника (vision дорогая), только текст и голос

---

## Архитектура

```
Пользователь (голос или текст в Telegram)
        ↓
Telegram Webhook → FastAPI
        ↓
[STT Agent] - Groq Whisper API
(только если пришло голосовое сообщение)
        ↓
[Router Agent] - LLM определяет домен
        ├── "cooking" → Cooking Pipeline
        ├── "home" → Home Pipeline
        └── "unclear" → Clarification (один уточняющий вопрос)

Cooking Pipeline:
├── [Inventory Agent] - извлекает список продуктов из сообщения
├── [Preference Agent] - учитывает время/порции/ограничения
├── [Recipe Agent] - подбирает 2-3 рецепта
├── [Substitution Agent] - чем заменить недостающее
└── [Shopping Agent] - что докупить

Home Pipeline:
├── [Classifier Agent] - тип ситуации
├── [Diagnosis Agent] - уточняющие вопросы
├── [DIY Agent] - пошаговое решение самому
├── [Pro Agent] - когда и какой специалист нужен
├── [Cost Agent] - примерная стоимость
└── [Prevention Agent] - как избежать повторения

        ↓
Финальный ответ пользователю (текст)
```

**Оркестрация:** LangGraph - граф с явными переходами между агентами, state передаётся между узлами, условные выходы.

---

## Стек

**Backend:**
- Python 3.12
- FastAPI + Uvicorn (webhook endpoint)
- aiogram 3 (Telegram bot)
- PostgreSQL + SQLAlchemy 2.0 async + Alembic
- LangGraph (multi-agent оркестрация)
- LangSmith (трейсинг в продакшне)

**AI:**
- Groq API - Whisper Large v3 для STT (быстро, дёшево)
- DeepSeek через OpenRouter - основной LLM (дёшево, хорошее качество)
- Claude Haiku как fallback (через OpenRouter)

**LLM абстракция:**
- Единый LLMProvider interface
- Смена провайдера через .env без изменения кода

**Деплой:**
- Railway (FastAPI сервис + PostgreSQL)
- Cloudflare (DNS + SSL если будет домен)
- Webhook режим (не polling)

---

## Модель данных

```sql
-- Пользователи
users
  id              bigint PK
  telegram_id     bigint UNIQUE NOT NULL
  username        text
  first_name      text
  language_code   text DEFAULT 'ru'
  created_at      timestamp DEFAULT now()
  last_active_at  timestamp

-- Настройки и предпочтения пользователя
user_preferences
  id              bigint PK
  user_id         bigint FK users(id) ON DELETE CASCADE
  -- кулинарные предпочтения
  dietary_restrictions text[]              -- ["вегетарианство", "без глютена"]
  disliked_ingredients text[]             -- что не любит
  default_portions     int DEFAULT 2      -- на сколько человек обычно готовит
  cooking_skill        text DEFAULT 'beginner' -- "beginner" | "intermediate" | "advanced"
  -- общие
  preferred_language   text DEFAULT 'ru'
  updated_at           timestamp

-- История диалогов (для контекста в рамках сессии)
conversations
  id              bigint PK
  user_id         bigint FK users(id) ON DELETE CASCADE
  domain          text                    -- "cooking" | "home" | "unclear"
  started_at      timestamp DEFAULT now()
  ended_at        timestamp
  messages_count  int DEFAULT 0

-- Сообщения
messages
  id              bigint PK
  conversation_id bigint FK conversations(id) ON DELETE CASCADE
  role            text                    -- "user" | "assistant"
  content         text
  is_voice        bool DEFAULT false      -- было ли голосовым
  created_at      timestamp DEFAULT now()

-- Аналитика (без персданных)
events
  id              bigint PK
  user_id         bigint FK users(id)
  event_type      text                    -- "voice_received" | "recipe_generated" | "home_advice_given" | "domain_unclear"
  domain          text
  metadata        jsonb                   -- агрегированные данные, не контент
  created_at      timestamp DEFAULT now()

-- Конфигурация (гибкие лимиты)
config
  key             text PK
  value           jsonb

-- Примеры значений:
-- ('beta_mode', 'true')                    -- всё бесплатно на старте
-- ('free_requests_per_day', '20')          -- лимит бесплатных запросов
-- ('voice_enabled', 'true')               -- можно выключить если Groq дорого
-- ('max_conversation_turns', '10')         -- макс сообщений в одном диалоге
```

---

## Multi-agent система подробно

### Router Agent

**Задача:** определить домен из первого сообщения пользователя.

```
Промпт: Ты роутер. Определи к какому домену относится запрос.

Домены:
- cooking: вопросы о еде, рецептах, продуктах, приготовлении
- home: бытовые проблемы, поломки, уборка, ремонт
- unclear: непонятно, нужно уточнить

Верни JSON: {"domain": "cooking"|"home"|"unclear", "confidence": 0-1}

Если unclear - сформулируй один уточняющий вопрос.
```

**Граничные случаи:**
- "Как вывести пятно от соуса с одежды" - home (уборка), не cooking
- "Что приготовить на день рождения на 10 человек" - cooking
- "Сломалась духовка" - home, даже если контекст кулинарный

---

### Cooking Pipeline

**Inventory Agent**

Извлекает список продуктов из свободного текста:

```
Вход: "у меня есть куриное филе, картошка, лук, морковь,
       немного сметаны и укроп"

Выход (JSON):
{
  "ingredients": ["куриное филе", "картошка", "лук", "морковь", "сметана", "укроп"],
  "approximate_quantities": {"куриное филе": "~500г", "картошка": "немного"},
  "missing_info": ["количество порций", "время готовки"]
}
```

**Preference Agent**

Учитывает сохранённые предпочтения + данные из текущего запроса:

```
Вход: inventory + user_preferences из БД + текущий запрос

Выход:
{
  "portions": 2,
  "max_time_minutes": 30,
  "restrictions": [],
  "skill_level": "beginner"
}
```

**Recipe Agent**

Основной агент. Генерирует 2-3 рецепта.

```
Промпт включает:
- список доступных ингредиентов
- предпочтения и ограничения
- уровень готовки
- просьба: дать КОНКРЕТНЫЕ рецепты с шагами, не "можно приготовить X"

Формат ответа:
Рецепт 1: Курица со сметаной
Время: 25 минут
Сложность: простой

Шаги:
1. Нарезать филе кусочками по 3-4 см
2. Обжарить на среднем огне 7-10 минут
...

Подача: ...

---
Рецепт 2: ...
```

**Substitution Agent** (если пользователь спрашивает "а если нет X?")

```
Вход: "нет сметаны"
Контекст: рецепт "Курица со сметаной"

Выход: "Сметану можно заменить:
- Греческий йогурт (1:1, вкус чуть кислее)
- Сливки 20% (1:1, нежнее)
- Майонез (половину дозы, будет сытнее)
Без молочного: кокосовые сливки (другой вкус но рецепт работает)"
```

---

### Home Pipeline

**Classifier Agent**

Определяет тип бытовой проблемы:

```
Категории:
- plumbing: трубы, краны, унитаз, душ, водонагреватель
- electrical: розетки, выключатели, проводка, автоматы
- appliances: стиральная машина, холодильник, плита, посудомойка
- cleaning: пятна, запахи, уборка, дезинфекция
- structure: стены, полы, потолок, окна, двери
- legal: соседи, управляющая компания, ЖКХ споры
- other: всё остальное

Выход: {"category": "plumbing", "urgency": "high"|"medium"|"low"}
```

Urgency важен - если "urgency: high" (затопление, короткое замыкание) - первый ответ это экстренные действия, не диагностика.

**Diagnosis Agent**

Задаёт 1-2 уточняющих вопроса если нужно:

```
Пользователь: "кран капает"

Агент понимает что нужно знать:
- какой кран (смеситель в ванной/кухне или шаровый)?
- откуда капает (из носика или из-под ручки)?

Вопрос: "Где именно капает - из носика крана или из-под ручки управления?"
(один вопрос, не оба сразу - не перегружать пользователя)
```

**DIY Agent**

Пошаговое решение. Самый важный агент.

```
Промпт включает:
- тип проблемы и детали из diagnosis
- уровень сложности (всегда объяснять как для новичка)
- список инструментов которые понадобятся
- дисклеймер для опасных задач

Формат:
Что нужно: отвёртка крестовая, новая прокладка (продаётся в любом хозмаге за 50р)

Шаги:
1. Перекройте воду под раковиной (кран справа или слева от трубы)
2. Откройте кран чтобы стекла оставшаяся вода
3. Снимите декоративный колпачок ручки (обычно просто тянется вверх)
...

Время: ~20 минут
Сложность: легко, справится любой

⚠ Если не уверены - лучше вызвать сантехника.
   Неправильная замена может привести к протечке.
```

**Pro Agent**

Когда и какой специалист:

```
Вывод когда DIY не подходит:
- электрика (всё кроме замены лампочки)
- газовое оборудование (всегда)
- несущие конструкции
- когда DIY усугубит проблему

Формат:
"Здесь нужен сантехник. Это займёт 30-60 минут,
стоит обычно 1500-3000р в Москве.

Что сказать мастеру: 'течёт обратный клапан на стиральной машине'"
```

**Cost Agent**

Примерная стоимость решения:

```
Для DIY: стоимость материалов
Для мастера: диапазон цен по Москве с пометкой "цены ориентировочные"

Всегда с дисклеймером: "Цены ориентировочные, уточняйте у мастера"
```

**Prevention Agent**

Как избежать в будущем. Короткий, в конце ответа:

```
"Чтобы не повторилось:
- Раз в год проверяйте прокладки в смесителях
- Если кран начал капать - лучше поменять сразу, 
  потом сложнее"
```

---

## Обработка голосовых сообщений

```python
# handlers/voice.py

@dp.message(F.voice)
async def handle_voice(message: Message):
    # 1. Скачать аудио
    file = await bot.get_file(message.voice.file_id)
    audio_data = await bot.download_file(file.file_path)

    # 2. Транскрибировать через Groq Whisper
    transcript = await stt_service.transcribe(
        audio_data=audio_data,
        language="ru"
    )

    # 3. Обработать как обычный текст
    await process_message(message, text=transcript)

# stt/groq_whisper.py

class GroqSTTService:
    async def transcribe(self, audio_data: bytes, language: str = "ru") -> str:
        # Groq Whisper Large v3
        # ~$0.111 за час аудио
        # Голосовое в Telegram обычно 5-30 секунд = копейки
        ...
```

---

## FSM диалог (Finite State Machine)

aiogram 3 FSM для управления состоянием диалога:

```python
class ConversationStates(StatesGroup):
    idle = State()                    # начальное состояние
    clarifying_domain = State()       # уточняем домен
    cooking_clarifying = State()      # уточняем кулинарный запрос
    cooking_answering = State()       # ответили, ждём follow-up
    home_diagnosing = State()         # диагностируем проблему
    home_answering = State()          # ответили, ждём follow-up

# Переходы:
# idle → clarifying_domain (если Router вернул "unclear")
# idle → cooking_clarifying (если cooking но мало данных)
# idle → cooking_answering (если cooking и данных достаточно)
# idle → home_diagnosing (если home и нужно уточнить)
# idle → home_answering (если home и ситуация ясна)
# любое состояние → idle (команда /start или /reset)
```

---

## Деплой: Railway + Cloudflare

### Railway конфигурация

**railway.toml** в корне проекта:

```toml
[build]
builder = "DOCKERFILE"
dockerfilePath = "Dockerfile"

[deploy]
startCommand = "uvicorn src.main:app --host 0.0.0.0 --port $PORT"
healthcheckPath = "/health"
healthcheckTimeout = 30
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 3

[[services]]
name = "domovoy-bot"

[[services]]
name = "domovoy-db"
```

**Dockerfile** (оптимизированный для Railway):

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Зависимости отдельно для кэша слоёв
COPY pyproject.toml .
RUN pip install --no-cache-dir uv && uv sync --no-dev

COPY . .

EXPOSE 8000

# Railway сам передаёт PORT
CMD ["sh", "-c", "uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
```

### Webhook setup

```python
# src/main.py

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from aiogram.types import Update

@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    webhook_url = f"{settings.base_url}/webhook"
    await bot.set_webhook(
        url=webhook_url,
        secret_token=settings.webhook_secret,  # защита от левых запросов
        drop_pending_updates=True
    )
    await db.connect()
    yield
    # shutdown
    await bot.delete_webhook()
    await db.disconnect()

app = FastAPI(lifespan=lifespan)

@app.post("/webhook")
async def webhook(request: Request):
    # проверка secret_token
    if request.headers.get("X-Telegram-Bot-Api-Secret-Token") != settings.webhook_secret:
        return {"error": "unauthorized"}

    update = Update(**await request.json())
    await dp.process_update(update)
    return {"ok": True}

@app.get("/health")
async def health():
    return {"status": "ok", "service": "domovoy"}
```

### Переменные окружения (.env.example)

```bash
# Telegram
BOT_TOKEN=...
WEBHOOK_SECRET=...          # случайная строка, защита webhook

# Base URL (Railway даёт автоматически, или Cloudflare домен)
BASE_URL=https://domovoy.yourdomain.com

# Database (Railway даёт автоматически при добавлении PostgreSQL)
DATABASE_URL=postgresql+asyncpg://...

# AI Providers
GROQ_API_KEY=...            # для STT (Whisper)
OPENROUTER_API_KEY=...      # для LLM (DeepSeek)

# Optional
LANGSMITH_API_KEY=...       # для трейсинга (можно без него)
LANGSMITH_PROJECT=domovoy

# Config
DEBUG=false
LOG_LEVEL=INFO
```

### Cloudflare (если есть домен)

```
1. Добавить домен в Cloudflare
2. DNS запись: CNAME domovoy → your-app.up.railway.app
3. Proxy: включить (оранжевое облако)
4. SSL/TLS: Full (strict)
5. BASE_URL в Railway = https://domovoy.yourdomain.com
```

**Без домена:** Railway даёт `https://domovoy-bot-production.up.railway.app` - это тоже валидный HTTPS для webhook.

---

## Структура репозитория

```
domovoy/
├── README.md
├── CLAUDE.md                      # этот файл
├── CHANGELOG.md
├── Dockerfile
├── railway.toml
├── pyproject.toml
├── .env.example
├── .gitignore
│
├── src/
│   ├── main.py                    # FastAPI app + webhook endpoint
│   ├── config.py                  # pydantic-settings
│   │
│   ├── bot/                       # aiogram 3
│   │   ├── __init__.py
│   │   ├── setup.py               # Bot + Dispatcher инициализация
│   │   ├── states.py              # FSM States
│   │   ├── handlers/
│   │   │   ├── start.py           # /start, /help, /reset
│   │   │   ├── text.py            # текстовые сообщения
│   │   │   └── voice.py           # голосовые сообщения
│   │   └── middlewares/
│   │       ├── user.py            # создаёт/обновляет юзера в БД
│   │       ├── logging.py
│   │       └── rate_limit.py
│   │
│   ├── agents/                    # multi-agent система
│   │   ├── __init__.py
│   │   ├── graph.py               # LangGraph граф (главный оркестратор)
│   │   ├── state.py               # TypedDict для state графа
│   │   ├── router.py              # Router agent
│   │   ├── cooking/
│   │   │   ├── inventory.py       # Inventory agent
│   │   │   ├── preference.py      # Preference agent
│   │   │   ├── recipe.py          # Recipe agent
│   │   │   └── substitution.py   # Substitution agent
│   │   └── home/
│   │       ├── classifier.py      # Classifier agent
│   │       ├── diagnosis.py       # Diagnosis agent
│   │       ├── diy.py             # DIY agent
│   │       ├── pro.py             # Pro agent
│   │       ├── cost.py            # Cost agent
│   │       └── prevention.py     # Prevention agent
│   │
│   ├── llm/                       # абстракция LLM
│   │   ├── base.py                # LLMProvider protocol
│   │   ├── openrouter.py          # DeepSeek через OpenRouter
│   │   └── prompts/
│   │       ├── router.md
│   │       ├── cooking/
│   │       │   ├── inventory.md
│   │       │   ├── recipe.md
│   │       │   └── substitution.md
│   │       └── home/
│   │           ├── classifier.md
│   │           ├── diagnosis.md
│   │           ├── diy.md
│   │           └── pro.md
│   │
│   ├── stt/                       # Speech-to-Text
│   │   ├── base.py                # STTProvider protocol
│   │   └── groq_whisper.py        # Groq Whisper реализация
│   │
│   ├── db/                        # база данных
│   │   ├── models.py              # SQLAlchemy модели
│   │   ├── session.py             # async session factory
│   │   └── repositories/
│   │       ├── user_repo.py
│   │       ├── conversation_repo.py
│   │       └── config_repo.py
│   │
│   ├── domain/                    # чистые pydantic типы
│   │   ├── user.py
│   │   └── conversation.py
│   │
│   └── services/                  # бизнес-логика
│       ├── user_service.py
│       ├── conversation_service.py
│       └── config_service.py
│
├── alembic/
│   ├── env.py
│   └── versions/
│
└── tests/
    ├── unit/
    │   ├── test_router_agent.py
    │   ├── test_inventory_agent.py
    │   └── test_classifier_agent.py
    ├── integration/
    └── golden/                    # эталонные кейсы для агентов
        ├── cooking_cases.yaml
        └── home_cases.yaml
```

---

## Roadmap

### v0.1 - Closed Beta (3 недели)

**Неделя 1: Скелет и роутинг**
- FastAPI + aiogram 3 в webhook-режиме
- Деплой на Railway (сразу, не потом)
- PostgreSQL + модели + миграции
- Groq STT для голосовых
- Router agent: определяет домен
- Базовые команды: /start, /help, /reset

**Неделя 2: Кулинарный домен**
- Inventory agent
- Recipe agent (2-3 рецепта)
- Substitution agent
- FSM для уточнений
- Тестирование на 5-10 реальных запросах

**Неделя 3: Бытовой домен**
- Classifier + Diagnosis agents
- DIY agent (пошаговые инструкции)
- Pro agent (когда вызывать мастера)
- Prevention agent
- Финальное тестирование, фиксы

**Что НЕ входит в v0.1:**
- Фото холодильника (vision)
- Preference сохранение в БД (просто спрашивать каждый раз)
- Shopping list агент
- Cost агент
- Монетизация
- Статистика и аналитика

---

### v0.2 - Public Beta

- Сохранение предпочтений пользователя (dietary restrictions, порции)
- Shopping list агент
- Cost агент для бытовых ситуаций
- История рецептов (избранное)
- Telegram Stars монетизация (лимит бесплатных запросов)
- Базовая аналитика (какие запросы популярны)

---

### v0.3 - Features

- Фото холодильника через vision-модель
- Голосовые ответы бота (TTS) - опционально
- Расширение бытового домена: юридические вопросы с соседями/ЖКХ
- Кулинарный план на неделю
- Inline-кнопки для быстрых ответов (Ещё рецепт / Список покупок / Другая ситуация)

---

## Безопасность

### Данные пользователей
- Не храним содержимое голосовых сообщений после транскрипции
- Не храним тексты сообщений дольше чем нужно для контекста диалога (24 часа)
- В логи не попадают тексты запросов, только метаданные (domain, event_type)
- 152-ФЗ: при росте до публичного продукта - хостинг в РФ (Yandex Cloud / Selectel)

### Webhook защита
- Secret token в каждом запросе от Telegram
- Проверка на каждый входящий запрос

### Rate limiting
- Middleware в aiogram: не более 20 запросов в день на бесплатном плане
- Экспоненциальный бэкофф при ошибках от LLM-провайдеров

### Ответственность
- Для электрики под напряжением, газа, медицинских симптомов - всегда дисклеймер
- "Это информация для общего понимания. При сомнениях - обратитесь к специалисту"

---

## Принципы работы с LLM

### Промпты как код
- Все промпты в `src/llm/prompts/*.md`
- Версионируются в git
- Изменения через PR

### Structured output
- Router agent возвращает JSON (domain + confidence)
- Inventory agent возвращает JSON (список продуктов)
- Все остальные агенты - свободный текст для пользователя

### Защита от галлюцинаций
- DIY agent: явный запрет выдумывать стоимости без пометки "ориентировочно"
- Recipe agent: использовать только указанные ингредиенты, не добавлять "само собой разумеющееся"
- Home agent: если не знает категорию - спросить, не угадывать

### Eval framework
- Golden dataset: 20 кулинарных + 20 бытовых эталонных запросов
- Регресс-тесты после изменения промптов
- Метрика: domain_accuracy (правильно ли определил домен), user_satisfaction (субъективно)

---

## Запуск локально

```bash
# 1. Клонируем
git clone https://github.com/hitprim/domovoy.git
cd domovoy

# 2. Зависимости
uv sync

# 3. Конфигурация
cp .env.example .env
# Заполнить: BOT_TOKEN, GROQ_API_KEY, OPENROUTER_API_KEY, DATABASE_URL

# 4. БД
docker compose up -d postgres
uv run alembic upgrade head

# 5. Для локальной разработки - polling вместо webhook
uv run python -m src.dev  # отдельный entrypoint с polling

# Для тестирования webhook локально:
# ngrok http 8000
# BASE_URL=https://xxxx.ngrok.io в .env

# 6. Production-режим (webhook)
uv run uvicorn src.main:app --host 0.0.0.0 --port 8000
```

---

## Заметки автора

**Почему Домовой:** название отсылает к домашнему духу-помощнику из русского фольклора. Запоминается, ассоциируется с домом и помощью по хозяйству. Уникально для рынка.

**Почему повар + быт в одном:** оба домена про повседневную жизнь дома. Один бот - одна точка входа. Не нужно держать в голове "какой бот для чего". После v0.1 видно будет - какой домен популярнее, туда и фокус.

**Почему без фото:** Claude Vision и GPT-4V стоят денег за каждый вызов. На старте важнее собрать пользователей и понять насколько продукт нужен. Фото - v0.2 когда будет монетизация.

**Railway с первого дня:** деплоить сразу, не откладывать. Бот запущенный в продакшне это другой опыт - реальная обработка ошибок, реальная нагрузка, реальные проблемы с Railway которые лучше решать по одной.

**После Домового:** AI-помощник для изучения языков (ElevenLabs TTS + STT + оценка произношения) и AI-помощник для чтения сложных книг. Домовой - самый простой из трёх технически, хорошая точка старта.
