# 架构设计 — architect

任务: 设计共签机制与配置即契约的治理桩，使业务域主与架构师共同签署阈值的反射修改
步骤: architecture
Agent: build_architect

---

📋 任务: 8665633b-cad
🤖 Agent: Architect (architect)
📂 工作目录: /Users/panglaohu/Downloads/AgentsGroup2026
🔧 执行方式: DeepSeek API (直连)
⏱️ 超时: 1200s
────────────────────────────────────────────────────────────
📝 提示词:
  你是 AgentsGroup2026 系统的 Architect (architect)。
  请执行以下开发任务:
  
  你是系统架构师。请为以下任务设计技术方案:
  
  ## 任务
  设计共签机制与配置即契约的治理桩，使业务域主与架构师共同签署阈值的反射修改
  Architect + 业务域主
  
  ## 📂 项目上下文 (系统自动预加载)
  
  ### 项目文件结构 (src/ 目录)
  ```
  src/frontend/agent-team-config.html
  src/frontend/datacenter-ratchet-evolution.html
  src/frontend/index.html
  src/frontend/login.html
  src/frontend/plaza-dark.html
  src/frontend/plaza-old.html
  src/frontend/plaza-wabisabi-v2.html
  src/frontend/plaza-wabisabi.html
  src/frontend/plaza.html
  src/frontend/system-evolution.html
  src/frontend/tasks.html
  src/frontend/css/agent-team-config.css
  src/frontend/css/openbridge-theme.css
  src/frontend/css/ws-theme-bridge.css
  src/frontend/js/agent-team-config.js
  src/frontend/js/i18n.js
  src/frontend/js/nav-sidebar.js
  src/backend/__init__.py
  src/backend/agent_team_api.py
  src/backend/main.py
  src/backend/main.py.bak
  src/backend/startup_check.py
  src/backend/startup_validator.py
  src/backend/agents/__init__.py
  src/backend/agents/ab_testing.py
  src/backend/agents/agent_loop.py
  src/backend/agents/agent_toolbox.py
  src/backend/agents/api.py
  src/backend/agents/chat_harness.py
  src/backend/agents/execution_registry.py
  src/backend/agents/hermes_research.py
  src/backend/agents/knowledge_base.py
  src/backend/agents/models.py
  src/backend/agents/plaza.py
  src/backend/agents/plaza_engine.py
  src/backend/agents/plaza_routes.py
  src/backend/agents/plaza_routes.py.bak
  src/backend/agents/plaza_store.py
  src/backend/agents/session_store.py
  src/backend/agents/skill_registry.py
  src/backend/agents/task_engine.py
  src/backend/agents/task_store.py
  src/backend/agents/team_manager.py
  src/backend/agents/team_store.py
  src/backend/agents/tool_executor.py
  src/backend/agents/tool_registry.py
  src/backend/agents/tts_routes.py
  src/backend/agents/teams/__init__.py
  src/backend/agents/teams/ai_coding_team.py
  src/backend/agents/teams/build_team.py
  src/backend/agents/teams/energy_team.py
  src/backend/agents/skills/__init__.py
  src/backend/agents/skills/greeting.py
  src/backend/agents/skills/hello.py
  src/backend/scripts/__init__.py
  src/backend/scripts/validate_startup.py
  src/backend/scripts/validate_telemetry.py
  src/backend/monitoring/__init__.py
  src/backend/monitoring/collector.py
  src/backend/monitoring/models.py
  src/backend/monitoring/plaza_monitor.py
  src/backend/monitoring/plaza_monitor.py.bak
  src/backend/monitoring/sampler.py
  src/backend/channels/__init__.py
  src/backend/channels/bridge_chat.py
  src/backend/channels/marine_base.py
  src/backend/channels/openclaw_sync.py
  src/backend/channels/openclaw_sync.py.bak
  src/backend/channels/system_evolution.py
  src/docs/agent_handoffs/1ce78c0e-062_architecture_20260503T045804.md
  src/docs/agent_handoffs/1ce78c0e-062_deploy_FAILED_20260503T050220.md
  src/docs/agent_handoffs/1ce78c0e-062_develop_20260503T045845.md
  src/docs/agent_handoffs/1ce78c0e-062_develop_20260503T050025.md
  src/docs/agent_handoffs/1ce78c0e-062_develop_20260503T050150.md
  src/docs/agent_handoffs/1ce78c0e-062_pm_decompose_20260503T045724.md
  src/docs/agent_handoffs/1ce78c0e-062_research_20260503T045739.md
  src/docs/agent_handoffs/1ce78c0e-062_task_init_20260503T045659.md
  src/docs/agent_handoffs/1ce78c0e-062_test_20260503T045905.md
  src/docs/agent_handoffs/1ce78c0e-062_test_20260503T050050.md
  src/docs/agent_handoffs/1ce78c0e-062_test_20260503T050210.md
  src/docs/agent_handoffs/23cb267e-4e0_executor_started_20260503T114540.md
  src/docs/agent_handoffs/38e22004-b64_architecture_20260503T045011.md
  src/docs/agent_handoffs/38e22004-b64_pm_decompose_20260503T044921.md
  src/docs/agent_handoffs/38e22004-b64_research_20260503T044941.md
  src/docs/agent_handoffs/38e22004-b64_task_init_20260503T044856.md
  src/docs/agent_handoffs/3bde709e-2fe_executor_started_20260507T031444.md
  src/docs/agent_handoffs/4b17f83b-805_architecture_20260507T003640.md
  src/docs/agent_handoffs/4b17f83b-805_deploy_FAILED_20260507T004132.md
  src/docs/agent_handoffs/4b17f83b-805_develop_FAILED_20260507T003706.md
  src/docs/agent_handoffs/4b17f83b-805_develop_FAILED_20260507T003913.md
  src/docs/agent_handoffs/4b17f83b-805_develop_FAILED_20260507T004040.md
  src/docs/agent_handoffs/4b17f83b-805_executor_started_20260507T003435.md
  src/docs/agent_handoffs/4b17f83b-805_pm_decompose_20260507T003510.md
  src/docs/agent_handoffs/4b17f83b-805_research_20260507T003555.md
  src/docs/agent_handoffs/4b17f83b-805_test_FAILED_20260507T003732.md
  src/docs/agent_handoffs/4b17f83b-805_test_FAILED_20260507T003939.md
  src/docs/agent_handoffs/4b17f83b-805_test_FAILED_20260507T004102.md
  src/docs/agent_handoffs/6f911ba3-822_architecture_20260507T003740.md
  src/docs/agent_handoffs/6f911ba3-822_deploy_FAILED_20260507T004337.md
  src/docs/agent_handoffs/6f911ba3-822_develop_FAILED_20260507T003806.md
  src/docs/agent_handoffs/6f911ba3-822_develop_FAILED_20260507T004113.md
  src/docs/agent_handoffs/6f911ba3-822_develop_FAILED_20260507T004235.md
  src/docs/agent_handoffs/6f911ba3-822_executor_started_20260507T003435.md
  src/docs/agent_handoffs/6f911ba3-822_pm_decompose_20260507T003510.md
  src/docs/agent_handoffs/6f911ba3-822_research_20260507T003550.md
  src/docs/agent_handoffs/6f911ba3-822_test_FAILED_20260507T003827.md
  src/docs/agent_handoffs/6f911ba3-822_test_FAILED_20260507T004134.md
  src/docs/agent_handoffs/6f911ba3-822_test_FAILED_20260507T004311.md
  src/docs/agent_handoffs/7c934759-39e_architecture_20260505T010014.md
  src/docs/agent_handoffs/7c934759-39e_develop_20260505T010359.md
  src/docs/agent_handoffs/7c934759-39e_develop_20260505T012357.md
  src/docs/agent_handoffs/7c934759-39e_develop_FAILED_20260505T011447.md
  src/docs/agent_handoffs/7c934759-39e_executor_started_20260505T005814.md
  src/docs/agent_handoffs/7c934759-39e_pm_decompose_20260505T005849.md
  src/docs/agent_handoffs/7c934759-39e_research_20260505T005919.md
  src/docs/agent_handoffs/7c934759-39e_test_FAILED_20260505T011016.md
  src/docs/agent_handoffs/7c934759-39e_test_FAILED_20260505T011949.md
  src/docs/agent_handoffs/7c934759-39e_test_FAILED_20260505T012853.md
  src/docs/agent_handoffs/8a5071c5-834_architecture_20260507T003655.md
  src/docs/agent_handoffs/8a5071c5-834_deploy_FAILED_20260507T004051.md
  src/docs/agent_handoffs/8a5071c5-834_develop_FAILED_20260507T003716.md
  src/docs/agent_handoffs/8a5071c5-834_develop_FAILED_20260507T003903.md
  src/docs/agent_handoffs/8a5071c5-834_develop_FAILED_20260507T004005.md
  src/docs/agent_handoffs/8a5071c5-834_executor_started_20260507T003435.md
  src/docs/agent_handoffs/8a5071c5-834_pm_decompose_20260507T003510.md
  src/docs/agent_handoffs/8a5071c5-834_research_20260507T003540.md
  src/docs/agent_handoffs/8a5071c5-834_test_FAILED_20260507T003737.md
  src/docs/agent_handoffs/8a5071c5-834_test_FAILED_20260507T003929.md
  src/docs/agent_handoffs/8a5071c5-834_test_FAILED_20260507T004031.md
  src/docs/agent_handoffs/a77bd3b9-2db_architecture_20260507T003625.md
  src/docs/agent_handoffs/a77bd3b9-2db_deploy_FAILED_20260507T004102.md
  src/docs/agent_handoffs/a77bd3b9-2db_develop_FAILED_20260507T003646.md
  src/docs/agent_handoffs/a77bd3b9-2db_develop_FAILED_20260507T003838.md
  src/docs/agent_handoffs/a77bd3b9-2db_develop_FAILED_20260507T004005.md
  src/docs/agent_handoffs/a77bd3b9-2db_executor_started_20260507T003435.md
  src/docs/agent_handoffs/a77bd3b9-2db_pm_decompose_20260507T003515.md
  src/docs/agent_handoffs/a77bd3b9-2db_research_20260507T003545.md
  src/docs/agent_handoffs/a77bd3b9-2db_test_FAILED_20260507T003712.md
  src/docs/agent_handoffs/a77bd3b9-2db_test_FAILED_20260507T003904.md
  src/docs/agent_handoffs/a77bd3b9-2db_test_FAILED_20260507T004042.md
  src/docs/agent_handoffs/ba3b66b1-a77_architecture_20260505T154317.md
  src/docs/agent_handoffs/ba3b66b1-a77_deploy_FAILED_20260505T154903.md
  src/docs/agent_handoffs/ba3b66b1-a77_develop_FAILED_20260505T154353.md
  src/docs/agent_handoffs/ba3b66b1-a77_develop_FAILED_20260505T154600.md
  src/docs/agent_handoffs/ba3b66b1-a77_develop_FAILED_20260505T154807.md
  src/docs/agent_handoffs/ba3b66b1-a77_executor_started_20260505T153921.md
  src/docs/agent_handoffs/ba3b66b1-a77_pm_decompose_20260505T153951.md
  src/docs/agent_handoffs/ba3b66b1-a77_research_20260505T154041.md
  src/docs/agent_handoffs/ba3b66b1-a77_test_FAILED_20260505T154424.md
  src/docs/agent_handoffs/ba3b66b1-a77_test_FAILED_20260505T154631.md
  ... (共 256 个 src/ 文件)
  
  ```
  
  ### 文件: `src/backend/agents/agent_toolbox.py`
  ```py
  """AgentToolbox — function-calling tools for code-aware agents.
  
  Gives Developer / QA agents the ability to read, grep, write, and execute code
  in the project so they don't have to hallucinate file contents.
  
  All tool calls are scoped to the project root and write operations are
  restricted to a safe allowlist (src/, tests/, docs/, config/, public/).
  
  Each tool returns a JSON-serializable dict suitable for OpenAI/DeepSeek
  function-calling protocol.
  """
  from __future__ import annotations
  
  import json
  import logging
  import os
  import re
  import shlex
  import subprocess
  import time
  from pathlib import Path
  from typing import Any, Dict, List, Optional, Tuple
  
  logger = logging.getLogger("AgentToolbox")
  
  PROJECT_ROOT = Path(__file__).resolve().parents[3]  # src/backend/agents/ -> root
  ALLOWED_WRITE_PREFIXES = ("src/", "tests/", "docs/", "config/", "public/",
                             "storage/agent_workspaces/", "storage/pipeline_runs/")
  MAX_FILE_BYTES = 256 * 1024   # 256KB per read
  MAX_GREP_HITS = 200
  MAX_EXEC_OUTPUT = 32 * 1024   # 32KB stdout/stderr cap
  
  
  # ═════════════════════════════════════════════════════════════════
  # OpenAI / DeepSeek function-calling tool schema (V4 supports this)
  # ═════════════════════════════════════════════════════════════════
  
  TOOL_SCHEMA: List[Dict[str, Any]] = [
      {
          "type": "function",
          "function": {
              "name": "read_file",
              "description": (
                  "读取项目里某个文件的内容。优先使用此工具理解现有代码，再基于实际代码做修改。"
                  "只能读取项目根目录下的文件。"
              ),
              "parameters": {
                  "type": "object",
                  "properties": {
                      "path": {
                          "type": "string",
                          "description": "项目相对路径，如 src/backend/channels/marine_base.py",
                      },
                      "start_line": {"type": "integer", "description": "起始行 (1-based, 可选)", "default": 1},
                      "end_line": {"type": "integer", "description": "结束行 (1-based, 可选)", "default": 0},
                  },
                  "required": ["path"],
              },
          },
      },
      {
          "type": "function",
          "function": {
              "name": "grep",
              "description": (
                  "在项目中按正则搜索文本。用于查找类/函数/枚举值的真实定义位置。"
                  "返回每个匹配的文件路径、行号、行内容。"
              ),
              "parameters": {
                  "type": "object",
                  "properties": {
                      "pattern": {"type": "string", "description": "正则表达式"},
                      "include": {
                          "type": "string",
                          "description": "glob 限定，如 src/backend/**/*.py",
                          "default": "**/*",
                      },
                      "max_hits": {"type": "integer", "default": 50},
                  },
                  "required": ["pattern"],
              },
          },
      },
      {
          "type": "function",
          "function": {
              "name": "list_files",
              "description": "列出某个目录下的所有文件（递归）。",
              "parameters": {
                  "type": "object",
                  "properties": {
                      "path": {"type": "string", "description": "项目相对目录"},
                      "max_depth": {"type": "integer", "default": 3},
                  },
                  "required": ["path"],
              },
          },
      },
      {
          "type": "function",
          "function": {
              "name": "write_file",
              "description": (
                  "向项目写入或新建文件。只能写入 src/, tests/, docs/, config/, public/ 下。"
                  "如果目标已存在，旧内容会先备份为 .bak。优先创建新文件而非整文件覆盖大文件。"
              ),
              "parameters": {
                  "type": "object",
                  "properties": {
                      "path": {"type": "string", "description": "项目相对路径"},
                      "content": {"type": "string", "description": "完整文件内容"},
                      "create_only": {
                          "type": "boolean",
                          "description": "为 true 时仅在文件不存在时写入",
                          "default": False,
                      },
                  },
                  "required": ["path", "content"],
              },
          },
      },
      {
          "type": "function",
          "function": {
              "name": "patch_file",
              "description": (
                  "对已有文件做精准搜索-替换。比 write_file 安全，因为它要求你先看到原文。"
                  "search 必须是文件中存在的、唯一的连续片段。"
              ),
              "parameters": {
                  "type": "object",
                  "properties": {
                      "path": {"type": "string"},
                      "search": {"type": "string", "description": "要被替换的原文片段（必须唯一）"},
                      "replace": {"type": "string", "description": "替换为的新内容"},
                  },
                  "required": ["path", "search", "replace"],
              },
          },
      },
      {
          "type": "function",
          "function": {
              "name": "run_python",
              "description": (
                  "在项目 venv 中执行一段 Python 代码（cwd=src/backend）。"
                  "用于验证 import 是否成功、检查类的属性等。最长执行 30s。"
              ),
              "parameters": {
                  "type": "object",
                  "properties": {
                      "code": {"type": "string", "description": "要执行的 Python 代码"},
                      "timeout": {"type": "integer", "default": 30},
                  },
                  "required": ["code"],
              },
          },
      },
      {
          "type": "function",
          "function": {
              "name": "run_pytest",
              "description": (
                  "运行 pytest，可指定路径或 -k 表达式。仅 QA agent 使用。"
                  "返回最后 60 行输出。"
              ),
              "parameters": {
                  "type": "object",
                  "properties": {
                      "target": {"type": "string", "description": "测试路径或 -k 表达式", "default": ""},
                      "timeout": {"type": "integer", "default": 120},
                  },
              },
          },
      },
      {
          "type": "function",
          "function": {
              "name": "finish",
              "description": (
                  "声明任务完成。Agent 调用此工具表示完成本步骤的所有工作，并附上简短总结。"
                  "调用后循环终止。"
              ),
              "parameters": {
                  "type": "object",
                  "properties": {
                      "summary": {"type": "string", "description": "本步骤完成情况的简短总结"},
                      "files_changed": {
                          "type": "array",
                          "items": {"type": "string"},
                          "description": "本步骤修改/新建的文件路径列表",
                          "default": [],
                      },
                  },
                  "required": ["summary"],
              },
          },
      },
  ]
  
  
  def _safe_path(rel: str) -> Path:
      """Resolve a project-relative path, refusing escapes."""
      if not rel:
          raise ValueError("empty path")
      p = (PROJECT_ROOT / rel).resolve()
      try:
          p.relative_to(PROJECT_ROOT)
      except ValueError:
          raise PermissionError(f"path escapes project root: {rel}")
      return p
  
  
  def _is_allowed_write(rel: str) -> bool:
      rel = rel.replace("\\", "/")
      return any(rel.startswith(p) for p in ALLOWED_WRITE_PREFIXES)
  
  
  # ═════════════════════════════════════════════════════════════════
  # Tool implementations
  # ═════════════════════════════════════════════════════════════════
  
  def tool_read_file(path: str, start_line: int = 1, end_line: int = 0) -> Dict[str, Any]:
      try:
          p = _safe_path(path)
          if not p.is_file():
              return {"ok": False, "error": f"not a file: {path}"}
          size = p.stat().st_size
          if size > MAX_FILE_BYTES * 4:
              return {
                  "ok": False,
                  "error": f"file too large ({size}B). Use grep to find the relevant section first.",
              }
          text = p.read_text(encoding="utf-8", errors="replace")
          lines = text.splitlines()
          total = len(lines)
          if end_line and end_line > 0:
              lines = lines[max(0, start_line - 1):end_line]
          elif start_line > 1:
              lines = lines[start_line - 1:]
          out = "\n".join(lines)
          if len(out) > MAX_FILE_BYTES:
              out = out[:MAX_FILE_BYTES] + "\n…(truncated)"
          return {"ok": True, "path": path, "total_lines": total, "content": out}
      except Exception as e:
          return {"ok": False, "error": str(e)}
  
  
  def tool_grep(pattern: str, include: str = "**/*", max_hits: int = 50) -> Dict[str, Any]:
      try:
          regex = re.compile(pattern)
      except re.error as e:
          return {"ok": False, "error": f"bad regex: {e}"}
      max_hits = min(max_hits, MAX_GREP_HITS)
      hits: List[Dict[str, Any]] = []
      for fp in PROJECT_ROOT.glob(include):
          if not fp.is_file():
              continue
          # Skip irrelevant
          rel = str(fp.relative_to(PROJECT_ROOT))
          if any(seg in rel for seg in ("/node_modules/", "/.git/", "/__pycache__/", "/venv/", ".bak")):
              continue
          try:
              with fp.open("r", encoding="utf-8", errors="replace") as f:
                  for i, line in enumerate(f, 1):
                      if regex.search(line):
                          hits.append({"path": rel, "line": i, "text": line.rstrip()[:200]})
                          if len(hits) >= max_hits:
                              return {"ok": True, "hits": hits, "truncated": True}
          except Exception:
              continue
      return {"ok": True, "hits": hits, "truncated": False}
  
  
  def tool_list_files(path: str, max_depth: int = 3) -> Dict[str, Any]:
      try:
          p = _safe_path(path)
          if not p.is_dir():
              return {"ok": False, "error": f"not a directory: {path}"}
          out: List[str] = []
          base_depth = len(p.parts)
          for root, dirs, files in os.walk(p):
              depth = len(Path(root).parts) - base_depth
              if depth > max_depth:
                  dirs[:] = []
                  continue
              dirs[:] = [d for d in dirs
                         if not d.startswith(".")
                         and d not in ("node_modules", "__pycache__", "venv")]
              for f in files:
                  if f.endswith((".pyc", ".bak")):
                      continue
                  rel = str((Path(root) / f).relative_to(PROJECT_ROOT))
                  out.append(rel)
                  if len(out) >= 500:
                      return {"ok": True, "files": out, "truncated": True}
          return {"ok": True, "files": out, "truncated": False}
      except Exception as e:
          return {"ok": False, "error": str(e)}
  
  
  def tool_write_file(path: str, content: str, create_only: bool = False) -> Dict[str, Any]:
      try:
          if not _is_allowed_write(path):
              return {"ok": False, "error": f"write denied (outside allowed dirs): {path}"}
          p = _safe_path(path)
          if p.exists() and create_only:
              return {"ok": False, "error": f"file exists and create_only=True: {path}"}
          # Shrink-replace guard
          if p.is_file():
              old_size = p.stat().st_size
              if old_size > 2048 and len(content) < old_size * 0.5:
                  return {
                      "ok": False,
                      "error": (
                          f"shrink-replace blocked: new {len(content)}B "
                          f"< 50% of existing {old_size}B. "
                          f"Use patch_file for incremental edits, or write a new file."
                      ),
                  }
              # Backup
              bak = p.with_suffix(p.suffix + ".bak")
              try:
                  bak.write_bytes(p.read_bytes())
              except Exception:
                  pass
          p.parent.mkdir(parents=True, exist_ok=True)
          p.write_text(content, encoding="utf-8")
          return {"ok": True, "path": path, "bytes": len(content), "created": not p.exists()}
      except Exception as e:
          return {"ok": False, "error": str(e)}
  
  
  def tool_patch_file(path: str, search: str, replace: str) -> Dict[str, Any]:
      try:
          if not _is_allowed_write(path):
              return {"ok": False, "error": f"write denied: {path}"}
          p = _safe_path(path)
          if not p.is_file():
              return {"ok": False, "error": f"file not found: {path}"}
          text = p.read_text(encoding="utf-8")
          cnt = text.count(search)
          if cnt == 0:
              return {"ok": False, "error": "search pattern not found in file"}
          if cnt > 1:
              return {
                  "ok": False,
                  "error": f"search pattern matches {cnt} times — must be unique. Add more context.",
              }
          new_text = text.replace(search, replace, 1)
          bak = p.with_suffix(p.suffix + ".bak")
          try:
              bak.write_text(text, encoding="utf-8")
          except Exception:
              pass
          p.write_text(new_text, encoding="utf-8")
          return {"ok": True, "path": path, "old_bytes": len(text), "new_bytes": len(new_text)}
      except Exception as e:
          return {"ok": False, "error": str(e)}
  
  
  def _run_subprocess(cmd: List[str], cwd: Path, timeout: int) -> Dict[str, Any]:
      start = time.time()
      try:
          proc = subprocess.run(
              cmd, cwd=str(cwd), capture_output=True, text=True,
              timeout=timeout,
              env={**os.environ, "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1"},
          )
          elapsed = time.time() - start
          out = proc.stdout or ""
          err = proc.stderr or ""
          if len(out) > MAX_EXEC_OUTPUT:
              out = "…(truncated)\n" + out[-MAX_EXEC_OUTPUT:]
          if len(err) > MAX_EXEC_OUTPUT:
              err = "…(truncated)\n" + err[-MAX_EXEC_OUTPUT:]
          return {
              "ok": True,
              "exit_code": proc.returncode,
              "stdout": out,
              "stderr": err,
              "elapsed_sec": round(elapsed, 2),
          }
      except subprocess.TimeoutExpired:
          return {"ok": False, "error": f"timeout after {timeout}s"}
      except Exception as e:
          return {"ok": False, "error": str(e)}
  
  
  def tool_run_python(code: str, timeout: int = 30) -> Dict[str, Any]:
      venv_py = PROJECT_ROOT / "venv" / "bin" / "python"
      py = str(venv_py) if venv_py.exists() else "python3"
      cwd = PROJECT_ROOT / "src" / "backend"
      return _run_subprocess([py, "-c", code], cwd, timeout)
  
  
  def tool_run_pytest(target: str = "", timeout: int = 120) -> Dict[str, Any]:
      venv_py = PROJECT_ROOT / "venv" / "bin" / "python"
      py = str(venv_py) if venv_py.exists() else "python3"
      args = [py, "-m", "pytest", "-q", "--tb=short", "--maxfail=5"]
      if target:
          if target.startswith("-k") or "::" in target or target.endswith(".py"):
              if target.startswith("-k"):
                  args += target.split(maxsplit=1)
              else:
                  args.append(target)
          else:
              args += ["-k", target]
      return _run_subprocess(args, PROJECT_ROOT, timeout)
  
  
  # ═════════════════════════════════════════════════════════════════
  # Dispatcher
  # ═════════════════════════════════════════════════════════════════
  
  _DISPATCH = {
      "read_file": l
  ```
  
  ### 文件: `src/backend/agents/chat_harness.py`
  ```py
  # -*- coding: utf-8 -*-
  """AgentsGroup2026 Chat Harness — Unified LLM Chat Module.
  
  Inspired by claw-code's QueryEngine + Runtime architecture:
  - Single chat module used by ALL agents, bridge commands, and sessions
  - Provider abstraction: OpenAI-compatible, Anthropic, DeepSeek, local Ollama
  - Session/turn management, token budgeting, transcript compaction
  - Tool invocation pipeline with permission checks
  - Streaming support via SSE-compatible generator
  
  Usage:
      harness = ChatHarness.from_config(config_path="config/settings.json")
      result = await harness.chat(agent_id, prompt, tools=[...])
  
      # Or streaming:
      async for chunk in harness.stream_chat(agent_id, prompt):
          ...
  """
  
  from __future__ import annotations
  
  import json
  import logging
  import os
  import time
  from collections import deque
  from dataclasses import dataclass, field
  from datetime import datetime, timezone
  from enum import Enum
  from pathlib import Path
  from typing import Any, AsyncIterator, Callable, Dict, List, Optional, Tuple
  from uuid import uuid4
  
  from .session_store import (
      StoredSession, TranscriptStore,
      save_session, load_session as _load_stored_session,
      list_sessions as _list_stored_sessions,
      search_sessions,
  )
  from .execution_registry import (
      HistoryLog, ToolPermissionContext, PermissionDenial,
      RoutedMatch, ToolPool, assemble_tool_pool,
      PortRuntime, build_execution_registry,
  )
  
  logger = logging.getLogger(__name__)
  
  
  # ═══════════════════════════════════════════════════════════════
  # UltraPlan — Agentic Planning + Execution Pipeline
  # Inspired by Clawith's plan→act→observe→reflect loop
  # ═══════════════════════════════════════════════════════════════
  
  
  class PlanStepStatus(Enum):
      """Status of a single plan step."""
      PENDING = "pending"
      RUNNING = "running"
      COMPLETED = "completed"
      FAILED = "failed"
      SKIPPED = "skipped"
  
  
  @dataclass
  class PlanStep:
      """A single step in an execution plan."""
      step_id: int = 0
      action: str = ""            # e.g. "tool_call", "think", "respond", "delegate"
      tool_name: str = ""         # Tool to invoke (if action == "tool_call")
      tool_args: Dict[str, Any] = field(default_factory=dict)
      description: str = ""       # Human-readable description
      status: PlanStepStatus = PlanStepStatus.PENDING
      result: str = ""
      error: str = ""
      duration_ms: float = 0.0
      depends_on: List[int] = field(default_factory=list)
  
      def to_dict(self) -> Dict[str, Any]:
          return {
              "step_id": self.step_id,
              "action": self.action,
              "tool_name": self.tool_name,
              "description": self.description,
              "status": self.status.value,
              "result": self.result[:500] if self.result else "",
              "error": self.error,
              "duration_ms": self.duration_ms,
              "depends_on": self.depends_on,
          }
  
  
  @dataclass
  class ExecutionPlan:
      """An ordered plan of steps to fulfill a user request."""
      plan_id: str = field(default_factory=lambda: uuid4().hex[:8])
      goal: str = ""
      steps: List[PlanStep] = field(default_factory=list)
      created_at: str = field(
          default_factory=lambda: datetime.now(timezone.utc).isoformat()
      )
      status: str = "pending"  # pending / running / completed / failed
      final_response: str = ""
  
      def add_step(self, action: str, description: str = "",
                   tool_name: str = "", tool_args: Optional[Dict[str, Any]] = None,
                   depends_on: Optional[List[int]] = None) -> PlanStep:
          step = PlanStep(
              step_id=len(self.steps) + 1,
              action=action,
              tool_name=tool_name,
              tool_args=tool_args or {},
              description=description,
              depends_on=depends_on or [],
          )
          self.steps.append(step)
          return step
  
      @property
      def completed_steps(self) -> int:
          return sum(1 for s in self.steps if s.status == PlanStepStatus.COMPLETED)
  
      @property
      def progress(self) -> float:
          if not self.steps:
              return 1.0
          return self.completed_steps / len(self.steps)
  
      def to_dict(self) -> Dict[str, Any]:
          return {
              "plan_id": self.plan_id,
              "goal": self.goal,
              "status": self.status,
              "steps": [s.to_dict() for s in self.steps],
              "progress": round(self.progress, 2),
              "created_at": self.created_at,
          }
  
  
  # Plan builder: analyzes prompt keywords to auto-generate execution steps
  def build_plan_from_prompt(prompt: str, available_tools: List[str] = None) -> ExecutionPlan:
      """Build an execution plan by analyzing the prompt intent.
  
      This is a rule-based planner that maps keywords to tool invocations.
      When an LLM is available, the plan can be refined by the model.
      """
      plan = ExecutionPlan(goal=prompt[:200])
      lower = prompt.lower()
      tools = set(available_tools or [])
  
      # Multi-domain research
      if any(kw in lower for kw in ["研究", "分析", "调研", "research", "investigate"]):
          plan.add_step("tool_call", "网络搜索相关资料", tool_name="web_search",
                         tool_args={"query": prompt[:100]})
          plan.add_step("think", "整理搜索结果")
          plan.add_step("tool_call", "保存研究发现", tool_name="memory_save",
                         tool_args={"key": f"research_{uuid4().hex[:6]}", "content": ""})
          plan.add_step("respond", "生成研究报告")
  
      # General — single-step
      else:
          plan.add_step("think", "理解用户意图")
          plan.add_step("respond", "生成回复")
  
      return plan
  
  
  # Middleware hook type for plan interception
  PlanMiddleware = Callable[[ExecutionPlan], ExecutionPlan]
  
  
  # ═══════════════════════════════════════════════════════════════
  # Provider Abstraction
  # ═══════════════════════════════════════════════════════════════
  
  
  class LLMProvider(Enum):
      """Supported LLM providers."""
      OPENAI = "openai"
      ANTHROPIC = "anthropic"
      DEEPSEEK = "deepseek"
      OPENROUTER = "openrouter"
      LOCAL = "local"         # Ollama / vLLM / local OpenAI-compatible
      GITHUB = "github"       # GitHub Copilot models
      QWEN = "qwen"
  
  
  @dataclass
  class ProviderConfig:
      """LLM provider connection configuration."""
      provider: LLMProvider = LLMProvider.DEEPSEEK
      api_key: str = ""
      api_base_url: str = ""
      model: str = "deepseek-v4-pro"
      max_tokens: int = 65536  # DeepSeek V4: 64K output
      temperature: float = 0.2
      timeout: float = 1200.0  # Long timeout for big code generations
      thinking: Optional[Dict[str, str]] = None  # e.g. {"type": "enabled"}
      reasoning_effort: str = ""  # "low" | "medium" | "high"
  
      # Default endpoints per provider
      _DEFAULT_URLS: dict = field(default_factory=lambda: {
          LLMProvider.OPENAI: "https://api.openai.com/v1",
          LLMProvider.ANTHROPIC: "https://api.anthropic.com/v1",
          LLMProvider.DEEPSEEK: "https://api.deepseek.com",
          LLMProvider.OPENROUTER: "https://openrouter.ai/api/v1",
          LLMProvider.LOCAL: "http://127.0.0.1:11434/v1",
          LLMProvider.GITHUB: "https://models.inference.ai.azure.com",
          LLMProvider.QWEN: "https://dashscope.aliyuncs.com/compatible-mode/v1",
      }, repr=False)
  
      def resolve_base_url(self) -> str:
          if self.api_base_url:
              return self.api_base_url.rstrip("/")
          return self._DEFAULT_URLS.get(self.provider, "http://127.0.0.1:11434/v1")
  
      @classmethod
      def from_env(cls) -> "ProviderConfig":
          """Build config from environment variables."""
          provider_str = os.getenv("AG_LLM_PROVIDER", "deepseek")
          try:
              provider = LLMProvider(provider_str)
          except ValueError:
              provider = LLMProvider.DEEPSEEK
  
          return cls(
              provider=provider,
              api_key=os.getenv("AG_LLM_API_KEY", os.getenv("DEEPSEEK_API_KEY", "")),
              api_base_url=os.getenv("AG_LLM_BASE_URL", ""),
              model=os.getenv("AG_LLM_MODEL", "deepseek-v4-pro"),
              max_tokens=int(os.getenv("AG_LLM_MAX_TOKENS", "65536")),
              temperature=float(os.getenv("AG_LLM_TEMPERATURE", "0.2")),
              thinking={"type": "enabled"},
              reasoning_effort="high",
          )
  
      @classmethod
      def from_settings(cls, settings: Dict[str, Any]) -> "ProviderConfig":
          """Build from config/settings.json llm section."""
          llm = settings.get("llm", {})
          provider_str = llm.get("provider", "local")
          try:
              provider = LLMProvider(provider_str)
          except ValueError:
              provider = LLMProvider.LOCAL
  
          return cls(
              provider=provider,
              api_key=llm.get("api_key", os.getenv("DEEPSEEK_API_KEY", "")),
              api_base_url=llm.get("local", llm.get("api_base_url", "")),
              model=llm.get("model", "deepseek-v4-pro"),
              max_tokens=llm.get("max_tokens", 65536),
              temperature=llm.get("temperature", 0.2),
              thinking=llm.get("thinking"),
              reasoning_effort=llm.get("reasoning_effort", ""),
          )
  
      @classmethod
      def from_model_config(cls, model_config: Any) -> "ProviderConfig":
          """Build from agents.models.ModelConfig."""
          provider_str = getattr(model_config, "provider", "deepseek")
          try:
              provider = LLMProvider(provider_str)
          except ValueError:
              provider = LLMProvider.DEEPSEEK
  
          return cls(
              provider=provider,
              api_key=getattr(model_config, "api_key", ""),
              api_base_url=getattr(model_config, "api_base_url", ""),
              model=getattr(model_config, "name", "deepseek-v4-pro"),
              max_tokens=getattr(model_config, "max_tokens", 65536),
              temperature=getattr(model_config, "temperature", 0.2),
              thinking={"type": "enabled"},
              reasoning_effort="high",
          )
  
  
  # ═══════════════════════════════════════════════════════════════
  # Turn / Session Data Models
  # ═══════════════════════════════════════════════════════════════
  
  
  @dataclass
  class UsageSummary:
      """Token usage tracking (mirrors claw-code UsageSummary)."""
      input_tokens: int = 0
      output_tokens: int = 0
      total_tokens: int = 0
  
      def add(self, inp: int, out: int) -> "UsageSummary":
          return UsageSummary(
              input_tokens=self.input_tokens + inp,
              output_tokens=self.output_tokens + out,
              total_tokens=self.total_tokens + inp + out,
          )
  
      def to_dict(self) -> Dict[str, int]:
          return {
              "input_tokens": self.input_tokens,
              "output_tokens": self.output_tokens,
              "total_tokens": self.total_tokens,
          }
  
  
  @dataclass
  class ToolInvocation:
      """A tool call extracted from the LLM response."""
      tool_name: str = ""
      arguments: Dict[str, Any] = field(default_factory=dict)
      result: str = ""
      permitted: bool = True
      denial_reason: str = ""
  
      def to_dict(self) -> Dict[str, Any]:
          return {
              "tool_name": self.tool_name,
              "arguments": self.arguments,
              "result": self.result,
              "permitted": self.permitted,
              "denial_reason": self.denial_reason,
          }
  
  
  @dataclass
  class TurnResult:
      """Result of a single chat turn (mirrors claw-code TurnResult)."""
      prompt: str = ""
      response: str = ""
      usage: UsageSummary = field(default_factory=UsageSummary)
      tool_invocations: List[ToolInvocation] = field(default_factory=list)
      stop_reason: str = "completed"
      model: str = ""
      provider: str = ""
      latency_ms: float = 0.0
      error: str = ""
      timestamp: str = field(
          default_factory=lambda: datetime.now(timezone.utc).isoformat()
      )
  
      def to_dict(self) -> Dict[str, Any]:
          return {
              "prompt": self.prompt,
              "response": self.response,
              "usage": self.usage.to_dict(),
              "tool_invocations": [t.to_dict() for t in self.tool_invocations],
              "stop_reason": self.stop_reason,
              "model": self.model,
              "provider": self.provider,
              "latency_ms": self.latency_ms,
              "error": self.error,
              "timestamp": self.timestamp,
          }
  
  
  @dataclass
  class ChatMessage:
      """A single message in a conversation."""
      role: str = "user"  # user | assistant | system | tool
      content: str = ""
      name: str = ""
      tool_calls: List[Dict[str, Any]] = field(default_factory=list)
      timestamp: str = field(
          default_factory=lambda: datetime.now(timezone.utc).isoformat()
      )
  
      def to_openai_dict(self) -> Dict[str, Any]:
          d: Dict[str, Any] = {"role": self.role, "content": self.content}
          if self.name:
              d["name"] = self.name
          return d
  
  
  @dataclass
  class ChatSession:
      """Stateful conversation session with compaction, history & transcript.
  
      Integrates claw-code-parity patterns:
      - HistoryLog for event tracking
      - TranscriptStore for persistence & replay
      - Permission tracking
      """
      session_id: str = field(default_factory=lambda: uuid4().hex[:12])
      agent_id: str = ""
      system_prompt: str = ""
      messages: List[ChatMessage] = field(default_factory=list)
      total_usage: UsageSummary = field(default_factory=UsageSummary)
      turn_count: int = 0
      created_at: str = field(
          default_factory=lambda: datetime.now(timezone.utc).isoformat()
      )
      max_turns: int = 100
      compact_after: int = 40
      # claw-code-parity extensions
      history: HistoryLog = field(default_factory=HistoryLog)
      transcript: TranscriptStore = field(default_factory=TranscriptStore)
      permission_denials: List[PermissionDenial] = field(default_factory=list)
  
      def add_user_message(self, content: str) -> None:
          self.messages.append(ChatMessage(role="user", content=content))
          self.transcript.append(content)
          self.history.add("user_message", content[:100])
  
      def add_assistant_message(self, content: str) -> None:
          self.messages.append(ChatMessage(role="assistant", content=content))
          self.turn_count += 1
          self.transcript.append(content)
          self.history.add("assistant_message", f"turn={self.turn_count}")
  
      def compact_if_needed(self) -> None:
          """Keep conversation manageable by dropping old turns."""
          if len(self.messages) > self.compact_after:
              # Keep system prompt context (first msg if system) + last N messages
              keep = self.compact_after // 2
              sys_msgs = [m for m in self.messages[:1] if m.role == "system"]
              self.messages = sys_msgs + self.messages[-keep:]
  
      def build_openai_messages(self) -> List[Dict[str, Any]]:
          """Build the messages array for OpenAI-compatible API calls."""
          msgs = []
          if self.system_prompt:
              msgs.append({"role": "system", "content": self.system_prompt})
          msgs.extend(m.to_openai_dict() for m in self.messages)
          return msgs
  
      def persist(self) -> str:
        
  ```
  
  ### 文件: `src/backend/agents/hermes_research.py`
  ```py
  # -*- coding: utf-8 -*-
  """AgentsGroup2026 — Hermes-style Research Agent Module.
  
  Transforms the Research Agent from a read-only advisory role into a
  self-improving research agent inspired by NousResearch/hermes-agent:
  
  Architecture mapping (Hermes → AgentsGroup2026):
    - AIAgent class         → HermesResearchAgent
    - run_conversation()    → agent_loop()
    - toolsets.py           → RESEARCH_TOOLSET_DISTRIBUTIONS
    - prompt_builder.py     → build_research_system_prompt()
    - SOUL.md               → agent.hermes_config.soul_md
    - Memory/Skills nudge   → MEMORY_GUIDANCE / SKILLS_GUIDANCE
    - Delegate subagents    → delegate_task()
    - Session search        → session_search()
  
  Key Hermes characteristics adopted:
    1. Closed learning loop — auto-create skills from complex research
    2. Persistent memory — save research findings across sessions
    3. Probabilistic toolset distribution — web 90%, browser 70%, vision 50%
    4. SOUL.md — research persona
    5. Context files — AGENTS.md project context
    6. Tool-use enforcement — tools must be used, not just described
    7. Session search — cross-session recall of past research
  """
  
  from __future__ import annotations
  
  import random
  from dataclasses import dataclass, field
  from typing import Any, Dict, List, Optional
  
  from .models import (
      AgentProfile,
      AgentTemplateType,
      AgentPersonality,
      HermesAgentConfig,
      ToolsetDistribution,
  )
  
  
  # ══════════════════════════════════════════════════════════════
  # Hermes-style Toolset Distributions
  # Inspired by NousResearch/hermes-agent/toolset_distributions.py
  # ══════════════════════════════════════════════════════════════
  
  RESEARCH_TOOLSET_DISTRIBUTIONS: Dict[str, Dict[str, Any]] = {
      "general_research": {
          "description": "General domain research — literature review, data analysis, technical investigation",
          "toolsets": {
              "web": 90,
              "browser": 70,
              "vision": 50,
              "file": 80,
              "research": 95,
              "memory": 100,
              "skills": 100,
              "delegation": 30,
          },
      },
      "deep_analysis": {
          "description": "Deep analysis — systematic review, data verification, cross-referencing",
          "toolsets": {
              "web": 60,
              "file": 95,
              "research": 100,
              "code_execution": 80,
              "memory": 100,
              "vision": 40,
          },
      },
      "compliance_audit": {
          "description": "Standards and compliance verification",
          "toolsets": {
              "web": 85,
              "browser": 65,
              "file": 90,
              "research": 100,
              "code_execution": 70,
              "memory": 100,
          },
      },
      "technical_review": {
          "description": "Technical design review, architecture analysis, code review",
          "toolsets": {
              "web": 50,
              "file": 95,
              "code_execution": 90,
              "research": 100,
              "vision": 70,
              "memory": 100,
          },
      },
      "general_research": {
          "description": "General web research with all tools available",
          "toolsets": {
              "web": 90,
              "browser": 70,
              "vision": 50,
              "memory": 100,
              "skills": 100,
              "file": 60,
              "code_execution": 30,
          },
      },
  }
  
  # ══════════════════════════════════════════════════════════════
  # Hermes-style Toolset Definitions
  # Inspired by NousResearch/hermes-agent/toolsets.py
  # ══════════════════════════════════════════════════════════════
  
  HERMES_TOOLSETS: Dict[str, Dict[str, Any]] = {
      "web": {
          "description": "Web research and content extraction",
          "tools": ["web_search", "extract_content"],
      },
      "browser": {
          "description": "Browser automation for deep research",
          "tools": ["navigate_url", "screenshot", "click_element", "fill_form", "extract_content", "web_search"],
      },
      "file": {
          "description": "File read/write/search operations",
          "tools": ["read_file", "write_file", "list_directory", "search_files"],
      },
      "code_execution": {
          "description": "Run Python/shell for analysis and calculation",
          "tools": ["run_python", "run_shell"],
      },
      "vision": {
          "description": "Image/chart analysis for technical documents",
          "tools": ["screenshot"],
      },
      "research": {
          "description": "Research-specific tools — search, analysis, data retrieval",
          "tools": ["search_query", "data_lookup", "info_fetch", "analysis_engine"],
      },
      "memory": {
          "description": "Persistent memory and session search",
          "tools": ["memory_save", "memory_read", "session_search"],
      },
      "skills": {
          "description": "Skill management — list, view, create, patch",
          "tools": ["skill_list", "skill_view", "skill_manage"],
      },
      "delegation": {
          "description": "Spawn subagents for parallel research tasks",
          "tools": ["delegate_task"],
      },
  }
  
  
  def sample_toolsets(distribution_name: str) -> List[str]:
      """Sample toolsets based on distribution probabilities.
  
      Each toolset rolls independently — multiple can be active.
      Mirrors NousResearch/hermes-agent/toolset_distributions.py logic.
      """
      dist = RESEARCH_TOOLSET_DISTRIBUTIONS.get(distribution_name)
      if not dist:
          dist = RESEARCH_TOOLSET_DISTRIBUTIONS["general_research"]
  
      selected = []
      for toolset_name, probability in dist["toolsets"].items():
          if random.random() * 100 < probability:
              selected.append(toolset_name)
  
      # Ensure at least one toolset
      if not selected and dist["toolsets"]:
          highest = max(dist["toolsets"].items(), key=lambda x: x[1])
          selected.append(highest[0])
  
      return selected
  
  
  def resolve_tools(toolset_names: List[str]) -> List[str]:
      """Resolve toolset names to individual tool IDs."""
      tools: set[str] = set()
      for name in toolset_names:
          ts = HERMES_TOOLSETS.get(name)
          if ts:
              tools.update(ts["tools"])
      return sorted(tools)
  
  
  # ══════════════════════════════════════════════════════════════
  # Hermes-style System Prompt Builder
  # Inspired by NousResearch/hermes-agent/agent/prompt_builder.py
  # ══════════════════════════════════════════════════════════════
  
  MARINE_RESEARCHER_IDENTITY = (
      "You are AgentsGroup2026 Research Agent, an intelligent research agent "
      "built on the Hermes Agent architecture from Nous Research. "
      "You are a self-improving researcher with a closed learning loop — "
      "you create skills from experience, improve them during use, persist knowledge, "
      "and build deepening expertise across research sessions.\n\n"
      "Your research expertise includes:\n"
      "- Literature review, systematic analysis, and cross-referencing\n"
      "- Technical standards research and compliance verification\n"
      "- Data analysis, formula validation, and computational verification\n"
      "- Architecture review, design pattern analysis, and best practices\n"
      "- Multi-source information synthesis and knowledge extraction\n\n"
      "You communicate in Chinese with English technical terms preserved."
  )
  
  MEMORY_GUIDANCE = (
      "You have persistent memory across sessions. Save durable facts using the memory "
      "tool: research findings, domain conventions, technical citations, calculation results. "
      "Memory is injected into every turn, so keep it compact and focused on facts that "
      "will still matter later.\n"
      "Prioritize what reduces future user steering — the most valuable memory is one "
      "that prevents the user from having to correct or remind you again. "
      "Technical standards, validated formulas, and verified references are high-value.\n"
      "Do NOT save task progress, session outcomes, or temporary TODO state to memory; "
      "use session_search to recall those from past transcripts."
  )
  
  SKILLS_GUIDANCE = (
      "After completing a complex research task (5+ tool calls), validating a formula, "
      "or discovering a non-trivial analysis workflow, save the approach as a "
      "skill with skill_manage so you can reuse it next time.\n"
      "When using a skill and finding it outdated or wrong, "
      "patch it immediately with skill_manage(action='patch').\n"
      "Skills to prioritize: standard lookup workflows, calculation verification, "
      "literature review patterns, compliance audit procedures."
  )
  
  SESSION_SEARCH_GUIDANCE = (
      "When the user references something from a past research session or you suspect "
      "relevant cross-session context exists, use session_search to recall it before "
      "asking them to repeat themselves."
  )
  
  TOOL_USE_ENFORCEMENT = (
      "# Tool-use enforcement\n"
      "You MUST use your tools to take action — do not describe what you would do "
      "or plan to do without actually doing it. When you say you will perform a "
      "research action (e.g. 'I will check the standard', 'Let me verify the formula'), "
      "you MUST immediately make the corresponding tool call in the same response.\n"
      "Every response should either (a) contain tool calls that make progress, or "
      "(b) deliver a final research result to the user."
  )
  
  
  def build_research_system_prompt(
      agent: AgentProfile,
      active_toolsets: Optional[List[str]] = None,
  ) -> str:
      """Build the full Hermes-style system prompt for a research agent.
  
      Assembles: identity → memory guidance → skills guidance → tool enforcement
      → context files → SOUL.md persona.
  
      Mirrors NousResearch/hermes-agent/agent/prompt_builder.py structure.
      """
      sections: List[str] = []
  
      # 1. Identity (SOUL.md or default)
      hc = agent.hermes_config
      if hc and hc.soul_md:
          sections.append(hc.soul_md)
      else:
          sections.append(MARINE_RESEARCHER_IDENTITY)
  
      # 2. Memory guidance
      if hc and hc.memory_enabled:
          sections.append(MEMORY_GUIDANCE)
  
      # 3. Session search guidance
      if hc and hc.session_search_enabled:
          sections.append(SESSION_SEARCH_GUIDANCE)
  
      # 4. Skills guidance
      if hc and hc.skill_auto_create:
          sections.append(SKILLS_GUIDANCE)
  
      # 5. Tool-use enforcement
      sections.append(TOOL_USE_ENFORCEMENT)
  
      # 6. Available toolsets
      if active_toolsets:
          ts_lines = ["## Active Toolsets"]
          for ts_name in active_toolsets:
              ts = HERMES_TOOLSETS.get(ts_name)
              if ts:
                  ts_lines.append(f"- **{ts_name}**: {ts['description']} — tools: {', '.join(ts['tools'])}")
          sections.append("\n".join(ts_lines))
  
      # 7. Context files
      if hc and hc.context_files:
          context_header = "## Project Context\nThe following project context files are loaded:\n"
          sections.append(context_header + "\n".join(f"- {f}" for f in hc.context_files))
  
      # 8. Research reference files
      sections.append(
          "## Key Research Reference Files\n"
          "- `docs/requirements_analysis.md` — Project requirements and specifications\n"
          "- `docs/gap_analysis.md` — Gap analysis and improvement areas\n"
          "- `docs/architecture.md` — System architecture documentation\n"
          "- `config/settings.json` — System configuration and parameters"
      )
  
      return "\n\n".join(sections)
  
  
  # ══════════════════════════════════════════════════════════════
  # Hermes-style Agent Factory
  # ══════════════════════════════════════════════════════════════
  
  # Default SOUL.md for the research agent
  MARINE_RESEARCHER_SOUL = """# Research Agent
  
  You are AgentsGroup2026's research specialist, powered by Hermes Agent architecture.
  
  ## Core Identity
  I am a domain expert in systematic research, technical analysis, and knowledge synthesis.
  I research, validate, and advise — producing rigorous analysis backed by authoritative sources.
  
  ## Personality
  - Rigorous and methodical — every claim must cite a source or provide evidence
  - Proactive learner — after solving a complex problem, I save it as a skill
  - Memory-driven — I persist key findings so I never repeat the same research twice
  - Collaborative — I can delegate sub-research tasks to specialized agents
  
  ## Research Domains
  1. **Literature Review** — systematic search, source evaluation, cross-referencing
  2. **Technical Analysis** — architecture review, design patterns, best practices
  3. **Data Verification** — formula validation, calculation checking, data integrity
  4. **Standards Compliance** — industry standards, regulatory requirements, audit
  5. **Knowledge Synthesis** — multi-source integration, summary generation, insight extraction
  
  ## Behavioral Rules
  - Always cite specific sources, standards, or evidence
  - Never guess parameter ranges — look them up
  - After 5+ tool calls on a complex task, offer to save as a reusable skill
  - Write in Chinese, keep English for technical terms
  """
  
  
  def create_hermes_researcher(
      name: str = "Research Agent",
      distribution: str = "general_research",
      soul_md: str = "",
      can_delegate: bool = True,
  ) -> AgentProfile:
      """Create a Hermes-style research agent.
  
      Returns an AgentProfile with HermesAgentConfig attached,
      pre-configured with the research toolset distribution,
      SOUL.md persona, and self-improving skill/memory capabilities.
      """
      dist = RESEARCH_TOOLSET_DISTRIBUTIONS.get(distribution)
      if not dist:
          dist = RESEARCH_TOOLSET_DISTRIBUTIONS["general_research"]
  
      hermes_config = HermesAgentConfig(
          max_iterations=90,
          iteration_budget=90,
          toolset_distribution=ToolsetDistribution(
              name=distribution,
              description=dist["description"],
              toolsets=dict(dist["toolsets"]),
          ),
          enabled_toolsets=list(dist["toolsets"].keys()),
          disabled_toolsets=[],
          memory_enabled=True,
          session_search_enabled=True,
          skill_auto_create=True,
          soul_md=soul_md or MARINE_RESEARCHER_SOUL,
          context_files=[
              "AGENTS.md",
              "docs/SJTU_REQUIREMENTS_ANALYSIS.md",
              "docs/requirements_analysis.md",
              "docs/gap_analysis.md",
          ],
          can_delegate=can_delegate,
          max_subagents=3,
          platform="cli",
      )
  
      agent = AgentProfile(
          name=name,
          role="研究员 (Hermes Agent)",
          description=(
              "Hermes-style self-improving research agent — "
              "literature review, technical analysis, data verification, "
              "standards compliance, and knowledge synthesis. "
              "Closed learning loop with skills, memory, and session search."
          ),
          template_type=AgentTemplateType.HERMES_RESEARCHER,
          system_prompt="",  # Built dynamically via build_research_system_prompt()
          personality=AgentPersonality(
              tone="professional",
              language="zh-CN",
              expertise_areas=[
                  "literature review",
                  "technical analysis",
                  "data verification",
                 
  ```
  
  ### 文件: `src/backend/agents/models.py`
  ```py
  # -*- coding: utf-8 -*-
  """AgentsGroup2026 Agent Team Framework — Core Data Models.
  
  Inspired by Clawith platform architecture:
  - AgentTeam = Company (team-level resource sharing)
  - AgentProfile = Employee (individual agent with personality/skills/permissions)
  - ModelConfig = Model Pool entry
  - ToolDefinition = Tool catalog entry
  - SkillDefinition = Skill catalog entry
  """
  
  from __future__ import annotations
  
  import uuid
  from dataclasses import dataclass, field
  from datetime import datetime, timezone
  from enum import Enum
  from typing import Any, Dict, List, Optional
  
  
  # ── Enums ──────────────────────────────────────────────────────────────────
  
  
  class AgentState(Enum):
      """Agent lifecycle states."""
  
      IDLE = "idle"
      WORKING = "working"
      PAUSED = "paused"
      ERROR = "error"
      STOPPED = "stopped"
  
  
  class ToolCategory(Enum):
      """Tool classification categories."""
  
      GENERAL = "general"
      BROWSER = "browser"
      CODE_EXECUTION = "code_execution"
      COMMUNICATION = "communication"
      FILE_OPERATION = "file_operation"
      TRIGGERS = "triggers"
      DISCOVERY = "discovery"
      DIGITAL_TWIN = "digital_twin"
      # Hermes-style tool categories
      WEB = "web"
      VISION = "vision"
      MEMORY = "memory"
      SKILLS = "skills"
      DELEGATION = "delegation"
  
  
  class SkillCategory(Enum):
      """Skill classification categories."""
  
      GENERAL = "general"
      DIGITAL_TWIN = "digital_twin"
      AUTOMATION = "automation"
      # Hermes-style skill categories
      RESEARCH = "research"
      DOMAIN_KNOWLEDGE = "domain_knowledge"
  
  
  class Visibility(Enum):
      """Visibility level for teams/agents."""
  
      PUBLIC = "public"
      PRIVATE = "private"
      INTERNAL = "internal"
  
  
  class AccessLevel(Enum):
      """Permission access levels."""
  
      READ = "read"
      WRITE = "write"
      ADMIN = "admin"
  
  
  class AgentTemplateType(Enum):
      """Predefined agent template types."""
  
      RESEARCHER = "researcher"
      DEVELOPER = "developer"
      ANALYST = "analyst"
      ENGINEER = "engineer"
      COORDINATOR = "coordinator"
      CUSTOM = "custom"
      # Hermes-style agent types
      HERMES_RESEARCHER = "hermes_researcher"
      HERMES_DEVELOPER = "hermes_developer"
      HERMES_CREATIVE = "hermes_creative"
  
  
  # ── Dataclasses ────────────────────────────────────────────────────────────
  
  
  @dataclass
  class ModelConfig:
      """LLM model configuration entry."""
  
      model_id: str = ""
      provider: str = "anthropic"
      name: str = "claude-sonnet-4-20250514"
      max_tokens: int = 65536
      temperature: float = 0.7
      is_default: bool = False
      enabled: bool = True
      api_key: str = ""
      api_base_url: str = ""
  
      def __post_init__(self) -> None:
          if not self.model_id:
              self.model_id = str(uuid.uuid4())[:8]
  
      def to_dict(self) -> Dict[str, Any]:
          return {
              "model_id": self.model_id,
              "provider": self.provider,
              "name": self.name,
              "max_tokens": self.max_tokens,
              "temperature": self.temperature,
              "is_default": self.is_default,
              "enabled": self.enabled,
              "api_key": ("****" + self.api_key[-4:]) if len(self.api_key) >= 4 else ("****" if self.api_key else ""),
              "api_base_url": self.api_base_url,
              "has_api_key": bool(self.api_key),
          }
  
  
  @dataclass
  class ToolDefinition:
      """Tool catalog entry."""
  
      tool_id: str = ""
      name: str = ""
      description: str = ""
      category: ToolCategory = ToolCategory.BROWSER
      enabled: bool = True
      requires_approval: bool = False
      parameters: Dict[str, Any] = field(default_factory=dict)
      icon: str = "🔧"
      config_schema: Dict[str, Any] = field(default_factory=dict)
      config: Dict[str, Any] = field(default_factory=dict)
      is_default: bool = False
      source: str = "builtin"
  
      def __post_init__(self) -> None:
          if not self.tool_id:
              self.tool_id = str(uuid.uuid4())[:8]
  
      def to_dict(self) -> Dict[str, Any]:
          return {
              "tool_id": self.tool_id,
              "name": self.name,
              "description": self.description,
              "category": self.category.value,
              "enabled": self.enabled,
              "requires_approval": self.requires_approval,
              "parameters": self.parameters,
              "icon": self.icon,
              "config_schema": self.config_schema,
              "config": self.config,
              "is_default": self.is_default,
              "source": self.source,
          }
  
  
  @dataclass
  class SkillDefinition:
      """Skill catalog entry."""
  
      skill_id: str = ""
      name: str = ""
      description: str = ""
      category: SkillCategory = SkillCategory.GENERAL
      required: bool = False
      enabled: bool = True
      icon: str = "⚡"
      config_schema: Dict[str, Any] = field(default_factory=dict)
      config: Dict[str, Any] = field(default_factory=dict)
      is_default: bool = False
      source: str = "builtin"
      slug: str = ""
      required_tools: List[str] = field(default_factory=list)
      instructions: str = ""
  
      def __post_init__(self) -> None:
          if not self.skill_id:
              self.skill_id = str(uuid.uuid4())[:8]
  
      def to_dict(self) -> Dict[str, Any]:
          return {
              "skill_id": self.skill_id,
              "name": self.name,
              "description": self.description,
              "category": self.category.value,
              "required": self.required,
              "enabled": self.enabled,
              "icon": self.icon,
              "config_schema": self.config_schema,
              "config": self.config,
              "is_default": self.is_default,
              "source": self.source,
              "slug": self.slug,
              "required_tools": self.required_tools,
              "has_instructions": bool(self.instructions),
          }
  
  
  @dataclass
  class AgentPersonality:
      """Agent personality and behavior configuration."""
  
      tone: str = "professional"
      language: str = "zh-CN"
      expertise_areas: List[str] = field(default_factory=list)
      response_style: str = "concise"
      creativity: float = 0.5
  
      def to_dict(self) -> Dict[str, Any]:
          return {
              "tone": self.tone,
              "language": self.language,
              "expertise_areas": self.expertise_areas,
              "response_style": self.response_style,
              "creativity": self.creativity,
          }
  
  
  @dataclass
  class ToolsetDistribution:
      """Hermes-style probabilistic toolset distribution.
  
      Each toolset has a % probability of being available per turn.
      Inspired by NousResearch/hermes-agent toolset_distributions.py.
      """
  
      name: str = "default"
      description: str = ""
      toolsets: Dict[str, int
  ```
  
  (后续文件因 token 预算已省略)
  
  (后续文件因 token 预算已省略)
  
  
  ## 前序步骤的产出 (递进式摘要)
  
  ### 步骤 01: pm_decompose
  任务: 设计共签机制与配置即契约的治理桩，使业务域主与架构师共同签署阈值的反射修改
  步骤: pm_decompose
  📋 任务: 8665633b-cad
  🤖 Agent: PM (project_manager)
  📂 工作目录: /Users/panglaohu/Downloads/AgentsGroup2026
  🔧 执行方式: DeepSeek API (直连)
  ────────────────────────────────────────────────────────────
  你是 AgentsGroup2026 系统的 PM (project_manager)。
  你是项目经理 (PM)。请对以下任务进行分解和规划:
  设计共签机制与配置即契约的治理桩，使业务域主与架构师共同签署阈值的反射修改
  Architect + 业务域主
  ## 📂 项目上下文 (系统自动预加载)
  ### 项目文件结构 (src/ 目录)
  ### 文件: `src/backend/agents/agent_toolbox.py`
  ### 文件: `src/backend/agents/chat_harness.py`
  **变更文件 (5):**
    - `src/backend/agents/models.py`
    - `src/backend/agents/governance_store.py`
    - `src/backend/agents/governance_stub.py`
    - `src/backend/agents/agent_toolbox.py`
    - `src/backend/main.py`
  **子任务拆解:**
    - *任务ID:** `PM-20260507-001`
    - *任务名称:** 设计共签机制与配置即契约的治理桩，使业务域主与架构师共同签署阈值的反射修改
    - *负责人:** 项目经理 (PM)
    - *日期:** 2026-05-07
    - **子步骤 1.1: 定义阈值元数据模型**
    - **子步骤 1.2: 设计治理桩接口 (Governance Stub)**
    - **子步骤 2.1: 实现共签状态机**
    - **子步骤 2.2: 实现反射修改逻辑**
  
  ### 步骤 02: research (完整产出)
  
  # 研究分析 — researcher
  
  任务: 设计共签机制与配置即契约的治理桩，使业务域主与架构师共同签署阈值的反射修改
  步骤: research
  Agent: build_researcher
  
  ---
  
  📋 任务: 8665633b-cad
  🤖 Agent: Researcher (researcher)
  📂 工作目录: /Users/panglaohu/Downloads/AgentsGroup2026
  🔧 执行方式: DeepSeek API (直连)
  ⏱️ 超时: 1200s
  ────────────────────────────────────────────────────────────
  📝 提示词:
    你是 AgentsGroup2026 系统的 Researcher (researcher)。
    请执行以下开发任务:
    
    你是技术研究员。请对以下任务进行技术调研:
    
    ## 任务
    设计共签机制与配置即契约的治理桩，使业务域主与架构师共同签署阈值的反射修改
    Architect + 业务域主
    
    ## 📂 项目上下文 (系统自动预加载)
    
    ### 项目文件结构 (src/ 目录)
    ```
    src/frontend/agent-team-config.html
    src/frontend/datacenter-ratchet-evolution.html
    src/frontend/index.html
    src/frontend/login.html
    src/frontend/plaza-dark.html
    src/frontend/plaza-old.html
    src/frontend/plaza-wabisabi-v2.html
    src/frontend/plaza-wabisabi.html
    src/frontend/plaza.html
    src/frontend/system-evolution.html
    src/frontend/tasks.html
    src/frontend/css/agent-team-config.css
    src/frontend/css/openbridge-theme.css
    src/frontend/css/ws-theme-bridge.css
    src/frontend/js/agent-team-config.js
    src/frontend/js/i18n.js
    src/frontend/js/nav-sidebar.js
    src/backend/__init__.py
    src/backend/agent_team_api.py
    src/backend/main.py
    src/backend/main.py.bak
    src/backend/startup_check.py
    src/backend/startup_validator.py
    src/backend/agents/__init__.py
    src/backend/agents/ab_testing.py
    src/backend/agents/agent_loop.py
    src/backend/agents/agent_toolbox.py
    src/backend/agents/api.py
    src/backend/agents/chat_harness.py
    src/backend/agents/execution_registry.py
    src/backend/agents/hermes_research.py
    src/backend/agents/knowledge_base.py
    src/backend/agents/models.py
    src/backend/agents/plaza.py
    src/backend/agents/plaza_engine.py
    src/backend/agents/plaza_routes.py
    src/backend/agents/plaza_routes.py.bak
    src/backend/agents/plaza_store.py
    src/backend/agents/session_store.py
    src/backend/agents/skill_registry.py
    src/backend/agents/task_engine.py
    src/backend/agents/task_store.py
    src/backend/agents/team_manager.py
    src/backend/agents/team_store.py
    src/backend/agents/tool_executor.py
    src/backend/agents/tool_registry.py
    src/backend/agents/tts_routes.py
    src/backend/agents/teams/__init__.py
    src/backend/agents/teams/ai_coding_team.py
    src/backend/agents/teams/build_team.py
    src/backend/agents/teams/energy_team.py
    src/backend/agents/skills/__init__.py
    src/backend/agents/skills/greeting.py
    src/backend/agents/skills/hello.py
    src/backend/scripts/__init__.py
    src/backend/scripts/validate_startup.py
    src/backend/scripts/validate_telemetry.py
    src/backend/monitoring/__init__.py
    src/backend/monitoring/collector.py
    src/backend/monitoring/models.py
    src/backend/monitoring/plaza_monitor.py
    src/backend/monitoring/plaza_monitor.py.bak
    src/backend/monitoring/sampler.py
    src/backend/channels/__init__.py
    src/backend/channels/bridge_chat.py
    src/backend/channels/marine_base.py
    src/backend/channels/openclaw_sync.py
    src/backend/channels/openclaw_sync.py.bak
    src/backend/channels/system_evolution.py
    src/docs/agent_handoffs/1ce78c0e-062_architecture_20260503T045804.md
    src/docs/agent_handoffs/1ce78c0e-062_deploy_FAILED_20260503T050220.md
    src/docs/agent_handoffs/1ce78c0e-062_develop_20260503T045845.md
    src/docs/agent_handoffs/1ce78c0e-062_develop_20260503T050025.md
    src/docs/agent_handoffs/1ce78c0e-062_develop_20260503T050150.md
    src/docs/agent_handoffs/1ce78c0e-062_pm_decompose_20260503T045724.md
    src/docs/agent_handoffs/1ce78c0e-062_research_20260503T045739.md
    src/docs/agent_handoffs/1ce78c0e-062_task_init_20260503T045659.md
    src/docs/agent_handoffs/1ce78c0e-062_test_20260503T045905.md
    src/docs/agent_handoffs/1ce78c0e-062_test_20260503T050050.md
    src/docs/agent_handoffs/1ce78c0e-062_test_20260503T050210.md
    src/docs/agent_handoffs/23cb267e-4e0_executor_started_20260503T114540.md
    src/docs/agent_handoffs/38e22004-b64_architecture_20260503T045011.md
    src/docs/agent_handoffs/38e22004-b64_pm_decompose_20260503T044921.md
    src/docs/agent_handoffs/38e22004-b64_research_20260503T044941.md
    src/docs/agent_handoffs/38e22004-b64_task_init_20260503T044856.md
    src/docs/agent_handoffs/3bde709e-2fe_executor_started_20260507T031444.md
    src/docs/agent_handoffs/4b17f83b-805_architecture_20260507T003640.md
    src/docs/agent_handoffs/4b17f83b-805_deploy_FAILED_20260507T004132.md
    src/docs/agent_handoffs/4b17f83b-805_develop_FAILED_20260507T003706.md
    src/docs/agent_handoffs/4b17f83b-805_develop_FAILED_20260507T003913.md
    src/docs/agent_handoffs/4b17f83b-805_develop_FAILED_20260507T004040.md
    src/docs/agent_handoffs/4b17f83b-805_executor_started_20260507T003435.md
    src/docs/agent_handoffs/4b17f83b-805_pm_decompose_20260507T003510.md
    src/docs/agent_handoffs/4b17f83b-805_research_20260507T003555.md
    src/docs/agent_handoffs/4b17f83b-805_test_FAILED_20260507T003732.md
    src/docs/agent_handoffs/4b17f83b-805_test_FAILED_20260507T003939.md
    src/docs/agent_handoffs/4b17f83b-805_test_FAILED_20260507T004102.md
    src/docs/agent_handoffs/6f911ba3-822_architecture_20260507T003740.md
    src/docs/agent_handoffs/6f911ba3-822_deploy_FAILED_20260507T004337.md
    src/docs/agent_handoffs/6f911ba3-822_develop_FAILED_20260507T003806.md
    src/docs/agent_handoffs/6f911ba3-822_develop_FAILED_20260507T004113.md
    src/docs/agent_handoffs/6f911ba3-822_develop_FAILED_20260507T004235.md
    src/docs/agent_handoffs/6f911ba3-822_executor_started_20260507T003435.md
    src/docs/agent_handoffs/6f911ba3-822_pm_decompose_20260507T003510.md
    src/docs/agent_handoffs/6f911ba3-822_research_20260507T003550.md
    src/docs/agent_handoffs/6f911ba3-822_test_FAILED_20260507T003827.md
    src/docs/agent_handoffs/6f911ba3-822_test_FAILED_20260507T004134.md
    src/docs/agent_handoffs/6f911ba3-822_test_FAILED_20260507T004311.md
    src/docs/agent_handoffs/7c934759-39e_architecture_20260505T010014.md
    src/docs/agent_handoffs/7c934759-39e_develop_20260505T010359.md
    src/docs/agent_handoffs/7c934759-39e_develop_20260505T012357.md
    src/docs/agent_handoffs/7c934759-39e_develop_FAILED_20260505T011447.md
    src/docs/agent_handoffs/7c934759-39e_executor_started_20260505T005814.md
    src/docs/agent_handoffs/7c934759-39e_pm_decompose_20260505T005849.md
    src/docs/agent_handoffs/7c934759-39e_research_20260505T005919.md
    src/docs/agent_handoffs/7c934759-39e_test_FAILED_20260505T011016.md
    src/docs/agent_handoffs/7c934759-39e_test_FAILED_20260505T011949.md
    src/docs/agent_handoffs/7c934759-39e_test_FAILED_20260505T012853.md
    src/docs/agent_handoffs/8a5071c5-834_architecture_20260507T003655.md
    src/docs/agent_handoffs/8a5071c5-834_deploy_FAILED_20260507T004051.md
    src/docs/agent_handoffs/8a5071c5-834_develop_FAILED_20260507T003716.md
    src/docs/agent_handoffs/8a5071c5-834_develop_FAILED_20260507T003903.md
    src/docs/agent_handoffs/8a5071c5-834_develop_FAILED_20260507T004005.md
    src/docs/agent_handoffs/8a5071c5-834_executor_started_20260507T003435.md
    src/docs/agent_handoffs/8a5071c5-834_pm_decompose_20260507T003510.md
    src/docs/agent_handoffs/8a5071c5-834_research_20260507T003540.md
    src/docs/agent_handoffs/8a5071c5-834_test_FAILED_20260507T003737.md
    src/docs/agent_handoffs/8a5071c5-834_test_FAILED_20260507T003929.md
    src/docs/agent_handoffs/8a5071c5-834_test_FAILED_20260507T004031.md
    src/docs/agent_handoffs/a77bd3b9-2db_architecture_20260507T003625.md
    src/docs/agent_handoffs/a77bd3b9-2db_deploy_FAILED_20260507T004102.md
    src/docs/agent_handoffs/a77bd3b9-2db_develop_FAILED_20260507T003646.md
    src/docs/agent_handoffs/a77bd3b9-2db_develop_FAILED_20260507T003838.md
    src/docs/agent_handoffs/a77bd3b9-2db_develop_FAILED_20260507T004005.md
    src/docs/agent_handoffs/a77bd3b9-2db_executor_started_20260507T003435.md
    src/docs/agent_handoffs/a77bd3b9-2db_pm_decompose_20260507T003515.md
    src/docs/agent_handoffs/a77bd3b9-2db_research_20260507T003545.md
    src/docs/agent_handoffs/a77bd3b9-2db_test_FAILED_20260507T003712.md
    src/docs/agent_handoffs/a77bd3b9-2db_test_FAILED_20260507T003904.md
    src/docs/agent_handoffs/a77bd3b9-2db_test_FAILED_20260507T004042.md
    src/docs/agent_handoffs/ba3b66b1-a77_architecture_20260505T154317.md
    src/docs/agent_handoffs/ba3b66b1-a77_deploy_FAILED_20260505T154903.md
    src/docs/agent_handoffs/ba3b66b1-a77_develop_FAILED_20260505T154353.md
    src/docs/agent_handoffs/ba3b66b1-a77_develop_FAILED_20260505T154600.md
    src/docs/agent_handoffs/ba3b66b1-a77_develop_FAILED_20260505T154807.md
    src/docs/agent_handoffs/ba3b66b1-a77_executor_started_20260505T153921.md
    src/docs/agent_handoffs/ba3b66b1-a77_pm_decompose_20260505T153951.md
    src/docs/agent_handoffs/ba3b66b1-a77_research_20260505T154041.md
    src/docs/agent_handoffs/ba3b66b1-a77_test_FAILED_20260505T154424.md
    src/docs/agent_handoffs/ba3b66b1-a77_test_FAILED_20260505T154631.md
    ... (共 256 个 src/ 文件)
    
    ```
    
    ### 文件: `src/backend/agents/agent_toolbox.py`
    ```py
    """AgentToolbox — function-calling tools for code-aware agents.
    
    Gives Developer / QA agents the ability to read, grep, write, and execute code
    in the project so they don't have to hallucinate file contents.
    
    All tool calls are scoped to the project root and write operations are
    restricted to a safe allowlist (src/, tests/, docs/, config/, public/).
    
    Each tool returns a JSON-serializable dict suitable for OpenAI/DeepSeek
    function-calling protocol.
    """
    from __future__ import annotations
    
    import json
    import logging
    import os
    import re
    import shlex
    import subprocess
    import time
    from pathlib import Path
    from typing import Any, Dict, List, Optional, Tuple
    
    logger = logging.getLogger("AgentToolbox")
    
    PROJECT_ROOT = Path(__file__).resolve().parents[3]  # src/backend/agents/ -> root
    ALLOWED_WRITE_PREFIXES = ("src/", "tests/", "docs/", "config/", "public/",
                               "storage/agent_workspaces/", "storage/pipeline_runs/")
    MAX_FILE_BYTES = 256 * 1024   # 256KB per read
    MAX_GREP_HITS = 200
    MAX_EXEC_OUTPUT = 32 * 1024   # 32KB stdout/stderr cap
    
    
    # ═════════════════════════════════════════════════════════════════
    # OpenAI / DeepSeek function-calling tool schema (V4 supports this)
    # ═════════════════════════════════════════════════════════════════
    
    TOOL_SCHEMA: List[Dict[str, Any]] = [
        {
            "type": "function",
            "function": {
                "name": "read_file",
                "description": (
                    "读取项目里某个文件的内容。优先使用此工具理解现有代码，再基于实际代码做修改。"
                    "只能读取项目根目录下的文件。"
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "项目相对路径，如 src/backend/channels/marine_base.py",
                        },
                        "start_line": {"type": "integer", "description": "起始行 (1-based, 可选)", "default": 1},
                        "end_line": {"type": "integer", "description": "结束行 (1-based, 可选)", "default": 0},
                    },
                    "required": ["path"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "grep",
                "description": (
                    "在项目中按正则搜索文本。用于查找类/函数/枚举值的真实定义位置。"
                    "返回每个匹配的文件路径、行号、行内容。"
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "pattern": {"type": "string", "description": "正则表达式"},
                        "include": {
                            "type": "string",
                            "description": "glob 限定，如 src/backend/**/*.py",
                            "default": "**/*",
                        },
                        "max_hits": {"type": "integer", "default": 50},
                    },
                    "required": ["pattern"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "list_files",
                "description": "列出某个目录下的所有文件（递归）。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "项目相对目录"},
                        "max_depth": {"type": "integer", "default": 3},
                    },
                    "required": ["path"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "write_file",
                "description": (
                    "向项目写入或新建文件。只能写入 src/, tests/, docs/, config/, public/ 下。"
                    "如果目标已存在，旧内容会先备份为 .bak。优先创建新文件而非整文件覆盖大文件。"
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "项目相对路径"},
                        "content": {"type": "string", "description": "完整文件内容"},
                        "create_only": {
                            "type": "boolean",
                            "description": "为 true 时仅在文件不存在时写入",
                            "default": False,
                        },
                    },
                    "required": ["path", "content"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "patch_file",
                "description": (
                    "对已有文件做精准搜索-替换。比 write_file 安全，因为它要求你先看到原文。"
                    "search 必须是文件中存在的、唯一的连续片段。"
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string"},
                        "search": {"type": "string", "description": "要被替换的原文片段（必须唯一）"},
                        "replace": {"type": "string", "description": "替换为的新内容"},
                    },
                    "required": ["path", "search", "replace"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "run_python",
                "description": (
                    "在项目 venv 中执行一段 Python 代码（cwd=src/backend）。"
                    "用于验证 import 是否成功、检查类的属性等。最长执行 30s。"
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "string", "description": "要执行的 Python 代码"},
                        "timeout": {"type": "integer", "default": 30},
                    },
                    "required": ["code"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "run_pytest",
                "description": (
                    "运行 pytest，可指定路径或 -k 表达式。仅 QA agent 使用。"
                    "返回最后 60 行输出。"
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "target": {"type": "string", "description": "测试路径或 -k 表达式", "default": ""},
                        "timeout": {"type": "integer", "default": 120},
                    },
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "finish",
                "description": (
                    "声明任务完成。Agent 调用此工具表示完成本步骤的所有工作，并附上简短总结。"
                    "调用后循环终止。"
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "summary": {"type": "string", "description": "本步骤完成情况的简短总结"},
                        "files_changed": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "本步骤修改/新建的文件路径列表",
                            "default": [],
                        },
                    },
                    "required": ["summary"],
                },
            },
        },
    ]
    
    
    def _safe_path(rel: str) -> Path:
        """Resolve a project-relative path, refusing escapes."""
        if not rel:
            raise ValueError("empty path")
        p = (PROJECT_ROOT / rel).resolve()
        try:
            p.relative_to(PROJECT_ROOT)
        except ValueError:
            raise PermissionError(f"path escapes project root: {rel}")
        return p
    
    
    def _is_allowed_write(rel: str) -> bool:
        rel = rel.replace("\\", "/")
        return any(rel.startswith(p) for p in ALLOWED_WRITE_PREFIXES)
    
    
    # ═════════════════════════════════════════════════════════════════
    # Tool implementations
    # ═════════════════════════════════════════════════════════════════
    
    def tool_read_file(path: str, start_line: int = 1, end_line: int = 0) -> Dict[str, Any]:
        try:
            p = _safe_path(path)
            if not p.is_file():
                return {"ok": False, "error": f"not a file: {path}"}
            size = p.stat().st_size
            if size > MAX_FILE_BYTES * 4:
                return {
                    "ok": False,
                    "error": f"file too large ({size}B). Use grep to find the relevant section first.",
                }
            text = p.read_text(encoding="utf-8", errors="replace")
            lines = text.splitlines()
            total = len(lines)
            if end_line and end_line > 0:
                lines = lines[max(0, start_line - 1):end_line]
            elif start_line > 1:
                lines = lines[start_line - 1:]
            out = "\n".join(lines)
            if len(out) > MAX_FILE_BYTES:
                out = out[:MAX_FILE_BYTES] + "\n…(truncated)"
            return {"ok": True, "path": path, "total_lines": total, "content": out}
        except Exception as e:
            return {"ok": False, "error": str(e)}
    
    
    def tool_grep(pattern: str, include: str = "**/*", max_hits: int = 50) -> Dict[str, Any]:
        try:
            regex = re.compile(pattern)
        except re.error as e:
            return {"ok": False, "error": f"bad regex: {e}"}
        max_hits = min(max_hits, MAX_GREP_HITS)
        hits: List[Dict[str, Any]] = []
        for fp in PROJECT_ROOT.glob(include):
            if not fp.is_file():
                continue
            # Skip irrelevant
            rel = str(fp.relative_to(PROJECT_ROOT))
            if any(seg in rel for seg in ("/node_modules/", "/.git/", "/__pycache__/", "/venv/", ".bak")):
                continue
            try:
                with fp.open("r", encoding="utf-8", errors="replace") as f:
                    for i, line in enumerate(f, 1):
                        if regex.search(line):
                            hits.append({"path": rel, "line": i, "text": line.rstrip()[:200]})
                            if len(hits) >= max_hits:
                                return {"ok": True, "hits": hits, "truncated": True}
            except Exception:
                continue
        return {"ok": True, "hits": hits, "truncated": False}
    
    
    def tool_list_files(path: str, max_depth: int = 3) -> Dict[str, Any]:
        try:
            p = _safe_path(path)
            if not p.is_dir():
                return {"ok": False, "error": f"not a directory: {path}"}
            out: List[str] = []
            base_depth = len(p.parts)
            for root, dirs, files in os.walk(p):
                depth = len(Path(root).parts) - base_depth
                if depth > max_depth:
                    dirs[:] = []
                    continue
                dirs[:] = [d for d in dirs
                           if not d.startswith(".")
                           and d not in ("node_modules", "__pycache__", "venv")]
                for f in files:
                    if f.endswith((".pyc", ".bak")):
                        continue
                    rel = str((Path(root) / f).relative_to(PROJECT_ROOT))
                    out.append(rel)
                    if len(out) >= 500:
                        return {"ok": True, "files": out, "truncated": True}
            return {"ok": True, "files": out, "truncated": False}
        except Exception as e:
            return {"ok": False, "error": str(e)}
    
    
    def tool_write_file(path: str, content: str, create_only: bool = False) -> Dict[str, Any]:
        try:
            if not _is_allowed_write(path):
                return {"ok": False, "error": f"write denied (outside allowed dirs): {path}"}
            p = _safe_path(path)
            if p.exists() and create_only:
                return {"ok": False, "error": f"file exists and create_only=True: {path}"}
            # Shrink-replace guard
            if p.is_file():
                old_size = p.stat().st_size
                if old_size > 2048 and len(content) < old_size * 0.5:
                    return {
                        "ok": False,
                        "error": (
                            f"shrink-replace blocked: new {len(content)}B "
                            f"< 50% of existing {old_size}B. "
                            f"Use patch_file for incremental edits, or write a new file."
                        ),
                    }
                # Backup
                bak = p.with_suffix(p.suffix + ".bak")
                try:
                    bak.write_bytes(p.read_bytes())
                except Exception:
                    pass
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")
            return {"ok": True, "path": path, "bytes": len(content), "created": not p.exists()}
        except Exception as e:
            return {"ok": False, "error": str(e)}
    
    
    def tool_patch_file(path: str, search: str, replace: str) -> Dict[str, Any]:
        try:
            if not _is_allowed_write(path):
                return {"ok": False, "error": f"write denied: {path}"}
            p = _safe_path(path)
            if not p.is_file():
                return {"ok": False, "error": f"file not found: {path}"}
            text = p.read_text(encoding="utf-8")
            cnt = text.count(search)
            if cnt == 0:
                return {"ok": False, "error": "search pattern not found in file"}
            if cnt > 1:
                return {
                    "ok": False,
                    "error": f"search pattern matches {cnt} times — must be unique. Add more context.",
                }
            new_text = text.replace(search, replace, 1)
            bak = p.with_suffix(p.suffix + ".bak")
            try:
                bak.write_text(text, encoding="utf-8")
            except Exception:
                pass
            p.write_text(new_text, encoding="utf-8")
            return {"ok": True, "path": path, "old_bytes": len(text), "new_bytes": len(new_text)}
        except Exception as e:
            return {"ok": False, "error": str(e)}
    
    
    def _run_subprocess(cmd: List[str], cwd: Path, timeout: int) -> Dict[str, Any]:
        start = time.time()
        try:
            proc = subprocess.run(
                cmd, cwd=str(cwd), capture_output=True, text=True,
                timeout=timeout,
                env={**os.environ, "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1"},
            )
            elapsed = time.time() - start
            out = proc.stdout or ""
            err = proc.stderr or ""
            if len(out) > MAX_EXEC_OUTPUT:
                out = "…(truncated)\n" + out[-MAX_EXEC_OUTPUT:]
            if len(err) > MAX_EXEC_OUTPUT:
                err = "…(truncated)\n" + err[-MAX_EXEC_OUTPUT:]
            return {
                "ok": True,
                "exit_code": proc.returncode,
                "stdout": out,
                "stderr": err,
                "elapsed_sec": round(elapsed, 2),
            }
        except subprocess.TimeoutExpired:
            return {"ok": False, "error": f"timeout after {timeout}s"}
        except Exception as e:
            return {"ok": False, "error": str(e)}
    
    
    def tool_run_python(code: str, timeout: int = 30) -> Dict[str, Any]:
        venv_py = PROJECT_ROOT / "venv" / "bin" / "python"
        py = str(venv_py) if venv_py.exists() else "python3"
        cwd = PROJECT_ROOT / "src" / "backend"
        return _run_subprocess([py, "-c", code], cwd, timeout)
    
    
    def tool_run_pytest(target: str = "", timeout: int = 120) -> Dict[str, Any]:
        venv_py = PROJECT_ROOT / "venv" / "bin" / "python"
        py = str(venv_py) if venv_py.exists() else "python3"
        args = [py, "-m", "pytest", "-q", "--tb=short", "--maxfail=5"]
        if target:
            if target.startswith("-k") or "::" in target or target.endswith(".py"):
                if target.startswith("-k"):
                    args += target.split(maxsplit=1)
                else:
                    args.append(target)
            else:
                args += ["-k", target]
        return _run_subprocess(args, PROJECT_ROOT, timeout)
    
    
    # ═════════════════════════════════════════════════════════════════
    # Dispatcher
    # ═════════════════════════════════════════════════════════════════
    
    _DISPATCH = {
        "read_file": l
    ```
    
    ### 文件: `src/backend/agents/chat_harness.py`
    ```py
    # -*- coding: utf-8 -*-
    """AgentsGroup2026 Chat Harness — Unified LLM Chat Module.
    
    Inspired by claw-code's QueryEngine + Runtime architecture:
    - Single chat module used by ALL agents, bridge commands, and sessions
    - Provider abstraction: OpenAI-compatible, Anthropic, DeepSeek, local Ollama
    - Session/turn management, token budgeting, transcript compaction
    - Tool invocation pipeline with permission checks
    - Streaming support via SSE-compatible generator
    
    Usage:
        harness = ChatHarness.from_config(config_path="config/settings.json")
        result = await harness.chat(agent_id, prompt, tools=[...])
    
        # Or streaming:
        async for chunk in harness.stream_chat(agent_id, prompt):
            ...
    """
    
    from __future__ import annotations
    
    import json
    import logging
    import os
    import time
    from collections import deque
    from dataclasses import dataclass, field
    from datetime import datetime, timezone
    from enum import Enum
    from pathlib import Path
    from typing import Any, AsyncIterator, Callable, Dict, List, Optional, Tuple
    from uuid import uuid4
    
    from .session_store import (
        StoredSession, TranscriptStore,
        save_session, load_session as _load_stored_session,
        list_sessions as _list_stored_sessions,
        search_sessions,
    )
    from .execution_registry import (
        HistoryLog, ToolPermissionContext, PermissionDenial,
        RoutedMatch, ToolPool, assemble_tool_pool,
        PortRuntime, build_execution_registry,
    )
    
    logger = logging.getLogger(__name__)
    
    
    # ═══════════════════════════════════════════════════════════════
    # UltraPlan — Agentic Planning + Execution Pipeline
    # Inspired by Clawith's plan→act→observe→reflect loop
    # ═══════════════════════════════════════════════════════════════
    
    
    class PlanStepStatus(Enum):
        """Status of a single plan step."""
        PENDING = "pending"
        RUNNING = "running"
        COMPLETED = "completed"
        FAILED = "failed"
        SKIPPED = "skipped"
    
    
    @dataclass
    class PlanStep:
        """A single step in an execution plan."""
        step_id: int = 0
        action: str = ""            # e.g. "tool_call", "think", "respond", "delegate"
        tool_name: str = ""         # Tool to invoke (if action == "tool_call")
        tool_args: Dict[str, Any] = field(default_factory=dict)
        description: str = ""       # Human-readable description
        status: PlanStepStatus = PlanStepStatus.PENDING
        result: str = ""
        error: str = ""
        duration_ms: float = 0.0
        depends_on: List[int] = field(default_factory=list)
    
        def to_dict(self) -> Dict[str, Any]:
            return {
                "step_id": self.step_id,
                "action": self.action,
                "tool_name": self.tool_name,
                "description": self.description,
                "status": self.status.value,
                "result": self.result[:500] if self.result else "",
                "error": self.error,
                "duration_ms": self.duration_ms,
                "depends_on": self.depends_on,
            }
    
    
    @dataclass
    class ExecutionPlan:
        """An ordered plan of steps to fulfill a user request."""
        plan_id: str = field(default_factory=lambda: uuid4().hex[:8])
        goal: str = ""
        steps: List[PlanStep] = field(default_factory=list)
        created_at: str = field(
            default_factory=lambda: datetime.now(timezone.utc).isoformat()
        )
        status: str = "pending"  # pending / running / completed / failed
        final_response: str = ""
    
        def add_step(self, action: str, description: str = "",
                     tool_name: str = "", tool_args: Optional[Dict[str, Any]] = None,
                     depends_on: Optional[List[int]] = None) -> PlanStep:
            step = PlanStep(
                step_id=len(self.steps) + 1,
                action=action,
                tool_name=tool_name,
                tool_args=tool_args or {},
                description=description,
                depends_on=depends_on or [],
            )
            self.steps.append(step)
            return step
    
        @property
        def completed_steps(self) -> int:
            return sum(1 for s in self.steps if s.status == PlanStepStatus.COMPLETED)
    
        @property
        def progress(self) -> float:
            if not self.steps:
                return 1.0
            return self.completed_steps / len(self.steps)
    
        def to_dict(self) -> Dict[str, Any]:
            return {
                "plan_id": self.plan_id,
                "goal": self.goal,
                "status": self.status,
                "steps": [s.to_dict() for s in self.steps],
                "progress": round(self.progress, 2),
                "created_at": self.created_at,
            }
    
    
    # Plan builder: analyzes prompt keywords to auto-generate execution steps
    def build_plan_from_prompt(prompt: str, available_tools: List[str] = None) -> ExecutionPlan:
        """Build an execution plan by analyzing the prompt intent.
    
        This is a rule-based planner that maps keywords to tool invocations.
        When an LLM is available, the plan can be refined by the model.
        """
        plan = ExecutionPlan(goal=prompt[:200])
        lower = prompt.lower()
        tools = set(available_tools or [])
    
        # Multi-domain research
        if any(kw in lower for kw in ["研究", "分析", "调研", "research", "investigate"]):
            plan.add_step("tool_call", "网络搜索相关资料", tool_name="web_search",
                           tool_args={"query": prompt[:100]})
            plan.add_step("think", "整理搜索结果")
            plan.add_step("tool_call", "保存研究发现", tool_name="memory_save",
                           tool_args={"key": f"research_{uuid4().hex[:6]}", "content": ""})
            plan.add_step("respond", "生成研究报告")
    
        # General — single-step
        else:
            plan.add_step("think", "理解用户意图")
            plan.add_step("respond", "生成回复")
    
        return plan
    
    
    # Middleware hook type for plan interception
    PlanMiddleware = Callable[[ExecutionPlan], ExecutionPlan]
    
    
    # ═══════════════════════════════════════════════════════════════
    # Provider Abstraction
    # ═══════════════════════════════════════════════════════════════
    
    
    class LLMProvider(Enum):
        """Supported LLM providers."""
        OPENAI = "openai"
        ANTHROPIC = "anthropic"
        DEEPSEEK = "deepseek"
        OPENROUTER = "openrouter"
        LOCAL = "local"         # Ollama / vLLM / local OpenAI-compatible
        GITHUB = "github"       # GitHub Copilot models
        QWEN = "qwen"
    
    
    @dataclass
    class ProviderConfig:
        """LLM provider connection configuration."""
        provider: LLMProvider = LLMProvider.DEEPSEEK
        api_key: str = ""
        api_base_url: str = ""
        model: str = "deepseek-v4-pro"
        max_tokens: int = 65536  # DeepSeek V4: 64K output
        temperature: float = 0.2
        timeout: float = 1200.0  # Long timeout for big code generations
        thinking: Optional[Dict[str, str]] = None  # e.g. {"type": "enabled"}
        reasoning_effort: str = ""  # "low" | "medium" | "high"
    
        # Default endpoints per provider
        _DEFAULT_URLS: dict = field(default_factory=lambda: {
            LLMProvider.OPENAI: "https://api.openai.com/v1",
            LLMProvider.ANTHROPIC: "https://api.anthropic.com/v1",
            LLMProvider.DEEPSEEK: "https://api.deepseek.com",
            LLMProvider.OPENROUTER: "https://openrouter.ai/api/v1",
            LLMProvider.LOCAL: "http://127.0.0.1:11434/v1",
            LLMProvider.GITHUB: "https://models.inference.ai.azure.com",
            LLMProvider.QWEN: "https://dashscope.aliyuncs.com/compatible-mode/v1",
        }, repr=False)
    
        def resolve_base_url(self) -> str:
            if self.api_base_url:
                return self.api_base_url.rstrip("/")
            return self._DEFAULT_URLS.get(self.provider, "http://127.0.0.1:11434/v1")
    
        @classmethod
        def from_env(cls) -> "ProviderConfig":
            """Build config from environment variables."""
            provider_str = os.getenv("AG_LLM_PROVIDER", "deepseek")
            try:
                provider = LLMProvider(provider_str)
            except ValueError:
                provider = LLMProvider.DEEPSEEK
    
            return cls(
                provider=provider,
                api_key=os.getenv("AG_LLM_API_KEY", os.getenv("DEEPSEEK_API_KEY", "")),
                api_base_url=os.getenv("AG_LLM_BASE_URL", ""),
                model=os.getenv("AG_LLM_MODEL", "deepseek-v4-pro"),
                max_tokens=int(os.getenv("AG_LLM_MAX_TOKENS", "65536")),
                temperature=float(os.getenv("AG_LLM_TEMPERATURE", "0.2")),
                thinking={"type": "enabled"},
                reasoning_effort="high",
            )
    
        @classmethod
        def from_settings(cls, settings: Dict[str, Any]) -> "ProviderConfig":
            """Build from config/settings.json llm section."""
            llm = settings.get("llm", {})
            provider_str = llm.get("provider", "local")
            try:
                provider = LLMProvider(provider_str)
            except ValueError:
                provider = LLMProvider.LOCAL
    
            return cls(
                provider=provider,
                api_key=llm.get("api_key", os.getenv("DEEPSEEK_API_KEY", "")),
                api_base_url=llm.get("local", llm.get("api_base_url", "")),
                model=llm.get("model", "deepseek-v4-pro"),
                max_tokens=llm.get("max_tokens", 65536),
                temperature=llm.get("temperature", 0.2),
                thinking=llm.get("thinking"),
                reasoning_effort=llm.get("reasoning_effort", ""),
            )
    
        @classmethod
        def from_model_config(cls, model_config: Any) -> "ProviderConfig":
            """Build from agents.models.ModelConfig."""
            provider_str = getattr(model_config, "provider", "deepseek")
            try:
                provider = LLMProvider(provider_str)
            except ValueError:
                provider = LLMProvider.DEEPSEEK
    
            return cls(
                provider=provider,
                api_key=getattr(model_config, "api_key", ""),
                api_base_url=getattr(model_config, "api_base_url", ""),
                model=getattr(model_config, "name", "deepseek-v4-pro"),
                max_tokens=getattr(model_config, "max_tokens", 65536),
                temperature=getattr(model_config, "temperature", 0.2),
                thinking={"type": "enabled"},
                reasoning_effort="high",
            )
    
    
    # ═══════════════════════════════════════════════════════════════
    # Turn / Session Data Models
    # ═══════════════════════════════════════════════════════════════
    
    
    @dataclass
    class UsageSummary:
        """Token usage tracking (mirrors claw-code UsageSummary)."""
        input_tokens: int = 0
        output_tokens: int = 0
        total_tokens: int = 0
    
        def add(self, inp: int, out: int) -> "UsageSummary":
            return UsageSummary(
                input_tokens=self.input_tokens + inp,
                output_tokens=self.output_tokens + out,
                total_tokens=self.total_tokens + inp + out,
            )
    
        def to_dict(self) -> Dict[str, int]:
            return {
                "input_tokens": self.input_tokens,
                "output_tokens": self.output_tokens,
                "total_tokens": self.total_tokens,
            }
    
    
    @dataclass
    class ToolInvocation:
        """A tool call extracted from the LLM response."""
        tool_name: str = ""
        arguments: Dict[str, Any] = field(default_factory=dict)
        result: str = ""
        permitted: bool = True
        denial_reason: str = ""
    
        def to_dict(self) -> Dict[str, Any]:
            return {
                "tool_name": self.tool_name,
                "arguments": self.arguments,
                "result": self.result,
                "permitted": self.permitted,
                "denial_reason": self.denial_reason,
            }
    
    
    @dataclass
    class TurnResult:
        """Result of a single chat turn (mirrors claw-code TurnResult)."""
        prompt: str = ""
        response: str = ""
        usage: UsageSummary = field(default_factory=UsageSummary)
        tool_invocations: List[ToolInvocation] = field(default_factory=list)
        stop_reason: str = "completed"
        model: str = ""
        provider: str = ""
        latency_ms: float = 0.0
        error: str = ""
        timestamp: str = field(
            default_factory=lambda: datetime.now(timezone.utc).isoformat()
        )
    
        def to_dict(self) -> Dict[str, Any]:
            return {
                "prompt": self.prompt,
                "response": self.response,
                "usage": self.usage.to_dict(),
                "tool_invocations": [t.to_dict() for t in self.tool_invocations],
                "stop_reason": self.stop_reason,
                "model": self.model,
                "provider": self.provider,
                "latency_ms": self.latency_ms,
                "error": self.error,
                "timestamp": self.timestamp,
            }
    
    
    @dataclass
    class ChatMessage:
        """A single message in a conversation."""
        role: str = "user"  # user | assistant | system | tool
        content: str = ""
        name: str = ""
        tool_calls: List[Dict[str, Any]] = field(default_factory=list)
        timestamp: str = field(
            default_factory=lambda: datetime.now(timezone.utc).isoformat()
        )
    
        def to_openai_dict(self) -> Dict[str, Any]:
            d: Dict[str, Any] = {"role": self.role, "content": self.content}
            if self.name:
                d["name"] = self.name
            return d
    
    
    @dataclass
    class ChatSession:
        """Stateful conversation session with compaction, history & transcript.
    
        Integrates claw-code-parity patterns:
        - HistoryLog for event tracking
        - TranscriptStore for persistence & replay
        - Permission tracking
        """
        session_id: str = field(default_factory=lambda: uuid4().hex[:12])
        agent_id: str = ""
        system_prompt: str = ""
        messages: List[ChatMessage] = field(default_factory=list)
        total_usage: UsageSummary = field(default_factory=UsageSummary)
        turn_count: int = 0
        created_at: str = field(
            default_factory=lambda: datetime.now(timezone.utc).isoformat()
        )
        max_turns: int = 100
        compact_after: int = 40
        # claw-code-parity extensions
        history: HistoryLog = field(default_factory=HistoryLog)
        transcript: TranscriptStore = field(default_factory=TranscriptStore)
        permission_denials: List[PermissionDenial] = field(default_factory=list)
    
        def add_user_message(self, content: str) -> None:
            self.messages.append(ChatMessage(role="user", content=content))
            self.transcript.append(content)
            self.history.add("user_message", content[:100])
    
        def add_assistant_message(self, content: str) -> None:
            self.messages.append(ChatMessage(role="assistant", content=content))
            self.turn_count += 1
            self.transcript.append(content)
            self.history.add("assistant_message", f"turn={self.turn_count}")
    
        def compact_if_needed(self) -> None:
            """Keep conversation manageable by dropping old turns."""
            if len(self.messages) > self.compact_after:
                # Keep system prompt context (first msg if system) + last N me
  ...(截断)
  
  ## ⚠️ 重要提示
  上方 📂 项目上下文 包含了任务相关的实际源文件。
  请基于这些文件设计方案，不要引用不存在的文件。
  
  ## 要求
  1. 基于调研结果和实际源码，设计详细技术方案
  2. 明确指出需要修改的文件和具体修改内容
  3. 定义接口规范（如有新增 API）
  4. 为开发工程师提供逐步实施指南
  
  项目根目录: /Users/panglaohu/Downloads/DoubleBoatClawSystem
  后端: src/backend/ (Python FastAPI)
  前端: src/frontend/ (HTML + JS)
  
  
  项目根目录: /Users/panglaohu/Downloads/AgentsGroup2026
  后端: src/backend/ (Python FastAPI)
  前端: src/frontend/ (HTML + JS)
  
────────────────────────────────────────────────────────────
⚡ 使用 DeepSeek V4 直连 (64K 输出, 流式)...

🔗 API: api.deepseek.com | 模型: deepseek-chat
────────────────────────────────────────────────────────────

# 技术方案：共签机制与配置即契约的治理桩

## 1. 概述

### 1.1 目标
设计一套**共签机制（Co-Signing Mechanism）** 与**配置即契约（Configuration as Contract）** 的治理桩，使业务域主（Business Domain Owner）与架构师（Architect）共同签署阈值的反射修改（Reflective Threshold Modification）。

### 1.2 核心概念
- **阈值（Threshold）**：系统运行的关键参数边界，如速率限制、资源配额、超时时间等
- **反射修改（Reflective Modification）**：系统在运行时根据状态自动调整阈值的能力
- **共签（Co-Signing）**：业务域主和架构师双方必须共同批准才能生效的机制
- **配置即契约（Configuration as Contract）**：将配置视为不可随意修改的契约，任何变更必须经过治理流程

## 2. 系统架构

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                    Governance Layer                          │
│  ┌─────────────────┐  ┌──────────────────┐  ┌───────────┐  │
│  │ Threshold Store  │  │ Co-Sign Engine   │  │ Audit Log │  │
│  │ (阈值存储)       │  │ (共签引擎)       │  │ (审计日志)│  │
│  └────────┬────────┘  └────────┬─────────┘  └───────────┘  │
│           │                    │                             │
│  ┌────────▼────────────────────▼─────────────────────────┐  │
│  │              Governance Stub (治理桩)                   │  │
│  │  - 拦截所有阈值修改请求                                 │  │
│  │  - 验证共签状态                                         │  │
│  │  - 执行反射修改                                         │  │
│  └────────────────────────┬──────────────────────────────┘  │
│                           │                                  │
└─────────────────────��─────┼──────────────────────────────────┘
                            │
┌───────────────────────────▼──────────────────────────────────┐
│                    Application Layer                          │
│  ┌─────────────────┐  ┌──────────────────┐  ┌───────────┐  │
│  │ Agent Toolbox   │  │ Chat Harness     │  │ Plaza     │  │
│  │ (工具调用)       │  │ (聊天引擎)       │  │ (广场)    │  │
│  └─────────────────┘  └──────────────────┘  └───────────┘  │
└─────────────────────────────────────────────────────────���────┘
```

