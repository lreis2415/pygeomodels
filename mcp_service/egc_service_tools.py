# EGC服务模块
# 包含GIS模型的查询、运行和状态管理功能

from typing import Any

from mcp.types import ToolAnnotations
from pygeomodels.config import parse_config
from pygeomodels.modelBank import modelBank
from pygeomodels.modelTask import modelTask

from mcp_service.inner_api import get_required_bearer_token
from mcp_service.schemas import (
    CategorySummary,
    Lang,
    ModelDescription,
    ModelParameter,
    ModelSummary,
    NonEmptyId,
    RunModelRequest,
    RunModelResult,
    TaskLogEntry,
    TaskLogResult,
    TaskStatusResult,
)

# 全局变量，用于存储配置和模型库
cfg = None
mb = None


def _normalize_parameter(raw: dict[str, Any]) -> ModelParameter | None:
    """Convert backend parameter metadata to the public MCP shape."""
    arg_name = raw.get("arg_name") or raw.get("name")
    if not arg_name:
        return None
    specification = raw.get("specification")
    if not isinstance(specification, dict):
        specification = {}
    return ModelParameter(
        arg_name=str(arg_name),
        param_type=str(raw.get("param_type") or "param"),
        name=str(raw.get("name") or ""),
        description=str(raw.get("description") or ""),
        data_type=str(raw.get("data_type") or ""),
        required=bool(raw.get("required", raw.get("is_required", False))),
        specification=specification,
    )


def _normalize_model_description(
    model_name: str, raw: dict[str, Any]
) -> ModelDescription:
    """Normalize a modelBank description without exposing backend dictionaries."""
    parameter_info = raw.get("parameter_info") or {}
    if not isinstance(parameter_info, dict):
        parameter_info = {}
    raw_parameters = parameter_info.get("parameters", [])
    parameters = []
    if isinstance(raw_parameters, list):
        for item in raw_parameters:
            if isinstance(item, dict):
                normalized = _normalize_parameter(item)
                if normalized is not None:
                    parameters.append(normalized)

    template = raw.get("run_template") or {}
    if not isinstance(template, dict):
        template = {}
    return ModelDescription(
        model_name=model_name,
        description=str(raw.get("description") or ""),
        run_template={
            "model_name": model_name,
            "inputs": template.get("inputs") or {},
            "params": template.get("params") or {},
            "outputs": template.get("outputs") or {},
            "task_name": template.get("task_name") or "",
        },
        parameter_info={"parameters": parameters},
    )


def _validate_dynamic_parameters(
    request: RunModelRequest, description: ModelDescription
) -> None:
    """Validate the model-specific keys after metadata discovery."""
    known: dict[str, ModelParameter] = {
        parameter.arg_name: parameter
        for parameter in description.parameter_info.parameters
    }
    provided_by_bucket = {
        "inputs": request.inputs,
        "params": request.params,
        "outputs": request.outputs,
    }
    provided = {
        key
        for values in provided_by_bucket.values()
        for key in values
    }
    missing = []
    misplaced = []
    for parameter in known.values():
        parameter_type = parameter.param_type.strip().lower()
        expected_bucket = {
            "input_data": "inputs",
            "output_data": "outputs",
        }.get(parameter_type, "params")
        expected_values = provided_by_bucket[expected_bucket]
        if parameter.arg_name not in expected_values:
            if parameter.arg_name in provided:
                misplaced.append(f"{parameter.arg_name} (expected {expected_bucket})")
            elif parameter.required:
                missing.append(parameter.arg_name)
    if missing:
        raise ValueError(
            "Missing required model parameters: " + ", ".join(sorted(missing))
        )
    if misplaced:
        raise ValueError(
            "Model parameters are in the wrong section: " + ", ".join(sorted(misplaced))
        )

    unknown = sorted(provided - set(known)) if known else []
    if unknown:
        raise ValueError(
            "Unknown model parameters for "
            f"{request.model_name}: {', '.join(unknown)}"
        )


def _normalize_task_status(project_id: str, raw: Any) -> TaskStatusResult:
    if raw is None:
        raise RuntimeError(f"Task status unavailable for project_id={project_id}")
    if isinstance(raw, dict):
        progress = raw.get("progress", raw.get("percentage", raw.get("value")))
        state = str(raw.get("state", raw.get("status", "unknown")))
        message = raw.get("message")
    else:
        progress = raw
        state = "unknown"
        message = None
    try:
        progress_value = float(progress)
    except (TypeError, ValueError) as exc:
        raise RuntimeError(
            f"Invalid task progress returned for project_id={project_id}"
        ) from exc
    return TaskStatusResult(
        project_id=project_id,
        progress=progress_value,
        state=state,
        message=str(message) if message is not None else None,
    )


