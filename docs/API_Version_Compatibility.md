# API版本兼容性方案

## 背景

EGC服务部分API已从v1升级到v2，需要支持v1和v2混用的场景。

## 升级现状

### 已升级到 v2
- ✅ `/v2/model-manager/general-models/catalog/categories` - 模型类别目录
- ✅ `/v2/model-manager/general-single-models/{id}/ui-info` - 模型UI信息

### 仍在 v1
- ⏸️ `/v1/model-manager/general-single-models/list` - 模型列表查询
- ⏸️ `/v1/model-manager/general-single-models/{id}/info` - 模型详细信息
- ⏸️ 其他未明确升级的API

## 解决方案：分层版本配置

### 配置方式

在 `default_config.ini` 或 `local_config.ini` 中配置：

```ini
[SERVICE]
# 默认版本（未指定版本的API使用此版本）
api_basename = mbms/v1

# 为特定API指定v2版本
api_version_gm_catalog = v2  # catalog系列使用v2
api_version_sm_ui = v2       # ui-info使用v2
```

### 代码使用

#### 方法1：使用 `build_api_path()` (推荐)

```python
from pygeomodels.config import parse_config

cfg = parse_config()

# 不指定version_key，使用默认v1
path = cfg.build_api_path('model-manager', 'general-single-models', 'list')
# 结果: mbms/v1/model-manager/general-single-models/list

# 指定version_key，自动使用配置的版本
path = cfg.build_api_path(
    'model-manager', 'general-models', 'catalog/categories',
    version_key='gm_catalog'
)
# 结果: mbms/v2/model-manager/general-models/catalog/categories

# UI-info使用v2
path = cfg.build_api_path(
    'model-manager', 'general-single-models', 'pitRemove', 'ui-info',
    version_key='sm_ui'
)
# 结果: mbms/v2/model-manager/general-single-models/pitRemove/ui-info
```

#### 方法2：使用 `get_api_base()` (灵活但需手动拼接)

```python
# 获取默认版本base
base = cfg.get_api_base()  # 'mbms/v1'

# 获取指定版本base
base = cfg.get_api_base('v2')  # 'mbms/v2'

# 完整路径需要手动拼接
url = f"{cfg.modelmanager_url}/{base}/model-manager/general-models/catalog"
```

## 代码改造示例

### 改造前 (硬编码版本)

```python
# modelBank.py - set_categories()
res = restapi_get(
    self.cfg.modelmanager_url,
    "%s/%s/%s/%s" % (
        self.cfg.api_basename,  # 硬编码使用v1
        self.cfg.api_cls_modelmanager,
        self.cfg.api_mgt_generalmodel,
        self.cfg.api_gm_catalogcls,
    ),
    token,
)
```

### 改造后 (自动版本选择)

```python
# modelBank.py - set_categories()
path = self.cfg.build_api_path(
    self.cfg.api_cls_modelmanager,
    self.cfg.api_mgt_generalmodel,
    self.cfg.api_gm_catalogcls,
    version_key='gm_catalog'  # 自动使用v2
)
res = restapi_get(self.cfg.modelmanager_url, path, token)
```

## 添加新的版本覆盖

### 1. 在配置文件中声明

```ini
[SERVICE]
# 如果某个新API升级到v2，添加配置
api_version_new_feature = v2
```

### 2. 在 config.py 中添加属性

```python
class ModelEngineConfig(object):
    def __init__(self, cf):
        # ... existing code ...
        
        self.api_version_new_feature = get_option_value(
            cf, service, 'api_version_new_feature',
            valtyp=str, defvalue='', required=False
        )
```

### 3. 在调用处使用

```python
path = cfg.build_api_path(
    'model-manager', 'new-feature', 'endpoint',
    version_key='new_feature'
)
```

## 测试验证

```bash
# 运行测试脚本验证配置
python -c "
from pygeomodels.config import parse_config
cfg = parse_config()

# 验证v1路径
print('v1 API:', cfg.build_api_path('model-manager', 'general-single-models', 'list'))

# 验证v2路径
print('v2 catalog:', cfg.build_api_path('model-manager', 'general-models', 'catalog', version_key='gm_catalog'))
print('v2 ui-info:', cfg.build_api_path('model-manager', 'general-single-models', 'test', 'ui-info', version_key='sm_ui'))
"
```

## 优势

1. **向后兼容**: 默认使用v1，不影响现有功能
2. **灵活升级**: 通过配置文件控制，无需修改代码
3. **渐进迁移**: 可以逐个API升级，不需要全部一次性迁移
4. **环境差异**: 可以通过 `local_config.ini` 为不同环境配置不同版本
5. **易于维护**: 版本信息集中管理，修改方便

## 注意事项

1. **配置文件注释**: INI文件中行内注释（`key = value # comment`）会被当作值的一部分，应使用独立行注释
2. **版本一致性**: 确保配置的版本与实际EGC服务支持的版本一致
3. **测试覆盖**: 升级API版本后，务必测试相关功能
4. **文档同步**: 更新 `MCP服务代码文档.md` 中的API路径说明

## 未来扩展

当所有API都升级到v2后，可以：

1. 修改默认配置: `api_basename = mbms/v2`
2. 移除所有 `api_version_*` 配置
3. 简化代码，移除版本选择逻辑