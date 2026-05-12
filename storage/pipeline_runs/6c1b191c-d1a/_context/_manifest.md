# Pipeline Context — 实现 Skill 沉淀交互页面：包含半自动提炼向导（异步 LLM 预填、对比视图编辑）、待审核队列红绿灯可视化与 SSE 实时推送，用户确认后触发 SkillApproved 事件写入主表。

Task ID: 6c1b191c-d1a
Keywords: developer, llm, researcher, skill, skillapproved, sse, 事件写入主表, 包含半自动提, 实时推送, 实现, 对比视图编辑, 异步, 待审核队列红, 沉淀交互页面, 炼向导, 用户确认后触, 绿灯可视化与, 预填
Seeded files: 10

- `src/backend/agents/skill_registry.py`
- `src/backend/agents/plaza_engine.py`
- `src/backend/agents/models.py`
- `src/backend/agents/api.py`
- `src/backend/agents/teams/ai_coding_team.py`
- `src/backend/agents/teams/build_team.py`
- `src/backend/agents/skills/hello.py`
- `src/backend/monitoring/plaza_monitor.py`
- `src/frontend/agent-team-config.html`
- `src/backend/channels/evolution_executor.py`
