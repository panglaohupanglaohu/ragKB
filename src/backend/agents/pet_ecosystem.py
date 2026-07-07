"""
PetEcosystem — 宠物团队生态仿真管理器

可插拔、可配置的宠物 3D 模型 + AI 行为 + LLM 台词 + TTS 语音管理。
配置存储在 storage/pet_config.json，通过 REST API 管理。
"""
from __future__ import annotations

import copy
import json
import logging
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_DEFAULT_CONFIG_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "storage", "pet_config.json"
)

# Predator/Prey 行为模型默认字段（论文 Artificial Fishes 心理状态/感知/意图参数）。
# get_config() 用其为缺字段的旧配置补全，用户显式值始终覆盖默认。
_PET_DEFAULTS: Dict[str, Dict[str, Any]] = {
    "perception": {"detect_radius": 6.0, "vision_cone_deg": 300},
    "mental_state": {
        "hunger_full_sec": 20,
        "hunt_hunger_threshold": 0.3,
        "fear_scale_D0": 6.0,
        "f_escape": 0.55,
        "f_calm": 0.35,
    },
    "intention": {"beta_turn_cost": 0.2, "persistence_threshold": 1.5, "catch_radius": 0.8},
}

# 内置默认种子（小虎 predator + 吳吳 prey）—— storage/pet_config.json 被 .gitignore 忽略，
# 跨机拉取后文件不存在时用此种子自动初始化并落盘，避免 0 个生物。
_DEFAULT_SEED: Dict[str, Any] = {
    "pets": [
        {
            "id": "xiaohu_cat",
            "name": "小虎",
            "species": "cat",
            "team_id": "pet_squad",
            "role": "predator",
            "model": {
                "type": "builtin_cat",
                "scale": 1,
                "fur_color": "#C7D9A5",
                "ear_position_x": 0.52,
                "ear_swing_amplitude": 0.3,
                "tail_length": 0.55,
            },
            "behavior": {
                "type": "patrol",
                "route": [[-6, -4], [6, -4], [6, 4], [-6, 4]],
                "speed": 1.6,
                "flee_speed_multiplier": 1,
                "chase_targets": ["squeak_mouse"],
                "flee_from": [],
            },
            "perception": {"detect_radius": 6.0, "vision_cone_deg": 300},
            "mental_state": {
                "hunger_full_sec": 20,
                "hunt_hunger_threshold": 0.3,
                "fear_scale_D0": 6.0,
                "f_escape": 0.55,
                "f_calm": 0.35,
            },
            "intention": {"beta_turn_cost": 0.2, "persistence_threshold": 1.5, "catch_radius": 0.8},
            "speak": {
                "provider": "llm",
                "skill_id": "cat_speak_prompt",
                "trigger": "on_detect_mouse",
                "cooldown_sec": 10,
                "fallback": "",
            },
            "voice": {
                "provider": "browser",
                "enabled": True,
                "lang": "zh-CN",
                "rate": 1.05,
                "pitch": 1.4,
                "volume": 0.9,
                "preferred_voice": "Google US English",
            },
            "click_action": {"type": "dialog", "personality": "叛逆高中生灵魂的巡检猫，毒舌但善良"},
        },
        {
            "id": "squeak_mouse",
            "name": "吳吳",
            "species": "mouse",
            "team_id": "pet_squad",
            "role": "prey",
            "model": {"type": "builtin_mouse", "scale": 0.85, "fur_color": "0x8a8a8a"},
            "behavior": {
                "type": "patrol",
                "route": [[13, 2], [-13, 2], [-13, -2], [13, -2]],
                "speed": 1.7,
                "flee_speed_multiplier": 2.1,
                "chase_targets": [],
                "flee_from": ["xiaohu_cat"],
            },
            "perception": {"detect_radius": 6.0, "vision_cone_deg": 300},
            "mental_state": {
                "hunger_full_sec": 20,
                "hunt_hunger_threshold": 0.3,
                "fear_scale_D0": 6.0,
                "f_escape": 0.55,
                "f_calm": 0.35,
            },
            "intention": {"beta_turn_cost": 0.2, "persistence_threshold": 1.5, "catch_radius": 0.8},
            "speak": {"provider": "none"},
            "voice": {
                "provider": "browser",
                "enabled": False,
                "lang": "zh-CN",
                "rate": 1.3,
                "pitch": 2,
                "volume": 0.85,
            },
            "click_action": {"type": "bubble"},
        },
    ],
    "ecosystem": {
        "chase_pairs": [["xiaohu_cat", "squeak_mouse"]],
        "flee_pairs": [["squeak_mouse", "xiaohu_cat"]],
        "coexistence": [],
    },
}


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
            if not self._config.get("pets"):
                raise ValueError("config has no pets")
            logger.info("🐾 PetEcosystem loaded %d pets from %s", len(self._config.get("pets", [])), self._path)
        except Exception as e:
            # 文件缺失/损坏/无宠物 → 用内置默认种子（小虎+吳吳）并落盘，保证跨机自带
            logger.warning("🐾 PetEcosystem config unavailable (%s); seeding built-in defaults", e)
            self._config = copy.deepcopy(_DEFAULT_SEED)
            self._save()

    def _save(self) -> None:
        try:
            with open(self._path, "w", encoding="utf-8") as f:
                json.dump(self._config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error("🐾 PetEcosystem save failed: %s", e)

    # ── CRUD ──

    def get_config(self) -> Dict[str, Any]:
        """获取全量配置（内存补全 Predator/Prey 默认字段，向后兼容旧配置）。"""
        for pet in self._config.get("pets", []):
            # role 缺省：有 chase_targets 视为 predator，否则 prey
            if "role" not in pet:
                has_chase = bool(pet.get("behavior", {}).get("chase_targets"))
                pet["role"] = "predator" if has_chase else "prey"
            for key, defaults in _PET_DEFAULTS.items():
                # 用户值覆盖默认（默认在前，用户在后）
                pet[key] = {**defaults, **pet.get(key, {})}
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
