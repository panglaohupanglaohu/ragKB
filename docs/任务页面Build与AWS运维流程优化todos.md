<!-- docs-signoff: author="GitHub Copilot" kind="llm" doc="todos" ts="2026-08-04T08:45:00Z" -->

# 任务页面 Build System 与 AWS 运维流程优化 Todos

## P0 根因修复

- [ ] **T0.1 角色规范化**：在 `build_team.py` 与 `aws_ops_team.py` 为每个 Agent 增加稳定 `workflow_role`，保留中文展示 role；补映射兼容历史存量数据。验收：两队所有 workflow step 都能解析真实 `agent_id`。
- [ ] **T0.2 工作流模板分域**：将 `api.py` 的 `_ROLE_WORKFLOW_MAP` 与 `_generate_workflow` 改为 Build/AWS 配置驱动；AWS 至少覆盖 baseline、script、dry-run/review、apply、monitor、cost/compliance、rollback。验收：同一任务快照包含正确步骤和顺序。
- [ ] **T0.3 空 Agent 硬门禁**：workflow 生成或启动前检查每个必需步骤的 agent；缺失时返回 `workflow_agent_unresolved` 并保持 `pending/blocked`，记录原因。验收：不能出现“无 agent 但 running”。
- [ ] **T0.4 接通执行模式**：给 `SubmitTaskRequest` 增加 `execution_mode: Literal['linear','collaborative']`，持久化到 metadata/顶层兼容字段；为 collaborative 接回 Plaza 讨论与计划派发。验收：页面选择协作模式后 API/TaskStore/详情均保留该值。
- [ ] **T0.5 统一单条与批量预检**：抽取共享函数，统一 token budget、provider、locked bid、依赖校验、workflow 初始化和 handoff。验收：单条/批量对同一无 LLM 场景返回一致状态和错误结构。
- [ ] **T0.6 启动事务化**：修复 `start_task_endpoint` 先置 `running` 后启动失败不回滚的问题；session 创建成功后再提交 running，失败回 pending/blocked。验收：模拟 `_real_task_executor` 异常，任务不残留假 running。
- [ ] **T0.7 批量 DAG 校验**：提交前校验依赖存在性、跨团队依赖策略和循环依赖；依赖未完成任务保持 queued/blocked，失败依赖给出可解释原因。验收：覆盖缺依赖、环、先后完成、并行任务四个用例。
- [ ] **T0.8 修独立任务中心**：修改 `src/frontend/tasks.html`，使用共享 `api.js/_agFetch`，兼容 teams/tasks 的分页 envelope；处理部分团队请求失败和 401。验收：Build System、AWS Ops 均能显示，分页与刷新不丢数据。

## P1 业务闭环

- [ ] **T1.1 Build System 端到端夹具**：建立固定任务“功能构建交付”，验证 PM→研究→架构→开发→测试→部署→文档；每步生成最小 artifact/handoff。验收：最终 EvidenceRun passed，部署前测试失败可阻断。
- [ ] **T1.2 AWS Ops 端到端夹具**：建立固定任务“ES 扩缩容安全变更”，使用 mock AWS 工具验证基线、脚本、dry-run、审批、apply、健康检查、成本/合规、rollback。验收：成功和 rollback 两条分支均收敛。
- [ ] **T1.3 AWS 凭据阻塞态**：无 AWS 凭据或工具不可用时进入 `blocked`，显示 provider/tool/error，不启动无限重试。验收：任务可人工修复后 retry，且有审计事件。
- [ ] **T1.4 Step 验收门**：定义每类 step 的 output schema 和 pass predicate；未产出脚本、测试清单、监控验证或合规结论时禁止自动推进。验收：伪造空 session 输出不会推进下一步。
- [ ] **T1.5 失败回流**：失败步骤保存 error、attempt、last session、artifact；支持重试当前步、跳过（需确认）和终止；自动重试不超过配置上限。验收：重试后 step/session/任务状态一致。
- [ ] **T1.6 协作计划派发**：验证 collaborative discussion→consensus/plan→DAG→执行的关联字段，且讨论阶段不计入 task token budget。验收：页面可以从任务跳回 discussion/plan，并看到下游任务。

## P2 页面与观测

- [ ] **T2.1 统一任务详情**：任务中心与团队配置页共享状态字典、workflow renderer、错误提示和动作权限；删除/取消/重跑均使用统一 client。
- [ ] **T2.2 运行心跳与孤儿对账**：补 task lease/last_activity，服务启动时对无 monitor/无活 session 的 running 任务对账；超时进入 failed/blocked 并保留 evidence。
- [ ] **T2.3 任务统计口径**：stats 增加 team_id、execution_mode、workflow step、provider 维度；页面不要用全局 running 数冒充当前团队状态。
- [ ] **T2.4 任务可观测面板**：显示当前 step、agent、session、耗时、最后活动、重试、阻塞原因、artifact、EvidenceRun 链接。
- [ ] **T2.5 测试环境固化**：在项目启动/CI 中检查 `.venv` 的 pytest；增加最小命令 `pytest -q src/backend/tests/test_task_workflow_build_aws.py` 与前端任务页契约测试。pytest 缺失时 CI 明确失败，不报告假绿。

## 验收命令

- [ ] `npm run test:frontend -- src/frontend/__tests__/tasks-pagination.test.js` 通过，并新增 tasks.html envelope/401 测试。
- [ ] `node --check src/frontend/js/tasks-view.js` 及独立页面脚本检查通过。
- [ ] `npm run test:backend -- src/backend/tests/test_task_engine.py src/backend/tests/test_request_models.py src/backend/tests/test_aws_ops_costdown.py` 通过。
- [ ] 新增 Build/AWS workflow 测试通过：成功、工具不可用、空 agent、依赖失败、重试、取消、回滚至少各一例。
- [ ] 有后端环境运行一次认证后的 API E2E：提交→查询→启动→step 推进→完成/失败→EvidenceRun。
- [ ] 浏览器验收任务中心和团队配置页：Build System、AWS Ops、线性、协作、批量、失败回滚、刷新/分页。

## 交付记录

- [ ] 每个 P0/P1 项记录实际变更文件、测试命令、结果和未覆盖风险。
- [ ] 后端代码落盘后记录需要的 reload/restart 时间；不把旧进程缓存误判为新代码行为。
- [ ] 完成后同步 `.wolf/anatomy.md`、`.wolf/memory.md`、`.wolf/cerebrum.md` 与 `.wolf/buglog.json`。
