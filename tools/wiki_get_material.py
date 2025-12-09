"""
Инструмент для получения учебного материала из вики-источников.
Поддерживает Wikibooks, Vikidia и Wikipedia с приоритетом детских ресурсов.
"""
import re
from typing import Dict, List, Optional
import httpx
from pydantic import Field

from mcp_instance import mcp


# API URLs для разных вики-проектов
WIKI_SOURCES = {
    "ru": [
        {"name": "wikibooks", "url": "https://ru.wikibooks.org/w/api.php"},
        {"name": "wikipedia", "url": "https://ru.wikipedia.org/w/api.php"},
    ],
    "en": [
        {"name": "wikibooks", "url": "https://en.wikibooks.org/w/api.php"},
        {"name": "vikidia", "url": "https://en.vikidia.org/w/api.php"},
        {"name": "wikipedia", "url": "https://en.wikipedia.org/w/api.php"},
    ],
}

USER_AGENT = "WikiMaterialMCP/1.0 (Educational Bot; https://github.com/example/mcp-edtech; contact@example.com)"


def _clean_wiki_text(text: str) -> str:
    """Очистка текста от вики-разметки и служебных символов."""
    # Удаляем ссылки на изображения и файлы
    text = re.sub(r'\[\[(?:File|Image|Файл|Изображение):[^\]]+\]\]', '', text)
    # Удаляем категории
    text = re.sub(r'\[\[(?:Category|Категория):[^\]]+\]\]', '', text)
    # Упрощаем внутренние ссылки: [[текст|отображение]] -> отображение
    text = re.sub(r'\[\[[^\|\]]+\|([^\]]+)\]\]', r'\1', text)
    # Упрощаем простые ссылки: [[текст]] -> текст
    text = re.sub(r'\[\[([^\]]+)\]\]', r'\1', text)
    # Удаляем шаблоны {{...}}
    text = re.sub(r'\{\{[^}]+\}\}', '', text)
    # Удаляем HTML-теги
    text = re.sub(r'<[^>]+>', '', text)
    # Удаляем множественные пробелы и переносы
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)
    return text.strip()


def _truncate_content(content: str, max_chars: int) -> str:
    """Обрезать контент до указанного количества символов, не ломая слова."""
    if len(content) <= max_chars:
        return content
    
    truncated = content[:max_chars]
    # Найти последний пробел или перенос строки
    last_space = truncated.rfind(' ')
    last_newline = truncated.rfind('\n')
    cut_point = max(last_space, last_newline)
    
    if cut_point > max_chars * 0.7:  # Если нашли подходящую точку
        return truncated[:cut_point] + "..."
    return truncated + "..."


async def _search_wiki(api_url: str, query: str) -> Optional[Dict]:
    """Поиск статьи в указанном вики-источнике."""
    params = {
        "action": "query",
        "format": "json",
        "list": "search",
        "srsearch": query,
        "srlimit": 5,
        "utf8": 1,
    }
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                api_url,
                params=params,
                headers={"User-Agent": USER_AGENT}
            )
            response.raise_for_status()
            data = response.json()
            
            results = data.get("query", {}).get("search", [])
            if results:
                return {"title": results[0]["title"], "pageid": results[0]["pageid"]}
    except Exception:
        pass
    return None


async def _get_article_content(api_url: str, title: str) -> Optional[Dict]:
    """Получить полное содержимое статьи с секциями."""
    params = {
        "action": "query",
        "format": "json",
        "titles": title,
        "prop": "extracts|info|revisions",
        "inprop": "url",
        "explaintext": 1,
        "exsectionformat": "wiki",
        "redirects": 1,
    }
    
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(
                api_url,
                params=params,
                headers={"User-Agent": USER_AGENT}
            )
            response.raise_for_status()
            data = response.json()
            
            pages = data.get("query", {}).get("pages", {})
            if not pages:
                return None
            
            page = next(iter(pages.values()))
            if "missing" in page:
                return None
            
            return {
                "title": page.get("title", ""),
                "extract": page.get("extract", ""),
                "url": page.get("fullurl", ""),
            }
    except Exception:
        pass
    return None


