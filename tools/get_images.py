"""
Инструмент для поиска изображений через Unsplash API.
"""
import os
from typing import List
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
    topic: str = Field(..., description="Тема для поиска изображений"),
    count: int = Field(1, ge=1, le=10, description="Количество изображений (1-10)")
) -> List[dict]:
    """
    Поиск изображений через Unsplash API по заданной теме.
    
    Args:
        topic: Тема для поиска
        count: Количество изображений (1-10)
    
    Returns:
        Список словарей с информацией об изображениях
    """
    if not UNSPLASH_ACCESS_KEY:
        return []
    
    url = UNSPLASH_API_URL
    params = {
        "query": topic,
        "per_page": count,
        "orientation": "landscape"
    }
    headers = {
        "Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"
    }
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(url, params=params, headers=headers)
        if resp.status_code != 200:
            return []
        data = resp.json()
        results = []
        for photo in data.get("results", [])[:count]:
            results.append({
                "id": photo.get("id"),
                "url": photo.get("urls", {}).get("regular"),
                "description": photo.get("description") or photo.get("alt_description"),
                "author": photo.get("user", {}).get("name"),
            })
        return results

