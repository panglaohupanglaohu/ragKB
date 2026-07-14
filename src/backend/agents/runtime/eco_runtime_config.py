# -*- coding: utf-8 -*-
"""Eco Runtime Config — 仿生生态运行时可配置参数的单一数据源.

对应 docs/Agent仿生生态运行时plan.md §2/§3/§4 + todos P3/P4 里出现的所有阈值常量，
集中到一个 JSON 存储 + REST 可编辑，供前端「仿生生态运行时参数」Tab 页读写。

设计原则（对齐 pet_ecosystem.py）：
- `_DEFAULTS` 是内置默认；`get_config()` 用它对缺字段的旧配置做深度补全。
- 用户显式值始终覆盖默认。
- 落盘 storage/eco_runtime_config.json（原子写）。
- 各运行时模块通过 `from_config()` 工厂读取"当前生效阈值"，硬编码常量退居最终兜底，
  因此本模块缺失/损坏时系统仍能按内置默认运行（不破坏既有单元测试）。
"""

from __future__ import annotations

import copy
import json
import logging
import os
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

_DEFAULT_CONFIG_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "..", "storage", "eco_runtime_config.json"
)


# 内置默认——每个键对应 plan/todos 里一个可调阈值。
_DEFAULTS: Dict[str, Dict[str, Any]] = {
    # §2 H/F/L 意图仲裁阈值（eco_loop.IntentionThresholds）
    "mental_state": {
        "fear_escape": 0.55,        # 恐惧逃逸阈值：F 超此值 → avoid
        "fear_calm": 0.35,          # 恐惧平静阈值：滞回，降到此值以下才离开 avoid
        "hunger_threshold": 0.4,    # 饥饿觅食阈值：H 超此值 → forage
        "libido_threshold": 0.6,    # 繁殖意图阈值：L 超此值 → mate
    },
    # §3 Health 代谢账本（health_ledger.HealthState / HealthLedger）
    "metabolism": {
        "health_max": 100.0,        # 满血值
        "metabolic_rate": 1.0,      # 每 tick 基础代谢消耗
        "revive_ratio": 0.5,        # 复活恢复到 health_max 的比例
        "saturation_threshold": 0.7,  # 「饱暖」判定阈值（sustained_ratio）
    },
    # §4 盲目学习探索期 + 特征抽象（twin_loop.compute_exploration_rate / health_ledger.should_solidify）
    "learning": {
        "exploration_base_rate": 0.7,   # 新 Agent 初始探索率
        "exploration_half_life": 50,    # 探索率半衰期 tick 数
        "solidify_min_uses": 5,         # 触发特征抽象的最小使用次数
        "solidify_min_gain": 0.0,       # 触发特征抽象的最小净收益
        # 物竞天择 v2（eco_drill 盲目学习，plan §3.2）
        "blind_learning_rate": 0.1,     # REST 时随机习得 skill 的概率（学习是盲目的）
        "genome_carry_cost": 0.05,      # 每携带 1 个 skill 的每 tick 额外代谢（惩罚技能囤积）
    },
    # 物竞天择 v2 生境环境（eco_drill.EnvState，plan §3.3：环境必须流动）
    # 2026-07-14 加压默认：略降丰饶、略升捕食，避免「苟活」吸收态主导 T_i
    "habitat": {
        "drift_prob": 0.2,          # 每世代生态位漂移概率（随机替换 1 个需求 skill）
        "predator_pressure": 0.12,  # 每 tick 捕食事件概率（0=关闭）
        "abundance": 0.7,           # 丰饶度：觅食收益倍率（0.5 艰难 ~ 2.0 富足）
        "niche_capacity": 3,        # 「物竞」：每 tick 生态位可供成功觅食的名额（0=不限）
    },
    # 物竞天择 v2 觅食/协作经济学（eco_drill 常量的可调化，用户 2026-07-11 要求）
    "drill_economics": {
        "forage_gain": 9.0,          # 觅食命中获得的能量（×abundance）
        "forage_miss_penalty": 2.5,  # 觅食未命中的额外代谢惩罚
        "avoid_cost": 0.5,           # 避险动作代谢
        "signal_cost": 0.3,          # 发一次信号的代谢成本（协作有代价才会被选择）
        "share_fraction": 0.4,       # 分享时让渡给求助者的收益比例
        "follow_bonus": 0.18,        # 跟随 FOOD 信号的觅食成功率加成
        "help_hunger": 0.7,          # 饥饿超过此值才发 HELP 信号
        # 能 serve 却 REST：额外代谢（「有 skill 不用」被环境惩罚 → 抬高 skill%）
        "skill_idle_penalty": 1.2,
    },
    # 物竞天择选择状态机（skill_library.evaluate_selection_state）
    "selection": {
        "dominant_min_streak": 3,           # 连续正/负净收益的判定长度
        "dominant_usage_threshold": 10,     # 晋升 dominant 的最小总使用次数
    },
    # 交配门禁（team_manager.can_mate）
    "mating": {
        "saturation_threshold": 0.7,    # 允许交配的 Health 占比门槛
    },
    # 物竞天择 v3 混合竞争——纪元嵌套（plan V3-1.3：螺旋上升 · 大小迭代）
    "era": {
        "era_count": 3,                 # 纪元数（大迭代次数；1=退化为单纪元零回归）
        "epochs_per_era": 3,            # 每纪元内的世代数（小迭代）
        "cross_pop_mating": True,       # 跨队交配开关（混合竞争=基因流开启）
        # 环境阶跃加压：每跨一个纪元，环境参数按此增量调整
        "env_ramp": {
            "abundance": -0.15,         # 丰饶度递减（资源越来越稀缺）
            "predator_pressure": 0.05,  # 捕食压力递增
            "drift_prob": 0.05,         # 漂移概率递增（生态位变换加速）
            "niche_capacity": -1,       # 竞争名额递减（从 3→2→1…0=不限）
        },
    },
    # 物竞天择 v4 任务闭环（plan 物竞天择任务闭环与Skill遗传）
    "task_coupling": {
        "reduce_drift_when_bound": True,  # 绑定计划后降低漂移
        "role_affinity": 1.1,             # 角色匹配熟练度系数
        "write_policy": "suggest_only",   # Skill 集成默认只建议
    },
    # 演化加压旋钮（下一局「让 Skill/团队变强」）
    "evolution_pressure": {
        "skill_idle_penalty": 1.2,        # 与 drill_economics 同步入口；>0 惩罚能 serve 却 REST
        "genome_carry_cost": 0.08,        # 覆盖 learning.genome_carry_cost（囤积税）
        "min_steps_when_contract": 64,    # 绑定契约时至少跑这么多步/代
        "min_gens_when_contract": 4,      # 绑定契约时至少世代数
        "prefer_forage_when_can_serve": 1,  # 1=意图层对 can_serve 略偏 forage（见 eco_drill）
        # 捕食/协作选择压（默认>0 生产加压；单元测试 EcoDrill 直构 economics 默认 0）
        "predator_bias_unskilled": 2.0,   # 无法 serve 的个体被捕食权重 +=bias
        "scarce_share_boost": 1.2,        # 丰饶不足时分享让渡放大 → 协作更值钱
        "same_pop_share_bias": 0.7,       # 优先同队分享 → 团队边界可被选择
    },
    # LLM 演练分析提示词（pet-config 可编辑；{summary} 注入结构化数据）
    "llm_analysis": {
        "timeout_s": 90,
        "max_chars": 900,
        "system_preamble": (
            "你是 AgentsGroup 数字孪生实验室的进化分析师。用户已看到排行榜数字；"
            "你的任务是判断两件事并写可执行结论：\n"
            "A) 当前系统是否在让 **Skill 进化**（dominant/deprecated、skill% 归因、契约 demand 是否匹配 genome）？\n"
            "B) 当前系统是否在找到 **团队演化方式**（协作基因 share/signal/follow、多队对比、混合纪元）？"
        ),
        "hard_constraints": (
            "硬约束：\n"
            "- 唯一适应度是生存时长 T_i，禁止发明第二评分。\n"
            "- 任务/契约是客观环境（同一考卷过滤），不是「天选任务」。\n"
            "- 分场=多队比个体 skill；对抗=比协作策略；混合=个体+团队。\n"
            "- 若 skill%≈0 且 residual 主导：明确指出「环境 demand 与 agent genome 未对齐」或「选择压力太弱」，"
            "并给下一步（补 required_skills / 对齐 agent 技能 / 提高步数世代 / 降 abundance 升 predator）。\n"
            "- 若 dominant 技能与任务生态位一致：说明 Skill 进化闭环有效。\n"
            "- 若 collab% 高且幸存者 share/signal 偏移：说明团队协作方式被选择。"
        ),
        "output_structure": (
            "输出结构（中文，400~700 字，禁止空话）：\n"
            "1. **因果**：谁赢了、因为 skill 还是协作还是苟活残差\n"
            "2. **Skill 进化判定**：能 / 弱 / 不能 + 证据（dominant/deprecated/归因）\n"
            "3. **团队演化判定**：能 / 弱 / 不能 + 证据（协作基因组、多队差距）\n"
            "4. **下一局旋钮**：改 abundance/predator/drift 或契约 skills 的 2~3 条具体建议\n"
            "5. **一句话**：这个环境在选择什么样的 Agent/团队"
        ),
        "data_header": "=== 演练结构化数据 ===",
    },
}


