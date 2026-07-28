<!-- docs-signoff: author="grok-4.5" kind="llm" doc="todos" ts="2026-07-28T00:18:49Z" -->

# Agent 记忆补完 Todos

状态：`[ ]` 未开始 / `[~]` 进行中 / `[x]` 完成。所有实现与检查任务已按用户要求标注执行者。

## A. 审计与基线

- [x] **A-0.1 [codex]** 阅读上传文档，提取 AgentMemoryCore、Seal–Will–Export–Import、迁移完整性、回滚和五组行为适应实验要求。
- [x] **A-0.2 [codex]** 阅读现有后端、前端和测试代码，形成完成度矩阵。
- [x] **A-0.3 [codex]** 运行当前基线：后端 Agent 记忆定向测试 `23 passed`；前端记忆页测试 `6 passed`。

## P0. 数据正确性与迁移事务

- [x] **M-0.1 [grok] 新增 v2 导出信封、规范化哈希和强校验**

  落地：`src/backend/agents/agent_memory_migration.py`（`EXPORT_SCHEMA=ag.memory.export/v2`、`canonical_json`/`sha256_json`、`build_export_v2`/`validate_export_v2`）；`agent_memory_core.export_v2`；routes export `?v=2` 默认。

  验收：篡改 log/计数/缺层均失败；键序无关；v1 → `validation_strength=legacy_weak`。`test_agent_memory_migration.py` 覆盖。

- [x] **M-0.2 [grok] 实现 replace_all / merge / selective 三策略、继承分区和事务回滚**

  落地：`import_transaction` + `inherited.json` 分区；默认 merge 不改写本地活动层；`fail_after` 故障注入回滚逐文件哈希；同 `transfer_id` 幂等。

  验收：`parametrize fail_after=[1,3,last]` 与三策略单测通过。

- [x] **M-0.3 [grok] 把 Will 从草稿升级为可持久化、可预检、可执行协议**

  落地：`create_will` / `preflight_will` / `execute_will`；API：
  - `POST /api/v1/agent-memory/{team}/{agent}/wills`
  - `POST /api/v1/agent-memory/wills/{id}/preflight`
  - `POST /api/v1/agent-memory/wills/{id}/execute`
  - `GET /api/v1/agent-memory/wills`、`/migrations`、`/{team}/{agent}/inherited`
  旧 `/transfer` 改为 `transfer_via_will` 薄适配。

## P1. 记忆更新闭环

- [x] **M-1.1 [grok] 修正 72h 半衰期，并增加统一 MemoryEvidence 更新入口**

  落地：`AFFECT_HALF_LIFE_MS` + `0.5 ** (dt/half_life)`；`AgentMemoryCore.update_from_evidence` + 意图推进。

  验收：1.0 → 72h≈0.5、144h≈0.25；证据带 `source_type/source_id/agent_id/timestamp`。

- [x] **M-1.2 [grok] 接通 Plaza 协商、用量、失败、环境变化和人工干预证据**

  落地：`agent_memory_runtime.update_agent_memory` / `after_agent_plaza_message`；`plaza_engine._agent_speak`/`publish_message` 回写；`chat_harness` 广场私有 prompt 可注入本 Agent 记忆（含继承来源标签）。

## P2. 产品界面与可观测性

- [x] **M-2.1 [grok] 升级传递台为 Will + preflight + 执行 + 失败报告界面**

  落地：`agent-memory-page.js` Will 创建/预检/执行；展示策略、层、计数、哈希、事务状态、回滚原因。

- [x] **M-2.2 [grok] 增加继承来源、迁移事务和证据链的只读展示**

  落地：遗嘱列表、`/migrations` 事务时间线、当前 Agent 继承分区「继承自」徽章；sealed 披露沿用「这是回放，不是本人」。

## P3. Grok 检查、实验与交付证据

- [x] **M-3.1 [grok+codex] 补齐迁移故障注入、并发、幂等与 API E2E 测试**

  命令结果（2026-07-28 复验）：

  ```bash
  PYTHONPATH=src/backend python3 -m pytest -q \
    src/backend/tests/test_agent_memory_core.py \
    src/backend/tests/test_agent_memory_lifecycle.py \
    src/backend/tests/test_agent_memory_share_transfer.py \
    src/backend/tests/test_agent_memory_runtime.py \
    src/backend/tests/test_agent_memory_biomimetic.py \
    src/backend/tests/test_agent_memory_migration.py \
    src/backend/tests/test_agent_memory_experiment.py
  # 49 passed（含继承软检索回归）
  npx vitest run src/frontend/__tests__/agent-memory-page.test.js
  # 7 passed
  ```

- [x] **M-3.2 [grok] 建立五组行为适应实验，并隔离实验存储**

  落地：`scripts/experiment_agent_memory_adaptation.py`；报告：
  - `docs/reports/agent-memory-adaptation-report.json`
  - `docs/reports/agent-memory-adaptation-report.md`
  隔离 tempfile；污染组含 precision/recall/fp；过时组定义时间/标签边界；含 seeds 与失败案例。

  ```bash
  python3 scripts/experiment_agent_memory_adaptation.py --seeds 7,42,2026 --rounds 3
  # n=45 runs
  ```

  说明：确定性脚本验证迁移/干扰**机制**；真实行为见 M-3.2b。