### 2.2 组件职责

| 组件 | 职责 | 文件 |
|------|------|------|
| **Threshold Store** | 存储阈值定义、当前值、签名状态 | `governance_store.py` |
| **Co-Sign Engine** | 管理共签流程、状态机、通知 | `governance_stub.py` |
| **Governance Stub** | 治理桩，拦截并代理所有阈值修改 | `governance_stub.py` |
| **Audit Log** | 记录所有治理操作 | `governance_store.py` |

## 3. 数据模型

### 3.1 阈值定义 (ThresholdDefinition)

```python
# 在 src/backend/agents/models.py 中新增

@dataclass
class ThresholdDefinition:
    """阈值定义 - 配置即契约的核心实体"""
    threshold_id: str = ""                    # 唯一标识
    domain: str = ""                          # 业务域 (如: "rate_limit", "resource_quota")
    name: str = ""                            # 阈值名称
    description: str = ""                     # 描述
    current_value: Any = None                 # 当前值
    min_value: Any = None                     # 最小值
    max_value: Any = None                     # 最大值
    unit: str = ""                            # 单位
    category: ThresholdCategory = ThresholdCategory.NUMERIC
    auto_adjustable: bool = False             # 是否允许自动调整
    reflection_enabled: bool = False          # 是否启用反射修改
    reflection_rules: List[ReflectionRule] = field(default_factory=list)
    co_sign_required: bool = True             # 是否需要共签
    co_sign_status: CoSignStatus = CoSignStatus.PENDING
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    updated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    version: int = 1                          # 版本号，用于乐观锁

    def to_dict(self) -> Dict[str, Any]:
        return {
            "threshold_id": self.threshold_id,
            "domain": self.domain,
            "name": self.name,
            "description": self.description,
            "current_value": self.current_value,
            "min_value": self.min_value,
            "max_value": self.max_value,
            "unit": self.unit,
            "category": self.category.value,
            "auto_adjustable": self.auto_adjustable,
            "reflection_enabled": self.reflection_enabled,
            "reflection_rules": [r.to_dict() for r in self.reflection_rules],
            "co_sign_required": self.co_sign_required,
            "co_sign_status": self.co_sign_status.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "version": self.version,
        }


class ThresholdCategory(Enum):
    """阈值分类"""
    NUMERIC = "numeric"           # 数值型
    PERCENTAGE = "percentage"     # 百分比
    DURATION = "duration"         # 时长
    COUNT = "count"               # 计数
    BOOLEAN = "boolean"           # 布尔


class CoSignStatus(Enum):
    """共签状态"""
    PENDING = "pending"           # 待签署
    DOMAIN_SIGNED = "domain_signed"  # 业务域主已签署
    ARCHITECT_SIGNED = "architect_signed"  # 架构师已签署
    APPROVED = "approved"         # 双方已签署，生效
    REJECTED = "rejected"         # 被拒绝
    EXPIRED = "expired"           # 过期
```

