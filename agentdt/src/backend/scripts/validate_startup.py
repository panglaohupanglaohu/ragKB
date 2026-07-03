#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CLI 启动验证脚本

用法:
    python scripts/validate_startup.py                    # 默认 localhost:8080
    python scripts/validate_startup.py --url http://localhost:8080
    python scripts/validate_startup.py --json             # JSON 格式输出
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import os

# 确保 backend 目录在 sys.path 中
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from startup_validator import validate_startup


def main():
    parser = argparse.ArgumentParser(
        description="AgentsGroup2026 启动验证工具"
    )
    parser.add_argument(
        "--url",
        default="http://localhost:8080",
        help="后端服务 URL (默认: http://localhost:8080)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="以 JSON 格式输出报告",
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="静默模式，仅输出摘要",
    )

    args = parser.parse_args()

    report = asyncio.run(validate_startup(
        base_url=args.url,
        verbose=not args.quiet,
    ))

    if args.json:
        print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))

    sys.exit(1 if report.failed > 0 else 0)


if __name__ == "__main__":
    main()
