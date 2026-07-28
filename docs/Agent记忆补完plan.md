<!-- docs-signoff: author="grok-4.5" kind="llm" doc="plan" ts="2026-07-28T00:18:49Z" -->

# Agent 记忆补完 Plan

## 0. 复核后状态（2026-07-28 收口）

Grok 完成首轮实现后，Codex 通过反例、并发、HTTP 和本地页面复核补齐了迁移协议缺口。工程闭环已完成：v2 强校验、三策略导入、继承分区、双边回滚、Will、72h 半衰期、Plaza 证据回流、来源展示和页面均有测试证据。

论文级实证亦已完成：

1. **M-3.2b** 真实 LLM 五组实验（`experiment_agent_memory_adaptation_llm.py`，glm-5.1，30 cells，无 fallback）。首轮因 `inherited_hits_for_recall` 整句精确匹配导致继承未注入；已改为软相关检索并重跑，`inheritance_injected_rate=1.0`（非 cold 组）。
2. **M-3.3b** 生产库命中 log=20/sum=40 样本 + 隔离协议重跑；权威口径=v2 `record_counts`+`manifest_sha256`。

以下第 1～5 节保留为 2026-07-27 实施前的基线审计和目标设计，不代表当前代码仍处于该缺口状态。

## 1. 审计结论

Agent 记忆**尚未全部完成**。现状可以定义为：日常使用 MVP 已可用，上传文档所要求的实验级、可验证闭环仍未完成。

已完成的基础能力包括：按 `team_id + agent_id` 绑定、情节/感知/意图/情绪残留存储、感知 FIFO、巩固与软遗忘、任务/聊天/工具结果写入、运行时检索注入、生命周期、共享、封存、基础导入导出、记忆传递台及相应单元测试。

阻止“完成”判定的核心缺口是：

1. Seal–Will–Export–Import 不是一套可验证事务；`will` 仍是草稿，导出缺少记录数和内容哈希，导入缺少逐层校验及失败回滚。
2. 当前 `import_all` 是覆盖写，`transfer` 是直接追加写；两者没有统一的 `replace_all / merge / selective` 冲突策略，也没有独立的继承分区。
3. Agent 记忆能接收聊天、任务和工具结果，但议事广场阶段被明确跳过，未形成“协商状态/用量证据/失败类型/环境变化/人工干预 → 记忆更新 → 下一轮协商”的闭环。
4. `AFFECT_ETA_MS = 72h` 被用于 `exp(-dt/eta)`，72 小时后只保留约 36.8%，不是文档要求的 72 小时半衰期 50%。
5. 没有冷启动、完整继承、选择性继承、过时记忆、污染记忆五组行为适应实验，也没有负迁移指标和可复现实验报告。

## 2. 代码证据矩阵

| 文档要求 | 代码现状 | 判定 | 主要证据 |
|---|---|---|---|
| 四类并行记忆 | 情节、感知、意图、情绪均有持久化；另有语义核 | 已完成 | `agent_memory_core.py` |
| 感知流最近 500 条 | `PERCEPTION_CAPACITY = 500`，写入和替换均截断 | 已完成 | `agent_memory_core.py:29,314-398` |
| 情绪残留 72h 半衰期 | 有衰减，但公式把 72h 当时间常数 | 未完成 | `agent_memory_core.py:31,624-646` |
| 巩固、遗忘、风险更新、意图推进 | 巩固/软遗忘/适应度电荷已做；没有统一更新函数，意图没有自动推进闭环 | 部分完成 | `agent_memory_core.py:1256-1362` |
| 任务、聊天、工具轨迹回流 | 三类已有接线 | 已完成基础链路 | `agent_memory_runtime.py`、`chat_harness.py`、`runtime/tool_loop.py` |
| 协商状态和用量证据回流 | Plaza 阶段明确不注入记忆，未发现讨论完成后的记忆回写 | 未完成 | `chat_harness.py:1230-1246`、`plaza_engine.py` |
| Seal 形成只读遗产快照 | 有 legacy 快照和生命周期写锁 | 已完成基础能力 | `agent_memory_core.py:1364-1397`、`agent_memory_lifecycle.py` |
| Will 指定受益者、范围、冲突策略 | 只有空白草稿，注释仍写“迁移未实现” | 未完成 | `agent_memory_core.py:1399-1413` |
| 标准导出含版本、来源、时间、计数、哈希 | 只有 schema、来源标识、时间和 layers；无计数、哈希 | 未完成 | `agent_memory_core.py:1212-1227` |
| 导入前校验与失败回滚 | 仅校验顶层 schema，然后逐文件覆盖；跨文件失败不回滚 | 未完成 | `agent_memory_core.py:1229-1254` |
| replace/merge/selective 三策略 | 覆盖导入与追加传递各自存在，但不是统一策略；UI 不可选择 | 部分完成 | `agent_memory_transfer.py`、`agent-memory-page.js:704-805` |
| 来源隔离的继承分区 | 仅加标签、place 文本和 `meta.inherited_from`，继承内容混入本地层 | 未完成 | `agent_memory_transfer.py:90-164,280` |
| 迁移完整性和回滚测试 | 只有成功路径复制/凭吊测试 | 未完成 | `test_agent_memory_share_transfer.py` |
| 五组行为适应实验 | 仓库中未发现对应实验脚本和报告 | 未完成 | `scripts/`、`docs/reports/` 审计 |