### 3.2 反射规则 (ReflectionRule)

```python
@dataclass
class ReflectionRule:
    """反射修改规则 - 定义阈值如何根据系统状态自动调整"""
    rule_id: str = ""
    name: str = ""
    description: str = ""
    condition: str = ""           # 触发条件表达式 (如: "cpu_usage > 80")
    action: str = ""              # 调整动作 (如: "multiply(0.8)")
    cooldown_seconds: int = 300   # 冷却时间
    max_adjustments: int = 10     # 最大调整次数
    enabled: bool = True
    priority: int = 100

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "name": self.name,
            "description": self.description,
            "condition": self.condition,
            "action": self.action,
            "cooldown_seconds": self.cooldown_seconds,
            "max_adjustments": self.max_adjustments,
            "enabled": self.enabled,
            "priority": self.priority,
        }
```

### 3.3 共签记录 (CoSignRecord)

```python
@dataclass
class CoSignRecord:
    """共签记录 - 记录每次签署操作"""
    record_id: str = ""
    threshold_id: str = ""
    signer_type: str = ""         # "domain_owner" | "architect"
    signer_id: str = ""
    signer_name: str = ""
    action: str = ""              # "approve" | "reject"
    comment: str = ""
    old_value: Any = None
    new_value: Any = None
    signed_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "record_id": self.record_id,
            "threshold_id": self.threshold_id,
            "signer_type": self.signer_type,
            "signer_id": self.signer_id,
            "signer_name": self.signer_name,
            "action": self.action,
            "comment": self.comment,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "signed_at": self.signed_at,
        }
```

