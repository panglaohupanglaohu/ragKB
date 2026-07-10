# -*- coding: utf-8 -*-
"""PetEcosystem 单元测试 — 覆盖配置加载、默认值补全、嵌套副本清理。"""
import copy
import json
import os
import sys
from pathlib import Path

import pytest

# 确保能 import agents.pet_ecosystem
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src" / "backend"))

from agents.pet_ecosystem import PetEcosystem, _DEFAULT_SEED, _PET_DEFAULTS  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
PET_CONFIG_PATH = REPO_ROOT / "storage" / "pet_config.json"


# ── 1. 仓库实际配置文件数据完整性 ──────────────────────────────────────────────

class TestPetConfigIntegrity:
    """验证 storage/pet_config.json 的数据结构（清理嵌套副本后）。"""

    def test_config_file_exists(self):
        """配置文件存在且可解析。"""
        assert PET_CONFIG_PATH.exists(), "storage/pet_config.json 不存在"
        data = json.loads(PET_CONFIG_PATH.read_text(encoding="utf-8"))
        assert isinstance(data, dict)

    def test_top_level_has_pets_and_ecosystem(self):
        """顶层只有 pets + ecosystem 两个键。"""
        data = json.loads(PET_CONFIG_PATH.read_text(encoding="utf-8"))
        assert "pets" in data and isinstance(data["pets"], list)
        assert "ecosystem" in data and isinstance(data["ecosystem"], dict)

    def test_no_nested_pets_or_ecosystem_in_pet(self):
        """每个 pet 内部不应嵌套 pets/ecosystem（清理后唯一真相源在顶层）。"""
        data = json.loads(PET_CONFIG_PATH.read_text(encoding="utf-8"))
        for pet in data["pets"]:
            assert "pets" not in pet, f"pet {pet.get('id')} 仍嵌套 pets 副本，应清理"
            assert "ecosystem" not in pet, f"pet {pet.get('id')} 仍嵌套 ecosystem 副本，应清理"

    def test_xiaohu_voice_edge_tts_config_complete(self):
        """小虎的 edge-tts 配置字段齐全（页面配置驱动，无兜底）。"""
        data = json.loads(PET_CONFIG_PATH.read_text(encoding="utf-8"))
        xiaohu = next((p for p in data["pets"] if p["id"] == "xiaohu_cat"), None)
        assert xiaohu is not None, "缺少小虎"
        voice = xiaohu.get("voice", {})
        assert voice.get("provider") == "edge-tts", "小虎应为 edge-tts"
        assert voice.get("edge_voice"), "小虎缺 edge_voice（页面必填）"


# ── 2. PetEcosystem 加载与默认值补全 ──────────────────────────────────────────

class TestPetEcosystemLoad:
    """PetEcosystem 实例化逻辑。"""

    def test_load_from_temp_file(self, tmp_path):
        """从临时文件加载正常配置。"""
        cfg = {
            "pets": [
                {"id": "test_cat", "name": "测试猫", "species": "cat",
                 "behavior": {"chase_targets": ["test_mouse"]},
                 "voice": {"provider": "edge-tts", "edge_voice": "zh-CN-YunxiNeural"}},
                {"id": "test_mouse", "name": "测试鼠", "species": "mouse",
                 "behavior": {"flee_from": ["test_cat"]}},
            ],
            "ecosystem": {"chase_pairs": [], "flee_pairs": [], "coexistence": []},
        }
        p = tmp_path / "pet_config.json"
        p.write_text(json.dumps(cfg, ensure_ascii=False), encoding="utf-8")

        eco = PetEcosystem(config_path=str(p))
        result = eco.get_config()
        assert len(result["pets"]) == 2

    def test_default_seed_when_file_missing(self, tmp_path):
        """文件缺失时用 _DEFAULT_SEED 落盘。"""
        missing_path = tmp_path / "nonexistent.json"
        eco = PetEcosystem(config_path=str(missing_path))
        assert missing_path.exists(), "缺失时应自动落盘 seed"
        data = json.loads(missing_path.read_text(encoding="utf-8"))
        assert len(data["pets"]) >= 2, "seed 至少含小虎+吱吱"

    def test_get_config_fills_defaults(self, tmp_path):
        """get_config 为旧配置补全 role/perception/mental_state/intention 默认值。"""
        cfg = {
            "pets": [{"id": "legacy_cat", "name": "老猫", "species": "cat",
                      "behavior": {"chase_targets": ["x"]}}],
            "ecosystem": {},
        }
        p = tmp_path / "pet_config.json"
        p.write_text(json.dumps(cfg), encoding="utf-8")

        eco = PetEcosystem(config_path=str(p))
        result = eco.get_config()
        pet = result["pets"][0]
        assert pet["role"] == "predator", "有 chase_targets 应判为 predator"
        # 默认值补全（用户未配置时）
        assert "perception" in pet
        assert "mental_state" in pet
        assert "intention" in pet
        assert pet["intention"]["catch_radius"] == _PET_DEFAULTS["intention"]["catch_radius"]


# ── 3. _DEFAULT_SEED 结构一致性 ───────────────────────────────────────────────

class TestDefaultSeed:
    """内置种子结构应与页面 schema 对齐。"""

    def test_seed_has_two_pets(self):
        assert len(_DEFAULT_SEED["pets"]) == 2

    def test_seed_predator_has_voice_provider(self):
        """小虎种子必须有 voice.provider（页面配置驱动的最小要求）。"""
        xiaohu = next(p for p in _DEFAULT_SEED["pets"] if p["id"] == "xiaohu_cat")
        assert "voice" in xiaohu
        assert "provider" in xiaohu["voice"], "种子 voice 必须有 provider"
