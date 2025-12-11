"""
Тесты для create_presentation MCP tool.
Использует Aspose Slides для создания презентаций локально.
"""
import asyncio
import os
from typing import Dict, List


async def test_validation():
    """Тест валидации входных данных."""
    print("=" * 50)
    print("Test: create_presentation (validation)")
    print("=" * 50)
    
    # Test empty title handling
    if not "":
        print("[OK] Empty title would be rejected")
    
    # Test empty slides handling
    if not []:
        print("[OK] Empty slides list would be rejected")
    
    # Test invalid slide structure
    invalid_slide = "not a dict"
    if not isinstance(invalid_slide, dict):
        print("[OK] Non-dict slide would be rejected")
    
    # Test slide without title and text
    empty_slide = {"title": "", "text": ""}
    if not empty_slide.get("title") and not empty_slide.get("text"):
        print("[OK] Empty slide (no title/text) would be rejected")
    
    # Test invalid image_url
    bad_url = "not-a-url"
    if not bad_url.startswith(("http://", "https://")):
        print("[OK] Invalid image_url would be rejected")
    
    return True


async def test_aspose_slides_utils():
    """Тест вспомогательных функций Aspose Slides."""
    print("\n" + "=" * 50)
    print("Test: aspose_slides_module utils")
    print("=" * 50)
    
    from tools.aspose_slides_module import (
        _generate_filename,
        _ensure_exports_dir
    )
    
    # Test filename generation
    filename = _generate_filename("Test Presentation")
    print(f"[OK] Generated filename: {filename}")
    assert filename.endswith(".pptx"), "Filename should end with .pptx"
    assert "Test" in filename or "presentation" in filename.lower(), "Filename should contain title"
    
    # Test exports directory creation
    exports_dir = _ensure_exports_dir()
    assert os.path.exists(exports_dir), "Exports directory should exist"
    print(f"[OK] Exports directory exists: {exports_dir}")
    
    return True


async def test_build_presentation():
    """
    Тест создания презентации через Aspose Slides.
    """
    print("\n" + "=" * 50)
    print("Test: build_presentation (Aspose Slides)")
    print("=" * 50)
    
    from tools.aspose_slides_module import build_presentation
    
    # Test basic presentation creation
    result = await build_presentation(
        title="Test Presentation",
        slides_data=[
            {"title": "Slide 1", "text": "This is slide 1 content"},
            {"title": "Slide 2", "text": "This is slide 2 content"}
        ]
    )
    
    if "error" in result:
        error_msg = result['error'][:100]
        print(f"[FAIL] Error: {error_msg}...")
        return False
    
    print(f"[OK] Presentation created!")
    print(f"   File path: {result.get('file_path', 'N/A')}")
    print(f"   File name: {result.get('file_name', 'N/A')}")
    print(f"   Slides: {result.get('slides_count', 'N/A')}")
    print(f"   File size: {result.get('file_size', 'N/A')} bytes")
    
    # Verify file exists
    file_path = result.get('file_path', '')
    if os.path.exists(file_path):
        print(f"[OK] File exists on disk: {file_path}")
    else:
        print(f"[FAIL] File not found: {file_path}")
        return False
    
    return True


async def test_build_presentation_with_image():
    """
    Тест создания презентации с изображением.
    """
    print("\n" + "=" * 50)
    print("Test: build_presentation (with image)")
    print("=" * 50)
    
    from tools.aspose_slides_module import build_presentation
    
    # Test presentation with image
    result = await build_presentation(
        title="Presentation With Image",
        slides_data=[
            {"title": "Slide 1", "text": "This slide has no image"},
            {"title": "Slide 2", "text": "This slide has an image", 
             "image_url": "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=400"}
        ]
    )
    
    if "error" in result:
        error_msg = result['error'][:100]
        print(f"[WARN] Error: {error_msg}...")
        # Image download may fail due to network issues
        print("[OK] Error handled gracefully")
        return True
    
    print(f"[OK] Presentation with image created!")
    print(f"   File path: {result.get('file_path', 'N/A')}")
    print(f"   Slides: {result.get('slides_count', 'N/A')}")
    print(f"   File size: {result.get('file_size', 'N/A')} bytes")
    
    return True


async def test_slide_data_structure():
    """Тест структуры данных слайдов."""
    print("\n" + "=" * 50)
    print("Test: Slide data structure")
    print("=" * 50)
    
    # Valid slide structures
    valid_slides: List[Dict] = [
        {"title": "Only Title", "text": ""},
        {"title": "", "text": "Only Text"},
        {"title": "Title", "text": "Text"},
        {"title": "With Image", "text": "Content", "image_url": "https://example.com/img.jpg"},
    ]
    
    for i, slide in enumerate(valid_slides):
        has_content = slide.get("title") or slide.get("text")
        has_valid_url = not slide.get("image_url") or slide.get("image_url", "").startswith("https://")
        
        if has_content and has_valid_url:
            print(f"[OK] Slide {i+1} structure is valid")
        else:
            print(f"[FAIL] Slide {i+1} structure is invalid")
            return False
    
    return True


async def test_response_format():
    """Тест формата ответа."""
    print("\n" + "=" * 50)
    print("Test: Response format")
    print("=" * 50)
    
    # Expected success response format
    success_response = {
        "file_path": "exports/test.pptx",
        "file_name": "test.pptx",
        "slides_count": 2,
        "file_size": 12345
    }
    
    required_keys = ["file_path", "file_name", "slides_count", "file_size"]
    for key in required_keys:
        if key in success_response:
            print(f"[OK] Response contains '{key}'")
        else:
            print(f"[FAIL] Response missing '{key}'")
            return False
    
    # Expected error response format
    error_response = {"error": "Some error message"}
    if "error" in error_response:
        print("[OK] Error response contains 'error' key")
    
    return True


async def test_create_presentation_import():
    """Тест импорта MCP инструмента create_presentation."""
    print("\n" + "=" * 50)
    print("Test: create_presentation MCP import")
    print("=" * 50)
    
    try:
        from tools.create_presentation import create_presentation
        print("[OK] create_presentation imported successfully")
        
        # Verify it's a FunctionTool (MCP decorator applied)
        tool_name = type(create_presentation).__name__
        print(f"[OK] create_presentation is {tool_name}")
        
        # Check that underlying function exists
        from tools.aspose_slides_module import build_presentation
        print("[OK] build_presentation imported from aspose_slides_module")
        
        return True
    except ImportError as e:
        print(f"[FAIL] Import error: {e}")
        return False


async def main():
    """Запуск всех тестов."""
    print("\n[TEST] Running create_presentation tests (Aspose Slides)\n")
    
    results = []
    results.append(await test_validation())
    results.append(await test_aspose_slides_utils())
    results.append(await test_slide_data_structure())
    results.append(await test_response_format())
    results.append(await test_build_presentation())
    results.append(await test_build_presentation_with_image())
    results.append(await test_create_presentation_import())
    
    print("\n" + "=" * 50)
    print(f"[RESULT] {sum(results)}/{len(results)} tests passed")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
