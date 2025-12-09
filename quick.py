import asyncio
from tools.google_slides import build_presentation

async def main():
    result = await build_presentation(
        title="Тестовая презентация",
        slides=[
            {"title": "Слайд 1", "text": "Привет, это тест!"},
            {"title": "Слайд 2", "text": "Второй слайд с картинкой", 
             "image_url": "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=800"},
             {"title": "Слайд 3", "text": "Третий слайд с картинкой", 
             "image_url": "https://images.unsplash.com/photo-1585187012199-269f89f2238f"},
             {"title": "Слайд залупа", "text": "несколько картинок?", 
             "image_url": "https://images.unsplash.com/photo-1585187012199-269f89f2238f", 
             "image_url2": "https://images.unsplash.com/photo-1585187012199-269f89f2238f"}
        ],
        use_service_account=False
    )
    
    if "error" in result:
        print(f"Ошибка: {result['error']}")
    else:
        print(f"Презентация создана!")
        print(f"URL: {result['presentation_url']}")

asyncio.run(main())