### 3.4 审计日志 (AuditLog)

```python
@dataclass
class AuditLog:
    """审计日志 - 记录所有治理操作"""
    log_id: str = ""
    action: str = ""              # "threshold_created" | "threshold_modified" | "co_sign" | "reflection_triggered"
    threshold_id: str = ""
    actor_id: str = ""
    actor_name: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "log_id": self.log_id,
            "action": self.action,
            "threshold_id": self.threshold_id,
            "actor_id": self.actor_id,
            "actor_name": self.actor_name,
            "details": self.details,
            "timestamp": self.timestamp,
        }
```

## 4. 治理桩接口设计

### 4.1 GovernanceStub 类

```python
# src/backend/agents/governance_stub.py

class GovernanceStub:
    """
    治理桩 - 配置即契约的核心实现
    
    职责：
    1. 拦截所有阈值修改请求
    2. 管理共签流程
    3. 执行反射修改
    4. 记录审计日志
    """
    
    def __init__(self, store: GovernanceStore):
        self.store = store
        self._reflection_engine = ReflectionEngine(store)
    
    # ── 阈值管理 ──
    
    async def create_threshold(self, threshold: ThresholdDefinition, 
                                creator_id: str) -> ThresholdDefinition:
        """创建新阈值"""
        # 1. 验证阈值定义
        self._validate_threshold(threshold)
        # 2. 生成ID
        threshold.threshold_id = uuid4().hex[:12]
        # 3. 保存
        result = await self.store.save_threshold(threshold)
        # 4. 记录审计
        await self.store.add_audit_log(AuditLog(
            action="threshold_created",
            threshold_id=threshold.threshold_id,
            actor_id=creator_id,
            details={"threshold": threshold.to_dict()}
        ))
        return result
    
    async def propose_modification(self, threshold_id: str, 
                                     new_value: Any,
                                     proposer_id: str,
                                     proposer_name: str,
                                     reason: str) -> CoSignRecord:
        """提议修改阈值 - 触发共签流程"""
        # 1. 获取当前阈值
        threshold = await self.store.get_threshold(threshold_id)
        if not threshold:
            raise ValueError(f"Threshold {threshold_id} not found")
        
        # 2. 验证新值
        self._validate_value(threshold, new_value)
        
        # 3. 创建共签记录
        record = CoSignRecord(
            threshold_id=threshold_id,
            old_value=threshold.current_value,
            new_value=new_value,
        )
        
        # 4. 更新阈值状态
        threshold.co_sign_status = CoSignStatus.PENDING
        threshold.current_value = new_value  # 暂存新值
        threshold.version += 1
        
        # 5. 保存
        await self.store.save_threshold(threshold)
        await self.store.add_co_sign_record(record)
        
        # 6. 记录审计
        await self.store.add_audit_log(AuditLog(
            action="threshold_modification_proposed",
            threshold_id=threshold_id,
            actor_id=proposer_id,
            details={"old_value": record.old_value, "new_value": record.new_value, "reason": reason}
        ))
        
        return record
    
    async def sign_threshold(self, threshold_id: str,
                              signer_type: str,
                              signer_id: str,
                              signer_name: str,
                              action: str,
                              comment: str = "") -> CoSignStatus:
        """签署阈值修改"""
        # 1. 获取当前阈值
        threshold = await self.store.get_threshold(threshold_id)
        if not threshold:
            raise ValueError(f"Threshold {threshold_id} not found")
        
        # 2. 验证签署权限
        if signer_type == "domain_owner" and threshold.co_sign_status not in [CoSignStatus.PENDING]:
            raise PermissionError("Domain owner can only sign pending modifications")
        if signer_type == "architect" and threshold.co_sign_status not in [CoSignStatus.PENDING, CoSignStatus.DOMAIN_SIGNED]:
            raise PermissionError("Architect can only sign after domain owner or pending")
        
        # 3. 创建签署记录
        record = CoSignRecord(
            threshold_id=threshold_id,
            signer_type=signer_type,
            signer_id=signer_id,
            signer_name=signer_name,
            action=action,
            comment=comment,
            old_value=threshold.current_value,
            new_value=threshold.current_value,
        )
        
        # 4. 更新状态
        if action == "reject":
            threshold.co_sign_status = CoSignStatus.REJECTED
        elif signer_type == "domain_owner":
            threshold.co_sign_status = CoSignStatus.DOMAIN_SIGNED
        elif signer_type == "architect":
            if threshold.co_sign_status == CoSignStatus.DOMAIN_SIGNED:
                threshold.co_sign_status = CoSignStatus.APPROVED
            else:
                threshold.co_sign_status = CoSignStatus.ARCHITECT_SIGNED
        
        threshold.version += 1
        
        # 5. 保存
        await self.store.save_threshold(threshold)
        await self.store.add_co_sign_record(record)
        
        # 6. 如果已批准，执行修改
        if threshold.co_sign_status == CoSignStatus.APPROVED:
            await self._apply_modification(threshold)
        
        # 7. 记录审计
        await self.store.add_audit_log(AuditLog(
            action="co_sign",
            threshold_id=threshold_id,
            actor_id=signer_id,
            details={
                "signer_type": signer_type,
                "action": action,
                "comment": comment,
                "new_status": threshold.co_sign_status.value
            }
        ))
        
        return threshold.co_sign_status
    
    # ── 反射修改 ──
    
    async def trigger_reflection(self, threshold_id: str,
                                  context: Dict[str, Any]) -> Optional[Any]:
        """触发反射修改 - 根据系统状态自动调整阈值"""
        threshold = await self.store.get_threshold(threshold_id)
        if not threshold or not threshold.reflection_enabled:
            return None
        
        # 1. 检查冷却时间
        last_reflection = await self.store.get_last_reflection(threshold_id)
        if last_reflection:
            elapsed = (datetime.now(timezone.utc) - 
                      datetime.fromisoformat(last_reflection.timestamp)).total_seconds()
            if elapsed < self._get_cooldown(threshold):
                return None
        
        # 2. 评估规则
        for rule in threshold.reflection_rules:
            if not rule.enabled:
                continue
            if self._evaluate_condition(rule.condition, context):
                # 3. 计算新值
                new_value = self._apply_action(rule.action, threshold.current_value, context)
                
                # 4. 验证新值
                if not self._validate_value(threshold, new_value):
                    continue
                
                # 5. 如果需要共签，创建共签流程
                if threshold.co_sign_required:
                    await self.propose_modification(
                        threshold_id, new_value,
                        "system", "Reflection Engine",
                        f"Auto-adjustment triggered by rule: {rule.name}"
                    )
                else:
                    # 6. 直接应用
                    threshold.current_value = new_value
                    threshold.version += 1
                    await self.store.save_threshold(threshold)
                    
                    # 7. 记录反射事件
                    await self.store.add_reflection_event(ReflectionEvent(
                        threshold_id=threshold_id,
                        rule_id=rule.rule_id,
                        old_value=threshold.current_value,
                        new_value=new_value,
                        context=context
                    ))
                    
                    # 8. 记录审计
                    await self.store.add_audit_log(AuditLog(
                        action="reflection_triggered",
                        threshold_id=threshold_id,
                        actor_id="system",
                        details={
                            "rule": rule.name,
                            "old_value": threshold.current_value,
                            "new_value": new_value,
                            "context": context
                        }
                    ))
                
                return new_value
        
        return None
    
    # ── 查询接口 ──
    
    async def get_threshold(self, threshold_id: str) -> Optional[ThresholdDefinition]:
        """获取阈值定义"""
        return await self.store.get_threshold(threshold_id)
    
    async def list_thresholds(self, domain: Optional[str] = None) -> List[ThresholdDefinition]:
        """列出阈值"""
        return await self.store.list_thresholds(domain)
    
    async def get_pending_signatures(self) -> List[ThresholdDefinition]:
        """获取待签署的阈值"""
        return await self.store.get_thresholds_by_status(CoSignStatus.PENDING)
    
    async def get_audit_logs(self, threshold_id: Optional[str] = None,
                              limit: int = 100) -> List[AuditLog]:
        """获取审计日志"""
        return await self.store.get_audit_logs(threshold_id, limit)
    
    # ── 内部方法 ──
    
    def _validate_threshold(self, threshold: ThresholdDefinition):
        """验证阈值定义"""
        if not threshold.name:
            raise ValueError("Threshold name is required")
        if not threshold.domain:
            raise ValueError("Threshold domain is required")
        if threshold.min_value is not None and threshold.max_value is not None:
            if threshold.min_value > threshold.max_value:
                raise ValueError("min_value cannot be greater than max_value")
    
    def _validate_value(self, threshold: ThresholdDefinition, value: Any) -> bool:
        """验证阈值值是否在允许范围内"""
        if threshold.min_value is not None and value < threshold.min_value:
            return False
        if threshold.max_value is not None and value > threshold.max_value:
            return False
        return True
    
    def _evaluate_condition(self, condition: str, context: Dict[str, Any]) -> bool:
        """评估反射条件表达式"""
        # 简单实现：支持基本比较操作
        # 实际应使用安全表达式求值库
        try:
            # 示例: "cpu_usage > 80"
            parts = condition.split()
            if len(parts) == 3:
                var_name, op, threshold_str = parts
                var_value = context.get(var_name)
                if var_value is None:
                    return False
                threshold_value = float(threshold_str)
                
                if op == ">":
                    return var_value > threshold_value
                elif op == "<":
                    return var_value < threshold_value
                elif op == ">=":
                    return var_value >= threshold_value
                elif op == "<=":
                    return var_value <= threshold_value
                elif op == "==":
                    return var_value == threshold_value
            return False
        except Exception:
            return False
    
    def _apply_action(self, action: str, current_value: Any, 
                      context: Dict[str, Any]) -> Any:
        """应用反射动作"""
        # 示例: "multiply(0.8)" 或 "add(-10)"
        try:
            if action.startswith("multiply("):
                factor = float(action[9:-1])
                return current_value * factor
            elif action.startswith("add("):
                delta = float(action[4:-1])
                return current_value + delta
            elif action.startswith("set("):
                return float(action[4:-1])
            return current_value
        except Exception:
            return current_value
    
    def _get_cooldown(self, threshold: ThresholdDefinition) -> float:
        """获取冷却时间（秒）"""
        if threshold.reflection_rules:
            return min(r.cooldown_seconds for r in threshold.reflection_rules)
        return 300  # 默认5分钟
    
    async def _apply_modification(self, threshold: ThresholdDefinition):
        """应用已批准的修改"""
        # 通知相关组件阈值已变更
        # 可以触发事件总线或回调
        pass
```

