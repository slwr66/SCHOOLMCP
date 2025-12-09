"""
Утилиты для работы с Google Slides API.
Поддерживает создание презентаций с Service Account и OAuth авторизацией.
"""
import os
import uuid
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Пути к файлам учетных данных
GOOGLE_SLIDES_CREDENTIALS_PATH = os.getenv("GOOGLE_SLIDES_CREDENTIALS_PATH", "credentials.json")
GOOGLE_SLIDES_TOKEN_PATH = os.getenv("GOOGLE_SLIDES_TOKEN_PATH", "slides_token.json")
GOOGLE_SERVICE_ACCOUNT_PATH = os.getenv("GOOGLE_SERVICE_ACCOUNT_PATH", "service_account.json")
GOOGLE_SLIDES_AUTH_TYPE = os.getenv("GOOGLE_SLIDES_AUTH_TYPE", "service_account")

# Scopes для Google Slides API
SCOPES_OAUTH = [
    "https://www.googleapis.com/auth/presentations",
    "https://www.googleapis.com/auth/drive.file"
]

SCOPES_SERVICE_ACCOUNT = [
    "https://www.googleapis.com/auth/presentations",
    "https://www.googleapis.com/auth/drive"
]


def _get_slides_service(use_service_account: bool = True) -> Any:
    """
    Создает и возвращает сервис Google Slides API.
    
    Args:
        use_service_account: Использовать Service Account (True) или OAuth (False).
    
    Returns:
        Объект сервиса Google Slides API.
        
    Raises:
        ImportError: Если Google библиотеки не установлены.
        FileNotFoundError: Если файл учетных данных не найден.
    """
    try:
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        from google.oauth2.service_account import Credentials as ServiceAccountCredentials
        from googleapiclient.discovery import build
    except ImportError as e:
        raise ImportError(
            "Google API библиотеки не установлены. "
            "Выполните: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib"
        ) from e
    
    if use_service_account:
        # Авторизация через Service Account
        if not os.path.exists(GOOGLE_SERVICE_ACCOUNT_PATH):
            raise FileNotFoundError(
                f"Файл Service Account не найден: {GOOGLE_SERVICE_ACCOUNT_PATH}. "
                "Создайте Service Account в Google Cloud Console и скачайте JSON-ключ."
            )
        
        creds = ServiceAccountCredentials.from_service_account_file(
            GOOGLE_SERVICE_ACCOUNT_PATH,
            scopes=SCOPES_SERVICE_ACCOUNT
        )
        return build("slides", "v1", credentials=creds)
    
    else:
        # Авторизация через OAuth 2.0
        creds = None
        
        if os.path.exists(GOOGLE_SLIDES_TOKEN_PATH):
            creds = Credentials.from_authorized_user_file(
                GOOGLE_SLIDES_TOKEN_PATH, 
                SCOPES_OAUTH
            )
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(GOOGLE_SLIDES_CREDENTIALS_PATH):
                    raise FileNotFoundError(
                        f"Файл учетных данных не найден: {GOOGLE_SLIDES_CREDENTIALS_PATH}. "
                        "Скачайте credentials.json из Google Cloud Console."
                    )
                flow = InstalledAppFlow.from_client_secrets_file(
                    GOOGLE_SLIDES_CREDENTIALS_PATH,
                    SCOPES_OAUTH
                )
                creds = flow.run_local_server(port=0)
            
            # Сохраняем токен для последующего использования
            with open(GOOGLE_SLIDES_TOKEN_PATH, "w") as token:
                token.write(creds.to_json())
        
        return build("slides", "v1", credentials=creds)


