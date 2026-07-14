<!-- docs-signoff: author="Grok" kind="llm" doc="plan" ts="2026-07-14T12:36:00Z" -->
# 物竞适者反馈调整台 — 设计方案

> 状态：current · 产品接线设计（用户 2026-07-14）  
> 前提：进入 **演进式成本优化** 之前，物竞结果必须先 **反馈给智能体（Skill + 协作模式 + 关系/通道）**，由人在调整台上确认/改写后再放行。  
> **用户校准（2026-07-14）**：`metadata.eco_collab` 四维基因只是仿真表型；**真正的协作关系变化** = 团队配置页「关系」+「通道绑定」被物竞证据驱动并经人确认写回。

---

## 1. 问题

| 现状 | 问题 |
| --- | --- |
| 物竞跑完后，Skill 写回挤在右侧 `eco2-integration` 两颗小按钮里 | 不像「反馈给智能体」的工作台，易漏、不可审 |
| **协作模式**（share/signal/follow 基因）可写 `metadata.eco_collab` | 团队页「关系 / 通道绑定」**零联动**——基因写了，协作拓扑没变 |
| 成本页与物竞无门禁顺序 | 可直接去 `cost-dashboard` 谈 token，跳过适者构型落地 |
| `agent-detail` 有技能绑定，但无物竞上下文（考卷/归因/适者） | 单页改技能丢失「为何被选中」 |
| 关系只能人工建（`agent_relationships`） | 正确约束；物竞侧缺 **suggest→人确认** 桥，无法把演练协作链落地为真关系 |

**原则（用户）**：成本纪律在执行计划之后；物竞筛「谁适合干」；**写回智能体是进入成本优化的前置门**，不是成本页的附属按钮。  
**协作原则（用户 2026-07-14）**：仿真里 share/signal/follow 协作链若只停在基因元数据，**不算协作关系变化**；必须能 **建议并（经确认）写入** 关系网络与通道绑定——那才是团队页可见、通信门禁会吃到的真变化。

---

## 2. 页面落点（结论）

### 推荐：不新开独立站点，做「孪生试验田内的第三态面板」

| 方案 | 评价 |
| --- | --- |
| **A. 数字孪生页右侧全量「适者反馈台」**（推荐） | 与 3D/考卷/种群同屏；演练结束自然进入；改完再链成本页 |
| B. 新页面 `eco-feedback.html` | 多一次跳转，易丢 timeline 上下文；仅当面板过重再拆 |
| C. 只放 `agent-detail` / 团队配置 | 适合单人精修，不适合「一场演练 → 整队 diff」 |
| D. 放 `cost-dashboard` 里 | **否**——违反「先反馈智能体、再谈 token」 |

**落点 URL（不变）**

```
/Agent-digital-twin.html?office3d=1
```

演练结束后：

1. 右侧从「生境控制台（演练中）」切换或叠加 **「③ 适者反馈台」**（`#rp-eco-feedback`）  
2. 左树仍显示团队/智能体，点人可高亮反馈台中该行  
3. 顶部步骤条（试验田专用）：

```
① 生境旋钮 → ② 物竞演练 → ③ 适者反馈（Skill + 协作基因 + 关系/通道） → ④ 演进式成本优化
```

- ①② 已有（左旋钮 + 右控制台）  
- **③ 本设计**（含 §3.5 关系/通道）  
- ④ 链到 `/cost-dashboard.html?from=eco&team_id=…&fingerprint=…`，**仅当 ③ 门禁通过或用户显式跳过（记审计）**

---

## 3. 信息架构（③ 反馈台布局）

全高滚动面板，分区如下：

### 3.1 考卷与演练摘要（只读）

- 计划/任务 title、`plan_id` / `task_id`、fingerprint  
- 赛制、生境旋钮快照（A4+B8 摘要 chips）  
- KPI：最长 \(T_i\)、dominant 列表、均值 skill% / collab%  

### 3.2 Skill 反馈（写回 agent.skills）

对每个 **投放种群 × 适者（Top-K 或全队可展开）** 一行：

| 列 | 内容 |
| --- | --- |
| Agent | 名 / role / population |
| \(T_i\) | 生存 ticks |
| 当前技能 | 真身已绑定（API 拉） |
| 建议新增 | integration.recommended 勾选 chips（默认可勾 dominant∩demand、补 missing） |
| 建议弱化 | deprecated / 纯 residual 且与 demand 无关（默认不删，仅建议） |
| 归因条 | skill% / collab% / residual% 迷你条 |

