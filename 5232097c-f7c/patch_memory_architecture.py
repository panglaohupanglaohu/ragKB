# -*- coding: utf-8 -*-
"""Surgical patch for the biomimetic memory architecture."""
from pathlib import Path

ROOT=Path('/Users/panglaohu/Downloads/AgentsGroup2026')
core=ROOT/'src/backend/agents/agent_memory_core.py'
lifecycle=ROOT/'src/backend/agents/agent_memory_lifecycle.py'
routes=ROOT/'src/backend/agents/agent_memory_routes.py'
share=ROOT/'src/backend/agents/agent_memory_share.py'


def replace(path, old, new):
    text=path.read_text(encoding='utf-8')
    if old not in text:
        raise RuntimeError(f'fragment not found in {path}: {old[:80]}')
    path.write_text(text.replace(old,new,1),encoding='utf-8')

# Human-memory-inspired systems: semantic renamed autobiographical/semantic, procedural carried by skills.
replace(core,
'''SYSTEM_LABELS = {
    "sensory": "感觉痕迹",
    "episodic": "情节",
    "semantic": "语义核",
    "working": "工作台",
    "affective": "情绪电荷",
    "prospective": "前瞻意图",
}''',
'''SYSTEM_LABELS = {
    "sensory": "感觉痕迹",
    "episodic": "情节痕迹",
    "semantic": "自传语义",
    "working": "工作台",
    "affective": "情绪选择场",
    "prospective": "前瞻意图",
}
HUMAN_MEMORY_MAP = {
    "sensory": {"human_analogy": "sensory memory", "role": "极短暂输入痕迹，等待注意选择"},
    "working": {"human_analogy": "working memory", "role": "当前任务的容量受限工作空间"},
    "episodic": {"human_analogy": "episodic/autobiographical memory", "role": "带时间、地点和自我来源的经历"},
    "semantic": {"human_analogy": "semantic memory", "role": "从经历巩固出的概念、规律与自我叙事"},
    "prospective": {"human_analogy": "prospective memory", "role": "未来触发时要完成的行动；是过程，不是存储层"},
    "affective": {"human_analogy": "emotion-memory modulation", "role": "用价值、唤醒和身体式信号调制注意、巩固、检索与遗忘"},
    "procedural": {"human_analogy": "procedural memory", "role": "由技能库、熟练度和执行轨迹承载，不复制为文本层"},
}
MEMORY_STYLE_SCHEMA = "ag.memory.style/v1"''')

replace(core,
'''        "note": "prospective(前瞻意图) 是过程缓冲，不是记忆层；affective 是电荷场，不存事实。",
    }''',
'''        "human_memory_map": dict(HUMAN_MEMORY_MAP),
        "note": "三类保存痕迹：sensory / episodic / semantic；working 与 prospective 是过程，affective 是选择场，procedural 由技能系统承载。",
    }''')

