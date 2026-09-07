# Plan: MCP 服务端任务标识与输出路径生成

## 目标

让 `run_model` 的唯一任务名和输出数据路径由 MCP 服务端生成，Agent 只表达业务意图、模型参数和期望输出名称。这样可避免 Agent 重试或并发调用时复用任务名、覆盖输出文件。

## 设计决策

- `task_name` 不再是 Agent 必须保证唯一的执行标识。保留它以兼容现有调用，但仅作为可选的展示标签；最终提交给下游的名称一律由服务端生成。
- 最终任务名格式为 `<sanitized-task-label-or-model-name>-YYYYMMDD-HHMMSS-<8hex>`；每一次实际 MCP 提交均生成新值。
- 每个 `output_data` 参数由服务端解析为受控输出根目录下的唯一文件：`<mcp_output_root>/<generated-task-name>--<file-name>`。
- Agent 只能提供单层输出文件名；拒绝绝对路径、相对路径、`..` 路径穿越、空名称和不在元数据中声明的输出参数。
- `RunModelResult` 增加实际 `task_name` 与 `resolved_outputs`，使 Agent 和调用方能够追踪本次提交的真实资源位置。
- GeoRAG 不再按相同工具参数跳过调用；仍保留按工具计数的连续失败熔断。任务标识自动生成只解决每次真实提交的命名与路径冲突。

## TODO

- [x] 1. 复核现状：`ModelCaller` 对空 `task_name` 已生成唯一值，但 `RunModelRequest.outputs` 原样下传；`run_model` 工具说明也将完整输出路径交给 Agent。
- [x] 2. 在 `mcp_service/schemas.py` 将 `task_name` 明确标记为兼容性展示标签，新增受控输出名称的说明；扩展 `RunModelResult`，返回 `project_id`、服务端生成的 `task_name` 与 `resolved_outputs`。
- [x] 3. 在 `mcp_service/egc_service_tools.py` 新增纯函数的任务身份解析：生成简短随机后缀、构造最终任务名、逐个解析输出文件名，并拒绝路径穿越和非字符串输出目标。
- [x] 4. 为输出根目录新增显式配置项 `mcp_output_root`，默认 `/onesis/kt4/job_results`；不要从 Agent 输入推断根目录。
- [x] 5. 将解析后的 `task_name` 和输出映射写入传给 `ModelCaller` 的 request body；保留 `ModelCaller` 的空值兜底生成，作为非 MCP 调用路径的纵深防御。
- [x] 6. 更新 `run_model` 文档和示例：Agent 应传业务参数与输出文件名，不得自行拼接唯一目录或任务标识。
- [x] 7. 增加测试：任务名唯一、同名输出自动隔离、路径穿越拒绝，以及结果 schema 的解析值字段。
- [ ] 8. 重启 pygeomodels 服务，并刷新或重启 GeoRAG 的 MCP 工具加载；用两次相同业务提交验证下游接收到不同最终任务名与不同输出路径。

## 验收标准

- Agent 重复使用相同展示 `task_name` 或省略它时，每次真实 `run_model` 提交都拥有不同的下游任务名。
- 同一输出名称在不同真实提交中生成不同的根目录文件名，不会覆盖已有输出。
- 绝对路径、相对路径、路径穿越和空输出名称在调用下游前被拒绝；每个有效输出都解析到 `mcp_output_root` 下。
- 返回结果包含可用于审计和后续处理的 `project_id`、最终 `task_name` 与 `resolved_outputs`，且不含 Bearer Token。
- 更新后的 MCP schema/描述让 Agent 无需理解唯一命名规则；重复调用由失败熔断保护，而非按相同参数跳过。
- 新旧 schema 契约、动态参数校验与模型提交测试均通过。
