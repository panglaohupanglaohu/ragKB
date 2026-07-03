# Memory

> Chronological action log. Hooks and AI append to this file automatically.
> Old sessions are consolidated by the daemon weekly.

- 2026-06-12T14:48:00Z | G1-2 完成收口：在 skill_extractor.approve_item 接入 ClassificationStore.seed_reserve_from_extraction（幂等），实现“萃取完成即写入 reserve 分类记录”；新增 tests/test_skill_classifier.py::test_seed_reserve_from_extraction_idempotent，pytest 14 passed。
- 2026-06-12T14:58:00Z | G3-2 本机联测收口：trial_api 增加 routing_comparison/routing_benefit 输出，branches 列表暴露 routing_strategy；新增 tests/test_v4_apis.py::test_routing_strategy_fork_comparison；pytest tests/test_v4_apis.py 14 passed。
| 04:36 | 核对5份todos+排查协作图空白(已修复) | docs/Agent数字孪生场景演练与技能进化todos.md | C-4.1/D-0.2核销为[x]+新增G分派章节(Claude/Reasonix) | ~3k |
| 04:59 | 新增本机验收脚本(rtk pytest+全绿回写[~]→[x]) | scripts/verify_v4_local.sh | 覆盖test_v4_apis/secs/full_flow/move,排除真LLM项 | ~1k |
| 05:07 | verify脚本加--with-server(E-5活后端脚本跑法) | scripts/verify_v4_local.sh | test_full_flow非pytest需脚本式跑8080,secs+flow全绿才回写E-5 | ~0.6k |
| 05:40 | 修复system-evolution实时更新链路(P0) | src/frontend/js/system-evolution.js + src/backend/agent_team_api.py | 后端补GET /evolution/stream(SSE,只读快照,不改引擎)+前端onerror轮询降级修复;node --check+py_compile+vitest(3 passed)通过;真实SSE需本机rtk验;记buglog bug-002 | ~3k |
| 05:42 | 产出system-evolution优化plan+事无巨细todos(Claude/Reasonix分派,Reasonix多领) | docs/system-evolution优化plan.md, docs/system-evolution优化todos.md | 现状=已v2优化;头号缺陷=SSE实时更新整条死;cerebrum更正沙箱pip/vitest现可用但LLM域名+8080+5173不可达 | ~2k |
| 06:10 | 产出plaza优化plan+带伪代码todos(前后端,Reasonix多领) | docs/plaza优化plan.md, docs/plaza优化todos.md | 真实缺陷:SSE无onerror/无重连(后端全量重放需配重连去重)、Three.js不dispose致GPU泄漏、live消息esc vs 重载mdLite不一致、隐藏页仍渲染、confirm阻塞、escalation按index脆弱、SSE可加Last-Event-ID断点续传 | ~3k |
| 14:15 | 落地plaza Claude项(A-1/A-2/B-1/C-1) | src/frontend/js/plaza.js | SSE加onerror+指数退避重连+teardownSSE统一收口;_seenMsgKeys去重(去掉init门控,改去重既不重复又补断线期消息);disposeObject3D/disposeSceneAgents释放GPU;live分支esc→mdLite;beforeunload清理。7个plaza vitest全绿。F-2核对:escalation无稳定id需引擎改造(留本机) | ~3k |
| 06:30 | skill-extract调研+plan/todos+技能闭环实现 | docs/skill-extract优化plan.md, docs/skill-extract优化todos.md, storage/skills/c0de7a11.json, scripts/skill_closed_loop_demo.py, README.md | 现状最成熟(SSE重连/dispose/CSRF已健全);头号bug=HTML 10个重复id致第二复核UI错位;旗舰=设计"结构化代码评审"skill并在沙箱真跑闭环:twin_loop success_p=clamp(0.3+0.6*prof);code_review_delivery场景baseline 0.45 vs treatment 0.85,30种子,code_review成功率72.1%→90.4%(+18.3pp);README加"技能闭环演示"章节 | ~5k |
| 16:05 | 修复skill-extract P0重复id | src/frontend/skill-extract.html, src/frontend/js/skill-extract.js | block2快速确认面板10个重复id加-pipe后缀;JS新增_eachGateEl显示同时更新两套门禁UI,toggleReviewForm(scope)/submitReviewAction(action,scope)按''/'pipe'作用域读写;终检无重复id;vitest 5用例全绿;闭环demo exit=0。C-1 request_id已由Reasonix做 | ~2k |
| 16:40 | 本机真后端闭环脚本+模拟按钮改赋予注入(plan/todos) | scripts/skill_closed_loop_live.py, docs/skill-extract优化todos.md(S-5), docs/skill-extract优化plan.md(4.6) | 挖出真实缺口:skill_router.assign()只append agent.skills不写proficiency_store→UI赋予不抬升孪生熟练度,闭环UI这环断;S-5方案:⚡模拟→⚡赋予/注入真动作+assign按metadata.target_skill抬proficiency≥0.8返回proficiency_boosted;live脚本打8080试炼API设0.45/0.85对照离线+18.3pp,py_compile通过 | ~2k |
| 22:45 | 恢复误删build_system团队+硬化批量删团队 | storage/teams/teams.json(+bak), src/frontend/js/agent-team-config.js | 用种子create_build_team().to_dict()重建build_system(7 agent/2模型,与现有团队同schema)写回teams.json,先备份teams.json.bak.*;需用户重启后端加载。删除bug根因:agent-team-config与tasks-view同页共享隐式全局tid,批量删除用裸fetch+手动csrf且删后AG.state/loadView可能不刷新→"无效"。重写deleteSelectedTeams:只认勾选id、循环变量改名解耦tid、改用统一api()鉴权、404视为成功、finally必loadTeams刷新。node--check+team-unified 8/8+config 4/4全绿 | ~2k |
| 16:30 | 落地C-1.2(进化拒绝结构化原因前端) | src/frontend/js/digital-twin/v4-evolution.js | _evoErrCN(code,detail)升级:no_weak_skills_identified追加后端error_detail(扫描N试炼/usage M条/无数据or都达标);两处rejected/failed渲染统一传run.error_detail+_dtLogConsole。node--check+5 vitest绿。试炼页Claude项全done(A-1.1/B-1 Reasonix做、A-2/C-1/D-1 我做、C-2.1/C-2模型字段 Reasonix);剩C-2.2真LLM/D-2/D-3打磨/E-1留本机或Reasonix | ~1k |
| 12:10 | 落地试炼页Claude项(A-2/B-1/C-1/D-1) | src/backend/sandbox/trial_api.py, src/frontend/js/digital-twin/secs-core.js, v4-evolution.js, docs/试炼页优化todos.md | A-2.2 evaluate响应加meaningful+note(有场景且task>0.01);A-2.1/D-1 secs-core控制台无场景标"基线分"+task≈0警告;C-1 v4-evolution加_evoErrCN中文映射(no_weak_skills_identified→可操作引导)两处rejected渲染+console。node--check(secs-core/v4-evolution)+vitest 14/14;trial_api改动语法OK(py_compile仅卡既有3.12多行f-string,沙箱py3.10所致)。未做:A-1.1启动确认弹窗/C-2.1后端结构化原因(模型改动风险)/C-1.2链路UI失败态,留本机 | ~2.5k |
| 2026-06-15 | 任务执行防卡死+协作前端(T1.1/T4.2/T2.1/T3.1/T3.2/T5.5) | src/backend/agents/api.py, src/frontend/js/tasks-view.js, src/frontend/agent-team-config.html, docs/任务执行协作化plan与todos.md | T1.1:_STEP_WALL_TIMEOUT_SEC=1200墙钟超时(monitor running分支,stall检测前,超时kill proc→failed→复用重试逻辑);T4.2:_run()顶部无LLM配置fail-fast(no_llm_configured);T2.1:_reconcile_orphan_tasks()启动对账(无monitor无活session或超_TASK_MAX_RUN_SEC=10800→failed orphaned);T3.1:_annotate_stuck补current_step/last_activity_sec;T5.5:HTML加tk-exec-mode选择器+JS提交带execution_mode+协作badge;T3.2:retryStep/skipStep按钮(复用现有endpoint)。py_compile+node--check全绿 | ~4k |
| 11:30 | 本机验收脚本+试炼页plan/todos | scripts/local_acceptance.sh(新), docs/试炼页优化plan.md(新), docs/试炼页优化todos.md(新) | local_acceptance.sh汇总本机验证(vitest/py_compile/闭环demo/--with-server跑pytest+SSE+live闭环+浏览器清单),沙箱离线7PASS/0FAIL/3SKIP。试炼页两根因:无场景空跑(_generate_default_tasks→reward≈0,0.315是其它维度基线分,误导)+ no_weak_skills_identified(identify_weak_skills无usage即拒,UI不可操作)。plan/todos出P0无场景校验+评分语义标注、P1五维breakdown+进化拒绝中文可操作、P2可读性,带伪代码+Claude/Reasonix分派 | ~3k |
| 10:52 | L4接入补齐三页(实时跟随) | src/frontend/js/agent-team-config.js, system-evolution.js, docs/联动优化todos.md | Reasonix已给三页接入AGCtx(include+set+init-read);我补缺口=实时跟随AGCtx.on订阅:agent-team-config(下拉同步+loadView)、system-evolution(ev-team-select同步+loadEvolveSkills,防重复订阅);plaza无页面级团队选择器仅作基座引入。node--check全过+25 vitest全绿。跨页实时跟随浏览器验证留本机 | ~1.5k |
| 10:05 | T1任务卡死只读标注+L4推广skill-extract | src/backend/agents/api.py, src/frontend/skill-extract.html, src/frontend/js/skill-extract.js, docs/任务执行优化todos.md, docs/联动优化todos.md | T1安全部分:advance_workflow给next_step打started_at;list/detail端点加只读_annotate_stuck(elapsed_sec/stuck/threshold,running超1800s标stuck,不改状态)。L4.2:skill-extract引入ag-context.js+selectTeamChip上报AGCtx.set。py_compile+node--check+vitest 8/8。自动失败(T1.1状态改动)留本机 | ~2k |
| 06:10 | L4 AGCtx总线+聊天乐观渲染+任务卡死分析 | src/frontend/js/ag-context.js(新), __tests__/ag-context.test.js(新), Agent-digital-twin.html, digital-twin-cli.js, agent-detail.js, docs/任务执行优化todos.md(新) | L4.1总线落地(get/set/on+localStorage ag_ctx_*跨页+storage静默入站去重防循环;team双写兼容ag_current_team);数字孪生页接入(dtSetCurrentTeam→AGCtx.set+on订阅fromCtx防循环);ag-context单测4/4+合计22 vitest全绿。聊天sendChatMsg加乐观渲染(立即插用户气泡+正在思考占位,修"像没发出"问题)。任务卡死根因:每步真起Claude会话靠monitor推进、无超时→LLM不可达即无限running,出T1-T4优化todos | ~4k |
| 01:20 | 联动审计+plan/todos+数字孪生左右联动落地 | docs/联动优化plan.md, docs/联动优化todos.md, src/frontend/js/digital-twin/secs-core.js, src/frontend/js/digital-twin-cli.js | 根因:同一"当前团队"被三套状态各自持有(S.selectedTeams左多选/_selectedTeamId右SECS/localStorage selected_team)+跨页不共享;SECS→左早已联动但左→SECS缺失;L0已落地:secsSyncTeamFromLeft+secsSyncSceneFromRoom单向setter,toggleTeam/switchRoom/showRoom调用,room_<id>场景映射;node--check+数字孪生vitest 16/16;待做L1(三套统一)/L2(跨页ag_current_team)/L4(AGCtx总线) | ~3k |
| 01:00 | S-6.1 赋予/注入改必须显式勾选 | src/frontend/js/skill-extract.js, docs/skill-extract优化todos.md(S-6) | 实测发现左右栏联动(共享routerResults/routerSelectedSkills/selectedAgentId)但赋予/注入未勾选时盲选Top-K塞松匹配技能;改为仅注入显式勾选项,未选则提示+Toast不自动注入;todos加S-6(多需求支持/雷达文案澄清待做);vitest 4/4 | ~1k |
| 00:45 | 落地S-5.1/5.2/5.3代码 | src/frontend/skill-extract.html, src/frontend/js/skill-extract.js, src/backend/agents/skill_router.py | 前端:按钮⚡模拟→⚡赋予/注入(_executeInjectSkills:选中直接赋予/未选则路由→自动选TopK→赋予),注入成功提示proficiency_boosted+计数;后端:assign()加_resolve_target_skill+_boost_proficiency抬proficiency≥0.8返回proficiency_boosted(try/except容错)。py_compile OK,vitest 5/5,无重复id。真效果本机用skill_closed_loop_live.py验 | ~2k |
| 00:18 | designqc: captured 2 screenshots (38KB, ~5000 tok) | / | ready for eval | ~0 |
| 00:18 | designqc: captured 2 screenshots (38KB, ~5000 tok) | /system-evolution.html,/plaza.html,/Agent-digital-twin.html,/skill-extract.html,/cost-dashboard.html,/sandbox-twin.html,/agent-team-config.html | ready for eval | ~0 |
| 00:19 | designqc: captured 2 screenshots (38KB, ~5000 tok) | /system-evolution.html | ready for eval | ~0 |
| 00:19 | designqc: captured 2 screenshots (38KB, ~5000 tok) | /plaza.html | ready for eval | ~0 |
| 00:19 | designqc: captured 2 screenshots (38KB, ~5000 tok) | /Agent-digital-twin.html | ready for eval | ~0 |
| 00:19 | designqc: captured 2 screenshots (62KB, ~5000 tok) | /skill-extract.html | ready for eval | ~0 |
| 00:19 | designqc: captured 6 screenshots (181KB, ~15000 tok) | /cost-dashboard.html | ready for eval | ~0 |
| 00:20 | designqc: captured 6 screenshots (218KB, ~15000 tok) | /sandbox-twin.html | ready for eval | ~0 |
| 00:20 | designqc: captured 2 screenshots (38KB, ~5000 tok) | /agent-team-config.html | ready for eval | ~0 |
| 09:54 | designqc: captured 2 screenshots (38KB, ~5000 tok) | /system-evolution.html | ready for eval | ~0 |

