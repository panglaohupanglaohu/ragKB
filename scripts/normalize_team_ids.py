#!/usr/bin/env python3
"""P10.10: 一次性扫描既有数据中的 team_id，归一连字符↔下划线变体，标注孤儿。

用法: python3 scripts/normalize_team_ids.py [--dry-run]
"""
import json, os, sys, sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DRY_RUN = "--dry-run" in sys.argv

def load_known_team_ids():
    """从 TeamManager 数据文件加载已知 team_id。"""
    teams_file = ROOT / "config" / "teams.json"
    if not teams_file.exists():
        return set()
    try:
        data = json.loads(teams_file.read_text(encoding="utf-8"))
        return {t.get("team_id", "") for t in data.get("teams", []) if t.get("team_id")}
    except Exception:
        return set()

def scan_usage_db(known_ids):
    """扫描 usage.db 中 team_id 为空或不在已知列表的行。"""
    db = ROOT / "storage" / "usage.db"
    if not db.exists():
        return []
    conn = sqlite3.connect(str(db))
    rows = conn.execute(
        "SELECT DISTINCT team_id, COUNT(*), SUM(total_tokens) FROM usage_log "
        "WHERE total_tokens > 0 GROUP BY team_id"
    ).fetchall()
    conn.close()
    findings = []
    for tid, cnt, tok in rows:
        if not tid:
            findings.append({"source": "usage.db", "team_id": "(空)", "rows": cnt, "tokens": tok, "issue": "unattributed"})
        elif tid not in known_ids:
            # 尝试归一化：连字符↔下划线
            normalized = tid.replace("-", "_")
            if normalized in known_ids:
                findings.append({"source": "usage.db", "team_id": tid, "normalized": normalized, "rows": cnt, "tokens": tok, "issue": "normalizable"})
            else:
                findings.append({"source": "usage.db", "team_id": tid, "rows": cnt, "tokens": tok, "issue": "orphan"})
    return findings

def main():
    known = load_known_team_ids()
    print(f"已知团队: {sorted(known)}")
    findings = scan_usage_db(known)
    if not findings:
        print("✅ 无需归一化/标注的 team_id")
        return
    print(f"\n发现 {len(findings)} 个待处理项:")
    for f in findings:
        status = "→ 归一为 " + f.get("normalized", "") if f["issue"] == "normalizable" else f["issue"]
        print(f"  [{f['source']}] team_id='{f['team_id']}' rows={f['rows']} tokens={f['tokens']} → {status}")
    if DRY_RUN:
        print("\n--dry-run 模式，不执行修改")
    else:
        # 实际归一化（仅 normalizable 项）
        db = ROOT / "storage" / "usage.db"
        conn = sqlite3.connect(str(db))
        fixed = 0
        for f in findings:
            if f["issue"] == "normalizable":
                conn.execute("UPDATE usage_log SET team_id=? WHERE team_id=?", (f["normalized"], f["team_id"]))
                fixed += 1
        conn.commit()
        conn.close()
        print(f"\n已归一化 {fixed} 个 team_id")

if __name__ == "__main__":
    main()
