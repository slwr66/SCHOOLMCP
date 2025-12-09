"""
Инструмент для поиска изображений через Unsplash API.
Поддерживает безопасный поиск для детей и различные стили изображений.
"""
import os
from typing import Dict, List, Optional
from dotenv import load_dotenv
import httpx
from pydantic import Field

from mcp_instance import mcp

# Загружаем переменные окружения
load_dotenv()

UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")
UNSPLASH_API_URL = "https://api.unsplash.com/search/photos"


@mcp.tool()
async def get_images(
    query: str = Field(..., description="Поисковый запрос для изображений"),
    count: int = Field(5, ge=1, le=10, description="Количество изображений (1-10)"),
    safe_for_kids: bool = Field(True, description="Безопасный поиск для детей"),
    style_hint: Optional[str] = Field(
        None, 
        description="Стиль изображений: 'photo', 'cartoon', 'flat', 'illustration' и др."
    )
) -> Dict:
    """
    Поиск изображений через Unsplash API по заданному запросу.
    
    Инструмент находит качественные изображения для образовательных материалов
    с возможностью фильтрации по стилю и безопасности для детей.
    
    Args:
        query: Поисковый запрос (тема, ключевые слова).
        count: Количество изображений для возврата (1-10, по умолчанию 5).
        safe_for_kids: Включить безопасный поиск для детей (по умолчанию True).
        style_hint: Подсказка стиля ('photo', 'cartoon', 'flat', 'illustration').
    
    Returns:
        Словарь с результатами поиска:
        {
            "items": [
                {
                    "url": str,           # Полный URL изображения
                    "thumb_url": str,     # URL миниатюры
                    "author": str,        # Имя автора
                    "source": str,        # Источник ("unsplash")
                    "attribution": str    # Строка атрибуции
                },
                ...
            ],
            "query": str,
            "total_found": int
        }
        
        В случае ошибки:
        {
            "error": str,
            "items": []
        }
    """
    if not UNSPLASH_ACCESS_KEY:
        return {
            "error": "UNSPLASH_ACCESS_KEY не настроен. Добавьте ключ в .env файл.",
            "items": []
        }
    
    # Формируем поисковый запрос с учетом стиля
    search_query = query
    if style_hint:
        search_query = f"{query} {style_hint}"
    
    # Добавляем фильтр для детского контента
    if safe_for_kids:
        search_query = f"{search_query} educational safe"
    
    params = {
        "query": search_query,
        "per_page": count,
        "orientation": "landscape",
        "content_filter": "high" if safe_for_kids else "low"  # high = более строгий фильтр
    }
    
    headers = {
        "Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"
    }
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(UNSPLASH_API_URL, params=params, headers=headers)
            
            if resp.status_code == 401:
                return {
                    "error": "Неверный UNSPLASH_ACCESS_KEY. Проверьте ключ API.",
                    "items": []
                }
            
            if resp.status_code == 403:
                return {
                    "error": "Превышен лимит запросов Unsplash API.",
                    "items": []
                }
            
            if resp.status_code != 200:
                return {
                    "error": f"Ошибка Unsplash API: HTTP {resp.status_code}",
                    "items": []
                }
            
            data = resp.json()
            total_found = data.get("total", 0)
            
            items: List[Dict] = []
            for photo in data.get("results", [])[:count]:
                photo_id = photo.get("id", "")
                author_name = photo.get("user", {}).get("name", "Unknown")
                author_username = photo.get("user", {}).get("username", "")
                
                # Формируем строку атрибуции согласно требованиям Unsplash
                attribution = f"Photo by {author_name} on Unsplash"
                if author_username:
                    attribution = f"Photo by {author_name} (@{author_username}) on Unsplash"
                
                items.append({
                    "url": photo.get("urls", {}).get("regular", ""),
                    "thumb_url": photo.get("urls", {}).get("thumb", ""),
                    "author": author_name,
                    "source": "unsplash",
                    "attribution": attribution,
                    # Дополнительные поля для совместимости
                    "id": photo_id,
                    "description": photo.get("description") or photo.get("alt_description", ""),
                    "download_url": photo.get("links", {}).get("download", ""),
                })
            
            return {
                "items": items,
                "query": query,
                "total_found": total_found
            }
            
    except httpx.TimeoutException:
        return {
            "error": "Превышено время ожидания ответа от Unsplash API.",
            "items": []
        }
    except httpx.HTTPError as e:
        return {
            "error": f"Сетевая ошибка при запросе к Unsplash: {str(e)}",
            "items": []
        }
    except Exception as e:
        return {
            "error": f"Непредвиденная ошибка: {str(e)}",
            "items": []
        }
