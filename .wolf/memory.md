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
