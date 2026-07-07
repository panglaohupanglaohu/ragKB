"""
PetEcosystem REST API — 宠物团队生态仿真配置管理。

GET    /api/v1/pet-ecosystem/config           — 获取全量配置
POST   /api/v1/pet-ecosystem/pets              — 新增宠物
PUT    /api/v1/pet-ecosystem/pets/{pet_id}     — 更新宠物配置
DELETE /api/v1/pet-ecosystem/pets/{pet_id}     — 删除宠物
PUT    /api/v1/pet-ecosystem/ecosystem         — 更新互动关系
"""
from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .pet_ecosystem import get_pet_ecosystem

router = APIRouter(prefix="/api/v1/pet-ecosystem", tags=["pet-ecosystem"])


class PetConfigRequest(BaseModel):
    """宠物配置更新请求（部分更新）。"""
    model_config = {"extra": "allow"}
    id: str = ""
    name: str = ""
    species: str = ""
    team_id: str = ""
    role: str = ""
    model: Dict[str, Any] = {}
    behavior: Dict[str, Any] = {}
    perception: Dict[str, Any] = {}
    mental_state: Dict[str, Any] = {}
    intention: Dict[str, Any] = {}
    speak: Dict[str, Any] = {}
    voice: Dict[str, Any] = {}
    click_action: Dict[str, Any] = {}


class EcosystemRequest(BaseModel):
    """互动关系更新请求。"""
    chase_pairs: list = []
    flee_pairs: list = []
    coexistence: list = []


@router.get("/config", summary="获取全量宠物生态配置")
def get_config() -> Dict[str, Any]:
    return get_pet_ecosystem().get_config()


@router.get("/pets/{pet_id}", summary="获取单个宠物配置")
def get_pet(pet_id: str) -> Dict[str, Any]:
    pet = get_pet_ecosystem().get_pet(pet_id)
    if not pet:
        raise HTTPException(404, detail=f"Pet {pet_id} not found")
    return pet


@router.post("/pets", summary="新增宠物", status_code=201)
def add_pet(req: PetConfigRequest) -> Dict[str, Any]:
    result = get_pet_ecosystem().add_pet(req.model_dump(exclude_none=True))
    if "error" in result:
        raise HTTPException(400, detail=result["error"])
    return result


@router.put("/pets/{pet_id}", summary="更新宠物配置")
def update_pet(pet_id: str, req: PetConfigRequest) -> Dict[str, Any]:
    updates = req.model_dump(exclude_none=True)
    updates.pop("id", None)  # id 不可改
    result = get_pet_ecosystem().update_pet(pet_id, updates)
    if "error" in result:
        raise HTTPException(404, detail=result["error"])
    return result


@router.delete("/pets/{pet_id}", summary="删除宠物")
def delete_pet(pet_id: str) -> Dict[str, Any]:
    result = get_pet_ecosystem().delete_pet(pet_id)
    if "error" in result:
        raise HTTPException(404, detail=result["error"])
    return result


@router.put("/ecosystem", summary="更新互动关系")
def update_ecosystem(req: EcosystemRequest) -> Dict[str, Any]:
    return get_pet_ecosystem().update_ecosystem({
        "chase_pairs": req.chase_pairs,
        "flee_pairs": req.flee_pairs,
        "coexistence": req.coexistence,
    })
