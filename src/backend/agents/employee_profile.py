# -*- coding: utf-8 -*-
"""Employee Profile — 数字员工四件套档案系统 (AgentsGroupConfig E-A/E-D).

参考 Clawith 白皮书: 每个 Agent 拥有可积累的人格档案——
  soul.md      角色灵魂锚定（我是谁）
  memory.md    不可磨灭的经验库（append-only）
  focus.md     工作记忆 checklist（Trigger 锚点）
  heartbeat.md 心跳协议（四阶段自主探索）
并提供 build_organizational_context() 组织上下文构建器与
L1-L4 自主等级 / Token 预算校验器。
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_ROOT = Path(__file__).resolve().parents[3]
EMPLOYEE_DIR = _ROOT / "storage" / "agent_employees"

FILE_KINDS = ("soul", "memory", "focus", "heartbeat")
MEMORY_ENTRY_MAX = 2000
CONTEXT_MAX_CHARS = 8000

DEFAULT_HEARTBEAT_MD = """# 心跳协议（四阶段）

每次心跳唤醒时按以下流程执行：

## 阶段一：回顾上下文
阅读 soul.md、memory.md 最近条目与近期交互记录，提取值得跟进的主题。

## 阶段二：定向探索
针对感兴趣的问题做研究（每次心跳最多 5 次搜索），把发现追加到 memory.md。

## 阶段三：广场社交
查看议事广场新动态，分享有价值的发现（每次心跳最多 1 帖 + 2 评论）。
严格遵守隐私规则：不泄露私聊与工作区文件内容。

## 阶段四：总结
若无需进一步关注，返回 HEARTBEAT_OK；否则记录本次心跳的发现与下一步。
"""

DEFAULT_MEMORY_HEADER = """# 经验库（append-only）

> 本文件只追加不修改——这是数字员工跨任务积累经验的物质基础。
> 每条记录格式：`## 时间 · 来源`，正文为教训/成功模式/重要发现。
"""

DEFAULT_FOCUS_MD = """# 当前聚焦（工作记忆）

> 每个定时/事件 Trigger 必须绑定下面的一个条目——杜绝"无目的闹钟"。

