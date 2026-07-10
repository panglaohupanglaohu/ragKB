"""简易 .env 加载器（无第三方依赖）。

后端启动时调用 load_env()，从项目根目录 .env 读取 KEY=VALUE 注入 os.environ。
不覆盖已存在的环境变量（让真实环境变量优先）。
"""
from __future__ import annotations

import os
from pathlib import Path


def _project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _env_path() -> Path:
    return _project_root() / ".env"


def load_env() -> int:
    """加载 .env 到 os.environ。返回加载的变量数。已存在的环境变量不被覆盖。"""
    p = _env_path()
    if not p.exists():
        return 0
    count = 0
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        k, _, v = line.partition("=")
        k = k.strip()
        v = v.strip().strip('"').strip("'")
        if k and k not in os.environ:
            os.environ[k] = v
            count += 1
    return count
