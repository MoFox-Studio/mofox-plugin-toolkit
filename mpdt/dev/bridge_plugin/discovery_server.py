"""
开发模式发现服务器
固定端口 12318，用于 mpdt dev 获取主程序的动态端口
"""


import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

try:
    from src.common.logger import get_logger
    logger = get_logger("dev_discovery")
except ImportError:
    import logging
    logger = logging.getLogger("dev_discovery")

# 发现服务器固定端口
DISCOVERY_PORT = 12318

# 全局变量
_server_instance: uvicorn.Server | None = None


class ServerInfo(BaseModel):
    """主程序服务器信息"""
    host: str
    port: int


def create_discovery_app(main_host: str, main_port: int) -> FastAPI:
    """创建发现服务的 FastAPI 应用"""
    app = FastAPI(
        title="MoFox Dev Discovery",
        description="开发模式服务发现",
        version="1.0.0"
    )

    # 添加 CORS 中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/health")
    async def health_check():
        """健康检查"""
        return {
            "status": "ok",
            "service": "MoFox Dev Discovery"
        }

    @app.get("/api/server-info", response_model=ServerInfo)
    async def get_server_info():
        """获取主程序服务器信息
        
        Returns:
            主程序的 host 和 port
            
        Example:
            GET http://127.0.0.1:12318/api/server-info
            → {"host": "127.0.0.1", "port": 8000}
            
            WebSocket: ws://127.0.0.1:8000/plugin-api/dev_bridge/dev_bridge_router/ws
        """
        return ServerInfo(host=main_host, port=main_port)

    return app


async def start_discovery_server(
    main_host: str,
    main_port: int,
    discovery_host: str = "127.0.0.1"
) -> None:
    """启动发现服务器
    
    Args:
        main_host: 主程序的 host
        main_port: 主程序的 port
        discovery_host: 发现服务器绑定的 host
    """
    global _server_instance

    if _server_instance is not None:
        logger.warning("发现服务器已经在运行")
        return

    app = create_discovery_app(main_host, main_port)

    config = uvicorn.Config(
        app,
        host=discovery_host,
        port=DISCOVERY_PORT,
        log_level="error",  # 减少日志输出
        access_log=False
    )

    _server_instance = uvicorn.Server(config)

    logger.info(f"发现服务器启动在 http://{discovery_host}:{DISCOVERY_PORT}")
    logger.info(f"主程序地址: http://{main_host}:{main_port}")

    try:
        await _server_instance.serve()
    except Exception as e:
        logger.error(f"发现服务器运行出错: {e}")
        _server_instance = None


async def stop_discovery_server() -> None:
    """停止发现服务器"""
    global _server_instance

    if _server_instance is None:
        return

    logger.info("正在停止发现服务器...")
    _server_instance.should_exit = True
    _server_instance = None
