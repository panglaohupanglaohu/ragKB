# -*- coding: utf-8 -*-
"""ExecutionPlan — Plaza 集体智慧的结构化产出契约 (Todos P5-1) + 落地性审查 (P6-2).

两阶段经济学的分界物:
- 讨论阶段产出本结构（不计成本，只求落地）；
- 本结构经人批准(approve)后进入执行阶段（派发/孪生竞标/生产），成本纪律从此开始。

每个步骤必须具备: 标题、负责角色、预期产出(验收依据)；依赖必须可解析。
审查不过 → 不允许派发（除非显式 force）。
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

# ── 计划文本解析（自 plaza_routes 迁移，成为唯一实现） ──────────

_PRIORITY_MAP = {"P0": 1, "P1": 1, "P2": 2, "P3": 3, "1": 1, "2": 2, "3": 3}

_GARBAGE_TITLE_PATTERNS = [
    re.compile(r"^```"),
    re.compile(r"我的定位[:：]"),
    re.compile(r"你是议事长"),
    re.compile(r"^⚠️"),
    re.compile(r"^💡"),
    re.compile(r"我是 AgentsGroup"),
    re.compile(r"当前系统功能正常"),
    re.compile(r"^[#]{1,6}\s"),
    re.compile(r"[{}]"),
    re.compile(r"Authentication\s+Fails"),
    re.compile(r"api key"),
    re.compile(r"^{.*}$"),
]


def is_valid_task_title(title: str) -> bool:
    """检查任务标题是否为有效的人类任务描述，排除代码块/系统提示/错误等."""
    if not title or len(title.strip()) < 3:
        return False
    if len(title) > 150:
        return False
    t = title.strip()
    for pattern in _GARBAGE_TITLE_PATTERNS:
        if pattern.search(t):
            return False
    return True


def parse_plan_table(plan_text: str) -> List[Dict[str, Any]]:
    """从 markdown 表格或列表格式中提取任务项.

    只接受结构化格式（表格/列表），拒绝按行分割兜底。
    返回空列表时，调用方应回退到 LLM 拆解或单任务兜底。
    """
    tasks: List[Dict[str, Any]] = []

    # ── 策略 1: Markdown 表格 ──
    table_lines = [
        line.strip()
        for line in plan_text.splitlines()
        if line.strip().startswith("|") and line.strip().endswith("|")
    ]
    if len(table_lines) >= 3:
        header_cells = [cell.strip() for cell in table_lines[0].strip("|").split("|")]
        if any("任务" in cell for cell in header_cells):
            for row_line in table_lines[2:]:
                cells = [cell.strip() for cell in row_line.strip("|").split("|")]
                if len(cells) < 6:
                    continue
                if not cells[0] or re.fullmatch(r"-{3,}", cells[0].replace(" ", "")):
                    continue
                title = cells[1]
                responsible = cells[2]
                priority = cells[3]
                dependencies = cells[4]
                expected_artifact = cells[5]
                if not is_valid_task_title(title):
                    continue
                description = "\n".join(
                    line for line in [
                        f"负责角色: {responsible}" if responsible else "",
                        f"依赖: {dependencies}" if dependencies and dependencies != "-" else "",
                        f"预期产出: {expected_artifact}" if expected_artifact else "",
                    ] if line
                )
                tasks.append({
                    "title": title,
                    "description": description or title,
                    "priority": _PRIORITY_MAP.get(priority.strip(), 2),
                    "responsible": responsible,
                    "dependencies": dependencies,
                    "expected_artifact": expected_artifact,
                })
            if tasks:
                return tasks

    # ── 策略 2: 列表格式 ( - 标题: 描述 ) ──
    list_items = re.findall(r'[-*]\s+(.+?)[:：]\s*(.+)', plan_text)
    if list_items:
        for title, desc in list_items:
            clean_title = title.strip()
            if not is_valid_task_title(clean_title):
                continue
            tasks.append({
                "title": clean_title,
                "description": desc.strip(),
                "priority": 2,
                "responsible": "",
                "dependencies": "",
                "expected_artifact": "",
            })
        if tasks:
            return tasks

    return []


# ── 结构化契约 ─────────────────────────────────────────────

STEP_STATUSES = ("pending", "dispatched", "completed", "failed")
PLAN_STATUSES = ("draft", "approved", "dispatched", "completed")


@dataclass
class PlanStep:
    """执行计划的一个步骤 — 派发后 1 步骤 ↔ 1 任务."""

    step_id: str = ""
    index: int = 0
    title: str = ""
    description: str = ""
    responsible_role: str = ""
    acceptance: str = ""            # 验收依据 = 预期产出
    dependencies: List[str] = field(default_factory=list)   # 引用其他 step 的序号/标题
    required_skills: List[str] = field(default_factory=list)
    priority: int = 2
    status: str = "pending"
    task_id: str = ""               # 派发后回填

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_id": self.step_id, "index": self.index, "title": self.title,
            "description": self.description, "responsible_role": self.responsible_role,
            "acceptance": self.acceptance, "dependencies": list(self.dependencies),
            "required_skills": list(self.required_skills), "priority": self.priority,
            "status": self.status, "task_id": self.task_id,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "PlanStep":
        return cls(
            step_id=d.get("step_id", ""), index=int(d.get("index", 0)),
            title=d.get("title", ""), description=d.get("description", ""),
            responsible_role=d.get("responsible_role", ""),
            acceptance=d.get("acceptance", ""),
            dependencies=list(d.get("dependencies", [])),
            required_skills=list(d.get("required_skills", [])),
            priority=int(d.get("priority", 2)),
            status=d.get("status", "pending"), task_id=d.get("task_id", ""),
        )


@dataclass
class ExecutionPlan:
    """Plaza 讨论收敛出的结构化执行计划."""

    plan_id: str = ""
    plaza_id: str = ""
    discussion_id: str = ""
    topic: str = ""
    goal: str = ""
    revision: int = 1
    status: str = "draft"
    approved_by: str = ""
    steps: List[PlanStep] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self) -> None:
        if not self.plan_id:
            self.plan_id = f"plan-{uuid.uuid4().hex[:8]}"
        now = datetime.now(timezone.utc).isoformat()
        if not self.created_at:
            self.created_at = now
        if not self.updated_at:
            self.updated_at = now

    def touch(self) -> None:
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def get_step(self, step_id: str) -> Optional[PlanStep]:
        for s in self.steps:
            if s.step_id == step_id:
                return s
        return None

    def refresh_status(self) -> None:
        """步骤状态汇总 → 计划状态（全完成→completed）."""
        if not self.steps:
            return
        if all(s.status == "completed" for s in self.steps):
            self.status = "completed"
        elif any(s.status in ("dispatched", "completed", "failed") for s in self.steps):
            if self.status in ("approved", "dispatched"):
                self.status = "dispatched"
        self.touch()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plan_id": self.plan_id, "plaza_id": self.plaza_id,
            "discussion_id": self.discussion_id, "topic": self.topic,
            "goal": self.goal, "revision": self.revision, "status": self.status,
            "approved_by": self.approved_by,
            "steps": [s.to_dict() for s in self.steps],
            "created_at": self.created_at, "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ExecutionPlan":
        plan = cls(
            plan_id=d.get("plan_id", ""), plaza_id=d.get("plaza_id", ""),
            discussion_id=d.get("discussion_id", ""), topic=d.get("topic", ""),
            goal=d.get("goal", ""), revision=int(d.get("revision", 1)),
            status=d.get("status", "draft"), approved_by=d.get("approved_by", ""),
            created_at=d.get("created_at", ""), updated_at=d.get("updated_at", ""),
        )
        plan.steps = [PlanStep.from_dict(s) for s in d.get("steps", [])]
        return plan


def build_plan_from_text(
    plan_text: str,
    *,
    plaza_id: str = "",
    discussion_id: str = "",
    topic: str = "",
    goal: str = "",
    revision: int = 1,
) -> ExecutionPlan:
    """把议事长的计划文本编译为结构化 ExecutionPlan."""
    items = parse_plan_table(plan_text or "")
    plan = ExecutionPlan(
        plaza_id=plaza_id, discussion_id=discussion_id,
        topic=topic, goal=goal, revision=revision,
    )
    for i, item in enumerate(items):
        deps_raw = str(item.get("dependencies", "") or "")
        deps = [
            d.strip() for d in re.split(r"[,，、;；\s]+", deps_raw)
            if d.strip() and d.strip() not in ("-", "无", "none", "None")
        ]
        plan.steps.append(PlanStep(
            step_id=f"{plan.plan_id}-s{i + 1}",
            index=i + 1,
            title=item.get("title", ""),
            description=item.get("description", ""),
            responsible_role=item.get("responsible", ""),
            acceptance=item.get("expected_artifact", ""),
            dependencies=deps,
            priority=int(item.get("priority", 2)),
        ))
    return plan


# ── P6-2: 落地性审查（可执行性关卡） ───────────────────────────


def validate_plan(plan: ExecutionPlan) -> List[Dict[str, str]]:
    """落地性审查: 返回问题清单，空列表 = 可派发.

    规则: 计划非空；每步骤必须有 标题/负责角色/验收依据(预期产出)；依赖必须能
    解析到计划内的其他步骤（按序号或标题）。
    """
    issues: List[Dict[str, str]] = []
    if not plan.steps:
        issues.append({"step_id": "", "field": "steps", "message": "计划为空：讨论尚未收敛出可执行步骤"})
        return issues
    known_refs: set = set()
    for s in plan.steps:
        known_refs.add(str(s.index))
        if s.title:
            known_refs.add(s.title)
    for s in plan.steps:
        if not is_valid_task_title(s.title):
            issues.append({"step_id": s.step_id, "field": "title",
                           "message": f"步骤{s.index} 标题无效或缺失"})
        if not s.responsible_role.strip():
            issues.append({"step_id": s.step_id, "field": "responsible_role",
                           "message": f"步骤{s.index}「{s.title[:20]}」缺少负责角色"})
        if not s.acceptance.strip():
            issues.append({"step_id": s.step_id, "field": "acceptance",
                           "message": f"步骤{s.index}「{s.title[:20]}」缺少预期产出/验收依据"})
        for dep in s.dependencies:
            if dep == str(s.index) or dep == s.title:
                issues.append({"step_id": s.step_id, "field": "dependencies",
                               "message": f"步骤{s.index} 依赖自身"})
            elif dep not in known_refs:
                issues.append({"step_id": s.step_id, "field": "dependencies",
                               "message": f"步骤{s.index} 的依赖「{dep}」无法解析到计划内步骤"})
    return issues


# ── 存取（结构化计划随讨论持久化于 disc.plan['structured']） ──────


def load_plan_from_discussion(disc: Any) -> Optional[ExecutionPlan]:
    data = (disc.plan or {}).get("structured") if getattr(disc, "plan", None) else None
    return ExecutionPlan.from_dict(data) if data else None


def save_plan_to_discussion(disc: Any, plan: ExecutionPlan) -> None:
    if not isinstance(getattr(disc, "plan", None), dict):
        disc.plan = {}
    plan.touch()
    disc.plan["structured"] = plan.to_dict()
