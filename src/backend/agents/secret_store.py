from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List


_CONFIG_DIR = Path(__file__).resolve().parents[3] / "config"
_API_KEYS_PATH = _CONFIG_DIR / ".api_keys.json"
_DEFAULT_SECTION = "__default__"
_DEFAULT_LLM_KEY = "llm"


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


def load_secret_store() -> Dict[str, Any]:
    if not _API_KEYS_PATH.is_file():
        return {}
    try:
        with _API_KEYS_PATH.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except Exception:
        return {}


def save_secret_store(data: Dict[str, Any]) -> None:
    _CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with _API_KEYS_PATH.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)


def load_model_api_keys() -> Dict[str, Dict[str, str]]:
    raw = load_secret_store()
    return {
        team_id: team_keys
        for team_id, team_keys in raw.items()
        if team_id != _DEFAULT_SECTION and isinstance(team_keys, dict)
    }


def save_model_api_keys(secrets: Dict[str, Dict[str, str]]) -> None:
    raw = load_secret_store()
    default_section = raw.get(_DEFAULT_SECTION, {})
    payload: Dict[str, Any] = {
        team_id: dict(team_keys)
        for team_id, team_keys in secrets.items()
        if team_keys
    }
    if default_section:
        payload[_DEFAULT_SECTION] = default_section
    save_secret_store(payload)


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
    if explicit:
        return explicit
    for env_name in provider_api_key_envs(provider):
        value = os.getenv(env_name, "")
        if value:
            return value
    if default_secret:
        return default_secret
    return plaintext_fallback
