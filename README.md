# MCP Servers (Images & Quiz)

Два полноценных MCP сервера для работы с изображениями и генерации викторин.

## Установка

1. Установите зависимости:
```bash
# С использованием uv (рекомендуется)
uv sync
# или
uv pip install -r requirements.txt

# С использованием pip
pip install -r requirements.txt
```

**Примечание:** Если у вас не установлен `uv`, вы можете установить его:
- Windows: `powershell -c "irm https://astral.sh/uv/install.ps1 | iex"`
- Linux/Mac: `curl -LsSf https://astral.sh/uv/install.sh | sh`

**Если PowerShell не видит `uv` после установки:**
1. `uv` устанавливается в `%USERPROFILE%\.local\bin\`
2. Добавьте этот путь в PATH:
   - Запустите скрипт: `.\setup_uv_path.ps1`
   - Или вручную добавьте `%USERPROFILE%\.local\bin` в переменную окружения PATH
3. **Перезапустите PowerShell/Cursor**, чтобы изменения вступили в силу
4. Проверьте: `uv --version`

2. Создайте файл `.env` на основе `.env.example` и добавьте ваши API ключи:
```
UNSPLASH_ACCESS_KEY=your_key_here
YANDEX_IAM_TOKEN=your_token_here
```

## Запуск

```bash
uv run server.py
# или
python server.py
```

## Инструменты

### Images-MCP

- **get_images**: Поиск изображений через Unsplash API
  - Параметры: `topic` (str), `prompts` (list[str], опционально), `count` (int, 1-10)

### Quiz-MCP

- **get_quiz**: Генерация викторин на заданную тему с автоматическим переводом на русский
  - Параметры: `topic` (str), `amount` (int, 1-50), `difficulty` (str, опционально), `question_type` (str, опционально)

- **export_quiz**: Экспорт викторины в файл (JSON, HTML, CSV)
  - Параметры: `quiz_data` (dict), `format` (str: "json", "html", "csv"), `filename` (str, опционально)

## Тестирование

```bash
# Тест Images-MCP
uv run test_images_mcp.py

# Тест Quiz-MCP
uv run test_quiz_mcp.py
```

## Структура проекта

```
.
├── mcp_instance.py          # Единый экземпляр FastMCP
├── server.py               # Точка входа
├── tools/
│   ├── get_images.py       # Инструмент поиска изображений
│   ├── get_quiz.py         # Инструмент генерации викторин
│   ├── export_quiz.py      # Инструмент экспорта
│   └── utils.py            # Утилиты для работы с API
├── templates/
│   └── quiz_template.html  # HTML шаблон для экспорта
├── exports/                # Папка для экспортированных файлов
└── test_*.py               # Тестовые скрипты
```

## Требования

- Python 3.10+
- FastMCP
- httpx
- python-dotenv
- aiofiles
- jinja2

