# AOI（研究区）工具模块
# 包含查询研究区列表和关联数据的功能

from typing import Any, Dict, List

from mcp_service.inner_api import call_inner_api, get_required_bearer_token
from pygeomodels.config import parse_config

# 全局变量，用于存储配置
cfg = None


def register_aoi_tools(mcp):
    """
    注册AOI研究区相关的工具函数到MCP服务器

    Args:
        mcp: FastMCP实例
    """

    def initialize() -> None:
        """初始化配置。"""
        global cfg
        if cfg is None:
            cfg = parse_config()

    @mcp.tool()
    def list_study_areas() -> List[Dict[str, Any]]:
        """
        查询所有研究区列表及其关联数据路径。

        Returns:
            研究区列表，每个研究区包含 aoiId, studyAreaName, dataWithPathList 等字段。
        """
        initialize()
        access_token = get_required_bearer_token()

        if not cfg.aoi_list_data_path:
            raise ValueError(
                "aoi_list_data_path is not configured in [SERVICE] section."
            )

        resp = call_inner_api(
            method="get",
            host=cfg.modelmanager_url,
            path=cfg.aoi_list_data_path,
            access_token=access_token,
        )

        # 返回 data 列表
        data = resp.get("data", [])
        return data if isinstance(data, list) else []
