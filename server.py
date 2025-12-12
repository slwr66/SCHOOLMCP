"""
Точка входа для запуска MCP сервера.
Импорты инструментов обязательны для регистрации декораторов.
"""
import os
import sys
import asyncio
import logging
import signal
from typing import Any
from mcp_instance import mcp

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

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
        logger.error(f"Неверный MCP_MODE={mode}. Допустимые значения: stdio, sse")
        sys.exit(1)
    
    if mode == "sse":
        try:
            port = int(os.getenv("PORT", 8000))
            if port < 1 or port > 65535:
                raise ValueError(f"Порт должен быть в диапазоне 1-65535, получено: {port}")
        except ValueError as e:
            logger.error(f"Неверный PORT: {e}")
            sys.exit(1)
        
        host = os.getenv("HOST", "0.0.0.0")
        if not host:
            logger.error("HOST не может быть пустым")
            sys.exit(1)
        
        # Проверка обязательных API ключей
        required_keys = ["UNSPLASH_ACCESS_KEY"]
        missing_keys = [key for key in required_keys if not os.getenv(key)]
        
        if missing_keys:
            logger.warning(f"Отсутствуют API ключи: {', '.join(missing_keys)}. Некоторые функции могут не работать.")
        
        # Проверка Yandex API (нужен либо API_KEY, либо IAM_TOKEN + FOLDER_ID)
        yandex_api_key = os.getenv("YANDEX_API_KEY")
        yandex_iam_token = os.getenv("YANDEX_IAM_TOKEN")
        yandex_folder_id = os.getenv("YANDEX_FOLDER_ID")
        
        if not yandex_api_key and not (yandex_iam_token and yandex_folder_id):
            logger.warning("Yandex API не настроен. Функция перевода может не работать.")


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
        
        logger.info(f"Зарегистрировано инструментов: {tools_count}")
        
        if tools_count == 0:
            logger.warning("Не удалось определить количество инструментов через внутренние атрибуты.")
            logger.warning("Это может быть нормально - инструменты могут быть зарегистрированы, но недоступны для проверки.")
            logger.warning("Сервер будет работать нормально, если инструменты действительно зарегистрированы.")
            logger.warning("Проверьте работоспособность через /tools endpoint или подключение агента.")
        else:
            logger.info("Список инструментов:")
            if isinstance(tools_list, list) and len(tools_list) > 0:
                if isinstance(tools_list[0], str):
                    # Если это список строк (имен)
                    for tool_name in tools_list:
                        logger.info(f"   - {tool_name}")
                else:
                    # Если это объекты инструментов
                    for tool in tools_list:
                        tool_name = getattr(tool, 'name', getattr(tool, '__name__', str(tool)))
                        logger.info(f"   - {tool_name}")
            else:
                logger.info("   (детали недоступны)")
                
    except Exception as e:
        logger.warning(f"Не удалось проверить список инструментов: {e}")
        logger.warning("Продолжаем запуск...")
        logger.debug("Traceback:", exc_info=True)


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
                    "call_tool": "/api/call-tool",
                    "mcp": "/sse" if os.getenv("MCP_TRANSPORT", "sse").lower() == "sse" else "/"
                }
            })
        
        async def call_tool_endpoint(request):
            """HTTP endpoint для вызова MCP инструментов (для тестирования)."""
            try:
                data = await request.json()
                tool_name = data.get("tool_name")
                arguments = data.get("arguments", {})
                
                if not tool_name:
                    return JSONResponse({
                        "error": "tool_name is required"
                    }, status_code=400)
                
                # Вызов инструмента через FastMCP
                try:
                    # Пытаемся найти и вызвать инструмент напрямую
                    result_data = None
                    
                    # Метод 1: Через _call_tool_mcp (основной метод FastMCP)
                    if hasattr(mcp, '_call_tool_mcp'):
                        result = await mcp._call_tool_mcp(tool_name, arguments)
                        # Преобразуем результат FastMCP в JSON
                        if hasattr(result, 'content'):
                            if isinstance(result.content, list) and len(result.content) > 0:
                                content_item = result.content[0]
                                if hasattr(content_item, 'text'):
                                    try:
                                        import json
                                        result_data = json.loads(content_item.text)
                                    except:
                                        result_data = content_item.text
                                else:
                                    result_data = str(content_item)
                            elif hasattr(result.content, 'text'):
                                try:
                                    import json
                                    result_data = json.loads(result.content.text)
                                except:
                                    result_data = result.content.text
                            else:
                                result_data = str(result.content)
                        else:
                            result_data = str(result)
                    
                    # Метод 2: Через _call_tool (альтернативный метод)
                    elif hasattr(mcp, '_call_tool'):
                        result = await mcp._call_tool(tool_name, arguments)
                        if isinstance(result, (dict, list, str, int, float, bool, type(None))):
                            result_data = result
                        else:
                            result_data = str(result)
                    
                    # Метод 3: Прямой вызов через _server (если доступно)
                    elif hasattr(mcp, '_server'):
                        server = getattr(mcp, '_server')
                        # Ищем инструмент в _server
                        if hasattr(server, '_tools'):
                            tools_dict = getattr(server, '_tools', {})
                            if tool_name in tools_dict:
                                tool_func = tools_dict[tool_name]
                                # Вызываем функцию напрямую
                                if asyncio.iscoroutinefunction(tool_func):
                                    result_data = await tool_func(**arguments)
                                else:
                                    result_data = tool_func(**arguments)
                            else:
                                return JSONResponse({
                                    "error": f"Tool '{tool_name}' not found"
                                }, status_code=404)
                        else:
                            return JSONResponse({
                                "error": "Tools dictionary not available"
                            }, status_code=500)
                    else:
                        return JSONResponse({
                            "error": "Tool calling method not available"
                        }, status_code=500)
                    
                    # Убеждаемся, что result_data не None
                    if result_data is None:
                        result_data = {"message": "Tool executed but returned None"}
                    
                    return JSONResponse({
                        "success": True,
                        "tool_name": tool_name,
                        "result": result_data
                    })
                except Exception as e:
                    import traceback
                    return JSONResponse({
                        "success": False,
                        "error": str(e),
                        "traceback": traceback.format_exc()
                    }, status_code=500)
                    
            except Exception as e:
                import traceback
                return JSONResponse({
                    "error": f"Request parsing error: {str(e)}",
                    "traceback": traceback.format_exc()
                }, status_code=400)
        
        # Проверяем, является ли base_app Starlette приложением
        if isinstance(base_app, Starlette):
            # Если это Starlette, добавляем routes
            base_app.routes.extend([
                Route("/health", health_check, methods=["GET"]),
                Route("/tools", list_tools_endpoint, methods=["GET"]),
                Route("/api/call-tool", call_tool_endpoint, methods=["POST"]),
                Route("/", root_endpoint, methods=["GET"]),
            ])
            return base_app
        else:
            # Если нет, создаем новое приложение с монтированием
            mcp_path = "/sse" if os.getenv("MCP_TRANSPORT", "sse").lower() == "sse" else "/"
            health_app = Starlette(routes=[
                Route("/health", health_check, methods=["GET"]),
                Route("/tools", list_tools_endpoint, methods=["GET"]),
                Route("/api/call-tool", call_tool_endpoint, methods=["POST"]),
                Route("/", root_endpoint, methods=["GET"]),
                Mount(mcp_path, app=base_app),
            ])
            return health_app
            
    except ImportError as e:
        logger.warning(f"Не удалось импортировать Starlette: {e}")
        logger.warning("Health endpoints недоступны, но MCP сервер будет работать")
        return base_app
    except Exception as e:
        logger.warning(f"Не удалось создать health endpoints: {e}")
        logger.warning("MCP сервер будет работать без дополнительных endpoints")
        logger.debug("Traceback:", exc_info=True)
        return base_app


