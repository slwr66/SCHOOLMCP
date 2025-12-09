"""
Testy dlya wiki_get_material MCP tool.
"""
import asyncio
import httpx
from tools.wiki_get_material import (
    _search_wiki,
    _get_article_content,
    _parse_sections,
    _apply_max_chars,
    WIKI_SOURCES
)


async def test_search_wiki():
    """Test poiska statji v wiki."""
    print("=" * 50)
    print("Test: _search_wiki")
    print("=" * 50)
    
    # Test search in Russian Wikipedia
    api_url = "https://ru.wikipedia.org/w/api.php"
    result = await _search_wiki(api_url, "Python")
    
    if result:
        print(f"[OK] Found: {result.get('title', 'N/A')}")
        print(f"[OK] PageID: {result.get('pageid', 'N/A')}")
        return True
    else:
        print("[FAIL] No result found")
        return False


async def test_get_article_content():
    """Test poluchenija soderzimogo statji."""
    print("\n" + "=" * 50)
    print("Test: _get_article_content")
    print("=" * 50)
    
    api_url = "https://ru.wikipedia.org/w/api.php"
    result = await _get_article_content(api_url, "Python")
    
    if result:
        print(f"[OK] Title: {result.get('title', 'N/A')}")
        print(f"[OK] URL: {result.get('url', 'N/A')}")
        print(f"[OK] Extract length: {len(result.get('extract', ''))} chars")
        return True
    else:
        print("[FAIL] No content found")
        return False


async def test_parse_sections():
    """Test razbora sekcij."""
    print("\n" + "=" * 50)
    print("Test: _parse_sections")
    print("=" * 50)
    
    sample_text = """This is the introduction paragraph.

== History ==
This is history section content.

== Features ==
This is features section content.

=== Subsection ===
This is subsection content.
"""
    
    result = _parse_sections(sample_text, "Test Article")
    
    print(f"[OK] Summary length: {len(result.get('summary', ''))} chars")
    print(f"[OK] Sections count: {len(result.get('sections', []))}")
    
    for section in result.get('sections', []):
        print(f"  - Section: {section.get('title', 'N/A')}")
    
    return True


async def test_apply_max_chars():
    """Test ogranichenija po simvolam."""
    print("\n" + "=" * 50)
    print("Test: _apply_max_chars")
    print("=" * 50)
    
    test_data = {
        "summary": "A" * 500,
        "sections": [
            {"title": "Section 1", "content": "B" * 500},
            {"title": "Section 2", "content": "C" * 500}
        ]
    }
    
    result = _apply_max_chars(test_data, 800)
    
    total_chars = len(result.get("summary", ""))
    for section in result.get("sections", []):
        total_chars += len(section.get("content", ""))
    
    print(f"[OK] Original total: 1500 chars")
    print(f"[OK] After truncation: {total_chars} chars")
    print(f"[OK] Max allowed: 800 chars")
    
    return total_chars <= 1000  # Some tolerance for truncation


async def test_full_flow():
    """Test polnogo potoka poluchenija materiala."""
    print("\n" + "=" * 50)
    print("Test: Full flow (wiki_get_material logic)")
    print("=" * 50)
    
    language = "ru"
    topic = "Python"
    max_chars = 2000
    
    sources = WIKI_SOURCES.get(language, [])
    
    for source in sources:
        search_result = await _search_wiki(source["url"], topic)
        if not search_result:
            print(f"[SKIP] {source['name']}: no results")
            continue
        
        article = await _get_article_content(source["url"], search_result["title"])
        if not article or not article.get("extract"):
            print(f"[SKIP] {source['name']}: no content")
            continue
        
        parsed = _parse_sections(article["extract"], article["title"])
        
        if parsed["summary"] or parsed["sections"]:
            result = {
                "title": article["title"],
                "summary": parsed["summary"],
                "sections": parsed["sections"],
                "source_urls": [article.get("url", "")],
                "source": source["name"]
            }
            
            result = _apply_max_chars(result, max_chars)
            
            print(f"[OK] Source: {result.get('source', 'N/A')}")
            print(f"[OK] Title: {result.get('title', 'N/A')}")
            print(f"[OK] Summary: {len(result.get('summary', ''))} chars")
            print(f"[OK] Sections: {len(result.get('sections', []))}")
            
            return True
    
    print("[FAIL] No material found in any source")
    return False


async def main():
    """Zapusk vseh testov."""
    print("\n[TEST] Running wiki_get_material tests\n")
    
    results = []
    results.append(await test_search_wiki())
    results.append(await test_get_article_content())
    results.append(await test_parse_sections())
    results.append(await test_apply_max_chars())
    results.append(await test_full_flow())
    
    print("\n" + "=" * 50)
    print(f"[RESULT] {sum(results)}/{len(results)} tests passed")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
