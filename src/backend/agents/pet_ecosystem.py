"""
PetEcosystem — 宠物团队生态仿真管理器

可插拔、可配置的宠物 3D 模型 + AI 行为 + LLM 台词 + TTS 语音管理。
配置存储在 storage/pet_config.json，通过 REST API 管理。
"""
from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_DEFAULT_CONFIG_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "storage", "pet_config.json"
)


class PetEcosystem:
    """宠物生态管理器 — 加载/保存/CRUD 配置。"""

    def __init__(self, config_path: str = "") -> None:
        self._path = config_path or _DEFAULT_CONFIG_PATH
        self._config: Dict[str, Any] = {"pets": [], "ecosystem": {"chase_pairs": [], "coexistence": []}}
        self._load()

    def _load(self) -> None:
        try:
            with open(self._path, "r", encoding="utf-8") as f:
                self._config = json.load(f)
            logger.info("🐾 PetEcosystem loaded %d pets from %s", len(self._config.get("pets", [])), self._path)
        except Exception as e:
            logger.warning("🐾 PetEcosystem config load failed: %s, using empty config", e)
            self._config = {"pets": [], "ecosystem": {"chase_pairs": [], "coexistence": []}}

    def _save(self) -> None:
        try:
            with open(self._path, "w", encoding="utf-8") as f:
                json.dump(self._config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error("🐾 PetEcosystem save failed: %s", e)

    # ── CRUD ──

    def get_config(self) -> Dict[str, Any]:
        """获取全量配置。"""
        return self._config

    def get_pet(self, pet_id: str) -> Optional[Dict[str, Any]]:
        """获取单个宠物配置。"""
        for pet in self._config.get("pets", []):
            if pet.get("id") == pet_id:
                return pet
        return None

    def add_pet(self, pet_config: Dict[str, Any]) -> Dict[str, Any]:
        """新增宠物。"""
        pet_id = pet_config.get("id", "")
        if not pet_id:
            return {"error": "pet id is required"}
        if self.get_pet(pet_id):
            return {"error": f"pet {pet_id} already exists"}
        self._config.setdefault("pets", []).append(pet_config)
        self._save()
        logger.info("🐾 PetEcosystem: added pet %s", pet_id)
        return {"status": "created", "pet_id": pet_id}

    def update_pet(self, pet_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """更新宠物配置（部分更新）。"""
        for i, pet in enumerate(self._config.get("pets", [])):
            if pet.get("id") == pet_id:
                # 深度合并
                merged = _deep_merge(pet, updates)
                merged["id"] = pet_id  # id 不可改
                self._config["pets"][i] = merged
                self._save()
                logger.info("🐾 PetEcosystem: updated pet %s", pet_id)
                return {"status": "updated", "pet_id": pet_id, "config": merged}
        return {"error": f"pet {pet_id} not found"}

    def delete_pet(self, pet_id: str) -> Dict[str, Any]:
        """删除宠物。"""
        before = len(self._config.get("pets", []))
        self._config["pets"] = [p for p in self._config.get("pets", []) if p.get("id") != pet_id]
        if len(self._config["pets"]) == before:
            return {"error": f"pet {pet_id} not found"}
        # 清理 ecosystem 引用
        eco = self._config.get("ecosystem", {})
        eco["chase_pairs"] = [
            pair for pair in eco.get("chase_pairs", []) if pet_id not in pair
        ]
        eco["flee_pairs"] = [
            pair for pair in eco.get("flee_pairs", []) if pet_id not in pair
        ]
        eco["coexistence"] = [
            pair for pair in eco.get("coexistence", []) if pet_id not in pair
        ]
        self._save()
        logger.info("🐾 PetEcosystem: deleted pet %s", pet_id)
        return {"status": "deleted", "pet_id": pet_id}

    def update_ecosystem(self, ecosystem: Dict[str, Any]) -> Dict[str, Any]:
        """更新互动关系。"""
        self._config["ecosystem"] = ecosystem
        self._save()
        return {"status": "updated", "ecosystem": ecosystem}

    def get_chase_targets(self, pet_id: str) -> List[str]:
        """获取某宠物的追逐目标列表。"""
        pet = self.get_pet(pet_id)
        if not pet:
            return []
        return pet.get("behavior", {}).get("chase_targets", [])

    def get_flee_from(self, pet_id: str) -> List[str]:
        """获取某宠物的逃跑来源列表。"""
        pet = self.get_pet(pet_id)
        if not pet:
            return []
        return pet.get("behavior", {}).get("flee_from", [])


def _deep_merge(base: Dict, updates: Dict) -> Dict:
    """深度合并两个 dict。"""
    result = dict(base)
    for k, v in updates.items():
        if k in result and isinstance(result[k], dict) and isinstance(v, dict):
            result[k] = _deep_merge(result[k], v)
        else:
            result[k] = v
    return result


# 单例
_ecosystem: Optional[PetEcosystem] = None


def get_pet_ecosystem() -> PetEcosystem:
    global _ecosystem
    if _ecosystem is None:
        _ecosystem = PetEcosystem()
    return _ecosystem
