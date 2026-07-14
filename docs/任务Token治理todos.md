<!-- docs-signoff: author="Grok" kind="llm" doc="todos" ts="2026-07-14T23:03:06Z" -->
# 任务 Token 治理 — Todos

> 配套 [`任务Token治理plan.md`](任务Token治理plan.md)  
> 状态：`[ ]` 待办 / `[~]` 进行中 / `[x]` 完成。  
> 目标：本页 = **⑤ Token 治理**；物竞竞标折叠；2h 内可验收闭环。

---

## TG-0: 文档与导航

- [ ] **TG-0.1** plan / todos 落盘  
- [ ] **TG-0.2** `docs/README.md` 导航（若有物竞/成本节）  
- [ ] **TG-0.3** 全链序号文案：1 团队 → 2 Plaza → 3 技能 → 4 物竞 → **5 Token 治理** → 6 生产  

---

## TG-1: 页面骨架（主轴 / 折叠）

- [ ] **TG-1.1** 标题/顶栏改为「Token 治理」  
- [ ] **TG-1.2** 全链 1–6 进度条，⑤ is-here  
- [ ] **TG-1.3** 物竞竞标区 `<details>` 默认折叠；`candidate_id` 自动 open  
- [ ] **TG-1.4** 治理主轴四区 DOM：计量 / 缓存压缩 / 路由 / 预算+验证  

---

## TG-2: Token 计量（任务维）

- [ ] **TG-2.1** `TokenLedger.by_task`（scenario_id / run_id）  
- [ ] **TG-2.2** `GET /cost/tokens/by-task`  
- [ ] **TG-2.3** UI 任务 token 表（team / task_key / total / calls）  
- [ ] **TG-2.4** token_context 支持 `task_id` → 写入 scenario_id（兼容）  

---

## TG-3: 上下文缓存 + 内容压缩

- [ ] **TG-3.1** `agents/prompt_cache.py`：规范化指纹、LRU、hit/miss 统计  
- [ ] **TG-3.2** `compress_messages`：去重 + 长文本截断 + 重复 tool 折叠  
- [ ] **TG-3.3** API cache-stats / compress-preview  
- [ ] **TG-3.4** chat_harness 可选接入 compress（开关默认 on for estimate）  

---

## TG-4: 智能路由

- [ ] **TG-4.1** 暴露 ModelRouter 状态 API（档位/预算/粘滞）  
- [ ] **TG-4.2** UI 展示三档与当前档位 / 降档原因  

---

## TG-5: 效果验证 + 预算闭环

- [ ] **TG-5.1** BudgetGuard GET/POST 配置 API（session/agent/team 限额）  
- [ ] **TG-5.2** UI 预算读写（替换纯 localStorage 为服务端为主）  
- [ ] **TG-5.3** verify API：ledger 摘要 + token gate evaluate + cache 节省  
- [ ] **TG-5.4** UI「运行验证」按钮与结果卡  

---

## TG-6: 验收

- [ ] **TG-6.1** pytest：prompt_cache / by_task / budget / compress  
- [ ] **TG-6.2** verify 脚本符号检查 TG 主轴  
- [ ] **TG-6.3** 活后端 smoke（可选）  

---

## 非目标

- Plaza token 优化 · Redis 缓存 · LLM 摘要压缩 · 3D 图腾进成本页  
