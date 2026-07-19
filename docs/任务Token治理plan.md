<!-- docs-signoff: author="Grok" kind="llm" doc="plan" ts="2026-07-15T12:45:00Z" -->
# 任务 Token 治理 — 统一工作台设计（v2.4 R10 一行管线 + 参数旋钮）

> 状态：current · **v2.4 完成**  
> v2.3：算法入 prepare 真省。  
> **v2.4**：长文迁 README；杠杆 UI = 一行（接线·启用·试跑·旋钮）；`lever_params` 可调并真进 prepare；预算 `alert_threshold` 等可旋。  
> 权威：`lever_catalog.py` + `lever_params.py`；文档主文：根 `README.md#任务-token-治理`。

---

## 0. 设计读

浅色 B2B FinOps 控制台 · Linear 冷静密度 · 冷灰白 + 森林绿单 accent（Taste Skill）。  
**治理对象** = 任务执行 LLM token（Plaza 讨论阶段 **不** 优化）。

**页面布局（强制）：** KPI → **行为动作（杠杆卡 + 预算）** → 报表（任务账单 / 节省 / prepare 流水）。

---

## 1. 架构（前后端一体）

```
┌─ cost-dashboard 任务 Token 工作台 ─────────────────────┐
│  KPI · 【行为】杠杆卡(catalog) · 预算 · 【报表】账单   │
└───────────────────────┬───────────────────────────────┘
                        │ GET  /cost/token-governance/levers   ← catalog+runtime+architecture
                        │ GET  /cost/token-governance/dashboard
                        │ POST /cost/token-governance/simulate  ← 本轮 prepare.levers[]
                        │ POST /cost/token-governance/levers    ← 写 settings
          ┌─────────────▼─────────────┐
          │ TokenGovernanceService     │
          │ prepare_request (唯一入口) │
          │ ① simplify_prompt          │
          │ ② compress                 │
          │ ③ cache (exact+semantic-lite) │
          │ ④ skill route + shorten    │
          │ ⑤ model route              │
          │ ⑥ budget check             │
          │ → savings JSONL + counters │
          └─┬──────┬──────┬──────┬────┘
            ▼      ▼      ▼      ▼
     TokenLedger  PromptCache ModelRouter SkillRouter BudgetGuard
     usage.db     LRU进程内   三档       route()     session/agent/team

执行强制接线（生产路径，非演示）：
  chat_harness.chat  ──► prepare_request ──► LLM
  tool_loop 每轮     ──► prepare_request ──► LLM
```

**原则：**

1. UI **不发明**杠杆文案；只渲染 `GET /levers.catalog[]`。  
2. 试跑只调用 `POST /simulate` → 同一 `prepare_request`。  
3. 每条 `prepare.levers[]` 带 `catalog_id` / `module` / `before|after|saved`，供表与卡片「试跑效果」回写。

---

## 2. 业界调研 → 本仓选型（杠杆对照表）

调研范围：Portkey（缓存/路由/预算）、Helicone（可观测+缓存思想）、LiteLLM（cascade 路由）、
BCG 2026 agent cost（传目标不传全日志）、GPTCache（语义缓存思想）、OpenAI/Anthropic prompt cache（稳定 prefix）、
本仓既有 `SKILL_ROUTING_MISS` / BudgetGuard / TokenLedger。

| # | 杠杆 | 业界借鉴 | 本仓模块 | 方法（算法） | 接线点 |
| --- | --- | --- | --- | --- | --- |
| ① | **提示词简化** | BCG 2026「传目标不传全日志」；Helicone prompt 去冗；稳定 prefix 以利缓存 | `token_governance/prompt_simplify.py` · `simplify_messages` | 空白折叠；短套话行去重（你是/You are/请务必…）；**零 LLM** | prepare ① |
| ② | **内容压缩** | BCG agent flow；Claude/GPT tool-result compaction；**拒绝** LLM 摘要（防递归烧 token） | `prompt_cache.compress_messages` | 相邻同内容去重；长 tool 头尾折叠；硬截断 system≤6k / 其它≤4k | prepare ② |
| ③ | **上下文缓存** | **Portkey** exact+semantic；**Helicone** gateway cache；GPTCache；OpenAI/Anthropic prompt cache | `prompt_cache.PromptCache` + `semantic_lite_fingerprint` | Exact SHA-256；Semantic-lite 剥 UUID/时间/hex 再哈希；进程 LRU 256；`observe\|serve\|off` | prepare ③ |
| ④ | **Skill 路由** | 本仓 `SKILL_ROUTING_MISS`；Agent skill 复用；「有 playbook 勿 raw 长生成」 | `skill_router.route`→`RoutingSession`；`_apply_skill_shorten` | 解析 `.results[].skill_id`；pool 空则团队 skills 关键词回退；system 截到 3500 + 注入 `[TG_SKILL_BODY]` | prepare ④ |
| ⑤ | **模型路由** | **LiteLLM** cascade；OpenRouter/Not Diamond；Portkey routing | `runtime/model_router.ModelRouter` | economy/standard/frontier 三档；预算紧降档；失败升档；粘滞防抖 | prepare ⑤ |
| ⑥ | **预算门禁** | Portkey budgets；企业 FinOps token policy（Airia/BCG）；本仓 BudgetGuard | `budget/guard.BudgetGuard` | session/agent/team 日限额；warn@0.8；halt；submit **HTTP 402** | prepare ⑥ + submit 预检 |

