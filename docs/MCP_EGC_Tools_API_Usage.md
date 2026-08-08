# MCP EGC Tools API Usage Guide

## 🎯 工作流程

MCP EGC工具的正确使用流程是：

```
1. list_categories() → 获取所有可用类别
2. list_models_by_category(category) → 获取指定类别下的所有模型
3. describe_model(model_name) → 获取特定模型的详细元数据
4. run_model(request) → 运行选定的模型
5. get_task_status(project_id) → 查询任务执行状态
```

## 📋 工具详解

### 1. list_categories()
**作用**: 获取所有可用的模型类别（含本地化的名称和描述）

**参数**:
- `lang` (str, 可选): 返回内容的语言，`cn` 为中文，`en` 为英文，默认 `en`

**返回**: `List[CategorySummary]` - 类别列表，每个类别包含：
- `category_id`: 类别 ID，传给 `list_models_by_category` 使用
- `name`: 本地化类别名称
- `description`: 本地化类别描述

**示例**:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "list_categories",
    "arguments": {"lang": "en"}
  }
}
```

**响应示例**:
```json
{
  "result": [
    {
      "category_id": "basic",
      "name": "Basic",
      "description": "Basic models"
    },
    {
      "category_id": "interpolation",
      "name": "Interpolation",
      "description": "Interpolation models"
    }
  ]
}
```

> 提示：旧版本的 `list_categories` 返回纯字符串列表（类别 ID）。升级后请从
> `result[].category_id` 读取类别 ID，从 `result[].name` 读取显示名称。

---

### 2. list_models_by_category(category)
**作用**: 获取指定类别下的所有模型简要信息

**参数**:
- `category` (str, 必填): 模型类别名称
- `lang` (str, 可选): 返回内容的语言，`cn` 为中文，`en` 为英文，默认 `en`

**返回**: `List[ModelSummary]` - 模型列表，每个模型包含：
- `model_id`: 后端模型 ID
- `model_unique_abbr`: 可传给 `describe_model` 和 `run_model` 的模型缩写（可能为空）
- `display_name`: 显示名称
- `description`: 简要描述
- `category_name`: 所属类别（可能为空）

**示例**:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "list_models_by_category",
    "arguments": {
      "category": "basic",
      "lang": "en"
    }
  }
}
```

**响应示例**:
```json
{
  "result": [
    {
      "model_id": "model-001",
      "model_unique_abbr": "pitRemove",
      "display_name": "Pit removal",
      "description": "Remove sinks from DEM",
      "category_name": "basic"
    },
    {
      "model_id": "model-002",
      "model_unique_abbr": "slopeAnalysis",
      "display_name": "Slope analysis",
      "description": "Calculate slope from DEM",
      "category_name": "basic"
    }
  ]
}
```

---

### 3. describe_model(model_name)
**作用**: 获取特定模型的详细元数据和参数定义

**参数**:
- `model_name` (str, 必填): 模型唯一标识符
- `lang` (str, 可选): 返回内容的语言，`cn` 为中文，`en` 为英文，默认 `en`

**返回**: `Dict` - 模型详细信息，包括输入/输出参数定义

**示例**:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "describe_model",
    "arguments": {
      "model_name": "pitRemove",
      "lang": "cn"
    }
  }
}
```

---

### 4. run_model(request)
**作用**: 提交地理模型任务执行

**参数**:
- `request` (RunModelRequest, 必填): 任务请求体
  - `model_name` (str): 模型缩写，必填
  - `inputs` (Dict[str, JSON]): 输入参数，至少一个
  - `params` (Dict[str, JSON]): 模型参数，可选
  - `outputs` (Dict[str, JSON]): 输出参数，至少一个
  - `task_name` (str): 任务名称，可选

`inputs`、`params` 和 `outputs` 的键必须来自 `describe_model` 返回的
`parameter_info.parameters[].arg_name`。值保持 JSON 类型，以兼容不同 GIS 模型的参数类型；服务端会在提交前依据模型元数据校验参数名和必填项。

**返回**: `RunModelResult` - 包含项目 ID：

```json
{"project_id": "proj_12345"}
```

**示例**:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "run_model",
    "arguments": {
      "request": {
        "model_name": "pitRemove",
        "inputs": {
          "dem": "/path/to/input_dem.tif"
        },
        "params": {
          "algorithm": "horn"
        },
        "outputs": {
          "dem": "/path/to/output_dem.tif"
        },
        "task_name": "DEM填洼处理"
      }
    }
  }
}
```