## Session: 2026-06-14 23:25

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-06-14 23:31

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-06-14 23:32

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-06-14 23:42

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-06-14 06:26

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|

## Session: 2026-06-14 06:26

| Time | Action | File(s) | Outcome | ~Tokens |
|------|--------|---------|---------|--------|
| 03:45 | 任务执行LLM改读系统配置(根因修复) | src/backend/agents/api.py · docs/任务执行优化todos.md | _harness_provider_credentials+优先harness;T4.1→[~]待本机 | ~2k |
| 05:48 | 任务新增协作模式(广场驱动,与线性并存) | src/backend/agents/api.py · docs/任务执行优化todos.md | _start_task_collaboration+execution_mode开关;plaza多轮讨论→共识→回写任务;py_compile通过 | ~3k |
| 05:56 | 落自包含规划+伪代码todos(任务协作化+防卡死) | docs/任务执行协作化plan与todos.md | 含落点/行锚/伪代码/验收/回滚,不打工具标签可被任意工具接续 | ~3k |
| 16:05 | skill-extract 批准入库静默失败修复+重登验证 | src/frontend/js/skill-extract.js · .wolf/buglog.json | approveAs 失败弹明确提示;浏览器重登后 approve HTTP200 ready→approved | ~4k |
| 16:06 | awsOps 两个非LLM待优化项修复 | src/frontend/js/skill-extract.js · docs/awsOpsE2ETestPlanTodos.md | renderRouterResults 按skill_id去重+版本徽章;init加_ensureAuthOrRedirect认证门禁;vitest 171 passed | ~3k |
| 16:08 | awsOps E2E复跑+标注 | docs/awsOpsE2ETestPlanTodos.md · docs/reports/aws-ops-e2e-report.* | PASS=8/FAIL=5,FAIL全为DeepSeek key无效(secret,需用户填)根因 | ~2k |
| 06:28 | 修复技能页LLM路由与版本创建耦合问题 | src/backend/agents/api.py, chat_harness.py, skill_evolver.py, skill_verifier.py, src/frontend/js/skill-extract.js, src/frontend/skill-extract.html | 演化/验证按team默认模型路由(config_override)+api_base_url统一strip；效果页新增“展示对比”按钮；版本创建改走/version/snapshot脱离LLM依赖；后端健康恢复 | ~3k |
| 16:32 | 修复plaza控制台CSP/Three废弃警告 | src/frontend/plaza.html, src/frontend/js/plaza.js, .wolf/buglog.json | connect-src放行ga.jspm.io sourcemap；Clock→performance.now；PCFSoftShadowMap→PCFShadowMap；plaza vitest 10/10 + node --check 通过 | ~1k |
| 17:18 | 修复删除叉触发灰屏与data:audio CSP噪音 | src/frontend/plaza.html, src/frontend/js/plaza.js, .wolf/buglog.json | 移除unlockAudio data:audio播放；CSP增media-src；新增静态m-confirm并修正overlay关闭守卫；plaza vitest 10/10 + node --check通过 | ~1.5k |
| 18:51 | 修复数字孪生页运行时无限连接中 | src/frontend/js/digital-twin/secs-core.js, .wolf/buglog.json | runtime bootstrap 从 load 前移到 DOMContentLoaded；runtime-status 加4s超时，避免永远转圈；digital-twin vitest 10/10 + node --check通过 | ~1.5k |
| 18:52 | 移除数字孪生页失效 Lucide 样式依赖 | src/frontend/Agent-digital-twin.html, .wolf/buglog.json | 外链 lucide.min.css 返回404且页面未使用；删除引用，rg 无残留；digital-twin vitest 10/10 通过 | ~0.8k |
| 2026-06-17 | 修复模型与连接页 CodeBuddy 编辑不弹窗 | src/frontend/js/agent-team-config.js, .wolf/buglog.json | loadModels 的 inline onclick 改为传 URL 编码 model_id；openEditModel/delModel/setModelDefault 统一解码；编辑前查找模型增加 trim 兜底与 cache fallback，恢复 CodeBuddy 编辑弹窗 | ~1k |
| 19:22 | 修复智能体技能删除不生效 | src/frontend/js/agent-detail.js, .wolf/buglog.json | 删除按钮参数改为 encodeURIComponent 传递，deleteSkillWithContext 内 decode；DELETE 路径段也 encode，修复特殊字符 ID 删除失败；node --check + get_errors 通过 | ~1k |
| 18:25 | 修复智能体详情可读性与会话LLM回退 | src/frontend/js/agent-detail.js, src/backend/agents/api.py, src/backend/agents/chat_harness.py | 人格页技能ID→名称映射、关系页优先name；会话聊天针对CodeBuddy跳过tools并加11133参数错误降级重试，浏览器实测 send_session_message 返回 assistant=“连接正常” 非 fallback | ~4k |
| 19:05 | 修复智能体技能页缺少删除入口 | src/frontend/js/agent-detail.js, .wolf/buglog.json | 智能体详情→技能列表将“删除技能”按钮从仅已绑定可见改为所有技能行可见；已绑定仍保留“解绑”，未绑定保留“绑定”；node --check + get_errors 通过 | ~0.8k |