操作：

- 行级：应用建议 / 清空建议 / 打开 `agent-detail`  
- 底栏：**预览写回**（confirm=false）→ **确认写回 Skill 绑定**（confirm=true，现有 `skill-integration/apply`）  

### 3.3 协作基因反馈（写回 agent.metadata.eco_collab）— 表型层

物竞 `collab_genome` 四维：`share_tendency` / `signal_tendency` / `follow_tendency` / `mate_choosiness`。

| 列 | 内容 |
| --- | --- |
| Agent | 同上 |
| 演练表达型 | 本场 timeline 统计的实际协作强度（可选） |
| 建议基因 | 适者均值或该 agent 终局 collab_genome 滑杆（0~1） |
| 写回策略 | 覆盖 / 与真身加权混合 / 仅记录不写（默认混合或仅记录，防一次演练污染人格） |

操作：

- **预览协作写回** → **确认写回协作模式**  
- 后端：`POST /api/v1/eco-runtime/collab-integration/apply`  
- 存储：`AgentProfile.metadata.eco_collab = { share, signal, follow, choosiness, source, eco_fp, updated_at }`  
- 运行时消费：物竞再跑初始基因组；**不**直接改团队页关系/通道（见 §3.5）

> 说明：本节是「倾向参数」。用户已明确：**真正的协作关系变化**在 §3.5。

### 3.5 协作关系真变化：关系网络 + 通道绑定（用户要求 · 主轴）

#### 3.5.1 为什么必须做

| 层 | 落点 | 是否「协作关系变了」 |
| --- | --- | --- |
| 基因表型 | `metadata.eco_collab` | **否**（下一场仿真用；团队页看不见） |
| **关系边** | `RelationshipStore` / 团队页「关系」 | **是**（谁能跟谁通信的门禁图） |
| **通道绑定** | `AgentProfile.channels[]` / 团队页「通道绑定」 | **是**（subscribe/publish 总线权限） |

物竞协作链（signal → follow / HELP → share）在 timeline 里已有边证据；应 **汇总为可勾选建议**，经人确认后写入上表两处。

#### 3.5.2 与现有「关系只能人工建立」的兼容

`agent_relationships.py`：**关系只能人工建立，Agent 不能自己加**。  
本设计 **不**让仿真静默建边，而是：

```
物竞 timeline + collab_genome
  → relation/channel integration suggest（suggest_only）
  → ③ 反馈台展示边/通道 diff（默认勾选高强度证据）
  → 人确认 apply（created_by="human_via_eco_feedback"，记 eco_fp）
  → 团队配置「关系」页立即可见
```

无 confirm **零写入**（与 skill/collab apply 一致）。

#### 3.5.3 证据 → 建议映射（默认规则，可阈值调）

**A. 关系边（agent_agent，默认 `rel_type=collaborator`）**

从 timeline steps 的 `actions[aid].shared_to` / `signals` / `followed` 聚合边权：

| 证据 | 建议 |
| --- | --- |
| A `shared_to` B（累计 ≥1 或权重大） | A→B 与 B→A 的 **collaborator**（或单向 + note「share 受益」） |
| A 发 FOOD，B `followed=true` 同 tick 窗口 | A→B **collaborator**，note=`eco:follow_food` |
| 同 population 且双方高 share+signal 且同场存活 Top | 建议互为 collaborator（弱证据，默认不勾或低优先级） |
| `mate_choosiness` / COURT | **不**映射为业务协作边（繁衍非通信关系）；可选 note 仅出现在报告，不写 RelationshipStore |

去重：已存在同 source/target/kind 边 → 建议标 `already_exists`，不重复建。

**B. 通道绑定（`AgentChannelConfig`）**

| 证据 / 基因 | 建议通道动作 |
| --- | --- |
| 高 `signal_tendency` 或 timeline 多次 FOOD/HELP | 对队总线（如 `{team_id}_bus` 或既有主通道）**publish=true**（保留 subscribe） |
| 高 `follow_tendency` 或多次 followed | 对队总线 **subscribe=true** |
| 高 `share_tendency` 且发生过 share | 可对「help/collab」类通道提高 priority 或确保双向 subscribe+publish |
| 已绑定同名通道 | 合并 diff（只改缺失的 subscribe/publish/priority），不整表覆盖 |

