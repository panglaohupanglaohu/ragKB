#!/usr/bin/env python3
"""P2-3: 技能库 similarity 去重批处理.

扫描所有团队的技能，找出 similarity > threshold 的重复对，
可选 --auto-merge 自动合并（保留 version 最高的，解绑旧版本的 agent 引用）。

用法:
  python scripts/skill_dedup.py                    # 只扫描，不修改
  python scripts/skill_dedup.py --threshold 0.85   # 指定阈值
  python scripts/skill_dedup.py --auto-merge       # 自动合并
"""
import sys, os, json, argparse
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'backend'))

from agents.team_manager import TeamManager

def jaccard_similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    ta = set(a.lower().split())
    tb = set(b.lower().split())
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)

def find_duplicates(tm: TeamManager, threshold: float = 0.85):
    """找出所有团队中 similarity > threshold 的技能对."""
    all_skills = []
    for team in tm.list_teams():
        for sid, skill in team.skills.items():
            text = f"{skill.name} {skill.description}"
            all_skills.append({
                "team_id": team.team_id,
                "skill_id": sid,
                "name": skill.name,
                "description": skill.description or "",
                "version": getattr(skill, 'version', 1),
                "text": text,
            })

    duplicates = []
    for i in range(len(all_skills)):
        for j in range(i + 1, len(all_skills)):
            s1, s2 = all_skills[i], all_skills[j]
            sim = jaccard_similarity(s1["text"], s2["text"])
            if sim >= threshold:
                duplicates.append({
                    "skill_a": f"{s1['team_id']}/{s1['skill_id']}",
                    "name_a": s1["name"],
                    "skill_b": f"{s2['team_id']}/{s2['skill_id']}",
                    "name_b": s2["name"],
                    "similarity": round(sim, 3),
                    "keep": s1["skill_id"] if s1["version"] >= s2["version"] else s2["skill_id"],
                    "remove": s2["skill_id"] if s1["version"] >= s2["version"] else s1["skill_id"],
                })
    return duplicates

def auto_merge(tm: TeamManager, duplicates):
    """自动合并：移除低版本技能 + 解绑 agent 引用."""
    merged = 0
    for dup in duplicates:
        remove_id = dup["remove"]
        for team in tm.list_teams():
            if remove_id in team.skills:
                del team.skills[remove_id]
                merged += 1
            for agent in team.agents.values():
                if remove_id in agent.skills:
                    agent.skills.remove(remove_id)
    tm._persist()
    return merged

def main():
    parser = argparse.ArgumentParser(description="技能库 similarity 去重")
    parser.add_argument("--threshold", type=float, default=0.85, help="相似度阈值")
    parser.add_argument("--auto-merge", action="store_true", help="自动合并重复技能")
    args = parser.parse_args()

    tm = TeamManager()
    dups = find_duplicates(tm, args.threshold)

    if not dups:
        print(f"✅ 未发现 similarity >= {args.threshold} 的重复技能对")
        return 0

    print(f"⚠️ 发现 {len(dups)} 对重复技能 (threshold={args.threshold}):")
    for d in dups:
        print(f"  [{d['similarity']:.2f}] {d['skill_a']} ({d['name_a']})")
        print(f"       ↔ {d['skill_b']} ({d['name_b']})")
        print(f"       建议: 保留 {d['keep']}, 移除 {d['remove']}")

    if args.auto_merge:
        merged = auto_merge(tm, dups)
        print(f"\n✅ 已合并 {merged} 个重复技能副本，已持久化")
    else:
        print(f"\n💡 加 --auto-merge 自动合并")

    return 0

if __name__ == "__main__":
    sys.exit(main())
