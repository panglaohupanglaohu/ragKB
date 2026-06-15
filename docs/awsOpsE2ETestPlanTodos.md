# AWS 运维团队端到端测试规划与 TODOS（v1.0）

> 日期：2026-06-15  
> 目标：验证“团队配置 → 议事厅计划 → 任务执行/技能萃取 → 数字孪生演练 → 系统演进 → 成本治理”的完整产品闭环。  
> LLM 目标配置：以模型池中截图所示 `codebuddy / deepseek-v4-pro / deepseek / max_tokens=4096 / temperature=0.7 / 默认` 为准。自动化脚本会优先查找该配置并用 `/api/v1/agent-config/llm/test-model` 或 `/llm/test` 做真实调用。

---

## 2026-06-15 自动化执行标注

- [x] 已编写自动化脚本：`scripts/aws_ops_e2e_test.py`
- [x] 已执行语法校验：`rtk python3 -m py_compile scripts/aws_ops_e2e_test.py`
- [x] 已执行单队结构复测：PASS=7 / FAIL=4 / SKIP=1
- [x] 已输出报告：`docs/reports/aws-ops-e2e-report.md`、`docs/reports/aws-ops-e2e-report.json`
- [x] 已覆盖并通过：认证、AWS 运维团队创建、6 成员创建、初始工具/技能绑定、AWS trial 演练(6类故障注入)、系统演进 Loop、成本治理。
- [x] 已修正团队策略：复用单支 `AWS 运维团队`，幂等维护 6 个成员。
- [x] 已给 AWS E2E Demo 团队添加 LLM 模型（codebuddy/deepseek-v4-pro, 从 Build System 复制）
- [ ] **待修复**：DeepSeek API key 无效 (`Authentication Fails, api key: ****TAzS is invalid`)。需在 Build System 团队 → 模型 → codebuddy → 填入有效 key，然后重跑 E2E 脚本。此 key 失效导致 Plaza plan 为空、派发无任务、技能候选不足（均 LLM 依赖）。

---

## 自动化入口

- 脚本：`scripts/aws_ops_e2e_test.py`
- 默认后端：`http://127.0.0.1:8080`
- 运行：

```bash
rtk python3 scripts/aws_ops_e2e_test.py \
  --base-url http://127.0.0.1:8080 \
  --report-md docs/reports/aws-ops-e2e-report.md \
  --report-json docs/reports/aws-ops-e2e-report.json
```

---

## T0 测试环境与 LLM 前置检查

- [ ] **T0-1** 注册一次性测试用户并获取 cookie + CSRF。
  - Case：`POST /api/v1/auth/register` 后 `GET /api/v1/auth/me` 返回 `authenticated=true`。
  - 失败判定：401/403、CSRF 为空且写接口失败。
  - 伪代码：
    ```python
    session.post('/api/v1/auth/register', {username, password})
    csrf = session.get('/api/v1/auth/csrf-token').csrf_token
    assert session.get('/api/v1/auth/me').authenticated is True
    ```

- [ ] **T0-2** 校验 CodeBuddy/DeepSeek LLM 配置。
  - Case：遍历所有团队模型池，找到 `name=deepseek-v4-pro`、`provider=deepseek`、`max_tokens=4096`、`temperature=0.7`、`is_default=true` 或模型名/ID 含 `codebuddy` 的配置。
  - Case：调用 `/api/v1/agent-config/llm/test-model`；如找不到团队模型，退化到 `/api/v1/agent-config/llm/test`。
  - 失败判定：找不到配置、无 API key、LLM test 返回 `success=false`、响应超时。
  - 伪代码：
    ```python
    for team in list_teams():
        for model in list_models(team.id):
            if matches_codebuddy(model):
                result = post('/llm/test-model', model_id=model.model_id, ...)
                assert result.success
    ```

## T1 创建 AWS 运维团队与成员

