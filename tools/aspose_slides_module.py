"""
Утилиты для работы с Aspose Slides для Python.
Создание презентаций PPTX локально без внешних API.
https://products.aspose.com/slides/python-net/
"""
import os
import uuid
import io
from datetime import datetime
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Директория для сохранения презентаций
EXPORTS_DIR = os.getenv("EXPORTS_DIR", "exports")

# Путь к файлу лицензии Aspose (опционально, без лицензии будет watermark)
ASPOSE_LICENSE_PATH = os.getenv("ASPOSE_LICENSE_PATH", "")


def _apply_license() -> bool:
    """
    Применение лицензии Aspose Slides (если указана).
    Без лицензии презентации будут содержать watermark.
    
    Returns:
        True если лицензия применена, False если нет.
    """
    if not ASPOSE_LICENSE_PATH or not os.path.exists(ASPOSE_LICENSE_PATH):
        return False
    
    try:
        import aspose.slides as slides
        license = slides.License()
        license.set_license(ASPOSE_LICENSE_PATH)
        return True
    except Exception:
        return False


def _ensure_exports_dir() -> str:
    """
    Создание директории для экспорта, если она не существует.
    
    Returns:
        Путь к директории экспорта.
    """
    os.makedirs(EXPORTS_DIR, exist_ok=True)
    return EXPORTS_DIR


def _generate_filename(title: str) -> str:
    """
    Генерация уникального имени файла для презентации.
    
    Args:
        title: Заголовок презентации.
        
    Returns:
        Уникальное имя файла с расширением .pptx
    """
    # Очищаем заголовок от недопустимых символов
    safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_'))
    safe_title = safe_title.strip()[:50]
    
    if not safe_title:
        safe_title = "presentation"
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = uuid.uuid4().hex[:8]
    
    return f"{safe_title}_{timestamp}_{unique_id}.pptx"


async def _download_image(url: str) -> Optional[bytes]:
    """
    Загрузка изображения по URL.
    
    Args:
        url: URL изображения.
        
    Returns:
        Байты изображения или None при ошибке.
    """
    try:
        import httpx
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            if response.status_code == 200:
                return response.content
    except Exception:
        pass
    return None


def _add_title_to_slide(slide, title: str, slides_module, drawing_module) -> None:
    """
    Добавление заголовка на слайд.
    
    Args:
        slide: Объект слайда Aspose.
        title: Текст заголовка.
        slides_module: Модуль aspose.slides.
        drawing_module: Модуль aspose.pydrawing.
    """
    title_box = slide.shapes.add_auto_shape(
        slides_module.ShapeType.RECTANGLE,
        50, 30,  # x, y (в пунктах)
        620, 60  # width, height
    )
    title_box.fill_format.fill_type = slides_module.FillType.NO_FILL
    title_box.line_format.fill_format.fill_type = slides_module.FillType.NO_FILL
    title_box.text_frame.text = title
    
    # Стиль заголовка
    for para in title_box.text_frame.paragraphs:
        for portion in para.portions:
            portion.portion_format.font_bold = slides_module.NullableBool.TRUE
            portion.portion_format.font_height = 28
            portion.portion_format.fill_format.fill_type = slides_module.FillType.SOLID
            portion.portion_format.fill_format.solid_fill_color.color = drawing_module.Color.dark_blue


def _add_text_box(
    slide, 
    text: str, 
    x: float, 
    y: float, 
    width: float, 
    height: float,
    slides_module
) -> None:
    """
    Добавление текстового блока на слайд с заданными параметрами.
    
    Args:
        slide: Объект слайда Aspose.
        text: Текст контента.
        x: Позиция X (в пунктах).
        y: Позиция Y (в пунктах).
        width: Ширина блока (в пунктах).
        height: Высота блока (в пунктах).
        slides_module: Модуль aspose.slides.
    """
    content_box = slide.shapes.add_auto_shape(
        slides_module.ShapeType.RECTANGLE,
        x, y, width, height
    )
    content_box.fill_format.fill_type = slides_module.FillType.NO_FILL
    content_box.line_format.fill_format.fill_type = slides_module.FillType.NO_FILL
    content_box.text_frame.text = text
    
    # Стиль текста
    for para in content_box.text_frame.paragraphs:
        for portion in para.portions:
            portion.portion_format.font_height = 16


