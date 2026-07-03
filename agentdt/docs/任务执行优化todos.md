# 并发任务"一直执行中"优化 Todos

> 起因:并发任务页大量任务长期 `执行中`(截屏:217 总 / 5 运行中 / 159 完成),流程进行中不收敛。
> 根因(已核查 `src/backend/agents/api.py`):
> - 任务按 workflow 分步(PM分解→研究→架构→开发→测试→部署→文档),每步 `advance_workflow` 时 `_start_claude_session` **真起一个 Claude/LLM 会话**,靠 `_start_harness_monitor` 检测完成再推进下一步;
> - 全程**没有任何步骤级/任务级超时**:一旦某步的 LLM 会话挂起、失败无回信、或 monitor 漏掉完成信号,该步永远停在 `active`,任务状态就永远 `running`(`advance_workflow` 只在收到推进时才翻状态);
> - 因此在 LLM 不可达 / 会话异常退出时,任务会无限"执行中"。
> 编写日期:2026-06-14
> 标注:【Claude(沙箱可 py_compile,真验证本机)】/【Reasonix(本机/浏览器)】

---

## T1. 步骤级超时 + 自动失败/重试 — 【Claude 实现 + Reasonix 本机验】
- [~] **T1.0(已落地·安全部分)** 步骤激活打点 `started_at`(advance_workflow);任务列表/详情端点新增**只读**标注 `elapsed_sec` / `stuck`(running 超 `_TASK_STUCK_SEC=1800s` 即 true)+ `stuck_threshold_sec`,**不改任务状态**,供前端高亮"可能卡死"。　⟦已落地 api.py:`_annotate_stuck`/`_ts_to_epoch`;py_compile 通过;前端 8 vitest 全绿(未受影响)⟧
- [ ] **T1.1(待本机)** 在此基础上加**自动失败/重试**:`_start_harness_monitor` 周期检查 active 步骤 `started_at` 超 `STEP_TIMEOUT` → 标 `failed`(或 retry<N 自动重起),写 `failure_reason: step_timeout`。涉及任务生命周期状态改动,需起服务运行时验证,留本机。
- [ ] **T1.2** `_start_claude_session` 包超时与异常回调:会话进程退出码非 0 / 抛错 → 立即把步骤置 `failed` 并停止该任务推进,不再无限等待。

  伪代码:
  ```python
  STEP_TIMEOUT = 600  # 秒
  def _check_stuck_steps(task):
      wf = task.metadata.get("workflow", [])
      for s in wf:
          if s["status"]=="active" and now() - s.get("started_at",now()) > STEP_TIMEOUT:
              s["status"]="failed"; s["failure_reason"]="step_timeout"
              task.status = TaskStatus.FAILED   # 或:retry if s.get("retry",0)<1
  ```

## T2. 启动时状态对账(orphan 清理)— 【Claude】
- [ ] **T2.1** 后端启动 / 任务列表查询时,对账:`running` 但其 Claude 会话已不存在 / 超过最大运行时长的任务 → 置 `failed`(orphaned),避免重启后残留"执行中"。
- [ ] **T2.2** 前端「🧹 清理」按钮:核查现状是否真能清掉 `running` 卡死项;若只清完成/失败,扩展为可清理"超时 running"(二次确认)。

## T3. 可观测 + 体验 — 【Reasonix/Claude】
- [ ] **T3.1** 任务卡显示"已运行时长 + 当前步骤 + 最近活动时间";超阈值红色高亮提示"可能卡死"。
- [ ] **T3.2** 单步「重试 / 跳过 / 终止」操作按钮(现有「取消」之外),便于人工解卡。
- [ ] **T3.3** 【Reasonix】本机验证:LLM 配置正常时任务能正常推进到完成;断开 LLM 时任务在 T1 超时后转 `failed` 而非无限 running。

## T5. 协作模式:任务改为真正的智能体协作(广场驱动,与线性流水线并存)— 【Claude 实现·待本机验证】
> 决策:广场讨论驱动 + 新增"协作模式"并存(不替换线性流水线)。LLM 走系统配置(plaza 启动已 set_chat_fn(harness.chat))。
- [~] **T5.1** `SubmitTaskRequest` 新增 `execution_mode: "linear"|"collaborative"`(默认 linear,零回归);submit_task 端点把它落入 `metadata.execution_mode`。　⟦api.py SubmitTaskRequest.execution_mode + submit_task 合并进 _meta;py_compile 通过⟧
- [~] **T5.2** 新增 `_start_task_collaboration(task, team_id)`:建广场→拉团队全员入场(add_participant)→ create_discussion(topic=任务标题, max_rounds 默认4)→ 后台 asyncio 跑 run_discussion(各 agent 多轮真实发言/主持人/共识)→ 结束后把 summary/key_conclusions 回写 task.metadata.collaboration + artifacts,并 _finalize_task_terminal_state 落终态;异常走 failed。　⟦api.py _start_task_collaboration;_submit_internal_task auto_start 分支按 execution_mode 选路;py_compile 通过⟧
- [ ] **T5.3** 【Reasonix 本机】起后端,用 `execution_mode:"collaborative"` 提交一个任务,确认:广场讨论真实产生多轮发言(走配置模型)、任务最终 completed 且 metadata.collaboration 带 summary/结论;对比 linear 模式仍正常。
- [ ] **T5.4** 批量/队列路径(`_real_task_executor`)暂仍走线性;协作模式批量化(可选增强)留后续。
- [ ] **T5.5** 前端:任务创建表单加"执行模式"选择(线性/协作);协作任务详情展示讨论 discussion_id + 共识结论(可链接到 plaza 页)。

## T4. 根因联动(与 LLM 配置)— 【Claude 改代码 + Reasonix 本机验】
- [~] **T4.1** 【Claude 已修根因·待本机验证】任务执行的 LLM **不再写死本地 Claude CLI / `~/.claude/settings.json`**,改为优先读"模型与连接页"配置的 provider(model_pool 经 ChatHarness)。　⟦api.py 新增 `_harness_provider_credentials()`(读 `get_chat_harness().get_provider_config()`:api_key/resolve_base_url/model/provider);`_get_deepseek_credentials()` 改为①优先 harness 配置 ②回退 `~/.claude/settings.json`+RTK;`_should_use_direct_api()` 增加"配置 provider 非 anthropic→直连(绕开本地 CLI)"。py_compile 通过。本机验证:在"模型与连接页"配 codebuddy/deepseek-v4-pro → 起任务,确认会话走配置模型、不再因本地 claude 不可达而无限 running⟧
- [ ] **T4.2** 若 harness 未配置任何 provider(api_key 为空),仍会回退老路径(本地 CLI);本机确认线上确有配置后,可考虑无配置时直接 fail-fast 标 `failed(no_llm_configured)` 而非起本地 CLI 空等。