## 3. 实施原则

1. 不重写现有记忆核心；在现有 `AgentMemoryCore`、生命周期和 transfer API 上做兼容扩展。
2. 新增统一迁移引擎，现有 `/transfer` 路由改为薄适配层，避免继续维护两套迁移语义。
3. 新导出协议使用 `ag.memory.export/v2`，仍能读取 `ag.memory/v1`，但 v1 只允许显式的兼容导入并在审计中标记为弱校验。
4. 默认策略使用 `merge`，将导入内容放入带 `source_agent` 的继承分区；只有用户明确选择 `replace_all` 时才能覆盖本地活动记忆。
5. 跨层写入必须有迁移前快照、阶段化写入、导入后复核和异常回滚；“每个 JSON 文件原子写”不能替代“整次迁移事务”。
6. Plaza 只向当前发言 Agent 注入其可用记忆，不把私有记忆塞进公共共识提示；讨论产物按参与者和来源写回，保留隐私边界。
7. 行为实验与功能实现分离；实验脚本不得污染 `storage/agent_memory` 的生产数据。

## 4. 目标架构

### 4.1 迁移信封

```text
MemoryExportV2
├── schema_version = ag.memory.export/v2
├── export_id / exported_at
├── source_agent { team_id, agent_id }
├── seal_id
├── record_counts { log, perception, intentions, affect, semantic }
├── content_hashes { layer_sha256..., manifest_sha256 }
├── layers
└── provenance { discussion_ids, task_ids, usage_ids }
```

### 4.2 遗嘱与事务

```text
draft will → preflight validate → snapshot beneficiary → stage import
           → verify staged counts/hashes → commit all layers
           → verify committed state → seal/archive source → audit success
                                      ↘ any failure: restore snapshot + audit failure
```

### 4.3 继承分区

新增 `inherited.json`，按 `partition_id + source_agent + transfer_id` 保存来源和层数据。检索时可以合并本地活动记忆和继承分区，但返回结果必须保留 `origin`，前端也必须显示“本地/继承自谁”。

### 4.4 记忆更新闭环

统一输入对象 `MemoryEvidence`：

```text
deliberation_state + usage_evidence + tool_trace + failure_type
+ environment_delta + human_intervention
        ↓
AgentMemoryCore.update_from_evidence(...)
        ↓
encode → intention progression → risk/affect update → consolidate → forget
        ↓
下一次该 Agent 发言或任务执行时按权限检索
```

## 5. 完成定义

只有同时满足以下条件，才能把 Agent 记忆标记为“完成”：

1. v2 导出信封的 schema、逐层计数、逐层 SHA-256 和 manifest SHA-256 都能验证。
2. 三种导入策略均有单测和 API E2E；默认 merge 不覆盖受益 Agent 的本地记忆。
3. 人为在第 N 层写入时抛错后，受益 Agent 的逐层哈希与导入前完全一致，源 Agent 状态不变。
4. 继承内容有独立分区和来源展示，检索结果不会丢失来源。
5. 72 小时后情绪强度为初值的 50%（允许浮点误差）。
6. Plaza 讨论、任务、工具、用量和人工干预均有可追踪的记忆证据，且能进入下一次该 Agent 的上下文。
7. 五组行为实验可一键运行，输出首任务成功率、适应轮数、历史失败重复率、负迁移率及随机种子。
8. Agent 记忆后端定向测试、前端测试、迁移故障注入测试和 docs 签名检查全部通过。

具体执行项、伪代码和验收命令见 `docs/Agent记忆补完todos.md`。
