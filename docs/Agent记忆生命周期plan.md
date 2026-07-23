<!-- docs-signoff: author="grok-4.5" kind="llm" doc="plan" ts="2026-07-24T03:00:00Z" -->
# Agent 记忆生命周期重构 Plan

> 完整架构见会话 plan；本文为仓库内可验收执行版。

## 目标

1. Agent **拥有** MemoryCore，状态机管理 bind/active/shared/sealed/transfer/destroy  
2. 站级菜单 **Agent记忆** 总控台  
3. 小满 / 沈弥安 / 混合 Persona 驱动自主策略  
4. 共享 · 传递 · 保存 · 销毁（P0 完成保存/封存/销毁/Persona；P1 共享与传递）

## 模块

| 模块 | 状态 |
|------|------|
| `agent_memory_core.py` | ✅ 四层 |
| `agent_memory_lifecycle.py` | ✅ P0 |
| `agent_memory_routes.py` + hub | ✅ |
| `agent-memory.html` + nav | ✅ |
| share / transfer | ⏳ P1 |
| runtime chat/task hooks | ⏳ P2 |

## API

- 兼容：`/api/v1/agent-config/teams/{t}/agents/{a}/memory-core/*`  
- 站级：`/api/v1/agent-memory/overview` · `/{t}/{a}/lifecycle` · `/persona` · `/destroy`

## Persona

- **xiaoman 小满**：活体连续、感知/情绪自主  
- **shenmian 沈弥安**：择要、克制检索、反思间隔  
- **hybrid**：默认  
