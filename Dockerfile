FROM python:3.12-slim

WORKDIR /app

# Зависимости отдельно для кэша слоёв
COPY pyproject.toml .
RUN pip install --no-cache-dir uv && uv sync --no-dev

COPY . .

EXPOSE 8000

# Railway сам передаёт PORT
CMD ["sh", "-c", "uv run uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
