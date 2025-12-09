"""
Утилиты для работы с Google Calendar API.
Обеспечивает создание и управление событиями календаря.
"""
import os
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Пути к файлам учетных данных
GOOGLE_CREDENTIALS_PATH = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")
GOOGLE_TOKEN_PATH = os.getenv("GOOGLE_TOKEN_PATH", "token.json")
GOOGLE_CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID", "primary")

# Scopes для Google Calendar API
SCOPES = ["https://www.googleapis.com/auth/calendar.events"]


def _get_calendar_service() -> Any:
    """
    Создает и возвращает сервис Google Calendar API.
    
    Returns:
        Объект сервиса Google Calendar или None при ошибке.
        
    Raises:
        ImportError: Если Google библиотеки не установлены.
        FileNotFoundError: Если credentials.json не найден.
    """
    try:
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build
    except ImportError as e:
        raise ImportError(
            "Google API библиотеки не установлены. "
            "Выполните: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib"
        ) from e
    
    creds = None
    
    # Проверяем существующий токен
    if os.path.exists(GOOGLE_TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(GOOGLE_TOKEN_PATH, SCOPES)
    
    # Если нет валидных учетных данных, запрашиваем авторизацию
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(GOOGLE_CREDENTIALS_PATH):
                raise FileNotFoundError(
                    f"Файл учетных данных не найден: {GOOGLE_CREDENTIALS_PATH}. "
                    "Скачайте credentials.json из Google Cloud Console."
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                GOOGLE_CREDENTIALS_PATH, SCOPES
            )
            creds = flow.run_local_server(port=0)
        
        # Сохраняем токен для последующего использования
        with open(GOOGLE_TOKEN_PATH, "w") as token:
            token.write(creds.to_json())
    
    return build("calendar", "v3", credentials=creds)


def parse_iso_datetime(iso_string: str, timezone: str) -> Dict[str, str]:
    """
    Преобразует ISO 8601 строку в формат для Google Calendar API.
    
    Args:
        iso_string: Дата/время в формате ISO 8601.
        timezone: Часовой пояс.
    
    Returns:
        Словарь с dateTime и timeZone для Google Calendar API.
    """
    return {
        "dateTime": iso_string,
        "timeZone": timezone
    }


def calculate_end_time(start_iso: str, duration_minutes: int = 60) -> str:
    """
    Вычисляет время окончания события.
    
    Args:
        start_iso: Время начала в формате ISO 8601.
        duration_minutes: Продолжительность в минутах.
    
    Returns:
        Время окончания в формате ISO 8601.
    """
    # Парсим ISO строку (поддерживаем формат с и без Z/timezone)
    start_str = start_iso.replace("Z", "+00:00")
    
    # Пробуем разные форматы
    formats = [
        "%Y-%m-%dT%H:%M:%S%z",      # С timezone
        "%Y-%m-%dT%H:%M:%S.%f%z",   # С микросекундами и timezone
        "%Y-%m-%dT%H:%M:%S",        # Без timezone
        "%Y-%m-%dT%H:%M",           # Без секунд
    ]
    
    dt = None
    for fmt in formats:
        try:
            dt = datetime.strptime(start_str, fmt)
            break
        except ValueError:
            continue
    
    if dt is None:
        # Если не удалось распарсить, пробуем как naive datetime
        try:
            dt = datetime.fromisoformat(start_iso.replace("Z", ""))
        except ValueError:
            # Возвращаем start + 1 час как строку
            return start_iso.replace("T", "T") if "T" in start_iso else start_iso
    
    end_dt = dt + timedelta(minutes=duration_minutes)
    
    # Возвращаем в том же формате, что и входная строка
    if "T" in start_iso:
        return end_dt.strftime("%Y-%m-%dT%H:%M:%S")
    return end_dt.isoformat()


async def create_calendar_event(
    summary: str,
    start_iso: str,
    end_iso: Optional[str] = None,
    timezone: str = "Europe/Moscow",
    description: Optional[str] = None,
    location: Optional[str] = None,
) -> Dict:
    """
    Создает событие в Google Calendar.
    
    Args:
        summary: Заголовок события.
        start_iso: Время начала в формате ISO 8601.
        end_iso: Время окончания в формате ISO 8601 (опционально).
        timezone: Часовой пояс.
        description: Описание события (опционально).
        location: Место проведения (опционально).
    
    Returns:
        Словарь с информацией о созданном событии или ошибкой.
    """
    try:
        service = _get_calendar_service()
    except ImportError as e:
        return {"error": str(e)}
    except FileNotFoundError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Ошибка авторизации Google Calendar: {str(e)}"}
    
    # Вычисляем время окончания, если не указано
    if not end_iso:
        end_iso = calculate_end_time(start_iso, 60)
    
    # Формируем тело события
    event_body: Dict[str, Any] = {
        "summary": summary,
        "start": parse_iso_datetime(start_iso, timezone),
        "end": parse_iso_datetime(end_iso, timezone),
    }
    
    if description:
        event_body["description"] = description
    
    if location:
        event_body["location"] = location
    
    try:
        event = service.events().insert(
            calendarId=GOOGLE_CALENDAR_ID,
            body=event_body
        ).execute()
        
        return {
            "event_id": event.get("id", ""),
            "html_link": event.get("htmlLink", ""),
            "start": event.get("start", {}).get("dateTime", start_iso),
            "end": event.get("end", {}).get("dateTime", end_iso),
            "summary": event.get("summary", summary),
        }
        
    except Exception as e:
        error_message = str(e)
        
        # Пытаемся извлечь более понятное сообщение об ошибке
        if "invalid_grant" in error_message.lower():
            return {
                "error": "Токен авторизации истек или недействителен. "
                         f"Удалите файл {GOOGLE_TOKEN_PATH} и повторите авторизацию."
            }
        if "access" in error_message.lower() and "denied" in error_message.lower():
            return {
                "error": "Нет доступа к календарю. Проверьте права доступа в Google Cloud Console."
            }
        
        return {"error": f"Ошибка создания события: {error_message}"}