- [ ] **T1-1** 创建或复用唯一 AWS 运维团队。
  - Case：团队名固定为 `AWS 运维团队`，`run_id` 只用于讨论、任务、报告和萃取标题，不用于团队名。
  - Case：自动化启动时清理历史 `AWS 运维团队 aws_ops_e2e_*` 遗留团队，避免 UI 中出现多个测试团队。
  - 验收：`GET /teams/{team_id}` 返回团队，`agent_count >= 6` 在 T1-2 后成立。

- [ ] **T1-2** 创建 6 个成员。
  - 成员：
    - 运维 Leader：协调、任务派发、风险升级。
    - 上云架构师：ES/AWS 资源规划、容量评估。
    - 运维操作员：Terraform/脚本执行、资源创建。
    - 巡检监控员：监控、告警、故障处理。
    - 成本优化成员：账单、RI/Savings Plan、成本治理。
    - 北美 AI 项目运维员：北美 AWS AI 项目部署与合规约束。
  - 失败判定：成员缺失、角色描述为空、模型/权限更新失败。
  - 伪代码：
    ```python
    team = find_team_by_name('AWS 运维团队') or migrate_team('AWS 运维团队 E2E Demo') or create_team(...)
    for role in aws_ops_roles:
        agent = find_agent_by_name(team.id, role.name) or post(f'/teams/{team_id}/agents', role_payload)
        put(f'/teams/{team_id}/agents/{agent.id}', role_payload)
        put(f'/teams/{team_id}/agents/{agent.id}/personality', ...)
    ```

- [ ] **T1-3** 赋予初始工具与技能。
  - Case：从全局工具/技能池匹配 `aws / terraform / shell / kubectl / monitor / cost / review / test` 等关键词；技能引用优先使用 `slug/name`，避免搜索结果中的临时 `skill_id` 与团队注册表不一致。
  - 验收：工具/技能 enable 调用返回 200；`GET /teams/{team_id}/skills` 能看到实际团队技能；每个 agent 至少有一组工具或技能；成本优化成员包含成本相关工具/技能；北美运维员包含合规/区域相关描述。
  - 失败判定：工具池或技能池完全没有可匹配项。

## T2 议事厅讨论 ElasticSearch 伸缩并形成计划

- [ ] **T2-1** 创建议事厅并让 AWS 运维团队入座。
  - Case：`POST /plaza` 带 `selected_agents`，Leader 为 chairperson。
  - 验收：广场详情中参与者数量 `>= 6`。

- [ ] **T2-2** 创建讨论：`ElasticSearch 实例资源缩放`。
  - Case：目标包括容量评估、变更窗口、Terraform/脚本、监控告警、成本、北美合规。
  - 验收：讨论状态可查询，topic/goal 保存。

- [ ] **T2-3** 使用 LLM 启动讨论并生成执行计划。
  - Case：`POST /plaza/{plaza_id}/discussions/{disc_id}/start`。
  - 验收：discussion 有 `summary`、`key_conclusions` 或 `plan.content`。
  - 失败判定：LLM 调用失败、plan 为空、超时。

- [ ] **T2-4** 分支 A：将计划派发给 Build System 团队编写整体运维脚本。
  - Case：`POST /dispatch`，`team_id=build_system`。
  - 验收：创建至少 1 个任务，任务 metadata 包含 plaza/discussion trace。

- [ ] **T2-5** 分支 B：记录技能萃取输出并进入技能萃取页链路。
  - Case：`POST /outputs`，`output_type=skill_candidate`。
  - 验收：discussion outputs 包含 skill_candidate。

## T3 技能萃取、补全、演化、验证、注入

- [ ] **T3-1** 从讨论计划启动技能萃取。
  - Case：`POST /teams/{aws_team}/skill-extract/start`，source_text 使用讨论摘要/计划。
  - 验收：LLM 预填在超时时间内结束，至少 3 个 `ready_for_review` 候选。

- [ ] **T3-2** 选取 3 个技能进行补全/批准。
  - Case：分别以 `public`、`trait`、`reserve` 批准；trait 指向北美 AI 项目运维员。
  - 验收：公共技能进入团队公共技能，特质技能只绑定目标成员，备用技能进入库但不强制绑定 agent。

