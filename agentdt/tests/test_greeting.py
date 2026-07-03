# -*- coding: utf-8 -*-
"""Tests for the greeting skill module."""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure src/backend is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src" / "backend"))

from agents.skills.greeting import greet


def test_greet_basic():
    """Test greet with a simple name."""
    result = greet("World")
    assert result == "Hello World"


def test_greet_chinese():
    """Test greet with Chinese characters."""
    result = greet("测试")
    assert result == "Hello 测试"


def test_greet_empty_string():
    """Test greet with empty string."""
    result = greet("")
    assert result == "Hello "


def test_greet_special_chars():
    """Test greet with special characters."""
    result = greet("Alice-123!")
    assert result == "Hello Alice-123!"


def test_greet_type():
    """Test that greet always returns a string."""
    result = greet("anything")
    assert isinstance(result, str)
