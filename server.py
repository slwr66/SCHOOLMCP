"""
Точка входа для запуска MCP сервера.
Импорты инструментов обязательны для регистрации декораторов.
"""
from mcp_instance import mcp

# Импорты инструментов для регистрации декораторов
from tools.get_images import get_images  # noqa: F401
from tools.get_quiz import get_quiz  # noqa: F401
from tools.export_quiz import export_quiz  # noqa: F401
from tools.get_text_from_wiki import get_text_from_wiki  # noqa: F401
from tools.wiki_get_material import wiki_get_material  # noqa: F401
from tools.schedule_lesson import schedule_lesson  # noqa: F401

if __name__ == "__main__":
    mcp.run()