class EcoRuntimeConfig:
    """仿生生态运行时参数管理器 — 加载/保存/深度合并默认。"""

    def __init__(self, config_path: str = "") -> None:
        self._path = config_path or _DEFAULT_CONFIG_PATH
        self._config: Dict[str, Any] = {}
        self._load()

    def _load(self) -> None:
        try:
            with open(self._path, "r", encoding="utf-8") as f:
                self._config = json.load(f)
            if not isinstance(self._config, dict):
                raise ValueError("config is not an object")
        except FileNotFoundError:
            self._config = {}
        except Exception as e:
            logger.warning("🧬 EcoRuntimeConfig load failed (%s); using defaults", e)
            self._config = {}

    def _save(self) -> None:
        try:
            os.makedirs(os.path.dirname(self._path), exist_ok=True)
            tmp = self._path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(self._config, f, ensure_ascii=False, indent=2)
            os.replace(tmp, self._path)
        except Exception as e:
            logger.error("🧬 EcoRuntimeConfig save failed: %s", e)

    def get_config(self) -> Dict[str, Any]:
        """返回深度补全默认后的全量配置（用户值覆盖默认）。"""
        merged: Dict[str, Any] = {}
        for section, defaults in _DEFAULTS.items():
            merged[section] = {**defaults, **(self._config.get(section, {}) or {})}
        return merged

    def get_section(self, section: str) -> Dict[str, Any]:
        defaults = _DEFAULTS.get(section, {})
        return {**defaults, **(self._config.get(section, {}) or {})}

    def get_defaults(self) -> Dict[str, Any]:
        return copy.deepcopy(_DEFAULTS)

    def update(self, updates: Dict[str, Any]) -> Dict[str, Any]:
        """部分更新：只覆盖 _DEFAULTS 里已知的 section/键，忽略未知键（防脏写）。

        支持 str / number / bool / dict（如 era.env_ramp）值。
        """
        for section, values in (updates or {}).items():
            if section not in _DEFAULTS or not isinstance(values, dict):
                continue
            cur = dict(self._config.get(section, {}) or {})
            defaults_sec = _DEFAULTS[section]
            for k, v in values.items():
                if k not in defaults_sec:
                    continue
                # 嵌套 dict：浅合并（保留未提交子键的默认）
                if isinstance(defaults_sec[k], dict) and isinstance(v, dict):
                    base = {**defaults_sec[k], **(cur.get(k) if isinstance(cur.get(k), dict) else {})}
                    base.update(v)
                    cur[k] = base
                else:
                    cur[k] = v
            self._config[section] = cur
        self._save()
        return self.get_config()

    def reset(self) -> Dict[str, Any]:
        """恢复全部默认（清空用户覆盖）。"""
        self._config = {}
        self._save()
        return self.get_config()


# ── 单例 ──
_instance: Optional[EcoRuntimeConfig] = None


def get_eco_runtime_config() -> EcoRuntimeConfig:
    global _instance
    if _instance is None:
        _instance = EcoRuntimeConfig()
    return _instance


def reset_eco_runtime_config(config_path: str = "") -> EcoRuntimeConfig:
    """测试专用：重建单例（可指定临时路径）。"""
    global _instance
    _instance = EcoRuntimeConfig(config_path=config_path)
    return _instance
