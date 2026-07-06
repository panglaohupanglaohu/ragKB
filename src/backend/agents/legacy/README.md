# LEGACY 成本体系隔离 (P4-5)

此目录存放已废弃的成本策略模块，不再新增依赖。

## 包含文件
- `cost_policy.py` — Terraform cost_policy（已废弃，由 cost_aggregator.py 替代）
- `cost_gate_routes.py` — 旧成本门禁路由（已废弃）

## 规则
- CI 检查 `grep -r "from.*cost_policy import\|from.*cost_gate_routes import" src/backend/agents/ --include="*.py" | grep -v legacy` 应为空
- 新代码不应 import 这些模块
- 如需迁移功能，请使用 `agents/cost_aggregator.py`
