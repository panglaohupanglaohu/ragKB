# Pipeline Context — 搭建领域事件管道与 SkillStore：事件携带完整上下文而非 ID，SkillStore 主表幂等写入并带 schema_version，异步 Indexing Worker 消费事件构建向量索引，检索与衰减策略通过 SkillQuer

Task ID: fbdf38b3-949
Keywords: architect, deployer, developer, indexing, schema_version, skillquer, skillstore, worker, 上下文而非, 主表幂等写入, 事件携带完整, 向量索引, 并带, 异步, 搭建领域事件, 检索与衰减策, 消费事件构建, 略通过, 管道与
Seeded files: 10

- `src/backend/agents/tts_routes.py`
- `src/backend/agents/plaza_engine.py`
- `src/backend/agents/skill_registry.py`
- `src/backend/agents/teams/build_team.py`
- `src/backend/channels/evolution_executor.py`
- `src/backend/tests/test_agent_toolbox.py`
- `src/backend/agents/models.py`
- `src/backend/agents/teams/ai_coding_team.py`
- `src/backend/monitoring/models.py`
- `src/backend/channels/evolution_executor.py`
