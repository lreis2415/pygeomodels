# Reference: https://github.com/jlowin/fastmcp?tab=readme-ov-file#-documentation

import logging
from typing import Optional

import uvicorn
from fastmcp import FastMCP
from mcp.types import ToolAnnotations
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from auth_context import set_bearer_token
from pygeomodels.config import parse_config

# logging.basicConfig(
#     filename="mcp_debug.log",
#     level=logging.DEBUG,
#     format="%(asctime)s [%(levelname)s] %(message)s",
# )

logger = logging.getLogger(__name__)

__version__ = "0.1.0"

# Global configuration
_cfg = None


def get_feature_flags():
    """Get feature flags from configuration."""
    global _cfg
    if _cfg is None:
        _cfg = parse_config()
    return _cfg


# 地形分析工具集开关
# 设置为 True 时启用地形分析工具，设置为 False 时禁用
def ENABLE_TERRAIN_ANALYSIS_TOOLS():
    cfg = get_feature_flags()
    return cfg.enable_terrain_analysis_tools


# EGC工具集开关
# 设置为 True 时启用EGC工具，设置为 False 时禁用
def ENABLE_MODEL_MANAGEMENT_TOOLS():
    cfg = get_feature_flags()
    return cfg.enable_model_management_tools


# AOI研究区工具集开关
# 设置为 True 时启用AOI工具，设置为 False 时禁用
def ENABLE_AOI_TOOLS():
    cfg = get_feature_flags()
    return cfg.enable_aoi_tools


def validate_api_key(api_key: Optional[str]) -> bool:
    """
    验证API Key是否有效

    Args:
        api_key: 从URL参数中获取的API key

    Returns:
        bool: API key是否有效

    Example:
        # 从环境变量获取有效key列表
        valid_keys = os.getenv("VALID_API_KEYS", "").split(",")
        return api_key in valid_keys
    """
    # TODO: 在此处实现具体的API key验证逻辑
    # 示例：可以从环境变量、配置文件或数据库验证
    if api_key is None:
        return False

    # 示例验证逻辑（请根据实际情况修改）
    # valid_keys = os.getenv("VALID_API_KEYS", "").split(",")
    # return api_key in valid_keys and api_key != ""

    # 临时：为了测试，返回True
    return True


class APIKeyMiddleware(BaseHTTPMiddleware):
    """
    API Key验证中间件
    从URL查询参数中获取key参数并进行验证
    """

    async def dispatch(self, request: Request, call_next):
        # 获取URL中的key参数
        api_key = request.query_params.get("key")

        # 验证API key
        if not validate_api_key(api_key):
            return JSONResponse(
                status_code=401,
                content={
                    "error": "Invalid or missing API key. Use ?key=<your-api-key>"
                },
            )

        # 验证通过，继续处理请求
        response = await call_next(request)
        return response


class BearerCaptureMiddleware(BaseHTTPMiddleware):
    """Capture Bearer token from Authorization header."""

    async def dispatch(self, request: Request, call_next):
        auth = request.headers.get("authorization", "")
        token = None
        if auth.lower().startswith("bearer "):
            token = auth[7:].strip()

        set_bearer_token(token)
        try:
            response = await call_next(request)
            return response
        finally:
            set_bearer_token(None)


# Create an MCP server instance
mcp = FastMCP("PyGeoModels")

# 根据开关条件导入地形分析工具集
if ENABLE_TERRAIN_ANALYSIS_TOOLS():
    from mcp_service.terrain_analysis_tools import register_terrain_tools

    register_terrain_tools(mcp)

# 根据开关条件导入EGC工具集
if ENABLE_MODEL_MANAGEMENT_TOOLS():
    from mcp_service.egc_service_tools import register_model_tools

    register_model_tools(mcp)

# 根据开关条件导入AOI研究区工具集
if ENABLE_AOI_TOOLS():
    from mcp_service.aoi_tools import register_aoi_tools

    register_aoi_tools(mcp)


@mcp.tool(
    annotations=ToolAnnotations(
        readOnlyHint=True, idempotentHint=True, openWorldHint=False
    )
)
def ready() -> str:
    """
    Confirm the service is ready.
    """
    return "ready"


if __name__ == "__main__":
    # mcp.run()  # Default: transport="STDIO"

    # mcp.run(transport="sse", host="127.0.0.1", port=5000) # Use SSE transport（官方弃用） "url": "http://localhost:5000/sse"

    app = mcp.http_app(
        path="/mcp",
        middleware=[
            Middleware(BearerCaptureMiddleware),
        ],
    )
    uvicorn.run(app, host="127.0.0.1", port=8050)
