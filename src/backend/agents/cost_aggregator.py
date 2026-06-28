# -*- coding: utf-8 -*-
"""Cost Aggregator — OpenCost data polling, label-based aggregation & caching.

Polls the OpenCost /model/allocation API periodically, aggregates costs
by configurable dimensions (service, environment, team, namespace, cluster),
and maintains an in-memory cache for fast dashboard queries.

Architecture:
  1. _CostCache — thread-safe LRU-style cache with TTL
  2. CostAggregator — main service with polling loop and query API
  3. get_cost_aggregator() — singleton accessor
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

try:
    import aiohttp
except Exception:
    aiohttp = None

from .cost_models import (
    AggregatedCostItem,
    CostGranularity,
    CostLabel,
    CostQueryParams,
    CostSummary,
    CostTrendPoint,
    CostTrendSeries,
    PodCostItem,
)

logger = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────

OPENCOST_DEFAULT_URL = "http://localhost:9003"
OPENCOST_ALLOCATION_PATH = "/allocation"
DEFAULT_POLL_INTERVAL_SEC = 300  # 5 minutes
CACHE_TTL_SEC = 600  # 10 minutes
MAX_POD_ITEMS = 50000

# Label keys that OpenCost may expose on Kubernetes pods
COST_LABEL_KEYS = [
    "app", "app_kubernetes_io/name", "application",
    "service", "service_istio_io/canonical-name",
    "environment", "env",
    "team", "owner",
    "component", "tier",
    "namespace", "cluster",
]


class _CostCache:
    """Thread-safe in-memory cache with TTL for cost data."""

    def __init__(self):
        self._pods: List[PodCostItem] = []
        self._fetched_at: float = 0.0
        self._window_start: str = ""
        self._window_end: str = ""

    @property
    def is_fresh(self) -> bool:
        return (time.monotonic() - self._fetched_at) < CACHE_TTL_SEC

    @property
    def age_seconds(self) -> int:
        if self._fetched_at == 0:
            return 999999
        return int(time.monotonic() - self._fetched_at)

    def update(self, pods: List[PodCostItem], window_start: str = "", window_end: str = ""):
        self._pods = pods
        self._fetched_at = time.monotonic()
        self._window_start = window_start
        self._window_end = window_end

    def get_all(self) -> Tuple[List[PodCostItem], str, str]:
        return list(self._pods), self._window_start, self._window_end


class CostAggregator:
    """Aggregates OpenCost allocation data for dashboard queries.

    Supports:
      - Polling OpenCost REST API
      - Label extraction from pod metadata
      - Aggregation by service/env/team/namespace/cluster
      - Trend computation over time windows
      - In-memory caching with TTL
    """

    def __init__(
        self,
        opencost_url: str = OPENCOST_DEFAULT_URL,
        poll_interval: int = DEFAULT_POLL_INTERVAL_SEC,
    ):
        self._opencost_url = opencost_url.rstrip("/")
        self._poll_interval = poll_interval
        self._cache = _CostCache()
        self._opencost_ok: bool = False
        self._last_error: str = ""
        self._poll_task: Optional[asyncio.Task] = None

    # ── Properties ───────────────────────────────────────

    @property
    def opencost_healthy(self) -> bool:
        return self._opencost_ok

    @property
    def last_error(self) -> str:
        return self._last_error

    @property
    def cache_age_seconds(self) -> int:
        return self._cache.age_seconds

    # ── Lifecycle ────────────────────────────────────────

    async def start(self):
        """Start the background polling loop."""
        if aiohttp is None:
            self._opencost_ok = False
            self._last_error = "aiohttp is not installed; OpenCost polling disabled"
            logger.warning("CostAggregator polling disabled: aiohttp is not installed")
            return
        if self._poll_task is not None:
            return
        self._poll_task = asyncio.create_task(self._poll_loop())
        logger.info("CostAggregator polling started (interval=%ds)", self._poll_interval)

    async def stop(self):
        """Stop the background polling loop."""
        if self._poll_task is not None:
            self._poll_task.cancel()
            try:
                await self._poll_task
            except asyncio.CancelledError:
                pass
            self._poll_task = None

    async def _poll_loop(self):
        """Background loop that polls OpenCost periodically."""
        while True:
            try:
                await self._fetch_and_cache()
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.warning("CostAggregator poll failed: %s", exc, exc_info=True)
                self._last_error = str(exc)
                self._opencost_ok = False
            await asyncio.sleep(self._poll_interval)

    # ── OpenCost Communication ───────────────────────────

    async def _fetch_and_cache(self):
        """Fetch allocation data from OpenCost and update cache.
        
        Falls back to mock seed data when OpenCost is unreachable,
        so the dashboard always has numbers to display.
        """
        url = f"{self._opencost_url}{OPENCOST_ALLOCATION_PATH}"
        window = self._build_opencost_window("7d")

        params = {
            "window": window,
            "aggregate": "pod",
            "includeIdle": "false",
            "format": "json",
        }

        # Try real OpenCost first
        if aiohttp is not None:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            pods = self._parse_allocation_response(data)
                            self._cache.update(pods, window_start=window, window_end="now")
                            self._opencost_ok = True
                            self._last_error = ""
                            logger.info(
                                "CostAggregator: fetched %d pod cost items from OpenCost", len(pods)
                            )
                            return
                        else:
                            text = await resp.text()
                            logger.warning("OpenCost returned %d: %s", resp.status, text[:200])
            except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
                logger.warning("CostAggregator: OpenCost unreachable — %s", exc)

        # ══ Mock data fallback DISABLED — only real OpenCost data ══
        # if not self._opencost_ok:
        #     self._last_error = "OpenCost unreachable; showing mock seed data"
        #     self._seed_mock_data(window_start=window, window_end="now")

    # ═══════════════════════════════════════════════════════════════
    # _seed_mock_data() DISABLED — no fake data, OpenCost only
    # ═══════════════════════════════════════════════════════════════
    def _seed_mock_data(self, window_start: str = "", window_end: str = ""):
        """DISABLED: real OpenCost data only."""
        return  # no-op, mock data disabled
        import random
        random.seed(42)  # deterministic seed for stable demo data

        services = [
            ("api-gateway", "platform", "production"),
            ("api-gateway", "platform", "production"),
            ("user-service", "backend", "production"),
            ("user-service", "backend", "production"),
            ("user-service", "backend", "staging"),
            ("order-service", "backend", "production"),
            ("order-service", "backend", "production"),
            ("order-service", "backend", "staging"),
            ("payment-worker", "backend", "production"),
            ("payment-worker", "backend", "production"),
            ("notification-svc", "backend", "production"),
            ("notification-svc", "backend", "staging"),
            ("frontend-web", "frontend", "production"),
            ("frontend-web", "frontend", "production"),
            ("frontend-web", "frontend", "staging"),
            ("admin-dashboard", "frontend", "production"),
            ("admin-dashboard", "frontend", "staging"),
            ("ml-inference", "ai_coding", "production"),
            ("ml-inference", "ai_coding", "staging"),
            ("ml-training", "ai_coding", "production"),
            ("data-pipeline", "data_team", "production"),
            ("data-pipeline", "data_team", "production"),
            ("data-warehouse", "data_team", "production"),
            ("cache-redis", "platform", "production"),
            ("cache-redis", "platform", "production"),
            ("cache-redis", "platform", "staging"),
            ("message-queue", "platform", "production"),
            ("message-queue", "platform", "production"),
            ("monitoring-stack", "platform", "production"),
            ("log-collector", "platform", "production"),
            ("log-collector", "platform", "staging"),
            ("ci-runner", "build_system", "production"),
            ("ci-runner", "build_system", "production"),
            ("ci-runner", "build_system", "staging"),
            ("cdn-edge", "platform", "production"),
            ("cdn-edge", "platform", "production"),
            ("dns-resolver", "platform", "production"),
            ("auth-service", "backend", "production"),
            ("auth-service", "backend", "production"),
            ("search-engine", "backend", "production"),
        ]

        pods = []
        for i, (svc, team, env) in enumerate(services):
            pod_name = f"{svc}-{random.choice(['7d8f','3a2b','9c1e','5f4a','2b6d','8e0c'])}"
            namespace = "default" if env == "production" else env

            # Vary costs per service type
            if "ml-" in svc:
                cpu_cost = round(random.uniform(20, 80), 2)
                ram_cost = round(random.uniform(15, 60), 2)
                gpu_cost = round(random.uniform(50, 200), 2)
            elif "data-" in svc:
                cpu_cost = round(random.uniform(10, 40), 2)
                ram_cost = round(random.uniform(8, 35), 2)
                gpu_cost = 0.0
            elif "cache" in svc or "queue" in svc:
                cpu_cost = round(random.uniform(3, 12), 2)
                ram_cost = round(random.uniform(5, 20), 2)
                gpu_cost = 0.0
            elif "gateway" in svc or "cdn" in svc:
                cpu_cost = round(random.uniform(5, 18), 2)
                ram_cost = round(random.uniform(3, 10), 2)
                gpu_cost = 0.0
            elif "frontend" in svc or "dashboard" in svc or "admin" in svc:
                cpu_cost = round(random.uniform(2, 8), 2)
                ram_cost = round(random.uniform(1, 5), 2)
                gpu_cost = 0.0
            elif "ci-" in svc or "build" in svc:
                cpu_cost = round(random.uniform(8, 25), 2)
                ram_cost = round(random.uniform(6, 20), 2)
                gpu_cost = 0.0
            else:
                cpu_cost = round(random.uniform(4, 20), 2)
                ram_cost = round(random.uniform(3, 15), 2)
                gpu_cost = 0.0

            pv_cost = round(random.uniform(0.5, 8), 2)
            network_cost = round(random.uniform(0.2, 4), 2)
            total_cost = round(cpu_cost + ram_cost + gpu_cost + pv_cost + network_cost, 2)

            pods.append(PodCostItem(
                pod=pod_name,
                namespace=namespace,
                container=svc,
                cpu_cost=cpu_cost,
                ram_cost=ram_cost,
                gpu_cost=gpu_cost,
                pv_cost=pv_cost,
                network_cost=network_cost,
                total_cost=total_cost,
                cpu_core_hours=round(cpu_cost * 24, 2),
                ram_gb_hours=round(ram_cost * 24, 2),
                labels={
                    "service": svc,
                    "environment": env,
                    "team": team,
                    "app": svc,
                },
                window_start=window_start,
                window_end=window_end,
            ))

        pods.sort(key=lambda p: p.total_cost, reverse=True)
        self._cache.update(pods, window_start=window_start, window_end=window_end)

    def _build_opencost_window(self, duration: str) -> str:
        """Build window string for OpenCost API (e.g., '7d')."""
        return duration

    def _parse_allocation_response(self, data: Dict[str, Any]) -> List[PodCostItem]:
        """Parse OpenCost /allocation JSON into PodCostItem list.

        Handles both old (/model/allocation) and new (/allocation) response formats.
        """
        pods: List[PodCostItem] = []
        for entry in self._allocation_items(data):
            for pod_data in self._pod_entry_candidates(entry):
                pod = self._safe_pod_from_entry(pod_data)
                if pod is not None:
                    pods.append(pod)
        return self._sort_and_limit_pods(pods)

    @staticmethod
    def _allocation_items(data: Dict[str, Any]) -> List[Any]:
        items = data if isinstance(data, list) else data.get("data", [])
        if isinstance(items, dict):
            return list(items.values())
        return list(items) if isinstance(items, list) else []

    @staticmethod
    def _is_wrapped_allocation_entry(entry: Dict[str, Any]) -> bool:
        return bool(entry) and all(isinstance(value, dict) for value in entry.values())

    def _pod_entry_candidates(self, entry: Any) -> List[Dict[str, Any]]:
        if not isinstance(entry, dict):
            return []
        if self._is_wrapped_allocation_entry(entry):
            return list(entry.values())
        return [entry]

    def _safe_pod_from_entry(self, entry: Dict[str, Any]) -> Optional[PodCostItem]:
        try:
            return self._pod_from_entry(entry)
        except Exception:
            return None

    @staticmethod
    def _sort_and_limit_pods(pods: List[PodCostItem]) -> List[PodCostItem]:
        pods.sort(key=lambda p: p.total_cost, reverse=True)
        return pods[:MAX_POD_ITEMS]

    def _pod_from_entry(self, entry: Dict[str, Any]) -> Optional[PodCostItem]:
        """Extract a PodCostItem from a single OpenCost allocation entry.

        Handles both old and new OpenCost response formats:
        - Old: costs and metadata may be mixed in properties
        - New: costs at top-level, metadata in properties sub-object
        """
        name = entry.get("name", "")
        props = entry.get("properties", entry)
        labels = self._labels_from_entry(entry, props)
        namespace = labels.get("namespace", props.get("namespace", ""))
        self._apply_namespace_label_fallback(labels, namespace)
        self._apply_team_label_fallback(labels, props, name, namespace)

        cpu_cost = self._entry_cost(entry, props, "cpuCost")
        ram_cost = self._entry_cost(entry, props, "ramCost")
        pv_cost = self._entry_cost(entry, props, "pvCost")
        network_cost = self._entry_cost(entry, props, "networkCost")
        gpu_cost = self._entry_cost(entry, props, "gpuCost")
        total_cost = self._entry_cost(entry, props, "totalCost")

        # If total not provided, sum components
        if total_cost == 0:
            total_cost = cpu_cost + ram_cost + pv_cost + network_cost + gpu_cost

        cpu_core_hours = self._entry_cost(entry, props, "cpuCoreHours")
        ram_gb_hours = self._ram_gb_hours(entry, props)

        namespace = labels.get("namespace", props.get("namespace", ""))
        pod_name = props.get("pod", "") or name.rsplit("/", 1)[-1] if "/" in name else name
        container = props.get("container", entry.get("container", ""))
        window_start, window_end = self._entry_window(entry)

        return PodCostItem(
            pod=pod_name,
            namespace=namespace,
            container=container,
            cpu_cost=round(cpu_cost, 6),
            ram_cost=round(ram_cost, 6),
            pv_cost=round(pv_cost, 6),
            network_cost=round(network_cost, 6),
            gpu_cost=round(gpu_cost, 6),
            total_cost=round(total_cost, 6),
            cpu_core_hours=round(cpu_core_hours, 6),
            ram_gb_hours=round(ram_gb_hours, 6),
            labels=labels,
            window_start=window_start,
            window_end=window_end,
        )

    def _labels_from_entry(self, entry: Dict[str, Any], props: Dict[str, Any]) -> Dict[str, str]:
        labels_raw = props.get("labels", {}) if isinstance(props, dict) else {}
        if not labels_raw:
            labels_raw = entry.get("labels", {})
        return self._normalize_labels(labels_raw)

    @staticmethod
    def _apply_namespace_label_fallback(labels: Dict[str, str], namespace: str) -> None:
        if labels.get("service") or not namespace:
            return
        if namespace == "agentsgroup":
            labels.setdefault("service", "agentsgroup-backend")
            labels.setdefault("app", "agentsgroup2026")
            labels.setdefault("component", "backend")
        elif namespace == "opencost":
            labels.setdefault("service", "opencost")
            labels.setdefault("component", "monitoring")
        elif namespace == "prometheus-system":
            labels.setdefault("service", "prometheus")
            labels.setdefault("component", "monitoring")
        elif namespace == "kube-system":
            labels.setdefault("service", "kubernetes")
            labels.setdefault("component", "infrastructure")
        else:
            labels.setdefault("service", namespace)
        labels.setdefault("environment", "production")

    @staticmethod
    def _apply_team_label_fallback(
        labels: Dict[str, str],
        props: Dict[str, Any],
        name: str,
        namespace: str,
    ) -> None:
        if labels.get("team") and labels.get("team") != "platform":
            return
        pod_name = props.get("pod", name.rsplit("/", 1)[-1] if "/" in name else name)
        # K8s deployment names convert "_" to "-", so pod name
        # "agentsgroup-build-system-xxx" maps to team_id "build_system"
        team_map = {
            "build-system": "build_system",
            "ai-coding": "ai_coding",
            "energy": "energy",
            "xops": "xops",
            "cloud-ops": "cloud_ops",
        }
        for segment, team_id in team_map.items():
            if f"agentsgroup-{segment}-" in pod_name:
                labels.setdefault("team", team_id)
                break
        if not labels.get("team") and namespace == "agentsgroup":
            labels.setdefault("team", "platform")

    @staticmethod
    def _entry_cost(entry: Dict[str, Any], props: Dict[str, Any], key: str) -> float:
        return float(entry.get(key, props.get(key, 0)) or 0)

    def _ram_gb_hours(self, entry: Dict[str, Any], props: Dict[str, Any]) -> float:
        ram_byte_hours = entry.get("ramByteHours", props.get("ramByteHours", 0)) or 0
        if not ram_byte_hours:
            return 0.0
        return float(ram_byte_hours) / (1024 ** 3)

    @staticmethod
    def _entry_window(entry: Dict[str, Any]) -> Tuple[str, str]:
        window = entry.get("window", {})
        if not isinstance(window, dict):
            return "", ""
        return window.get("start", ""), window.get("end", "")

    def _normalize_labels(self, raw_labels: Dict[str, str]) -> Dict[str, str]:
        """Normalize Kubernetes labels to standard cost label keys."""
        normalized: Dict[str, str] = {}
        for key, value in raw_labels.items():
            v = str(value)
            if key in ("app", "app_kubernetes_io/name", "application", "app_name"):
                normalized.setdefault("app", v)
            if key in ("service", "service_istio_io/canonical-name", "svc"):
                normalized.setdefault("service", v)
            if key in ("environment", "env", "stage"):
                normalized.setdefault("environment", v)
            if key in ("team", "owner", "managed_by"):
                normalized.setdefault("team", v)
            if key in ("component", "tier", "part_of"):
                normalized.setdefault("component", v)
            if key in ("namespace", "ns"):
                normalized["namespace"] = v
            if key in ("cluster", "cluster_name"):
                normalized["cluster"] = v
        return normalized

    # ── Query API ────────────────────────────────────────

    async def get_summary(self, params: Optional[CostQueryParams] = None) -> CostSummary:
        """Build a full cost summary for the dashboard."""
        if params is None:
            params = CostQueryParams()

        pods, ws, we = self._cache.get_all()
        if not pods:
            return CostSummary(
                window_start=ws,
                window_end=we,
            )

        # Calculate totals
        total = sum(p.total_cost for p in pods)
        cpu = sum(p.cpu_cost for p in pods)
        ram = sum(p.ram_cost for p in pods)
        pv = sum(p.pv_cost for p in pods)
        net = sum(p.network_cost for p in pods)
        gpu = sum(p.gpu_cost for p in pods)

        # Aggregations
        by_service = self._aggregate(pods, "service", total)
        by_environment = self._aggregate(pods, "environment", total)
        by_team = self._aggregate(pods, "team", total)

        # Trends — compute daily trend for primary aggregation
        trends = self._compute_trends(
            pods, params.aggregation, params.granularity, params.window
        )

        return CostSummary(
            total_cost=round(total, 4),
            cpu_cost=round(cpu, 4),
            ram_cost=round(ram, 4),
            pv_cost=round(pv, 4),
            network_cost=round(net, 4),
            gpu_cost=round(gpu, 4),
            pod_count=len(pods),
            container_count=sum(1 for p in pods if p.container),
            service_count=len(by_service),
            environment_count=len(by_environment),
            team_count=len(by_team),
            namespace_count=len(set(p.namespace for p in pods if p.namespace)),
            window_start=ws,
            window_end=we,
            by_service=by_service[:10],
            by_environment=by_environment[:10],
            by_team=by_team[:10],
            trends=trends,
        )

    def _aggregate(
        self, pods: List[PodCostItem], dimension: str, total: float
    ) -> List[AggregatedCostItem]:
        """Aggregate pod costs by a dimension."""
        buckets: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "cpu": 0.0, "ram": 0.0, "pv": 0.0, "net": 0.0, "gpu": 0.0,
            "total": 0.0, "pods": set(), "containers": set(),
        })

        for pod in pods:
            value = pod.labels.get(dimension, "")
            if not value:
                value = getattr(pod, dimension, "") if hasattr(pod, dimension) else ""
            if not value:
                value = "(unknown)"

            b = buckets[value]
            b["cpu"] += pod.cpu_cost
            b["ram"] += pod.ram_cost
            b["pv"] += pod.pv_cost
            b["net"] += pod.network_cost
            b["gpu"] += pod.gpu_cost
            b["total"] += pod.total_cost
            b["pods"].add(pod.pod)
            if pod.container:
                b["containers"].add(pod.container)

        result = []
        for value, b in buckets.items():
            pct = (b["total"] / total * 100) if total > 0 else 0.0
            result.append(AggregatedCostItem(
                dimension=dimension,
                value=value,
                cpu_cost=round(b["cpu"], 4),
                ram_cost=round(b["ram"], 4),
                pv_cost=round(b["pv"], 4),
                network_cost=round(b["net"], 4),
                gpu_cost=round(b["gpu"], 4),
                total_cost=round(b["total"], 4),
                pod_count=len(b["pods"]),
                container_count=len(b["containers"]),
                percentage=round(pct, 2),
            ))

        result.sort(key=lambda x: x.total_cost, reverse=True)
        return result

    def _compute_trends(
        self,
        pods: List[PodCostItem],
        aggregation: str,
        granularity: str,
        window: str,
    ) -> List[CostTrendSeries]:
        """Compute cost trends over time windows.

        For now, since OpenCost returns window-aggregated data, we simulate
        daily trends by distributing costs across the time window proportionally.
        When OpenCost provides step-level data, this will be enhanced.
        """
        if not pods:
            return []

        # Determine number of days in window
        window_days = self._parse_window_days(window)
        if window_days <= 0:
            window_days = 7

        # Group by aggregation dimension
        grouped: Dict[str, List[PodCostItem]] = defaultdict(list)
        for pod in pods:
            value = pod.labels.get(aggregation, "(unknown)")
            grouped[value].append(pod)

        trends = []
        for value, group_pods in list(grouped.items())[:5]:  # Top 5
            total = sum(p.total_cost for p in group_pods)
            daily_avg = total / window_days if window_days > 0 else total

            # Build trend points (simulated daily distribution)
            points = []
            now = datetime.now(timezone.utc)
            for day_offset in range(window_days, -1, -1):
                day = now - timedelta(days=day_offset)
                # Simple linear distribution
                day_cost = daily_avg
                cpu_day = sum(p.cpu_cost for p in group_pods) / window_days
                ram_day = sum(p.ram_cost for p in group_pods) / window_days

                points.append(CostTrendPoint(
                    timestamp=day.strftime("%Y-%m-%d"),
                    total_cost=round(day_cost, 4),
                    cpu_cost=round(cpu_day, 4),
                    ram_cost=round(ram_day, 4),
                ))

            trends.append(CostTrendSeries(
                dimension=aggregation,
                value=value,
                points=points,
                total=round(total, 4),
                avg_daily=round(daily_avg, 4),
            ))

        trends.sort(key=lambda t: t.total, reverse=True)
        return trends[:10]

    @staticmethod
    def _parse_window_days(window: str) -> int:
        """Parse window string like '7d', '30d', '90d' to days."""
        window = window.strip().lower()
        if window.endswith("d"):
            try:
                return int(window[:-1])
            except ValueError:
                pass
        if window.endswith("h"):
            try:
                return max(1, int(window[:-1]) // 24)
            except ValueError:
                pass
        if window.endswith("w"):
            try:
                return int(window[:-1]) * 7
            except ValueError:
                pass
        return 7

    # ── Label Injection Simulation ───────────────────────

    def generate_label_patch(
        self,
        pod_name: str,
        namespace: str,
        service: str = "",
        environment: str = "production",
        team: str = "platform",
    ) -> Dict[str, Any]:
        """Generate a Kubernetes label patch for cost tracking.

        Simulates what a MutatingAdmissionWebhook would inject.
        """
        labels = {
            "cost.opencost.io/app": service or pod_name,
            "cost.opencost.io/environment": environment,
            "cost.opencost.io/team": team,
            "cost.opencost.io/injected-at": datetime.now(timezone.utc).isoformat(),
        }
        return {
            "apiVersion": "admission.k8s.io/v1",
            "kind": "AdmissionReview",
            "response": {
                "uid": "",
                "allowed": True,
                "patchType": "JSONPatch",
                "patch": [
                    {"op": "add", "path": f"/metadata/labels/{k.replace('/', '~1')}", "value": v}
                    for k, v in labels.items()
                ],
            },
        }


# ── Singleton ────────────────────────────────────────────

_aggregator: Optional[CostAggregator] = None


def get_cost_aggregator() -> CostAggregator:
    """Get or create the global CostAggregator singleton.

    Reads AG_OPENCOST_URL from environment; falls back to OPENCOST_DEFAULT_URL.
    """
    global _aggregator
    if _aggregator is None:
        opencost_url = os.environ.get("AG_OPENCOST_URL", OPENCOST_DEFAULT_URL)
        _aggregator = CostAggregator(opencost_url=opencost_url)
    return _aggregator
