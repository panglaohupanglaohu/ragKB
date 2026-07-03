# -*- coding: utf-8 -*-
"""Root-level pytest configuration."""
import sys
from pathlib import Path

# Ensure src/backend is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src" / "backend"))
