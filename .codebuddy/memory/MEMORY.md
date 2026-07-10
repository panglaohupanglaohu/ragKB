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

## Agent 仿生生态运行时（2026-07-09 规划）
- 规划文档：`docs/Agent仿生生态运行时plan.md` + `todos.md`（Eco-1~Eco-6, EC-1~EC-17）。
- 统一了现有两条线：宠物 Phase I（感知-意图-行为泛化，PI-1~6 全未开工）+ 孪生 EvolutionRun（skill 进化闭环，设计态），补上两者都缺的"物竞天择"维度（选择压力→繁殖/淘汰）。
- 核心新增：EC-7/8/9（skill 繁殖 dominant 扩散 + 淘汰 deprecated/retired + Agent 预算按 fitness 调节）、EC-14（协作基因组进化）、EC-16/17（生态可观测）。
- 执行顺序：Eco-1（eco_loop 基座）→ Eco-2（适应度度量）→ [Eco-3 选择淘汰 ∥ Eco-4 变异验证] → Eco-5 协作进化 → Eco-6 可观测。
- 关键现状缺口：`eco_loop.py`/`evolution_bridge.py` 均未建；chat_harness reflect 是假总结；skill_router 纯词法匹配无 intention。
