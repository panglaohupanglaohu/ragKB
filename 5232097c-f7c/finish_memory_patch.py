# -*- coding: utf-8 -*-
from pathlib import Path
R=Path('/Users/panglaohu/Downloads/AgentsGroup2026')
core=R/'src/backend/agents/agent_memory_core.py'; routes=R/'src/backend/agents/agent_memory_routes.py'; share=R/'src/backend/agents/agent_memory_share.py'
def rep(p,a,b):
 t=p.read_text(encoding='utf-8')
 if a not in t: print('SKIP',p.name,a[:45]);return
 p.write_text(t.replace(a,b,1),encoding='utf-8');print('OK',p.name,a[:35])

# Complete sync drift; patch exactly within drift method marker context.
rep(core,
'''        meta["topology"] = topo
        self._save_meta(meta)
        # 感知容量即时生效''',
'''        meta["topology"] = topo
        style = self.memory_style()
        style["topology"] = dict(topo)
        style["updated_at"] = now
        history = list(style.get("history") or [])
        history.append({"t": now, "reason": "fitness_drift", "fitness_delta": fd})
        style["history"] = history[-50:]
        meta["memory_style"] = style
        self._save_meta(meta)
        # 感知容量即时生效''')
# systems view exact ending near topology
rep(core,
'''            "topology": self.topology(),
        }

    def memory_style''',
'''            "topology": self.topology(),
            "memory_style": self.memory_style(),
            "dynamic_state": self.dynamic_state(),
        }

    def memory_style''')
# overview exact
rep(core,
'''            "systems": self.systems_view(),
            "topology": self.topology(),
            "memorial": self.memorial() if sealed else None,''',
'''            "systems": self.systems_view(),
            "topology": self.topology(),
            "memory_style": self.memory_style(),
            "dynamic_state": self.dynamic_state(),
            "memorial": self.memorial() if sealed else None,''')
rep(core,'''                "semantic": "语义核",
                "working": "工作台",''','''                "semantic": "自传语义",
                "working": "工作台（过程）",''')

# routes
rep(routes,
'''@hub_router.get("/{team_id}/{agent_id}/audit", summary="审计")''',
'''@hub_router.get("/{team_id}/{agent_id}/memory-style", summary="Agent 独有记忆方式")
def hub_memory_style_get(team_id: str, agent_id: str) -> Dict[str, Any]:
    core = _core(team_id, agent_id)
    return {"ok": True, "memory_style": core.memory_style(), "dynamic_state": core.dynamic_state()}


@hub_router.put("/{team_id}/{agent_id}/memory-style", summary="调整 Agent 独有记忆方式")
def hub_memory_style_put(team_id: str, agent_id: str, body: Dict[str, Any] = Body(default={})) -> Dict[str, Any]:
    core = _writable(team_id, agent_id)
    style = core.set_memory_style(body or {})
    _lc()._append_audit(team_id, agent_id, {"t": __import__("time").time_ns() // 1_000_000, "action": "set_memory_style", "version": style.get("version")})
    return {"ok": True, "memory_style": style, "dynamic_state": core.dynamic_state()}


@hub_router.get("/{team_id}/{agent_id}/audit", summary="审计")''')
# semantic sharing
rep(share,
'''        elif layer == "affect":
            data = core.affect.residue()
        else:
            raise MemoryLifecycleError("invalid_layer", layer)''',
'''        elif layer == "affect":
            data = core.affect.residue()
        elif layer == "semantic":
            data = core.semantic.active()[-limit:]
        else:
            raise MemoryLifecycleError("invalid_layer", layer)''')
print('finished')
