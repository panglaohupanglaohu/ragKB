<!-- docs-signoff: author="Grok" kind="llm" doc="todos" ts="2026-07-14T15:17:30Z" -->
# 物竞天择 × 演进式成本优化 — Todos

> 配套 [`物竞与成本优化结合plan.md`](物竞与成本优化结合plan.md)  
> 原则：**先选活得长的（\(T_i\) 过线），再选花钱省的（token 最小）**。  
> 任务主轴：业务场景实例挂载 → 演练 → 适者反馈 → 成本竞标。  
> 状态：`[ ]` 待办 / `[~]` 进行中 / `[x]` 完成 / `[?]` 待讨论。  
> **验收**：`pytest tests/test_bid_candidate.py`（5）+ `PYTHONPATH=src/backend python3 scripts/verify_eco_feedback_xf.py`（PASS=51，含 live create→lock→GET production）。

---

## XC-0: 文档与入口

- [x] **XC-0.1** plan 落盘（sign-off）  
- [x] **XC-0.2** todos 落盘（sign-off）  
- [x] **XC-0.3** `docs/README.md` 导航条目  
- [x] **XC-0.4** 根 `README.md` 物竞节交叉链接「先适者后省钱」  

---

## XC-1: M0 试验田任务主入口（XF-6）

- [x] **XC-1.1** 选种群后展示「② 挂载任务」菜单（`eco2-task-mount`）  
- [x] **XC-1.2** 拉取队任务列表 + 选中编译契约  
- [x] **XC-1.3** 解除挂载  
- [x] **XC-1.4** 未挂任务开跑 → 确认随机空跑  
- [x] **XC-1.5** 任务挂载符号 + 任务列表 API 验收（`verify_eco_feedback_xf.py`）  

---

## XC-2: M1 BidCandidate 与推送

- [x] **XC-2.1** `sandbox/bid_candidate.py` schema + `storage/eco_bid_candidates/{team}/`  
- [x] **XC-2.2** `POST /api/v1/eco-runtime/bid-candidates`  
- [x] **XC-2.3** `GET .../bid-candidates?team_id=&task_id=`  
- [x] **XC-2.4** ③「推送到成本竞标」`ecoFeedbackPushBid` → POST → cost 带 `candidate_id`  
- [x] **XC-2.5** 无 task / 未反馈 → API 拒绝 + UI 文案  
- [x] **XC-2.6** cost-dashboard：候选表（T_i、质量门、token、棘轮）  
- [x] **XC-2.7** 单测 `tests/test_bid_candidate.py`  

---

## XC-3: M2 质量门 + token 填入

- [x] **XC-3.1** `POST .../quality-check` Q1–Q5（Q1/Q2 硬；Q3–Q5 默认可软）  
- [x] **XC-3.2** cost 页同 task 列表按 best_T 排序 + token 列  
- [x] **XC-3.3** 详情里手填/PATCH `tokens_baseline` / `tokens_candidate` → 自动 `cost_gate`  
- [x] **XC-3.4** baseline/candidate 字段可编辑保存  
- [x] **XC-3.5** 质量过线徽章 / 未过线原因  

---

## XC-4: M3 成本棘轮锁定与生产

- [x] **XC-4.1** `POST .../lock` 仅 `quality_passed`  
- [x] **XC-4.2** token 已填且候选更贵 → 拒绝锁定  
- [x] **XC-4.3** `ratchet_state=locked` 持久化；cost 页展示  
- [x] **XC-4.4** 生产任务提交读 locked：`apply_locked_config_to_task` 注入 metadata.required_skills + 适者 agent；`GET bid-candidates-locked`；step prompt 标注  
- [x] **XC-4.4b** SkillRouter 静默绑定 locked skill：`bind_locked_skills_via_router`；lock 时绑适者真身；任务提交幂等再绑；`skip_locked_skill_bind` 可关  
- [x] **XC-4.5** 文案区分：先适者后省钱 / 生存棘轮 vs 成本棘轮  

---

## XC-5: 文案与验收

- [x] **XC-5.1** 反馈台/成本页文案：任务实例 · 适者 · 省钱 · 禁止倒序  
- [x] **XC-5.2** API E2E：创建→列表→PATCH token→lock（本机已通）  
- [x] **XC-5.3** 与 XF 验收脚本并列；深链/对比/空跑既有 XF-6  

---

## 依赖与非目标

| 依赖 | 说明 |
| --- | --- |
| 反馈台 ③ | Skill/协作/关系/通道写回、门禁 |
| XF-6 / XC-1 | 任务挂载 |
| cost-dashboard | 候选面板 + 棘轮 UI |
| 非目标 | Plaza token 优化；成本页改 skills；默认 3D 觅食图腾 |
| 可选开关 | `metadata.skip_locked_bid` 全关；`skip_locked_skill_bind` 只关 SkillRouter 真身写入 |
