"""
Инструмент для экспорта викторин в различные форматы (JSON, HTML, CSV).
"""
import os
import json
import csv
from datetime import datetime
from typing import Dict, Optional
from pathlib import Path
import aiofiles
from pydantic import Field
from jinja2 import Template

from mcp_instance import mcp

# Создаем папку exports, если её нет
EXPORTS_DIR = Path("exports")
EXPORTS_DIR.mkdir(exist_ok=True)


def load_html_template() -> str:
    """Загружает HTML шаблон из файла."""
    template_path = Path("templates/quiz_template.html")
    if template_path.exists():
        with open(template_path, "r", encoding="utf-8") as f:
            return f.read()
    return ""


@mcp.tool()
async def export_quiz(
    quiz_data: Dict = Field(..., description="Данные викторины для экспорта"),
    format: str = Field("json", description="Формат экспорта: json, html, csv"),
    filename: Optional[str] = Field(None, description="Имя файла (без расширения). Если не указано, будет сгенерировано автоматически")
) -> Dict:
    """
    Экспорт викторины в файл (JSON, HTML или CSV).
    
    Args:
        quiz_data: Словарь с данными викторины (результат get_quiz)
        format: Формат экспорта (json, html, csv)
        filename: Имя файла без расширения (опционально)
    
    Returns:
        Словарь с информацией о созданном файле
    """
    if not quiz_data.get("success"):
        return {
            "success": False,
            "error": "Данные викторины некорректны или отсутствуют"
        }
    
    # Генерируем имя файла, если не указано
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        topic_safe = "".join(c for c in quiz_data.get("topic", "quiz") if c.isalnum() or c in (" ", "-", "_")).strip()[:30]
        topic_safe = topic_safe.replace(" ", "_")
        filename = f"quiz_{topic_safe}_{timestamp}"
    
    format = format.lower()
    
    if format == "json":
        return await _export_json(quiz_data, filename)
    elif format == "html":
        return await _export_html(quiz_data, filename)
    elif format == "csv":
        return await _export_csv(quiz_data, filename)
    else:
        return {
            "success": False,
            "error": f"Неподдерживаемый формат: {format}. Используйте: json, html, csv"
        }


async def _export_json(quiz_data: Dict, filename: str) -> Dict:
    """Экспорт в JSON формат."""
    filepath = EXPORTS_DIR / f"{filename}.json"
    
    try:
        async with aiofiles.open(filepath, "w", encoding="utf-8") as f:
            await f.write(json.dumps(quiz_data, ensure_ascii=False, indent=2))
        
        return {
            "success": True,
            "format": "json",
            "filename": filepath.name,
            "filepath": str(filepath.absolute()),
            "size": filepath.stat().st_size
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Ошибка при сохранении JSON: {str(e)}"
        }


async def _export_html(quiz_data: Dict, filename: str) -> Dict:
    """Экспорт в HTML формат с использованием Jinja2 шаблона."""
    filepath = EXPORTS_DIR / f"{filename}.html"
    
    try:
        template_content = load_html_template()
        if not template_content:
            return {
                "success": False,
                "error": "HTML шаблон не найден в templates/quiz_template.html"
            }
        
        template = Template(template_content)
        
        # Подготавливаем данные для шаблона
        template_data = {
            "topic": quiz_data.get("topic", "Неизвестная тема"),
            "amount": len(quiz_data.get("questions", [])),
            "category": quiz_data.get("questions", [{}])[0].get("category", "Unknown") if quiz_data.get("questions") else "Unknown",
            "questions": quiz_data.get("questions", [])
        }
        
        html_content = template.render(**template_data)
        
        async with aiofiles.open(filepath, "w", encoding="utf-8") as f:
            await f.write(html_content)
        
        return {
            "success": True,
            "format": "html",
            "filename": filepath.name,
            "filepath": str(filepath.absolute()),
            "size": filepath.stat().st_size
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Ошибка при сохранении HTML: {str(e)}"
        }


async def _export_csv(quiz_data: Dict, filename: str) -> Dict:
    """Экспорт в CSV формат с поддержкой кириллицы для Excel."""
    filepath = EXPORTS_DIR / f"{filename}.csv"
    
    try:
        questions = quiz_data.get("questions", [])
        
        # Используем синхронную запись для CSV с BOM
        with open(filepath, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f, delimiter=",", quoting=csv.QUOTE_MINIMAL)
            
            # Заголовки
            writer.writerow([
                "Номер",
                "Вопрос",
                "Правильный ответ",
                "Неправильные ответы",
                "Сложность",
                "Тип",
                "Категория"
            ])
            
            # Данные
            for idx, question in enumerate(questions, 1):
                incorrect_answers = " | ".join(question.get("incorrect_answers", []))
                writer.writerow([
                    idx,
                    question.get("question", ""),
                    question.get("correct_answer", ""),
                    incorrect_answers,
                    question.get("difficulty", ""),
                    question.get("type", ""),
                    question.get("category", "")
                ])
        
        return {
            "success": True,
            "format": "csv",
            "filename": filepath.name,
            "filepath": str(filepath.absolute()),
            "size": filepath.stat().st_size,
            "note": "Файл сохранен с BOM для корректного отображения кириллицы в Excel"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Ошибка при сохранении CSV: {str(e)}"
        }