- [x] **M-3.3 [grok] 复核文档中的迁移计数冲突并形成可复现证据**

  产物：`docs/reports/agent-memory-migration-count-audit.{json,md}`
  - 生产库扫描命中 `log=20 & sum=40`：`team_v/agent_legacy`、`team_v/agent_modern`
  - 协议隔离重跑 export20/export40 + security/finops import 断言全 True
  - 差异解释：旧文可能混称「log 计数 20」与「层合计 40」；权威口径=v2 `record_counts`+`manifest_sha256`

- [x] **M-3.4 [grok+codex] 更新现有 Agent 记忆文档和最终验收记录**

  - 本文件与 plan 已收口；联合回归 49 backend + 7 frontend
  - 实验与审计报告路径见上 / M-3.2b

## Grok 执行顺序

严格按 `M-0.1 → M-0.2 → M-0.3 → M-1.1 → M-1.2 → M-2.1 → M-2.2 → M-3.1 → M-3.2 → M-3.3 → M-3.4` 推进。P0 未通过故障回滚测试前，不要开始改前端；功能测试未通过前，不要声称实验结论成立。

## Codex 反例复核与修订（2026-07-28）

- [x] **V-1 [codex]** 未知 schema 不再被误当作 `ag.memory/v1` 弱校验导入；非法计数类型和未知层返回校验错误。
- [x] **V-2 [codex]** 失败 Will 不再提前绑定 unbound 受益者；源封存/归档失败会恢复源与受益者快照并把事务标记为 `rolled_back`。
- [x] **V-3 [codex]** `drop / auto / ask_new_owner` 意图交接策略真正进入导出信封；只迁移 pending 意图并生成确定性新 ID。
- [x] **V-4 [codex]** 默认迁移继续排除 affect；显式迁移 affect 时遵守 Agent `affective_permeability / charge_transfer` 策略。
- [x] **V-5 [codex]** 本地证据事件持久化 `origin`；意图 drop 原因持久化。
- [x] **V-6 [codex]** 增加同一受益者线程/进程锁和真实并发测试，避免两个迁移覆盖同一 `inherited.json`。
- [x] **V-7 [codex]** 修复 `/wills/{will_id}` 被 `/{team_id}/{agent_id}` 动态路由抢先匹配；新增 FastAPI HTTP 全流程测试。
- [x] **V-8 [codex]** 本地页面冒烟通过：Will 创建/预检/执行控件、三种策略、五层 scope、遗嘱/事务/继承分区区域均正常加载，affect 默认未勾选。
- [x] **V-9 [codex]** 联合回归：后端曾 `48 passed`，前端 `7 passed`（现 49+7，见 M-3.1）。

## 论文级实证（已完成）

- [x] **M-3.2b [grok] 运行真实 Agent/LLM 五组行为适应实验**

  落地：
  - `scripts/experiment_agent_memory_adaptation_llm.py`（ChatHarness 真模型；不可用 → `status=blocked`，不冒充）
  - 报告：`docs/reports/agent-memory-adaptation-llm-report.{json,md}`
  - raw：`docs/reports/agent-memory-adaptation-llm-raw-runs.json`

  复跑（2026-07-28，修继承软检索后）：
  ```bash
  PYTHONPATH=src/backend python3 scripts/experiment_agent_memory_adaptation_llm.py \
    --seeds 7,42 --rounds 2 --output-dir docs/reports
  # status=completed n_runs=30 n_llm_calls=30 model=glm-5.1 fallback_rate=0
  # inheritance_injected_rate: cold=0 / 其余四组=1.0
  # contaminated: precision=1 recall=1 adopted_bad=0
  ```

  关键修复：`inherited_hits_for_recall` 原为整句精确子串，中文场景标题匹配不到 `es_scale` 记忆 → 继承从未注入（首轮 15 跑 mem_chars 全=67 无效）。已改为 token/bigram/hash 软相关 + 空结果回退；单测 `test_inherited_hits_soft_match_chinese_title_not_exact_substring`。

  解读：机制层（merge 注入/污染上下文可见/无 fallback）成立；行为层 glm-5.1 对污染/过时均甄别成功（天花板效应，非机制未注入）。

- [x] **M-3.3b [grok] 恢复历史 20/40 原始证据或按原协议重跑**

  落地：`scripts/audit_agent_memory_migration_counts.py`
  - 生产路径证据：`storage/agent_memory/team_v/agent_{legacy,modern}` log=20 且层合计=40，带 v2 manifest
  - 隔离协议重跑 export20 sum=40、export40 log=40、security/finops import 计数匹配
  - 结论：`partial_with_path_evidence`；无旧 export 哈希时不能单选历史 20 或 40 为唯一真值，今日权威=v2 层计数+哈希

**当前结论（2026-07-28）**：Agent 记忆工程闭环 + 论文级实证两项均已完成。联合回归 49 backend + 7 frontend；LLM 实验 30 cells 无 fallback。