## 2026-06-17 — fix: agent-team-config 编辑弹窗不显示
- 根因: 全局 components.css `.modal{display:none}` 污染本页用作内容面板的 `.modal`（局部未声明 display），属性级联致面板隐藏，仅遮罩可见。
- 修复: src/frontend/css/agent-team-config.css 局部 `.modal` 加 `display:block`（单处）。
- 还原: 之前误诊的 agent-team-config.js encode/decode 改动已 git checkout 还原。
- 验证: 浏览器复现 openEditModel(qwen3) → panelDisplay block、面板 456x257 可见、编辑表单完整渲染。

## 2026-06-17 — fix: 向导专长领域 addExp 未定义
- 现象: 新建智能体 → 人格设定 → 专长领域点击「+ 添加」报 ReferenceError: addExp is not defined。
- 根因: wizard.js 为 IIFE，模板用 inline onclick；addExp/addPerm/rmPerm/togWzChan/wzFinish 未导出到 window。
- 修复: 在 wizard.js 底部补齐 window 导出上述函数。
- 验证: node --check 通过；浏览器里 typeof window.addExp===function，执行后可新增专长 chip。

## 2026-06-17 — fix: 智能体技能页无删除按钮
- 现象: 智能体详情→技能中，部分页面仅显示“绑定”按钮，没有技能删除入口。
- 根因: ag-skills 行模板把删除按钮放在 `isBound` 分支内，未绑定技能行不会渲染删除操作。
- 修复: 将删除按钮提升为行级通用操作（绑定与未绑定均可见），仅绑定/解绑按钮继续按状态分支。
- 验证: node --check src/frontend/js/agent-detail.js + get_errors 均通过。

