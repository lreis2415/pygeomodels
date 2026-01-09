## ModelCaller 类工作原理详解

### 1. 类的基本结构

`ModelCaller` 是一个动态生成模型调用函数的工厂类，它根据配置和元数据为每个模型创建对应的调用函数。

### 2. 实际数据示例

假设我们有以下配置和元数据：

**配置数据 (ModelEngineConfig):**
```python
# 从 default_config.ini 解析的配置
cfg = ModelEngineConfig(config_parser)
# 关键配置项：
cfg.modelmanager_url = "http://localhost:7504"
cfg.api_basename = "mbms/v1"
cfg.api_cls_usrprj = "user-projects"
cfg.api_uprj_single = "single-models"
cfg.api_sprj_run = "run"
cfg.token = "default_token"
```

**模型元数据 (metadata):**
```python
metadata = {
    "model_001": {
        "model_unique_abbr": "flood_simulation",
        "model_name": "洪水模拟模型",
        "version": "1.0"
    },
    "model_002": {
        "model_unique_abbr": "terrain_analysis", 
        "model_name": "地形分析模型",
        "version": "2.1"
    }
}
```

### 3. 工作流程示例

#### 步骤1: 初始化 ModelCaller
```python
caller = ModelCaller(cfg, metadata)
```

#### 步骤2: 动态生成模型函数
`_generate_model_functions()` 方法会为每个模型创建调用函数：

```python
# 为 flood_simulation 模型生成的函数
def flood_simulation(request_body: Dict[str, Any]) -> Optional[str]:
    _inputs = request_body.get('inputs', {})
    _params = request_body.get('params', {})
    _outputs = request_body.get('outputs', {})
    _taskname = request_body.get('task_name', '')
    _model_id = request_body.get('model_id', 'model_001')
    
    # 构建API路径
    method = "mbms/v1/user-projects/single-models/model_001/run"
    
    # 生成任务名
    if _taskname == '':
        _taskname = 'mcp-flood_simulation-123456789'
    
    # 构建请求体
    post_body = {
        "params": [],
        "task_name": _taskname
    }
    
    # 添加输入参数
    for ik, iv in _inputs.items():
        post_body['params'].append({'param_name': ik, 'param_value': iv})
    
    # 添加模型参数
    for pk, pv in _params.items():
        post_body['params'].append({'param_name': pk, 'param_value': pv})
    
    # 添加输出参数
    for ok, ov in _outputs.items():
        post_body['params'].append({'param_name': ok, 'param_value': ov})
    
    # 调用API
    res = restapi_post("http://localhost:7504", method, post_body, "default_token")
    
    if res and (res['success'] == 'true' or res['success']):
        return res['data']['project_id']
    return None
```

#### 步骤3: 使用生成的函数

```python
# 调用洪水模拟模型
request_data = {
    "inputs": {
        "rainfall_data": "rainfall_2024.csv",
        "terrain_data": "dem.tif"
    },
    "params": {
        "simulation_time": 24,
        "resolution": 10
    },
    "outputs": {
        "flood_map": "flood_result.tif",
        "report": "flood_report.pdf"
    },
    "task_name": "flood_analysis_2024"
}

# 通过属性访问调用模型
project_id = caller.flood_simulation(request_data)
print(f"项目ID: {project_id}")  # 输出: 项目ID: proj_12345

# 或者通过字典访问
project_id = caller.model_functions['flood_simulation'](request_data)
```

### 4. API调用示例

实际发送的HTTP请求：

```http
POST http://localhost:7504/mbms/v1/user-projects/single-models/model_001/run
Authorization: Bearer default_token
Content-Type: application/json

{
    "params": [
        {"param_name": "rainfall_data", "param_value": "rainfall_2024.csv"},
        {"param_name": "terrain_data", "param_value": "dem.tif"},
        {"param_name": "simulation_time", "param_value": 24},
        {"param_name": "resolution", "param_value": 10},
        {"param_name": "flood_map", "param_value": "flood_result.tif"},
        {"param_name": "report", "param_value": "flood_report.pdf"}
    ],
    "task_name": "flood_analysis_2024"
}
```

