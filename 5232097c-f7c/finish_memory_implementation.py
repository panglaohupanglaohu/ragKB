# -*- coding: utf-8 -*-
from pathlib import Path
R=Path('/Users/panglaohu/Downloads/AgentsGroup2026')
life=R/'src/backend/agents/agent_memory_lifecycle.py';transfer=R/'src/backend/agents/agent_memory_transfer.py';runtime=R/'src/backend/agents/agent_memory_runtime.py';test=R/'src/backend/tests/test_agent_memory_biomimetic.py';ft=R/'src/frontend/__tests__/agent-memory-page.test.js'
def rep(p,a,b):
 t=p.read_text(encoding='utf-8')
 if a not in t: raise RuntimeError(f'missing {p}: {a[:80]}')
 p.write_text(t.replace(a,b,1),encoding='utf-8')
# Team overview exposes styles and dynamic states.
rep(life,
'''                        counts = core.counts()
                        # 简易健康分 0–100：有绑定+有日志+有意图/感知/语气''',
'''                        counts = core.counts()
                        memory_style = core.memory_style()
                        dynamic_state = core.dynamic_state()
                        # 简易健康分 0–100：有绑定+有日志+有意图/感知/语气''')
rep(life,
'''                        "counts": counts,
                        "health": health,
                    }''',
'''                        "counts": counts,
                        "health": health,
                        "memory_style": memory_style if st["state"] not in ("destroyed",) else {},
                        "dynamic_state": dynamic_state if st["state"] not in ("destroyed",) else {},
                    }''')
# Variables must exist even if unreadable.
rep(life,
'''                counts = {}
                health = 0
                if st["state"] not in ("destroyed",):''',
'''                counts = {}
                health = 0
                memory_style = {}
                dynamic_state = {}
                if st["state"] not in ("destroyed",):''')
# Affect transfer constrained by unique style permeability, not visible prototype.
rep(transfer,
'''        src_status = self.lc.get_status(team_id, from_agent_id)
        src_persona = (src_status.get("persona") or "hybrid").lower()
        topo = src.topology()
        charge_policy = (topo.get("charge_transfer") or "ask").lower()
        if src_persona == "shenmian":
            charge_policy = "never"''',
'''        src_status = self.lc.get_status(team_id, from_agent_id)
        src_persona = (src_status.get("persona") or "hybrid").lower()  # legacy prototype only
        topo = src.topology()
        memory_style = src.memory_style()
        permeability = float(memory_style.get("affective_permeability") or 0.0)
        charge_policy = (topo.get("charge_transfer") or "ask").lower()
        if permeability < 0.2:
            charge_policy = "never"
        elif permeability < 0.5 and charge_policy != "never":
            charge_policy = "soft"''')
rep(transfer,
'''                scale = 0.35 if charge_policy == "soft" else 0.5''',
'''                scale = min(permeability, 0.35 if charge_policy == "soft" else 0.5)''')
rep(transfer,
'''            "topology_snapshot": topo,
        }''',
'''            "topology_snapshot": topo,
            "memory_style_snapshot": memory_style,
        }''')
# Runtime text removes persona-specific names.
rep(runtime,'# 失败多 → 遗忘更激进、巩固门槛升高（沈弥安式克制）','# 失败多 → 遗忘更激进、巩固门槛升高（更克制）') if '# 失败多 → 遗忘更激进、巩固门槛升高（沈弥安式克制）' in runtime.read_text(encoding='utf-8') else None
# Tests
with test.open('a',encoding='utf-8') as f:
 f.write('''\n\ndef test_unique_memory_style_and_dynamic_state(tmp_path: Path):
    store = AgentMemoryStore(tmp_path)
    core = AgentMemoryCore("style-team", "agent-one", store=store)
    core.bind(True)
    style = core.memory_style()
    assert style["name"] == "agent-one的记忆方式"
    assert 0 <= style["continuity"] <= 1
    changed = core.set_memory_style({"name": "潮汐式记忆", "continuity": 0.8, "restraint": 0.6})
    assert changed["name"] == "潮汐式记忆"
    assert changed["version"] > style["version"]
    core.log.append({"action": "经历", "detail": "一次重要经历", "importance": 8})
    state = core.dynamic_state()
    assert state["style_name"] == "潮汐式记忆"
    assert 0 <= state["continuity_index"] <= 1
    assert "human_memory_map" in core.systems_view()
\n\ndef test_semantic_layer_can_be_shared(tmp_path: Path):
    from agents.agent_memory_share import AgentMemoryShare
    from agents.agent_memory_lifecycle import AgentMemoryLifecycle
    store = AgentMemoryStore(tmp_path)
    lc = AgentMemoryLifecycle(store=store)
    lc.transition("share-team", "owner", "bind")
    lc.transition("share-team", "reader", "bind")
    owner = AgentMemoryCore("share-team", "owner", store=store)
    owner.semantic.add("失败前先保留回滚点", strength=0.8)
    sharing = AgentMemoryShare(store=store, lifecycle=lc)
    sharing.grant("share-team", "owner", "reader", layers=["semantic"])
    got = sharing.read_shared_layer("share-team", "owner", "reader", "semantic")
    assert got["data"][0]["claim"] == "失败前先保留回滚点"
''')
# Frontend tests: remove old required prototype labels and assert unique style.
t=ft.read_text(encoding='utf-8')
t=t.replace("    expect(page).toContain('xiaoman');\n    expect(page).toContain('shenmian');", "    expect(page).toContain('memory-style');\n    expect(page).toContain('memoryStyleName');")
t=t.replace("  it('supports shared log preview and co_writer path', () => {", "  it('hides prototype names and exposes an agent-owned memory style', () => {\n    expect(html).not.toContain('<b>小满</b>');\n    expect(html).not.toContain('<b>沈弥安</b>');\n    expect(html).toContain('每个 Agent 都会形成自己的记忆方式');\n    expect(page).toContain('连续性');\n    expect(page).toContain('克制性');\n    expect(page).toContain('前瞻意图·过程');\n  });\n\n  it('supports shared log preview and co_writer path', () => {")
ft.write_text(t,encoding='utf-8')
print('finished implementation')