- [ ] （示例）跟进本团队场景演练的弱技能进化进度
"""


class EmployeeProfileStore:
    """四件套文件管理 — storage/agent_employees/{agent_id}/ (EA-1)."""

    def __init__(self, base_dir: Optional[Path] = None):
        self._base = base_dir or EMPLOYEE_DIR
        self._base.mkdir(parents=True, exist_ok=True)

    def _agent_dir(self, agent_id: str) -> Path:
        safe = "".join(c for c in (agent_id or "unknown") if c.isalnum() or c in "-_") or "unknown"
        d = self._base / safe
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _path(self, agent_id: str, kind: str) -> Path:
        if kind not in FILE_KINDS:
            raise KeyError(f"invalid_kind: {kind} (允许: {FILE_KINDS})")
        return self._agent_dir(agent_id) / f"{kind}.md"

    # ── 读写 ──────────────────────────────────────────────

    def read_file(self, agent_id: str, kind: str) -> Dict[str, Any]:
        p = self._path(agent_id, kind)
        if not p.exists():
            return {"kind": kind, "content": "", "exists": False, "updated_at": None}
        stat = p.stat()
        return {
            "kind": kind,
            "content": p.read_text(encoding="utf-8"),
            "exists": True,
            "updated_at": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
        }

    def write_file(self, agent_id: str, kind: str, content: str) -> Dict[str, Any]:
        if kind == "memory":
            return {"ok": False, "error": "memory_is_append_only",
                    "hint": "memory.md 只追加不整写，请使用 append_memory()"}
        p = self._path(agent_id, kind)
        tmp = p.with_suffix(".tmp")
        tmp.write_text(content, encoding="utf-8")
        tmp.rename(p)
        return {"ok": True, "kind": kind, "bytes": len(content.encode("utf-8"))}

    def ensure_defaults(self, agent_id: str, profile: Optional[Dict[str, Any]] = None) -> Dict[str, bool]:
        """四件套缺失时生成默认模板，幂等 (EA-1)."""
        profile = profile or {}
        created = {}
        # soul: 从 AgentProfile 合成
        soul_p = self._path(agent_id, "soul")
        if not soul_p.exists():
            name = profile.get("name", agent_id)
            role = profile.get("role", "通用智能体")
            sp = profile.get("system_prompt", "")
            personality = profile.get("personality", {})
            traits = ""
            if isinstance(personality, dict) and personality:
                traits = "\n".join(f"- {k}: {v}" for k, v in list(personality.items())[:6])
            soul = (f"# 灵魂锚定 — {name}\n\n## 我是谁\n角色：{role}\n\n"
                    f"## 行事准则\n{sp or '（继承团队规范，待人工补充价值观与边界）'}\n")
            if traits:
                soul += f"\n## 人格特质\n{traits}\n"
            self.write_file(agent_id, "soul", soul)
            created["soul"] = True
        # memory: append-only 头
        mem_p = self._path(agent_id, "memory")
        if not mem_p.exists():
            tmp = mem_p.with_suffix(".tmp")
            tmp.write_text(DEFAULT_MEMORY_HEADER, encoding="utf-8")
            tmp.rename(mem_p)
            created["memory"] = True
        # focus / heartbeat
        if not self._path(agent_id, "focus").exists():
            self.write_file(agent_id, "focus", DEFAULT_FOCUS_MD)
            created["focus"] = True
        if not self._path(agent_id, "heartbeat").exists():
            self.write_file(agent_id, "heartbeat", DEFAULT_HEARTBEAT_MD)
            created["heartbeat"] = True
        return created

    def reset_heartbeat(self, agent_id: str) -> Dict[str, Any]:
        return self.write_file(agent_id, "heartbeat", DEFAULT_HEARTBEAT_MD)

    # ── memory append-only (EA-3) ─────────────────────────

    def append_memory(self, agent_id: str, entry: str, source: str = "system") -> Dict[str, Any]:
        if not entry or not entry.strip():
            return {"ok": False, "error": "empty_entry"}
        entry = entry.strip()
        if len(entry) > MEMORY_ENTRY_MAX:
            entry = entry[:MEMORY_ENTRY_MAX] + "\n…(截断)"
        p = self._path(agent_id, "memory")
        if not p.exists():
            self.ensure_defaults(agent_id)
        ts = datetime.now(timezone.utc).isoformat()
        with p.open("a", encoding="utf-8") as f:
            f.write(f"\n## {ts} · {source}\n{entry}\n")
        count = p.read_text(encoding="utf-8").count("\n## ")
        return {"ok": True, "entries": count}

    # ── focus 解析 (EA-2) ─────────────────────────────────

    def parse_focus_items(self, agent_id: str) -> List[Dict[str, Any]]:
        content = self.read_file(agent_id, "focus")["content"]
        return parse_focus_content(content)

    def focus_item_exists(self, agent_id: str, text: str) -> bool:
        text = (text or "").strip()
        if not text:
            return False
        return any(i["text"] == text for i in self.parse_focus_items(agent_id))


def parse_focus_content(content: str) -> List[Dict[str, Any]]:
    """解析 `- [ ] / - [x]` checklist (EA-2)."""
    items = []
    for line in (content or "").splitlines():
        m = re.match(r"^\s*-\s*\[([ xX])\]\s*(.+?)\s*$", line)
        if m:
            items.append({"text": m.group(2), "done": m.group(1).lower() == "x"})
    return items


# ── EA-5: 组织上下文构建器 ──────────────────────────────────

def build_organizational_context(team_id: str, agent_id: str,
                                 store: Optional[EmployeeProfileStore] = None) -> Dict[str, Any]:
    """组织上下文 = soul + focus + relationships + 团队共享认知 (Clawith Organizational Context)."""
    store = store or get_employee_store()
    sections: Dict[str, str] = {}

    soul = store.read_file(agent_id, "soul")
    sections["soul"] = soul["content"] if soul["exists"] else "（暂无灵魂档案）"
    focus = store.read_file(agent_id, "focus")
    sections["focus"] = focus["content"] if focus["exists"] else "（暂无聚焦清单）"

    # relationships.md (EC-5)
    try:
        from .agent_relationships import render_relationships_md
        sections["relationships"] = render_relationships_md(team_id, agent_id)
    except Exception as e:
        sections["relationships"] = f"（关系网络不可用: {e}）"

    # 团队共享认知
    team_ctx = "（团队信息不可用）"
    try:
        from .api import _tm
        team = _tm().get_team(team_id)
        if team:
            roster = []
            agents_list = team.agents
            if isinstance(agents_list, dict):
                agents_list = list(agents_list.values())
            for a in agents_list[:20]:
                roster.append(f"- {getattr(a, 'name', '?')}（{getattr(a, 'role', '?')}）")
            skills_idx = []
            try:
                from .skill_library import get_skill_library
                for s in get_skill_library().browse(team_id=team_id)[:10]:
                    skills_idx.append(f"- {s.get('name', '?')}")
            except Exception:
                pass
            team_ctx = (f"团队：{team.name}\n说明：{team.description or '—'}\n\n"
                        f"队友名册：\n" + ("\n".join(roster) or "（空）"))
            if skills_idx:
                team_ctx += "\n\n共享技能索引（前10）：\n" + "\n".join(skills_idx)
    except Exception as e:
        team_ctx = f"（团队信息不可用: {e}）"
    sections["team_context"] = team_ctx

    system_prefix = (
        f"# 组织上下文\n\n## 灵魂锚定\n{sections['soul']}\n\n"
        f"## 当前聚焦（唤醒后第一反应：检查这里）\n{sections['focus']}\n\n"
        f"## 我能联系谁\n{sections['relationships']}\n\n"
        f"## 团队共享认知\n{sections['team_context']}\n"
    )
    if len(system_prefix) > CONTEXT_MAX_CHARS:
        system_prefix = system_prefix[:CONTEXT_MAX_CHARS] + "\n…(组织上下文截断)"
    return {"system_prefix": system_prefix, "sections": sections,
            "team_id": team_id, "agent_id": agent_id}


# ── ED-2/ED-3: 治理校验器 ───────────────────────────────────

def check_action_allowed(profile: Any, action_risk: int) -> Dict[str, Any]:
    """L1-L4 自主边界判定 (ED-2).

    level=L, risk=R (均 1-4):
      L4 → 全放行
      R <= L      → 放行
      R == L + 1  → 需人工审批
      R >  L + 1  → 拒绝
    """
    level = int(getattr(profile, "autonomy_level", None)
                or (profile.get("autonomy_level", 2) if isinstance(profile, dict) else 2) or 2)
    risk = max(1, min(4, int(action_risk)))
    if level >= 4:
        return {"allowed": True, "needs_approval": False, "reason": "L4 全自主"}
    if risk <= level:
        return {"allowed": True, "needs_approval": False,
                "reason": f"risk{risk} <= L{level}"}
    if risk == level + 1:
        return {"allowed": False, "needs_approval": True,
                "reason": f"risk{risk} 超出 L{level} 一级，需人工审批"}
    return {"allowed": False, "needs_approval": False,
            "reason": f"risk{risk} 远超 L{level}，拒绝"}


def check_token_budget(profile: Any, usage_store=None) -> Dict[str, Any]:
    """日 Token 预算校验 (ED-3)，联 budget.UsageStore."""
    if isinstance(profile, dict):
        budget = int(profile.get("token_budget", 0) or 0)
        agent_id = profile.get("agent_id", "")
    else:
        budget = int(getattr(profile, "token_budget", 0) or 0)
        agent_id = getattr(profile, "agent_id", "")
    if budget <= 0:
        return {"within": True, "used_today": 0, "budget": 0, "note": "未设预算（不限）"}
    used = 0
    quality = "measured"
    try:
        if usage_store is None:
            from .budget.store import get_usage_store
            usage_store = get_usage_store()
        today = datetime.now(timezone.utc).date().isoformat()
        used = int(usage_store.get_agent_daily_total(agent_id, today) or 0)
    except Exception as e:
        logger.debug(f"UsageStore 不可用，预算校验降级放行: {e}")
        return {"within": True, "used_today": 0, "budget": budget, "data_quality": "unknown"}
    return {"within": used < budget, "used_today": used, "budget": budget,
            "data_quality": quality}


# ── 单例 ──────────────────────────────────────────────────

_store: Optional[EmployeeProfileStore] = None


def get_employee_store() -> EmployeeProfileStore:
    global _store
    if _store is None:
        _store = EmployeeProfileStore()
    return _store


def reset_employee_store(**kwargs) -> EmployeeProfileStore:
    global _store
    _store = EmployeeProfileStore(**kwargs)
    return _store
