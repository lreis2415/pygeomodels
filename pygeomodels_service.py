# Reference: https://github.com/jlowin/fastmcp?tab=readme-ov-file#-documentation

from typing import Any, Dict, List, Optional

from fastmcp import FastMCP
import logging
import uvicorn
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware

from pygeomodels.modelBank import modelBank
from pygeomodels.config import parse_config
from pygeomodels.modelTask import modelTask

# logging.basicConfig(
#     filename="mcp_debug.log",
#     level=logging.DEBUG,
#     format="%(asctime)s [%(levelname)s] %(message)s",
# )

logger = logging.getLogger(__name__)

__version__ = "0.1.0"


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
                content={"error": "Invalid or missing API key. Use ?key=<your-api-key>"}
            )

        # 验证通过，继续处理请求
        response = await call_next(request)
        return response


# Create an MCP server instance
mcp = FastMCP("PyGeoModels")

# Load configuration and initialize ModelBank
cfg = None
mb = None

def initialize() -> None:
    """
    Initializes the model bank and configuration.
    """
    global cfg, mb
    if cfg is None:
        cfg = parse_config()
    if mb is None:
        mb = modelBank(cfg)
    # 确保models_caller也被初始化
    if mb.models_caller is None:
        mb.set_models_caller()

@mcp.tool()
def list_models() -> List[Dict[str, Any]]:
    """
    Returns a list of all GIS models with brief information (model_id, name, description).
    """
    initialize()
    return mb.list_all_models()

@mcp.tool()
def describe_model(model_id: str) -> Optional[Dict[str, Any]]:
    """
    Returns detailed parameter definitions(metadata) for a specific model using model_id instead of model_name.
    """
    return mb.describe_model(model_id)

@mcp.tool()
def run_model(request_body: Dict[str, Any]) -> Optional[str]:
    """
    提交地理模型任务
    Args:
        request_body: 任务请求体，包含以下字段：
            - model_name (str): 模型名称，必填
            - inputs (Dict): 输入参数，必填
            - params (Dict): 模型参数，可选
            - outputs (Dict): 输出配置，必填
            - task_name (str): 任务名称，可选
    
    Returns:
        str: 任务ID，project Id，用于后续状态查询
    
    Raises:
        ValueError: 参数验证失败
        AttributeError: 模型不存在
    
    Example:
        request_body = {
            "model_name": "pitRemove",
            "inputs": {"dem": "/path/to/dem.tif"},
            "params": {"algorithm": "horn"},
            "outputs": {"dem": "/path/to/dem_filled.tif"},
            "task_name": "填洼任务"
        }
    """
    # logger.debug(f"raw request_body: {request_body}")
    model_name = request_body.get("model_name")
    if model_name is None:
        raise ValueError("model_name must be provided in the request body.")
    
    # Initialize model caller if not already initialized
    if mb.models_caller is None:
        mb.set_models_caller()
    
    # Dynamically get the model function from ModelCaller
    model_function = getattr(mb.models_caller, model_name, None)
    if model_function is None:
        raise AttributeError(f"No such model: {model_name}")

    project_id = model_function(request_body)
    return project_id

@mcp.tool()
def get_task_status(project_id: str) -> int:
    """
    Queries task progress for a given project_id.
    """
    task = modelTask(cfg, project_id)
    return task.progress()

@mcp.tool()
def get_task_log(project_id: str) -> list[Dict[str, Any]]:
    """
    Queries task logs for a given project_id.
    """
    task = modelTask(cfg, project_id)
    return task.log()

@mcp.tool()
def ready() -> str:
    """
    Confirm the service is ready.
    """
    return "ready"


@mcp.tool()
## 通过研究区经纬度来获取需要的DEM数据
def get_dem_by_bbox(min_lon: float, max_lon: float, max_lat: float, min_lat: float) -> str:
    """
    通过研究区经纬度范围获取对应的DEM数据路径

    :param min_lon: 最小经度
    :param max_lon: 最大经度
    :param max_lat: 最大纬度
    :param min_lat: 最小纬度
    :return: DEM数据文件路径
    """
    # 1. 选择DEM数据 
    # 目前梅西数据和范围是对不上的
    vert = (max_lat + min_lat) / 2
    hori = (min_lon + max_lon) / 2
    if (vert < 34. and vert >28.) and (hori > 116. and hori < 122.):
        DEMfile = "/onesis/kt4/dsm_case/xuancheng/dem_xc_900913.tif"
    elif vert < 50. and vert > 48. and hori > 124. and hori < 126.5:
        DEMfile = "/onesis/kt4/dsm_case/heshan/dem_heshan_900913.tif"
    elif vert < 26. and vert > 25. and hori > 116. and hori < 117:
        DEMfile = "/onesis/kt4/dsm_case/dem_meixi.tif"
    else:
        return "invalid study area"
    return DEMfile
    # 2. TODO 读取并裁剪DEM数据


@mcp.tool()
# 计算研究区面积(Area)
def calculate_area(dem_path: str) -> float:
    """
    计算给定DEM文件的研究区面积

    :param dem_path: DEM数据文件路径
    :return: 研究区面积
    """

    # 计算研究区面积，这里仅仅是模拟数据
    area = 100.0

    return float(area)

@mcp.tool()
# 计算高程差 (Elevation Difference)
def calculate_elevation_difference(dem_path: str) -> float:
    """
    计算给定DEM文件的高程差

    :param dem_path: DEM数据文件路径
    :return: 高程差
    """

    # 计算高程差，这里仅仅是模拟数据
    elevation_difference = 50.0

    return float(elevation_difference)

@mcp.tool()
# 计算标准差 (SDH - Standard Deviation of Height)
def calculate_sdh(dem_path: str) -> float:
    """
    计算给定DEM文件的高程值标准差，反映地形起伏程度

    :param dem_path: DEM数据文件路径
    :return: 高程值标准差
    """

    # 计算高程值的标准差，这里仅仅是模拟数据
    sdh = 5.0

    return float(sdh)

@mcp.tool()
# 计算平均坡度值(Mean Slope)
def calculate_mean_slope(dem_path: str) -> float:
    """
    计算给定坡度文件的平均值

    :param dem_path: 坡度数据文件路径
    :return: 平均坡度值
    """

    # 计算坡度的平均值，这里仅仅是模拟数据
    slope_average = 20.0

    return float(slope_average)

# 计算空间分辨率 (Resolution)
@mcp.tool()
def calculate_resolution(dem_path: str) -> float:
    """
    计算给定DEM文件的空间分辨率

    :param dem_path: DEM数据文件路径
    :return: 空间分辨率
    """

    # 计算空间分辨率，这里仅仅是模拟数据
    resolution = 30.0

    return float(resolution)

if __name__ == "__main__":
    # mcp.run()  # Default: transport="STDIO"

    # mcp.run(transport="sse", host="127.0.0.1", port=5000) # Use SSE transport（官方弃用） "url": "http://localhost:5000/sse"

    mcp.run(transport="http", host="127.0.0.1", port=8050, path="/mcp") # Use Streamable HTTP transport "url": "http://localhost:5000/mcp"

    # 使用自定义中间件启动服务，支持 ?key=<api-key> 参数验证
    # app = mcp.http_app(middleware=[Middleware(APIKeyMiddleware)])
    # uvicorn.run(app, host="127.0.0.1", port=8050, path="/mcp")