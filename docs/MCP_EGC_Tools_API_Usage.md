# MCP EGC Tools API Usage Guide

## 🎯 工作流程

MCP EGC工具的正确使用流程是：

```
1. list_categories() → 获取所有可用类别
2. list_models_by_category(category) → 获取指定类别下的所有模型
3. describe_model(model_name) → 获取特定模型的详细元数据
4. run_model(request_body) → 运行选定的模型
5. get_task_status(project_id) → 查询任务执行状态
```

## 📋 工具详解

### 1. list_categories()
**作用**: 获取所有可用的模型类别

**参数**:
- `lang` (str, 可选): 返回内容的语言，`cn` 为中文，`en` 为英文，默认 `en`

**返回**: `List[str]` - 类别名称列表

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
  "result": ["basic", "interpolation", "topographic_attribute", "hydrology_analysis"]
}
```

---

### 2. list_models_by_category(category)
**作用**: 获取指定类别下的所有模型简要信息

**参数**:
- `category` (str, 必填): 模型类别名称
- `lang` (str, 可选): 返回内容的语言，`cn` 为中文，`en` 为英文，默认 `en`

**返回**: `List[Dict]` - 模型列表，每个模型包含：
- `model_name`: 模型唯一标识符
- `model_description`: 模型描述

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
      "model_name": "pitRemove",
      "model_description": "Remove sinks from DEM"
    },
    {
      "model_name": "slopeAnalysis",
      "model_description": "Calculate slope from DEM"
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

### 4. run_model(request_body)
**作用**: 提交地理模型任务执行

**参数**:
- `request_body` (Dict, 必填): 任务请求体
  - `model_name` (str): 模型名称，必填
  - `inputs` (Dict): 输入数据路径，必填
  - `params` (Dict): 模型参数，可选
  - `outputs` (Dict): 输出数据路径，必填
  - `task_name` (str): 任务名称，可选

**返回**: `str` - 项目ID (project_id)，用于后续状态查询

**示例**:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "run_model",
    "arguments": {
      "request_body": {
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
print(f"basic类别模型: {[m['model_name'] for m in models]}")

# Step 3: 获取模型详细信息
model_info = call_mcp("describe_model", {"model_name": "pitRemove"})["result"]
print(f"模型详情: {model_info}")

# Step 4: 运行模型
project_id = call_mcp("run_model", {
    "request_body": {
        "model_name": "pitRemove",
        "inputs": {"dem": "/data/dem.tif"},
        "params": {},
        "outputs": {"dem": "/data/dem_filled.tif"}
    }
})["result"]

print(f"任务ID: {project_id}")
```

---

## ⚠️ 重要说明

1. **参数必填性**: `list_models_by_category` 的 `category` 参数是必填的，必须先调用 `list_categories` 获取可用类别
2. **模型名称**: 使用 `model_name` (model_unique_abbr) 而不是其他标识符
3. **认证**: 所有调用都需要有效的 Bearer token
4. **错误处理**: 检查响应中的错误信息并适当处理
5. **语言参数**: `lang` 参数可选，支持 `cn`（中文）和 `en`（英文），默认 `en`。无效值回退到 `en`
6. **缓存机制**: 系统按 token 和 lang 缓存结果。切换语言时自动刷新缓存，确保返回正确的本地化内容

---

## 📝 API变更历史

### 2026-06-29
- **新增参数**: `list_categories`、`list_models_by_category`、`describe_model` 增加 `lang` 参数（默认 `en`）
- **缓存增强**: 缓存现在同时按 token 和 lang 存储，语言切换时自动刷新

### 2025-06-28
- **重命名**: `list_models` → `list_models_by_category`
- **移除参数**: 删除了未使用的 `model_name` 参数
- **参数调整**: `category` 从可选改为必填
- **目的**: 明确API语义，改进工作流程的清晰度