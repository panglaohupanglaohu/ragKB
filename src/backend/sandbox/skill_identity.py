# -*- coding: utf-8 -*-
"""Skill 身份归一 — 物竞天择 v4 XG-3.

genome 匹配与 demanded_skills 必须在同一 canonical 空间比较，
避免「同名不同 ID」导致误饿死。
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional, Tuple


def _norm(s: str) -> str:
    return (s or "").strip().lower().replace(" ", "_").replace("-", "_")


def build_catalog(
    entries: Iterable[Any],
) -> Dict[str, str]:
    """从 (id, name/slug) 条目构建 alias→canonical_id 映射.

    entries 每项可为:
      - str id
      - (id, name)
      - dict with id/skill_id + name/slug
      - 对象 with id/skill_id + name/slug
    """
    catalog: Dict[str, str] = {}
    for e in entries:
        sid, name, slug = "", "", ""
        if isinstance(e, str):
            sid = e
        elif isinstance(e, (tuple, list)) and e:
            sid = str(e[0])
            if len(e) > 1 and e[1]:
                name = str(e[1])
        elif isinstance(e, dict):
            sid = str(e.get("id") or e.get("skill_id") or e.get("sid") or "")
            name = str(e.get("name") or "")
            slug = str(e.get("slug") or "")
        else:
            sid = str(getattr(e, "skill_id", None) or getattr(e, "id", "") or "")
            name = str(getattr(e, "name", "") or "")
            slug = str(getattr(e, "slug", "") or "")
        if not sid:
            continue
        canonical = sid
        catalog[_norm(sid)] = canonical
        if name:
            catalog[_norm(name)] = canonical
        if slug:
            catalog[_norm(slug)] = canonical
    return catalog


def canonicalize(skill_ref: str, catalog: Optional[Dict[str, str]] = None) -> str:
    """将 skill 引用归一到 canonical id；无 catalog 或未命中时返回原串（去空白）."""
    raw = (skill_ref or "").strip()
    if not raw:
        return ""
    if not catalog:
        return raw
    hit = catalog.get(_norm(raw))
    return hit if hit else raw


def canonicalize_list(
    skills: Iterable[str],
    catalog: Optional[Dict[str, str]] = None,
    *,
    dedupe: bool = True,
) -> List[str]:
    out: List[str] = []
    seen = set()
    for s in skills or []:
        c = canonicalize(str(s), catalog)
        if not c:
            continue
        if dedupe:
            if c in seen:
                continue
            seen.add(c)
        out.append(c)
    return out


def merge_catalogs(*catalogs: Dict[str, str]) -> Dict[str, str]:
    merged: Dict[str, str] = {}
    for c in catalogs:
        if c:
            merged.update(c)
    return merged
