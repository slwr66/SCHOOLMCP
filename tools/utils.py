"""
Утилиты для работы с OpenTDB и Yandex Translate API.
"""
import os
import html
import asyncio
from typing import List, Optional, Dict
from dotenv import load_dotenv
import httpx

# Загружаем переменные окружения
load_dotenv()

YANDEX_IAM_TOKEN = os.getenv("YANDEX_IAM_TOKEN")
YANDEX_API_KEY = os.getenv("YANDEX_API_KEY")
OPENTDB_API_URL = "https://opentdb.com/api.php"
YANDEX_TRANSLATE_URL = "https://translate.api.cloud.yandex.net/translate/v2/translate"

# Маппинг категорий OpenTDB (название -> id)
OPENTDB_CATEGORIES = {
    "general knowledge": 9,
    "books": 10,
    "film": 11,
    "music": 12,
    "musicals & theatres": 13,
    "television": 14,
    "video games": 15,
    "board games": 16,
    "science & nature": 17,
    "science computers": 18,
    "science mathematics": 19,
    "mythology": 20,
    "sports": 21,
    "geography": 22,
    "history": 23,
    "politics": 24,
    "art": 25,
    "celebrities": 26,
    "animals": 27,
    "vehicles": 28,
    "comics": 29,
    "science gadgets": 30,
    "anime & manga": 31,
    "cartoon & animations": 32,
}


async def fetch_category_id(topic: str) -> Optional[int]:
    """
    Поиск ID категории в OpenTDB по названию темы.
    
    Args:
        topic: Тема для поиска категории
    
    Returns:
        ID категории или None, если не найдена
    """
    topic_lower = topic.lower()
    
    # Прямой поиск по ключам
    for category_name, category_id in OPENTDB_CATEGORIES.items():
        if topic_lower in category_name or category_name in topic_lower:
            return category_id
    
    # Поиск по частичному совпадению
    for category_name, category_id in OPENTDB_CATEGORIES.items():
        words = topic_lower.split()
        for word in words:
            if word in category_name or category_name in word:
                return category_id
    
    # Если не найдено, возвращаем General Knowledge
    return OPENTDB_CATEGORIES.get("general knowledge", 9)


async def translate_batch(texts: List[str], target: str = "ru") -> List[str]:
    """
    Пакетный перевод списка строк через Yandex Translate API.
    
    Args:
        texts: Список строк для перевода
        target: Целевой язык (по умолчанию "ru")
    
    Returns:
        Список переведенных строк в том же порядке
    """
    if not texts:
        return []
    
    if not YANDEX_IAM_TOKEN and not YANDEX_API_KEY:
        # Если нет токена, возвращаем оригинальные тексты
        return texts
    
    headers = {}
    if YANDEX_API_KEY:
        headers["Authorization"] = f"Api-Key {YANDEX_API_KEY}"
    
    body = {
        "texts": texts,
        "targetLanguageCode": target
    }
    
    if YANDEX_IAM_TOKEN:
        body["folderId"] = f"{YANDEX_IAM_TOKEN}"

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                YANDEX_TRANSLATE_URL,
                headers=headers,
                json=body
            )
            response.raise_for_status()
            data = response.json()
            
            # Извлекаем переведенные тексты
            translations = []
            for translation in data.get("translations", []):
                translations.append(translation.get("text", ""))
            
            return translations if translations else texts
            
    except httpx.HTTPError as e:
        # В случае ошибки возвращаем оригинальные тексты
        print(f"Ошибка перевода: {e}")
        return texts
    except Exception as e:
        print(f"Неожиданная ошибка при переводе: {e}")
        return texts


async def fetch_questions_from_opentdb(
    category_id: Optional[int] = None,
    amount: int = 10,
    difficulty: Optional[str] = None,
    question_type: Optional[str] = None
) -> Dict:
    """
    Получение вопросов из OpenTDB API.
    """
    params = {"amount": min(amount, 50)}
    if category_id:
        params["category"] = category_id
    if difficulty:
        params["difficulty"] = difficulty
    if question_type:
        params["type"] = question_type
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(OPENTDB_API_URL, params=params)
        if response.status_code != 200:
            return {"response_code": 1, "results": []}
        data = response.json()
        
        # Обрабатываем HTML-сущности
        if data.get("results"):
            for question in data["results"]:
                question["question"] = html.unescape(question["question"])
                question["correct_answer"] = html.unescape(question["correct_answer"])
                question["incorrect_answers"] = [
                    html.unescape(ans) for ans in question["incorrect_answers"]
                ]
        
        return data

