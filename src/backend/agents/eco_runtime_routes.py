# -*- coding: utf-8 -*-
"""Eco Runtime Config REST API — 仿生生态运行时可配置参数管理.

GET   /api/v1/eco-runtime/config     — 获取全量配置（默认补全后）
GET   /api/v1/eco-runtime/defaults   — 获取内置默认（供"恢复默认"）
PUT   /api/v1/eco-runtime/config     — 部分更新（只覆盖已知 section/键）
POST  /api/v1/eco-runtime/reset      — 恢复全部默认
"""
from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter
from pydantic import BaseModel

from .runtime.eco_runtime_config import get_eco_runtime_config

router = APIRouter(prefix="/api/v1/eco-runtime", tags=["eco-runtime"])


class EcoRuntimeUpdateRequest(BaseModel):
    """部分更新请求：{section: {key: value}}，未知 section/键会被后端忽略。"""
    model_config = {"extra": "allow"}
    mental_state: Dict[str, Any] = {}
    metabolism: Dict[str, Any] = {}
    learning: Dict[str, Any] = {}
    selection: Dict[str, Any] = {}
    mating: Dict[str, Any] = {}


@router.get("/config", summary="获取仿生生态运行时全量参数")
def get_config() -> Dict[str, Any]:
    return get_eco_runtime_config().get_config()


@router.get("/defaults", summary="获取内置默认参数")
def get_defaults() -> Dict[str, Any]:
    return get_eco_runtime_config().get_defaults()


@router.put("/config", summary="部分更新仿生生态运行时参数")
def update_config(req: EcoRuntimeUpdateRequest) -> Dict[str, Any]:
    updates = {k: v for k, v in req.model_dump(exclude_none=True).items() if v}
    return get_eco_runtime_config().update(updates)


@router.post("/reset", summary="恢复全部默认参数")
def reset_config() -> Dict[str, Any]:
    return get_eco_runtime_config().reset()
