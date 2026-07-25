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


# 角色 → 默认技能（计划表无技能列时的推断源，v4 XG-1）
# 含 AWS 运维 / Build 域真实 skill_id，使生境 demand 能对上 agent genome（否则 skill 选择压力=0）
ROLE_DEFAULT_SKILLS: Dict[str, List[str]] = {
    "开发": ["coding", "code_review"],
    "developer": ["coding", "code_review"],
    "engineer": ["coding", "testing"],
    "工程师": ["coding", "testing"],
    "测试": ["testing", "qa"],
    "qa": ["testing", "qa"],
    "tester": ["testing", "qa"],
    "运维": ["deployment", "ops", "aws_cli_script_authoring"],
    "ops": ["deployment", "ops"],
    "sre": ["deployment", "ops", "monitoring"],
    "架构": ["architecture", "analysis", "aws_es_capacity_planning"],
    "architect": ["architecture", "analysis"],
    "产品": ["analysis", "planning"],
    "pm": ["analysis", "planning"],
    "分析": ["analysis", "research"],
    "researcher": ["analysis", "research"],
    "安全": ["security", "code_review"],
    "security": ["security", "code_review"],
    # AWS 运维团队角色
    "成本优化": ["aws_cost_finops", "analysis"],
    "成本": ["aws_cost_finops", "analysis"],
    "容量": ["aws_es_capacity_planning", "planning"],
    "上云架构": ["aws_es_capacity_planning", "architecture"],
    "运维leader": ["aws_es_scaling_orchestration", "ops"],
    "运维操作": ["aws_cli_script_authoring", "ops"],
    "巡检": ["aws_ops_monitoring", "monitoring"],
    "监控": ["aws_ops_monitoring", "monitoring"],
    "合规": ["compliance_region_guard", "security"],
    "区域合规": ["compliance_region_guard", "security"],
    # Build system
    "项目经理": ["planning", "analysis"],
    "全栈": ["coding", "code_review"],
    "技术研究": ["research", "analysis"],
}

# title/description 关键词 → 技能（最后兜底；优先匹配更长/更具体的域技能）
_SKILL_HINTS: Dict[str, List[str]] = {
    # 域 skill（与 aws-ops / build 基因组对齐）
    "aws_es_capacity_planning": ["容量", "分片", "slo", "索引", "capacity", "elasticsearch 基线", "es 当前"],
    "aws_es_scaling_orchestration": ["缩放", "伸缩", "编排", "scaling", "orchestration"],
    "aws_cli_script_authoring": ["shell", "aws-cli", "cli 脚本", "运维脚本", "脚本编写"],
    "aws_cost_finops": ["账单", "ri/", "savings", "finops", "成本", "降本"],
    "aws_ops_monitoring": ["cloudwatch", "opensearch", "指标门禁", "故障处理", "监控"],
    "compliance_region_guard": ["合规", "区域", "region", "北美", "部署限制"],
    "terraform": ["terraform", "基础设施", "iac"],
    "coding": ["代码", "开发", "实现", "编程", "code", "implement", "develop"],
    "code_review": ["审查", "评审", "review", "彩排回滚", "单步变更"],
    "testing": ["测试", "test", "qa", "单测"],
    "deployment": ["部署", "发布", "deploy", "上线"],
    "analysis": ["分析", "调研", "research", "评估"],
    "ops": ["运维", "ops"],
    "security": ["安全", "security", "漏洞"],
    "planning": ["规划", "计划", "拆解", "plan"],
    "monitoring": ["监控", "monitor", "巡检"],
}


def _parse_skills_cell(raw: str) -> List[str]:
    """解析技能单元格：逗号/顿号/斜杠分隔."""
    if not raw or raw.strip() in ("-", "无", "none", "None", "—", "–"):
        return []
    parts = re.split(r"[,，、;/|]+", raw)
    return [p.strip() for p in parts if p.strip()]


def _header_index(headers: List[str], *needles: str) -> Optional[int]:
    for i, h in enumerate(headers):
        hl = h.lower()
        for n in needles:
            if n.lower() in hl or n in h:
                return i
    return None