## 2026-06-17 — fix: 议事广场底部按钮被挤出视口（前端优化回归）
- 现象: plaza.html 底部「+ 新建广场」「开始」按钮看不见（以前修过又复现），用户疑前端优化导致。
- 根因: UI美化(8a420c7)把顶栏换成普通流的 .topbar-ws(position:relative,56px)，但 .layout 仍保留固定顶栏时代的 margin-top:56px，叠加 height:calc(100vh-56px) 使内容溢出视口 56px，底部按钮被推出可视区。
- 修复: 删除 .layout 的 margin-top:56px 并加注释。浏览器实测 .btn-new/#btn-start 回到视口内(inView=true)，.left/.right 正好 56→561 填满。
- 关联: bug-021 / 同源回归 bug-016。

## 2026-06-17 — doc: 冻结 UI美化plan/todos 阶段A
- 决策: 用户选「方案A 保留但冻结」。UI美化优化plan.md/UI美化todos.md 不删除。
- 动作: plan 顶部加 ⚠️暂停 banner（A1/A4/A6 已致 bug-016/bug-021）；todos A4 加「步骤0 固定顶栏偏移审计」+ 浏览器实测验收项；plan §6 三决策未拍板前不得续推 A1/A4/A6。

## 2026-06-17 — fix: plaza escalations 404 持续刷屏
- 现象: 控制台反复报 `API 404: /api/v1/agent-config/plaza/escalations?... 广场不存在`，同一讨论上下文每 2~3 秒重复触发。
- 根因: `refreshEscalationState` 被多处并发/定时触发；后端返回 404 时前端没有熔断与并发去重，导致同一上下文持续重试。另有深链/本地缓存上下文需前端容错自愈。
- 修复: plaza.js 增加按讨论维度熔断(`escalationFetchBlocked`) + in-flight 去重(`escalationFetchInFlight`)；`refreshEscalationState` 增加 DOM/localStorage 上下文回补与已知广场校验；init 深链讨论选择改为仅在 deepLink plaza 与当前选中一致时采用。
- 验证: 浏览器并发触发 3 次 `refreshEscalationState(true)` 仅 1 次 escalations 请求；不再出现持续 404 请求风暴。
- 关联: bug-022。

