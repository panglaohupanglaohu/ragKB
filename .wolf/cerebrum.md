# Cerebrum

> OpenWolf's learning memory. Updated automatically as the AI learns from interactions.
> Do not edit manually unless correcting an error.
> Last updated: 2026-06-12

## User Preferences

<!-- How the user likes things done. Code style, tools, patterns, communication. -->

## Key Learnings

- **Project:** agentsgroup2026
- **Description:** Standalone Agent Management, Evolution & Chat Platform — extracted from PoseidonX
- G1-2 约定：萃取审批通过时即写入 skill_classification 初始 reserve 记录（幂等），后续由 verifier + 周期 reclassify 决定毕业。
- G3-2 约定：试炼评估结果需携带 routing_comparison/routing_benefit（相对 baseline 的策略收益），并在 branches 接口返回 routing_strategy 供导演台直接展示。
- 任务执行（agent_team 工作流分步）的"系统配置 LLM"权威来源是 ChatHarness 的 provider 配置（由"模型与连接页"→ `update_default_provider` → `config/model_pool.json`），用 `get_chat_harness().get_provider_config()` 读（字段 provider/api_key/api_base_url/model，`resolve_base_url()` 给 base）。**不要**用 `~/.claude/settings.json` / 本地 `claude` CLI 作为任务执行 LLM 来源——那是历史写死路径，本地不可达会导致任务无限 `running`。api.py `_get_deepseek_credentials()` 已改为优先 harness 配置。
- 任务执行三条路径：tool 角色→`_run_tool_loop`；文本角色(_TEXT_ONLY_ROLES)→`_run_openai_compatible`；其余→`_should_use_direct_api` 决定直连 vs 本地 CLI。`_run_openai_compatible` 用 urlparse(base_url) 拼 `{path}/chat/completions`，deepseek/codebuddy 的 base（有无 /v1 均可）兼容。

## Do-Not-Repeat

<!-- Mistakes made and corrected. Each entry prevents the same mistake recurring. -->
<!-- Format: [YYYY-MM-DD] Description of what went wrong and what to do instead. -->
- [2026-06-13] 执行沙箱无 fastapi/pytest 且 pip 被防火墙拦截（proxy 403），无法安装。所有"接口通路门"(2xx)类验收只能在本机 `rtk` 环境复跑，不要尝试在沙箱跑 test_v4_apis 等依赖 fastapi 的用例；可在沙箱跑的仅 `node --check` 与纯逻辑（但纯逻辑也需 pytest，沙箱同样缺）。
- [2026-06-13 更正上一条] Cowork 沙箱环境已变化：**pip 现可用**（pypi 在网络白名单内，`pip install fastapi pytest httpx` 成功）；**前端 vitest 也能在沙箱跑**——先 `npm i @rollup/rollup-linux-arm64-gnu @esbuild/linux-arm64` 补 linux 原生二进制（项目 node_modules 是 macOS arm64 装的），再从**项目根目录** `npx vitest run src/frontend/__tests__/xxx.test.js`（现有 system-evolution 3 用例全绿）。真正的硬限制是**网络白名单**：LLM 域名（api.deepseek.com、copilot.tencent.com/v2）DNS 解析直接失败、本机后端 8080、本机 5173 全部不可达。故依赖**真 LLM / 起后端 / 浏览器**的验收仍必须本机 `rtk`；纯代码/语法检查/前端单测可在沙箱完成。codebuddy 的 key 即使配在 app 里，沙箱也调不到该 LLM（域名不可达，非 key 问题）。
- [2026-06-13] 跨文档状态会滞后：本文件 v4 的 C-4.1/D-0.2 标 [~]，实际已由 frontendBigChangeTodos F3/F4 完成。核对 todos 时必须跨 5 份文档交叉比对（全局优化 / 数字孪生v3.1 / 场景演练v4 / AgentsGroupConfig / frontendBigChange），避免误报未完成。

## Decision Log

<!-- Significant technical decisions with rationale. Why X was chosen over Y. -->
- 任务执行支持两种模式(execution_mode)：linear=原线性 Claude 流水线(默认)；collaborative=智能体广场多轮讨论(`_start_task_collaboration`→plaza create_plaza/add_participant/create_discussion/run_discussion→共识→回写 task.metadata.collaboration+artifacts→_finalize_task_terminal_state)。广场用 set_chat_fn(harness.chat) 即系统配置 LLM。批量/队列路径(_real_task_executor)暂仍线性。
