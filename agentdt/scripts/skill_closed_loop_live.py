# -*- coding: utf-8 -*-
"""技能闭环 — 本机真后端交叉验证（对照离线 demo 的 +18.3pp）。

与 `skill_closed_loop_demo.py`（纯 sandbox 离线）不同,本脚本打**真实运行后端**
(http://localhost:8080)的试炼 REST API,用 `proficiency_store` 为评审员 agent
设两档 code_review 熟练度(baseline 0.45 / treatment 0.85,其余技能不动),
各跑一次真试炼并 evaluate,对比评分与 code_review 成功率,与离线结论互相印证。

必须在本机用 `rtk` 跑(需后端 8080 + 仓库本地 storage 可写):
    rtk python3 scripts/skill_closed_loop_live.py --team <团队id> --agent <评审员agent_id>

说明:
- 后端为 cookie+CSRF 鉴权,脚本会自动注册一次性用户引导会话(照搬 test_full_flow)。
- 熟练度通过本机 `sandbox.proficiency_store` 直接落盘(trial 创建时会读它作为先验)。
- team/agent 需指向一个含「评审员(具备 code_review 技能)」的真实团队;不传则尝试 default。
"""
import argparse
import json
import os
import sys
import time
import http.cookiejar
import urllib.request
import urllib.error

ROOT_DEFAULT = "http://localhost:8080/api/v1"
SCENARIO = "code_review_delivery"
CR_BASELINE = 0.45
CR_TREATMENT = 0.85

_JAR = http.cookiejar.CookieJar()
_OPENER = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(_JAR))
_CSRF = None


def _raw(method, url, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    if _CSRF and method in ("POST", "PUT", "DELETE", "PATCH"):
        req.add_header("X-CSRF-Token", _CSRF)
    try:
        resp = _OPENER.open(req, timeout=120)
        txt = resp.read().decode()
        return (json.loads(txt) if txt else {}), resp.status
    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read().decode()), e.code
        except Exception:
            return {"error": str(e)}, e.code
    except Exception as e:
        return {"error": str(e)}, 0


def bootstrap_auth(root):
    """注册一次性用户 → cookie + CSRF(后端 cookie+token 鉴权)。"""
    global _CSRF
    user = f"loopcheck_{int(time.time())}"
    pw = "Loop#Check123"
    _raw("POST", f"{root}/auth/register", {"username": user, "password": pw})
    _raw("POST", f"{root}/auth/login", {"username": user, "password": pw})
    cr, _ = _raw("GET", f"{root}/auth/csrf-token")
    _CSRF = cr.get("csrf_token") if isinstance(cr, dict) else None
    return user


def seed_proficiency(team, agent, code_review_prof):
    """用本机 proficiency_store 给评审员设 code_review 熟练度(trial 创建时读为先验)。"""
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "backend"))
    from sandbox.proficiency_store import get_proficiency_store
    store = get_proficiency_store()
    data = store.load_proficiency(team) or {}
    key = f"{agent}::code_review"
    entry = data.get(key, {})
    entry.update({"skill_name": "code_review", "success_rate": code_review_prof,
                  "agent_id": agent, "category": "code_delivery"})
    data[key] = entry
    store.save_proficiency(team, data)


def run_trial(root, team):
    """创建 → 运行 baseline 分支 → evaluate,返回 (total_score, code_review成功率)。"""
    body = {
        "team_id": team,
        "task_goal": {"name": "闭环交叉验证", "description": "structured-code-review 赋予前后对比"},
        "scenario_id": SCENARIO,
        "scenario": SCENARIO,
        "mode": "what_if",
        "max_steps": 130,
        "acceleration": 10000,
        "parallel_branches": 1,
    }
    trial, code = _raw("POST", f"{root}/twin-trials", body)
    if code not in (200, 201):
        raise SystemExit(f"创建试炼失败 HTTP {code}: {trial}")
    tid = trial.get("id") or trial.get("trial_id")
    branches = trial.get("branches") or []
    bid = branches[0] if branches else (trial.get("baseline_branch_id"))
    if not tid or not bid:
        raise SystemExit(f"试炼响应缺 id/branch: {trial}")
    # 跑完 baseline 分支
    _raw("POST", f"{root}/twin-trials/{tid}/branches/{bid}/run", {})
    # evaluate
    ev, _ = _raw("POST", f"{root}/twin-trials/{tid}/evaluate", {})
    total = ev.get("total_score", ev.get("evaluation", {}).get("total_score", 0))
    # code_review 成功率
    stats, _ = _raw("GET", f"{root}/twin-trials/{tid}/skill-stats")
    items = stats.get("items", stats if isinstance(stats, list) else [])
    cr = next((s for s in items if s.get("skill_name") == "code_review"), {})
    cr_rate = cr.get("success_rate", 0)
    return float(total or 0), float(cr_rate or 0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default=ROOT_DEFAULT)
    ap.add_argument("--team", default="default")
    ap.add_argument("--agent", default="", help="评审员 agent_id(具备 code_review 技能)")
    args = ap.parse_args()
    root = args.base_url.rstrip("/")
    if not args.agent:
        raise SystemExit("请用 --agent 指定评审员 agent_id(具备 code_review 技能)")

    user = bootstrap_auth(root)
    print(f"✅ 已鉴权 {user} (csrf={'yes' if _CSRF else 'no'})  团队={args.team} 评审员={args.agent}")

    print(f"\n[baseline] 设 code_review={CR_BASELINE} 后跑真试炼…")
    seed_proficiency(args.team, args.agent, CR_BASELINE)
    b_total, b_cr = run_trial(root, args.team)

    print(f"[treatment] 设 code_review={CR_TREATMENT}(=赋予 structured-code-review 后)再跑…")
    seed_proficiency(args.team, args.agent, CR_TREATMENT)
    t_total, t_cr = run_trial(root, args.team)

    print("\n" + "=" * 60)
    print("技能闭环 · 本机真后端交叉验证 @ code_review_delivery")
    print("-" * 60)
    print(f"{'指标':<20}{'baseline':>12}{'treatment':>12}")
    print(f"{'total_score':<20}{b_total:>12.3f}{t_total:>12.3f}")
    print(f"{'code_review 成功率':<20}{b_cr:>11.1%}{t_cr:>12.1%}")
    print("-" * 60)
    print(f"total_score 提升: {t_total - b_total:+.3f}")
    print(f"code_review 成功率提升: {(t_cr - b_cr) * 100:+.1f} 个百分点")
    print("对照离线 demo: code_review 成功率 +18.3pp(scripts/skill_closed_loop_demo.py)")
    print("=" * 60)
    print("提示:真试炼含随机性,可多跑几次取均值;若 code_review 成功率随 treatment 明显上升即互相印证。")


if __name__ == "__main__":
    main()
