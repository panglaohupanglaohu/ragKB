# -*- coding: utf-8 -*-
"""K8s MutatingAdmissionWebhook handler for cost label auto-injection.

Handles AdmissionReview requests from the Kubernetes API server,
injecting cost allocation labels (service, environment, team, component)
into Pod specifications based on namespace annotations, workload metadata,
and default configuration.

Architecture:
  - K8sCostWebhook — FastAPI APIRouter that serves /mutate-cost-labels
  - MutatingAdmissionWebhook handler for Pod CREATE operations
  - Injects standard cost labels as defined in CostLabelConfig
  - Supports namespace-level annotation overrides for environment/team defaults
"""

from __future__ import annotations

import base64
import json
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field

from .cost_models import CostLabelConfig

logger = logging.getLogger(__name__)

# ── AdmissionReview Models ──────────────────────────────


class AdmissionRequest(BaseModel):
    """K8s AdmissionReview request."""
    uid: str = ""
    kind: Dict[str, str] = Field(default_factory=dict)
    resource: Dict[str, str] = Field(default_factory=dict)
    namespace: str = ""
    operation: str = ""
    userInfo: Dict[str, Any] = Field(default_factory=dict)
    object: Dict[str, Any] = Field(default_factory=dict)
    oldObject: Optional[Dict[str, Any]] = None
    dryRun: bool = False


class AdmissionResponse(BaseModel):
    """K8s AdmissionReview response for a single request."""
    uid: str = ""
    allowed: bool = True
    patchType: Optional[str] = None
    patch: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)


class AdmissionReviewRequest(BaseModel):
    """Incoming AdmissionReview from K8s API server."""
    apiVersion: str = "admission.k8s.io/v1"
    kind: str = "AdmissionReview"
    request: Optional[AdmissionRequest] = None


class AdmissionReviewResponse(BaseModel):
    """Outgoing AdmissionReview response."""
    apiVersion: str = "admission.k8s.io/v1"
    kind: str = "AdmissionReview"
    response: AdmissionResponse


class PodMetadata(BaseModel):
    """Simplified Pod metadata for dry-run."""
    name: str = "dry-run-pod"
    labels: Dict[str, str] = Field(default_factory=dict)


class DryRunLabelInjectionRequest(BaseModel):
    """Request body for /mutate-cost-labels/dry-run."""
    metadata: PodMetadata = Field(default_factory=PodMetadata)
    namespace: str = "default"
    namespaceAnnotations: Dict[str, str] = Field(default_factory=dict)


# ── Webhook Router ──────────────────────────────────────

webhook_router = APIRouter(prefix="/webhook", tags=["K8s Webhook"])


# ── Label Injection Logic ───────────────────────────────

def _resolve_labels(
    pod_metadata: Dict[str, Any],
    namespace_annotations: Dict[str, str],
    config: CostLabelConfig,
) -> Dict[str, str]:
    """Resolve cost labels for a Pod based on metadata and namespace annotations.

    Priority (highest first):
      1. Existing Pod labels (if already set)
      2. Namespace annotations (e.g., cost.opencost.io/environment)
      3. Defaults from CostLabelConfig
    """
    existing_labels: Dict[str, str] = dict(pod_metadata.get("labels", {}) or {})

    # Resolve each target label
    resolved: Dict[str, str] = {}

    # Environment
    env_key = f"{config.label_prefix}/environment"
    if "environment" in existing_labels:
        resolved["environment"] = existing_labels["environment"]
    elif env_key in existing_labels:
        resolved["environment"] = existing_labels[env_key]
    else:
        ns_env = namespace_annotations.get(env_key, "")
        resolved["environment"] = ns_env or config.default_environment

    # Team
    team_key = f"{config.label_prefix}/team"
    if "team" in existing_labels:
        resolved["team"] = existing_labels["team"]
    elif team_key in existing_labels:
        resolved["team"] = existing_labels[team_key]
    else:
        ns_team = namespace_annotations.get(team_key, "")
        resolved["team"] = ns_team or config.default_team

    # Service (derived from app label or workload name)
    svc_key = f"{config.label_prefix}/service"
    if "service" in existing_labels:
        resolved["service"] = existing_labels["service"]
    elif svc_key in existing_labels:
        resolved["service"] = existing_labels[svc_key]
    elif "app" in existing_labels:
        resolved["service"] = existing_labels["app"]
    elif "app.kubernetes.io/name" in existing_labels:
        resolved["service"] = existing_labels["app.kubernetes.io/name"]
    else:
        resolved["service"] = pod_metadata.get("name", "unknown")

    # Component
    component_key = f"{config.label_prefix}/component"
    if "component" in existing_labels:
        resolved["component"] = existing_labels["component"]
    elif component_key in existing_labels:
        resolved["component"] = existing_labels[component_key]
    elif "app.kubernetes.io/component" in existing_labels:
        resolved["component"] = existing_labels["app.kubernetes.io/component"]
    else:
        resolved["component"] = "application"

    return resolved


