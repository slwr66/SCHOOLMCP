"""
Инструмент для генерации викторин через OpenTDB с автоматическим переводом на русский.
"""
from typing import Optional, Dict
from pydantic import Field

from mcp_instance import mcp
from tools.utils import fetch_category_id, fetch_questions_from_opentdb, translate_batch


@mcp.tool()
async def get_quiz(
    topic: str = Field(..., description="Тема викторины"),
    amount: int = Field(10, ge=1, le=50, description="Количество вопросов (1-50)"),
    difficulty: Optional[str] = Field(None, description="Сложность: easy, medium, hard"),
    question_type: Optional[str] = Field(None, description="Тип вопроса: multiple, boolean")
) -> Dict:
    """
    Генерация викторины на заданную тему с автоматическим переводом на русский язык.
    
    Args:
        topic: Тема викторины
        amount: Количество вопросов (1-50)
        difficulty: Сложность вопросов (опционально)
        question_type: Тип вопроса (опционально)
    
    Returns:
        Словарь с переведенными вопросами викторины
    """
    # Шаг 1: Найти категорию по теме
    category_id = await fetch_category_id(topic)
    
    # Шаг 2: Получить вопросы из OpenTDB
    opentdb_data = await fetch_questions_from_opentdb(
        category_id=category_id,
        amount=amount,
        difficulty=difficulty,
        question_type=question_type
    )
    
    # Проверка на ошибки
    if opentdb_data.get("response_code") != 0:
        error_msg = opentdb_data.get("error", "Неизвестная ошибка при получении вопросов")
        return {
            "success": False,
            "error": error_msg,
            "topic": topic,
            "category_id": category_id
        }
    
    questions = opentdb_data.get("results", [])
    
    if not questions:
        return {
            "success": False,
            "error": "Не найдено вопросов для данной темы",
            "topic": topic,
            "category_id": category_id
        }
    
    # Шаг 3: Собрать все тексты для перевода в один плоский список
    text_pool = []
    text_indices = []  # Для отслеживания, к какому вопросу относится каждый текст
    
    for q_idx, question in enumerate(questions):
        # Вопрос
        text_pool.append(question["question"])
        text_indices.append(("question", q_idx))
        
        # Правильный ответ
        text_pool.append(question["correct_answer"])
        text_indices.append(("correct_answer", q_idx))
        
        # Неправильные ответы
        for ans_idx in range(len(question["incorrect_answers"])):
            text_pool.append(question["incorrect_answers"][ans_idx])
            text_indices.append(("incorrect_answer", q_idx, ans_idx))
    
    # Шаг 4: Пакетный перевод всех текстов
    translated_texts = await translate_batch(text_pool, target="ru")
    
    # Шаг 5: Разобрать переведенные тексты обратно в структуру вопросов
    translated_questions = []
    text_idx = 0
    
    for question in questions:
        translated_q = {
            "category": question["category"],
            "type": question["type"],
            "difficulty": question["difficulty"],
            "question": translated_texts[text_idx] if text_idx < len(translated_texts) else question["question"],
            "correct_answer": translated_texts[text_idx + 1] if text_idx + 1 < len(translated_texts) else question["correct_answer"],
            "incorrect_answers": []
        }
        text_idx += 2
        
        # Неправильные ответы
        num_incorrect = len(question["incorrect_answers"])
        for i in range(num_incorrect):
            if text_idx < len(translated_texts):
                translated_q["incorrect_answers"].append(translated_texts[text_idx])
            else:
                translated_q["incorrect_answers"].append(question["incorrect_answers"][i])
            text_idx += 1
        
        # Формируем все варианты ответов для удобства
        all_answers = [translated_q["correct_answer"]] + translated_q["incorrect_answers"]
        translated_q["all_answers"] = all_answers
        
        translated_questions.append(translated_q)
    
    return {
        "success": True,
        "topic": topic,
        "category_id": category_id,
        "amount": len(translated_questions),
        "questions": translated_questions
    }

