# -*- coding: utf-8 -*-
"""Greeting tool function — returns a simple greeting message."""

from __future__ import annotations


def greet(name: str) -> str:
    """Return a greeting message.

    Args:
        name: The person to greet.

    Returns:
        A formatted greeting string "Hello {name}".
    """
    return f"Hello {name}"