### 5. 关键特性

1. **动态函数生成**: 根据元数据自动为每个模型创建调用函数
2. **统一接口**: 所有模型都使用相同的调用格式
3. **参数标准化**: 将输入、参数、输出统一转换为API格式
4. **任务管理**: 自动生成唯一任务名，支持任务跟踪
5. **错误处理**: 处理API调用失败的情况

### 6. 设计模式

这个类使用了以下设计模式：
- **工厂模式**: 动态创建模型调用函数
- **代理模式**: 通过 `__getattr__` 提供属性式访问
- **策略模式**: 不同模型使用相同的调用策略

这种设计使得用户可以像调用普通函数一样调用不同的地理模型，大大简化了模型调用的复杂性。

```python
# 从 default_config.ini 解析的配置
cfg = ModelEngineConfig(config_parser)
# 关键配置项：
cfg.modelmanager_url = "http://localhost:7504"
cfg.api_basename = "mbms/v1"
cfg.api_cls_usrprj = "user-projects"
cfg.api_uprj_single = "single-models"
cfg.api_sprj_run = "run"
cfg.token = "default_token"
```

```python
metadata = {
    "model_001": {
        "model_unique_abbr": "flood_simulation",
        "model_name": "洪水模拟模型",
        "version": "1.0"
    },
    "model_002": {
        "model_unique_abbr": "terrain_analysis", 
        "model_name": "地形分析模型",
        "version": "2.1"
    }
}
```

```python
caller = ModelCaller(cfg, metadata)
```

```python
# 为 flood_simulation 模型生成的函数
def flood_simulation(request_body: Dict[str, Any]) -> Optional[str]:
    _inputs = request_body.get('inputs', {})
    _params = request_body.get('params', {})
    _outputs = request_body.get('outputs', {})
    _taskname = request_body.get('task_name', '')
    _model_id = request_body.get('model_id', 'model_001')
    
    # 构建API路径
    method = "mbms/v1/user-projects/single-models/model_001/run"
    
    # 生成任务名
    if _taskname == '':
        _taskname = 'mcp-flood_simulation-123456789'
    
    # 构建请求体
    post_body = {
        "params": [],
        "task_name": _taskname
    }
    
    # 添加输入参数
    for ik, iv in _inputs.items():
        post_body['params'].append({'param_name': ik, 'param_value': iv})
    
    # 添加模型参数
    for pk, pv in _params.items():
        post_body['params'].append({'param_name': pk, 'param_value': pv})
    
    # 添加输出参数
    for ok, ov in _outputs.items():
        post_body['params'].append({'param_name': ok, 'param_value': ov})
    
    # 调用API
    res = restapi_post("http://localhost:7504", method, post_body, "default_token")
    
    if res and (res['success'] == 'true' or res['success']):
        return res['data']['project_id']
    return None
```

```python
# 调用洪水模拟模型
request_data = {
    "inputs": {
        "rainfall_data": "rainfall_2024.csv",
        "terrain_data": "dem.tif"
    },
    "params": {
        "simulation_time": 24,
        "resolution": 10
    },
    "outputs": {
        "flood_map": "flood_result.tif",
        "report": "flood_report.pdf"
    },
    "task_name": "flood_analysis_2024"
}

# 通过属性访问调用模型
project_id = caller.flood_simulation(request_data)
print(f"项目ID: {project_id}")  # 输出: 项目ID: proj_12345

# 或者通过字典访问
project_id = caller.model_functions['flood_simulation'](request_data)
```

```plaintext
POST http://localhost:7504/mbms/v1/user-projects/single-models/model_001/run
Authorization: Bearer default_token
Content-Type: application/json

{
    "params": [
        {"param_name": "rainfall_data", "param_value": "rainfall_2024.csv"},
        {"param_name": "terrain_data", "param_value": "dem.tif"},
        {"param_name": "simulation_time", "param_value": 24},
        {"param_name": "resolution", "param_value": 10},
        {"param_name": "flood_map", "param_value": "flood_result.tif"},
        {"param_name": "report", "param_value": "flood_report.pdf"}
    ],
    "task_name": "flood_analysis_2024"
}
```

