<!-- docs-signoff: author="grok-4.5" kind="llm" doc="plan" ts="2026-07-25T03:00:00Z" -->

# 议事大厅 · 执行计划多队并行派发

## 目标

一份执行计划 → **多个 agent 团队**各得完整任务赛道，便于孪生页 `extra_team_ids` 多队对抗。

## 模型

```
dispatch_group_id  (共享组 id)
  ├── team_alpha / lane=primary  → tasks[1..n]
  ├── team_beta  / lane=rival_1  → tasks[1..n]  (同一步骤克隆)
  └── …
```

- **mode=parallel（默认）**：每队独立克隆全步骤（对抗/对照）
- 元数据：`dispatch_group_id`, `dispatch_team_ids`, `multi_team`, `lane`
- `disc.plan.dispatches[]` 聚合各队 task_ids

## API

`POST .../dispatch` · `dispatch-and-execute` · `assign`

```json
{ "team_id": "primary", "team_ids": ["a","b","c"], "mode": "parallel" }
```

响应含 `dispatches`, `twin_hint.url_query`。

## UI

计划卡：团队 **多选 checkbox** + 全选/清空；派发提示多队；任务列表按赛道汇总。

## 孪生

深链：`team_id` + `team_ids` + `extra_team_ids` + `matchup=1`  
session：`eco_extra_team_ids` / `eco_bound_teams`  
eco-console 创建 drill 时读入 `extra_team_ids`。
