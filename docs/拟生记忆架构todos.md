<!-- docs-signoff: author="grok-4.5" kind="llm" doc="todos" ts="2026-07-24T01:40:00Z" -->

# 拟生记忆架构 Todos

## P0 正名与兼容
- [x] `systems_catalog` / `LEGACY_TO_SYSTEM` 映射
- [x] `overview.systems` + `ui_labels`
- [x] 前瞻意图 / 情绪电荷 文案（前端 + API summary）
- [x] share 支持 semantic 层；默认不共享 affect

## P1 语义 + 遗忘
- [x] `SemanticCore` + `semantic.json`
- [x] `consolidate_tick` / `forget_tick`
- [x] 路由 `/consolidate` `/forget` `/systems`
- [x] runtime 注入语义 + 任务路径 fitness/consolidate/forget
- [x] `save` 生命周期触发 consolidate+forget
- [x] Persona 切换写默认 topology
- [x] 单测 `test_agent_memory_biomimetic.py`

## P2 动态拓扑 + 物竞
- [x] `drift_topology`（age / fitness / survival_ticks，有 clamp）
- [x] eco `survival_ticks` 读 profile → `apply_fitness` / `record_task_outcome`
- [x] working 槽位 push/clear + API + 对话注入 + 中枢展示
- [x] 路由 `/working` `/forgotten` `/drift`
- [x] EventBus `ECO_SURVIVAL_UPDATED` + collab apply emit + hooks
- [x] `apply_eco_survival_to_memory` 直接路径

## P3 传递体验
- [x] transfer 默认复制 semantic
- [x] 小满连续叙事 / 沈弥安凭吊清单 `transfer_narrative`
- [x] 沈弥安/never 电荷剥离；soft 弱传
- [x] 中枢分栏：层 | 场 | 过程 + 拓扑行
- [x] soft-forget 审计可视化（中枢 + overview.forgotten_recent）
- [x] 配置页 **工作台** 独立 pane

## 可选增强
- [x] vector-lite 哈希袋余弦（默认开，`AG_MEMORY_VECTOR_LITE=0` 关）
- [x] README 拟生记忆专章更新

## 完成标准
- [x] 记忆相关单测全绿
- [x] docs plan/todos 全部勾选
