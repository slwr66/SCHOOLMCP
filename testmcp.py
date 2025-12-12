"""
Тестовый скрипт для проверки MCP сервера через HTTP API.
Использует /api/call-tool endpoint для вызова инструментов.
"""
import httpx
import json
import asyncio

# URL вашего Container App
MCP_SERVER_URL = "https://container-app-mrizf-stems.containerapps.ru"

async def call_mcp_tool(tool_name: str, **kwargs):
    """Вызов MCP инструмента через HTTP API endpoint."""
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{MCP_SERVER_URL}/api/call-tool",
            json={
                "tool_name": tool_name,
                "arguments": kwargs
            }
        )
        response.raise_for_status()
        return response.json()

async def test_health():
    """Проверка health check."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(f"{MCP_SERVER_URL}/health")
        response.raise_for_status()
        return response.json()

async def test_tools_list():
    """Получение списка инструментов."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(f"{MCP_SERVER_URL}/tools")
        response.raise_for_status()
        return response.json()

async def main():
    print("=" * 60)
    print("Тестирование MCP сервера")
    print("=" * 60)
    
    # 1. Проверка health check
    print("\n1. Проверка health check...")
    try:
        health = await test_health()
        print(f"✅ Health check: {json.dumps(health, indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"❌ Ошибка health check: {e}")
        return
    
    # 2. Получение списка инструментов
    print("\n2. Получение списка инструментов...")
    try:
        tools = await test_tools_list()
        print(f"✅ Найдено инструментов: {tools.get('count', 0)}")
        if tools.get('tools'):
            print("   Доступные инструменты:")
            for tool in tools['tools']:
                print(f"   - {tool.get('name', 'unknown')}")
    except Exception as e:
        print(f"❌ Ошибка получения списка инструментов: {e}")
    
    # 3. Тест вызова get_images (не требует API ключей для проверки структуры)
    print("\n3. Тест вызова get_images...")
    try:
        result = await call_mcp_tool(
            "get_images",
            query="космос планеты",
            count=3,
            safe_for_kids=True
        )
        print(f"✅ Результат вызова get_images:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"❌ Ошибка вызова get_images: {e}")
        import traceback
        traceback.print_exc()
    
    # 4. Тест вызова wiki_get_material (не требует API ключей)
    print("\n4. Тест вызова wiki_get_material...")
    try:
        result = await call_mcp_tool(
            "wiki_get_material",
            topic="Солнечная система",
            language="ru",
            max_chars=1000
        )
        print(f"✅ Результат вызова wiki_get_material:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"❌ Ошибка вызова wiki_get_material: {e}")
        import traceback
        traceback.print_exc()
    
    # 5. Тест вызова get_quiz (не требует API ключей)
    print("\n5. Тест вызова get_quiz...")
    try:
        result = await call_mcp_tool(
            "get_quiz",
            topic="science",
            amount=5,
            difficulty="easy"
        )
        print(f"✅ Результат вызова get_quiz:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"❌ Ошибка вызова get_quiz: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("Тестирование завершено")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())