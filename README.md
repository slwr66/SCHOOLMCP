# MCP Server для EdTech / Lesson Kit

MCP-сервер для бизнес-агентов (Cloud.ru / Evolution AI Agents) в сфере детских курсов и EdTech. Основная задача — помогать AI-агенту собирать «**Lesson Kit**» — полный набор материалов для урока: учебный контент, иллюстрации, квиз, презентацию и запись в календарь.

## 🎯 Основные возможности

| Tool | Назначение |
|------|------------|
| `wiki_get_material` | Получение учебного материала из вики-источников (Wikibooks, Vikidia, Wikipedia) |
| `get_images` | Подбор иллюстраций через Unsplash API с безопасным поиском для детей |
| `get_quiz` | Генерация викторины с автоматическим переводом на русский язык |
| `export_quiz` | Экспорт викторины в файл (JSON, HTML, CSV) |
| `create_presentation` | Создание презентации Google Slides с текстом и изображениями |
| `schedule_lesson` | Запись урока в Google Calendar |
| `get_text_from_wiki` | Получение полного текста статьи из Wikipedia |
| `search_article` | Поиск статей в Wikipedia |

## 🔗 Как использовать с агентами (Cloud.ru / Evolution AI Agents)

### Схема интеграции

```
┌─────────────┐     ┌──────────────────────┐     ┌─────────────────┐
│ Пользователь│────▶│ AI-Агент (Cloud.ru)  │────▶│ MCP Server      │
│             │     │ Qwen / GPT / другой  │     │ (этот проект)   │
└─────────────┘     └──────────────────────┘     └─────────────────┘
                              │                          │
                              │                          ▼
                              │                  ┌───────────────┐
                              │                  │ Внешние API:  │
                              │                  │ - Wikipedia   │
                              │                  │ - Unsplash    │
                              │                  │ - OpenTDB     │
                              │                  │ - Google Slides│
                              │                  │ - Google Cal  │
                              │                  └───────────────┘
                              ▼
                    ┌──────────────────┐
                    │ Lesson Kit:      │
                    │ • Материал       │
                    │ • Картинки       │
                    │ • Квиз           │
                    │ • Презентация    │
                    │ • Событие в кал. │
                    └──────────────────┘
```

### Пример сценария

1. **Пользователь:** «Подготовь урок по теме 'Солнечная система' для 5 класса»

2. **Агент:** Строит `lesson_plan`, затем последовательно вызывает:
   ```
   wiki_get_material(topic="Солнечная система", language="ru", max_chars=4000)
   get_images(query="солнечная система планеты", count=5, safe_for_kids=True)
   get_quiz(topic="science", amount=10, difficulty="easy")
   create_presentation(
       title="Урок: Солнечная система",
       slides=[
           {"title": "Введение", "text": "Солнечная система...", "image_url": "..."},
           {"title": "Планеты", "text": "8 планет..."}
       ]
   )
   schedule_lesson(
       summary="Урок: Солнечная система",
       start_iso="2025-12-12T14:00:00",
       description="Тема: планеты, орбиты, Солнце",
       location="https://meet.google.com/abc-xyz"
   )
   ```

3. **Результат:** Готовый Lesson Kit с материалом, иллюстрациями, квизом, презентацией и записью в календаре.

## 📦 Установка

### Зависимости

```bash
# С использованием uv (рекомендуется)
uv sync
# или
uv pip install -r requirements.txt

# С использованием pip
pip install -r requirements.txt
```

**Установка uv (если не установлен):**
- Windows: `powershell -c "irm https://astral.sh/uv/install.ps1 | iex"`
- Linux/Mac: `curl -LsSf https://astral.sh/uv/install.sh | sh`

### Настройка переменных окружения

Создайте файл `.env` в корне проекта:

