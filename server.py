"""
Точка входа для запуска MCP сервера.
Импорты инструментов обязательны для регистрации декораторов.
"""
from mcp_instance import mcp

# Импорты инструментов для регистрации декораторов
from tools.get_images import get_images  # noqa: F401
from tools.get_quiz import get_quiz  # noqa: F401
from tools.export_quiz import export_quiz  # noqa: F401
from tools.get_text_from_wiki import get_text_from_wiki

if __name__ == "__main__":
    mcp.run()