### 4.2 GovernanceStore 类

```python
# src/backend/agents/governance_store.py

class GovernanceStore:
    """
    治理存储 - 管理阈值定义、共签记录、审计日志的持久化
    """
    
    def __init__(self, storage_path: str = "storage/governance/"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self._thresholds: Dict[str, ThresholdDefinition] = {}
        self._co_sign_records: List[CoSignRecord] = []
        self._audit_logs: List[AuditLog] = []
        self._reflection_events: List[ReflectionEvent] = []
        self._load()
    
    async def save_threshold(self, threshold: ThresholdDefinition) -> ThresholdDefinition:
        """保存阈值定义"""
        self._thresholds[threshold.threshold_id] = threshold
        self._save()
        return threshold
    
    async def get_threshold(self, threshold_id: str) -> Optional[ThresholdDefinition]:
        """获取阈值定义"""
        return self._thresholds.get(threshold_id)
    
    async def list_thresholds(self, domain: Optional[str] = None) -> List[ThresholdDefinition]:
        """列出阈值"""
        if domain:
            return [t for t in self._thresholds.values() if t.domain == domain]
        return list(self._thresholds.values())
    
    async def get_thresholds_by_status(self, status: CoSignStatus) -> List[ThresholdDefinition]:
        """按状态获取阈值"""
        return [t for t in self._thresholds.values() if t.co_sign_status == status]
    
    async def add_co_sign_record(self, record: CoSignRecord):
        """添加共签记录"""
        record.record_id = uuid4().hex[:12]
        self._co_sign_records.append(record)
        self._save()
    
    async def get_co_sign_records(self, threshold_id: str) -> List[CoSignRecord]:
        """获取阈值的共签记录"""
        return [r for r in self._co_sign_records if r.threshold_id == threshold_id]
    
    async def add_audit_log(self, log: AuditLog):
        """添加审计日志"""
        log.log_id = uuid4().hex[:12]
        self._audit_logs.append(log)
        self._save()
    
    async def get_audit_logs(self, threshold_id: Optional[str] = None,
                              limit: int = 100) -> List[AuditLog]:
        """获取审计日志"""
        logs = self._audit_logs
        if threshold_id:
            logs = [l for l in logs if l.threshold_id == threshold_id]
        return sorted(logs, key=lambda x: x.timestamp, reverse=True)[:limit]
    
    async def get_last_reflection(self, threshold_id: str) -> Optional[ReflectionEvent]:
        """获取最后一次反射事件"""
        events = [e for e in self._reflection_events if e.threshold_id == threshold_id]
        if events:
            return max(events, key=lambda e: e.timestamp)
        return None
    
    async def add_reflection_event(self, event: ReflectionEvent):
        """添加反射事件"""
        event.event_id = uuid4().hex[:12]
        self._reflection_events.append(event)
        self._save()
    
    def _save(self):
        """持久化到磁盘"""
        data = {
            "thresholds": {k: v.to_dict() for k, v in self._thresholds.items()},
            "co_sign_records": [r.to_dict() for r in self._co_sign_records],
            "audit_logs": [l.to_dict() for l in self._audit_logs],
            "reflection_events": [e.to_dict() for e in self._reflection_events],
        }
        with open(self.storage_path / "governance.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _load(self):
        """从磁盘加载"""
        file_path = self.storage_path / "governance.json"
        if file_path.exists():
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self._thresholds = {
                    k: ThresholdDefinition(**v) for k, v in data.get("thresholds", {}).items()
                }
                self._co_sign_records = [
                    CoSignRecord(**r) for r in data.get("co_sign_records", [])
                ]
                self._audit_logs = [
                    AuditLog(**l) for l in data.get("audit_logs", [])
                ]
                self._reflection_events = [
                    ReflectionEvent(**e) for e in data.get("reflection_events", [])
                ]
```

