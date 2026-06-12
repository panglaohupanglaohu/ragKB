# Memory

> Chronological action log. Hooks and AI append to this file automatically.
> Old sessions are consolidated by the daemon weekly.

- 2026-06-12T14:48:00Z | G1-2 完成收口：在 skill_extractor.approve_item 接入 ClassificationStore.seed_reserve_from_extraction（幂等），实现“萃取完成即写入 reserve 分类记录”；新增 tests/test_skill_classifier.py::test_seed_reserve_from_extraction_idempotent，pytest 14 passed。
- 2026-06-12T14:58:00Z | G3-2 本机联测收口：trial_api 增加 routing_comparison/routing_benefit 输出，branches 列表暴露 routing_strategy；新增 tests/test_v4_apis.py::test_routing_strategy_fork_comparison；pytest tests/test_v4_apis.py 14 passed。
