"""
Точка входа для запуска MCP сервера.
Импорты инструментов обязательны для регистрации декораторов.
"""
import os
import sys
from typing import Any
from mcp_instance import mcp

# Импорты инструментов для регистрации декораторов
from tools.get_images import get_images  # noqa: F401
from tools.get_quiz import get_quiz  # noqa: F401
from tools.export_quiz import export_quiz  # noqa: F401
from tools.get_text_from_wiki import get_text_from_wiki  # noqa: F401
from tools.wiki_get_material import wiki_get_material  # noqa: F401
from tools.schedule_lesson import schedule_lesson  # noqa: F401
from tools.create_presentation import create_presentation  # noqa: F401


def validate_configuration() -> None:
    """Проверка конфигурации перед запуском."""
    mode = os.getenv("MCP_MODE", "sse").lower()
    
    if mode not in ["stdio", "sse"]:
        print(f"❌ ОШИБКА: Неверный MCP_MODE={mode}. Допустимые значения: stdio, sse")
        sys.exit(1)
    
    if mode == "sse":
        try:
            port = int(os.getenv("PORT", 8000))
            if port < 1 or port > 65535:
                raise ValueError(f"Порт должен быть в диапазоне 1-65535, получено: {port}")
        except ValueError as e:
            print(f"❌ ОШИБКА: Неверный PORT: {e}")
            sys.exit(1)
        
        host = os.getenv("HOST", "0.0.0.0")
        if not host:
            print("❌ ОШИБКА: HOST не может быть пустым")
            sys.exit(1)


def check_tools_registration() -> None:
    """Проверка регистрации инструментов."""
    try:
        # Примечание: инструменты регистрируются через декораторы @mcp.tool()
        # при импорте модулей. Проверка может не найти их через внутренние
        # атрибуты, но это не означает, что они не зарегистрированы.
        
        # Пытаемся получить список инструментов через внутренний атрибут FastMCP
        # FastMCP хранит инструменты в разных местах в зависимости от версии
        tools_count = 0
        tools_list = []
        
        # Пробуем разные способы доступа к инструментам
        # 1. Через метод list_tools (если есть)
        if hasattr(mcp, 'list_tools'):
            try:
                tools = mcp.list_tools()
                tools_count = len(tools) if tools else 0
                tools_list = tools if tools else []
            except Exception:
                pass
        
        # 2. Через внутренний атрибут _tools (dict)
        if tools_count == 0 and hasattr(mcp, '_tools'):
            try:
                tools_dict = getattr(mcp, '_tools', {})
                if isinstance(tools_dict, dict):
                    tools_count = len(tools_dict)
                    tools_list = list(tools_dict.keys())
            except Exception:
                pass
        
        # 3. Через атрибут tools
        if tools_count == 0 and hasattr(mcp, 'tools'):
            try:
                tools_dict = getattr(mcp, 'tools', {})
                if isinstance(tools_dict, dict):
                    tools_count = len(tools_dict)
                    tools_list = list(tools_dict.keys())
            except Exception:
                pass
        
        # 4. Через _server._tools (внутренняя структура FastMCP)
        if tools_count == 0 and hasattr(mcp, '_server'):
            try:
                server = getattr(mcp, '_server')
                if hasattr(server, '_tools'):
                    tools_dict = getattr(server, '_tools', {})
                    if isinstance(tools_dict, dict):
                        tools_count = len(tools_dict)
                        tools_list = list(tools_dict.keys())
            except Exception:
                pass
        
        # 5. Через _server.tools (альтернативный путь)
        if tools_count == 0 and hasattr(mcp, '_server'):
            try:
                server = getattr(mcp, '_server')
                if hasattr(server, 'tools'):
                    tools_dict = getattr(server, 'tools', {})
                    if isinstance(tools_dict, dict):
                        tools_count = len(tools_dict)
                        tools_list = list(tools_dict.keys())
            except Exception:
                pass
        
        # 6. Через _call_tool_mcp (проверяем наличие инструментов через вызов)
        if tools_count == 0 and hasattr(mcp, '_call_tool_mcp'):
            try:
                # Пытаемся получить список через внутренний метод
                # Это может не сработать, но попробуем
                if hasattr(mcp, '_server'):
                    server = getattr(mcp, '_server')
                    # Проверяем все возможные места хранения
                    for attr_name in ['_tools', 'tools', '_registered_tools', 'registered_tools']:
                        if hasattr(server, attr_name):
                            tools_dict = getattr(server, attr_name)
                            if isinstance(tools_dict, dict) and len(tools_dict) > 0:
                                tools_count = len(tools_dict)
                                tools_list = list(tools_dict.keys())
                                break
            except Exception:
                pass
        
        # 7. Прямая проверка через dir() для отладки
        if tools_count == 0:
            # Выводим доступные атрибуты для отладки
            mcp_attrs = [attr for attr in dir(mcp) if not attr.startswith('__')]
            print(f"🔍 Доступные атрибуты FastMCP: {', '.join(mcp_attrs[:10])}...")
            
            # Пытаемся проверить через _server
            if hasattr(mcp, '_server'):
                try:
                    server = getattr(mcp, '_server')
                    server_attrs = [attr for attr in dir(server) if not attr.startswith('__')]
                    print(f"🔍 Доступные атрибуты _server: {', '.join(server_attrs[:10])}...")
                    
                    # Проверяем все атрибуты, которые могут содержать инструменты
                    for attr in server_attrs:
                        if 'tool' in attr.lower():
                            try:
                                value = getattr(server, attr)
                                if isinstance(value, dict):
                                    print(f"🔍 Найден словарь в {attr}: {len(value)} элементов")
                                    if len(value) > 0:
                                        tools_count = len(value)
                                        tools_list = list(value.keys())
                                        break
                            except Exception:
                                pass
                except Exception as e:
                    print(f"🔍 Ошибка при проверке _server: {e}")
        
        print(f"✅ Зарегистрировано инструментов: {tools_count}")
        
        if tools_count == 0:
            print("⚠️  ВНИМАНИЕ: Не удалось определить количество инструментов через внутренние атрибуты.")
            print("   Это может быть нормально - инструменты могут быть зарегистрированы, но недоступны для проверки.")
            print("   Сервер будет работать нормально, если инструменты действительно зарегистрированы.")
            print("   Проверьте работоспособность через /tools endpoint или подключение агента.")
        else:
            print("📋 Список инструментов:")
            if isinstance(tools_list, list) and len(tools_list) > 0:
                if isinstance(tools_list[0], str):
                    # Если это список строк (имен)
                    for tool_name in tools_list:
                        print(f"   - {tool_name}")
                else:
                    # Если это объекты инструментов
                    for tool in tools_list:
                        tool_name = getattr(tool, 'name', getattr(tool, '__name__', str(tool)))
                        print(f"   - {tool_name}")
            else:
                print("   (детали недоступны)")
                
    except Exception as e:
        print(f"⚠️  Предупреждение: Не удалось проверить список инструментов: {e}")
        print("   Продолжаем запуск...")
        import traceback
        traceback.print_exc()


