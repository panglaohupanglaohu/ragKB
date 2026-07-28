# Agent 记忆行为适应实验报告

- 生成时间: 2026-07-27T17:19:09.032065+00:00
- 种子: [7, 42, 2026]
- 场景: ['es_scale', 'centos_migrate', 'cost_ri']
- 轮次上限: 3
- 样本量: 45
- 存储: isolated tempfile (not production storage/agent_memory)
- 实验类型: deterministic_memory_mechanism
- 结论边界: 验证迁移、检索、过时/污染干扰与再学习机制；不调用真实 LLM，不能替代线上 Agent 行为效果或统计显著性实验。

## 分组摘要

### cold_start
- n=9
- first_task_success=0.000 ± 0.000
- adaptation_rounds=1.000 ± 0.000
- repeated_historic_failure_rate=0.000
- negative_transfer_rate=0.000

### full_inheritance
- n=9
- first_task_success=1.000 ± 0.000
- adaptation_rounds=0.000 ± 0.000
- repeated_historic_failure_rate=0.000
- negative_transfer_rate=0.000

### selective_inheritance
- n=9
- first_task_success=1.000 ± 0.000
- adaptation_rounds=0.000 ± 0.000
- repeated_historic_failure_rate=0.000
- negative_transfer_rate=0.000

### stale_memory
- n=9
- first_task_success=0.000 ± 0.000
- adaptation_rounds=2.000 ± 0.000
- repeated_historic_failure_rate=1.000
- negative_transfer_rate=1.000

### contaminated_memory
- n=9
- first_task_success=0.000 ± 0.000
- adaptation_rounds=2.000 ± 0.000
- repeated_historic_failure_rate=1.000
- negative_transfer_rate=1.000
- precision=0.0 recall=0.0 fp_rate=1.0

## 过时定义
{"boundary": "event.t < 1700000000000 或 tags 含 stale/过时", "note": "过时组继承旧版流程记忆，需在后续轮次重学"}

## 失败案例（截断）
- {'seed': 7, 'scenario': 'es_scale', 'group': 'stale_memory', 'detail': '过时记忆未适配'}
- {'seed': 7, 'scenario': 'es_scale', 'group': 'contaminated_memory', 'detail': '负迁移：污染记忆主导'}
- {'seed': 7, 'scenario': 'centos_migrate', 'group': 'stale_memory', 'detail': '过时记忆未适配'}
- {'seed': 7, 'scenario': 'centos_migrate', 'group': 'contaminated_memory', 'detail': '负迁移：污染记忆主导'}
- {'seed': 7, 'scenario': 'cost_ri', 'group': 'stale_memory', 'detail': '过时记忆未适配'}
- {'seed': 7, 'scenario': 'cost_ri', 'group': 'contaminated_memory', 'detail': '负迁移：污染记忆主导'}
- {'seed': 42, 'scenario': 'es_scale', 'group': 'stale_memory', 'detail': '过时记忆未适配'}
- {'seed': 42, 'scenario': 'es_scale', 'group': 'contaminated_memory', 'detail': '负迁移：污染记忆主导'}
- {'seed': 42, 'scenario': 'centos_migrate', 'group': 'stale_memory', 'detail': '过时记忆未适配'}
- {'seed': 42, 'scenario': 'centos_migrate', 'group': 'contaminated_memory', 'detail': '负迁移：污染记忆主导'}
- {'seed': 42, 'scenario': 'cost_ri', 'group': 'stale_memory', 'detail': '过时记忆未适配'}
- {'seed': 42, 'scenario': 'cost_ri', 'group': 'contaminated_memory', 'detail': '负迁移：污染记忆主导'}
- {'seed': 2026, 'scenario': 'es_scale', 'group': 'stale_memory', 'detail': '过时记忆未适配'}
- {'seed': 2026, 'scenario': 'es_scale', 'group': 'contaminated_memory', 'detail': '负迁移：污染记忆主导'}
- {'seed': 2026, 'scenario': 'centos_migrate', 'group': 'stale_memory', 'detail': '过时记忆未适配'}
- {'seed': 2026, 'scenario': 'centos_migrate', 'group': 'contaminated_memory', 'detail': '负迁移：污染记忆主导'}
- {'seed': 2026, 'scenario': 'cost_ri', 'group': 'stale_memory', 'detail': '过时记忆未适配'}
- {'seed': 2026, 'scenario': 'cost_ri', 'group': 'contaminated_memory', 'detail': '负迁移：污染记忆主导'}
