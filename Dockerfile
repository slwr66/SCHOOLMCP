# MCP Server для EdTech / Lesson Kit
# Docker образ для запуска MCP сервера

FROM python:3.11-slim

# Метаданные
LABEL maintainer="MCP EdTech Team"
LABEL description="MCP Server for EdTech / Lesson Kit - Cloud.ru / Evolution AI Agents"
LABEL version="0.3.3"

# Установка рабочей директории
WORKDIR /app

# Устанавливаем системные зависимости для Aspose Slides
# Aspose Slides for Python via .NET требует некоторые библиотеки
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgdiplus \
    libc6-dev \
    && rm -rf /var/lib/apt/lists/*

# Копируем файлы зависимостей первыми для лучшего кэширования
COPY requirements.txt pyproject.toml ./

# Устанавливаем зависимости
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Копируем остальной код проекта
COPY mcp_instance.py server.py ./
COPY tools/ ./tools/
COPY templates/ ./templates/

# Создаем директорию для экспорта презентаций и квизов
RUN mkdir -p exports

# Переменные окружения по умолчанию
ENV PYTHONUNBUFFERED=1
ENV EXPORTS_DIR=/app/exports

# Опционально: путь к лицензии Aspose Slides
# ENV ASPOSE_LICENSE_PATH=/app/Aspose.Slides.lic

# Health check для мониторинга работоспособности
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=5)" || exit 1

# Точка входа
CMD ["python", "server.py"]