## 5. API 接口设计

### 5.1 REST API 端点

```python
# 在 src/backend/main.py 中新增

from fastapi import APIRouter, HTTPException, Depends
from .agents.governance_stub import GovernanceStub
from .agents.governance_store import GovernanceStore

governance_router = APIRouter(prefix="/api/v1/governance", tags=["governance"])

# 依赖注入
def get_governance_stub() -> GovernanceStub:
    store = GovernanceStore()
    return GovernanceStub(store)

@governance_router.post("/thresholds")
async def create_threshold(
    threshold: ThresholdDefinition,
    creator_id: str = Query(...),
    stub: GovernanceStub = Depends(get_governance_stub)
):
    """创建新阈值"""
    try:
        result = await stub.create_threshold(threshold, creator_id)
        return {"ok": True, "threshold": result.to_dict()}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@governance_router.post("/thresholds/{threshold_id}/propose")
async def propose_modification(
    threshold_id: str,
    new_value: Any = Body(...),
    proposer_id: str = Body(...),
    proposer_name: str = Body(...),
    reason: str = Body(""),
    stub: GovernanceStub = Depends(get_governance_stub)
):
    """提议修改阈值"""
    try:
        record = await stub.propose_modification(
            threshold_id, new_value, proposer_id, proposer_name, reason
        )
        return {"ok": True, "record": record.to_dict()}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@governance_router.post("/thresholds/{threshold_id}/sign")
async def sign_threshold(
    threshold_id: str,
    signer_type: str = Body(...),
    signer_id: str = Body(...),
    signer_name: str = Body(...),
    action: str = Body(...),
    comment: str = Body(""),
    stub: GovernanceStub = Depends(get_governance_stub)
):
    """签署阈值修改"""
    try:
        status = await stub.sign_threshold(
            threshold_id, signer_type, signer_id, signer_name, action, comment
        )
        return {"ok": True, "status": status.value}
    except (ValueError, PermissionError) as e:
        raise HTTPException(status_code=400, detail=str(e))

@governance_router.post("/thresholds/{threshold_id}/reflect")
async def trigger_reflection(
    threshold_id: str,
    context: Dict[str, Any] = Body(...),
    stub: GovernanceStub = Depends(get_governance_stub)
):
    """触发反射修改"""
    result = await stub.trigger_reflection(threshold_id, context)
    return {"ok": True, "new_value": result}

@governance_router.get("/thresholds")
async def list_thresholds(
    domain: Optional[str] = None,
    stub: GovernanceStub = Depends(get_governance_stub)
):
    """列出阈值"""
    thresholds = await stub.list_thresholds(domain)
    return {"ok": True, "thresholds": [t.to_dict() for t in thresholds]}

@governance_router.get("/thresholds/{threshold_id}")
async def get_threshold(
    threshold_id: str,
    stub: GovernanceStub = Depends(get_governance_stub)
):
    """获取阈值详情"""
    threshold = await stub.get_threshold(threshold_id)
    if not threshold:
        raise HTTPException(status_code=404, detail="Threshold not found")
    return {"ok": True, "threshold": threshold.to_dict()}

@governance_router.get("/pending")
async def get_pending_signatures(
    stub: GovernanceStub = Depends(get_governance_stub)
):
    """获取待签署的阈值"""
    thresholds = await stub.get_pending_signatures()
    return {"ok": True, "thresholds": [t.to_dict() for t in thresholds]}

@governance_router.get("/audit-logs")
async def get_audit_logs(
    threshold_id: Optional[str] = None,
    limit: int = 100,
    stub: GovernanceStub = Depends(get_governance_stub)
):
    """获取审计日志"""
    logs = await stub.get_audit_logs(threshold_id, limit)
    return {"ok": True, "logs": [l.to_dict() for l in logs]}
```

