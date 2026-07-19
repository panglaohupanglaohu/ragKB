# -*- coding: utf-8 -*-
"""治理杠杆目录 — 业界出处 + 本仓实现 + 可观测字段.

UI / plan 共用本清单，禁止前端硬编码「空开关文案」。
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

# 每条杠杆的权威定义（与 prepare_request 顺序一致）
LEVER_CATALOG: List[Dict[str, Any]] = [
    {
        "id": "simplify_prompt",
        "order": 1,
        "title": "提示词简化",
        "title_en": "Prompt Simplification",
        "settings_key": "simplify_prompt",
        "kind": "boolean",
        "default": True,
        "industry": {
            "lane": "E · 上下文工程",
            "inspired_by": [
                "BCG (2026) — re-architect agent flow: pass goals not full logs",
                "Helicone Prompt Engineering — 去冗余 prompt 变体对比",
                "OpenAI/Anthropic prompt caching 前置条件：稳定短 prefix",
            ],
            "what_they_do": "缩短 system/user 冗余，降低输入 token；不做语义改写以免伤效果",
        },
        "ours": {
            "module": "agents/token_governance/prompt_simplify.py",
            "entry": "simplify_messages()",
            "called_from": "TokenGovernanceService.prepare_request step①",
            "algorithm": [
                "normalize 空白与连续空行",
                "短套话行（你是/You are/请务必/重要：）去重",
                "确定性，零 LLM 调用",
            ],
            "metric_keys": ["simplify_saves"],
            "effect_field": "levers[].saved when kind=simplify",
        },
        "exec_path": [
            "chat_harness.chat → prepare_request",
            "tool_loop 每轮 → prepare_request",
            "POST /simulate → prepare_request",
        ],
    },
    {
        "id": "compress",
        "order": 2,
        "title": "内容压缩",
        "title_en": "Context Compression",
        "settings_key": "compress",
        "kind": "boolean",
        "default": True,
        "industry": {
            "lane": "E · 上下文工程",
            "inspired_by": [
                "BCG — share workspace; pass goals, not full logs",
                "Claude/GPT tool-result compaction 模式",
                "LangChain / LlamaIndex context condensers（我们不用 LLM 摘要）",
            ],
            "what_they_do": "压缩 tool 结果与重复消息，控制上下文窗口与费用",
        },
        "ours": {
            "module": "agents/prompt_cache.py",
            "entry": "compress_messages()",
            "called_from": "prepare_request step②",
            "algorithm": [
                "相邻同 role+同 content 去重 (dedupe_adjacent)",
                "长 tool/function/assistant 头尾折叠 (fold_long_*)",
                "超长 system/user 硬截断 (truncate_*)",
                "默认 system≤6000 字、其它≤4000 字",
            ],
            "metric_keys": ["compress_saves"],
            "effect_field": "levers[].saved + action_counts",
        },
        "exec_path": [
            "prepare_request → compress_messages",
            "试跑样例故意带重复 user + 超长 tool",
        ],
    },
    {
        "id": "rtk_tool_compress",
        "order": 2.1,
        "title": "RTK 工具输出压缩",
        "title_en": "RTK Tool Output Compress",
        "settings_key": "rtk_tool_compress",
        "kind": "boolean",
        "default": True,
        "industry": {
            "lane": "E · 工具环 token 杀手",
            "inspired_by": [
                "rtk-ai/rtk — CLI proxy 60–90% tool-output savings (Apache-2.0 ideas)",
                "flowork_Router RTK compressors — git-diff/grep/ls/tree 11 detectors",
            ],
            "what_they_do": "在 tool 结果进下一轮 LLM 前：滤噪声、去重、分组路径、失败优先截断",
        },
        "ours": {
            "module": "agents/token_governance/rtk_tool_compress.py",
            "entry": "rtk_compress_messages()",
            "called_from": "prepare_request step①b（compress 之前）",
            "algorithm": [
                "filter_noise: 进度条/ANSI/空分隔行",
                "dedupe: 连续重复行折叠 ×N；passed 测试过量省略",
                "group_paths: git status 按顶层目录聚合",
                "truncate: head+tail 预算默认 2200 字/ tool blob",
            ],
            "metric_keys": ["rtk_saves"],
            "effect_field": "levers[].saved when kind=rtk_tool",
        },
        "exec_path": [
            "tool_loop 每轮 → prepare → rtk_compress_messages",
            "chat_harness.chat → prepare",
        ],
    },
    {
        "id": "progressive_memory",
        "order": 2.2,
        "title": "渐进式历史（Mem Index）",
        "title_en": "Progressive Memory Disclosure",
        "settings_key": "progressive_memory",
        "kind": "boolean",
        "default": True,
        "industry": {
            "lane": "E · 上下文工程",
            "inspired_by": [
                "thedotmack/claude-mem — index→timeline→full 三层，~10x token",
                "OpenWolf STATUS.md handoff — 小文档恢复会话",
            ],
            "what_they_do": "旧轮次折叠成索引行，只保留最近 N 轮全文 + 任务锚点",
        },
        "ours": {
            "module": "agents/token_governance/progressive_history.py",
            "entry": "progressive_collapse()",
            "called_from": "prepare_request step②b",
            "algorithm": [
                "保留全部 system + 首条 user 目标锚点",
                "中间轮次 → [TG_MEM_INDEX] 一行摘要",
                "最近 keep_recent=6 轮保持全文",
                "零 LLM，确定性",
            ],
            "metric_keys": ["progressive_saves"],
            "effect_field": "levers[].collapsed / saved",
        },
        "exec_path": ["prepare_request → progressive_collapse"],
    },
    {
        "id": "codegraph_context",
        "order": 2.3,
        "title": "CodeGraph 手术刀上下文",
        "title_en": "CodeGraph Surgical Context",
        "settings_key": "codegraph_context",
        "kind": "boolean",
        "default": True,
        "industry": {
            "lane": "E · 代码智能",
            "inspired_by": [
                "colbymchenry/codegraph (MIT) — explore 一次给源码+调用路径，少 tool call",
                "OpenWolf anatomy symbols — offset/limit 读函数而非整文件",
            ],
            "what_they_do": "大源码 dump → 符号表/局部切片；可选 CLI codegraph explore",
        },
        "ours": {
            "module": "agents/token_governance/codegraph_bridge.py",
            "entry": "apply_codegraph() / compress_source_blobs()",
            "called_from": "prepare_request step②c",
            "algorithm": [
                "本地: 正则抽 def/class/function 行号表，省略函数体",
                "CLI: codegraph explore <query> （需 .codegraph 索引，MIT 包）",
                "AG_CODEGRAPH_BIN 可覆盖路径",
            ],
            "metric_keys": ["codegraph_saves"],
            "effect_field": "levers[].replaced / saved / indexed",
        },
        "exec_path": [
            "prepare → apply_codegraph",
            "npm i -g @colbymchenry/codegraph && codegraph init",
        ],
    },
    {
        "id": "ponytail_caveman",
        "order": 4.5,
        "title": "Ponytail + Caveman 行为",
        "title_en": "Ponytail Ladder + Caveman Output",
        "settings_key": "ponytail_level",
        "kind": "enum",
        "default": "full",
        "enum_values": ["off", "lite", "full", "ultra"],
        "industry": {
            "lane": "E · 生成侧省 token",
            "inspired_by": [
                "ponytail skill — YAGNI ladder，agentic -22% tokens (MIT)",
                "Flowork Router Caveman mode — terse output 省 output tokens",
                "caveman skill — 65% prose cut 思想",
            ],
            "what_they_do": "注入极短行为约束：少写代码废话 + 回复简练 → 降输出与后续工具轮次",
        },
        "ours": {
            "module": "agents/token_governance/behavior_inject.py",
            "entry": "inject_behavior(ponytail, caveman)",
            "called_from": "prepare_request step④b",
            "algorithm": [
                "system 追加 [TG_PONYTAIL] ladder（lite/full/ultra）",
                "system 追加 [TG_CAVEMAN] 简练回复（settings.caveman_level）",
                "幂等：已有 tag 不再注入",
                "output_save_est 启发式计入 counters（不虚增 input saved）",
            ],
            "metric_keys": ["behavior_injects", "output_save_est"],
            "effect_field": "levers[].injected / output_save_est",
        },
        "exec_path": ["prepare → inject_behavior → LLM 生成更短"],
    },
    {
        "id": "cache",
        "order": 3,
        "title": "上下文缓存",
        "title_en": "Prompt / Context Cache",
        "settings_key": "cache_mode",
        "kind": "enum",
        "default": "observe",
        "enum_values": ["observe", "serve", "off"],
        "industry": {
            "lane": "B · 缓存",
            "inspired_by": [
                "Portkey — exact + semantic caching (可省 30–70% 重复流量)",
                "Helicone — gateway cache / observability",
                "GPTCache — 语义缓存",
                "OpenAI/Anthropic — provider-side prompt cache（稳定 prefix）",
            ],
            "what_they_do": "重复/近重复请求命中缓存，跳过或减半计费",
        },
        "ours": {
            "module": "agents/prompt_cache.py + service.semantic_lite_fingerprint",
            "entry": "PromptCache.get/put · semantic_lite_fingerprint()",
            "called_from": "prepare_request step③",
            "algorithm": [
                "Exact：规范化 messages 后 SHA-256",
                "Semantic-lite：剥离 UUID/ISO时间/长 hex 再指纹（非向量）",
                "进程内 LRU（默认 256 条）",
                "observe=记 hit/miss 不短路 LLM；serve=可短路；off=关闭",
            ],
            "metric_keys": ["cache_hits", "cache_misses"],
            "effect_field": "levers[].hit + cache_key",
            "safety": "默认 observe，避免错误缓存答案；serve 需显式开启",
        },
        "exec_path": [
            "prepare_request 查 LRU",
            "同消息连跑两次 → 第二次 HIT（试跑按钮）",
        ],
    },
    {
        "id": "skill_route",
        "order": 4,
        "title": "Skill 路由",
        "title_en": "Skill Routing / Reuse",
        "settings_key": "skill_route_hint",
        "kind": "boolean",
        "default": True,
        "industry": {
            "lane": "C · 路由 + 复用",
            "inspired_by": [
                "token_policy.SKILL_ROUTING_MISS — 有 skill 却走 raw LLM",
                "Agent skill libraries / Cursor skills — 绑定可复用能力",
                "Portkey/LiteLLM routing 思想：先便宜再升级（此处是 skill 优先）",
            ],
            "what_they_do": "有可复用 skill 时注入短指令，避免每次从零生成长 playbook",
        },
        "ours": {
            "module": "skill_router.py + service._skill_hint + _apply_skill_shorten",
            "entry": "SkillRouter.route() → RoutingSession.results",
            "called_from": "prepare_request step④",
            "algorithm": [
                "解析 RoutingSession/RouteResult（非 dict）",
                "pool 为空 → 团队 skills 关键词回退",
                "命中后 system 硬上限 3500 字截断",
                "注入 [TG_SKILL_BODY] 精简指令（SkillRouter._generate_inject_prompt）",
                "saved 只计真实 before→after，禁止虚增",
            ],
            "metric_keys": ["skill_hints", "skill_tokens_saved_est"],
            "effect_field": "levers[].skills / injected / system_truncated / saved_est",
        },
        "exec_path": [
            "prepare → _skill_hint → _apply_skill_shorten",
            "chat_harness / tool_loop 使用缩短后 messages",
        ],
    },
    {
        "id": "model_route",
        "order": 5,
        "title": "模型路由",
        "title_en": "Model Tier Routing",
        "settings_key": "model_route",
        "kind": "boolean",
        "default": True,
        "industry": {
            "lane": "C · 智能路由",
            "inspired_by": [
                "LiteLLM — cascade / fallback / budget-aware route",
                "flowork_Router — cost-tier heuristic (char+code+tools+multi-turn)",
                "OpenRouter / Not Diamond — 按任务选便宜够用的模型",
                "Portkey — virtual keys + routing policies",
            ],
            "what_they_do": "简单任务用小模型，失败再升档；预算紧强制降档",
        },
        "ours": {
            "module": "runtime/model_router.py + token_governance/cost_tier.py",
            "entry": "classify_complexity() → prefer_tier() → ModelRouter.route()",
            "called_from": "prepare_request step⑤；harness/tool_loop 采用 model 名",
            "algorithm": [
                "cost_tier: 短/简单关键词 → economy；复杂/长/代码+工具 → frontier",
                "三档默认：deepseek-v4-flash / deepseek-v4-pro / glm-5.1",
                "预算用尽阈值 → ECONOMY；连续失败 → 升档",
                "sticky 粘滞防抖；prefer_tier 尊重失败阈值",
            ],
            "metric_keys": ["model_routes", "model_economy_routes"],
            "effect_field": "levers[].tier / model / cost_tier_hint",
        },
        "exec_path": [
            "prepare → model_decision",
            "chat_harness 无 model_override 时用 routed model",
            "tool_loop 用 model_name 调 LLM",
        ],
    },
    {
        "id": "budget",
        "order": 6,
        "title": "预算门禁",
        "title_en": "Token Budget Guard",
        "settings_key": "budget_enforce_turn",
        "kind": "boolean",
        "default": True,
        "industry": {
            "lane": "D · 预算治理",
            "inspired_by": [
                "Portkey budgets / virtual keys",
                "Enterprise FinOps token budgets as policy controls (Airia, BCG)",
                "本仓既有 BudgetGuard session/agent/team 日限额",
            ],
            "what_they_do": "超限 warn 或 halt，防止 runaway agent 烧 token",
        },
        "ours": {
            "module": "agents/budget/guard.py",
            "entry": "BudgetGuard.check() / save_budget_settings()",
            "called_from": "prepare step⑥；submit_task precheck；chat_harness 二次 check",
            "algorithm": [
                "per_session_max / per_agent_daily_max / per_team_daily_max",
                "alert_threshold 默认 0.8 warn",
                "on_exceed=halt|warn",
                "submit 时 halt → HTTP 402",
            ],
            "metric_keys": ["budget_blocks"],
            "effect_field": "budget.allowed / events",
        },
        "exec_path": [
            "prepare_request 末尾 check",
            "POST /teams/{id}/tasks 预检",
            "工作台预算表单 → POST /token-governance/budget",
        ],
    },
]


def get_lever_catalog() -> List[Dict[str, Any]]:
    return list(LEVER_CATALOG)


def catalog_with_runtime(
    settings: Dict[str, Any],
    counters: Dict[str, Any],
    cache: Dict[str, Any],
    model_state: Dict[str, Any],
    budget_params: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """目录 + 当前开关 + 运行时指标 + 可调参数当前值."""
    from .lever_params import attach_params_to_catalog_row

    tg_params = (settings or {}).get("params") or {}
    budget_params = budget_params or {}
    out = []
    for item in LEVER_CATALOG:
        row = dict(item)
        key = item["settings_key"]
        if item["kind"] == "enum":
            val = settings.get(key, item["default"])
            row["enabled"] = val not in ("off", False, None)
            row["value"] = val
            # companion level for ponytail card
            if item["id"] == "ponytail_caveman":
                row["caveman_level"] = settings.get("caveman_level", "full")
        else:
            row["enabled"] = bool(settings.get(key, item["default"]))
            row["value"] = row["enabled"]
        if item["id"] == "model_route":
            row["cost_tier_route"] = bool(settings.get("cost_tier_route", True))
        metrics = {}
        for mk in item.get("ours", {}).get("metric_keys") or []:
            if mk in counters:
                metrics[mk] = counters[mk]
            if mk in ("cache_hits", "cache_misses") and cache:
                metrics["cache_size"] = cache.get("size")
                metrics["cache_hit_rate"] = cache.get("hit_rate")
                metrics[mk] = cache.get(mk.replace("cache_", ""), counters.get(mk))
        if item["id"] == "model_route" and model_state:
            metrics["current_tier"] = model_state.get("current_tier")
        if item["id"] == "codegraph_context":
            try:
                from .codegraph_bridge import find_codegraph_bin, project_has_index
                metrics["codegraph_bin"] = bool(find_codegraph_bin())
                metrics["indexed"] = project_has_index()
            except Exception:
                pass
        row["runtime"] = metrics
        # UI 一行表：接线状态（生产路径固定）
        row["wired"] = True
        row["wire_label"] = "harness·loop·sim"
        row["params"] = attach_params_to_catalog_row(item["id"], tg_params, budget_params)
        # 长文不进 UI 契约标记（前端应跳过 industry/algorithm 渲染）
        row["docs_anchor"] = "任务-token-治理"
        out.append(row)
    return out
