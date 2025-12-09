import sys 
from typing import Optional, List
import requests 
from mcp_instance import mcp
from pydantic import Field


WIKIPEDIA_API_URL = "https://ru.wikipedia.org/w/api.php"
USER_AGENT = "WikipediaMCP/1.0"


@mcp.tool()
async def search_article(
    query: str = Field(..., description="Название статьи"),
    language: str = Field("ru", description="Язык Википедии")
) -> str:
    """"
    Поиск статей в ru.Wikipedia
    
    """
    params = {
        "action": "query",
        "format" : "json",
        "list" : "search",
        "srsearch" : query,
        "srlimit" : 10,
        "utf8" : 1,
        "srprop": "snippet|titlesnippet|sectiontitle",
        "srinfo": "totalhits"
    }

    try:
        response = requests.get(
            f"https://{language}.wikipedia.org/w/api.php",
            params=params,
            headers={"User-Agent": USER_AGENT},
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        if "query" not in data or "search" not in data["query"]:
            return "Не найдено результатов"
        results = data["query"]["search"]
        total_hits = data["query"].get("searchinfo", {}).get("totalhits", 0)
        
        output = [f"**Результаты поиска:** '{query}'"]
        output.append(f"Найдено всего: {total_hits} статей")
        output.append("---")
        
        for result in results:
            title = result.get("title", "Без названия")
            snippet = result.get("snippet", "")
            output.append(f"**{title}**")
            if snippet:
                output.append(snippet)
            output.append("")
        
        return "\n".join(output)

    except requests.exceptions.RequestException as e:
        return f"Ошибка при поиске: {str(e)}"
    except Exception as e:
        return f"Непредвиденная ошибка: {str(e)}"

@mcp.tool()
async def get_text_from_wiki(
    title: Optional[str] = Field(None, description="Назване статьи"),
    pageid : Optional[int] = Field(None, description="ID страницы"),
    language: str = Field("ru", description="Язык Википедии")
) -> List[str]:
    """
    Асинхронно получает текст статьи из Википедии по названию или ID страницы.
    
    Функция обращается к API Википедии, получает содержимое статьи и разбивает его
    на абзацы. Поддерживает обработку редиректов и нормализацию названий статей.
    
    Параметры:
    ----------
    title : Optional[str]
        Название статьи в Википедии. Должен быть указан либо title, либо pageid.
    pageid : Optional[int]
        Идентификатор страницы в Википедии. Должен быть указан либо title, либо pageid.
    language : str, default="ru"
        Код языка Википедии (например, "ru", "en", "fr").
    
    Возвращает:
    -----------
    List[str]
        Список абзацев статьи. В случае ошибки возвращает список с одним элементом,
        содержащим описание ошибки.
    
    Примеры возвращаемых значений:
    -----------------------------
    - Успешный запрос: ["Первый абзац статьи", "Второй абзац статьи", ...]
    - Ошибка: ["Ошибка: необходимо указать title или page id"]
    - Статья не найдена: ["Статья не найдена"]
    - Сетевая ошибка: ["Ошибка при получении статьи: ..."]
    
    Особенности:
    ------------
    - Автоматически нормализует названия статей (заменяет пробелы на подчеркивания)
    - Обрабатывает редиректы статей
    - Извлекает чистый текст без разметки
    - Возвращает метаданные: заголовок, URL, timestamp последнего изменения
    - Разбивает текст по двойным переносам строк (\n\n) для выделения абзацев
    
    Исключения:
    -----------
    - Не выбрасывает исключения напрямую, все ошибки обрабатываются внутри функции
      и возвращаются как элементы списка с описанием ошибки.

    """

    if not title and not pageid:
        return ["Ошибка: необходимо указать title или page id"]
    
    headers = {"User-Agent": USER_AGENT}
    params = {
        "action": "query",
        "format": "json",
        "prop": "extracts|info|revisions",
        "inprop": "url",
        "explaintext": 1,
        "exsectionformat": "plain",
        "exintro": 0,
        "rvprop": "timestamp",
        "redirects": 1,  # Обработка редиректов
    }

    parameters = {}
    if title:
        # Нормализация названия: замена пробелов на подчеркивания
        normalized_title = title.strip().replace(" ", "_")
        parameters['titles'] = normalized_title  # Используем 'titles' (множественное число)
    elif pageid:
        parameters['pageids'] = pageid

    params.update(parameters)

    try:
        response = requests.get(
            f"https://{language}.wikipedia.org/w/api.php",
            params=params,
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        
        pages = data.get("query", {}).get("pages", {})
        if not pages:
            return ["Статья не найдена"]
        
        page_id, page = next(iter(pages.items()))
        
        if "missing" in page:
            return ["Статья не найдена. Проверьте правильность названия."]
        
        page_title = page.get("title", "Без названия")
        extract = page.get("extract", "Содержимое недоступно")
        url = page.get("fullurl", f"https://{language}.wikipedia.org/?curid={pageid}")
        timestamp = page.get("revisions", [{}])[0].get("timestamp", "")
        
        # Разбиваем текст по абзацам (двойной перенос строки)
        if not extract or extract == "Содержимое недоступно":
            return ["Содержимое статьи недоступно"]
        
        # Разбиваем по двойным переносам строк (\n\n) для получения абзацев
        paragraphs = [p.strip() for p in extract.split("\n\n") if p.strip()]
        
        # Если абзацев нет, разбиваем по одинарным переносам
        if not paragraphs:
            paragraphs = [p.strip() for p in extract.split("\n") if p.strip()]
        
        # Если все еще пусто, возвращаем весь текст как один абзац
        if not paragraphs:
            paragraphs = [extract] if extract else ["Текст статьи пуст"]
        
        return paragraphs
    
    except requests.exceptions.RequestException as e:
        return [f"Ошибка при получении статьи: {str(e)}"]
    except Exception as e:
        return [f"Непредвиденная ошибка: {str(e)}"]

 
@mcp.prompt()
def wikipedia_research_prompt(topic: str) -> str:
    """Промпт для исследования темы в Wikipedia"""
    return f"""
    Я хочу исследовать тему "{topic}" в Wikipedia. Пожалуйста:
    
    1. Найди статьи по этой теме
    2. Дай краткое содержание основных статей
    3. Предложи связанные темы для дальнейшего исследования
    4. Укажи ссылки на источники
    
    Буду благодарен за структурированный ответ с выделением ключевых моментов.
    """