def _normalize_task_log(project_id: str, raw: Any) -> TaskLogResult:
    if raw is None:
        raise RuntimeError(f"Task log unavailable for project_id={project_id}")
    if isinstance(raw, dict):
        raw_entries = raw.get("entries", raw.get("logs", []))
        next_cursor = raw.get("next_cursor")
    else:
        raw_entries = raw
        next_cursor = None
    if not isinstance(raw_entries, list):
        raise RuntimeError(f"Invalid task log returned for project_id={project_id}")

    entries: list[TaskLogEntry] = []
    for item in raw_entries:
        if isinstance(item, dict):
            known_keys = {"timestamp", "time", "level", "severity", "message", "msg"}
            details = {str(key): value for key, value in item.items() if key not in known_keys}
            entries.append(
                TaskLogEntry(
                    timestamp=str(item.get("timestamp", item.get("time")))
                    if item.get("timestamp", item.get("time")) is not None
                    else None,
                    level=str(item.get("level", item.get("severity", "info"))),
                    message=str(item.get("message", item.get("msg", ""))),
                    details=details,
                )
            )
        else:
            entries.append(TaskLogEntry(message=str(item)))
    return TaskLogResult(
        project_id=project_id,
        entries=entries,
        next_cursor=str(next_cursor) if next_cursor is not None else None,
    )


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

    @mcp.tool(
        annotations=ToolAnnotations(
            readOnlyHint=True, idempotentHint=True, openWorldHint=True
        )
    )
    def list_categories(lang: Lang = "en") -> list[CategorySummary]:
        """
        Returns all available model categories with localized names and descriptions.

        Args:
            lang: Response language, 'cn' for Chinese or 'en' for English. Defaults to 'en'.

        Returns:
            List of categories; each item contains category_id, name and description.
            Pass category_id to 'list_models_by_category'.
        """
        initialize()
        access_token = get_required_bearer_token()
        return [
            CategorySummary.model_validate(item)
            for item in mb.get_categories_info(access_token, lang)
        ]

    @mcp.tool(
        annotations=ToolAnnotations(
            readOnlyHint=True, idempotentHint=True, openWorldHint=True
        )
    )
    def list_models_by_category(
        category: NonEmptyId, lang: Lang = "en"
    ) -> list[ModelSummary]:
        """
        Returns a list of GIS models in a specific category with brief information.

        Args:
            category: The category name to query. Use 'list_categories' to discover available values.
            lang: Response language, 'cn' for Chinese or 'en' for English. Defaults to 'en'.

        Returns:
            List of models with their names and descriptions in the specified category.
        """
        initialize()
        access_token = get_required_bearer_token()
        models = mb.list_all_models_lightweight(
            access_token, category=category, lang=lang
        )
        return [ModelSummary.model_validate(model) for model in models]

    @mcp.tool(
        annotations=ToolAnnotations(
            readOnlyHint=True, idempotentHint=True, openWorldHint=True
        )
    )
    def describe_model(model_name: NonEmptyId, lang: Lang = "en") -> ModelDescription:
        """
        Returns model description and parameter info using model_name (model_unique_abbr).

        Args:
            model_name: The unique model abbreviation to describe.
            lang: Response language, 'cn' for Chinese or 'en' for English. Defaults to 'en'.
        """
        initialize()
        access_token = get_required_bearer_token()
        description = mb.describe_model(model_name, access_token, lang)
        if description is None:
            raise ValueError(f"No model found for model_name={model_name}")
        return _normalize_model_description(model_name, description)

    @mcp.tool(
        annotations=ToolAnnotations(
            readOnlyHint=False, destructiveHint=False, idempotentHint=False, openWorldHint=True
        )
    )
    def run_model(request: RunModelRequest) -> RunModelResult:
        """
        提交地理模型任务
        Args:
            request: Typed task request. Model-specific keys are validated
                against describe_model metadata before submission.

        Returns:
            RunModelResult: 项目 ID，用于后续状态查询

        Raises:
            ValueError: 参数验证失败
            AttributeError: 模型不存在

        Example:
            request = {
                "model_name": "pitRemove",
                "inputs": {"dem": "/path/to/dem.tif"},
                "params": {"algorithm": "horn"},
                "outputs": {"dem": "/path/to/dem_filled.tif"},
                "task_name": "填洼任务"
            }
        """
        initialize()
        access_token = get_required_bearer_token()

        description = mb.describe_model(request.model_name, access_token, "en")
        if description is None:
            raise ValueError(f"No model found for model_name={request.model_name}")
        normalized_description = _normalize_model_description(
            request.model_name, description
        )
        _validate_dynamic_parameters(request, normalized_description)

        request_body = request.model_dump()
        request_body["access_token"] = access_token

        # Initialize/Get model caller with current token
        model_caller = mb.get_models_caller(access_token)

        # Dynamically get the model function from ModelCaller
        model_function = getattr(model_caller, request.model_name, None)
        if model_function is None:
            raise AttributeError(f"No such model: {request.model_name}")

        project_id = model_function(request_body)
        if not project_id:
            raise RuntimeError("Model submission did not return a project_id")
        return RunModelResult(project_id=str(project_id))

    @mcp.tool(
        annotations=ToolAnnotations(
            readOnlyHint=True, idempotentHint=True, openWorldHint=True
        )
    )
    def get_task_status(project_id: NonEmptyId) -> TaskStatusResult:
        """
        Queries task progress for a given project_id.
        """
        initialize()
        access_token = get_required_bearer_token()
        task = modelTask(cfg, project_id, access_token)
        return _normalize_task_status(project_id, task.progress())

    @mcp.tool(
        annotations=ToolAnnotations(
            readOnlyHint=True, idempotentHint=True, openWorldHint=True
        )
    )
    def get_task_log(project_id: NonEmptyId) -> TaskLogResult:
        """
        Queries task logs for a given project_id.
        """
        initialize()
        access_token = get_required_bearer_token()
        task = modelTask(cfg, project_id, access_token)
        return _normalize_task_log(project_id, task.log())