def create_health_endpoints(base_app) -> Any:
    """Создание дополнительных endpoints для диагностики."""
    try:
        from starlette.applications import Starlette
        from starlette.routing import Route, Mount
        from starlette.responses import JSONResponse
        
        async def health_check(request):
            """Health check endpoint."""
            try:
                # Пытаемся получить количество инструментов
                tools_count = 0
                if hasattr(mcp, 'list_tools'):
                    tools = mcp.list_tools()
                    tools_count = len(tools) if tools else 0
                elif hasattr(mcp, '_tools'):
                    tools_count = len(getattr(mcp, '_tools', {}))
                elif hasattr(mcp, 'tools'):
                    tools_count = len(getattr(mcp, 'tools', {}))
                
                return JSONResponse({
                    "status": "ok",
                    "tools_count": tools_count,
                    "mode": os.getenv("MCP_MODE", "sse"),
                    "transport": os.getenv("MCP_TRANSPORT", "sse")
                })
            except Exception as e:
                return JSONResponse({
                    "status": "error",
                    "error": str(e)
                }, status_code=500)
        
        async def list_tools_endpoint(request):
            """Endpoint для просмотра зарегистрированных инструментов."""
            try:
                tools_list = []
                
                # Пытаемся получить список инструментов
                if hasattr(mcp, 'list_tools'):
                    tools = mcp.list_tools()
                    if tools:
                        for tool in tools:
                            tool_info = {
                                "name": getattr(tool, 'name', getattr(tool, '__name__', str(tool))),
                                "description": getattr(tool, 'description', ''),
                            }
                            if hasattr(tool, 'parameters'):
                                tool_info["parameters"] = tool.parameters
                            tools_list.append(tool_info)
                elif hasattr(mcp, '_tools'):
                    tools_dict = getattr(mcp, '_tools', {})
                    for tool_name, tool_obj in tools_dict.items():
                        tool_info = {
                            "name": tool_name,
                            "description": getattr(tool_obj, 'description', ''),
                        }
                        if hasattr(tool_obj, 'parameters'):
                            tool_info["parameters"] = tool_obj.parameters
                        tools_list.append(tool_info)
                elif hasattr(mcp, 'tools'):
                    tools_dict = getattr(mcp, 'tools', {})
                    for tool_name, tool_obj in tools_dict.items():
                        tool_info = {
                            "name": tool_name,
                            "description": getattr(tool_obj, 'description', ''),
                        }
                        if hasattr(tool_obj, 'parameters'):
                            tool_info["parameters"] = tool_obj.parameters
                        tools_list.append(tool_info)
                
                return JSONResponse({
                    "tools": tools_list,
                    "count": len(tools_list)
                })
            except Exception as e:
                return JSONResponse({
                    "error": str(e)
                }, status_code=500)
        
        async def root_endpoint(request):
            """Root endpoint."""
            return JSONResponse({
                "service": "MCP Server for EdTech",
                "version": "0.3.3",
                "status": "running",
                "endpoints": {
                    "health": "/health",
                    "tools": "/tools",
                    "mcp": "/sse" if os.getenv("MCP_TRANSPORT", "sse").lower() == "sse" else "/"
                }
            })
        
        # Проверяем, является ли base_app Starlette приложением
        if isinstance(base_app, Starlette):
            # Если это Starlette, добавляем routes
            base_app.routes.extend([
                Route("/health", health_check, methods=["GET"]),
                Route("/tools", list_tools_endpoint, methods=["GET"]),
                Route("/", root_endpoint, methods=["GET"]),
            ])
            return base_app
        else:
            # Если нет, создаем новое приложение с монтированием
            mcp_path = "/sse" if os.getenv("MCP_TRANSPORT", "sse").lower() == "sse" else "/"
            health_app = Starlette(routes=[
                Route("/health", health_check, methods=["GET"]),
                Route("/tools", list_tools_endpoint, methods=["GET"]),
                Route("/", root_endpoint, methods=["GET"]),
                Mount(mcp_path, app=base_app),
            ])
            return health_app
            
    except ImportError as e:
        print(f"⚠️  Предупреждение: Не удалось импортировать Starlette: {e}")
        print("   Health endpoints недоступны, но MCP сервер будет работать")
        return base_app
    except Exception as e:
        print(f"⚠️  Предупреждение: Не удалось создать health endpoints: {e}")
        print("   MCP сервер будет работать без дополнительных endpoints")
        import traceback
        traceback.print_exc()
        return base_app


