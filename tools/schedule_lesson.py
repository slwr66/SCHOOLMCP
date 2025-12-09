"""
Инструмент для планирования уроков через Google Calendar API.
"""
from typing import Dict, Optional
from pydantic import Field

from mcp_instance import mcp
from tools.google_calendar import create_calendar_event


@mcp.tool()
async def schedule_lesson(
    summary: str = Field(..., description="Заголовок урока (например, 'Урок: Основы алгоритмов')"),
    start_iso: str = Field(..., description="Начало в формате ISO 8601 (например, '2025-12-10T15:00:00')"),
    end_iso: Optional[str] = Field(None, description="Конец в формате ISO 8601. Если None — start + 60 минут"),
    timezone: str = Field("Europe/Moscow", description="Часовой пояс (например, 'Europe/Moscow')"),
    description: Optional[str] = Field(None, description="Описание урока (ссылки на материалы, план и т.д.)"),
    location: Optional[str] = Field(None, description="Место проведения или ссылка на онлайн-занятие")
) -> Dict:
    """
    Создать событие урока в Google Calendar.
    
    Инструмент позволяет запланировать урок с указанием времени, описания и места.
    Идеально подходит для интеграции с образовательными агентами, которые
    автоматически планируют занятия после подготовки материалов.
    
    Args:
        summary: Заголовок урока (например, 'Урок: Основы алгоритмов').
        start_iso: Начало урока в формате ISO 8601 (например, '2025-12-10T15:00:00').
        end_iso: Конец урока в формате ISO 8601. Если не указано, вычисляется как start + 60 минут.
        timezone: Часовой пояс (по умолчанию 'Europe/Moscow').
        description: Описание урока — ссылки на материалы, план занятия и т.д.
        location: Место проведения: офлайн-адрес или ссылка на онлайн-занятие (Zoom, Meet).
    
    Returns:
        Словарь с информацией о созданном событии:
        {
            "event_id": str,      # ID события в Google Calendar
            "html_link": str,     # Ссылка на событие в календаре
            "start": str,         # Время начала
            "end": str            # Время окончания
        }
        
        В случае ошибки:
        {
            "error": str          # Описание ошибки
        }
    
    Example:
        >>> await schedule_lesson(
        ...     summary="Урок: Введение в Python",
        ...     start_iso="2025-12-10T15:00:00",
        ...     description="План урока: переменные, типы данных, операторы",
        ...     location="https://meet.google.com/abc-defg-hij"
        ... )
        {
            "event_id": "abc123...",
            "html_link": "https://calendar.google.com/event?eid=...",
            "start": "2025-12-10T15:00:00",
            "end": "2025-12-10T16:00:00"
        }
    """
    # Валидация входных данных
    if not summary or not summary.strip():
        return {"error": "Заголовок урока (summary) не может быть пустым."}
    
    if not start_iso or not start_iso.strip():
        return {"error": "Время начала (start_iso) обязательно для указания."}
    
    # Базовая проверка формата ISO
    if "T" not in start_iso:
        return {
            "error": "Неверный формат времени начала. Используйте ISO 8601: '2025-12-10T15:00:00'"
        }
    
    if end_iso and "T" not in end_iso:
        return {
            "error": "Неверный формат времени окончания. Используйте ISO 8601: '2025-12-10T16:00:00'"
        }
    
    # Создаем событие через Google Calendar API
    result = await create_calendar_event(
        summary=summary.strip(),
        start_iso=start_iso.strip(),
        end_iso=end_iso.strip() if end_iso else None,
        timezone=timezone,
        description=description.strip() if description else None,
        location=location.strip() if location else None,
    )
    
    return result

