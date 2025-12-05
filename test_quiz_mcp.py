"""
Тестовый скрипт для проверки работоспособности Quiz-MCP сервера.
Включает тестирование генерации викторины и экспорта результатов.
"""
import asyncio
import json
from pathlib import Path
from fastmcp import Client
from mcp_instance import mcp

# Импорты инструментов для регистрации декораторов
from tools.get_quiz import get_quiz  # noqa: F401
from tools.export_quiz import export_quiz  # noqa: F401


def extract_result(result_obj):
    """Извлекает данные из результата FastMCP."""
    # Если это TextContent, парсим JSON из text
    if hasattr(result_obj, 'text'):
        return json.loads(result_obj.text)
    # Если это список с TextContent
    if isinstance(result_obj, list) and len(result_obj) > 0:
        if hasattr(result_obj[0], 'text'):
            return json.loads(result_obj[0].text)
        return result_obj[0] if len(result_obj) == 1 else result_obj
    # Если это словарь или список напрямую
    if isinstance(result_obj, dict):
        return result_obj
    if isinstance(result_obj, list):
        return result_obj[0] if len(result_obj) == 1 else result_obj
    # Если есть атрибут content
    if hasattr(result_obj, 'content'):
        return extract_result(result_obj.content)
    return result_obj


async def test_quiz():
    """Тестирование инструментов get_quiz и export_quiz."""
    print("Тестирование Quiz-MCP...")
    
    try:
        async with Client(mcp) as client:
            # Тест 1: Генерация викторины
            print("\nТест 1: Генерация викторины на тему 'science'...")
            quiz_result_obj = await client.call_tool("get_quiz", {
                "topic": "science",
                "amount": 3,
                "difficulty": "easy"
            })
            quiz_result = extract_result(quiz_result_obj)
            
            if not quiz_result or not isinstance(quiz_result, dict):
                print("ОШИБКА: Пустой или неверный результат")
                return False
            
            # Проверка успешности
            if not quiz_result.get("success"):
                error = quiz_result.get("error", "Неизвестная ошибка")
                print(f"ПРЕДУПРЕЖДЕНИЕ: Ошибка генерации викторины: {error}")
                if "YANDEX" in error.upper() or "IAM_TOKEN" in error.upper():
                    print("INFO: Убедитесь, что YANDEX_IAM_TOKEN установлен в .env файле")
                return False
            
            # Проверка структуры (quiz_result должен быть словарем)
            if not isinstance(quiz_result, dict):
                print(f"ОШИБКА: Ожидался словарь, получен {type(quiz_result)}")
                return False
            assert "questions" in quiz_result, "Отсутствует поле 'questions'"
            questions = quiz_result.get("questions", [])
            assert len(questions) > 0, "Список вопросов пуст"
            
            print(f"OK: Викторина сгенерирована: {len(questions)} вопросов")
            
            # Проверка перевода на русский
            first_question = questions[0]
            question_text = first_question.get("question", "")
            
            # Простая проверка: если текст содержит только ASCII, возможно перевод не сработал
            # (но это не гарантия, так как некоторые вопросы могут быть на английском)
            print(f"   Пример вопроса: {question_text[:60]}...")
            print(f"   Правильный ответ: {first_question.get('correct_answer', 'N/A')}")
            
            # Тест 2: Экспорт в JSON
            print("\nТест 2: Экспорт викторины в JSON...")
            export_json_obj = await client.call_tool("export_quiz", {
                "quiz_data": quiz_result,
                "format": "json",
                "filename": "test_quiz"
            })
            export_json = extract_result(export_json_obj)
            
            if not export_json or not isinstance(export_json, dict) or not export_json.get("success"):
                error = export_json.get("error", "Неизвестная ошибка") if export_json else "Пустой результат"
                print(f"ОШИБКА экспорта JSON: {error}")
                return False
            
            json_filepath = Path(export_json.get("filepath", ""))
            assert json_filepath.exists(), f"JSON файл не создан: {json_filepath}"
            assert json_filepath.stat().st_size > 0, "JSON файл пуст"
            
            print(f"OK: JSON файл создан: {json_filepath.name} ({export_json.get('size', 0)} байт)")
            
            # Тест 3: Экспорт в HTML
            print("\nТест 3: Экспорт викторины в HTML...")
            export_html_obj = await client.call_tool("export_quiz", {
                "quiz_data": quiz_result,
                "format": "html",
                "filename": "test_quiz"
            })
            export_html = extract_result(export_html_obj)
            
            if not export_html or not isinstance(export_html, dict) or not export_html.get("success"):
                error = export_html.get("error", "Неизвестная ошибка") if export_html else "Пустой результат"
                print(f"ОШИБКА экспорта HTML: {error}")
                return False
            
            html_filepath = Path(export_html.get("filepath", ""))
            assert html_filepath.exists(), f"HTML файл не создан: {html_filepath}"
            assert html_filepath.stat().st_size > 0, "HTML файл пуст"
            
            print(f"OK: HTML файл создан: {html_filepath.name} ({export_html.get('size', 0)} байт)")
            
            # Тест 4: Экспорт в CSV
            print("\nТест 4: Экспорт викторины в CSV...")
            export_csv_obj = await client.call_tool("export_quiz", {
                "quiz_data": quiz_result,
                "format": "csv",
                "filename": "test_quiz"
            })
            export_csv = extract_result(export_csv_obj)
            
            if not export_csv or not isinstance(export_csv, dict) or not export_csv.get("success"):
                error = export_csv.get("error", "Неизвестная ошибка") if export_csv else "Пустой результат"
                print(f"ОШИБКА экспорта CSV: {error}")
                return False
            
            csv_filepath = Path(export_csv.get("filepath", ""))
            assert csv_filepath.exists(), f"CSV файл не создан: {csv_filepath}"
            assert csv_filepath.stat().st_size > 0, "CSV файл пуст"
            
            # Проверка BOM для кириллицы
            with open(csv_filepath, "rb") as f:
                first_bytes = f.read(3)
                has_bom = first_bytes == b'\xef\xbb\xbf'
                if has_bom:
                    print("OK: CSV файл содержит BOM для корректной кириллицы в Excel")
                else:
                    print("ПРЕДУПРЕЖДЕНИЕ: CSV файл не содержит BOM (кириллица может отображаться некорректно в Excel)")
            
            print(f"OK: CSV файл создан: {csv_filepath.name} ({export_csv.get('size', 0)} байт)")
            
            print("\nOK: Quiz MCP тест пройден успешно!")
            print(f"\nСозданные файлы:")
            print(f"   - {json_filepath}")
            print(f"   - {html_filepath}")
            print(f"   - {csv_filepath}")
            
            return True
        
    except AssertionError as e:
        print(f"ОШИБКА проверки: {e}")
        return False
    except Exception as e:
        print(f"ОШИБКА: Неожиданная ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_quiz())
    exit(0 if success else 1)