if __name__ == "__main__":
    # Валидация конфигурации
    validate_configuration()
    
    # Режим работы: stdio (локально) или sse (удалённо через HTTP)
    mode = os.getenv("MCP_MODE", "sse").lower()
    
    if mode == "stdio":
        # Локальный режим через standard input/output (для тестирования)
        print("🔧 Запуск MCP сервера в режиме stdio (локально)")
        try:
            check_tools_registration()
            mcp.run()
        except KeyboardInterrupt:
            print("\n👋 Остановка сервера...")
            sys.exit(0)
        except Exception as e:
            print(f"❌ Критическая ошибка при запуске: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    else:
        # HTTP/SSE режим для удалённого подключения (Cloud.ru)
        import uvicorn
        
        port = int(os.getenv("PORT", 8000))
        host = os.getenv("HOST", "0.0.0.0")
        
        # Определяем тип транспорта (sse или http)
        transport = os.getenv("MCP_TRANSPORT", "sse").lower()
        
        # Проверка регистрации инструментов перед запуском
        check_tools_registration()
        
        try:
            if transport == "sse":
                print(f"🚀 Запуск MCP сервера в режиме SSE")
                print(f"📡 Слушаю на {host}:{port}")
                print(f"🌐 Endpoint: http://{host}:{port}/sse")
                # Используем старый метод sse_app() (работает, но показывает deprecation warning)
                # Подавляем предупреждение, так как новый API требует дополнительные параметры
                import warnings
                with warnings.catch_warnings():
                    warnings.filterwarnings("ignore", category=DeprecationWarning)
                    app = mcp.sse_app()
            else:
                print(f"🚀 Запуск MCP сервера в режиме HTTP")
                print(f"📡 Слушаю на {host}:{port}")
                print(f"🌐 Endpoint: http://{host}:{port}")
                # Получаем HTTP приложение из FastMCP (вызываем метод)
                app = mcp.http_app()
            
            # Добавляем health check endpoints
            app = create_health_endpoints(app)
            
            print(f"✅ Health check: http://{host}:{port}/health")
            print(f"✅ Tools list: http://{host}:{port}/tools")
            
        except Exception as e:
            print(f"❌ Ошибка при создании приложения: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
        
        # Запуск через uvicorn с приложением FastMCP
        try:
            uvicorn.run(
                app,
                host=host,
                port=port,
                log_level="info"
            )
        except KeyboardInterrupt:
            print("\n👋 Остановка сервера...")
            sys.exit(0)
        except Exception as e:
            print(f"❌ Критическая ошибка при запуске uvicorn: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
