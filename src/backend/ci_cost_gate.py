#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CI/CD Cost Gate CLI — Integration script for CI/CD pipelines.

Usage:
    # Evaluate a terraform plan file
    python ci_cost_gate.py evaluate --plan-file tfplan.json --project-id myproject

    # Evaluate from stdin (pipe terraform show -json output)
    terraform show -json tfplan | python ci_cost_gate.py evaluate --stdin --project-id myproject

    # Health check
    python ci_cost_gate.py health

    # List policies
    python ci_cost_gate.py policies

    # Set budget
    python ci_cost_gate.py set-budget --monthly-budget 5000 --current-spend 2000

    # Get evaluation history
    python ci_cost_gate.py history --project-id myproject

Exit codes:
    0: PASS — all checks passed
    1: WARN — warnings only, proceed with caution
    2: BLOCK — deployment blocked
    3: ERROR — evaluation failed (technical error)

Environment variables:
    COST_GATE_API_URL: Base URL of the cost gate API (default: http://localhost:8000)
    COST_GATE_TIMEOUT: Request timeout in seconds (default: 30)

CI/CD Integration Examples:

    GitHub Actions:
        - name: Cost Gate Check
          run: |
            terraform plan -out=tfplan
            terraform show -json tfplan | python src/backend/ci_cost_gate.py evaluate --stdin
          env:
            COST_GATE_API_URL: ${{ secrets.COST_GATE_API_URL }}

    GitLab CI:
        cost-gate:
          stage: verify
          script:
            - terraform plan -out=tfplan
            - terraform show -json tfplan | python src/backend/ci_cost_gate.py evaluate --stdin
          allow_failure: false  # Block pipeline on non-zero exit

    Jenkins:
        stage('Cost Gate') {
            steps {
                sh '''
                    terraform plan -out=tfplan
                    terraform show -json tfplan | python src/backend/ci_cost_gate.py evaluate --stdin
                '''
            }
        }
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path
from typing import Any, Dict, Optional

# ── Configuration ────────────────────────────────────────────

DEFAULT_API_URL = os.environ.get("COST_GATE_API_URL", "http://localhost:8000")
DEFAULT_TIMEOUT = int(os.environ.get("COST_GATE_TIMEOUT", "30"))


# ══════════════════════════════════════════════════════════════════
# API Client
# ══════════════════════════════════════════════════════════════════


class CostGateClient:
    """Lightweight HTTP client for Cost Gate API."""

    def __init__(self, base_url: str = DEFAULT_API_URL, timeout: int = DEFAULT_TIMEOUT):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _request(
        self,
        method: str,
        path: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make an HTTP request to the cost gate API."""
        url = f"{self.base_url}/api/v1/cost-gate{path}"
        headers = {"Content-Type": "application/json", "Accept": "application/json"}

        body = None
        if data is not None:
            body = json.dumps(data).encode("utf-8")

        req = urllib.request.Request(url, data=body, headers=headers, method=method)

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8") if e.fp else str(e)
            try:
                error_data = json.loads(error_body)
                return {"_error": True, "status_code": e.code, "detail": error_data.get("detail", error_body)}
            except json.JSONDecodeError:
                return {"_error": True, "status_code": e.code, "detail": error_body}
        except urllib.error.URLError as e:
            return {"_error": True, "detail": f"Connection failed: {e.reason}"}

    def health(self) -> Dict[str, Any]:
        return self._request("GET", "/health")

    def evaluate(
        self,
        plan: Optional[Dict[str, Any]] = None,
        plan_json: Optional[str] = None,
        project_id: str = "default",
        budget: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        data: Dict[str, Any] = {"project_id": project_id}
        if plan is not None:
            data["plan"] = plan
        if plan_json is not None:
            data["plan_json"] = plan_json
        if budget is not None:
            data["budget"] = budget
        if metadata is not None:
            data["metadata"] = metadata
        return self._request("POST", "/evaluate", data)

    def list_policies(self, resource_type: Optional[str] = None) -> Dict[str, Any]:
        path = "/policies"
        if resource_type:
            path += f"?resource_type={resource_type}"
        return self._request("GET", path)

    def get_budget(self) -> Dict[str, Any]:
        return self._request("GET", "/budget")

    def set_budget(self, budget_data: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("POST", "/budget", budget_data)

    def history(self, project_id: Optional[str] = None, limit: int = 20) -> Dict[str, Any]:
        params = [f"limit={limit}"]
        if project_id:
            params.append(f"project_id={project_id}")
        path = f"/history?{'&'.join(params)}"
        return self._request("GET", path)


# ══════════════════════════════════════════════════════════════════
# CLI Commands
# ══════════════════════════════════════════════════════════════════


def cmd_evaluate(args) -> int:
    """Evaluate a terraform plan."""
    client = CostGateClient(base_url=args.api_url, timeout=args.timeout)

    # Get plan data
    plan_data = None
    plan_json = None

    if args.stdin:
        plan_json = sys.stdin.read()
        if not plan_json.strip():
            print("❌ ERROR: No data on stdin", file=sys.stderr)
            return 3
    elif args.plan_file:
        plan_path = Path(args.plan_file)
        if not plan_path.exists():
            print(f"❌ ERROR: Plan file not found: {args.plan_file}", file=sys.stderr)
            return 3
        plan_json = plan_path.read_text()
    elif args.plan_json:
        plan_json = args.plan_json
    else:
        print("❌ ERROR: Must provide --plan-file, --plan-json, or --stdin", file=sys.stderr)
        return 3

    # Parse plan if provided as string
    try:
        if plan_json:
            plan_data = json.loads(plan_json)
    except json.JSONDecodeError as e:
        print(f"❌ ERROR: Invalid JSON in plan: {e}", file=sys.stderr)
        return 3

    # Build metadata
    metadata = {}
    if args.commit_sha:
        metadata["commit_sha"] = args.commit_sha
    if args.branch:
        metadata["branch"] = args.branch
    if args.pipeline_id:
        metadata["pipeline_id"] = args.pipeline_id

    # Budget override
    budget = None
    if args.monthly_budget:
        budget = {
            "project_id": args.project_id,
            "monthly_budget_usd": args.monthly_budget,
            "current_spend_usd": args.current_spend or 0,
            "alert_threshold_pct": args.alert_threshold or 80,
            "block_threshold_pct": args.block_threshold or 100,
        }

    # Evaluate
    result = client.evaluate(
        plan=plan_data,
        project_id=args.project_id,
        budget=budget,
        metadata=metadata,
    )

    if result.get("_error"):
        print(f"❌ API ERROR: {result.get('detail', 'Unknown error')}", file=sys.stderr)
        return 3

    # Display result
    decision = result.get("decision", "unknown")
    violations = result.get("violations", [])
    summary = result.get("violations_summary", {})

    if args.format == "json":
        print(json.dumps(result, indent=2))
    elif args.format == "summary":
        _print_summary(result)
    else:
        _print_full_report(result)

    # Return appropriate exit code
    if decision == "pass":
        return 0
    elif decision == "warn":
        return 1
    elif decision == "block":
        return 2
    return 3


def cmd_health(args) -> int:
    """Health check."""
    client = CostGateClient(base_url=args.api_url, timeout=args.timeout)
    result = client.health()

    if result.get("_error"):
        print(f"❌ Health check failed: {result.get('detail')}", file=sys.stderr)
        return 3

    print(f"✅ Cost Gate: {result.get('status', 'unknown')}")
    print(f"   Version: {result.get('version', '?')}")
    print(f"   Policies: {result.get('policies_count', 0)}")
    stats = result.get("stats", {})
    print(f"   Evaluations: {stats.get('total_evaluations', 0)} "
          f"(P:{stats.get('passed', 0)} W:{stats.get('warned', 0)} B:{stats.get('blocked', 0)})")
    return 0


def cmd_policies(args) -> int:
    """List policies."""
    client = CostGateClient(base_url=args.api_url, timeout=args.timeout)
    result = client.list_policies(resource_type=args.resource_type)

    if result.get("_error"):
        print(f"❌ Error: {result.get('detail')}", file=sys.stderr)
        return 3

    if "resource_type" in result:
        # Single policy
        print(json.dumps(result, indent=2))
    else:
        configs = result.get("resource_configs", {})
        print(f"Cost Policies ({len(configs)} resource types):\n")
        for rt, cfg in sorted(configs.items()):
            families = ", ".join(cfg.get("allowed_instance_families", [])[:5])
            if len(cfg.get("allowed_instance_families", [])) > 5:
                families += ", ..."
            print(f"  {rt}:")
            print(f"    Instance families: {families or '(none)'}")
            print(f"    Max size: {cfg.get('max_instance_size', '?')}")
            print(f"    Max count: {cfg.get('max_count', '?')}")
            print(f"    Required tags: {', '.join(cfg.get('required_tags', []))}")
            print()
    return 0


def cmd_budget(args) -> int:
    """Manage budget."""
    client = CostGateClient(base_url=args.api_url, timeout=args.timeout)

    if args.set:
        budget_data = {
            "project_id": args.project_id or "default",
            "monthly_budget_usd": args.monthly_budget,
            "current_spend_usd": args.current_spend or 0,
            "alert_threshold_pct": args.alert_threshold or 80,
            "block_threshold_pct": args.block_threshold or 100,
        }
        result = client.set_budget(budget_data)
        if result.get("_error"):
            print(f"❌ Error: {result.get('detail')}", file=sys.stderr)
            return 3
        print(f"✅ Budget set: ${result.get('monthly_budget_usd', 0):.2f}/month")
    else:
        result = client.get_budget()
        if result.get("_error"):
            print(f"❌ Error: {result.get('detail')}", file=sys.stderr)
            return 3
        print(json.dumps(result, indent=2))
    return 0


def cmd_history(args) -> int:
    """Show evaluation history."""
    client = CostGateClient(base_url=args.api_url, timeout=args.timeout)
    result = client.history(project_id=args.project_id, limit=args.limit)

    if result.get("_error"):
        print(f"❌ Error: {result.get('detail')}", file=sys.stderr)
        return 3

    reports = result.get("reports", [])
    print(f"Evaluation History ({len(reports)} reports):\n")
    for r in reports:
        decision_icon = {"pass": "✅", "warn": "⚠️", "block": "🚫"}.get(r.get("decision", ""), "❓")
        print(f"  {decision_icon} {r.get('report_id', '?')} | {r.get('decision', '?').upper():6s} | "
              f"{r.get('violations_count', 0)} violations | "
              f"${r.get('estimated_monthly_cost_usd', 0):.2f}/mo | "
              f"{r.get('timestamp', '?')[:19]}")
    return 0


# ══════════════════════════════════════════════════════════════════
# Output Formatters
# ══════════════════════════════════════════════════════════════════


def _print_summary(result: Dict[str, Any]) -> None:
    """Print a compact summary."""
    decision = result.get("decision", "unknown")
    violations = result.get("violations", [])
    summary = result.get("violations_summary", {})
    blocked_by = result.get("blocked_by", [])

    icon = {"pass": "✅", "warn": "⚠️", "block": "🚫"}.get(decision, "❓")

    print(f"{icon} COST GATE: {decision.upper()}")
    print(f"   Report: {result.get('report_id', '?')}")
    print(f"   Resources evaluated: {result.get('total_resources_evaluated', 0)}")
    print(f"   Resources changed: {result.get('total_resources_changed', 0)}")
    print(f"   Estimated monthly cost: ${result.get('estimated_monthly_cost_usd', 0):.2f}")
    print(f"   Violations: {summary.get('total', 0)} "
          f"(C:{summary.get('critical', 0)} H:{summary.get('high', 0)} "
          f"M:{summary.get('medium', 0)} L:{summary.get('low', 0)})")

    if blocked_by:
        print(f"   Blocked by: {', '.join(blocked_by)}")

    if violations:
        print(f"\n   Violation details:")
        for v in violations:
            sev_icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🔵", "info": "ℹ️"}.get(
                v.get("severity", ""), "  "
            )
            print(f"   {sev_icon} [{v.get('severity', '?').upper()}] {v.get('resource_address', '?')}")
            print(f"      {v.get('message', '')}")
            if v.get("suggestion"):
                print(f"      💡 {v.get('suggestion')}")


def _print_full_report(result: Dict[str, Any]) -> None:
    """Print a full report."""
    _print_summary(result)


# ══════════════════════════════════════════════════════════════════
# Main CLI
# ══════════════════════════════════════════════════════════════════


def main():
    parser = argparse.ArgumentParser(
        description="CI/CD Cost Gate — Terraform Policy-based resource cost evaluation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exit Codes:
  0: PASS  — all checks passed
  1: WARN  — warnings only
  2: BLOCK — deployment blocked
  3: ERROR — evaluation failed
        """,
    )

    parser.add_argument(
        "--api-url",
        default=DEFAULT_API_URL,
        help=f"Cost Gate API base URL (default: {DEFAULT_API_URL})",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT,
        help=f"Request timeout in seconds (default: {DEFAULT_TIMEOUT})",
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # evaluate
    eval_parser = subparsers.add_parser("evaluate", help="Evaluate a terraform plan")
    eval_parser.add_argument("--plan-file", help="Path to terraform plan JSON file")
    eval_parser.add_argument("--plan-json", help="Terraform plan JSON string")
    eval_parser.add_argument("--stdin", action="store_true", help="Read plan from stdin")
    eval_parser.add_argument("--project-id", default="default", help="Project identifier")
    eval_parser.add_argument("--commit-sha", help="Git commit SHA")
    eval_parser.add_argument("--branch", help="Git branch name")
    eval_parser.add_argument("--pipeline-id", help="CI/CD pipeline ID")
    eval_parser.add_argument("--monthly-budget", type=float, help="Monthly budget in USD")
    eval_parser.add_argument("--current-spend", type=float, help="Current month spend in USD")
    eval_parser.add_argument("--alert-threshold", type=float, help="Alert threshold %")
    eval_parser.add_argument("--block-threshold", type=float, help="Block threshold %")
    eval_parser.add_argument(
        "--format",
        choices=["full", "summary", "json"],
        default="full",
        help="Output format (default: full)",
    )

    # health
    subparsers.add_parser("health", help="Health check")

    # policies
    pol_parser = subparsers.add_parser("policies", help="List cost policies")
    pol_parser.add_argument("--resource-type", help="Filter by resource type")

    # budget
    budget_parser = subparsers.add_parser("budget", help="Get/set budget")
    budget_parser.add_argument("--set", action="store_true", help="Set budget (requires --monthly-budget)")
    budget_parser.add_argument("--project-id", default="default")
    budget_parser.add_argument("--monthly-budget", type=float)
    budget_parser.add_argument("--current-spend", type=float)
    budget_parser.add_argument("--alert-threshold", type=float)
    budget_parser.add_argument("--block-threshold", type=float)

    # history
    hist_parser = subparsers.add_parser("history", help="Evaluation history")
    hist_parser.add_argument("--project-id", help="Filter by project")
    hist_parser.add_argument("--limit", type=int, default=20, help="Max reports")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 3

    # Dispatch
    commands = {
        "evaluate": cmd_evaluate,
        "health": cmd_health,
        "policies": cmd_policies,
        "budget": cmd_budget,
        "history": cmd_history,
    }

    handler = commands.get(args.command)
    if handler:
        try:
            return handler(args)
        except KeyboardInterrupt:
            print("\n⚠️ Interrupted", file=sys.stderr)
            return 3
        except Exception as e:
            print(f"❌ Unexpected error: {e}", file=sys.stderr)
            return 3

    return 3


if __name__ == "__main__":
    sys.exit(main())