## 2026-06-18 — fix: ASSIGN 下拉 Build System 选不中
- 现象: 在 plaza 执行计划卡片里将 ASSIGN 选为 Build System 后，几秒后又自动跳回 AI 编程团队，用户体感“选不中”。
- 根因: renderPlanCard 重渲染会替换整块 DOM，`#assign-team` 新节点默认选中第一个 option；未保留旧值。
- 修复: renderPlanCard 渲染前读取旧值 `previousTeam`，回退 `AGCtx.get('team')` 作为 `preferredTeam`；options 对匹配项加 selected，并在渲染后再次赋值 `assign-team.value=preferredTeam`。
- 验证: 浏览器实测选择 build_system 后等待 6 秒（节点重建 sameNode=false）仍保持 build_system。
- 关联: bug-023。

## 2026-06-18 — fix: QA 误判导致 deploy 被阻断
- 现象: deploy 报“部署已被 QA 阻断: QA 验证结论 = FAIL”，并最终“重试上限已达(2)”。但任务 metadata 里 `qa_feedback.verdict` 已是 PASS。
- 根因: deploy QA Gate 在已有结构化 verdict 的情况下仍做 test markdown 正则扫描，文本内出现 FAIL/BLOCKER 关键词会误触发 gate_blocked。
- 修复: backend `api.py` 中 QA Gate 改为优先使用结构化 verdict；若 verdict=PASS/PASSED/OK/SUCCESS 则跳过 markdown 正则兜底，仅在 verdict 缺失/未知时才回退文本规则。
- 验证: py_compile + get_errors 通过；新任务不会再因 PASS 场景被 regex 误判阻断。
- 关联: bug-024。

