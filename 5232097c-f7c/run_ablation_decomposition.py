# -*- coding: utf-8 -*-
"""Extended ablation: 5-condition decomposition + new metrics for Plaza structural components."""

import re, json, math, sys, statistics
from pathlib import Path

sys.path.insert(0, "/Users/panglaohu/Downloads/AgentsGroup2026/src/backend")
from agents.tse import TSEConfig, TSEPipeline, parse_transcript, validate_skill_fields

# Load discussion transcripts from existing experiment script
import ast

with open(
    "/Users/panglaohu/Downloads/AgentsGroup2026/5232097c-f7c/run_agent_experiments.py"
) as f:
    code = f.read()
tree = ast.parse(code)
DISCUSSIONS = {}
for node in ast.walk(tree):
    if (
        isinstance(node, ast.Assign)
        and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id == "DISCUSSIONS"
    ):
        for elt in node.value.elts:
            key = elt.elts[0].value
            val = elt.elts[1].value
            DISCUSSIONS[key] = val

results_all = {}


# ═══ STEP 1: Parse metrics from each transcript ═══
def parse_utterances(transcript):
    """Extract list of {round, role, role_en, signal, content} from transcript."""
    pattern = r"\[Round (\d+)\] ([^(]+) \(([^,]+), signal=([^)]+)\): (.+)"
    utterances = []
    for line in transcript.strip().split("\n"):
        m = re.match(pattern, line.strip())
        if m:
            utterances.append(
                {
                    "round": int(m.group(1)),
                    "role": m.group(2).strip(),
                    "role_en": m.group(3).strip(),
                    "signal": m.group(4).strip(),
                    "content": m.group(5).strip(),
                }
            )
    return utterances


def compute_metrics(utterances, disc_name):
    """Compute C_role, coverage, CHALLENGE ratio, dominance, entropy, risk coverage, tool omission."""
    n = len(utterances)
    if n == 0:
        return None

    # --- C_role: task-required vs actual key roles ---
    expected_roles = {
        "architect",
        "devops",
        "security",
        "admin",
        "sre",
        "finops",
        "platform",
        "dba",
    }
    actual_key_roles = set(u["role_en"] for u in utterances)
    # Core roles for each discussion based on topic keywords
    topic = disc_name
    if "es_scaling" in topic:
        task_roles = {"architect", "devops", "security"}
    elif "centos" in topic:
        task_roles = {"admin", "security", "devops", "dba"}
    elif "cost_ri" in topic:
        task_roles = {"finops", "architect", "security"}
    elif "monitoring" in topic:
        task_roles = {"sre", "devops", "security"}
    elif "terraform" in topic:
        task_roles = {"platform", "security", "dba"}
    else:
        task_roles = expected_roles

    c_role = len(task_roles) / len(actual_key_roles) if len(actual_key_roles) > 0 else 0

    # Role coverage in task
    role_coverage = (
        len(task_roles & actual_key_roles) / len(task_roles) if task_roles else 0
    )

    # Cross-role CHALLENGE ratio
    challenge_utt = [u for u in utterances if u["signal"] == "challenge"]
    cross_role_challenges = 0
    for cu in challenge_utt:
        # Find previous utterance role
        cu_idx = utterances.index(cu)
        if cu_idx > 0:
            prev_role = utterances[cu_idx - 1]["role_en"]
            if prev_role != cu["role_en"]:
                cross_role_challenges += 1
    challenge_ratio = cross_role_challenges / len(challenge_utt) if challenge_utt else 0

    # Risk boundary coverage: CHALLENGE utterances mentioning constraint/keywords
    risk_keywords = [
        "注意",
        "风险",
        "限制",
        "禁止",
        "必须",
        "不能",
        "约束",
        "安全",
        "回滚",
        "备份",
        "warn",
        "risk",
    ]
    risk_utt_count = sum(
        1 for u in utterances if any(k in u["content"] for k in risk_keywords)
    )
    risk_coverage = risk_utt_count / n if n > 0 else 0

    # Tool/precondition omission rate: count utterances that SHOULD mention tools but don't
    tool_keywords = [
        "aws_cli",
        "boto3",
        "terraform",
        "leapp",
        "ansible",
        "rsync",
        "dnf",
        "cloudwatch",
        "prometheus",
        "git",
        "iamlint",
        "tfsec",
        "checkov",
    ]
    tools_mentioned = set()
    for u in utterances:
        for tk in tool_keywords:
            if tk in u["content"].lower():
                tools_mentioned.add(tk)
    tool_omission = (
        1.0 - (len(tools_mentioned) / len(tool_keywords)) if tool_keywords else 0
    )

    # Single-role dominance: max role utterance count / total
    from collections import Counter

    role_counts = Counter(u["role_en"] for u in utterances)
    max_role_count = role_counts.most_common(1)[0][1] if role_counts else 0
    dominance = max_role_count / n if n > 0 else 1.0

    # Source role entropy (normalized Shannon entropy of role distribution)
    total = sum(role_counts.values())
    entropy = 0.0
    for count in role_counts.values():
        if count > 0:
            p = count / total
            entropy -= p * math.log(p)
    max_entropy = math.log(len(role_counts)) if len(role_counts) > 0 else 1.0
    norm_entropy = entropy / max_entropy if max_entropy > 0 else 0.0

    return {
        "c_role": round(c_role, 3),
        "role_coverage": round(role_coverage, 3),
        "challenge_ratio": round(challenge_ratio, 3),
        "risk_coverage": round(risk_coverage, 3),
        "tool_omission": round(tool_omission, 3),
        "dominance": round(dominance, 3),
        "source_entropy": round(norm_entropy, 3),
        "utterance_count": n,
        "key_roles": sorted(actual_key_roles),
    }