---

## 🔧 使用示例：完整流程

```python
import requests

MCP_URL = "http://127.0.0.1:8050/mcp"
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": "Bearer YOUR_TOKEN"
}

def call_mcp(tool_name, arguments):
    """调用MCP工具的辅助函数"""
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments
        }
    }
    response = requests.post(MCP_URL, headers=HEADERS, json=payload)
    return response.json()

# Step 1: 获取所有类别
categories = call_mcp("list_categories", {})["result"]
print(f"可用类别: {categories}")

# Step 2: 查看特定类别下的模型
models = call_mcp("list_models_by_category", {"category": "basic"})["result"]
print(f"basic类别模型: {[m.get('model_unique_abbr') for m in models]}")

# Step 3: 获取模型详细信息
model_info = call_mcp("describe_model", {"model_name": "pitRemove"})["result"]
print(f"模型详情: {model_info}")

# Step 4: 运行模型
project_id = call_mcp("run_model", {
    "request": {
        "model_name": "pitRemove",
        "inputs": {"dem": "/data/dem.tif"},
        "params": {},
        "outputs": {"dem": "/data/dem_filled.tif"}
    }
})["result"]["project_id"]

print(f"任务ID: {project_id}")
```

---

## ⚠️ 重要说明

1. **参数必填性**: `list_models_by_category` 的 `category` 参数是必填的，必须先调用 `list_categories` 获取可用类别
2. **模型名称**: 使用 `model_name` (model_unique_abbr) 而不是其他标识符
3. **认证**: 所有调用都需要有效的 Bearer token
4. **错误处理**: 参数错误、模型不存在、上游失败和空结果是不同情况，应分别处理 MCP tool error 与正常结果
5. **语言参数**: `lang` 参数可选，支持 `cn`（中文）和 `en`（英文），默认 `en`。其他值会在 MCP schema 校验阶段拒绝
6. **缓存机制**: 系统按 token 和 lang 缓存结果。切换语言时自动刷新缓存，确保返回正确的本地化内容
7. **严格 schema**: `lang` 仅接受 `en` 或 `cn`；ID 不能为空；`run_model` 的 `inputs` 和 `outputs` 至少各包含一个键。工具 schema 可通过 MCP `tools/list` 获取。
8. **任务状态与日志**: `get_task_status` 返回 `{project_id, progress, state, message}`；`get_task_log` 返回 `{project_id, entries, next_cursor}`。

---

## 📝 API变更历史

### 2026-06-29
- **新增参数**: `list_categories`、`list_models_by_category`、`describe_model` 增加 `lang` 参数（默认 `en`）
- **缓存增强**: 缓存现在同时按 token 和 lang 存储，语言切换时自动刷新

### 2026-08-08
- **schema 收紧**: 新增 Pydantic MCP DTO，`run_model` 使用 `request` 外层对象，字段和返回值不再是无约束字典。
- **动态参数校验**: `describe_model` 元数据用于提交前校验模型参数名和必填项。
- **结构化任务结果**: 任务状态、日志和模型提交结果统一为结构化对象。
- **迁移提示**: 旧客户端需将 `request_body` 改为 `request`，并从 `result.project_id` 读取项目 ID。

### 2026-08-08 (v2 catalog)
- **结构化类别**: `list_categories` 从 `List[str]` 升级为 `List[CategorySummary]`，每项含
  `category_id` / `name` / `description`（v2 catalog 接口本地化字段）。
- **根节点前缀匹配**: v2 catalog 顶层节点 id 带环境后缀（如 `modelbank-dev`），
  按配置的根 id（`modelbank`）做前缀匹配定位。
- **迁移提示**: 旧客户端从 `result`（字符串数组）改为 `result[].category_id` / `result[].name`。

### 2025-06-28
- **重命名**: `list_models` → `list_models_by_category`
- **移除参数**: 删除了未使用的 `model_name` 参数
- **参数调整**: `category` 从可选改为必填
- **目的**: 明确API语义，改进工作流程的清晰度