- [ ] **T3-3** 技能验证、发布门禁与发布。
  - Case：对 public skill 调 `/skill-library/verify`、`/publish-gate`、`/publish`。
  - 验收：返回 Evidence/验证结果；门禁阻断时必须有可读原因。

- [ ] **T3-4** 技能演化。
  - Case：对其中一个技能调用 `/skill-library/evolve`；若生成改进建议，调用 `/apply-evolution`。
  - 验收：产生演化结果或明确失败原因。

## T4 数字孪生工作坊：模拟运维脚本编写过程

- [ ] **T4-1** 用 Build System 创建脚本编写沙箱 session。
  - Case：`POST /api/v1/sandbox/sessions`，`team_id=build_system`、`mode=what_if`、`use_llm=true`、`initial_skill_id` 指向代码 review/重构类技能。
  - 验收：session 创建成功，至少可单步执行 2 步。

- [ ] **T4-2** 注入新技能改善协作。
  - Case：`POST /sessions/{sid}/inject`，`type=skill_inject`，再注入 `task_change` 或 `network_delay`。
  - 验收：返回 injected/chaos 记录；后续 step 不崩。

- [ ] **T4-3** 自动运行/暂停/单步覆盖。
  - Case：pause → step → run → get session。
  - 验收：`total_steps_executed > 0`，步骤里有 `agent_actions/messages_count`。

## T5 数字孪生演练场：AWS 运维团队执行 ES 伸缩演练

- [ ] **T5-1** 创建 trial。
  - Case：`POST /api/v1/twin-trials`，`team_id=aws_team`，目标为 ES 实例资源缩放。
  - 验收：返回 `trial_id/branch_id/session_id`。

- [ ] **T5-2** 单步、自动、故障注入全覆盖。
  - Case：对 session 单步；对 branch 注入 6 类事件：`network_delay`、`agent_leave`、`task_change`、`skill_degraded`、`model_hallucination`、`logic_deadlock`。
  - 验收：每类事件返回 `injected=true`。

- [ ] **T5-3** 评分、技能统计、SOP、反哺。
  - Case：`/skill-stats`、`/evaluate`、`/extract-sop`、`/feedback`。
  - 验收：评分对象存在；SOP 结果有候选或明确“不达阈值”；反馈不报 500。

## T6 系统演进 Loop

- [ ] **T6-1** 从讨论计划进入系统演进。
  - Case：`POST /plaza/{plaza_id}/discussions/{disc_id}/evolve`。
  - 验收：创建 evolution items；trace context 能回到 plaza/discussion/task。

- [ ] **T6-2** 驱动演进 Loop。
  - Case：`POST /agent-teams/evolution/audit`、`/cycle`、`/verify`、`GET /items`。
  - 验收：summary/items/history 可读；失败项有原因和 request/evidence 信息。

## T7 成本分析与治理目标

- [ ] **T7-1** 汇总团队/服务成本与 token 可持续性。
  - Case：`GET /cost/summary`、`/cost/by-team`、`/sustainability/group`。
  - 验收：能识别 token 或成本最重团队/服务；没有数据时给出清晰 empty/degraded 状态。

- [ ] **T7-2** 生成治理目标。
  - Case：针对 ES 扩容 Terraform plan 调 `/cost-gate/evaluate`，metadata 带 aws team、plaza/discussion、trial。
  - 验收：返回 pass/warn/block；阻断时列出违规资源和建议。

## T8 报告与改进 TODO

- [ ] **T8-1** 输出 Markdown 和 JSON 测试报告。
  - 报告包含：run id、LLM 配置、每步 PASS/FAIL/SKIP、关键对象 ID、失败原因、建议。

- [ ] **T8-2** 生成改进 TODO。
  - 失败样例：
    - LLM 配置不可用 → 补模型连接/密钥/默认模型验证。
    - 讨论无计划 → Plaza 计划生成兜底。
    - 技能候选不足 3 个 → 萃取 prompt 或候选拆分策略优化。
    - 数字孪生按钮/API 不一致 → 前端按钮状态机补回归。
    - 成本数据为空 → 注入测试成本样本或增加 dry-run 成本数据源。
