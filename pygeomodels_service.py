from typing import Optional, List
from pygeomodels.modelBank import modelBank
from pygeomodels.config import parse_config
from pygeomodels.modelTask import modelTask
from typing import Any, Dict, List, Optional
from fastmcp import FastMCP

__version__ = "0.1.0"

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
    Returns detailed parameter definitions(metadata) for a specific model.
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
        str: 任务ID，用于后续状态查询
    
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

@mcp.tool("tasks/{project_id}/status")
def get_task_status(project_id: str) -> int:
    """
    Queries task progress for a given project_id.
    """
    task = modelTask(cfg, project_id)
    return task.progress()

@mcp.tool("tasks/{project_id}/log")
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

if __name__ == "__main__":
    mcp.run() 