def infer_skills_for_step(
    *,
    title: str = "",
    description: str = "",
    responsible_role: str = "",
    explicit: Optional[List[str]] = None,
) -> tuple[List[str], bool]:
    """返回 (skills, inferred). explicit 非空则 inferred=False."""
    if explicit:
        return list(explicit), False
    role = (responsible_role or "").strip().lower()
    if role:
        for key, skills in ROLE_DEFAULT_SKILLS.items():
            kl = key.lower()
            if kl in role or role in kl:
                return list(skills), True
    blob = f"{title} {description}".lower()
    found: List[str] = []
    for skill, kws in _SKILL_HINTS.items():
        if any(kw.lower() in blob for kw in kws):
            if skill not in found:
                found.append(skill)
    if found:
        return found, True
    return ["generic"], True


def parse_plan_table(plan_text: str) -> List[Dict[str, Any]]:
    """从 markdown 表格或列表格式中提取任务项.

    只接受结构化格式（表格/列表），拒绝按行分割兜底。
    返回空列表时，调用方应回退到 LLM 拆解或单任务兜底。
    支持可选「所需技能/技能」列（v4 XG-1）。
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
            # 兼容固定 6 列布局 + 按表头定位
            idx_title = _header_index(header_cells, "任务", "title") or 1
            idx_resp = _header_index(header_cells, "负责", "角色", "responsible") or 2
            idx_pri = _header_index(header_cells, "优先级", "priority") or 3
            idx_dep = _header_index(header_cells, "依赖", "depend") or 4
            idx_art = _header_index(header_cells, "预期", "产出", "验收", "artifact") or 5
            idx_sk = _header_index(header_cells, "技能", "skill", "所需技能")
            for row_line in table_lines[2:]:
                cells = [cell.strip() for cell in row_line.strip("|").split("|")]
                if len(cells) < 6:
                    continue
                if not cells[0] or re.fullmatch(r"-{3,}", cells[0].replace(" ", "")):
                    continue
                title = cells[idx_title] if idx_title < len(cells) else cells[1]
                responsible = cells[idx_resp] if idx_resp < len(cells) else cells[2]
                priority = cells[idx_pri] if idx_pri < len(cells) else cells[3]
                dependencies = cells[idx_dep] if idx_dep < len(cells) else cells[4]
                expected_artifact = cells[idx_art] if idx_art < len(cells) else cells[5]
                skills_raw = cells[idx_sk] if idx_sk is not None and idx_sk < len(cells) else ""
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
                    "required_skills": _parse_skills_cell(skills_raw),
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
                "required_skills": [],
            })
        if tasks:
            return tasks

    return []


# ── 结构化契约 ─────────────────────────────────────────────

STEP_STATUSES = ("pending", "dispatched", "completed", "failed")
PLAN_STATUSES = ("draft", "approved", "dispatched", "completed")


@dataclass
class PlanStep:
    """执行计划的一个步骤 — 派发后 1 步骤 ↔ 1 任务（多队时 1 步骤 ↔ 多任务）."""

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
    task_id: str = ""               # 派发后回填（主队/primary）
    # 多队并行：team_id → task_id
    task_ids_by_team: Dict[str, str] = field(default_factory=dict)
    dispatch_group_id: str = ""

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "step_id": self.step_id, "index": self.index, "title": self.title,
            "description": self.description, "responsible_role": self.responsible_role,
            "acceptance": self.acceptance, "dependencies": list(self.dependencies),
            "required_skills": list(self.required_skills), "priority": self.priority,
            "status": self.status, "task_id": self.task_id,
        }
        if self.task_ids_by_team:
            d["task_ids_by_team"] = dict(self.task_ids_by_team)
        if self.dispatch_group_id:
            d["dispatch_group_id"] = self.dispatch_group_id
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "PlanStep":
        by_team = d.get("task_ids_by_team") or {}
        if not isinstance(by_team, dict):
            by_team = {}
        return cls(
            step_id=d.get("step_id", ""), index=int(d.get("index", 0)),
            title=d.get("title", ""), description=d.get("description", ""),
            responsible_role=d.get("responsible_role", ""),
            acceptance=d.get("acceptance", ""),
            dependencies=list(d.get("dependencies", [])),
            required_skills=list(d.get("required_skills", [])),
            priority=int(d.get("priority", 2)),
            status=d.get("status", "pending"), task_id=d.get("task_id", ""),
            task_ids_by_team={str(k): str(v) for k, v in by_team.items() if k and v},
            dispatch_group_id=str(d.get("dispatch_group_id") or ""),
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
        explicit = list(item.get("required_skills") or [])
        skills, _inferred = infer_skills_for_step(
            title=item.get("title", ""),
            description=item.get("description", ""),
            responsible_role=item.get("responsible", ""),
            explicit=explicit or None,
        )
        plan.steps.append(PlanStep(
            step_id=f"{plan.plan_id}-s{i + 1}",
            index=i + 1,
            title=item.get("title", ""),
            description=item.get("description", ""),
            responsible_role=item.get("responsible", ""),
            acceptance=item.get("expected_artifact", ""),
            dependencies=deps,
            required_skills=skills,
            priority=int(item.get("priority", 2)),
        ))
    return plan


# ── P6-2: 落地性审查（可执行性关卡） ───────────────────────────


def validate_plan(plan: ExecutionPlan, profile: str = "dispatch") -> List[Dict[str, str]]:
    """落地性审查（唯一实现，禁止另起炉灶）: 返回问题清单，空列表 = 通过.

    基础规则（所有 profile）: 计划非空；每步骤必须有 标题/负责角色/验收依据(预期产出)；
    依赖必须能解析到计划内的其他步骤（按序号或标题）且不得自依赖。
    profile='dispatch': 生产派发关卡（approve/dispatch 使用）。
    profile='twin':     进孪生演练关卡——在基础规则上叠加「每步骤必须声明所需技能」
                        （孪生按技能生成任务流，无技能无法仿真执行）。
    profile='eco':      物竞天择任务生境关卡——每步至少 1 个技能（可为推断的 generic 以外的技能；
                        仅 generic 时给出 warning 级 issue，message 含 inferred）。
    """
    issues: List[Dict[str, str]] = []
    if not plan.steps:
        issues.append({"step_id": "", "field": "steps", "message": "计划为空：讨论尚未收敛出可执行步骤"})
        return issues
    known_titles = {s.title for s in plan.steps if s.title}
    known_indexes = {str(s.index) for s in plan.steps}

    def _dep_index(dep: str) -> Optional[str]:
        """依赖引用归一: 支持 裸序号/步骤N/stepN/sN（与编译器同口径）。"""
        m = re.fullmatch(r"(?:步骤|step|s)?\s*0*(\d+)", dep.strip(), re.IGNORECASE)
        return m.group(1) if m else None

    def _dep_resolves(dep: str) -> bool:
        if dep in known_titles:
            return True
        idx = _dep_index(dep)
        return idx is not None and idx in known_indexes
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
            if _dep_index(dep) == str(s.index) or dep == s.title:
                issues.append({"step_id": s.step_id, "field": "dependencies",
                               "message": f"步骤{s.index} 依赖自身"})
            elif not _dep_resolves(dep):
                issues.append({"step_id": s.step_id, "field": "dependencies",
                               "message": f"步骤{s.index} 的依赖「{dep}」无法解析到计划内步骤"})
        if profile == "twin" and not (s.required_skills or []):
            issues.append({"step_id": s.step_id, "field": "required_skills",
                           "message": f"步骤{s.index}「{s.title[:20]}」缺所需技能（孪生按技能仿真执行）"})
        if profile == "eco":
            skills = list(s.required_skills or [])
            if not skills:
                issues.append({"step_id": s.step_id, "field": "required_skills",
                               "message": f"步骤{s.index}「{s.title[:20]}」缺所需技能（物竞生境按技能选择）"})
            elif skills == ["generic"]:
                issues.append({"step_id": s.step_id, "field": "required_skills",
                               "message": f"步骤{s.index}「{s.title[:20]}」技能仅为 generic（inferred 兜底，建议补充真实技能）"})
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