通道名解析顺序：团队已有最常见 `channel_name` → 否则 `eco_{team_id}_collab` 新建建议。

**C. 与四维基因的关系（两层一起展示，不互替）**

```
share  ──► 边：share 对；通道：互助总线权限
signal ──► 边：信号源→跟随者；通道：publish
follow ──► 边：跟随者→信号源；通道：subscribe
mate   ──► 仅保留在 eco_collab；不进关系/通道
```

#### 3.5.4 ③ 反馈台 UI

新增分区 **「协作关系建议（关系 + 通道）」**：

- 表 1：建议关系边列表（勾选、rel_type 下拉、已存在灰显）  
- 表 2：建议通道 diff（agent × channel × subscribe/publish/priority）  
- 操作：预览 / 确认写回关系 / 确认写回通道 / 一键写回关系+通道  
- 链：`打开团队配置 · 该 Agent · 关系 tab`（带 `?highlight=eco_fp`）

#### 3.5.5 API（最小增量）

| 接口 | 行为 |
| --- | --- |
| `POST .../relation-integration/suggest` | 入参 result/timeline + team_id → 边建议列表 |
| `POST .../relation-integration/apply` | `confirm=true` 才 `RelationshipStore.add`；审计 `eco_fp` |
| `POST .../channel-integration/suggest` | 通道 diff 建议 |
| `POST .../channel-integration/apply` | `confirm=true` 合并写 `agent.channels` 并持久化 |

可选合并为 `collab-topology/suggest|apply` 一次返回边+通道（实现任选，产品一体）。

#### 3.5.6 门禁

进入 ④ 成本优化时，门禁扩展为（可配置 OR）：

- Skill 已确认写回，**或**  
- 协作基因已确认，**或**  
- **关系或通道至少一侧已确认**，**或**  
- 显式跳过并记原因  

推荐默认文案强调：**仅写 eco_collab 未写关系/通道时提示「协作拓扑尚未落地到团队页」**（可仍允许进成本，但 amber 警告）。

### 3.4 门禁与去向

| 按钮 | 行为 |
| --- | --- |
| 保存反馈快照 | 写入 `storage/eco_feedback/{fp}.json`（审计，不必写真身） |
| 确认写回 Skill | 调现有 apply |
| 确认写回协作基因 | 调 collab apply（metadata.eco_collab） |
| **确认写回关系 / 通道** | 调 relation/channel apply（**真协作拓扑**） |
| **进入演进式成本优化** | 校验：Skill / 协作基因 / 关系·通道 至少一侧已确认，**或**勾选「跳过写回（仅快照）」并填原因 → 跳转 cost-dashboard 带 query |
| 再跑一场物竞 | 回到 ②，保留契约 |

门禁文案（用户可见）：

> 进入成本优化前，请将物竞筛出的 Skill、协作基因与 **关系/通道** 反馈到智能体（或显式跳过并记审计）。成本页只计量 token，不负责改协作拓扑。

---

## 4. 用户路径（主故事）

```
Plaza / 任务 → 送入试验田（team+task 深链）
  → ① 拧生境/加压旋钮
  → ② 开始物竞天择 + 回放
  → ③ 适者反馈台自动打开
       勾选 Skill 建议 + 调协作基因
       勾选关系边 / 通道 diff（物竞协作链证据）
       预览 → 确认写回（Skill / 基因 / 关系·通道）
  → 团队配置「关系」页可见新 collaborator / 通道权限
  → ④ 进入 cost-dashboard（候选构型 = 已反馈团队）
       tokens_per_goal / 棘轮 只针对该构型计量
```

次要路径：

- 从成本页「物竞候选」链回 ③（若未写回）  
- 从智能体详情「来自物竞的建议」徽标链回 ③ 同 fingerprint  
- 从团队页「关系」空态链到「用最近一场物竞生成建议」 

---

## 5. 后端与数据（最小增量）

