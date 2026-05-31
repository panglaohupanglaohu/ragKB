# -*- coding: utf-8 -*-
"""Cost Policy Engine — Terraform resource cost evaluation rules.

Defines:
- ResourceTypeConfig: optimal configuration for each resource type
- BudgetProfile: budget tracking model
- CostPolicyRule: individual cost policy rule
- CostPolicyEngine: evaluates terraform plan resources against policies
- CostViolation: structured violation record
- CostEvaluationReport: complete evaluation result

Design: pure functions, zero I/O, deterministic, idempotent.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
from datetime import datetime, timezone
import json


# ══════════════════════════════════════════════════════════════════
# Enums & Constants
# ══════════════════════════════════════════════════════════════════


class CostViolationSeverity(str, Enum):
    """Cost violation severity levels."""
    CRITICAL = "critical"   # Auto-block: e.g., budget overrun >20%
    HIGH = "high"           # Auto-block: e.g., non-optimal instance type
    MEDIUM = "medium"       # Warning: e.g., oversized storage
    LOW = "low"             # Advisory: e.g., missing cost tag
    INFO = "info"           # Informational


class ViolationType(str, Enum):
    """Types of cost violations."""
    OVER_BUDGET = "over_budget"                 # Exceeds budget limit
    NON_OPTIMAL_INSTANCE = "non_optimal_instance"  # Wrong instance family/size
    OVER_PROVISIONED = "over_provisioned"       # > 80% unused capacity
    MISSING_COST_TAG = "missing_cost_tag"       # No cost allocation tag
    WRONG_STORAGE_TIER = "wrong_storage_tier"   # Premium tier for cold data
    WRONG_REGION = "wrong_region"               # Expensive region
    RESERVED_INSTANCE_MISSING = "reserved_instance_missing"  # On-demand instead of RI
    ORPHAN_RESOURCE = "orphan_resource"         # Unattached resource
    EXCEEDS_QUOTA = "exceeds_quota"             # Over provisioned count
    RETENTION_OVERKILL = "retention_overkill"   # Excessive backup retention


class GateDecision(str, Enum):
    """Final gate decision."""
    PASS = "pass"           # All checks passed, proceed
    WARN = "warn"           # Warnings only, proceed with caution
    BLOCK = "block"         # Block deployment


# ══════════════════════════════════════════════════════════════════
# Data Models
# ══════════════════════════════════════════════════════════════════


@dataclass
class ResourceTypeConfig:
    """Optimal configuration for a specific resource type.

    Args:
        resource_type: Terraform resource type (e.g., "aws_instance")
        allowed_instance_families: Allowed instance families (e.g., ["t3", "t4g", "m6i"])
        max_instance_size: Maximum allowed size (e.g., "2xlarge")
        recommended_storage_tier: Recommended storage tier
        max_storage_gb: Maximum storage in GB
        cost_per_unit_hourly: Estimated hourly cost per unit
        required_tags: Tags that must be present
        max_count: Maximum number of instances
        blocked_regions: Regions not allowed for this resource
        notes: Human-readable notes
    """
    resource_type: str
    allowed_instance_families: List[str] = field(default_factory=list)
    max_instance_size: str = "4xlarge"
    recommended_storage_tier: str = "gp3"
    max_storage_gb: int = 1000
    cost_per_unit_hourly: float = 0.0
    required_tags: List[str] = field(default_factory=lambda: ["Environment", "CostCenter", "Owner"])
    max_count: int = 10
    blocked_regions: List[str] = field(default_factory=list)
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "resource_type": self.resource_type,
            "allowed_instance_families": self.allowed_instance_families,
            "max_instance_size": self.max_instance_size,
            "recommended_storage_tier": self.recommended_storage_tier,
            "max_storage_gb": self.max_storage_gb,
            "cost_per_unit_hourly": self.cost_per_unit_hourly,
            "required_tags": self.required_tags,
            "max_count": self.max_count,
            "blocked_regions": self.blocked_regions,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ResourceTypeConfig":
        return cls(
            resource_type=data["resource_type"],
            allowed_instance_families=data.get("allowed_instance_families", []),
            max_instance_size=data.get("max_instance_size", "4xlarge"),
            recommended_storage_tier=data.get("recommended_storage_tier", "gp3"),
            max_storage_gb=data.get("max_storage_gb", 1000),
            cost_per_unit_hourly=data.get("cost_per_unit_hourly", 0.0),
            required_tags=data.get("required_tags", ["Environment", "CostCenter", "Owner"]),
            max_count=data.get("max_count", 10),
            blocked_regions=data.get("blocked_regions", []),
            notes=data.get("notes", ""),
        )


@dataclass
class BudgetProfile:
    """Budget tracking profile.

    Args:
        project_id: Project identifier
        monthly_budget_usd: Monthly budget in USD
        current_spend_usd: Current month spend
        alert_threshold_pct: Alert when spend reaches this % of budget
        block_threshold_pct: Block when spend reaches this % of budget
        estimated_new_cost_usd: Estimated cost of pending changes
        currency: Currency code
    """
    project_id: str = ""
    monthly_budget_usd: float = 0.0
    current_spend_usd: float = 0.0
    alert_threshold_pct: float = 80.0
    block_threshold_pct: float = 100.0
    estimated_new_cost_usd: float = 0.0
    currency: str = "USD"

    @property
    def total_projected(self) -> float:
        return self.current_spend_usd + self.estimated_new_cost_usd

    @property
    def utilization_pct(self) -> float:
        if self.monthly_budget_usd <= 0:
            return 0.0
        return (self.current_spend_usd / self.monthly_budget_usd) * 100.0

    @property
    def projected_utilization_pct(self) -> float:
        if self.monthly_budget_usd <= 0:
            return 0.0
        return (self.total_projected / self.monthly_budget_usd) * 100.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_id": self.project_id,
            "monthly_budget_usd": self.monthly_budget_usd,
            "current_spend_usd": self.current_spend_usd,
            "alert_threshold_pct": self.alert_threshold_pct,
            "block_threshold_pct": self.block_threshold_pct,
            "estimated_new_cost_usd": self.estimated_new_cost_usd,
            "currency": self.currency,
            "total_projected": self.total_projected,
            "utilization_pct": self.utilization_pct,
            "projected_utilization_pct": self.projected_utilization_pct,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BudgetProfile":
        return cls(
            project_id=data.get("project_id", ""),
            monthly_budget_usd=data.get("monthly_budget_usd", 0.0),
            current_spend_usd=data.get("current_spend_usd", 0.0),
            alert_threshold_pct=data.get("alert_threshold_pct", 80.0),
            block_threshold_pct=data.get("block_threshold_pct", 100.0),
            estimated_new_cost_usd=data.get("estimated_new_cost_usd", 0.0),
            currency=data.get("currency", "USD"),
        )


@dataclass
class CostViolation:
    """A single cost policy violation.

    Args:
        violation_type: Type of violation
        severity: Severity level
        resource_address: Terraform resource address
        resource_type: Terraform resource type
        message: Human-readable violation description
        expected: Expected value/configuration
        actual: Actual value/configuration
        estimated_cost_impact_usd: Estimated monthly cost impact
        suggestion: Remediation suggestion
        policy_rule_id: ID of the policy rule that triggered this
    """
    violation_type: ViolationType
    severity: CostViolationSeverity
    resource_address: str = ""
    resource_type: str = ""
    message: str = ""
    expected: str = ""
    actual: str = ""
    estimated_cost_impact_usd: float = 0.0
    suggestion: str = ""
    policy_rule_id: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "violation_type": self.violation_type.value,
            "severity": self.severity.value,
            "resource_address": self.resource_address,
            "resource_type": self.resource_type,
            "message": self.message,
            "expected": self.expected,
            "actual": self.actual,
            "estimated_cost_impact_usd": self.estimated_cost_impact_usd,
            "suggestion": self.suggestion,
            "policy_rule_id": self.policy_rule_id,
        }

    def is_blocking(self) -> bool:
        return self.severity in (CostViolationSeverity.CRITICAL, CostViolationSeverity.HIGH)


@dataclass
class CostEvaluationReport:
    """Complete cost evaluation report.

    Args:
        report_id: Unique report identifier
        project_id: Project identifier
        terraform_plan_hash: Hash of the terraform plan for idempotency
        total_resources_evaluated: Number of resources evaluated
        total_resources_changed: Number of resources being changed
        violations: List of violations found
        estimated_monthly_cost_usd: Estimated monthly cost
        estimated_cost_change_usd: Estimated cost change
        budget_profile: Budget profile used
        decision: Final gate decision
        blocked_by: List of violation types that caused the block
        warnings: List of warning messages
        timestamp: Evaluation timestamp
        metadata: Additional metadata
    """
    report_id: str = ""
    project_id: str = ""
    terraform_plan_hash: str = ""
    total_resources_evaluated: int = 0
    total_resources_changed: int = 0
    violations: List[CostViolation] = field(default_factory=list)
    estimated_monthly_cost_usd: float = 0.0
    estimated_cost_change_usd: float = 0.0
    budget_profile: Optional[BudgetProfile] = None
    decision: GateDecision = GateDecision.PASS
    blocked_by: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def critical_count(self) -> int:
        return sum(1 for v in self.violations if v.severity == CostViolationSeverity.CRITICAL)

    @property
    def high_count(self) -> int:
        return sum(1 for v in self.violations if v.severity == CostViolationSeverity.HIGH)

    @property
    def medium_count(self) -> int:
        return sum(1 for v in self.violations if v.severity == CostViolationSeverity.MEDIUM)

    @property
    def low_count(self) -> int:
        return sum(1 for v in self.violations if v.severity == CostViolationSeverity.LOW)

    @property
    def is_blocked(self) -> bool:
        return self.decision == GateDecision.BLOCK

    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id,
            "project_id": self.project_id,
            "terraform_plan_hash": self.terraform_plan_hash,
            "total_resources_evaluated": self.total_resources_evaluated,
            "total_resources_changed": self.total_resources_changed,
            "violations": [v.to_dict() for v in self.violations],
            "estimated_monthly_cost_usd": self.estimated_monthly_cost_usd,
            "estimated_cost_change_usd": self.estimated_cost_change_usd,
            "budget_profile": self.budget_profile.to_dict() if self.budget_profile else None,
            "decision": self.decision.value,
            "blocked_by": self.blocked_by,
            "warnings": self.warnings,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
            "violations_summary": {
                "critical": self.critical_count,
                "high": self.high_count,
                "medium": self.medium_count,
                "low": self.low_count,
                "total": len(self.violations),
            },
        }


# ══════════════════════════════════════════════════════════════════
# Instance Size Comparator
# ══════════════════════════════════════════════════════════════════


# Ordered list of instance sizes from smallest to largest
_INSTANCE_SIZE_ORDER: List[str] = [
    "nano", "micro", "small", "medium", "large",
    "xlarge", "2xlarge", "3xlarge", "4xlarge",
    "6xlarge", "8xlarge", "9xlarge", "10xlarge",
    "12xlarge", "16xlarge", "18xlarge", "24xlarge",
    "32xlarge", "48xlarge", "56xlarge", "112xlarge",
    "metal",
]


def _instance_size_index(size: str) -> int:
    """Get the ordinal index of an instance size."""
    size_lower = size.lower().strip()
    try:
        return _INSTANCE_SIZE_ORDER.index(size_lower)
    except ValueError:
        # Try fuzzy matching: strip prefixes like "db.", "cache."
        for i, known in enumerate(_INSTANCE_SIZE_ORDER):
            if size_lower.endswith(known):
                return i
        return -1


def _get_instance_family(instance_type: str) -> str:
    """Extract the instance family from an instance type string.

    Examples:
        "t3.medium" -> "t3"
        "m6i.2xlarge" -> "m6i"
        "db.r6g.large" -> "r6g"
        "Standard_D4" -> "Standard_D"
        "Standard_DC2s" -> "Standard_DC"
        "e2-medium" -> "e2"
    """
    # Handle AWS-style (dot-separated) names
    parts = instance_type.replace("db.", "").replace("cache.", "").split(".")
    if len(parts) >= 2:
        return parts[0]

    # Handle Azure-style VM sizes: Standard_D4, Standard_D4_v3, Standard_DC2s
    # Pattern: Standard_{Family}{digits}[_variant]
    import re
    azure_match = re.match(r'(Standard_[A-Z]+)\d', instance_type)
    if azure_match:
        return azure_match.group(1)

    # Handle GCP-style machine types: e2-medium, n2-standard-4
    gcp_match = re.match(r'^([a-z]+\d+)-', instance_type)
    if gcp_match:
        return gcp_match.group(1)

    return parts[0] if parts else ""


def _get_instance_size(instance_type: str) -> str:
    """Extract the instance size from an instance type string.

    Examples:
        "t3.medium" -> "medium"
        "m6i.2xlarge" -> "2xlarge"
        "db.r6g.large" -> "large"
        "Standard_D4" -> "4"
        "Standard_D4_v3" -> "4_v3"
        "e2-medium" -> "medium"
    """
    # Handle AWS-style (dot-separated) names
    parts = instance_type.replace("db.", "").replace("cache.", "").split(".")
    if len(parts) >= 2:
        return parts[-1]

    # Handle Azure-style VM sizes: Standard_D4, Standard_D4_v3
    # Pattern: Standard_{Family}{digits}[_variant]
    import re
    azure_match = re.match(r'Standard_[A-Z]+(\d[\w_]*)', instance_type)
    if azure_match:
        return azure_match.group(1)

    # Handle GCP-style machine types: e2-medium, n2-standard-4
    gcp_match = re.match(r'^[a-z]+\d+-(.+)', instance_type)
    if gcp_match:
        return gcp_match.group(1)

    return ""


# ══════════════════════════════════════════════════════════════════
# Default Policy Catalog
# ══════════════════════════════════════════════════════════════════


def _build_default_resource_configs() -> Dict[str, ResourceTypeConfig]:
    """Build the default catalog of optimal resource configurations."""
    return {
        # AWS
        "aws_instance": ResourceTypeConfig(
            resource_type="aws_instance",
            allowed_instance_families=[
                "t3", "t4g",           # General purpose (burstable)
                "m6i", "m6g", "m7i", "m7g",  # General purpose
                "c6i", "c6g", "c7i", "c7g",  # Compute optimized
                "r6i", "r6g", "r7i", "r7g",  # Memory optimized
            ],
            max_instance_size="8xlarge",
            required_tags=["Environment", "CostCenter", "Owner", "Name"],
            max_count=50,
            notes="Prefer graviton (g) instances for 20% cost savings",
        ),
        "aws_db_instance": ResourceTypeConfig(
            resource_type="aws_db_instance",
            allowed_instance_families=["t3", "t4g", "m6i", "m6g", "r6i", "r6g"],
            max_instance_size="4xlarge",
            max_storage_gb=5000,
            required_tags=["Environment", "CostCenter", "Owner", "Name"],
            max_count=20,
        ),
        "aws_rds_cluster_instance": ResourceTypeConfig(
            resource_type="aws_rds_cluster_instance",
            allowed_instance_families=["t3", "t4g", "m6i", "m6g", "r6i", "r6g"],
            max_instance_size="4xlarge",
            required_tags=["Environment", "CostCenter", "Owner", "Name"],
            max_count=20,
        ),
        "aws_elasticache_cluster": ResourceTypeConfig(
            resource_type="aws_elasticache_cluster",
            allowed_instance_families=["t3", "t4g", "m6i", "m6g", "r6i", "r6g"],
            max_instance_size="4xlarge",
            required_tags=["Environment", "CostCenter", "Owner", "Name"],
            max_count=10,
        ),
        "aws_eks_node_group": ResourceTypeConfig(
            resource_type="aws_eks_node_group",
            allowed_instance_families=["t3", "t4g", "m6i", "m6g", "c6i", "c6g"],
            max_instance_size="4xlarge",
            required_tags=["Environment", "CostCenter", "Owner", "Name"],
            max_count=30,
        ),
        # Azure
        "azurerm_virtual_machine": ResourceTypeConfig(
            resource_type="azurerm_virtual_machine",
            allowed_instance_families=[
                "Standard_B", "Standard_D", "Standard_E",
                "Standard_F", "Standard_DC",
            ],
            max_instance_size="Standard_D16",
            required_tags=["Environment", "CostCenter", "Owner"],
            max_count=50,
            notes="Prefer B-series for burstable; D/E/F for production",
        ),
        "azurerm_kubernetes_cluster_node_pool": ResourceTypeConfig(
            resource_type="azurerm_kubernetes_cluster_node_pool",
            allowed_instance_families=["Standard_B", "Standard_D", "Standard_F"],
            max_instance_size="Standard_D8",
            required_tags=["Environment", "CostCenter", "Owner"],
            max_count=30,
        ),
        # GCP
        "google_compute_instance": ResourceTypeConfig(
            resource_type="google_compute_instance",
            allowed_instance_families=[
                "e2", "n2", "n2d", "t2d", "t2a",
                "c2", "c3", "m2", "m3",
            ],
            max_instance_size="n2-standard-32",
            required_tags=["environment", "cost-center", "owner"],
            max_count=50,
        ),
        # Storage resources
        "aws_s3_bucket": ResourceTypeConfig(
            resource_type="aws_s3_bucket",
            required_tags=["Environment", "CostCenter", "Owner", "Name"],
            max_count=100,
            notes="Use Intelligent-Tiering for unknown access patterns",
        ),
        "aws_ebs_volume": ResourceTypeConfig(
            resource_type="aws_ebs_volume",
            max_storage_gb=500,
            recommended_storage_tier="gp3",
            required_tags=["Environment", "CostCenter", "Owner", "Name"],
            max_count=50,
        ),
        # Load balancers
        "aws_lb": ResourceTypeConfig(
            resource_type="aws_lb",
            required_tags=["Environment", "CostCenter", "Owner", "Name"],
            max_count=20,
        ),
        # NAT Gateways (expensive!)
        "aws_nat_gateway": ResourceTypeConfig(
            resource_type="aws_nat_gateway",
            max_count=3,
            required_tags=["Environment", "CostCenter", "Owner", "Name"],
            notes="NAT Gateways cost ~$32/month each; prefer VPC endpoints",
        ),
    }


# ══════════════════════════════════════════════════════════════════
# Cost Policy Engine (Pure Functions)
# ══════════════════════════════════════════════════════════════════


@dataclass
class CostPolicyEngine:
    """Pure-function cost policy evaluation engine.

    Evaluates a terraform plan against cost policies and budget constraints.
    No I/O, no side effects, deterministic.
    """

    resource_configs: Dict[str, ResourceTypeConfig] = field(default_factory=_build_default_resource_configs)
    default_budget_profile: Optional[BudgetProfile] = None

    def evaluate_terraform_plan(
        self,
        plan_json: Dict[str, Any],
        budget_profile: Optional[BudgetProfile] = None,
        project_id: str = "",
    ) -> CostEvaluationReport:
        """Evaluate a terraform plan JSON against cost policies.

        Args:
            plan_json: Terraform plan JSON (terraform show -json)
            budget_profile: Budget constraints (uses default if None)
            project_id: Project identifier

        Returns:
            CostEvaluationReport with all violations and decision
        """
        import hashlib
        plan_hash = hashlib.sha256(json.dumps(plan_json, sort_keys=True).encode()).hexdigest()[:16]

        report = CostEvaluationReport(
            report_id=f"COST-{plan_hash[:8]}",
            project_id=project_id,
            terraform_plan_hash=plan_hash,
        )

        budget = budget_profile or self.default_budget_profile

        # Extract resources from plan
        resource_changes = self._extract_resource_changes(plan_json)
        report.total_resources_evaluated = len(resource_changes)
        report.total_resources_changed = sum(
            1 for r in resource_changes
            if r.get("change", {}).get("actions", []) not in (["no-op"], [])
        )

        # Run all checks
        violations: List[CostViolation] = []

        for resource in resource_changes:
            violations.extend(self._check_resource(resource))

        # Budget check
        if budget:
            budget_violations = self._check_budget(resource_changes, budget)
            violations.extend(budget_violations)
            report.budget_profile = budget
            report.estimated_monthly_cost_usd = self._estimate_monthly_cost(resource_changes)
            report.estimated_cost_change_usd = budget.estimated_new_cost_usd
        else:
            report.estimated_monthly_cost_usd = self._estimate_monthly_cost(resource_changes)

        report.violations = violations

        # Determine decision
        blocking_violations = [v for v in violations if v.is_blocking()]
        if blocking_violations:
            report.decision = GateDecision.BLOCK
            report.blocked_by = sorted(set(
                list({v.violation_type.value for v in blocking_violations})
            ))
        elif violations:
            report.decision = GateDecision.WARN
            report.warnings = [v.message for v in violations]
        else:
            report.decision = GateDecision.PASS

        return report

    def evaluate_terraform_plan_json(
        self,
        plan_json_str: str,
        budget_profile: Optional[BudgetProfile] = None,
        project_id: str = "",
    ) -> CostEvaluationReport:
        """Evaluate a terraform plan from a JSON string.

        Args:
            plan_json_str: Terraform plan JSON string
            budget_profile: Budget constraints
            project_id: Project identifier

        Returns:
            CostEvaluationReport
        """
        plan_json = json.loads(plan_json_str)
        return self.evaluate_terraform_plan(plan_json, budget_profile, project_id)

    # ── Internal: Resource Extraction ──────────────────────────

    def _extract_resource_changes(self, plan_json: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract resource changes from a terraform plan JSON."""
        # Support both formats: top-level "resource_changes" and nested under "planned_values"
        resources = []

        # Format 1: Standard terraform JSON plan
        if "resource_changes" in plan_json:
            resources = plan_json["resource_changes"]
        elif "planned_values" in plan_json:
            pv = plan_json["planned_values"]
            if "root_module" in pv:
                resources = self._extract_from_module(pv["root_module"])
        elif "resources" in plan_json:
            # Simplified format
            resources = plan_json["resources"]

        return resources

    def _extract_from_module(self, module: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Recursively extract resources from a terraform module."""
        resources = []
        if "resources" in module:
            for res in module["resources"]:
                resources.append({
                    "address": res.get("address", ""),
                    "type": res.get("type", ""),
                    "name": res.get("name", ""),
                    "provider_name": res.get("provider_name", ""),
                    "change": {"actions": ["create"]},  # Simplified
                    "values": res.get("values", {}),
                })
        if "child_modules" in module:
            for child in module["child_modules"]:
                resources.extend(self._extract_from_module(child))
        return resources

    # ── Internal: Resource Checks ─────────────────────────────

    def _check_resource(self, resource: Dict[str, Any]) -> List[CostViolation]:
        """Run all cost policy checks on a single resource."""
        violations: List[CostViolation] = []
        resource_type = resource.get("type", "")
        address = resource.get("address", "")
        values = resource.get("values", {})
        change = resource.get("change", {})
        actions = change.get("actions", ["no-op"])

        # Skip no-op resources
        if actions == ["no-op"]:
            return []

        # Get resource config if available
        config = self.resource_configs.get(resource_type)

        # Check instance type
        violations.extend(self._check_instance_type(resource_type, address, values, config))

        # Check required tags
        violations.extend(self._check_tags(resource_type, address, values, config))

        # Check count limits
        violations.extend(self._check_count(resource_type, address, values, config))

        # Check storage tier for relevant resources
        violations.extend(self._check_storage_tier(resource_type, address, values, config))

        # Check storage size
        violations.extend(self._check_storage_size(resource_type, address, values, config))

        # Check for expensive NAT gateways
        violations.extend(self._check_nat_gateway(resource_type, address, values))

        # Check for orphan resources (resources being destroyed without replacement)
        if "delete" in actions and "create" not in actions:
            violations.append(CostViolation(
                violation_type=ViolationType.ORPHAN_RESOURCE,
                severity=CostViolationSeverity.LOW,
                resource_address=address,
                resource_type=resource_type,
                message=f"Resource {address} is being destroyed",
                suggestion="Ensure this resource is intentionally being decommissioned",
                policy_rule_id="orphan-check",
            ))

        return violations

    def _check_instance_type(
        self,
        resource_type: str,
        address: str,
        values: Dict[str, Any],
        config: Optional[ResourceTypeConfig],
    ) -> List[CostViolation]:
        """Check that the instance type is allowed and optimal."""
        violations: List[CostViolation] = []

        # Find instance_type field
        instance_type = values.get("instance_type", "")
        if not instance_type:
            # Try vm_size for Azure
            instance_type = values.get("vm_size", "")
        if not instance_type:
            # Try machine_type for GCP
            instance_type = values.get("machine_type", "")

        if not instance_type:
            return violations  # No instance type to check

        if config is None:
            return violations  # No config to check against

        # Check instance family
        family = _get_instance_family(instance_type)
        if config.allowed_instance_families and family not in config.allowed_instance_families:
            violations.append(CostViolation(
                violation_type=ViolationType.NON_OPTIMAL_INSTANCE,
                severity=CostViolationSeverity.HIGH,
                resource_address=address,
                resource_type=resource_type,
                message=f"Instance family '{family}' is not in allowed list for {resource_type}",
                expected=f"Allowed families: {', '.join(config.allowed_instance_families[:5])}",
                actual=instance_type,
                estimated_cost_impact_usd=50.0,
                suggestion=f"Switch to an allowed instance family: {config.allowed_instance_families[0] if config.allowed_instance_families else 't3'}",
                policy_rule_id="instance-family-check",
            ))

        # Check instance size
        size = _get_instance_size(instance_type)
        max_size = config.max_instance_size
        max_size_idx = _instance_size_index(max_size)
        actual_size_idx = _instance_size_index(size)

        if actual_size_idx >= 0 and max_size_idx >= 0 and actual_size_idx > max_size_idx:
            violations.append(CostViolation(
                violation_type=ViolationType.OVER_PROVISIONED,
                severity=CostViolationSeverity.HIGH,
                resource_address=address,
                resource_type=resource_type,
                message=f"Instance size '{size}' exceeds maximum allowed '{max_size}'",
                expected=max_size,
                actual=size,
                estimated_cost_impact_usd=100.0,
                suggestion=f"Downsize to {max_size} or smaller",
                policy_rule_id="instance-size-check",
            ))

        return violations

    def _check_tags(
        self,
        resource_type: str,
        address: str,
        values: Dict[str, Any],
        config: Optional[ResourceTypeConfig],
    ) -> List[CostViolation]:
        """Check that required tags are present."""
        violations: List[CostViolation] = []

        if config is None:
            return violations

        if not config.required_tags:
            return violations

        # Get tags from values
        tags = values.get("tags", {})
        if isinstance(tags, list):
            # Some TF formats use list of {key, value} dicts
            tag_keys = {t.get("key", "") for t in tags if isinstance(t, dict)}
        elif isinstance(tags, dict):
            tag_keys = set(tags.keys())
        else:
            tag_keys = set()

        # Also check tag block format
        if not tag_keys and "tag" in values:
            tag_list = values.get("tag", [])
            if isinstance(tag_list, list):
                tag_keys = {t.get("key", "") for t in tag_list if isinstance(t, dict)}

        missing_tags = set(config.required_tags) - tag_keys

        # Case-insensitive check
        tag_keys_lower = {k.lower() for k in tag_keys}
        truly_missing = [
            t for t in missing_tags
            if t.lower() not in tag_keys_lower
        ]

        if truly_missing:
            violations.append(CostViolation(
                violation_type=ViolationType.MISSING_COST_TAG,
                severity=CostViolationSeverity.MEDIUM,
                resource_address=address,
                resource_type=resource_type,
                message=f"Missing required cost allocation tags: {', '.join(truly_missing)}",
                expected=f"Tags: {', '.join(config.required_tags)}",
                actual=f"Found: {', '.join(sorted(tag_keys)) if tag_keys else 'none'}",
                suggestion=f"Add tags: {', '.join(truly_missing)}",
                policy_rule_id="required-tags-check",
            ))

        return violations

    def _check_count(
        self,
        resource_type: str,
        address: str,
        values: Dict[str, Any],
        config: Optional[ResourceTypeConfig],
    ) -> List[CostViolation]:
        """Check that resource count is within limits."""
        violations: List[CostViolation] = []

        if config is None:
            return violations

        count = values.get("count", 1)
        if isinstance(count, dict):
            count = 1  # count is a dynamic expression

        if isinstance(count, (int, float)) and count > config.max_count:
            violations.append(CostViolation(
                violation_type=ViolationType.EXCEEDS_QUOTA,
                severity=CostViolationSeverity.HIGH,
                resource_address=address,
                resource_type=resource_type,
                message=f"Resource count {count} exceeds maximum allowed {config.max_count}",
                expected=str(config.max_count),
                actual=str(count),
                estimated_cost_impact_usd=count * 0.1 * config.cost_per_unit_hourly * 730,
                suggestion=f"Reduce count to {config.max_count} or request quota increase",
                policy_rule_id="count-limit-check",
            ))

        return violations

    def _check_storage_tier(
        self,
        resource_type: str,
        address: str,
        values: Dict[str, Any],
        config: Optional[ResourceTypeConfig],
    ) -> List[CostViolation]:
        """Check storage tier for relevant resource types."""
        violations: List[CostViolation] = []

        if config is None:
            return violations

        # Check volume_type for EBS volumes
        if resource_type == "aws_ebs_volume":
            volume_type = values.get("type", values.get("volume_type", "gp2"))
            if volume_type in ("io1", "io2") and config.recommended_storage_tier == "gp3":
                violations.append(CostViolation(
                    violation_type=ViolationType.WRONG_STORAGE_TIER,
                    severity=CostViolationSeverity.MEDIUM,
                    resource_address=address,
                    resource_type=resource_type,
                    message=f"Premium storage tier '{volume_type}' may not be necessary",
                    expected="gp3 (for most workloads)",
                    actual=volume_type,
                    estimated_cost_impact_usd=30.0,
                    suggestion="Use gp3 unless sub-millisecond latency is required",
                    policy_rule_id="storage-tier-check",
                ))

        return violations

    def _check_storage_size(
        self,
        resource_type: str,
        address: str,
        values: Dict[str, Any],
        config: Optional[ResourceTypeConfig],
    ) -> List[CostViolation]:
        """Check storage allocation size."""
        violations: List[CostViolation] = []

        if config is None:
            return violations

        # Check for allocated_storage or size
        storage = values.get("allocated_storage", values.get("size", 0))
        if isinstance(storage, (int, float)) and storage > 0 and storage > config.max_storage_gb:
            violations.append(CostViolation(
                violation_type=ViolationType.OVER_PROVISIONED,
                severity=CostViolationSeverity.MEDIUM,
                resource_address=address,
                resource_type=resource_type,
                message=f"Storage size {storage}GB exceeds recommended maximum {config.max_storage_gb}GB",
                expected=f"≤{config.max_storage_gb}GB",
                actual=f"{storage}GB",
                estimated_cost_impact_usd=storage * 0.08,
                suggestion=f"Reduce to {config.max_storage_gb}GB or justify the extra capacity",
                policy_rule_id="storage-size-check",
            ))

        return violations

    def _check_nat_gateway(
        self,
        resource_type: str,
        address: str,
        values: Dict[str, Any],
    ) -> List[CostViolation]:
        """Check for expensive NAT Gateway resources."""
        violations: List[CostViolation] = []

        if resource_type == "aws_nat_gateway":
            violations.append(CostViolation(
                violation_type=ViolationType.NON_OPTIMAL_INSTANCE,
                severity=CostViolationSeverity.INFO,
                resource_address=address,
                resource_type=resource_type,
                message="NAT Gateway costs ~$32/month + $0.045/GB data processed",
                expected="Consider VPC Endpoints for AWS services",
                actual="NAT Gateway",
                estimated_cost_impact_usd=32.0,
                suggestion="For AWS service access, use VPC Endpoints instead; for internet egress, use NAT Instance as cheaper alternative",
                policy_rule_id="nat-gateway-advisory",
            ))

        return violations

    # ── Internal: Budget Checks ───────────────────────────────

    def _check_budget(
        self,
        resources: List[Dict[str, Any]],
        budget: BudgetProfile,
    ) -> List[CostViolation]:
        """Check budget constraints."""
        violations: List[CostViolation] = []

        if budget.monthly_budget_usd <= 0:
            return violations

        projected_pct = budget.projected_utilization_pct

        if projected_pct > budget.block_threshold_pct:
            violations.append(CostViolation(
                violation_type=ViolationType.OVER_BUDGET,
                severity=CostViolationSeverity.CRITICAL,
                resource_address="budget:" + budget.project_id,
                resource_type="budget_profile",
                message=(
                    f"Projected spend ${budget.total_projected:.2f} "
                    f"({projected_pct:.1f}%) exceeds block threshold "
                    f"${budget.monthly_budget_usd:.2f} ({budget.block_threshold_pct:.0f}%)"
                ),
                expected=f"≤${budget.monthly_budget_usd:.2f}/month",
                actual=f"${budget.total_projected:.2f} projected",
                estimated_cost_impact_usd=budget.total_projected - budget.monthly_budget_usd,
                suggestion="Reduce resource allocation or request budget increase",
                policy_rule_id="budget-block-threshold",
            ))
        elif projected_pct > budget.alert_threshold_pct:
            violations.append(CostViolation(
                violation_type=ViolationType.OVER_BUDGET,
                severity=CostViolationSeverity.MEDIUM,
                resource_address="budget:" + budget.project_id,
                resource_type="budget_profile",
                message=(
                    f"Projected spend ${budget.total_projected:.2f} "
                    f"({projected_pct:.1f}%) exceeds alert threshold "
                    f"({budget.alert_threshold_pct:.0f}%)"
                ),
                expected=f"≤${budget.monthly_budget_usd * budget.alert_threshold_pct / 100:.2f}",
                actual=f"${budget.total_projected:.2f} projected",
                suggestion="Review resource allocation before deploying",
                policy_rule_id="budget-alert-threshold",
            ))

        return violations

    # ── Internal: Cost Estimation ─────────────────────────────

    def _estimate_monthly_cost(self, resources: List[Dict[str, Any]]) -> float:
        """Estimate monthly cost for a set of resources.

        This is a simplified heuristic — production would use actual pricing APIs.
        """
        total = 0.0
        for resource in resources:
            resource_type = resource.get("type", "")
            values = resource.get("values", {})
            config = self.resource_configs.get(resource_type)

            count = values.get("count", 1)
            if isinstance(count, dict):
                count = 1

            base_cost = config.cost_per_unit_hourly if config else 0.1

            # Instance type multiplier
            instance_type = values.get("instance_type", values.get("vm_size", values.get("machine_type", "")))
            size = _get_instance_size(instance_type)
            size_idx = _instance_size_index(size)
            multiplier = 1.0
            if size_idx >= 0:
                # Each size step roughly doubles the cost
                multiplier = 2.0 ** max(0, size_idx - 2)  # medium is baseline at index ~3

            # Storage cost
            storage_gb = values.get("allocated_storage", values.get("size", 0))
            if isinstance(storage_gb, (int, float)):
                total += storage_gb * 0.08  # $0.08/GB/month

            # NAT Gateway
            if resource_type == "aws_nat_gateway":
                total += 32.0  # Fixed $32/month

            # Compute cost
            total += base_cost * 730 * count * multiplier

        return round(total, 2)

    # ── Public Helpers ────────────────────────────────────────

    def get_all_resource_types(self) -> List[str]:
        """Get all known resource types with policies."""
        return sorted(self.resource_configs.keys())

    def get_resource_config(self, resource_type: str) -> Optional[ResourceTypeConfig]:
        """Get the policy config for a specific resource type."""
        return self.resource_configs.get(resource_type)

    def upsert_resource_config(self, config: ResourceTypeConfig) -> None:
        """Add or update a resource type configuration."""
        self.resource_configs[config.resource_type] = config

    def remove_resource_config(self, resource_type: str) -> bool:
        """Remove a resource type configuration."""
        if resource_type in self.resource_configs:
            del self.resource_configs[resource_type]
            return True
        return False

    def to_dict(self) -> Dict[str, Any]:
        """Export all configurations."""
        return {
            "resource_configs": {
                k: v.to_dict() for k, v in self.resource_configs.items()
            },
            "default_budget_profile": self.default_budget_profile.to_dict() if self.default_budget_profile else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CostPolicyEngine":
        """Import configurations from dict."""
        engine = cls()
        if "resource_configs" in data:
            engine.resource_configs = {
                k: ResourceTypeConfig.from_dict(v)
                for k, v in data["resource_configs"].items()
            }
        if "default_budget_profile" in data and data["default_budget_profile"]:
            engine.default_budget_profile = BudgetProfile.from_dict(data["default_budget_profile"])
        return engine
