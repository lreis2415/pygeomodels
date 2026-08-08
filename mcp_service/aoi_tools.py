# AOI（研究区）工具模块
# 包含查询研究区列表和关联数据的功能

from typing import Any

from mcp.types import ToolAnnotations
from pygeomodels.config import parse_config

from mcp_service.inner_api import call_inner_api, get_required_bearer_token
from mcp_service.schemas import StudyArea, StudyAreaData

# 全局变量，用于存储配置
cfg = None


def _normalize_study_area(raw: Any) -> StudyArea:
    if not isinstance(raw, dict):
        raise ValueError("Invalid study area item returned by the backend")

    aoi_id = raw.get("aoiId", raw.get("aoi_id", raw.get("id")))
    if not aoi_id:
        raise ValueError("Study area is missing aoiId")

    raw_data = raw.get("dataWithPathList", raw.get("data_with_path_list", []))
    data_items: list[StudyAreaData] = []
    if isinstance(raw_data, list):
        for item in raw_data:
            if isinstance(item, dict):
                known_keys = {
                    "name",
                    "dataName",
                    "path",
                    "dataPath",
                    "filePath",
                    "assetId",
                    "asset_id",
                    "dataType",
                    "data_type",
                }
                path = item.get("path", item.get("dataPath", item.get("filePath")))
                data_items.append(
                    StudyAreaData(
                        name=str(item.get("name", item.get("dataName", ""))),
                        path=str(path) if path else None,
                        asset_id=(
                            str(item.get("assetId", item.get("asset_id")))
                            if item.get("assetId", item.get("asset_id"))
                            else None
                        ),
                        data_type=(
                            str(item.get("dataType", item.get("data_type")))
                            if item.get("dataType", item.get("data_type"))
                            else None
                        ),
                        metadata={
                            str(key): value
                            for key, value in item.items()
                            if key not in known_keys
                        },
                    )
                )
            elif item is not None:
                data_items.append(StudyAreaData(path=str(item)))

    return StudyArea(
        aoi_id=str(aoi_id),
        study_area_name=str(
            raw.get("studyAreaName", raw.get("study_area_name", raw.get("name", "")))
        ),
        data_with_path_list=data_items,
    )


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

    @mcp.tool(
        annotations=ToolAnnotations(
            readOnlyHint=True, idempotentHint=True, openWorldHint=True
        )
    )
    def list_study_areas() -> list[StudyArea]:
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

        # Normalize backend-specific camelCase fields at the MCP boundary.
        data = resp.get("data", [])
        if not isinstance(data, list):
            raise RuntimeError("Invalid study area list returned by the backend")
        return [_normalize_study_area(item) for item in data]