# Insert unique style methods before topology.
replace(core,
'''    def topology(self) -> Dict[str, Any]:
        meta = self.store.load(self.team_id, self.agent_id, "meta", {})''',
'''    def memory_style(self) -> Dict[str, Any]:
        """Agent 独有的记忆方式。旧 persona 只作为不可见的初始化原型。"""
        meta = self._load_meta()
        style = meta.get("memory_style")
        if not isinstance(style, dict):
            prototype = str(meta.get("persona") or "hybrid")
            topo = dict(meta.get("topology") or self._default_topology(prototype))
            style = {
                "schema": MEMORY_STYLE_SCHEMA,
                "name": f"{self.agent_id}的记忆方式",
                "prototype": prototype,
                "created_at": int(meta.get("bound_at") or _now_ms()),
                "updated_at": _now_ms(),
                "version": 1,
                "continuity": 0.65 if prototype == "xiaoman" else (0.35 if prototype == "shenmian" else 0.5),
                "restraint": 0.35 if prototype == "xiaoman" else (0.8 if prototype == "shenmian" else 0.55),
                "plasticity": 0.7 if prototype == "xiaoman" else (0.35 if prototype == "shenmian" else 0.55),
                "affective_permeability": 0.65 if prototype == "xiaoman" else (0.15 if prototype == "shenmian" else 0.4),
                "topology": topo,
                "history": [{"t": _now_ms(), "reason": "prototype_seed", "prototype": prototype}],
            }
            meta["memory_style"] = style
            self._save_meta(meta)
        return json.loads(json.dumps(style))

    def set_memory_style(self, patch: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        patch = patch or {}
        meta = self._load_meta()
        style = self.memory_style()
        for key in ("continuity", "restraint", "plasticity", "affective_permeability"):
            if key in patch:
                style[key] = round(_clamp(float(patch[key]), 0.0, 1.0), 3)
        if patch.get("name"):
            style["name"] = str(patch["name"]).strip()[:48]
        topo_patch = patch.get("topology")
        if isinstance(topo_patch, dict):
            topo = dict(style.get("topology") or self.topology())
            allowed = {
                "sensory_capacity", "episodic_soft_cap", "semantic_max", "working_slots",
                "consolidate_min_importance", "forget_aggressiveness", "charge_transfer",
            }
            for key, value in topo_patch.items():
                if key in allowed:
                    topo[key] = value
            style["topology"] = topo
            meta["topology"] = topo
        style["version"] = int(style.get("version") or 1) + 1
        style["updated_at"] = _now_ms()
        history = list(style.get("history") or [])
        history.append({"t": style["updated_at"], "reason": str(patch.get("reason") or "manual_tuning")[:80]})
        style["history"] = history[-50:]
        meta["memory_style"] = style
        self._save_meta(meta)
        return self.memory_style()

    def dynamic_state(self) -> Dict[str, Any]:
        """随时间变化的记忆有机体状态，不把原始计数误当作静态容量。"""
        now = _now_ms()
        style = self.memory_style()
        live_events = [e for e in self.log.events if not e.get("forgotten_at")]
        strengths = []
        for e in live_events:
            anchor = e.get("lastAccessAt") or e.get("t") or now
            hours = max(0.0, (now - float(anchor)) / 3_600_000)
            strengths.append((RECENCY_DECAY_PER_HOUR ** hours) * (float(e.get("importance") or 5) / 10.0))
        semantic_strength = sum(float(c.get("strength") or 0.5) for c in self.semantic.active())
        charge = self.affect.residue(now)
        charge_energy = min(1.0, sum(float(v) for v in (charge.get("labels") or {}).values()))
        continuity = float(style.get("continuity") or 0.5)
        active_mass = sum(strengths) + semantic_strength
        forgotten = len([e for e in self.log.events if e.get("forgotten_at")])
        continuity_index = _clamp(
            0.45 * continuity + 0.25 * min(1.0, semantic_strength / 10.0)
            + 0.2 * min(1.0, len(self._working_slots()) / max(1, int(self.topology().get("working_slots") or 5)))
            + 0.1 * (1.0 if self.is_sealed() else 0.5), 0.0, 1.0,
        )
        return {
            "t": now,
            "active_memory_mass": round(active_mass, 3),
            "charge_energy": round(charge_energy, 3),
            "continuity_index": round(continuity_index, 3),
            "forgetting_ratio": round(forgotten / max(1, len(self.log.events)), 3),
            "plasticity": style.get("plasticity"),
            "restraint": style.get("restraint"),
            "style_name": style.get("name"),
        }

    def topology(self) -> Dict[str, Any]:
        meta = self.store.load(self.team_id, self.agent_id, "meta", {})''')

# Make topology style-aware.
replace(core,
'''        topo = meta.get("topology")
        if not isinstance(topo, dict):
            topo = self._default_topology(meta.get("persona") or "hybrid")
        return topo''',
'''        topo = meta.get("topology")
        style = meta.get("memory_style")
        if not isinstance(topo, dict) and isinstance(style, dict):
            topo = style.get("topology")
        if not isinstance(topo, dict):
            topo = self._default_topology(meta.get("persona") or "hybrid")
        return topo''')