def _build_json_patch(
    pod_name: str,
    existing_labels: Dict[str, str],
    resolved_labels: Dict[str, str],
    config: CostLabelConfig,
) -> List[Dict[str, Any]]:
    """Build RFC 6902 JSON Patch operations to inject cost labels.

    Only adds labels that are not already present, so we don't
    overwrite manual overrides.
    """
    patches: List[Dict[str, Any]] = []
    add_labels: Dict[str, str] = {}

    # Determine which labels need injection
    for label_name in config.inject_labels:
        if label_name not in existing_labels and label_name in resolved_labels:
            add_labels[label_name] = resolved_labels[label_name]

    # Also add the prefixed versions for OpenCost compatibility
    for label_name in config.inject_labels:
        if label_name in resolved_labels:
            prefixed_key = f"{config.label_prefix}/{label_name}"
            if prefixed_key not in existing_labels:
                add_labels[prefixed_key] = resolved_labels[label_name]

    if not add_labels:
        return patches

    # Check if pod already has labels — if so, add to existing
    # Otherwise create the labels map
    # For MutatingAdmissionWebhook, we patch /metadata/labels
    patches.append({
        "op": "add",
        "path": "/metadata/labels",
        "value": add_labels,
    })

    return patches


def handle_admission_review(
    body: AdmissionReviewRequest,
    config: Optional[CostLabelConfig] = None,
) -> AdmissionReviewResponse:
    """Process an AdmissionReview and return a response with label patches.

    This is the core webhook handler — called by the HTTP endpoint
    and also usable standalone for testing.

    Args:
        body: The AdmissionReview request from K8s API server.
        config: Label injection configuration (uses defaults if None).

    Returns:
        AdmissionReviewResponse with JSON Patch for label injection.
    """
    if config is None:
        config = CostLabelConfig()

    # Default: allow everything
    if body.request is None:
        return AdmissionReviewResponse(
            response=AdmissionResponse(
                uid="unknown",
                allowed=True,
                warnings=["No request in AdmissionReview"],
            )
        )

    req = body.request

    # Only mutate Pod CREATE operations
    if req.kind.get("kind", "") != "Pod" or req.operation != "CREATE":
        return AdmissionReviewResponse(
            response=AdmissionResponse(
                uid=req.uid,
                allowed=True,
            )
        )

    pod = req.object
    pod_metadata: Dict[str, Any] = pod.get("metadata", {}) or {}
    pod_name = pod_metadata.get("name", "unknown")

    # In a real webhook, namespace annotations would come from the K8s API.
    # Here we extract them from the request if available, or use empty.
    namespace_annotations: Dict[str, str] = {}
    if "namespace" in pod:
        ns_meta = pod.get("namespace", {}).get("metadata", {}) or {}
        namespace_annotations = ns_meta.get("annotations", {}) or {}

    # Resolve labels
    resolved = _resolve_labels(pod_metadata, namespace_annotations, config)
    existing_labels = dict(pod_metadata.get("labels", {}) or {})

    # Build JSON Patch
    patches = _build_json_patch(pod_name, existing_labels, resolved, config)

    logger.info(
        "Webhook: pod=%s ns=%s labels=%s patches=%d",
        pod_name, req.namespace, resolved, len(patches),
    )

    if patches:
        patch_bytes = json.dumps(patches).encode("utf-8")
        patch_b64 = base64.b64encode(patch_bytes).decode("utf-8")
        return AdmissionReviewResponse(
            response=AdmissionResponse(
                uid=req.uid,
                allowed=True,
                patchType="JSONPatch",
                patch=patch_b64,
            )
        )
    else:
        return AdmissionReviewResponse(
            response=AdmissionResponse(
                uid=req.uid,
                allowed=True,
            )
        )


# ── HTTP Endpoints ──────────────────────────────────────


@webhook_router.post("/mutate-cost-labels")
async def mutate_cost_labels(request: Request) -> Dict[str, Any]:
    """K8s MutatingAdmissionWebhook endpoint for cost label injection.

    Receives AdmissionReview v1 requests and responds with JSON Patch
    mutations to inject standard cost allocation labels.

    TLS is typically handled by the K8s API server or an ingress controller.
    """
    try:
        body_dict = await request.json()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON body",
        )

    try:
        adm_req = AdmissionReviewRequest(**body_dict)
    except Exception as e:
        logger.warning("Failed to parse AdmissionReview: %s", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid AdmissionReview: {e}",
        )

    response = handle_admission_review(adm_req)
    return response.model_dump()


@webhook_router.get("/mutate-cost-labels/health")
async def webhook_health() -> Dict[str, Any]:
    """Health check endpoint for the webhook."""
    return {
        "status": "ok",
        "webhook": "cost-label-injector",
        "version": "1.0.0",
    }


@webhook_router.post("/mutate-cost-labels/dry-run")
async def dry_run_label_injection(body: DryRunLabelInjectionRequest) -> Dict[str, Any]:
    """Dry-run endpoint: preview what labels would be injected.

    Accepts a simplified Pod spec and returns the resolved labels
    and JSON Patch without requiring a full AdmissionReview.
    """
    pod_metadata = body.metadata
    pod_name = pod_metadata.name
    namespace = body.namespace
    config = CostLabelConfig()

    namespace_annotations = body.namespaceAnnotations

    resolved = _resolve_labels(pod_metadata.model_dump(), namespace_annotations, config)
    existing = dict(pod_metadata.labels)
    patches = _build_json_patch(pod_name, existing, resolved, config)

    return {
        "pod_name": pod_name,
        "namespace": namespace,
        "resolved_labels": resolved,
        "existing_labels": existing,
        "patches": patches,
        "new_labels": {**existing, **resolved},
    }
