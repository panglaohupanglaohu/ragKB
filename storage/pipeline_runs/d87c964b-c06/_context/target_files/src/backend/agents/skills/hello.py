# -*- coding: utf-8 -*-
"""Hello-world skill module — end-to-end pipeline verification."""

from __future__ import annotations


def greet(name: str) -> str:
    """Return a greeting message.

    Args:
        name: The person to greet.

    Returns:
        A formatted greeting string.
    """
    return f"Hello, {name}!"
