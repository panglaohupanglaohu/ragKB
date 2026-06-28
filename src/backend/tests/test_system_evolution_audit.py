from __future__ import annotations

from channels.system_evolution import (
    AuditDomain,
    AuditRule,
    EvolutionStatus,
    EvolutionItem,
    Severity,
    SystemEvolutionChannel,
)


def test_run_full_audit_counts_results_and_creates_failed_items():
    channel = SystemEvolutionChannel()
    channel.initialize()
    channel.audit_rules = [
        AuditRule(
            id="pass-rule",
            domain="general",
            title="Pass Rule",
            description="passes",
            target_channel=channel.name,
            check_fn=lambda _: (True, "ok"),
        ),
        AuditRule(
            id="fail-rule",
            domain="general",
            title="Fail Rule",
            description="fails",
            target_channel=channel.name,
            check_fn=lambda _: (False, "needs work"),
        ),
        AuditRule(
            id="skip-rule",
            domain="general",
            title="Skip Rule",
            description="missing channel",
            target_channel="missing-channel",
            check_fn=lambda _: (True, "unused"),
        ),
    ]

    result = channel.run_full_audit()

    assert result["audit_run"] == 1
    assert result["rules_checked"] == 3
    assert result["passed"] == 1
    assert result["failed"] == 1
    assert result["skipped"] == 1
    assert len(result["new_items_created"]) == 1
    assert "compliance_rating" in result
    assert "escalation" in result
    item = channel.evolution_items[result["new_items_created"][0]]
    assert item.title == "Fail Rule"
    assert item.current_behavior == "needs work"
    assert item.build_task_id == "fail-rule"
    assert channel.audit_history[-1]["new_items"] == 1


def test_run_full_audit_does_not_duplicate_open_items_for_same_rule():
    channel = SystemEvolutionChannel()
    channel.initialize()
    channel.audit_rules = [
        AuditRule(
            id="fail-rule",
            domain="general",
            title="Fail Rule",
            description="fails",
            target_channel=channel.name,
            check_fn=lambda _: (False, "still failing"),
        )
    ]

    first = channel.run_full_audit()
    second = channel.run_full_audit()

    assert len(first["new_items_created"]) == 1
    assert second["new_items_created"] == []
    assert len(channel.evolution_items) == 1


def test_run_full_audit_rediscovers_closed_items_for_same_rule():
    channel = SystemEvolutionChannel()
    channel.initialize()
    channel.audit_rules = [
        AuditRule(
            id="fail-rule",
            domain="general",
            title="Fail Rule",
            description="fails",
            target_channel=channel.name,
            check_fn=lambda _: (False, "regressed"),
        )
    ]

    first = channel.run_full_audit()
    channel.evolution_items[first["new_items_created"][0]].status = EvolutionStatus.CLOSED.value
    second = channel.run_full_audit()

    assert len(second["new_items_created"]) == 1
    assert len(channel.evolution_items) == 2


def test_dispatch_all_pending_assigns_agents_and_build_tasks(monkeypatch):
    class FakeBuildManager:
        def __init__(self):
            self.tasks = []

        def assign_task(self, agent_id, task_description):
            self.tasks.append((agent_id, task_description))

    class FakeRegistry:
        def __init__(self, build_manager):
            self.build_manager = build_manager

        def get(self, name):
            if name == "build_team_manager":
                return self.build_manager
            return None

    build_manager = FakeBuildManager()
    monkeypatch.setattr(
        "channels.system_evolution.get_default_registry",
        lambda: FakeRegistry(build_manager),
    )
    channel = SystemEvolutionChannel()
    channel.initialize()
    channel.evolution_items = {
        "evo-general": EvolutionItem(
            id="evo-general",
            title="General Fix",
            audit_domain=AuditDomain.GENERAL.value,
            build_task_id="rule-general",
        ),
        "evo-critical": EvolutionItem(
            id="evo-critical",
            title="Critical Fix",
            audit_domain=AuditDomain.DATACENTER.value,
            severity=Severity.CRITICAL.value,
            build_task_id="rule-critical",
        ),
        "evo-skipped": EvolutionItem(
            id="evo-skipped",
            title="Already Dispatched",
            status=EvolutionStatus.DISPATCHED.value,
        ),
    }

    result = channel.dispatch_all_pending()

    assert result == {"dispatched": ["evo-general", "evo-critical"], "count": 2}
    assert channel.total_dispatched == 2
    assert channel.evolution_items["evo-general"].status == EvolutionStatus.DISPATCHED.value
    assert channel.evolution_items["evo-general"].assigned_agent == "dev_lead"
    assert channel.evolution_items["evo-critical"].assigned_agent == "chief_director"
    assert channel.evolution_items["evo-skipped"].assigned_agent is None
    assert build_manager.tasks == [
        ("dev_lead", "evolution_fix:rule-general:General Fix"),
        ("chief_director", "evolution_fix:rule-critical:Critical Fix"),
    ]


def test_verify_pending_items_skips_missing_verify_test():
    channel = SystemEvolutionChannel()
    channel.initialize()
    channel.evolution_items["evo-missing-verify"] = EvolutionItem(
        id="evo-missing-verify",
        title="Missing Verify",
        status=EvolutionStatus.VERIFY_PENDING.value,
        verify_test_name="missing-test",
    )

    result = channel.verify_all_pending()

    assert result["count"] == 1
    assert result["verified"][0]["item_id"] == "evo-missing-verify"
    assert result["verified"][0]["status"] == "skip"
    assert "missing-test" in result["verified"][0]["reason"]
    assert channel.evolution_items["evo-missing-verify"].status == EvolutionStatus.VERIFY_PENDING.value


def test_close_verified_items_filters_and_uses_default_conclusion():
    channel = SystemEvolutionChannel()
    channel.initialize()
    channel.evolution_items = {
        "evo-close": EvolutionItem(
            id="evo-close",
            title="Close Me",
            status=EvolutionStatus.VERIFIED.value,
            verify_result="passed",
            verify_detail="pytest passed",
            source_plaza_id="plaza-1",
            source_discussion_id="disc-1",
        ),
        "evo-other-source": EvolutionItem(
            id="evo-other-source",
            title="Other Source",
            status=EvolutionStatus.VERIFIED.value,
            source_plaza_id="plaza-2",
            source_discussion_id="disc-1",
        ),
        "evo-not-verified": EvolutionItem(
            id="evo-not-verified",
            title="Not Verified",
            status=EvolutionStatus.DISPATCHED.value,
        ),
    }

    closed = channel.close_verified_items(source_plaza_id="plaza-1")

    item = channel.evolution_items["evo-close"]
    assert closed == ["evo-close"]
    assert item.status == EvolutionStatus.CLOSED.value
    assert item.close_reason == "verified improvement accepted"
    assert item.close_verify_conclusion == "pytest passed"
    assert item.closed_at
    assert channel.total_closed == 1
    assert channel.evolution_items["evo-other-source"].status == EvolutionStatus.VERIFIED.value
    assert channel.evolution_items["evo-not-verified"].status == EvolutionStatus.DISPATCHED.value
