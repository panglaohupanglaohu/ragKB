# -*- coding: utf-8 -*-
"""SkillRouter API routes — /api/v1/skill-router."""

from __future__ import annotations

import logging
from dataclasses import asdict
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from .skill_router import get_skill_router, RouteResult

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/skill-router", tags=["skill-router"])


# ── Request/Response Models ──────────────────────────────────────

class RouteRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    team_id: str = ""
    agent_id: str = ""
    top_k: int = Field(default=8, ge=1, le=50)
    mode: str = Field(default="assign", pattern=r"^(assign|runtime)$")
    exclude_skill_ids: List[str] = Field(default_factory=list)


class AssignRequest(BaseModel):
    team_id: str
    agent_id: str
    skill_ids: List[str] = Field(..., min_length=1)
    session_id: str = ""


class SuggestRequest(BaseModel):
    """Request to suggest best agents for a given skill."""
    team_id: str
    skill_id: str
    top_k: int = Field(default=3, ge=1, le=10)


# ── Routes ───────────────────────────────────────────────────────

@router.get("/browse")
async def browse_skills(team_id: str = ""):
    """List all skills visible to a team from the skill library."""
    sr = get_skill_router()
    if sr._skill_library:
        skills = sr._skill_library.browse(team_id=team_id)
    else:
        skills = []
    return {"skills": skills, "total": len(skills)}


@router.post("/route")
async def route_skills(req: RouteRequest):
    """Execute skill routing pipeline (retrieve + rerank)."""
    sr = get_skill_router()
    session = sr.route(
        query=req.query,
        team_id=req.team_id,
        agent_id=req.agent_id,
        top_k=req.top_k,
        mode=req.mode,
        exclude_skill_ids=req.exclude_skill_ids,
    )
    return {
        "session_id": session.session_id,
        "agent_id": session.agent_id,
        "agent_name": session.agent_name,
        "query": session.query,
        "mode": session.mode,
        "duration_ms": session.duration_ms,
        "stage1_ms": session.stage1_ms,
        "stage2_ms": session.stage2_ms,
        "pool_size": session.pool_size,
        "results": [asdict(r) for r in session.results],
    }


@router.post("/assign")
async def assign_skills(req: AssignRequest):
    """Assign routed skills to an agent."""
    sr = get_skill_router()
    result = sr.assign(
        team_id=req.team_id,
        agent_id=req.agent_id,
        skill_ids=req.skill_ids,
        session_id=req.session_id,
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/sessions")
async def list_sessions(team_id: str = "", limit: int = 20):
    """List recent routing sessions."""
    sr = get_skill_router()
    return sr.list_sessions(team_id=team_id, limit=limit)


@router.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """Get a specific routing session."""
    sr = get_skill_router()
    session = sr.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="session_not_found")
    return {
        "session_id": session.session_id,
        "agent_id": session.agent_id,
        "agent_name": session.agent_name,
        "team_id": session.team_id,
        "query": session.query,
        "top_k": session.top_k,
        "mode": session.mode,
        "duration_ms": session.duration_ms,
        "created_at": session.created_at,
        "assigned_skill_ids": session.assigned_skill_ids,
        "results": [asdict(r) for r in session.results],
    }


@router.post("/suggest")
async def suggest_agents(req: SuggestRequest):
    """Suggest best agents for a newly approved skill (closed-loop injection).

    Takes a skill_id and returns ranked agents with affinity scores.
    Used after skill approval to enable one-click injection.
    """
    sr = get_skill_router()
    suggestions = sr.suggest_agents_for_skill(
        team_id=req.team_id,
        skill_id=req.skill_id,
        top_k=req.top_k,
    )
    if "error" in suggestions:
        raise HTTPException(status_code=400, detail=suggestions["error"])
    return suggestions


class FeedbackRequest(BaseModel):
    """Feedback for a skill-agent injection."""
    team_id: str
    agent_id: str
    skill_id: str
    action: str = Field(..., pattern=r"^(rate|revoke)$")
    rating: int = Field(default=0, ge=0, le=5)
    reason: str = ""


@router.post("/feedback")
async def submit_feedback(req: FeedbackRequest):
    """Submit quality feedback for a skill injection (rate or revoke)."""
    sr = get_skill_router()
    result = sr.submit_feedback(
        team_id=req.team_id,
        agent_id=req.agent_id,
        skill_id=req.skill_id,
        action=req.action,
        rating=req.rating,
        reason=req.reason,
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/feedback/stats")
async def feedback_stats(team_id: str = ""):
    """Get aggregated feedback statistics."""
    sr = get_skill_router()
    return sr.get_feedback_stats(team_id=team_id)


@router.get("/agent-profile/{team_id}/{agent_id}")
async def agent_skill_profile(team_id: str, agent_id: str):
    """Get agent's skill profile: injected skills with categories for visualization."""
    sr = get_skill_router()
    profile = sr.get_agent_skill_profile(team_id=team_id, agent_id=agent_id)
    if "error" in profile:
        raise HTTPException(status_code=400, detail=profile["error"])
    return profile


@router.get("/dashboard/{team_id}")
async def skill_pool_dashboard(team_id: str):
    """Get skill pool growth dashboard: total, categories, router metrics."""
    sr = get_skill_router()
    return sr.get_dashboard_stats(team_id=team_id)
