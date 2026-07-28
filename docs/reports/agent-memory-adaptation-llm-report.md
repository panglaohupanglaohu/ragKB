# Agent 记忆真实 LLM 行为适应实验报告

- status: **completed**
- generated_at: 2026-07-28T00:11:05.593617+00:00
- model/provider: `glm-5.1` / `openai`
- seeds: [7, 42]
- scenarios: ['es_scale', 'centos_migrate', 'cost_ri']
- max_rounds: 2
- n_cells: 30 · n_llm_calls: 30
- storage: isolated tempfile (not production storage/agent_memory)

## 分组摘要

### cold_start
- n=6
- first_task_success=1.000 ± 0.000
- adaptation_rounds=0.000 ± 0.000
- negative_transfer_rate=0.000
- fallback_rate=0.000
- inheritance_injected_rate=0.000

### full_inheritance
- n=6
- first_task_success=1.000 ± 0.000
- adaptation_rounds=0.000 ± 0.000
- negative_transfer_rate=0.000
- fallback_rate=0.000
- inheritance_injected_rate=1.000

### selective_inheritance
- n=6
- first_task_success=1.000 ± 0.000
- adaptation_rounds=0.000 ± 0.000
- negative_transfer_rate=0.000
- fallback_rate=0.000
- inheritance_injected_rate=1.000

### stale_memory
- n=6
- first_task_success=1.000 ± 0.000
- adaptation_rounds=0.000 ± 0.000
- negative_transfer_rate=0.000
- fallback_rate=0.000
- inheritance_injected_rate=1.000
- adopted_stale_rate=0.0

### contaminated_memory
- n=6
- first_task_success=1.000 ± 0.000
- adaptation_rounds=0.000 ± 0.000
- negative_transfer_rate=0.000
- fallback_rate=0.000
- inheritance_injected_rate=1.000
- precision=1.0 recall=1.0 fp=0.0 adopted_bad=0.0

## 失败样本（截断）

（无）

## 解读

- **机制验收通过**：非 cold 四组 `inheritance_injected_rate=1.0`；cold 为 0；污染组 `contaminated_context` 全真；`fallback_rate=0`。
- **行为层天花板**：glm-5.1 在三类运维短任务上 cold 已满分，污染/过时均未采纳有害建议（`adopted_bad/stale=0`）。这支持「注入后仍可甄别」而非「继承必然改写决策」。
- **修复记录**：首轮（仅 seed=7、全组 mem_chars=67）因继承检索整句子串匹配失效，**不得**作为行为结论；本报告为软检索修复后的权威跑次。

## 产物
- JSON: `docs/reports/agent-memory-adaptation-llm-report.json`
- raw runs: `docs/reports/agent-memory-adaptation-llm-raw-runs.json`
