from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List

from cryptography.fernet import Fernet, InvalidToken


_CONFIG_DIR = Path(__file__).resolve().parents[3] / "config"
_API_KEYS_PATH = _CONFIG_DIR / ".api_keys.json"
_MASTER_KEY_PATH = _CONFIG_DIR / ".master_key"
_DEFAULT_SECTION = "__default__"
_DEFAULT_LLM_KEY = "llm"
_ENCRYPTED_FLAG = "__encrypted__"
_ENCRYPTED_FORMAT = "fernet-v1"

logger = logging.getLogger(__name__)


def provider_api_key_envs(provider: str) -> List[str]:
    lowered = (provider or "").strip().lower()
    mapping = {
        "openai": ["OPENAI_API_KEY"],
        "deepseek": ["DEEPSEEK_API_KEY"],
        "anthropic": ["ANTHROPIC_API_KEY"],
        "openrouter": ["OPENROUTER_API_KEY"],
        "github": ["GITHUB_MODELS_API_KEY", "GITHUB_TOKEN"],
        "qwen": ["DASHSCOPE_API_KEY"],
        "local": [],
    }
    return ["AG_LLM_API_KEY", *mapping.get(lowered, [])]


def _load_master_key(*, create: bool) -> str:
    env_key = os.getenv("AG_MASTER_KEY", "").strip()
    if env_key:
        return env_key
    if _MASTER_KEY_PATH.is_file():
        return _MASTER_KEY_PATH.read_text(encoding="utf-8").strip()
    if not create:
        return ""
    _CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    key = Fernet.generate_key().decode("utf-8")
    _MASTER_KEY_PATH.write_text(key, encoding="utf-8")
    try:
        _MASTER_KEY_PATH.chmod(0o600)
    except Exception:
        pass
    return key


def _get_fernet(*, create: bool) -> Fernet | None:
    key = _load_master_key(create=create)
    if not key:
        return None
    try:
        return Fernet(key.encode("utf-8"))
    except Exception:
        logger.warning("Secret store master key is invalid")
        return None


def _read_secret_file() -> Dict[str, Any]:
    if not _API_KEYS_PATH.is_file():
        return {}
    try:
        with _API_KEYS_PATH.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except Exception:
        return {}


def _write_secret_file(data: Dict[str, Any]) -> None:
    _CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with _API_KEYS_PATH.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)


def _is_encrypted_payload(payload: Dict[str, Any]) -> bool:
    return bool(payload.get(_ENCRYPTED_FLAG) and payload.get("ciphertext"))


def _encrypt_payload(data: Dict[str, Any]) -> Dict[str, Any]:
    fernet = _get_fernet(create=True)
    if fernet is None:
        raise RuntimeError("Unable to initialize secret store master key")
    plaintext = json.dumps(data, ensure_ascii=False).encode("utf-8")
    return {
        _ENCRYPTED_FLAG: True,
        "format": _ENCRYPTED_FORMAT,
        "ciphertext": fernet.encrypt(plaintext).decode("utf-8"),
    }


def _decrypt_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    fernet = _get_fernet(create=False)
    if fernet is None:
        logger.warning(
            "Encrypted secret store present but no master key available; set AG_MASTER_KEY or restore %s",
            _MASTER_KEY_PATH,
        )
        return {}
    try:
        plaintext = fernet.decrypt(str(payload["ciphertext"]).encode("utf-8"))
        data = json.loads(plaintext.decode("utf-8"))
        return data if isinstance(data, dict) else {}
    except (InvalidToken, KeyError, json.JSONDecodeError):
        logger.warning("Failed to decrypt secret store payload")
        return {}


def load_secret_store() -> Dict[str, Any]:
    raw = _read_secret_file()
    if not raw:
        return {}
    if _is_encrypted_payload(raw):
        return _decrypt_payload(raw)
    if isinstance(raw, dict):
        # Legacy plaintext store: read once, then rewrite encrypted.
        try:
            save_secret_store(raw)
        except Exception:
            logger.warning("Failed to auto-migrate legacy plaintext secret store")
        return raw
    return {}