def _build_slide_requests(
    slides: List[Dict[str, str]],
    start_index: int = 0
) -> List[Dict[str, Any]]:
    """
    Формирует список запросов для создания слайдов.
    
    Args:
        slides: Список слайдов с title, text и опциональным image_url.
        start_index: Начальный индекс для вставки слайдов.
    
    Returns:
        Список запросов для batchUpdate API.
    """
    requests: List[Dict[str, Any]] = []
    insertion_index = start_index
    
    for slide_data in slides:
        slide_id = f"slide_{uuid.uuid4().hex}"
        title_shape_id = f"title_{uuid.uuid4().hex}"
        text_shape_id = f"text_{uuid.uuid4().hex}"
        
        slide_title = slide_data.get("title", "")
        slide_text = slide_data.get("text", "")
        image_url = slide_data.get("image_url")
        
        # Создаем слайд
        requests.append({
            "createSlide": {
                "objectId": slide_id,
                "insertionIndex": insertion_index,
                "slideLayoutReference": {"predefinedLayout": "BLANK"}
            }
        })
        
        # Определяем размеры в зависимости от наличия изображения
        if image_url:
            # С изображением: текст слева, картинка справа
            title_width = 600
            text_width = 320
            text_height = 300
            text_x = 30
        else:
            # Без изображения: текст на всю ширину
            title_width = 600
            text_width = 600
            text_height = 400
            text_x = 50
        
        # Создаем заголовок
        requests.append({
            "createShape": {
                "objectId": title_shape_id,
                "shapeType": "TEXT_BOX",
                "elementProperties": {
                    "pageObjectId": slide_id,
                    "size": {
                        "width": {"magnitude": title_width, "unit": "PT"},
                        "height": {"magnitude": 60, "unit": "PT"}
                    },
                    "transform": {
                        "scaleX": 1,
                        "scaleY": 1,
                        "translateX": 50,
                        "translateY": 30,
                        "unit": "PT"
                    }
                }
            }
        })
        
        if slide_title:
            requests.append({
                "insertText": {
                    "objectId": title_shape_id,
                    "insertionIndex": 0,
                    "text": slide_title
                }
            })
            
            # Форматируем заголовок (жирный, крупный шрифт)
            requests.append({
                "updateTextStyle": {
                    "objectId": title_shape_id,
                    "style": {
                        "bold": True,
                        "fontSize": {"magnitude": 24, "unit": "PT"}
                    },
                    "textRange": {"type": "ALL"},
                    "fields": "bold,fontSize"
                }
            })
        
        # Создаем текстовый блок
        requests.append({
            "createShape": {
                "objectId": text_shape_id,
                "shapeType": "TEXT_BOX",
                "elementProperties": {
                    "pageObjectId": slide_id,
                    "size": {
                        "width": {"magnitude": text_width, "unit": "PT"},
                        "height": {"magnitude": text_height, "unit": "PT"}
                    },
                    "transform": {
                        "scaleX": 1,
                        "scaleY": 1,
                        "translateX": text_x,
                        "translateY": 100,
                        "unit": "PT"
                    }
                }
            }
        })
        
        if slide_text:
            requests.append({
                "insertText": {
                    "objectId": text_shape_id,
                    "insertionIndex": 0,
                    "text": slide_text
                }
            })
        
        # Добавляем изображение, если указано
        if image_url:
            image_id = f"image_{uuid.uuid4().hex}"
            requests.append({
                "createImage": {
                    "objectId": image_id,
                    "url": image_url,
                    "elementProperties": {
                        "pageObjectId": slide_id,
                        "size": {
                            "width": {"magnitude": 300, "unit": "PT"},
                            "height": {"magnitude": 220, "unit": "PT"}
                        },
                        "transform": {
                            "scaleX": 1,
                            "scaleY": 1,
                            "translateX": 370,
                            "translateY": 100,
                            "unit": "PT"
                        }
                    }
                }
            })
        
        insertion_index += 1
    
    return requests


async def build_presentation(
    title: str,
    slides: List[Dict[str, str]],
    use_service_account: bool = True
) -> Dict[str, Any]:
    """
    Создает презентацию Google Slides.
    
    Args:
        title: Заголовок презентации.
        slides: Список слайдов. Каждый слайд — словарь с ключами:
            - title: str — заголовок слайда
            - text: str — основной текст слайда
            - image_url: str (опционально) — URL изображения для слайда
        use_service_account: Использовать Service Account (True) или OAuth (False).
    
    Returns:
        Словарь с информацией о созданной презентации:
        {
            "presentation_id": str,
            "presentation_url": str,
            "slides_count": int
        }
        
        В случае ошибки:
        {
            "error": str
        }
    """
    try:
        service = _get_slides_service(use_service_account)
    except ImportError as e:
        return {"error": str(e)}
    except FileNotFoundError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Ошибка авторизации Google Slides: {str(e)}"}
    
    try:
        # Создаем презентацию
        presentation = service.presentations().create(
            body={"title": title}
        ).execute()
        
        presentation_id = presentation["presentationId"]
        
        # Формируем запросы для слайдов
        requests = _build_slide_requests(slides, start_index=0)
        
        if requests:
            # Выполняем пакетное обновление
            service.presentations().batchUpdate(
                presentationId=presentation_id,
                body={"requests": requests}
            ).execute()
        
        return {
            "presentation_id": presentation_id,
            "presentation_url": f"https://docs.google.com/presentation/d/{presentation_id}/edit",
            "slides_count": len(slides)
        }
        
    except Exception as e:
        error_message = str(e)
        
        # Пытаемся извлечь более понятное сообщение об ошибке
        if "invalid_grant" in error_message.lower():
            return {
                "error": "Токен авторизации истек или недействителен. "
                         f"Удалите файл {GOOGLE_SLIDES_TOKEN_PATH} и повторите авторизацию."
            }
        if "access" in error_message.lower() and "denied" in error_message.lower():
            return {
                "error": "Нет доступа к Google Slides API. Проверьте права доступа в Google Cloud Console."
            }
        if "quota" in error_message.lower():
            return {
                "error": "Превышена квота запросов к Google Slides API. Повторите позже."
            }
        if "image" in error_message.lower() and "url" in error_message.lower():
            return {
                "error": "Ошибка загрузки изображения. Проверьте URL изображения — "
                         "он должен быть публично доступен."
            }
        
        return {"error": f"Ошибка создания презентации: {error_message}"}