## 6. 共签状态机

```
                    ┌─────────────┐
                    │   PENDING   │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
              ▼            ▼            ▼
     ┌────────────┐ ┌────────────┐ ┌──────────┐
     │DOMAIN_SIGN │ │ARCH_SIGN   │ │ REJECTED │
     └──────┬─────┘ └──────┬─────┘ └──────────┘
            │              │
            └──────┬───────┘
                   │
                   ▼
            ┌────────────┐
            │  APPROVED  │
            └────────────┘
```

**状态转换规则：**
1. **PENDING** → 初始状态，等待签署
2. **PENDING** → **DOMAIN_SIGNED**：业务域主签署
3. **PENDING** → **ARCHITECT_SIGNED**：架构师签署
4. **DOMAIN_SIGNED** → **APPROVED**：架构师签署（业务域主已签）
5. **ARCHITECT_SIGNED** → **APPROVED**：业务域主签署（架构师已签）
6. **任何状态** → **REJECTED**：任一方拒绝
7. **任何状态** → **EXPIRED**：超时（24小时未完成）

## 7. 集成到现有系统

### 7.1 修改 `src/backend/agents/agent_toolbox.py`

在 `TOOL_SCHEMA` 中添加治理相关工具：

```python
# 在 TOOL_SCHEMA 末尾添加
{
    "type": "function",
    "function": {
        "name": "propose_threshold_change",
        "description": "提议修改系统阈值 - 需要业务域主和架构师共同签署",
        "parameters": {
            "type": "object",
            "properties": {
                "threshold_id": {"type": "string", "description": "阈值ID"},
                "new_value": {"type": "number", "description": "新阈值"},
                "reason": {"type": "string", "description": "修改原因"},
            },
            "required": ["threshold_id", "new_value", "reason"],
        },
    },
},
{
    "type": "function",
    "function": {
        "name": "sign_threshold_change",
        "description": "签署待处理的阈值修改",
        "parameters": {
            "type": "object",
            "properties": {
                "threshold_id": {"type": "string", "description": "阈值ID"},
                "action": {"type": "string", "enum": ["approve", "reject"]},
                "comment": {"type": "string", "description": "签署意见"},
            },
            "required": ["threshold_id", "action"],
        },
    },
},
{
    "type": "function",
    "function": {
        "name": "list_pending_thresholds",
        "description": "列出所有待签署的阈值修改",
        "parameters": {
            "type": "object",
            "properties": {},
        },
    },
},
```

