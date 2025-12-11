"""
Быстрый тест создания презентации через Aspose Slides.
"""
import asyncio
from tools.aspose_slides_module import build_presentation


async def main():
    print("Создание презентации через Aspose Slides...")
    print("Локальная библиотека, без внешних API")
    print("-" * 50)
    
    result = await build_presentation(
        title="Тестовая презентация",
        slides_data=[
            {
                "title": "Введение", 
                "text": "Это тестовая презентация, созданная с помощью Aspose Slides для Python."
            },
            {
                "title": "Преимущества Aspose Slides", 
                "text": "• Работает локально, без внешних API\n• Создаёт слайды программно\n• Поддерживает изображения\n• Полный контроль над форматированием"
            },
            {
                "title": "Пример с изображением",
                "text": "Этот слайд содержит изображение из Unsplash.",
                "image_url": "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=400"
            },
            {
                "title": "Заключение",
                "text": "Aspose Slides — мощная библиотека для создания презентаций PowerPoint!"
            }
        ]
    )
    
    if "error" in result:
        print(f"\nОшибка: {result['error']}")
        print("\n" + "=" * 50)
        print("Для работы Aspose Slides необходимо:")
        print("1. Установить библиотеку: pip install aspose.slides")
        print("2. (Опционально) Добавить лицензию для удаления watermark")
        print("=" * 50)
    else:
        print(f"\nПрезентация создана!")
        print(f"Путь к файлу: {result['file_path']}")
        print(f"Имя файла: {result['file_name']}")
        print(f"Количество слайдов: {result['slides_count']}")
        print(f"Размер файла: {result['file_size']} байт")
        
        print("\n" + "=" * 50)
        print("Примечание: Без лицензии Aspose презентации")
        print("будут содержать watermark 'Evaluation Only'.")
        print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
