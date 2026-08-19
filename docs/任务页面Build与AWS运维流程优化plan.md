<!-- docs-signoff: author="GitHub Copilot" kind="llm" doc="plan" ts="2026-08-04T08:45:00Z" -->

# 任务页面 Build System 与 AWS 运维流程优化计划

## 1. 审计结论

本次检查覆盖了任务中心 `src/frontend/tasks.html`、团队配置页任务视图 `src/frontend/js/tasks-view.js`、任务 API/TaskEngine、Build System 团队、AWS 运维团队及现有测试。

当前“构建任务和运维任务流程跑不完整”不是单一 LLM 问题，而是三类契约没有统一：

1. **角色到工作流的契约断裂**：AWS 团队角色使用中文角色名（如“运维操作员”“巡检监控员”），而 `_ROLE_WORKFLOW_MAP` 只识别 `devops`、`qa_engineer` 等规范 role。AWS 任务因此常退化为无可执行 agent 的单步 `execute`，后续监控只能跳过或标失败。
2. **提交路径的契约断裂**：页面提交 `execution_mode`，但 `SubmitTaskRequest` 没有该字段；协作模式从 UI 到 API 被丢弃。单任务 REST、批量提交、手动启动又分别走不同的预检、工作流初始化和启动逻辑。
3. **状态与展示契约断裂**：任务启动先变为 `running`，工作流启动失败时没有原子回滚；独立 `tasks.html` 对 `/teams` 的分页 envelope 仍按数组处理，可能直接失去团队和任务列表。任务页现有测试只覆盖 `tasks-view.js`，没有覆盖独立任务中心和 Build/AWS 端到端闭环。

## 2. 目标状态

同一任务无论来自任务中心、团队配置页、单条提交、批量提交、议事计划派发或物竞回生产，都遵循统一状态机：

`draft -> queued -> running -> blocked/retrying -> completed | failed | cancelled`

每个 workflow step 必须具备：

- 可解析的 `agent_id` 和规范化 `agent_role`；
- 明确的输入、产物、验收条件、失败原因和重试次数；
- session/monitor 状态与任务状态一致；
- 下一步只能在当前步验收通过且协作拓扑门禁通过后激活；
- 最终任务必须有结果摘要、artifact/evidence、token 归因和可追溯 handoff。

## 3. 优化范围与顺序

### P0：先让两类任务完整、可收敛

**P0-A 统一角色身份**

- 保留每个 Agent 的展示名称，但增加稳定的规范 role 或 `workflow_role`：
  - Build System：`project_manager`、`researcher`、`architect`、`developer`、`qa_engineer`、`devops`、`documentation`。
  - AWS Ops：`operations_lead`、`cloud_architect`、`operations_operator`、`monitoring`、`cost_optimizer`、`regional_compliance`。
- 将 workflow 模板从“只按 team_id 特判”改为 team/role 配置，明确 AWS 的容量评估、脚本、dry-run、监控、成本、合规与回滚步骤。
- 生成 workflow 时若步骤没有 `agent_id`，禁止启动；返回结构化 `workflow_agent_unresolved`，不要让空 agent 任务进入 `running`。

**P0-B 收敛提交/启动入口**

- `SubmitTaskRequest` 正式接收并校验 `execution_mode`，允许值为 `linear`、`collaborative`。
- 抽取一个共享的“构建任务上下文”函数，供单任务、批量任务、内部派发使用：预算预检、LLM 可用性检查、locked bid 注入、workflow 初始化、pipeline context、handoff 初始化。
- 抽取一个共享的“启动事务”函数：先确认 workflow/agent/session 可以创建，再提交 `running`；启动失败回滚为 `pending` 或结构化 `failed`，不保留假 `running`。
- 批量任务必须校验依赖 ID、检测循环依赖，并返回每条任务的 queued/blocked/error 原因；不得静默接受无法推进的 DAG。

**P0-C 修复两个任务页面的数据协议**

- `tasks.html` 的团队和任务读取统一使用共享 API client，兼容数组与 `{items,total,limit,offset,has_more}` envelope。
- 列表按团队分批请求改为分页聚合，显示加载失败、部分团队失败、最后一次成功时间和重试入口。
- 统一 `task_id/team_id` URL 编码、CSRF、401 重登录提示和动作后局部刷新。

### P1：补齐 Build/AWS 的业务流程验收

**Build System 完整链路**

`PM 分解 -> 研究 -> 架构 -> 开发 -> 测试 -> 部署 -> 文档`

每一步必须产生 handoff/artifact；测试失败阻止部署；部署必须有 dry-run、审批、回滚信息；最后由文档步骤写入变更摘要。

**AWS Ops 完整链路**

`容量与风险基线 -> Terraform/aws-cli 脚本 -> dry-run -> review/审批 -> 单步 apply -> CloudWatch/集群健康验收 -> 成本与区域合规 -> 回滚演练/关闭任务`

AWS 任务默认禁止把“生成脚本”直接等同于“变更完成”。真实变更步骤需要显式 approval gate 和验收证据；无 AWS 凭据时应进入可见的 `blocked`，而不是伪完成或无限运行。

**协作模式完整链路**

- 页面选择 `collaborative` 后，创建 Plaza discussion，完成共识/计划回写，再把结构化计划派发到任务 DAG。
- 讨论阶段不做 token 预算压制；进入执行计划后才接入 token 预算、ModelRouter、EvidenceRun。
- 页面要显示 `execution_mode`、discussion/plan/task 关联、当前阶段和失败回流入口。

### P2：可观测性与体验

- 任务详情显示 step 时间线、当前 agent、session、最后活动、重试次数、阻塞原因、artifact 和 EvidenceRun。
- 对 `running` 任务提供心跳/租约、墙钟超时、孤儿任务对账和“重试当前步骤/跳过/终止”的审计记录。
- 统计统一按 task、team、execution_mode、step、provider 归因，避免全局 KPI 与当前团队混淆。
- 增加 Build System 与 AWS Ops 的固定示例任务和一键验收入口，避免只能靠人工点页面。

## 4. 验收标准

- Build System 线性任务从提交到文档完成，所有 workflow step 有 agent、session、artifact、handoff，任务最终 `completed`。
- AWS Ops 任务能完成基线、脚本、dry-run、审批、验收、成本/合规和回滚分支；缺凭据时稳定进入可解释阻塞态。
- `execution_mode=collaborative` 在 API 返回并持久化，Plaza 计划能生成并关联下游任务。
- 任一 session 创建失败不会留下无 session 的 `running` 任务；任务能在超时/孤儿对账后收敛。
- 任务中心和团队配置页在数组及分页 envelope 下均能列出 Build/AWS 任务。
- 离线单测、前端测试、语法检查和有后端的最小 E2E 均有可重复命令与结果记录。

## 5. 非本次范围

不改全局 LLM 配置铁律、不改 Plaza 讨论阶段的 token 规则、不把 AWS 真实云变更接入测试环境、不重构数字孪生页面视觉层。先修任务契约和验收闭环，再扩展业务动作。
