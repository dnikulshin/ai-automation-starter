FROM python:3.11-slim-bookworm

WORKDIR /app

# Системные зависимости
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Копируем зависимости и устанавливаем их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код
COPY src/ ./src/
COPY prompts/ ./prompts/

# Создаём директории для данных и логов
RUN mkdir -p data/input data/processed data/output logs

# Запускаем от не-root пользователя (безопасность)
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Health check (опционально, если запускать в оркестраторе)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import src.config; src.config.AppConfig()" || exit 1

# Точка входа
CMD ["python", "-m", "src"]