print("=== Phase 1: Compute Metrics from Transcripts ===")
phase1 = {}
for disc_name, transcript in DISCUSSIONS.items():
    utt = parse_utterances(transcript)
    metrics = compute_metrics(utt, disc_name)
    phase1[disc_name] = metrics
    print(
        f"  {disc_name}: C_role={metrics['c_role']}, "
        f"role_cov={metrics['role_coverage']}, challenge_xrole={metrics['challenge_ratio']}, "
        f"risk_cov={metrics['risk_coverage']}, tool_om={metrics['tool_omission']:.2f}, "
        f"dominance={metrics['dominance']}, entropy={metrics['source_entropy']}"
    )

results_all["metrics"] = phase1

# ═══ STEP 2: 5-condition ablation ═══
print("\n=== Phase 2: 5-Condition Ablation ===")


def strip_orid(transcript):
    """Remove round labels, keep content."""
    return re.sub(r"\[Round \d+\] ", "", transcript)


def strip_niche(transcript):
    """Replace specific role names with generic 'agent'."""
    return re.sub(r"\] [^(]+ \([^,]+", "] Agent (agent", transcript)


def strip_signals(transcript):
    """Remove signal= annotations."""
    return re.sub(r", signal=\w+", "", transcript)


def strip_all(transcript):
    """Remove all structural annotations (free chat)."""
    t = re.sub(r"\[Round \d+\] ", "", transcript)
    t = re.sub(r", signal=\w+", "", t)
    t = re.sub(r" \([^)]+\):", ":", t)
    return t


conditions = {
    "A. Plaza完整": lambda t: t,
    "B. 去除ORID": strip_orid,
    "C. 去除Niche": strip_niche,
    "D. 去除信号": strip_signals,
    "E. 自由聊天": strip_all,
}

config = TSEConfig()
pipe = TSEPipeline(config)
ablation_results = []

for cond_name, transform_fn in conditions.items():
    total_skills = 0
    total_completeness = 0
    disc_count = 0
    for disc_name, transcript in DISCUSSIONS.items():
        modified = transform_fn(transcript)
        tr = parse_transcript(modified, source_title=disc_name)
        stages = pipe.encode_stages(tr)
        # Count skills via focus indices
        focus_count = len(stages.get("focus_indices", []))
        # Field completeness: count how many of 5 fields have non-trivial evidence
        n_utt = stages["embeddings"].shape[0]
        # Simple heuristic: completeness = focus_count / max(1, n_utt)
        completeness = focus_count / max(1, n_utt)
        total_skills += max(1, focus_count)  # at least 1 skill per discussion
        total_completeness += completeness
        disc_count += 1

    avg_skills = total_skills / disc_count if disc_count > 0 else 0
    avg_completeness = total_completeness / disc_count if disc_count > 0 else 0
    ablation_results.append(
        {
            "condition": cond_name,
            "skills_per_discussion": round(avg_skills, 2),
            "field_completeness": round(avg_completeness * 100, 1),
            "discussions_tested": disc_count,
        }
    )
    print(
        f"  {cond_name}: skills={avg_skills:.1f}/disc, completeness={avg_completeness * 100:.0f}%"
    )

results_all["ablation"] = ablation_results

# ═══ STEP 3: Compute metric deltas across ablation conditions ═══
print("\n=== Phase 3: Metric Variation by Component ===")
component_contributions = {}
baseline = phase1  # metrics from full Plaza

for disc_name, full_metrics in baseline.items():
    transcript = DISCUSSIONS[disc_name]

    # Compute metrics for each stripped condition
    for cond_name, transform_fn in list(conditions.items())[1:]:  # skip "Full"
        if cond_name not in component_contributions:
            component_contributions[cond_name] = {}

        modified = transform_fn(transcript)
        utt = parse_utterances(modified)
        if not utt:
            continue

        stripped_metrics = compute_metrics(utt, disc_name)

        # Compute delta for each metric
        for metric_name in [
            "c_role",
            "role_coverage",
            "challenge_ratio",
            "risk_coverage",
            "dominance",
            "source_entropy",
        ]:
            if metric_name not in component_contributions[cond_name]:
                component_contributions[cond_name][metric_name] = []

            delta = stripped_metrics[metric_name] - full_metrics[metric_name]
            component_contributions[cond_name][metric_name].append(delta)

# Average deltas
metric_deltas = {}
for cond_name, metrics in component_contributions.items():
    metric_deltas[cond_name] = {}
    for metric_name, deltas in metrics.items():
        if deltas:
            metric_deltas[cond_name][metric_name] = round(statistics.mean(deltas), 3)
    print(f"  {cond_name}: {metric_deltas[cond_name]}")

results_all["metric_deltas"] = metric_deltas

# ═══ Save results ═══
output = Path(
    "/Users/panglaohu/Downloads/AgentsGroup2026/5232097c-f7c/ablation_metrics_results.json"
)
output.write_text(json.dumps(results_all, ensure_ascii=False, indent=2, default=str))
print(f"\nSaved to {output}")

# Summary
print("\n=== Summary ===")
print(f"Plaza metrics computed for {len(phase1)} discussions")
abl = [a for a in ablation_results if "完整" in a["condition"]][0]
print(
    f"Full Plaza baseline: {abl['skills_per_discussion']} skills/disc, {abl['field_completeness']}% completeness"
)
for a in ablation_results:
    if "完整" not in a["condition"]:
        delta_s = a["skills_per_discussion"] - abl["skills_per_discussion"]
        delta_c = a["field_completeness"] - abl["field_completeness"]
        print(
            f"  {a['condition']}: skills {a['skills_per_discussion']} (Δ{delta_s:+.1f}), completeness {a['field_completeness']}% (Δ{delta_c:+.0f}%)"
        )