```env
# Unsplash API (для get_images)
UNSPLASH_ACCESS_KEY=your_unsplash_key

# Yandex Translate (для get_quiz — перевод вопросов)
YANDEX_API_KEY=your_yandex_api_key
# или
YANDEX_IAM_TOKEN=your_yandex_iam_token

# Google Calendar API (для schedule_lesson)
GOOGLE_CREDENTIALS_PATH=credentials.json
GOOGLE_TOKEN_PATH=token.json
GOOGLE_CALENDAR_ID=primary

# Google Slides API (для create_presentation)
GOOGLE_SLIDES_CREDENTIALS_PATH=credentials.json
GOOGLE_SLIDES_TOKEN_PATH=slides_token.json
GOOGLE_SERVICE_ACCOUNT_PATH=service_account.json
GOOGLE_SLIDES_AUTH_TYPE=service_account  # или "oauth"
```

#### Получение ключей API

| Сервис | Как получить |
|--------|--------------|
| **Unsplash** | [Unsplash Developers](https://unsplash.com/developers) → Create App → Access Key |
| **Yandex Translate** | [Yandex Cloud Console](https://console.cloud.yandex.ru/) → Translate API → API Key |
| **Google Calendar** | [Google Cloud Console](https://console.cloud.google.com/) → APIs → Calendar API → OAuth 2.0 Client ID → Download JSON |
| **Google Slides** | [Google Cloud Console](https://console.cloud.google.com/) → APIs → Slides API → Service Account или OAuth 2.0 |

#### Настройка Google Calendar

1. Создайте проект в [Google Cloud Console](https://console.cloud.google.com/)
2. Включите **Google Calendar API**
3. Создайте **OAuth 2.0 Client ID** (тип: Desktop App)
4. Скачайте JSON и сохраните как `credentials.json` в корне проекта
5. При первом запуске `schedule_lesson` откроется браузер для авторизации
6. После авторизации будет создан `token.json` для последующих запросов

#### Настройка Google Slides

**Вариант 1: Service Account (рекомендуется для серверов)**
1. Создайте проект в [Google Cloud Console](https://console.cloud.google.com/)
2. Включите **Google Slides API** и **Google Drive API**
3. Создайте **Service Account** → Keys → Add Key → JSON
4. Скачайте JSON и сохраните как `service_account.json`
5. Установите `GOOGLE_SLIDES_AUTH_TYPE=service_account`

**Вариант 2: OAuth 2.0 (для персонального использования)**
1. Создайте **OAuth 2.0 Client ID** (тип: Desktop App)
2. Скачайте JSON как `credentials.json`
3. Установите `GOOGLE_SLIDES_AUTH_TYPE=oauth`
4. При первом запуске откроется браузер для авторизации

## 🚀 Запуск

### Локальный запуск

```bash
# С uv
uv run server.py

# С python
python server.py
```

### Docker (опционально)

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "server.py"]
```

```bash
docker build -t mcp-edtech .
docker run -p 8000:8000 --env-file .env mcp-edtech
```

## 🧪 Тестирование

```bash
# Тест поиска изображений
uv run test_images_mcp.py

# Тест генерации квиза
uv run test_quiz_mcp.py

# Тест Wikipedia
uv run test_wiki_mcp.py

# Тест создания презентаций
uv run test_presentation_mcp.py
```

## 📁 Структура проекта

```
.
├── mcp_instance.py           # Единый экземпляр FastMCP
├── server.py                 # Точка входа MCP-сервера
├── tools/
│   ├── wiki_get_material.py  # Учебный материал из вики
│   ├── get_images.py         # Поиск изображений (Unsplash)
│   ├── get_quiz.py           # Генерация викторины
│   ├── export_quiz.py        # Экспорт квиза в файл
│   ├── create_presentation.py # Создание презентаций (Google Slides)
│   ├── google_slides.py      # Утилиты Google Slides API
│   ├── schedule_lesson.py    # Запись урока в Google Calendar
│   ├── google_calendar.py    # Утилиты Google Calendar API
│   ├── get_text_from_wiki.py # Полный текст из Wikipedia
│   └── utils.py              # Общие утилиты (OpenTDB, Yandex)
├── templates/
│   └── quiz_template.html    # HTML шаблон для экспорта квиза
├── exports/                  # Папка для экспортированных файлов
├── test_*.py                 # Тестовые скрипты
├── requirements.txt          # Python зависимости
├── pyproject.toml            # Конфигурация проекта
└── .env                      # Переменные окружения (не в git!)
```

## 📚 API Tools — подробное описание

### `wiki_get_material`

Получает структурированный учебный материал из вики-источников.

```python
await wiki_get_material(
    topic="Фотосинтез",
    language="ru",      # "ru" или "en"
    max_chars=4000      # Ограничение размера
)
# Возвращает:
{
    "title": "Фотосинтез",
    "summary": "Фотосинтез — процесс...",
    "sections": [
        {"title": "История открытия", "content": "..."},
        {"title": "Механизм", "content": "..."}
    ],
    "source_urls": ["https://ru.wikipedia.org/wiki/..."],
    "source": "wikipedia"
}
```

### `get_images`

Ищет изображения через Unsplash API с поддержкой безопасного поиска.

```python
await get_images(
    query="космос планеты",
    count=5,
    safe_for_kids=True,
    style_hint="photo"  # "photo", "cartoon", "flat", "illustration"
)
# Возвращает:
{
    "items": [
        {
            "url": "https://images.unsplash.com/...",
            "thumb_url": "https://images.unsplash.com/...?w=200",
            "author": "John Doe",
            "source": "unsplash",
            "attribution": "Photo by John Doe on Unsplash"
        }
    ],
    "query": "космос планеты",
    "total_found": 1234
}
```

### `get_quiz`

Генерирует викторину из OpenTDB с автоматическим переводом на русский.

```python
await get_quiz(
    topic="science",
    amount=10,
    difficulty="easy",      # "easy", "medium", "hard"
    question_type="multiple" # "multiple", "boolean"
)
# Возвращает:
{
    "success": True,
    "topic": "science",
    "amount": 10,
    "questions": [
        {
            "question": "Какой газ составляет большую часть атмосферы?",
            "correct_answer": "Азот",
            "incorrect_answers": ["Кислород", "Углекислый газ", "Водород"],
            "all_answers": ["Азот", "Кислород", "Углекислый газ", "Водород"]
        }
    ]
}
```

### `create_presentation`

Создает презентацию Google Slides с текстом и изображениями.

```python
await create_presentation(
    title="Урок: Введение в астрономию",
    slides=[
        {
            "title": "Что такое астрономия?",
            "text": "Астрономия — наука о Вселенной...",
            "image_url": "https://images.unsplash.com/photo-..."  # опционально
        },
        {
            "title": "Солнечная система",
            "text": "Солнечная система состоит из 8 планет..."
        }
    ],
    use_service_account=True  # или False для OAuth
)
# Возвращает:
{
    "presentation_id": "1abc...",
    "presentation_url": "https://docs.google.com/presentation/d/1abc.../edit",
    "slides_count": 2
}
```

### `schedule_lesson`

Создает событие урока в Google Calendar.

```python
await schedule_lesson(
    summary="Урок: Основы Python",
    start_iso="2025-12-10T15:00:00",
    end_iso=None,              # Автоматически: start + 60 мин
    timezone="Europe/Moscow",
    description="Тема: переменные, циклы",
    location="https://meet.google.com/..."
)
# Возвращает:
{
    "event_id": "abc123xyz",
    "html_link": "https://calendar.google.com/event?eid=...",
    "start": "2025-12-10T15:00:00",
    "end": "2025-12-10T16:00:00"
}
```

## 📋 Требования

- Python 3.10+
- FastMCP >= 0.9.0
- httpx >= 0.25.0
- google-api-python-client >= 2.100.0
- google-auth-oauthlib >= 1.1.0

## 📄 Лицензия

MIT License

---

**Разработано для интеграции с Cloud.ru / Evolution AI Agents**
