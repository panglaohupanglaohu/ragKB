# -*- coding: utf-8 -*-
"""AWS 降本 Case · 脚本 criteria 评分（纯函数，离线可单测，不依赖 LLM）.

Phase 11 G2-a：对 Plaza 产出的运维脚本计划按 5 项 criteria 打分。
score 0~5：满分=脚本同时覆盖「实例规格确认 / 变更应用 / 状态轮询 / 监控告警 / 回滚成本兜底」。
设计依据：docs/superpowers/specs/2026-06-22-phase11-aws-costdown-best-practice-design.md §1 G2-a。
"""

from __future__ import annotations

import re

# (criterion_key, 判定函数) —— 判定函数接收脚本正文 str，返回 bool
CRITERIA = [
    ("instance_spec",
     lambda s: bool(re.search(r"describe-(elasticsearch-domain|domain-config)", s))),
    ("apply_change",
     lambda s: ("update-elasticsearch-domain-config" in s)
               and bool(re.search(r"--(instance-type|instance-count|cluster-config)", s))),
    ("state_poll",
     lambda s: bool(re.search(r"describe-domain", s))
               and bool(re.search(r"\b(while|sleep)\b", s))
               and bool(re.search(r"Processing|Active", s))),
    ("monitor_alarm",
     lambda s: "put-metric-alarm" in s),
    ("rollback_cost",
     lambda s: bool(re.search(r"\bif\b.*\belse\b", s, re.S))
               and bool(re.search(r"backup|备份", s))
               and ("aws pricing" in s or bool(re.search(r"成本|cost", s)))),
]


def score_script(plan_content: str) -> dict:
    """对运维脚本正文打分。

    Returns:
        {"score": int 0~5, "missing": [未命中的 criterion_key], "hit": [命中的 key]}
    """
    text = plan_content or ""
    hit = [k for k, fn in CRITERIA if fn(text)]
    missing = [k for k, _ in CRITERIA if k not in hit]
    return {"score": len(hit), "missing": missing, "hit": hit}