# Sync drift into style and derive drift from unique traits.
replace(core,
'''        fd = _clamp(float(fitness_delta), -1.0, 1.0)
        # 失败多 → 遗忘更激进、巩固门槛升高（沈弥安式克制）''',
'''        fd = _clamp(float(fitness_delta), -1.0, 1.0)
        style = self.memory_style()
        plasticity = float(style.get("plasticity") or 0.5)
        restraint = float(style.get("restraint") or 0.5)
        continuity = float(style.get("continuity") or 0.5)
        # 失败多 → 遗忘更激进、巩固门槛升高；变化幅度由该 Agent 的可塑性控制''')
replace(core,
'''        forget = _clamp(forget - fd * 0.04 + (0.01 if age_h > 168 else 0), 0.2, 0.9)
        min_imp = int(topo.get("consolidate_min_importance") or base["consolidate_min_importance"])
        min_imp = int(_clamp(min_imp - fd * 0.5 + (0.2 if age_h > 336 else 0), 3, 9))''',
'''        forget = _clamp(forget - fd * (0.02 + 0.06 * plasticity) + 0.025 * restraint + (0.01 if age_h > 168 else 0), 0.15, 0.95)
        min_imp = int(topo.get("consolidate_min_importance") or base["consolidate_min_importance"])
        min_imp = int(_clamp(min_imp - fd * plasticity + restraint * 0.7 + (0.2 if age_h > 336 else 0), 3, 9))''')
replace(core,
'''                soft_cap + fd * 10 + min(40, surv / 50.0),''',
'''                soft_cap + fd * (6 + 16 * plasticity) + min(40, surv / 50.0) + 12 * continuity,''')
replace(core,
'''        meta["topology"] = topo
        self._save_meta(meta)''',
'''        meta["topology"] = topo
        style = self.memory_style()
        style["topology"] = dict(topo)
        style["updated_at"] = now
        history = list(style.get("history") or [])
        history.append({"t": now, "reason": "fitness_drift", "fitness_delta": fd})
        style["history"] = history[-50:]
        meta["memory_style"] = style
        self._save_meta(meta)''',1)

# Add style/dynamic state to views and exports.
replace(core,
'''            "topology": self.topology(),
        }''',
'''            "topology": self.topology(),
            "memory_style": self.memory_style(),
            "dynamic_state": self.dynamic_state(),
        }''',1)
replace(core,
'''            "topology": self.topology(),
            "memorial": self.memorial() if sealed else None,''',
'''            "topology": self.topology(),
            "memory_style": self.memory_style(),
            "dynamic_state": self.dynamic_state(),
            "memorial": self.memorial() if sealed else None,''')
replace(core,
'''                "semantic": "语义核",
                "working": "工作台",''',
'''                "semantic": "自传语义",
                "working": "工作台（过程）",''')

# Add memory style route after persona route.
replace(routes,
'''@hub_router.get("/{team_id}/{agent_id}/audit", summary="审计")''',
'''@hub_router.get("/{team_id}/{agent_id}/memory-style", summary="Agent 独有记忆方式")
def hub_memory_style_get(team_id: str, agent_id: str) -> Dict[str, Any]:
    core = _core(team_id, agent_id)
    return {"ok": True, "memory_style": core.memory_style(), "dynamic_state": core.dynamic_state()}


@hub_router.put("/{team_id}/{agent_id}/memory-style", summary="调整 Agent 独有记忆方式")
def hub_memory_style_put(team_id: str, agent_id: str, body: Dict[str, Any] = Body(default={})) -> Dict[str, Any]:
    core = _writable(team_id, agent_id)
    style = core.set_memory_style(body or {})
    _lc()._append_audit(team_id, agent_id, {"t": __import__('time').time_ns() // 1_000_000, "action": "set_memory_style", "version": style.get("version")})
    return {"ok": True, "memory_style": style, "dynamic_state": core.dynamic_state()}


@hub_router.get("/{team_id}/{agent_id}/audit", summary="审计")''')

# Semantic share bug.
replace(share,
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

print('patched memory architecture')
