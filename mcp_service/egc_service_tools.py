# EGC服务模块
# 包含GIS模型的查询、运行和状态管理功能

from typing import Any, Dict, List, Optional

from pygeomodels.modelBank import modelBank
from pygeomodels.config import parse_config
from pygeomodels.modelTask import modelTask
from mcp_service.inner_api import get_required_bearer_token
from auth_context import get_bearer_token

# 全局变量，用于存储配置和模型库
cfg = None
mb = None


def register_model_tools(mcp):
    """
    注册EGC服务相关的工具函数到MCP服务器

    Args:
        mcp: FastMCP实例
    """

    def initialize() -> None:
        """
        Initializes the model bank and configuration.
        """
        global cfg, mb
        if cfg is None:
            cfg = parse_config()
        if mb is None:
            mb = modelBank(cfg)

    @mcp.tool()
    def list_categories() -> List[str]:
        """
        Returns all available model categories.
        """
        initialize()
        access_token = get_required_bearer_token()
        return mb.get_categories(access_token)

    @mcp.tool()
    def list_models_by_category(category: str) -> List[Dict[str, Any]]:
        """
        Returns a list of GIS models in a specific category with brief information.

        Args:
            category: The category name to query. Use 'list_categories' to discover available values.

        Returns:
            List of models with their names and descriptions in the specified category.
        """
        initialize()
        access_token = get_required_bearer_token()
        return mb.list_all_models(access_token, category=category)

    @mcp.tool()
    def describe_model(model_name: str) -> Optional[Dict[str, Any]]:
        """
        Returns model description and parameter info using model_name (model_unique_abbr).
        """
        initialize()
        access_token = get_required_bearer_token()
        return mb.describe_model(model_name, access_token)

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
        initialize()
        access_token = get_required_bearer_token()

        model_name = request_body.get("model_name")
        if model_name is None:
            raise ValueError("model_name must be provided in the request body.")

        request_body = dict(request_body)
        request_body["access_token"] = access_token

        # Initialize/Get model caller with current token
        model_caller = mb.get_models_caller(access_token)

        # Dynamically get the model function from ModelCaller
        model_function = getattr(model_caller, model_name, None)
        if model_function is None:
            raise AttributeError(f"No such model: {model_name}")

        project_id = model_function(request_body)
        return project_id

    @mcp.tool()
    def get_task_status(project_id: str) -> int:
        """
        Queries task progress for a given project_id.
        """
        initialize()
        access_token = get_required_bearer_token()
        task = modelTask(cfg, project_id, access_token)
        return task.progress()

    @mcp.tool()
    def get_task_log(project_id: str) -> list[Dict[str, Any]]:
        """
        Queries task logs for a given project_id.
        """
        initialize()
        access_token = get_required_bearer_token()
        task = modelTask(cfg, project_id, access_token)
        return task.log()

    @mcp.tool()
    def debug_token_tool() -> Dict[str, Any]:
        """Temporary debug tool for token propagation check."""
        token = get_bearer_token()
        return {
            "has_token": bool(token),
            "prefix": token[:8] if token else None,
        }