## 2026-06-18 — fix: 删除任务 404(Task not found) 的幂等处理
- 现象: 控制台出现 `DELETE .../tasks/<id>/remove 404`，前端提示删除失败。
- 根因: 任务 ID 已陈旧/已不存在；删除语义本应幂等，但前端把 404 作为硬失败。
- 修复: `src/frontend/js/tasks-view.js` 中单条删除与批量清理都对 404+Task not found 视为“已删除”；并在 `src/backend/agents/api.py` 把 remove 路由改为幂等（missing -> already_absent）。
- 验证: 浏览器同 ID 返回 404 时前端判定 `treatedAsSuccess=true`；语法/错误检查通过。
- 关联: bug-025。

## 2026-06-18 — fix: 讨论结束后看不到萃取等按钮
- 现象: 已结束讨论卡片在长标题场景下只看到部分按钮或看不到“萃取/网页”。
- 根因: `plaza.js` 把结束态按钮和标题塞在同一行，标题过长挤压按钮区域；样式未做独立动作行与换行容错。
- 修复: 结束态按钮改为独立 `.disc-actions` 行；`plaza.html` 增加 `.disc-actions` 可换行，`.disc-act` 强制 nowrap，标题 `.tp` 支持 `min-width:0 + word-break`。
- 验证: 浏览器检查已结束讨论 actions=`[重新讨论, 萃取, 网页]`。
- 关联: bug-026。

