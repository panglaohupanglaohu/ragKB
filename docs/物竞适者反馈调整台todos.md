<!-- docs-signoff: author="Grok" kind="llm" doc="todos" ts="2026-07-14T15:17:30Z" -->
# 物竞适者反馈调整台 — Todos

> 配套 [`物竞适者反馈调整台plan.md`](物竞适者反馈调整台plan.md)  
> 状态：`[ ]` 待办 / `[~]` 进行中 / `[x]` 完成 / **`[?]` 待讨论**。  
> **产品主轴（2026-07-14 用户明确）**：**以任务（业务场景实例）为主形成闭环**——物竞试验田不是「随便选队空跑」，而是 **任务挂接 → 契约考卷 → 演练 → 适者反馈 →（可选）成本优化**。  
> **协作主轴（2026-07-14）**：真正的协作关系变化 = **关系网络 + 通道绑定** 经人确认写回；`eco_collab` 基因只是表型层（见 **XF-7**）。  
> **验收**：`PYTHONPATH=src/backend python3 scripts/verify_eco_feedback_xf.py`（2026-07-14 PASS=51，含 XC BidCandidate 全链路）。

---

## XF-0: 文档

- [x] **XF-0.1** plan 落盘（sign-off）
- [x] **XF-0.2** todos 落盘（sign-off）
- [x] **XF-0.3** `docs/README.md` 增加导航条目

---

## XF-1: P0 反馈台壳 + Skill 写回（主路径）

- [x] **XF-1.1** `Agent-digital-twin.html`：试验田步骤条 ①②③④；`#rp-eco-feedback` 面板结构  
- [x] **XF-1.2** `eco-feedback.js`：从 `_lastResult` + contract 渲染考卷摘要 + Skill 建议表（勾选）  
- [x] **XF-1.3** 演练结束 / 报告关闭后调用 `ecoFeedbackOpen(result)` 打开 ③  
- [x] **XF-1.4** 接 `skill-integration/suggest|apply`：预览 + 确认写回；状态文案  
- [x] **XF-1.5** 「进入演进式成本优化」门禁：未写回且未跳过则拦截；跳过需原因  
- [x] **XF-1.6** 跳转 `cost-dashboard.html?team_id&eco_fp&feedback=done|skipped`  
- [x] **XF-1.7** `node --check` + HTML div 平衡

---

## XF-2: P1 协作模式写回

- [x] **XF-2.1** API `collab-integration/suggest`（从 ranking collab_genome 生成建议）  
- [x] **XF-2.2** API `collab-integration/apply`（confirm + metadata.eco_collab）  
- [x] **XF-2.3** 反馈台协作表 + 滑杆 + 写回策略（覆盖/混合/仅快照）  
- [x] **XF-2.4** agent-detail 状态页只读展示 eco_collab 四维条 + 关系 tab 摘要  
- [x] **XF-2.5** 单测：apply 幂等、confirm=false 零写入

---

## XF-3: P2 快照与成本页接线

- [x] **XF-3.1** 反馈状态 sessionStorage + cost URL 查询串（轻量快照；全量 JSON 落盘可后续）  
- [x] **XF-3.2** cost-dashboard 顶部「物竞候选」只读条（读 query + 可选拉快照）  
- [x] **XF-3.3** 成本页候选条说明：改人设回孪生 ③；本页只 token  

---

## XF-4: 验收

- [x] **XF-4.1** 通路验收：skill suggest/apply 符号 + 活后端集成（`verify_eco_feedback_xf.py`）；浏览器全流程仍可人肉抽检  
- [x] **XF-4.2** 协作写回后 `metadata.eco_collab` 可读（live API 已验）  
- [x] **XF-4.3** 前端门禁 `ecoFeedbackGoCost` + cost 页 `feedback=skipped|done` 接线（静态+符号验收）  

---

## XF-5: 任务型考卷可视化（已拍板落地）

> 背景（2026-07-14 用户校准）：办公室无「觅食」孪生；禁止蓝柱黄球 + 裸 skill hex 图腾。  
> **推进决策（2026-07-14）**：做可视化，但用**办公室/任务语言**；载体以 **B 为主 + 右侧 chips 进度**；**仅任务契约挂接时**开启；旧图腾仅 `__ECO_HABITAT_3D__` 实验保留。

| 问题 | 决策 |
| --- | --- |
| XF-5.1 是否做 | **做**：任务型演练显示考卷进度 / 本步技能 |
| XF-5.2 载体 | **B** 3D 窗口右上 2D HUD + 右侧 `eco2-env-niches` 高亮；**不做** 3D 蓝柱图腾 |
| XF-5.3 开关 | **仅** `_boundContract.niches` 非空时显示；随机空跑不出现考卷 HUD |
| XF-5.4 旧路径 | **保留** `window.__ECO_HABITAT_3D__` 实验开关，默认关 |

- [x] **XF-5.1** 任务型 HUD 表达：本步所需技能 + 考卷进度（中文 label / 非裸 hex + 可选 📖）  
- [x] **XF-5.2** 载体：`#env-3d-task-hud`（2D）+ 右侧 chips；3D 零 demand 柱  
- [x] **XF-5.3** 仅挂接 TaskHabitatContract / 任务时 `ecoTaskHudBind`；解除 `ecoTaskHudClear`  
- [x] **XF-5.4** 旧图腾路径仍默认关（`__ECO_HABITAT_3D__`）  
- [x] **XF-5.5** `eco-task-hud.js` + office-boot 任务型文案切换 + 回放 `ecoEnv` 驱动进度  

**实现**：`src/frontend/js/digital-twin/eco-task-hud.js` · `eco-console.js` bind/clear · `office-boot.js` · `Agent-digital-twin.html`

---

