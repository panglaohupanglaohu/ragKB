# Cerebrum

> OpenWolf's learning memory. Updated automatically as the AI learns from interactions.
> Do not edit manually unless correcting an error.
> Last updated: 2026-06-12

## User Preferences

<!-- How the user likes things done. Code style, tools, patterns, communication. -->
- [2026-07-04] 数字孪生统一办公室里的 Agent 造型必须复用 plaza 的 agent 模型骨架/视觉语言；不要做成黑色圆柱、棋子或“站桩胶囊”。参考 Marvis 办公室时保持极简白空间，但 Agent 本体用 plaza 风格。
- [2026-07-05] 统一办公室里的猫不是静态摆件；需要有 Agent↔猫互动过程。基础规则：离猫最近的 Agent 会转身面向猫，并通过闪烁/放大的脚下光圈吸引猫。
- [2026-07-05] 猫「按有效技能数跳到 Agent 桌上」的逻辑用户明确不要，已撤销；不要再加回。猫互动只保留最近 Agent 转身+光圈吸引。
- [2026-07-11] 用户世界观（物竞天择，最高设计约束）：Agent 不是人类模仿，应有自己的生态/沟通/繁衍/成长方式；以「感知-意图-行为」存在；skill 与协作过程都是被环境选择的可遗传单元（不是 skill 选路径、不是主动换协作方式）；主动学习是盲目的、选择是客观的；生存时长是唯一适应度，禁止人工评分。办公室视图(?office3d=1)=物竞天择试验田：右侧演练菜单整体换成生境控制台，3D 窗口必须始终保留且有内容。
- [2026-07-11] 演练类页面右侧菜单重构时用户要求「完全与以前不一样」，不接受在旧 SECS 菜单上叠加小块——要整面板替换。

## Key Learnings

- [2026-07-11] 密钥有两类槽位：全局默认 provider 槽（PUT /llm/provider → secret store __default__，cat-speak/广场/萃取等默认调用读它）与团队模型槽（编辑模型保存 → teams 段）。用户在编辑模型里存 key 不会自动喂饱默认 provider（除非 _sync_default_model_to_harness 同步 api_key——XB-8.2 待验证）。排查"LLM 未连接"先分清调用方读哪个槽。
- [2026-07-11] 判断线上行为是否为旧代码：先比对后端进程启动时间与相关文件 git 提交时间（XC-6.1 建议在 /health 暴露 git rev）。旧任务的会话 lines 缓存会回放旧引擎日志头，易被误判为"改了没生效"。

- **Project:** agentsgroup2026
- **Description:** Standalone Agent Management, Evolution & Chat Platform — extracted from PoseidonX
- G1-2 约定：萃取审批通过时即写入 skill_classification 初始 reserve 记录（幂等），后续由 verifier + 周期 reclassify 决定毕业。
- G3-2 约定：试炼评估结果需携带 routing_comparison/routing_benefit（相对 baseline 的策略收益），并在 branches 接口返回 routing_strategy 供导演台直接展示。
- 任务执行（agent_team 工作流分步）的"系统配置 LLM"权威来源是 ChatHarness 的 provider 配置（由"模型与连接页"→ `update_default_provider` → `config/model_pool.json`），用 `get_chat_harness().get_provider_config()` 读（字段 provider/api_key/api_base_url/model，`resolve_base_url()` 给 base）。**不要**用 `~/.claude/settings.json` / 本地 `claude` CLI 作为任务执行 LLM 来源——那是历史写死路径，本地不可达会导致任务无限 `running`。api.py `_get_deepseek_credentials()` 已改为优先 harness 配置。
- 任务执行三条路径：tool 角色→`_run_tool_loop`；文本角色(_TEXT_ONLY_ROLES)→`_run_openai_compatible`；其余→`_should_use_direct_api` 决定直连 vs 本地 CLI。`_run_openai_compatible` 用 urlparse(base_url) 拼 `{path}/chat/completions`，deepseek/codebuddy 的 base（有无 /v1 均可）兼容。

## Do-Not-Repeat

- [2026-07-11] 给用户交付后端改动时必须显式说明『此改动在 XX:XX 落盘，需要在此之后的重启』；更好的做法已落地——start.sh 默认 uvicorn --reload，后端与前端一样热更（AG_NO_RELOAD=1 关闭）。连环后端修复期间不要让用户手动追重启。

