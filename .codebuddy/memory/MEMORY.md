# 项目长期记忆 (MEMORY.md)

## 后端启动方式（重要）
- 后端必须用**项目根 `venv/`** 的 Python 启动，不能用系统 python3.14。
  - 正确：`cd src/backend && /Users/panglaohu/Downloads/AgentsGroup2026/venv/bin/python main.py --port 8080`
  - venv 里装了 `edge_tts`(7.2.8) 等；系统 python3.14 / python3 都**没有** edge_tts → 用系统 python 启动会导致 `/tts` 全部 503 (`No module named 'edge_tts'`)。
- `python main.py` 无 `--reload`，改后端代码必须重启进程才生效。
- 启动验证：日志出现 `✅ 启动验证通过: 全部 8 项检查通过` 即正常。

## TTS 引擎行为
- `/tts`（tts_routes.py）：全局 `engine=gpt-sovits` 时，GPT-SoVITS 为优先引擎，Edge-TTS 为兜底。
- 关键修复(2026-07-08)：GPT-SoVITS 优先分支加 `and not req.voice`——调用方显式带 Edge 声道(`req.voice`)时跳过 GPT-SoVITS，直接 Edge-TTS 合成。否则 GPT-SoVITS 在线+有 ref_audio_path 时会用固定女声克隆覆盖用户选的 Edge 男声。
- 调用方约定：`voice` 字段 = Edge-TTS 声道 ID；仅当 pet `voice.provider=edge-tts` 时前端才带 voice（office-boot.js / pet-config.html testVoice）。digital-twin-cli.js / plaza.js 不带 voice → 走全局 GPT-SoVITS。

## 前端
- Vite dev: `vite.config.mjs` root=`src/frontend`, port=5173, proxy `/api`→`http://localhost:8080`、`/ws`→ws://8080。
- pet-config.html `loadTTS()` 拉取女声列表后必须 `render()`，否则 Edge-TTS 下拉为空、选不中声道。
- `PUT /api/v1/pet-ecosystem/pets/{id}` 用**单个 pet 对象**作请求体（不是整包 ecosystem）；可正常持久化 `voice.edge_voice`。
