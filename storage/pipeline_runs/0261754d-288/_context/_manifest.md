# Pipeline Context — 搭建领域事件管道与 SkillStore：定义 InteractionContext 序列化格式，事件携带全量上下文，SkillStore 主表幂等写入 + `schema_version`，异步 Indexing Worker 构建向量索

Task ID: 0261754d-288
Keywords: architect, deployer, developer, indexing, interactioncontext, schema_version, skillstore, worker, 上下文, 主表幂等写入, 事件携带全量, 定义, 序列化格式, 异步, 搭建领域事件, 构建向量索, 管道与
Seeded files: 10

- `src/backend/agents/skill_registry.py`
- `src/backend/agents/plaza_engine.py`
- `src/backend/monitoring/models.py`
- `src/backend/agents/tts_routes.py`
- `src/backend/agents/teams/build_team.py`
- `src/backend/channels/evolution_executor.py`
- `src/backend/channels/bridge_chat.py`
- `src/backend/tests/test_agent_toolbox.py`
- `src/backend/agents/models.py`
- `src/backend/agents/agent_toolbox.py`