- [2026-07-11] 代码代龄指标必须在进程启动时缓存（git rev + process_started_at）；请求时现查 git 报告的是磁盘 HEAD 不是进程代码——commit 后未重启会谎报新版本（bug-052 实锤误导了一轮排查）。判断'改了没生效'一律看 process_started_at 是否晚于最后一次代码落盘。

- [2026-07-11] 拆分前端模块时（如 tasks-view.js 从 agent-team-config.js 抽出），新文件引用的每个助手函数（hideViewLoading 等）必须确认在 utils.js/全局已定义；且同名函数导出 window 会覆盖旧文件的可用实现——列表『完全空白连占位行都没有』九成是 load 函数首行 ReferenceError（bug-044）。排查先看 console 而不是后端数据。

- [2026-07-11] 加密密钥库(.api_keys.json)必须合并式写入：teams.json 反序列化按设计丢明文 key，任何“按内存全集整体重写”的持久化都会在内存缺 key 的时机把磁盘 key 连锅端（bug-043，症状=重启后密钥全丢要求重输）。删除 key 只能走显式 delete_model_api_key。

- [2026-07-11] 页面新增 right-panel 类面板必须放进布局容器内与既有面板同级（rp-secs depth1）；放在容器闭合标签之后（depth0）时隐藏期无症状、显示后会把 3D 主视图挤出布局（bug-028）。交付前用 div 深度扫描校验。
- [2026-07-11] CodeBuddy 与 Fable 5 会并行改同一工作树：整文件 Write 重写前先 grep 最新内容确认无并行新增（本次覆盖了 CodeBuddy 的 on_step/cat_commentary/write_lineage，靠 todos 契约才复原）。优先 Edit 局部替换而非 Write 整写。