def _add_image_to_slide(
    pres, 
    slide, 
    image_bytes: bytes, 
    slides_module
) -> bool:
    """
    Добавление изображения на слайд.
    
    Args:
        pres: Объект презентации Aspose.
        slide: Объект слайда Aspose.
        image_bytes: Байты изображения.
        slides_module: Модуль aspose.slides.
        
    Returns:
        True если изображение добавлено успешно.
    """
    try:
        # Создаем поток из байтов
        image_stream = io.BytesIO(image_bytes)
        
        # Добавляем изображение в коллекцию презентации
        image = pres.images.add_image(image_stream)
        
        # Добавляем рамку с изображением на слайд
        # Позиционируем справа от текста
        slide.shapes.add_picture_frame(
            slides_module.ShapeType.RECTANGLE,
            400, 100,  # x, y
            280, 200,  # width, height
            image
        )
        return True
    except Exception:
        return False


async def build_presentation(
    title: str,
    slides_data: List[Dict[str, str]]
) -> Dict[str, Any]:
    """
    Создает презентацию PowerPoint с помощью Aspose Slides.
    
    Презентация создаётся локально, без внешних API.
    Поддерживает создание неограниченного количества слайдов,
    добавление заголовков, текста и изображений.
    
    Args:
        title: Заголовок презентации.
        slides_data: Список слайдов. Каждый слайд — словарь с ключами:
            - title: str — заголовок слайда
            - text: str — основной текст слайда
            - image_url: str (опционально) — URL изображения для слайда
    
    Returns:
        Словарь с информацией о созданной презентации:
        {
            "file_path": str,      # Путь к сохраненному файлу
            "file_name": str,      # Имя файла
            "slides_count": int,   # Количество слайдов
            "file_size": int       # Размер файла в байтах
        }
        
        В случае ошибки:
        {
            "error": str           # Описание ошибки
        }
    """
    # Импортируем Aspose модули
    try:
        import aspose.slides as slides_module
        import aspose.pydrawing as drawing_module
    except ImportError as e:
        return {
            "error": "Aspose Slides не установлен. "
                     "Выполните: pip install aspose.slides"
        }
    
    # Применяем лицензию (если есть)
    _apply_license()
    
    # Создаем директорию для экспорта
    try:
        _ensure_exports_dir()
    except OSError as e:
        return {"error": f"Не удалось создать директорию для экспорта: {str(e)}"}
    
    try:
        # Создаем новую презентацию
        with slides_module.Presentation() as pres:
            # Удаляем пустой слайд по умолчанию
            if len(pres.slides) > 0:
                pres.slides.remove_at(0)
            
            # Ищем пустой layout (BLANK) без плейсхолдеров
            blank_layout = None
            for layout in pres.layout_slides:
                if layout.layout_type == slides_module.SlideLayoutType.BLANK:
                    blank_layout = layout
                    break
            
            # Если BLANK layout не найден, используем первый и будем удалять shapes
            if blank_layout is None:
                blank_layout = pres.layout_slides[0]
            
            # Создаем слайды
            for slide_data in slides_data:
                # Добавляем новый слайд
                slide = pres.slides.add_empty_slide(blank_layout)
                
                # Удаляем все дефолтные shapes (плейсхолдеры) со слайда
                # Перебираем в обратном порядке, чтобы удаление не сбивало индексы
                shapes_to_remove = []
                for i in range(len(slide.shapes)):
                    shape = slide.shapes[i]
                    # Удаляем все плейсхолдеры
                    if shape.placeholder is not None:
                        shapes_to_remove.append(shape)
                
                for shape in shapes_to_remove:
                    slide.shapes.remove(shape)
                
                slide_title = slide_data.get("title", "")
                slide_text = slide_data.get("text", "")
                image_url = slide_data.get("image_url")
                
                has_image = False
                
                # Загружаем изображение, если указано
                if image_url:
                    image_bytes = await _download_image(image_url)
                    if image_bytes:
                        has_image = _add_image_to_slide(
                            pres, slide, image_bytes, slides_module
                        )
                
                # Добавляем заголовок
                if slide_title:
                    _add_title_to_slide(slide, slide_title, slides_module, drawing_module)
                
                # Добавляем текст (позиция зависит от наличия изображения)
                if slide_text:
                    # Если есть изображение, текст левее и уже
                    if has_image:
                        _add_text_box(slide, slide_text, 50, 100, 330, 300, slides_module)
                    else:
                        _add_text_box(slide, slide_text, 50, 100, 620, 350, slides_module)
            
            # Генерируем имя файла и сохраняем
            filename = _generate_filename(title)
            file_path = os.path.join(EXPORTS_DIR, filename)
            
            pres.save(file_path, slides_module.export.SaveFormat.PPTX)
            
            # Получаем размер файла
            file_size = os.path.getsize(file_path)
            
            return {
                "file_path": file_path,
                "file_name": filename,
                "slides_count": len(slides_data),
                "file_size": file_size
            }
            
    except Exception as e:
        return {
            "error": f"Ошибка создания презентации: {str(e)}"
        }

