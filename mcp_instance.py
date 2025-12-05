"""
Единый экземпляр FastMCP для всех инструментов.
Этот файл должен быть импортирован во всех модулях с инструментами.
"""
from fastmcp import FastMCP

mcp = FastMCP("MCP Servers")

