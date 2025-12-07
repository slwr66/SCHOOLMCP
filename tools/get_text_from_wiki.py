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
            f"https://{language}.wikipedia.org/w/api.h",
            params = params
        )
        response.raise_for_status()
        data = response.json()
        if "query" not in data or "search" not in data["query"]:
            return "Не найдено результатов"
        results = data["query"]["search"]
        total_hits = data["query"].get("searchinfo", {}).get("totalhits", 0)
        
        output = [f"🔍 **Результаты поиска:** '{query.query}'"]
        output.append(f"📊 Найдено всего: {total_hits} статей")
        output.append("---")

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


    """

    if not title and not pageid:
        return "Ошибка : необходимо указать title или page id"
    
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
    }

    parameters = {}
    if title :
        parameters['title'] = title
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
            return "Статья не найдена"
        
        page_id, page = next(iter(pages.items()))
        
        if "missing" in page:
            return f"Статья не найдена. Проверьте правильность названия."
        
        title = page.get("title", "Без названия")
        extract = page.get("extract", "Содержимое недоступно")
        url = page.get("fullurl", f"https://{language}.wikipedia.org/?curid={pageid}")
        timestamp = page.get("revisions", [{}])[0].get("timestamp", "")
        
        
        return extract
    
    except requests.exceptions.RequestException as e:
        return f"Ошибка при получении статьи: {str(e)}"
    except Exception as e:
        return f"Непредвиденная ошибка: {str(e)}"

 
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