def save_secret_store(data: Dict[str, Any]) -> None:
    if not data:
        if _API_KEYS_PATH.exists():
            _API_KEYS_PATH.unlink()
        return
    _write_secret_file(_encrypt_payload(data))


def load_model_api_keys() -> Dict[str, Dict[str, str]]:
    raw = load_secret_store()
    return {
        team_id: team_keys
        for team_id, team_keys in raw.items()
        if team_id != _DEFAULT_SECTION and isinstance(team_keys, dict)
    }


def save_model_api_keys(secrets: Dict[str, Dict[str, str]]) -> None:
    """合并式写入（bug-043 修复）：只新增/更新传入的 key，绝不隐式删除已存 key.

    背景：teams.json 反序列化按设计丢弃明文 key（只保留 env: 引用），
    团队重载后内存密钥为空；旧实现按内存整体重写密钥库，任何一次这种时机的
    _save_model_pool 都会把其他团队/其他模型的已存 key 连同 __default__ 一起抹掉，
    表现为“每次重启密钥都要重输”。删除请走 delete_model_api_key（显式语义）。
    """
    raw = load_secret_store()
    for team_id, team_keys in (secrets or {}).items():
        if not isinstance(team_keys, dict):
            continue
        section = raw.get(team_id)
        section = dict(section) if isinstance(section, dict) else {}
        for model_id, key in team_keys.items():
            if key:  # 空值不覆盖已存 key（与“留空不修改”语义一致）
                section[model_id] = key
        if section:
            raw[team_id] = section
    if raw:
        save_secret_store(raw)


def delete_model_api_key(team_id: str, model_id: str) -> None:
    """显式删除某团队某模型的已存密钥（删模型/清密钥时调用）。"""
    raw = load_secret_store()
    section = raw.get(team_id)
    if not isinstance(section, dict) or model_id not in section:
        return
    section.pop(model_id, None)
    if section:
        raw[team_id] = section
    else:
        raw.pop(team_id, None)
    save_secret_store(raw)


def load_default_llm_api_key() -> str:
    raw = load_secret_store()
    section = raw.get(_DEFAULT_SECTION, {})
    if not isinstance(section, dict):
        return ""
    value = section.get(_DEFAULT_LLM_KEY, "")
    return value if isinstance(value, str) else ""


def save_default_llm_api_key(api_key: str) -> None:
    raw = load_secret_store()
    section = raw.get(_DEFAULT_SECTION, {})
    if not isinstance(section, dict):
        section = {}
    if api_key:
        section[_DEFAULT_LLM_KEY] = api_key
    else:
        section.pop(_DEFAULT_LLM_KEY, None)
    if section:
        raw[_DEFAULT_SECTION] = section
    else:
        raw.pop(_DEFAULT_SECTION, None)
    save_secret_store(raw)


def resolve_api_key(
    provider: str,
    *,
    explicit: str = "",
    default_secret: str = "",
    plaintext_fallback: str = "",
) -> str:
    """解析 API Key。

    优先级：
      1) explicit（含 env:VAR 引用）— 编辑框/测试连接/config_override
      2) default_secret（secret store __default__）— UI「设为全局默认」写入
      3) plaintext_fallback（settings.json llm.api_key）
      4) 进程环境变量 OPENAI_API_KEY 等 — 仅作最后兜底

    注意：环境变量不得压过 UI 已保存的 Key。否则会出现「测试连接成功
    （explicit=编辑框）但演化/广场仍 INVALID_API_KEY（读到 shell 里旧 OPENAI_API_KEY）」。
    """
    # env:VAR_NAME 引用 → 从环境变量解析（页面配置存 env: 引用，不存明文 key）
    if explicit.startswith("env:"):
        var_name = explicit[4:]
        return os.environ.get(var_name, "")
    if explicit:
        return explicit
    if default_secret:
        return default_secret
    if plaintext_fallback:
        return plaintext_fallback
    for env_name in provider_api_key_envs(provider):
        value = os.getenv(env_name, "")
        if value:
            return value
    return ""