<!-- Mistakes made and corrected. Each entry prevents the same mistake recurring. -->
<!-- Format: [YYYY-MM-DD] Description of what went wrong and what to do instead. -->
- [2026-06-13] 执行沙箱无 fastapi/pytest 且 pip 被防火墙拦截（proxy 403），无法安装。所有"接口通路门"(2xx)类验收只能在本机 `rtk` 环境复跑，不要尝试在沙箱跑 test_v4_apis 等依赖 fastapi 的用例；可在沙箱跑的仅 `node --check` 与纯逻辑（但纯逻辑也需 pytest，沙箱同样缺）。
- [2026-06-13 更正上一条] Cowork 沙箱环境已变化：**pip 现可用**（pypi 在网络白名单内，`pip install fastapi pytest httpx` 成功）；**前端 vitest 也能在沙箱跑**——先 `npm i @rollup/rollup-linux-arm64-gnu @esbuild/linux-arm64` 补 linux 原生二进制（项目 node_modules 是 macOS arm64 装的），再从**项目根目录** `npx vitest run src/frontend/__tests__/xxx.test.js`（现有 system-evolution 3 用例全绿）。真正的硬限制是**网络白名单**：LLM 域名（api.deepseek.com、copilot.tencent.com/v2）DNS 解析直接失败、本机后端 8080、本机 5173 全部不可达。故依赖**真 LLM / 起后端 / 浏览器**的验收仍必须本机 `rtk`；纯代码/语法检查/前端单测可在沙箱完成。codebuddy 的 key 即使配在 app 里，沙箱也调不到该 LLM（域名不可达，非 key 问题）。
- [2026-06-13] 跨文档状态会滞后：本文件 v4 的 C-4.1/D-0.2 标 [~]，实际已由 frontendBigChangeTodos F3/F4 完成。核对 todos 时必须跨 5 份文档交叉比对（全局优化 / 数字孪生v3.1 / 场景演练v4 / AgentsGroupConfig / frontendBigChange），避免误报未完成。
- [2026-06-17] 弹窗"点击只出遮罩、内容不显示"几乎都是 CSS 级联污染：页面把 `.modal` 当弹窗内容面板用，同时链入全局 `css/components.css`（其中 `.modal{display:none}`）。页面局部 `.modal` 若不声明 display，全局 display:none 按属性级联胜出 → 面板被隐藏。修法固定：在该页局部 `.modal` 规则加 `display:block`（单处）。已发生于 plaza.html 与 agent-team-config.css。**不要**误诊为 JS/ID 编码问题去改逻辑。排查命令：浏览器对 overlay 与 `.modal` 取 getComputedStyle，看 panel display 是否 none。
- [2026-06-17] 前端文件若用 IIFE 封装且模板内使用 inline onclick，必须把每个 onclick 引用函数显式挂到 window。仅在文件内定义函数不等于全局可见；漏导出会在点击时报 `ReferenceError: <fn> is not defined`（本次为 wizard.js 的 addExp）。
- [2026-06-17] 本机重启服务验证时必须用项目 `./start.sh`（会进入项目 virtualenv 并带齐 aiohttp 等依赖）。直接 `python3 src/backend/main.py` 可能使用系统解释器，导致会话聊天接口报 `ModuleNotFoundError: aiohttp` 假性回归，干扰真实问题定位。
- [2026-06-17] 智能体详情「技能」行操作不要把“删除”放进绑定状态分支里。删除是行级通用操作（无论当前是绑定还是未绑定都应可见）；仅“绑定/解绑”按钮按 isBound 切换，避免出现只有“绑定”但没有“删除”的页面回归。
- [2026-06-17] inline onclick 传参不能用 HTML 转义值（如 `escapeHtml(skill_id)`）直接当业务 ID；`&amp;` 等实体会导致后端删除/更新命中失败。参数应 `encodeURIComponent` 传递，在处理函数内 `decodeURIComponent` 还原，并在 URL path 段再次 `encodeURIComponent`。
- [2026-06-18] skill-extract 去重不能只看 source_text 前缀（如前 2000 字）且不能丢失来源上下文；不同讨论常有模板化前缀，会发生跨议题误判“已萃取过”。应使用来源签名（source_plaza_id/source_discussion_id/source_output_id）+ 全文哈希，至少要比对全文哈希而非前缀。
- [2026-06-18] 队列删除语义不能只删除当前项；若希望“删除后不再自动出现”，必须写 tombstone（来源指纹）并在 start_extraction 前拦截。否则同来源再次触发会复活，造成“删了又出现”。
- [2026-06-18] LLM 不可用时不能用固定兜底技能模板（同一组 ES/Terraform/成本等）；这会让不同议题看起来都萃取成“其他议题”。兜底也要绑定 source_title/source_text 动态生成，至少名称需体现当前议题关键词。
- [2026-06-18] skill-extract 队列 UI 不能无条件展示团队全部历史项；从议事厅跳转场景必须按 source_meta(plaza/discussion/output)做来源隔离，否则用户会把历史项误认为“当前萃取结果”。
- [2026-06-18] skill-extract 详情弹窗里“按钮没展示出来”优先排查 CSS 布局裁切（tab 条/usage 头部动作区的 flex 单行挤压），不要先怀疑 JS 显隐。先查元素是否在 DOM 中且无 `display:none`，再修为 `flex-wrap`/`overflow-x:auto` 并给动作区在窄宽度下换行。

## Decision Log

<!-- Significant technical decisions with rationale. Why X was chosen over Y. -->
- 任务执行支持两种模式(execution_mode)：linear=原线性 Claude 流水线(默认)；collaborative=智能体广场多轮讨论(`_start_task_collaboration`→plaza create_plaza/add_participant/create_discussion/run_discussion→共识→回写 task.metadata.collaboration+artifacts→_finalize_task_terminal_state)。广场用 set_chat_fn(harness.chat) 即系统配置 LLM。批量/队列路径(_real_task_executor)暂仍线性。

- [用户校准 2026-07-04] 两阶段经济学铁律: Plaza集体智慧阶段绝不做token优化/预算约束/效能计量(智慧无价,只求不跑题+计划落地); 成本纪律从执行计划产生后开始; 数字孪生的意义=对同一计划做团队×技能×协作的候选组合竞标,质量达标中选token效益最优者执行。任何成本优化建议不得触碰讨论阶段。
- [用户原则 2026-07-04] 考察智能体之间的协作能力必须在 Agents 数字孪生场景下完成——孪生3D不是装饰,是协作的观测仪器(协作光线/热度统计/镜像层)。
