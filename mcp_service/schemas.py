"""Public request and response models for the PyGeoModels MCP tools.

The backend model metadata is intentionally dynamic, so model-specific values
remain JSON values.  The MCP-facing envelope and all stable fields are typed
here instead of leaking backend dictionaries into the tool contract.
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, JsonValue


Lang = Literal["en", "cn"]
NonEmptyId = Annotated[str, Field(min_length=1, max_length=256)]
DataReference = Annotated[
    str,
    Field(
        min_length=1,
        max_length=4096,
        description="A server-side data asset reference or an approved data URI.",
    ),
]


class MCPModel(BaseModel):
    """Base model used for public MCP DTOs."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        str_strip_whitespace=True,
    )


class ModelSummary(MCPModel):
    """Stable lightweight model metadata returned by model discovery."""

    model_id: NonEmptyId = Field(description="Backend model identifier.")
    display_name: str = Field(default="", description="Localized display name.")
    description: str = Field(default="", description="Localized short description.")
    model_unique_abbr: str | None = Field(
        default=None,
        description="Stable model abbreviation accepted by describe_model/run_model.",
    )
    category_name: str | None = Field(default=None, description="Model category.")


class ModelParameter(MCPModel):
    """Normalized model parameter metadata used for dynamic validation."""

    arg_name: NonEmptyId = Field(description="Parameter name used by run_model.")
    param_type: str = Field(
        default="param", description="input_data, param, or output_data."
    )
    name: str = Field(default="", description="Human-readable parameter name.")
    description: str = Field(default="", description="Parameter description.")
    data_type: str = Field(default="", description="Backend data type label.")
    required: bool = Field(
        default=False, description="Whether the parameter is required."
    )
    specification: dict[str, JsonValue] = Field(
        default_factory=dict,
        description="Model-specific constraints and default value.",
    )


class ParameterInfo(MCPModel):
    parameters: list[ModelParameter] = Field(default_factory=list)


class RunTemplate(MCPModel):
    model_name: NonEmptyId
    inputs: dict[str, JsonValue] = Field(default_factory=dict)
    params: dict[str, JsonValue] = Field(default_factory=dict)
    outputs: dict[str, JsonValue] = Field(default_factory=dict)
    task_name: str = ""


class ModelDescription(MCPModel):
    model_name: NonEmptyId
    description: str = ""
    run_template: RunTemplate
    parameter_info: ParameterInfo = Field(default_factory=ParameterInfo)


class RunModelRequest(MCPModel):
    """The stable outer envelope for a model submission.

    Values inside inputs/params/outputs are open JSON because each model has
    its own parameter set.  Those keys are validated against ModelParameter
    metadata immediately before submission.
    """

    model_name: NonEmptyId = Field(
        description="Model abbreviation returned by model discovery."
    )
    inputs: dict[str, JsonValue] = Field(
        min_length=1,
        description="Input parameter values keyed by model arg_name.",
    )
    params: dict[str, JsonValue] = Field(
        default_factory=dict,
        description="Optional model parameter values keyed by model arg_name.",
    )
    outputs: dict[str, JsonValue] = Field(
        min_length=1,
        description="Output parameter values keyed by model arg_name.",
    )
    task_name: str = Field(default="", max_length=256)


class RunModelResult(MCPModel):
    project_id: NonEmptyId = Field(description="Project/task identifier.")


class TaskStatusResult(MCPModel):
    project_id: NonEmptyId
    progress: float = Field(ge=0, le=100, description="Progress percentage.")
    state: str = Field(
        default="unknown", description="Backend task state when available."
    )
    message: str | None = None


class TaskLogEntry(MCPModel):
    timestamp: str | None = None
    level: str = "info"
    message: str = ""
    details: dict[str, JsonValue] = Field(default_factory=dict)


class TaskLogResult(MCPModel):
    project_id: NonEmptyId
    entries: list[TaskLogEntry] = Field(default_factory=list)
    next_cursor: str | None = None


class StudyAreaData(MCPModel):
    name: str = ""
    path: DataReference | None = None
    asset_id: str | None = None
    data_type: str | None = None
    metadata: dict[str, JsonValue] = Field(default_factory=dict)


class StudyArea(MCPModel):
    aoi_id: NonEmptyId = Field(alias="aoiId")
    study_area_name: str = Field(default="", alias="studyAreaName")
    data_with_path_list: list[StudyAreaData] = Field(
        default_factory=list, alias="dataWithPathList"
    )