## 2026-06-18 — fix: 清掉 escalations 的“广场不存在”提示
- 现象: 控制台出现 `API 404 /api/v1/agent-config/plaza/escalations ... 广场不存在`。
- 根因: `refreshEscalationState` 使用全局 `api()`，404 会被 `api.js` 统一 `console.warn`，即便前端已做熔断也会先打印噪音。
- 修复: `plaza.js` 改为该接口使用 scoped `fetch`，在本地处理 404（广场/讨论不存在）并熔断，不再触发全局 API 警告。
- 验证: 浏览器两次触发 refreshEscalationState 后 `hasEscalation404Log=false`。
- 关联: bug-027。

- 2026-06-18 docs 签名治理:总规则 docs/SIGNING_RULE.md + 校验器 check-docs-signoff.cjs(selftest 5/5,全量 0 FAIL/29 WARN);ponytail 一行注入(copilot-instructions L19 + AGENTS.md §5);用户选 WARN-only、不挂钩子
- 2026-06-18 skill-extract 跨议题误去重修复: 去重从 source_text 前2000字改为 source_meta(plaza/discussion/output)+全文SHA-256；API start 支持 source_meta 透传，skill-extract.js 自动带来源元数据；不同议题不再误命中“该文本已萃取过”。(bug-028)
- 2026-06-18 skill-extract 删除后复活修复: delete_item 增加来源墓碑(source_key+全文sha256)并持久化；start_extraction 命中墓碑时不再入队，仅返回 dedup_skipped/rejected，避免“右侧删了再萃取又出现”。(bug-029)
- 2026-06-18 skill-extract fallback 议题化: LLM 不可用时不再输出固定ES/Terraform/成本模板，改为根据 source_title+source_text 关键词动态生成候选，避免跨议题同名误导。(bug-030)
- 2026-06-18 skill-extract 队列来源隔离: 从议事厅跳转时，右侧队列按 currentExtractSourceMeta 过滤，只显示当前讨论来源的项目，不再混入历史旧议题。(bug-031)
- 2026-06-18 skill-extract 详情弹窗按钮缺失修复: 按钮并非 JS 隐藏，而是 modal tab/usage action 的 flex 单行裁切；在 skill-extract.html 增加稳定 class 并在 skill-extract.css 增加 wrap/overflow 响应式规则，确保“展示对比/刷新/快捷建议”可见。(bug-032)
- 2026-06-22T18:08:00Z | 全局重构收尾:实现10.6.1 ensureTeamPositioned + 10.9 regression测试补全 + 文档状态标记 | secs-core.js, regression-smoke.cjs, docs/全局重构todos.md | secs-core.js新增ensureTeamPositioned(teamId,team,fallbackRoom)在sexySelectTeam内调用;regression-smoke.cjs第21b节新增breakdown/trend/detail/lever-split/ratchet/targets/duplicates 7个测试;todos.md已标记项的[x]状态+签名时间戳更新;所有Python/JS编译通过+check-docs-signoff 0 FAIL | ~3k
