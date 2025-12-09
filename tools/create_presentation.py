"""
Инструмент для создания презентаций через Google Slides API.
"""
from typing import Dict, List
from pydantic import Field

from mcp_instance import mcp
from tools.google_slides import build_presentation


@mcp.tool()
async def create_presentation(
    title: str = Field(..., description="Заголовок презентации"),
    slides: List[Dict] = Field(
        ..., 
        description="Список слайдов: [{title: str, text: str, image_url?: str}, ...]"
    ),
    use_service_account: bool = Field(
        True, 
        description="Использовать Service Account (True) или OAuth (False)"
    )
) -> Dict:
    """
    Создать презентацию Google Slides.
    
    Инструмент создает презентацию с указанными слайдами. Каждый слайд может
    содержать заголовок, текст и опционально изображение. Идеально подходит
    для автоматической генерации учебных презентаций на основе материалов урока.
    
    Args:
        title: Заголовок презентации (например, 'Урок: Солнечная система').
        slides: Список слайдов. Каждый слайд — словарь с ключами:
            - title (str): заголовок слайда
            - text (str): основной текст слайда
            - image_url (str, опционально): URL изображения для слайда
        use_service_account: Использовать Service Account (True) или OAuth (False).
            Service Account рекомендуется для серверного использования.
    
    Returns:
        Словарь с информацией о созданной презентации:
        {
            "presentation_id": str,    # ID презентации в Google Slides
            "presentation_url": str,   # Ссылка на презентацию
            "slides_count": int        # Количество созданных слайдов
        }
        
        В случае ошибки:
        {
            "error": str               # Описание ошибки
        }
    
    Example:
        >>> await create_presentation(
        ...     title="Урок: Введение в астрономию",
        ...     slides=[
        ...         {
        ...             "title": "Что такое астрономия?",
        ...             "text": "Астрономия — наука о Вселенной...",
        ...             "image_url": "https://images.unsplash.com/photo-xxx"
        ...         },
        ...         {
        ...             "title": "Солнечная система",
        ...             "text": "Солнечная система состоит из 8 планет..."
        ...         }
        ...     ],
        ...     use_service_account=True
        ... )
        {
            "presentation_id": "1abc...",
            "presentation_url": "https://docs.google.com/presentation/d/1abc.../edit",
            "slides_count": 2
        }
    """
    # Валидация входных данных
    if not title or not title.strip():
        return {"error": "Заголовок презентации (title) не может быть пустым."}
    
    if not slides:
        return {"error": "Список слайдов (slides) не может быть пустым."}
    
    if not isinstance(slides, list):
        return {"error": "Параметр slides должен быть списком словарей."}
    
    # Валидация каждого слайда
    validated_slides: List[Dict] = []
    for i, slide in enumerate(slides):
        if not isinstance(slide, dict):
            return {"error": f"Слайд #{i+1} должен быть словарём с ключами title, text, image_url."}
        
        slide_title = slide.get("title", "")
        slide_text = slide.get("text", "")
        image_url = slide.get("image_url")
        
        # Хотя бы title или text должен быть заполнен
        if not slide_title and not slide_text:
            return {"error": f"Слайд #{i+1}: укажите хотя бы title или text."}
        
        validated_slide = {
            "title": str(slide_title) if slide_title else "",
            "text": str(slide_text) if slide_text else ""
        }
        
        if image_url:
            # Базовая проверка URL
            image_url_str = str(image_url).strip()
            if not image_url_str.startswith(("http://", "https://")):
                return {
                    "error": f"Слайд #{i+1}: image_url должен начинаться с http:// или https://"
                }
            validated_slide["image_url"] = image_url_str
        
        validated_slides.append(validated_slide)
    
    # Создаем презентацию через Google Slides API
    result = await build_presentation(
        title=title.strip(),
        slides=validated_slides,
        use_service_account=use_service_account
    )
    
    return result