if __name__ == "__main__":
    # Валидация конфигурации
    validate_configuration()
    
    # Режим работы: stdio (локально) или sse (удалённо через HTTP)
    mode = os.getenv("MCP_MODE", "sse").lower()
    
    if mode == "stdio":
        # Локальный режим через standard input/output (для тестирования)
        logger.info("Запуск MCP сервера в режиме stdio (локально)")
        try:
            check_tools_registration()
            mcp.run()
        except KeyboardInterrupt:
            logger.info("Получен сигнал остановки. Завершение работы...")
            sys.exit(0)
        except Exception as e:
            logger.critical(f"Критическая ошибка при запуске: {e}", exc_info=True)
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
        
        # Глобальная переменная для graceful shutdown
        shutdown_event = asyncio.Event()
        
        def signal_handler(signum, frame):
            """Обработчик сигналов для graceful shutdown."""
            logger.info(f"Получен сигнал {signum}. Инициирую graceful shutdown...")
            shutdown_event.set()
        
        # Регистрация обработчиков сигналов
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        try:
            if transport == "sse":
                logger.info("Запуск MCP сервера в режиме SSE")
                logger.info(f"Слушаю на {host}:{port}")
                logger.info(f"Endpoint: http://{host}:{port}/sse")
                # Используем старый метод sse_app() (работает, но показывает deprecation warning)
                # Подавляем предупреждение, так как новый API требует дополнительные параметры
                import warnings
                with warnings.catch_warnings():
                    warnings.filterwarnings("ignore", category=DeprecationWarning)
                    app = mcp.sse_app()
            else:
                logger.info("Запуск MCP сервера в режиме HTTP")
                logger.info(f"Слушаю на {host}:{port}")
                logger.info(f"Endpoint: http://{host}:{port}")
                # Получаем HTTP приложение из FastMCP (вызываем метод)
                app = mcp.http_app()
            
            # Добавляем health check endpoints
            app = create_health_endpoints(app)
            
            logger.info(f"Health check: http://{host}:{port}/health")
            logger.info(f"Tools list: http://{host}:{port}/tools")
            logger.info(f"Call tool API: http://{host}:{port}/api/call-tool")
            
        except Exception as e:
            logger.critical(f"Ошибка при создании приложения: {e}", exc_info=True)
            sys.exit(1)
        
        # Запуск через uvicorn с приложением FastMCP
        try:
            config = uvicorn.Config(
                app,
                host=host,
                port=port,
                log_level="info",
                access_log=True,
                timeout_keep_alive=30,
                timeout_graceful_shutdown=10
            )
            server = uvicorn.Server(config)
            
            # Запуск сервера
            server.run()
            
        except KeyboardInterrupt:
            logger.info("Получен сигнал остановки. Завершение работы...")
            sys.exit(0)
        except Exception as e:
            logger.critical(f"Критическая ошибка при запуске uvicorn: {e}", exc_info=True)
            sys.exit(1)