### 7.2 修改 `src/backend/agents/chat_harness.py`

在 `ChatSession` 中添加治理上下文：

```python
@dataclass
class ChatSession:
    # ... 现有字段 ...
    governance_context: Dict[str, Any] = field(default_factory=dict)
    # 存储当前会话的治理状态
```

### 7.3 修改 `src/backend/main.py`

注册治理路由：

```python
from .agents.governance_stub import governance_router

app.include_router(governance_router)
```

## 8. 实施步骤

### 步骤 1: 创建数据模型文件
- **文件**: `src/backend/agents/models.py`
- **操作**: 添加 `ThresholdDefinition`, `ReflectionRule`, `CoSignRecord`, `AuditLog`, `ReflectionEvent` 数据类
- **优先级**: 高

### 步骤 2: 创建治理存储
- **文件**: `src/backend/agents/governance_store.py`
- **操作**: 实现 `GovernanceStore` 类，包含 JSON 文件持久化
- **优先级**: 高

### 步骤 3: 创建治理桩
- **文件**: `src/backend/agents/governance_stub.py`
- **操作**: 实现 `GovernanceStub` 类，包含共签引擎和反射引擎
- **优先级**: 高

### 步骤 4: 添加 REST API
- **文件**: `src/backend/main.py`
- **操作**: 注册治理路由，实现所有 API 端点
- **优先级**: 中

### 步骤 5: 集成到 Agent Toolbox
- **文件**: `src/backend/agents/agent_toolbox.py`
- **操作**: 添加治理相关工具函数
- **优先级**: 中

### 步骤 6: 集成到 Chat Harness
- **文件**: `src/backend/agents/chat_harness.py`
- **操作**: 添加治理上下文支持
- **优先级**: 低

### 步骤 7: 创建前端界面
- **文件**: `src/frontend/governance.html` (新建)
- **操作**: 创建阈值管理、共签审批、审计日志查看界面
- **优先级**: 低

## 9. 测试策略

### 9.1 单元测试
```python
# tests/test_governance.py

async def test_create_threshold():
    store = GovernanceStore()
    stub = GovernanceStub(store)
    
    threshold = ThresholdDefinition(
        name="max_concurrent_requests",
        domain="rate_limit",
        current_value=100,
        min_value=10,
        max_value=1000,
        unit="requests/sec"
    )
    
    result = await stub.create_threshold(threshold, "test_user")
    assert result.threshold_id is not None
    assert result.co_sign_status == CoSignStatus.PENDING

async def test_co_sign_flow():
    store = GovernanceStore()
    stub = GovernanceStub(store)
    
    # 创建阈值
    threshold = ThresholdDefinition(
        name="api_rate_limit",
        domain="rate_limit",
        current_value=100,
        min_value=10,
        max_value=1000,
    )
    threshold = await stub.create_threshold(threshold, "admin")
    
    # 提议修改
    await stub.propose_modification(
        threshold.threshold_id, 200,
        "developer", "Developer", "Need to increase limit"
    )
    
    # 业务域主签署
    status = await stub.sign_threshold(
        threshold.threshold_id, "domain_owner",
        "domain_owner_1", "Domain Owner",
        "approve", "Approved for production"
    )
    assert status == CoSignStatus.DOMAIN_SIGNED
    
    # 架构师签署
    status = await stub.sign_threshold(
        threshold.threshold_id, "architect",
        "architect_1", "Architect",
        "approve", "Approved after review"
    )
    assert status == CoSignStatus.APPROVED

async def test_reflection():
    store = GovernanceStore()
    stub = GovernanceStub(store)
    
    threshold = ThresholdDefinition(
        name="cpu_threshold",
        domain="resource",
        current_value=80,
        min_value=10,
        max_value=100,
        reflection_enabled=True,
        reflection_rules=[
            ReflectionRule(
                name="reduce_on_high_cpu",
                condition="cpu_usage > 90",
                action="multiply(0.8)",
                cooldown_seconds=60,
            )
        ],
        co_sign_required=False,
    )
    threshold = await stub.create_threshold(threshold, "admin")
    
    # 触发反射
    result = await stub.trigger_reflection(
        threshold.threshold_id,
        {"cpu_usage": 95}
    )
    assert result is not None
    assert result < 80  # 应该降低
```

## 10. 安全考虑

### 10.1 权限控制
- 只有业务域主可以签署 `domain_owner` 类型的签名
- 只有架构师可以签署 `architect` 类型的签名
- 系统管理员可以查看所有阈值但不能签署

### 10.2 防篡改
- 所有阈值修改都有完整的审计日志
- 阈值版本号用于乐观锁，防止并发修改
- 反射修改有冷却时间，防止频繁调整

### 10.3 数据完整性
- 阈值值必须在 `min_value` 和 `max_value` 范围内
- 共签记录不可删除或修改
- 审计日志不可删除或修改

## 11. 配置文件示例

```json
{
  "governance": {
    "enabled": true,
    "storage_path": "storage/governance/",
    "default_co_sign_required": true,
    "reflection": {
      "enabled": true,
      "max_adjustments_per_hour": 10,
      "default_cooldown_seconds": 300
    },
    "thresholds": {
      "rate_limit": {
        "max_concurrent_requests": {
          "current_value": 100,
          "min_value": 10,
          "max_value": 1000,
          "unit": "requests/sec",
          "auto_adjustable": true,
          "reflection_enabled": true
        }
      },
      "resource": {
        "max_memory_mb": {
          "current_value": 512,
          "min_value": 128,
          "max_value": 2048,
          "unit": "MB",
          "auto_adjustable": false,
          "reflection_enabled": false
        }
      }
    }
  }
}
```

## 12. 总结

本方案实现了：
1. **配置即契约**：所有阈值变更必须经过治理流程
2. **共签机制**：业务域主和架构师共同签署才能生效
3. **反射修改**：系统可根据状态自动调整阈值，但受治理约束
4. **完整审计**：所有操作都有日志记录
5. **安全可控**：权限分离、值验证、防篡改

需要修改的文件：
- `src/backend/agents/models.py` - 新增数据模型
- `src/backend/agents/governance_store.py` - 新建治理存储
- `src/backend/agents/governance_stub.py` - 新建治理桩
- `src/backend/agents/agent_toolbox.py` - 添加治理工具
- `src/backend/agents/chat_harness.py` - 添加治理上下文
- `src/backend/main.py` - 注册治理路由

────────────────────────────────────────────────────────────
✅ deepseek-chat 完成
