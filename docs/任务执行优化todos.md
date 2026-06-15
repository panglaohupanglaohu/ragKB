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

## T4. 根因联动(与 LLM 配置)— 【Reasonix】
- [ ] **T4.1** 确认这些卡死任务是否因 LLM 未正确配置/额度/网络导致会话起不来;若是,先修 LLM 连接(模型与连接页 codebuddy/deepseek-v4-pro),再观察是否仍卡。