def _parse_sections(text: str, title: str) -> Dict:
    """Разбить текст на секции по заголовкам."""
    if not text:
        return {"summary": "", "sections": []}
    
    # Разделяем по заголовкам (== Заголовок ==)
    section_pattern = r'^==+\s*([^=]+?)\s*==+$'
    lines = text.split('\n')
    
    sections: List[Dict[str, str]] = []
    current_section: Optional[Dict[str, str]] = None
    summary_lines: List[str] = []
    
    in_summary = True
    
    for line in lines:
        match = re.match(section_pattern, line)
        if match:
            in_summary = False
            # Сохраняем предыдущую секцию
            if current_section:
                current_section["content"] = _clean_wiki_text(
                    '\n'.join(current_section.get("_lines", []))
                )
                del current_section["_lines"]
                if current_section["content"].strip():
                    sections.append(current_section)
            
            current_section = {
                "title": match.group(1).strip(),
                "_lines": []
            }
        else:
            if in_summary:
                summary_lines.append(line)
            elif current_section:
                current_section["_lines"].append(line)
    
    # Добавляем последнюю секцию
    if current_section:
        current_section["content"] = _clean_wiki_text(
            '\n'.join(current_section.get("_lines", []))
        )
        del current_section["_lines"]
        if current_section["content"].strip():
            sections.append(current_section)
    
    summary = _clean_wiki_text('\n'.join(summary_lines))
    
    return {
        "summary": summary,
        "sections": sections
    }


def _apply_max_chars(result: Dict, max_chars: int) -> Dict:
    """Применить ограничение по символам к результату."""
    total_chars = len(result.get("summary", ""))
    
    for section in result.get("sections", []):
        total_chars += len(section.get("content", ""))
    
    if total_chars <= max_chars:
        return result
    
    # Обрезаем контент, начиная с последних секций
    remaining_chars = max_chars
    
    # Сначала учитываем summary
    if result.get("summary"):
        if len(result["summary"]) > remaining_chars * 0.4:
            result["summary"] = _truncate_content(
                result["summary"], 
                int(remaining_chars * 0.4)
            )
        remaining_chars -= len(result["summary"])
    
    # Распределяем оставшееся место между секциями
    sections = result.get("sections", [])
    if sections and remaining_chars > 0:
        chars_per_section = remaining_chars // len(sections)
        
        for section in sections:
            if len(section.get("content", "")) > chars_per_section:
                section["content"] = _truncate_content(
                    section["content"], 
                    chars_per_section
                )
    
    return result


@mcp.tool()
async def wiki_get_material(
    topic: str = Field(..., description="Тема для поиска учебного материала"),
    language: str = Field("ru", description="Язык материала: 'ru' или 'en'"),
    max_chars: int = Field(4000, ge=500, le=20000, description="Максимальное количество символов (500-20000)")
) -> Dict:
    """
    Получить учебный материал по теме из вики-проектов (Wikibooks/Vikidia/Wikipedia).
    
    Инструмент последовательно ищет материал в образовательных вики-ресурсах,
    начиная с более детских/учебных (Wikibooks, Vikidia) и переходя к Wikipedia.
    
    Args:
        topic: Запрос/тема для поиска.
        language: Язык материала ("ru" или "en").
        max_chars: Ограничение на размер текста (по умолчанию 4000).
    
    Returns:
        Словарь с учебным материалом:
        {
            "title": str,
            "summary": str,
            "sections": [{"title": str, "content": str}, ...],
            "source_urls": [str, ...]
        }
        
        В случае ошибки:
        {
            "error": str,
            "topic": str
        }
    """
    if language not in WIKI_SOURCES:
        return {
            "error": f"Неподдерживаемый язык: {language}. Используйте 'ru' или 'en'.",
            "topic": topic
        }
    
    sources = WIKI_SOURCES[language]
    source_urls: List[str] = []
    
    # Пробуем найти материал в разных источниках
    for source in sources:
        try:
            # Поиск статьи
            search_result = await _search_wiki(source["url"], topic)
            if not search_result:
                continue
            
            # Получаем содержимое
            article = await _get_article_content(source["url"], search_result["title"])
            if not article or not article.get("extract"):
                continue
            
            # Парсим секции
            parsed = _parse_sections(article["extract"], article["title"])
            
            # Если есть хоть какой-то контент
            if parsed["summary"] or parsed["sections"]:
                if article.get("url"):
                    source_urls.append(article["url"])
                
                result = {
                    "title": article["title"],
                    "summary": parsed["summary"],
                    "sections": parsed["sections"],
                    "source_urls": source_urls,
                    "source": source["name"]
                }
                
                # Применяем ограничение по символам
                result = _apply_max_chars(result, max_chars)
                
                return result
                
        except httpx.TimeoutException:
            continue
        except httpx.HTTPError:
            continue
        except Exception:
            continue
    
    # Если ничего не найдено
    return {
        "error": f"Не удалось найти учебный материал по теме '{topic}' ни в одном из источников.",
        "topic": topic,
        "searched_sources": [s["name"] for s in sources]
    }

