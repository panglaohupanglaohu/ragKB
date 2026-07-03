# -*- coding: utf-8 -*-
"""v4 存量 Trial 数据迁移 — 幂等 (A-4.5).

为 storage/trials/trials.json 中的旧 Trial 补齐 v4 字段:
  scenario_id="legacy", generation=0, parent_trial_id=""

用法: python src/backend/scripts/migrate_trials_v4.py [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TRIALS_FILE = ROOT / "storage" / "trials" / "trials.json"

V4_DEFAULTS = {
    "scenario_id": "legacy",
    "generation": 0,
    "parent_trial_id": "",
}


def migrate(dry_run: bool = False) -> dict:
    if not TRIALS_FILE.exists():
        return {"ok": True, "migrated": 0, "note": "trials.json 不存在，无需迁移"}

    data = json.loads(TRIALS_FILE.read_text(encoding="utf-8"))
    trials = data.get("trials", {})
    migrated = 0
    for tid, t in trials.items():
        changed = False
        for key, default in V4_DEFAULTS.items():
            if key not in t:
                t[key] = default
                changed = True
        if changed:
            migrated += 1

    if migrated and not dry_run:
        backup = TRIALS_FILE.with_suffix(".json.pre-v4.bak")
        if not backup.exists():
            backup.write_text(TRIALS_FILE.read_text(encoding="utf-8"), encoding="utf-8")
        tmp = TRIALS_FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.rename(TRIALS_FILE)

    return {"ok": True, "migrated": migrated, "total": len(trials), "dry_run": dry_run}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    result = migrate(dry_run=args.dry_run)
    print(json.dumps(result, ensure_ascii=False))
    sys.exit(0 if result["ok"] else 1)