**明确不做：** 外部 Portkey/Helicone 托管网关；Redis/向量语义缓存一期；Plaza token 优化；LLM 做摘要压缩。

---

## 3. 每个杠杆：实现细节（与 catalog / UI 一致）

### 3.1 提示词简化 `simplify_prompt`

| 项 | 内容 |
| --- | --- |
| 借鉴 | BCG 上下文工程；Helicone 去冗 prompt |
| 文件 | `src/backend/agents/token_governance/prompt_simplify.py` |
| 入口 | `simplify_messages(messages) → {messages, saved_tokens_est}` |
| 算法 | normalize 空白 → 短套话行去重 → 零 LLM |
| 开关 | `settings.token_governance.simplify_prompt` |
| 可观测 | counters.simplify_saves；lever `{kind:simplify, before, after, saved, module}` |

### 3.2 内容压缩 `compress`

| 项 | 内容 |
| --- | --- |
| 借鉴 | tool-result compaction；BCG share workspace |
| 文件 | `src/backend/agents/prompt_cache.py` |
| 入口 | `compress_messages()` |
| 算法 | `dedupe_adjacent` / `fold_long_*` / `truncate_*` |
| 开关 | `compress`；关后 prepare **不出现** kind=compress（R7.5） |
| 可观测 | compress_saves；`actions` 字典 |

### 3.3 缓存 `cache_mode`

| 值 | 行为 |
| --- | --- |
| `observe`（默认） | 查 LRU，HIT 只记统计，**仍调用 LLM**（安全） |
| `serve` | HIT 时可短路（高风险，显式开） |
| `off` | 不查不写 |

Semantic-lite：去动态字段后指纹，逼近 Portkey semantic 的「近重复」而不引 embedding。  
试跑：「连跑 2 次测缓存 HIT」第二次应 kind=cache hit=true。

### 3.4 Skill 路由 `skill_route_hint`

1. `SkillRouter.route(query, team_id)` → **RoutingSession**（**不是 dict**）  
2. 取 `results[].skill_id`  
3. 空池 → 团队 `skills` 关键词交集回退  
4. `_apply_skill_shorten`：截 system + 注入精简 instructions  
5. **saved 只认真实 before/after**，禁止虚增  

### 3.5 模型路由 `model_route`

- 默认档：flash / pro / glm-5.1（`ModelRouter._default_tiers`）  
- harness：无 `model_override` 时用 prepare 返回的 model  
- tool_loop：每轮 `model_name` 来自 prepare  

### 3.6 预算 `budget_enforce_*`

- 真源：`BudgetGuard` + `config/settings.json` budget 段  
- 工作台表单 → `POST /token-governance/budget`  
- 任务提交 → 402 + workbench 深链  
- prepare 末尾始终产出 budget lever（allowed/blocked）便于 UI 可见  

---

## 4. 数据与 API

| API | 用途 |
| --- | --- |
| `GET .../levers` | **catalog + settings + runtime + architecture + pipeline** |
| `POST .../levers` | 写 `token_governance` 开关 |
| `POST .../simulate` | 样例消息跑 prepare，返回每杠杆本轮效果 |
| `GET .../dashboard` | KPI + by_task + savings |
| `GET .../savings` | JSONL 节省按 task 查 |
| `POST .../budget` | 限额 |

Settings 键：`config/settings.json` → `token_governance.{simplify_prompt,compress,cache_mode,model_route,skill_route_hint,budget_enforce_*}`

节省落盘：`storage/token_governance/savings_events.jsonl`  
可观测 usage 行：`phase=tg_prepare`, `total_tokens=0`, `model=tg_prepare_save:{n}`

### 4.1 catalog 字段契约（UI 硬依赖）

```
catalog[i] = {
  id, order, title, title_en, settings_key, kind, default,
  industry: { lane, inspired_by[], what_they_do },
  ours: { module, entry, called_from, algorithm[], metric_keys[], effect_field, safety? },
  exec_path[], enabled, value, runtime{}
}
architecture = {
  entry, order, wired_into[], settings_file, savings_log
}
prepare.levers[j] = {
  kind, catalog_id, module, before?, after?, saved|saved_est?, ...kind-specific
}
```

---

## 5. 前端（杠杆区必须展示的信息）