## XF-6: 演练控制 — 选种群后必须提供任务挂载（任务主闭环）【用户要求 · 须落地】

> **用户建议（2026-07-14，须在 todos 明确）**  
> 在 **演练控制** 里 **选择投放种群（团队）之后，都要提供一个任务挂载菜单**。  
> 目标：形成 **以任务（业务场景实例）为主** 的闭环，而不是只选队、无考卷的空跑。

### 产品闭环（目标态）

```
业务场景实例 = 团队任务（plaza 派发 / 任务列表 / 执行计划）
    → 演练控制：选种群
    → 【必现】任务挂载菜单（该队任务列表，可选挂接）
    → 挂接后：TaskHabitatContract 考卷 + 右侧已挂接任务区
    → 物竞演练 → ③ 适者反馈（Skill/协作）→ ④ 成本优化
```

### 待办项

- [x] **XF-6.1** 主种群选中后：演练控制区 **始终展示「任务挂载」区块**（`#eco2-task-mount` + 下拉）  
- [x] **XF-6.2** 任务挂载菜单：拉取队任务列表（title/status/plan）  
- [x] **XF-6.3** 选中任务 → `eco2BindTaskById` 编译契约；解除 → `eco2ClearPrimaryTask`  
- [x] **XF-6.4** 未挂任务开跑 → confirm 随机空跑，否则引导挂任务  
- [x] **XF-6.5** 对比种群任务下拉（既有 XG-12）+ 主任务 plan 预选同 plan（保持）  
- [x] **XF-6.6** 文案：① 种群 ② 挂载任务（业务场景实例）  
- [x] **XF-6.7** 验收：DOM/符号 + 任务列表 API（`verify_eco_feedback_xf.py`）；深链人肉抽检可选  

> 与成本结合的后续：见 [`物竞与成本优化结合todos.md`](物竞与成本优化结合todos.md)（先适者后省钱）。

### 非目标（本条）

- 不在此条恢复 3D「当前需求」柱（见 XF-5 待讨论）  
- 不强制每个历史任务都可挂；无任务的队菜单显示空态 + 链到任务/Plaza 创建  

---

## XF-7: 物竞协作 → 关系/通道 + **通道能力全量补齐**【用户要求 · 须落地】

> **用户校准（2026-07-14）**  
> 协作基因写 `eco_collab` **≠** 协作关系变了。真正变化 = 团队页 **关系** + **通道绑定**。  
> **追加**：同队 peer 与共总线**就是协作关系**（三层 enforce 点不同）。

### A. 通道基础设施（已落地）

- [x] **XF-7.C1** 修复 `PUT .../channels` 调用 `_persist()`  
- [x] **XF-7.C2** `agents/agent_channel_bus.py`：publish/subscribe 权限 + 进程内总线  
- [x] **XF-7.C3** 工具 `broadcast` / `subscribe_channel` / `publish_event` 真正校验并写总线  
- [x] **XF-7.C4** API `POST .../channels/publish` + `GET .../channels/inbox`  
- [x] **XF-7.C5** 团队配置「关系」tab：通道可增删改保存 + 测发布/收件箱  
- [x] **XF-7.C6** `AgentChannelConfig.source/note`（物竞 chip）+ team_store 读写  
- [x] **XF-7.C7** pytest `tests/test_channel_integration.py`  

### B. 物竞 → 通道写回（已落地）

- [x] **XF-7.2** `sandbox/channel_integration.py`（genome + timeline → diff）  
- [x] **XF-7.2b** `resolve_team_bus` 优先真身已有 channel_name（修 `aws-ops_bus` vs `aws_ops_bus` 分叉）  
- [x] **XF-7.4** `channel-integration/suggest|apply`（confirm + 合并 + persist）  
- [x] **XF-7.7/8** ③ 反馈台通道表 + 预览/写回  
- [x] **XF-7.9** 文案：基因=表型；通道=真拓扑  
- [x] **XF-7.10** 仅写基因未写通道 → amber + query `topology=gene_only`  
- [x] **XF-7.12** 通道列表物竞 chip  

### C. 关系边

- [x] **XF-7.1** `sandbox/relation_integration.py`（timeline share/follow → 边建议；mate 不进）  
- [x] **XF-7.3** `relation-integration/suggest|apply`（confirm + RelationshipStore + created_by=human_via_eco_feedback）  
- [x] **XF-7.7b** ③ 反馈台关系边 Before/After 拓扑图 + 预览/写回 + 门禁纳入 relation  
- [x] **XF-7.11** 深链团队关系 tab（`team_id&view=agent&atab=ag-relations`）+ 关系 tab 读 RelationshipStore  
- [x] **XF-7.13** 空关系 CTA（团队配置 + agent-detail 链到物竞 ③）  

### D. 任务执行拓扑（续）

- [x] **XF-7.16** `check_can_communicate` = 门禁边 | 同队 peer | 共总线  
- [x] **XF-7.17** `delegate` / `send_message` / workflow handoff 接 gate  
- [x] **XF-7.18** step prompt 注入协作拓扑  

### 验收

- [x] **XF-7.14a** 单元测试权限/总线/suggest + relation/channel/topology  
- [x] **XF-7.14b** 活后端：写回通道/关系 → store/agent 可读（`verify_eco_feedback_xf.py`）  
- [x] **XF-7.15** confirm=false 零写入（离线+活后端）  

### 非目标

- 不静默建关系边；mate 不进通道；总线为进程内（非分布式 MQ）  
- XF-5 3D 可视化待用户确认后再做  

### 依赖

- `agent_channel_bus` · `channel_integration` · `relation_integration` · `eco_runtime_routes` · `eco-feedback.js` · `agent-team-config.js` · `agent_relationships.py`  
