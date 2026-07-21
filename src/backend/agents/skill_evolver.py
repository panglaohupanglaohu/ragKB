# -*- coding: utf-8 -*-
"""技能演化引擎 — Evidence→Attribution→Evolution.

对应 SkillClaw: evolve_skill / merge_skills / create_from_sessions.
触发模式: 自动建议 + 人工确认（不自动执行）。
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from .models import SkillDefinition, SkillLifecycleStage

logger = logging.getLogger(__name__)


class SkillEvolver:
    """技能演化引擎 — 收集证据 → LLM改进 → 版本递增."""

    def __init__(self, skill_library=None, chat_harness=None):
        self._skill_library = skill_library
        self._chat_harness = chat_harness

    @staticmethod
    def _is_unusable_evolution_text(text: str) -> bool:
        lowered = (text or "").lower()
        return any(
            marker in lowered
            for marker in (
                "当前 llm 未连接",
                "llm 未连接",
                "authentication fails",
                "api key",
                "invalid_api_key",
                "export deepseek_api_key",
                "我是 agentsgroup2026 智能体",
            )
        )

    def _resolve_live_provider_config(self):
        """每次演化前从 settings + secret store 拉最新 Key，避免 harness 内存里残留旧密钥.

        测试连接成功后会写 settings/secret，但若进程内 _default_config / global_override
        仍是旧 Key，演化会继续失败。此处优先：global_override(有 key) → settings 新鲜配置。
        """
        from .chat_harness import ProviderConfig, get_chat_harness
        import json
        import os

        harness = self._chat_harness or get_chat_harness()
        try:
            ov = harness.get_global_override() if harness else None
        except Exception:
            ov = None

        # 读盘最新 settings
        fresh = None
        try:
            root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
            path = os.path.join(root, "config", "settings.json")
            if not os.path.isfile(path):
                path = os.path.join(os.getcwd(), "config", "settings.json")
            with open(path, "r", encoding="utf-8") as f:
                settings = json.load(f)
            fresh = ProviderConfig.from_settings(settings)
        except Exception as e:
            logger.debug("load settings for evolve failed: %s", e)

        # 若 override 的 key 与磁盘一致或磁盘无 key，用 override；若磁盘 key 更新则用磁盘
        if ov and ov.api_key:
            if not fresh or not fresh.api_key or ov.api_key == fresh.api_key:
                return ov
            # 磁盘 key 与 override 不同 → 刷新 override 用新 key
            try:
                harness.set_global_override(fresh, getattr(harness, "_global_override_meta", None) or {
                    "name": fresh.model, "source": "evolve_refresh",
                })
            except Exception:
                pass
            return fresh

        if fresh and fresh.api_key:
            try:
                harness.update_default_provider(
                    provider=fresh.provider.value if hasattr(fresh.provider, "value") else str(fresh.provider),
                    api_key=fresh.api_key,
                    api_base_url=fresh.api_base_url or "",
                    model=fresh.model or "",
                )
            except Exception:
                pass
            return fresh

        return harness.get_provider_config() if harness else None

    @staticmethod
    def _deterministic_improvement(skill: SkillDefinition) -> str:
        text = " ".join([skill.name, skill.description, skill.instructions, skill.slug]).lower()
        if any(kw in text for kw in ("ri", "reserved instance", "savings plan", "成本", "账单", "finops")):
            return (
                "当问题出现 RI、Reserved Instance、预留实例、Savings Plan 或成本治理时，"
                "先把 RI 明确解释为 AWS Reserved Instance，不切换到编程/数据库/需求工程语境。"
                "执行步骤：1) 拉取 30/60/90 天实例族、区域、规格、运行小时、CPU/内存/IO 与账单基线；"
                "2) 区分稳定负载与波动负载，稳定负载评估 RI，弹性负载评估 Savings Plan、按需或 Spot；"
                "3) 计算覆盖率、利用率、预付方式、承诺期限、到期续约和现金流影响；"
                "4) 对 OpenSearch/ElasticSearch 扩容同时估算实例、存储、跨 AZ 流量、快照、监控和数据迁移成本；"
                "5) 设置 Cost Gate，覆盖率不足、利用率过低、预算超阈值或北美合规缺失时阻断采购；"
                "6) 输出购买建议、风险、回滚/调整策略，并把治理目标写回任务、议事厅或系统演进项。"
            )
        base = (skill.instructions or skill.description or skill.name or "").strip()
        return (
            f"{base}\n\n"
            "使用该技能时必须先确认业务场景、输入证据、验收标准和失败回退方式；"
            "回答要包含可执行步骤、风险、验证指标和后续演进建议。"
        ).strip()

    # ── Evolve: 证据 → 约束生成 → 人审草稿 ───────────────────────

    def _gather_evidence(
        self,
        skill: SkillDefinition,
        evidence_sessions: Optional[List[str]] = None,
        user_feedback: Optional[str] = None,
    ) -> Dict[str, Any]:
        """最小证据包：技能字段 + 反馈 + 会话 id（不做全量重放）。"""
        sessions = list(evidence_sessions or getattr(skill, "evidence_sessions", None) or [])
        return {
            "name": skill.name or "",
            "description": skill.description or "",
            "category": getattr(skill.category, "value", None) or str(skill.category or "general"),
            "instructions": skill.instructions or "",
            "usage_count": int(getattr(skill, "usage_count", 0) or 0),
            "effectiveness": float(getattr(skill, "effectiveness", 0) or 0),
            "version": int(getattr(skill, "version", 1) or 1),
            "evidence_sessions": sessions[:20],
            "user_feedback": (user_feedback or "").strip(),
            "language_hint": self._instruction_language_hint(skill.instructions or skill.name or ""),
            "language_code": self._detect_language_code(skill.instructions or skill.name or ""),
        }

    @staticmethod
    def _parse_evolution_json(raw: str) -> Optional[Dict[str, Any]]:
        """Extract evolution JSON object from model output (fences / trailing prose OK)."""
        if not raw or not str(raw).strip():
            return None
        text = str(raw).strip()
        m = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
        if m:
            text = m.group(1).strip()
        # direct parse
        for candidate in (text,):
            try:
                obj = json.loads(candidate)
                if isinstance(obj, dict) and (
                    obj.get("improved_instructions") or obj.get("instructions")
                ):
                    return obj
            except json.JSONDecodeError:
                pass
        # first { ... } span
        m2 = re.search(r"\{[\s\S]*\}", text)
        if m2:
            try:
                obj = json.loads(m2.group(0))
                if isinstance(obj, dict) and (
                    obj.get("improved_instructions") or obj.get("instructions")
                ):
                    return obj
            except json.JSONDecodeError:
                return None
        return None

    def _normalize_draft(self, skill: SkillDefinition, draft: Dict[str, Any]) -> Dict[str, Any]:
        instr = str(
            draft.get("improved_instructions")
            or draft.get("instructions")
            or ""
        ).strip()
        # 语言/格式要求只约束生成过程，禁止写进 skill 正文
        instr = self._strip_generation_meta_from_instructions(instr)
        changelog = draft.get("changelog") or draft.get("changes") or []
        if isinstance(changelog, str):
            changelog = [changelog] if changelog.strip() else []
        if not isinstance(changelog, list):
            changelog = []
        changelog = [str(x).strip() for x in changelog if str(x).strip()][:12]
        lang = str(draft.get("language") or self._detect_language_code(skill.instructions or "")).lower()
        if lang not in ("zh", "en", "mixed"):
            lang = self._detect_language_code(skill.instructions or "")
        return {
            "language": lang,
            "improved_instructions": instr,
            "changelog": changelog,
            "preserved_intent": str(draft.get("preserved_intent") or draft.get("intent") or "")[:300],
            "risks": [
                str(x).strip()
                for x in (draft.get("risks") or [])
                if str(x).strip()
            ][:8] if isinstance(draft.get("risks"), list) else [],
        }

    @staticmethod
    def _strip_generation_meta_from_instructions(text: str) -> str:
        """Remove LLM-leaked generation constraints from skill body.

        「语言：中文」「【要求】」等是演化引擎对模型的输出约束，不是 skill 业务指令。
        """
        if not (text or "").strip():
            return text or ""
        lines = text.replace("\r\n", "\n").split("\n")
        meta_line = re.compile(
            r"^\s*("
            r"【\s*要求\s*】|"
            r"【\s*语言\s*】|"
            r"输出语言|"
            r"语言\s*要求|"
            r"语言\s*[：:]|"
            r"Language\s*[：:]|"
            r"Output\s*language|"
            r"请用中文|"
            r"必须用中文|"
            r"用中文写|"
            r"主体语言|"
            r"硬约束|"
            r"与原文.*语言|"
            r"术语可保留|"
            r"专有名词.*缩写"
            r")",
            re.IGNORECASE,
        )
        # Drop leading meta block (title + bullets about language)
        out: List[str] = []
        i = 0
        # strip leading empty
        while i < len(lines) and not lines[i].strip():
            i += 1
        # if starts with 【要求】 or similar, skip until blank line after meta bullets
        if i < len(lines) and meta_line.search(lines[i].strip() or lines[i]):
            i += 1
            while i < len(lines):
                s = lines[i].strip()
                if not s:
                    i += 1
                    break
                if meta_line.search(s) or s.startswith("-") or s.startswith("•") or s.startswith("*"):
                    # still meta-ish bullet
                    if meta_line.search(s) or re.search(
                        r"语言|Language|中文|English|缩写|SOP/Agent", s, re.I
                    ):
                        i += 1
                        continue
                break
        while i < len(lines):
            s = lines[i]
            if meta_line.search(s.strip()):
                i += 1
                continue
            # lone "语言：中文（术语可保留…）" mid-doc
            if re.match(r"^\s*[-*•]?\s*语言\s*[：:]", s) and re.search(
                r"中文|English|英文|缩写", s
            ):
                i += 1
                continue
            out.append(s)
            i += 1
        cleaned = "\n".join(out).strip()
        # collapse excessive leading blank
        return cleaned

    # 单次演化最多 2 次 LLM；单次超时默认 60s（勿用 harness 默认 1200s）
    EVOLVE_LLM_TIMEOUT_SEC = float(os.environ.get("AG_EVOLVE_TIMEOUT", "60") or "60")
    EVOLVE_MAX_LLM_CALLS = 2

    async def _llm_chat_raw(
        self,
        *,
        prompt: str,
        system_prompt: str,
        live_cfg,
        call_budget: Optional[List[int]] = None,
    ) -> Tuple[str, str]:
        """Returns (response_text, error_text).

        - 每次演化用独立 session_id，避免 __skill_evolver__ 会话无限堆积拖死
        - asyncio 超时（默认 60s）
        - call_budget: 可变 list[int] 共享计数，耗尽则拒绝再调
        """
        if call_budget is not None:
            if call_budget[0] <= 0:
                return "", "evolve_llm_budget_exhausted"
            call_budget[0] -= 1

        if not self._chat_harness:
            from .chat_harness import get_chat_harness
            self._chat_harness = get_chat_harness()
        if not self._chat_harness:
            return "", "LLM 服务未初始化"
        # 独立会话：禁止复用 agent 级 history（那是「没完没了」的主因）
        sid = f"evolve-{uuid4().hex[:12]}"
        timeout = max(15.0, float(self.EVOLVE_LLM_TIMEOUT_SEC))
        try:
            result = await asyncio.wait_for(
                self._chat_harness.chat(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    agent_id="__skill_evolver__",
                    session_id=sid,
                    config_override=live_cfg,
                    model_override=getattr(live_cfg, "model", "") or "",
                ),
                timeout=timeout,
            )
            err = (getattr(result, "error", None) or "").strip()
            text = (getattr(result, "response", None) or "").strip() if result else ""
            return text, err
        except asyncio.TimeoutError:
            logger.error("LLM evolve timed out after %.0fs", timeout)
            return "", f"演化 LLM 超时（>{timeout:.0f}s），请重试或检查模型连通性"
        except Exception as e:
            logger.error("LLM evolve call failed: %s", e)
            return "", f"{type(e).__name__}: {e}"

    async def _generate_evolution_draft(
        self,
        skill: SkillDefinition,
        evidence: Dict[str, Any],
        live_cfg,
        call_budget: Optional[List[int]] = None,
    ) -> Dict[str, Any]:
        """Call LLM for structured evolution JSON; at most one schema retry (shared budget)."""
        lang_hint = evidence.get("language_hint") or "与原文相同语言"
        lang_code = evidence.get("language_code") or "zh"
        feedback = evidence.get("user_feedback") or ""
        sessions = evidence.get("evidence_sessions") or []
        budget = call_budget if call_budget is not None else [self.EVOLVE_MAX_LLM_CALLS]

        user_parts = [
            "请根据证据改进技能指令，并只输出一个 JSON 对象（不要 markdown 围栏外的解释）。",
            "",
            "【仅针对你这次回答的约束——不要写进 improved_instructions 正文】",
            f"- JSON 字段 language 填: {lang_code}",
            f"- improved_instructions 用与原文相同的主体语言书写（{lang_hint}）",
            "- 禁止把中文业务指令整段改写成英文企业模板",
            "- 禁止在 improved_instructions 里出现「语言要求 / 【要求】/ Language:」这类生成器元信息",
            "- improved_instructions 只写 Agent 执行该 skill 时要用的业务步骤与规则",
            "",
            f"技能名称: {evidence.get('name')}",
            f"描述: {evidence.get('description')}",
            f"类别: {evidence.get('category')}",
            f"使用次数: {evidence.get('usage_count')}, 成功率: {float(evidence.get('effectiveness') or 0) * 100:.0f}%",
            f"当前版本: v{evidence.get('version')}",
        ]
        if sessions:
            user_parts.append(f"关联会话ID: {', '.join(str(s) for s in sessions[:10])}")
        if feedback:
            user_parts.append(f"用户反馈: {feedback}")
        # 截断超长原文，避免 prompt 过大拖慢
        orig = (evidence.get("instructions") or "(空)")[:6000]
        user_parts.extend([
            "",
            "当前指令（原文，请在此基础上改进业务内容，勿丢失核心意图）:",
            orig,
            "",
            "JSON schema（示例值勿照抄进正文）:",
            json.dumps({
                "language": lang_code,
                "improved_instructions": "<仅业务步骤与规则，不要写语言要求>",
                "changelog": ["变更要点1", "变更要点2"],
                "preserved_intent": "一句话核心意图",
                "risks": ["仍需人工关注的点（可空数组）"],
            }, ensure_ascii=False, indent=2),
        ])
        prompt = "\n".join(user_parts)

        raw, err = await self._llm_chat_raw(
            prompt=prompt,
            system_prompt=EVOLVE_SYSTEM_PROMPT,
            live_cfg=live_cfg,
            call_budget=budget,
        )
        if err:
            return {"error": "llm_error", "error_detail": err, "raw": raw}
        if self._is_unusable_evolution_text(raw):
            return {
                "error": "llm_unusable",
                "error_detail": (
                    "LLM 返回了不可用回退文本（常见：Key 无效或模型不被上游接受）。"
                    f" model={getattr(live_cfg, 'model', '')}"
                ),
                "raw": raw,
            }
        parsed = self._parse_evolution_json(raw)
        if not parsed and budget[0] > 0:
            # 仅当预算仍有余量时做一次 JSON 重试
            repair_prompt = (
                "你的上一次输出不是合法 JSON。请只输出符合 schema 的 JSON 对象，"
                f"language={lang_code}；improved_instructions 只写业务步骤，不要写语言要求。\n\n"
                f"原文指令:\n{orig[:2000]}\n\n"
                f"上一次输出:\n{(raw or '')[:1500]}"
            )
            raw2, err2 = await self._llm_chat_raw(
                prompt=repair_prompt,
                system_prompt=EVOLVE_SYSTEM_PROMPT,
                live_cfg=live_cfg,
                call_budget=budget,
            )
            if err2:
                return {"error": "llm_error", "error_detail": err2, "raw": raw2 or raw}
            if self._is_unusable_evolution_text(raw2):
                return {"error": "llm_unusable", "error_detail": "JSON 重试仍返回不可用文本", "raw": raw2}
            parsed = self._parse_evolution_json(raw2)
            raw = raw2 or raw
        if not parsed:
            return {
                "error": "parse_failed",
                "error_detail": "无法从 LLM 输出解析改进指令 JSON（已达重试上限）",
                "raw": (raw or "")[:2000],
            }
        return {"ok": True, "draft": self._normalize_draft(skill, parsed), "raw": raw}

    def _enforce_language_and_shape(
        self,
        skill: SkillDefinition,
        draft: Dict[str, Any],
        live_cfg=None,
        lang_hint: str = "",
    ) -> Dict[str, Any]:
        """Language guard without extra LLM round-trip (strip meta only).

        不再二次调 LLM「语言修复」——那是「演化没完没了」的另一主因。
        翻转则直接拒绝交付，由用户重试或手改。
        """
        original = skill.instructions or ""
        improved = draft.get("improved_instructions") or ""
        if not improved.strip():
            return {
                "error": "empty_instructions",
                "error_detail": "演化结果缺少 improved_instructions",
            }
        # 再剥一次元信息
        improved = self._strip_generation_meta_from_instructions(improved)
        draft = dict(draft)
        draft["improved_instructions"] = improved

        if self._is_unusable_evolution_text(improved):
            return {
                "error": "llm_unusable",
                "error_detail": "改进指令含不可用回退文本，已拒绝",
            }
        if self._is_language_flip(original, improved):
            return {
                "error": "language_flip",
                "error_detail": (
                    "改进稿主体语言与原文不一致（例如中文 skill 被整段英文化）。"
                    "请重试演化，或手动用中文编辑后再应用。语言要求不会写入 skill 正文。"
                ),
                "draft": draft,
            }
        return {"ok": True, "draft": draft}

    async def evolve_skill(
        self,
        team_id: str,
        skill_id: str,
        evidence_sessions: Optional[List[str]] = None,
        user_feedback: Optional[str] = None,
        provider_config=None,
    ) -> Dict[str, Any]:
        """证据收集 → 约束 JSON 生成 → 语言硬守卫 → 人审草稿（不自动写库）。"""
        if not self._skill_library:
            return {"error": "skill_library_not_initialized"}

        skill = self._skill_library._find_skill(team_id, skill_id)
        if not skill:
            return {"error": "skill_not_found"}

        evidence = self._gather_evidence(skill, evidence_sessions, user_feedback)
        base_payload = {
            "status": "evolved_draft",
            "skill_id": skill_id,
            "original_version": skill.version,
            "new_version": skill.version + 1,
            "original_instructions": skill.instructions,
            "evidence_count": len(evidence.get("evidence_sessions") or []),
            "language": evidence.get("language_code") or "zh",
            "changelog": [],
            "preserved_intent": "",
            "risks": [],
            "improved_instructions": None,
            "llm_degraded": False,
        }

        live_cfg = provider_config or self._resolve_live_provider_config()
        if not self._chat_harness:
            from .chat_harness import get_chat_harness
            self._chat_harness = get_chat_harness()

        if not self._chat_harness:
            return {
                **base_payload,
                "error": "llm_degraded",
                "error_detail": "LLM 服务未初始化，无法生成技能演化建议。请检查后端 LLM 配置。",
                "llm_degraded": True,
            }
        if not live_cfg or not getattr(live_cfg, "api_key", None):
            return {
                **base_payload,
                "error": "llm_degraded",
                "error_detail": (
                    "未找到可用 API Key。请在「模型与连接」编辑模型、测试连接成功后"
                    "点「设为全局默认」，再重试演化。"
                ),
                "llm_degraded": True,
            }

        # 共享预算：整次 evolve 最多 2 次 LLM（生成 + 可选 JSON 重试），不再做第三次语言修复
        call_budget = [int(self.EVOLVE_MAX_LLM_CALLS)]
        gen = await self._generate_evolution_draft(
            skill, evidence, live_cfg, call_budget=call_budget
        )
        if not gen.get("ok"):
            return {
                **base_payload,
                "error": "llm_degraded",
                "error_detail": gen.get("error_detail") or gen.get("error") or "演化生成失败",
                "llm_degraded": True,
                "raw_preview": (gen.get("raw") or "")[:500],
            }

        enforced = self._enforce_language_and_shape(
            skill,
            gen["draft"],
            live_cfg,
            evidence.get("language_hint") or "",
        )
        if not enforced.get("ok"):
            err_code = enforced.get("error") or "language_flip"
            # 仍返回已剥离元信息的稿，方便用户手改
            partial = (enforced.get("draft") or {}).get("improved_instructions")
            return {
                **base_payload,
                "error": err_code,
                "error_detail": enforced.get("error_detail") or "语言校验失败",
                "llm_degraded": err_code in ("llm_unusable", "empty_instructions"),
                "improved_instructions": partial if err_code == "language_flip" else None,
                "changelog": (enforced.get("draft") or {}).get("changelog") or [],
                "language_flip": err_code == "language_flip",
            }

        draft = enforced["draft"]
        return {
            **base_payload,
            "improved_instructions": draft.get("improved_instructions"),
            "changelog": draft.get("changelog") or [],
            "preserved_intent": draft.get("preserved_intent") or "",
            "risks": draft.get("risks") or [],
            "language": draft.get("language") or evidence.get("language_code") or "zh",
            "language_repaired": False,
            "llm_degraded": False,
            "llm_calls_left": call_budget[0],
        }

    def apply_evolution(
        self,
        team_id: str,
        skill_id: str,
        new_instructions: str,
        changelog: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """应用演化结果（用户确认后调用）."""
        if not self._skill_library:
            return {"error": "skill_library_not_initialized"}

        skill = self._skill_library._find_skill(team_id, skill_id)
        if not skill:
            return {"error": "skill_not_found"}
        if self._is_unusable_evolution_text(new_instructions):
            return {
                "error": "invalid_evolution_instructions",
                "reason": "LLM fallback text cannot be applied as skill instructions",
            }
        if self._is_language_flip(skill.instructions or "", new_instructions or ""):
            return {
                "error": "language_flip",
                "reason": "新指令与原文主体语言不一致，拒绝应用。请改为与原文相同语言后再提交。",
            }

        old_version = skill.version
        # 演化前自动创建版本快照，支持后续回滚
        self._skill_library.create_version_snapshot(skill)
        skill.instructions = new_instructions
        skill.version += 1
        skill.lifecycle_stage = SkillLifecycleStage.TEAM_LOCAL  # Reset to team_local after evolution
        # 轻量留痕：changelog 进 config，供验证/效果页展示（无 schema 破坏）
        notes = [str(x).strip() for x in (changelog or []) if str(x).strip()]
        try:
            cfg = dict(getattr(skill, "config", None) or {})
            cfg["last_evolution"] = {
                "from_version": old_version,
                "to_version": skill.version,
                "changelog": notes[:20],
            }
            skill.config = cfg
        except Exception:
            pass
        self._skill_library._persist_skill(skill, team_id)

        logger.info("Skill %s evolved v%d → v%d", skill_id, old_version, skill.version)
        return {
            "status": "evolved",
            "skill_id": skill_id,
            "old_version": old_version,
            "version": skill.version,
            "changelog": notes[:20],
            "next_step": "verify",
            "next_step_hint": "建议立即验证（语义 + 沙箱 + Twin A/B）",
        }

    # ── Merge: 合并重复技能 ──────────────────────────────────────

    def merge_skills(self, team_id: str, skill_ids: List[str], strategy: str = "keep_longest") -> Dict[str, Any]:
        """合并多个重复技能为一个. 保留最长/最优的 instructions."""
        if not self._skill_library or len(skill_ids) < 2:
            return {"error": "invalid_merge_request"}

        skills = []
        for sid in skill_ids:
            s = self._skill_library._find_skill(team_id, sid)
            if s:
                skills.append(s)

        if len(skills) < 2:
            return {"error": "not_enough_skills_found"}

        # Select primary based on strategy
        if strategy == "keep_longest":
            primary = max(skills, key=lambda s: len(s.instructions))
        elif strategy == "pick_best_score":
            primary = max(skills, key=lambda s: s.effectiveness)
        else:
            primary = skills[0]

        # Create merged skill
        merged = SkillDefinition(
            skill_id=str(uuid4())[:8],
            name=primary.name,
            description=primary.description + " (合并版)",
            category=primary.category,
            icon=primary.icon,
            slug=primary.slug + "_merged",
            instructions=primary.instructions,
            required_tools=list(set(t for s in skills for t in s.required_tools)),
            source="merged",
            origin_team_id=team_id,
            lifecycle_stage=SkillLifecycleStage.TEAM_LOCAL,
            lineage=primary.skill_id,
            version=1,
            usage_count=sum(s.usage_count for s in skills),
            success_count=sum(s.success_count for s in skills),
            fail_count=sum(s.fail_count for s in skills),
        )
        # Recalculate effectiveness
        if merged.usage_count > 0:
            merged.effectiveness = merged.success_count / merged.usage_count

        # Persist merged skill
        self._skill_library._persist_skill(merged, team_id)
        if self._skill_library._team_manager:
            team = self._skill_library._team_manager.get_team(team_id)
            if team:
                team.add_skill(merged)
                self._skill_library._team_manager.save()

        logger.info("Merged %d skills into %s", len(skills), merged.skill_id)
        return {
            "status": "merged",
            "merged_skill_id": merged.skill_id,
            "merged_from": skill_ids,
            "strategy": strategy,
        }

    # ── Suggest: 演化建议 ────────────────────────────────────────

    def suggest_evolution(self, team_id: str) -> List[Dict[str, Any]]:
        """生成演化建议列表."""
        if not self._skill_library:
            return []

        suggestions = []
        all_skills = self._skill_library.browse(team_id=team_id)

        for s in all_skills:
            eff = s.get("effectiveness", 0)
            usage = s.get("usage_count", 0)
            stage = s.get("lifecycle_stage", "")

            # Low effectiveness + high usage → improve
            if usage >= 5 and eff < 0.4:
                suggestions.append({
                    "action": "improve",
                    "skill_id": s["skill_id"],
                    "name": s["name"],
                    "reason": f"💡 成功率{eff * 100:.0f}%，已使用{usage}次",
                    "priority": 1,
                })

            # High effectiveness + not published → publish
            if usage >= 3 and eff > 0.7 and s.get("visibility") == "private":
                suggestions.append({
                    "action": "publish",
                    "skill_id": s["skill_id"],
                    "name": s["name"],
                    "reason": f"🌐 成功率{eff * 100:.0f}%，建议分享到公共库",
                    "priority": 2,
                })

        # Check duplicates
        duplicates = self._skill_library.find_duplicates(threshold=0.85)
        for dup in duplicates:
            suggestions.append({
                "action": "merge",
                "skill_a": dup["skill_a"],
                "skill_b": dup["skill_b"],
                "reason": f"🔀 相似度{dup['similarity'] * 100:.0f}%",
                "priority": 3,
            })

        # Sort by priority
        suggestions.sort(key=lambda x: x.get("priority", 99))
        return suggestions

    # ── Evolution History ────────────────────────────────────────

    def get_evolution_history(self, team_id: str, skill_id: str) -> Dict[str, Any]:
        """获取技能的演化历史."""
        lineage = self._skill_library.get_lineage(skill_id) if self._skill_library else {}
        return {
            "skill_id": skill_id,
            "lineage": lineage,
        }


# ── System Prompt for Evolution ──────────────────────────────────

EVOLVE_SYSTEM_PROMPT = """你是技能演化引擎（Evidence → Attribution → Evolution）。
根据证据改进技能 instructions，输出**唯一** JSON 对象（可包在 ```json 围栏中）。

分清两件事（极其重要）:
A) **生成约束**（只约束你如何写 JSON，绝不能写进 improved_instructions 正文）:
   - improved_instructions 主体语言与「当前指令」一致（中文原文→中文步骤；英文原文→英文）
   - 禁止把中文业务指令整段改写成英文企业 SOP 模板
   - 禁止在正文中出现：「【要求】」「语言：中文」「Language:」「输出语言」「术语可保留英文缩写」等元说明
B) **技能正文**（improved_instructions 的唯一内容）:
   - Agent 执行该 skill 时的业务步骤、规则、验收、回滚、工具用法
   - 与「用什么自然语言写这段文字」无关

原则:
1. 保持核心意图（preserved_intent 一句话）
2. 更具体、可执行；补边界与失败回退
3. changelog 2～8 条业务向变更要点
4. 不要输出 JSON 以外的解释

JSON 字段:
- language: "zh" | "en" | "mixed"（元数据，不是正文）
- improved_instructions: string（仅业务指令）
- changelog: string[]
- preserved_intent: string
- risks: string[]（可空）
"""


def _count_cjk(text: str) -> int:
    return sum(1 for ch in (text or "") if "\u4e00" <= ch <= "\u9fff")


def _count_latin_words(text: str) -> int:
    return len(re.findall(r"[A-Za-z]{2,}", text or ""))


def _instruction_language_hint(text: str) -> str:
    cjk = _count_cjk(text)
    latin = _count_latin_words(text)
    if cjk >= 8 and cjk >= latin * 0.35:
        return "中文（与原文一致；专有名词可保留英文缩写）"
    if latin >= 12 and cjk < 4:
        return "English (match the original instructions)"
    if cjk > 0:
        return "中文为主（与原文一致）"
    return "与原文相同语言"


def _detect_language_code(text: str) -> str:
    cjk = _count_cjk(text)
    latin = _count_latin_words(text)
    if cjk >= 8 and cjk >= latin * 0.35:
        return "zh"
    if latin >= 12 and cjk < 4:
        return "en"
    if cjk > 0 and latin > 0:
        return "mixed"
    if cjk > 0:
        return "zh"
    return "en" if latin else "zh"


def _is_language_flip(original: str, improved: str) -> bool:
    """True if original is Chinese-dominant but improved is English-dominant (or reverse)."""
    if not (original or "").strip() or not (improved or "").strip():
        return False
    o_cjk, o_lat = _count_cjk(original), _count_latin_words(original)
    i_cjk, i_lat = _count_cjk(improved), _count_latin_words(improved)
    orig_zh = o_cjk >= 8 and o_cjk >= max(o_lat * 0.35, 1)
    impro_en = i_lat >= 20 and i_cjk < max(8, i_lat * 0.15)
    orig_en = o_lat >= 12 and o_cjk < 4
    impro_zh = i_cjk >= 12 and i_lat < max(8, i_cjk * 0.5)
    return (orig_zh and impro_en) or (orig_en and impro_zh)


SkillEvolver._instruction_language_hint = staticmethod(_instruction_language_hint)
SkillEvolver._detect_language_code = staticmethod(_detect_language_code)
SkillEvolver._is_language_flip = staticmethod(_is_language_flip)


# ── Singleton ────────────────────────────────────────────────────

_evolver: Optional[SkillEvolver] = None


def get_skill_evolver() -> SkillEvolver:
    global _evolver
    if _evolver is None:
        _evolver = SkillEvolver()
    return _evolver


def init_skill_evolver(skill_library=None, chat_harness=None) -> SkillEvolver:
    global _evolver
    _evolver = SkillEvolver(skill_library=skill_library, chat_harness=chat_harness)
    logger.info("SkillEvolver initialized")
    return _evolver