实现：`src/frontend/js/token-workbench.js` · `renderLevers`  
样式：`cost-dashboard.html` 内联 `.tg-lever-*`

每张杠杆卡（数据 **仅** 来自 catalog）：

1. 序号 + 标题 + 英文名 + ON/OFF（或 cache 模式枚举）  
2. 车道 `industry.lane`  
3. **业界做什么** `what_they_do`  
4. **借鉴技术（调研）** 全量 `inspired_by[]` 列表  
5. **本仓模块 / 入口 / 调用点 / 效果字段**  
6. **算法步骤** 全量 `algorithm[]`  
7. **执行路径** `exec_path[]`  
8. 安全注记（如 cache observe 默认）  
9. **运行时指标** `runtime`  
10. **试跑效果** 回写 `prepare.levers[]` 命中行  

试跑表列：`kind | module | before→after | saved | 细节`  
辅助按钮：试跑全杠杆 · 连跑 2 次测 HIT · **关 compress 再试跑**

---

## 6. 成功标准（杠杆专项）

| # | 标准 | 验证 |
| --- | --- | --- |
| 1 | 打开工作台无需猜：每张卡写清 **借鉴谁 / 哪个文件 / 什么算法** | UI 硬刷 cost-dashboard |
| 2 | 点「试跑 prepare」：表出现可触发行，**before > after 或 cache HIT** | simulate + UI |
| 3 | `GET /levers` catalog 与 `lever_catalog.py`、plan §3 一致 | pytest R7.7 |
| 4 | 关 compress 后再试跑：无 compress 行 | UI 按钮 + `test_disable_compress_no_compress_lever` |
| 5 | chat_harness / tool_loop 可 grep `prepare_request` | 源码 |

---

## 7. 分期与状态

| 期 | 内容 | 状态 |
| --- | --- | --- |
| R0–R4 | 服务、工作台、接线、验收 | ✅ |
| R5–R6 | skill 缩短、savings、RoutingSession | ✅ |
| R7 | 杠杆 catalog UI | ✅ |
| R8 | 节省计量诚实化 | ✅ |
| **R9** | **六源调研算法入 prepare（真省）** | ✅ |
| **R10** | **一行管线 UI + 可调 params 旋钮 + README 长文** | ✅ |

### 8.3 R10 UI / 参数

| 项 | 约定 |
|----|------|
| UI | 一行表：order · 名称 · 接线 · 启用 · 试跑槽 · 旋钮；禁止页面渲染 industry/algorithm 长文 |
| 长文 | 根 README「任务 Token 治理」 |
| params | `settings.token_governance.params` + budget 段；`POST /levers` 一体保存 |
| prepare | 读 params 传入 compress/rtk/progressive/skill/codegraph/cache；budget 阈值读 BudgetGuard |

配套 todos：[`任务Token治理todos.md`](任务Token治理todos.md)。

### 8.1 计量规则（R8）

| 量 | 规则 |
| --- | --- |
| `prepare.saved_tokens_est` | `max(0, before_tokens − after_tokens)` |
| 各 lever `saved`/`before`/`after` | 分步真实值 |
| KPI `counters.tokens_saved_est` | 净 `saved_tokens_est`；observe cache HIT 不计 |
| cache `serve` | 短路才计 HIT tokens |

### 8.2 R9 调研映射（算法进管线，非文案）

| 源 | License | 我们怎么做 | 入口 |
| --- | --- | --- | --- |
| [ponytail](https://skillsllm.com/skill/ponytail) | MIT skill | system 注入 YAGNI ladder（lite/full/ultra）→ 降输出与过建 | `behavior_inject` |
| [openwolf](https://github.com/cytostack/openwolf) | AGPL → **只模仿思想** | 大文件 → 符号行号表，避免整文件进上下文 | `codegraph_bridge` local |
| [rtk](https://github.com/rtk-ai/rtk) | Apache-2.0 ideas | tool 输出：滤噪声/去重/路径分组/截断 | `rtk_tool_compress` |
| [claude-mem](https://github.com/thedotmack/claude-mem) | Apache-2.0 ideas | 旧轮次 → MEM_INDEX 一行，保留近 N 轮 | `progressive_history` |
| [codegraph](https://github.com/colbymchenry/codegraph) | **MIT 真引入** | `npm i -g @colbymchenry/codegraph`；`codegraph explore` + 本地切片 | `codegraph_bridge` |
| [flowork_Router](https://github.com/flowork-os/flowork_Router) | 模仿 | cost-tier 启发式 + Caveman 简练输出 + prefer_tier | `cost_tier` + `ModelRouter` |

**生产路径（不变）：** `chat_harness.chat` / `tool_loop` 每轮 → `TokenGovernanceService.prepare_request`。

**实测（本机 simulate）：** 12.6k → 4.8k tokens，**净省 ≈7.8k**（rtk 主导 + progressive）。