| 能力 | 现状 | 增量 |
| --- | --- | --- |
| Skill 建议/写回 | `skill-integration/suggest|apply` | 反馈台消费；apply 审计带 `eco_fp` |
| 协作基因写回 | `collab-integration/suggest|apply` → metadata.eco_collab | 保留；标注为表型层 |
| **关系建议/写回** | 仅人工 RelationshipStore | **`relation-integration/suggest|apply`**（confirm；`created_by=human_via_eco_feedback`） |
| **通道建议/写回** | 仅人工改 `agent.channels` | **`channel-integration/suggest|apply`**（confirm；合并 diff） |
| 反馈快照 | 轻量 sessionStorage | 扩展含 relation/channel 建议快照 |
| 门禁 token | 前端 | 纳入关系/通道确认位 |
| 成本页入参 | `?team_id&eco_fp&feedback=` | 可带 `topology=done|skipped` |

**不在本阶段做**：静默自动建边（违反人工确认）、自动改 Soul.md 长文、自动改 Plaza 座席规则、把 mate/COURT 写成业务 collaborator。

---

## 6. 前端模块划分

| 模块 | 职责 |
| --- | --- |
| `Agent-digital-twin.html` | `#rp-eco-feedback` DOM + 步骤条 + 关系/通道区 |
| `js/digital-twin/eco-feedback.js` | 渲染 Skill/基因/关系/通道 diff、勾选、调 API、门禁 |
| `sandbox/relation_integration.py`（新） | timeline→边建议纯函数 |
| `sandbox/channel_integration.py`（新） | genome+timeline→通道 diff 纯函数 |
| `eco_runtime_routes.py` | suggest/apply 路由 |
| `agent_relationships.py` | apply 时 add；允许 created_by 扩展值（仍须人点确认） |
| `eco-console.js` | 演练 `onDone` → `ecoFeedbackOpen(result)` |
| `agent-team-config` 关系 tab | 展示边；可选「物竞来源」chip |
| `cost-dashboard.html` | 读 query 展示「来自物竞的候选」只读条 |

---

## 7. 与成本优化的边界（写进 UI 文案）

| 阶段 | 页面 | 改什么 |
| --- | --- | --- |
| 物竞 | 孪生试验田 ①② | 环境旋钮、演练 |
| **反馈** | 孪生试验田 **③** | **Skill + 协作基因 + 关系边 + 通道绑定** |
| 成本 | cost-dashboard | token 目标、棘轮、Gate——**不改人设/拓扑** |

---

## 8. 验收标准

1. 一场带契约的物竞结束后，无需翻找小按钮即可进入 ③ 反馈台。  
2. 可对至少 1 个 agent **预览并确认** Skill 写回，agent-detail 技能列表可见变化。  
3. 可对至少 1 个 agent **确认协作基因写回**，metadata.eco_collab 可读回。  
4. **可对至少 1 条关系边 / 1 条通道 diff 预览并确认写回**；团队配置「关系」页可见新边或通道权限变化。  
5. `confirm=false` 时关系与通道 **零写入**。  
6. 未反馈且未跳过时，「进入成本优化」给出拦截说明；仅写基因未写拓扑时有可见警告（可配置是否硬拦）。  
7. 跳过写回必须记原因；成本页 URL 可区分 `feedback=done|skipped`。  
8. `node --check` 相关 JS；pytest 覆盖 suggest 映射与 apply 门禁；div 平衡。

---

## 9. 非目标

- 不把反馈台塞进 pet-config  
- 不在 Plaza 讨论阶段引入 token 或物竞写回  
- 不一键静默改全队人格或 **静默建关系边**  
- 不把 mate/COURT 写成业务 collaborator  
- 不合并 cost 棘轮与 eco 生存棘轮为同一状态机（可后续关联 fingerprint）  
- 不在本阶段改造通信门禁算法本身（只喂 RelationshipStore / channels 数据）

---

## 10. 实施分期

| 期 | 内容 | 状态 |
| --- | --- | --- |
| P0 | ③ 面板 DOM + Skill 表 + apply + 步骤条 + 成本门禁 | 已落地 |
| P1 | 协作基因表 + collab apply + metadata | 已落地 |
| P2 | 反馈快照轻量 + cost 候选条 | 已落地 |
| **P3** | **通道能力全量 + 物竞 channel/relation 写回**（§3.5 / XF-7） | **通道+关系边均已落地**（suggest→confirm apply）；本机联测 XF-7.14b/15 待做 |

配套 todos：[`物竞适者反馈调整台todos.md`](物竞适者反馈调整台todos.md)。
