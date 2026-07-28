# Agent 记忆迁移计数审计（M-3.3b）

- generated_at: 2026-07-28T00:00:55.318056+00:00
- old_claims: [20, 40]
- production_root: `/Users/panglaohu/Downloads/AgentsGroup2026/storage/agent_memory`

## 生产库命中
- n_agents_scanned: 20
- log=20 & sum=40 样本数: 2
  - `team_v/agent_legacy` counts={'log': 20, 'perception': 20, 'intentions': 0, 'affect': 0, 'semantic': 0} manifest=`2924e663a81a39e7…` paths=['log', 'perception', 'affect', 'meta']
  - `team_v/agent_modern` counts={'log': 20, 'perception': 20, 'intentions': 0, 'affect': 0, 'semantic': 0} manifest=`621066a93cffac76…` paths=['log', 'perception', 'intentions', 'affect', 'semantic', 'meta']

## 协议重跑（隔离）
- seed: 20260728
- export20: {'log': 20, 'perception': 20, 'intentions': 0, 'affect': 0, 'semantic': 0} sum=40
- export40: {'log': 40, 'perception': 40, 'intentions': 0, 'affect': 0, 'semantic': 0}
- import security partition: {'log': 20, 'perception': 20, 'intentions': 0, 'affect': 0, 'semantic': 0}
- import finops partition: {'log': 20, 'perception': 20, 'intentions': 0, 'affect': 0, 'semantic': 0}
- assertions: {'export20_log_is_20': True, 'export20_sum_is_40': True, 'export40_log_is_40': True, 'import_counts_match_export20': True}

## 差异原因
生产库存在 log=20 且 layers 合计=40 的样本（如 team_v/*），旧文档可能把「log 计数 20」与「层合计 40」混称为 20/40。 v2 信封以 layers 重新计数+哈希为准；无旧 export 哈希时不能断言历史声明哪一个错误。

## 结论
{
  "can_adjudicate_historical_20_or_40_as_ground_truth": "partial_with_path_evidence",
  "authoritative_today": "v2 record_counts + manifest_sha256 from layers",
  "protocol_export20": {
    "log": 20,
    "perception": 20,
    "intentions": 0,
    "affect": 0,
    "semantic": 0
  },
  "protocol_export40": {
    "log": 40,
    "perception": 40,
    "intentions": 0,
    "affect": 0,
    "semantic": 0
  },
  "protocol_import_security_counts": {
    "log": 20,
    "perception": 20,
    "intentions": 0,
    "affect": 0,
    "semantic": 0
  },
  "protocol_import_finops_counts": {
    "log": 20,
    "perception": 20,
    "intentions": 0,
    "affect": 0,
    "semantic": 0
  }
}

JSON 产物: `/Users/panglaohu/Downloads/AgentsGroup2026/docs/reports/agent-memory-migration-count-audit.json`
