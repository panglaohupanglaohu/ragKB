# -*- coding: utf-8 -*-
"""Root-level pytest configuration."""
import sys
from pathlib import Path

import pytest

# Ensure src/backend is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src" / "backend"))


@pytest.fixture(autouse=True)
def _reset_shared_singletons():
    """根治测试数据污染 (bug-041): 每个用例前后重置共享模块级单例。

    OpenClawSyncChannel 等经 get_ab_test_manager() 共享同一个 ABTestManager，
    前序用例的事件会改动其 EWMA 阈值/决策历史，全量执行顺序下污染后序用例。
    在 conftest 层统一重置，覆盖所有测试文件，无需各文件自建 fixture。
    """
    def _reset():
        try:
            from agents.ab_testing import reset_ab_test_manager
            reset_ab_test_manager()
        except Exception:
            pass
    _reset()
    yield
    _reset()
