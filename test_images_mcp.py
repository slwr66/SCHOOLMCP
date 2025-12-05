"""
Тестовый скрипт для проверки работоспособности Images-MCP сервера.
"""
import asyncio
import json
from fastmcp import Client
from mcp_instance import mcp

# Импорты инструментов для регистрации декораторов
from tools.get_images import get_images  # noqa: F401


def extract_result(result_obj):
    """Извлекает данные из результата FastMCP."""
    # Если это TextContent, парсим JSON из text
    if hasattr(result_obj, 'text'):
        return json.loads(result_obj.text)
    # Если это список с TextContent
    if isinstance(result_obj, list) and len(result_obj) > 0:
        if hasattr(result_obj[0], 'text'):
            return json.loads(result_obj[0].text)
        return result_obj
    # Если это словарь или список напрямую
    if isinstance(result_obj, (list, dict)):
        return result_obj
    # Если есть атрибут content
    if hasattr(result_obj, 'content'):
        return extract_result(result_obj.content)
    return result_obj


async def test_images():
    """Тестирование инструмента get_images."""
    print("Тестирование Images-MCP...")
    
    try:
        async with Client(mcp) as client:
            print("\nТест: Поиск изображения по теме 'space'...")
            result_obj = await client.call_tool("get_images", {"topic": "space", "count": 1})
            result = extract_result(result_obj)
            
            if not result or len(result) == 0:
                print("ОШИБКА: Пустой результат")
                return False
            
            photo = result[0]
            if not isinstance(photo, dict) or "url" not in photo:
                print(f"ОШИБКА: Неверный формат результата")
                return False
            
            print(f"OK: Изображение найдено")
            print(f"   - URL: {photo.get('url', 'N/A')[:60]}...")
            print(f"   - Автор: {photo.get('author', 'N/A')}")
            
            print("\nOK: Images MCP тест пройден успешно!")
            return True
        
    except Exception as e:
        print(f"ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_images())
    exit(0 if success else 1)
