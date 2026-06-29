# Plan: 优化 list_models_by_category 性能

## 背景

当前 `list_models_by_category` 存在严重性能问题：
- 调用该工具时，需要先获取所有 158 个模型的 ID（通过 `/list` 接口）
- 然后对每个 ID 串行调用 `/info` 接口获取详细信息
- **导致 158 个串行 HTTP 请求，响应时间长达数秒**

根本原因：`list_all_models` 需要返回 `model_unique_abbr` 字段，但该字段只在 `/info` 接口中存在，而 `/list` 接口不提供。

## TODO

### 阶段1：代码优化（临时方案）

- [ ] 1. 添加轻量级缓存字段 `_models_basic_info: Dict[str, Dict]` 到 `modelBank.__init__`
- [ ] 2. 修改 `_load_models_by_category()` - 同时缓存 `/list` 返回的完整模型数据
  - 保存 `identification.model_name`（显示名称）
  - 保存 `identification.description`
  - 保存 `categoryName`
  - 键为 `model_id`
- [ ] 3. 添加新方法 `list_all_models_lightweight()` - 使用 `/list` 缓存数据
  - 返回格式: `[{"model_id": "...", "display_name": "...", "description": "..."}]`
  - **不需要调用 `/info` 接口**
- [ ] 4. 保持 `list_all_models()` 原有逻辑不变（用于需要 `model_unique_abbr` 的场景）
- [ ] 5. 更新 `egc_service_tools.py` - 评估是否可以使用轻量级版本
- [ ] 6. 添加单元测试验证缓存机制

### 阶段2：后端接口优化（根本解决方案）

- [ ] 7. 编写后端接口优化需求文档
  - 标题：在 `/list` 接口中添加 `model_unique_abbr` 字段
  - 说明性能问题：当前需要 158 个 `/info` 请求
  - 目标：将请求数从 158 降到 1
  - 建议返回格式示例
- [ ] 8. 提交需求给后端团队
- [ ] 9. 等待后端接口升级完成
- [ ] 10. 修改 `_load_models_by_category()` - 使用 `/list` 的 `model_unique_abbr`
- [ ] 11. 简化 `list_all_models()` - 直接使用轻量级缓存，无需调用 `/info`
- [ ] 12. 删除临时的 `list_all_models_lightweight()` 方法

### 阶段3：文档和测试

- [ ] 13. 更新 `MCP服务代码文档.md` - 说明性能优化
- [ ] 14. 更新 `docs/MCP_EGC_Tools_API_Usage.md` - 更新工作流程说明
- [ ] 15. 性能测试对比（优化前后响应时间）
- [ ] 16. 更新 API_Version_Compatibility.md - 记录 `/list` 接口的字段变更

## Acceptance Criteria

### 阶段1完成标准（临时方案）
- ✅ `list_models_by_category` 首次调用时间从 ~5s 降到 ~0.5s（仅调用 1 个 `/list` 请求）
- ✅ 后续调用使用缓存，响应时间 < 100ms
- ✅ `describe_model` 仍然可以获取完整的参数信息（调用 `/info`）
- ✅ 缓存机制正确处理 token 和 lang 切换

### 阶段2完成标准（根本解决）
- ✅ 后端 `/list` 接口返回 `model_unique_abbr` 字段
- ✅ 代码无需调用 `/info` 接口即可获取 `model_unique_abbr`
- ✅ `list_models_by_category` 首次调用只需 1 个 `/list` 请求
- ✅ 保持向后兼容：如果 `/list` 未返回 `model_unique_abbr`，回退到 `/info` 方式

### Edge Cases
- ❗ Token 过期或切换时，缓存正确失效
- ❗ Language 参数变化时，缓存正确刷新
- ❗ 某些模型没有 `model_unique_abbr` 时，gracefully 处理
- ❗ `/list` 接口返回空数据时，不crash

## 性能对比预估

| 场景 | 当前耗时 | 优化后（阶段1） | 优化后（阶段2） |
|------|---------|----------------|----------------|
| 首次 list_models_by_category | ~5s (158 req) | ~0.5s (1 req) | ~0.5s (1 req) |
| 缓存命中 | ~5s (重新请求) | < 100ms | < 100ms |
| describe_model | ~300ms (1 req) | ~300ms (1 req) | ~300ms (1 req) |

## 技术细节

### 当前数据流
```
list_models_by_category(category="basic")
  ↓
list_all_models(category="basic")
  ↓
set_models_metadata() [调用 158 次 /info]
  ↓
返回 [{model_name: "xxx", model_description: "..."}]
```

### 优化后数据流（阶段1）
```
list_models_by_category(category="basic")
  ↓
list_all_models_lightweight(category="basic")
  ↓
使用 _models_basic_info 缓存 [来自 /list]
  ↓
返回 [{display_name: "xxx", description: "..."}]
```

### 优化后数据流（阶段2 - 理想状态）
```
list_models_by_category(category="basic")
  ↓
list_all_models(category="basic")
  ↓
使用 _models_basic_info 缓存 [来自 /list，包含 model_unique_abbr]
  ↓
返回 [{model_name: "xxx", model_description: "..."}]
```

## 后端需求文档草稿

### 标题
为 `/list` 接口添加 `model_unique_abbr` 字段以优化性能

### 问题描述
当前前端调用 `list_models_by_category` 时存在严重性能问题：
- `/list` 接口返回 158 个模型的 ID 和基础信息
- 但缺少 `model_unique_abbr` 字段（模型唯一标识符）
- 前端不得不对每个 ID 再调用 `/info` 接口获取该字段
- **导致 158 个串行 HTTP 请求，响应时间长达 5 秒以上**

### 解决方案
在 `/v2/model-manager/general-single-models/list` 接口的返回数据中添加 `model_unique_abbr` 字段。

### 修改建议

**当前返回格式**:
```json
{
  "data": {
    "content": [
      {
        "model_id": "e5417946-70f4-328a-80c3-ff0a42a5fb71",
        "identification": {
          "model_name": "Planting Information Speculation",
          "description": "..."
        }
      }
    ]
  }
}
```

**期望返回格式**:
```json
{
  "data": {
    "content": [
      {
        "model_id": "e5417946-70f4-328a-80c3-ff0a42a5fb71",
        "model_unique_abbr": "add_crop_confid",  // 新增字段
        "identification": {
          "model_name": "Planting Information Speculation",
          "description": "..."
        }
      }
    ]
  }
}
```

### 性能收益
- **请求数**: 从 158 降到 1
- **响应时间**: 从 ~5s 降到 ~0.5s
- **用户体验**: 显著提升

### 影响范围
- 仅需在 `/list` 接口查询时 JOIN 模型表的 `model_unique_abbr` 字段
- 向后兼容：新增字段不影响现有客户端
- 前端可以优雅降级：如果该字段不存在，回退到原有 `/info` 方式

### 优先级
**高** - 该问题直接影响用户体验，建议尽快修复
