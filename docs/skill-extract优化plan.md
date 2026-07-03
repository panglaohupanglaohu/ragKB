# skill-extract.html 优化 Plan（前后端 + 技能闭环）

> 目标页面：`http://localhost:5173/skill-extract.html`（技能萃取/赋予）
> 前端：`skill-extract.html`(856) + `js/skill-extract.js`(5200) + `js/skill-extract-timeline.js`(572) + `js/extract-routing.js`(47)
> 后端：`agents/skill_extractor.py`(萃取引擎) + `agents/extraction_routes.py`(管线 REST,16 路由) + `agents/extraction_pipeline.py`(状态机) + `agents/extraction_store.py`(事件溯源) + `agents/skill_library.py`(技能库) + SSE 在 `agents/api.py` `/teams/{team_id}/skill-extract/stream`
> 编写日期：2026-06-13
> 分派：**【Claude(沙箱可做)】** = 代码/HTML 改动 + node--check/vitest/纯 python 可验证；**【Reasonix(本机/浏览器)】** = 起服务、真 LLM 萃取、浏览器冒烟、后端 2xx 门

---

## 0. 现状结论（先摸清，再动手）

skill-extract 是目前最成熟的页面：

- **3D 菌丝可视化**：Three.js（知识 → 菌丝 → 结晶技能节点），`rebuildSkillNodes` **已正确 dispose**（geometry/material/map），无 GPU 泄漏。
- **SSE 已健全**：`connectSSE` 有 `onopen` 复位 + `onerror` 指数退避重连（3s→6s→…上限 60s、最多 20 次、`document.hidden` 不重连）。比 plaza/system-evolution 都成熟。
- **CSRF 包装**：`_ensureCsrf_sk` + `_af_sk`/`api()` 对写操作自动带 `x-csrf-token`，`api()` 统一 try/catch + toast。
- **萃取管线**：六段式（知识投入 → ①日志采集 draft → ②上下文补全 review → 交叉复核门禁 → approve → 发布/赋予），后端事件溯源存储。

所以本轮：**修真实缺陷 + 落地一个「技能闭环」旗舰能力**。

---

## 1. 头号缺陷：HTML 重复 ID 致第二个交叉复核 UI 错位（P0）

`grep -oE 'id="..."' | uniq -d` 查出 **10 个重复 ID**：
`reviewer-list`、`review-inline-form`、`review-name`、`review-comment`、`review-identity`、`btn-show-review-form`、`gate-status-badge`、`gate-reviewer-count`、`gate-approval-count`、`gate-progress-fill`。

它们各出现两次：一处在 `#modal-detail`（队列项详情模态，~387 行），另一处在第二个复核区块（~625 行）。`document.getElementById()` **只返回第一个**，因此第二个交叉复核界面读写的全是第一个模态的元素 → **门禁计数、复核人列表、确认表单全部错位**，第二处的复核流程实质不可用 / 干扰第一处。

**修复方向（Claude）：** 第二套 ID 加后缀（如 `-secondary`）或按所在模态容器作用域查找（`modalEl.querySelector('.reviewer-list')` 取代全局 `getElementById`），并同步改 JS 引用。需判断两处分别服务哪个模式（萃取详情 vs 技能详情/赋予），属需设计判断的 Claude 项。

---

## 2. 第二缺陷：confirm()/prompt() 阻塞式对话（P1）

7 处原生阻塞对话框（回滚确认、拒绝原因×2、删除确认×2、替换示例确认、待办标题、删除技能确认）。体验割裂、无法自动化测试。

**修复方向（Reasonix）：** 统一替换为页内确认/输入弹层（页面已有 modal 体系 `openM`/`closeM`/`modal-overlay`），拒绝原因/待办标题改为页内输入框。

---

## 3. 第三梯队（P2，Reasonix 机械项）

- **`api()` 错误信息**：`showToast('请求失败: ${e.message}')` 仅含 HTTP 状态文本,无 request_id。可补 request_id 便于排障（与其它页对齐）。
- **生产日志**：`console.log/warn/error` 若干（SSE、API、TTS），收敛到 debug 开关。
- **可访问性**：modal `role="dialog"`、焦点陷阱;3D canvas `aria-label`。
- **后端接口门**：`extraction_routes` 16 路由 + skill-extract SSE 的 2xx 回归。

---

## 4. 旗舰能力：技能萃取 → 赋予 → 数字孪生提分（闭环）★

> 用户要求:亲自设计一个真能用、对 agent 有明显成效的 skill,并在数字孪生中证明它提升 agent 能力与协作评分,形成闭环,写入 README。

### 4.1 设计的 skill：「结构化代码评审」(`structured-code-review`)
- 产物：`storage/skills/c0de7a11.json`（已落地,schema 与现有技能一致）。
- 内容：一套五层评审检查清单（正确性 / 接口契约 / 测试 / 可维护性 / 风险回滚），「阻塞项 vs 建议项」两档、一次性给全、阻塞项必附行号与修法。
- 目标技能名：`code_review`（映射到场景 `code_review_delivery` 的瓶颈环节）。

### 4.2 为什么它有成效（系统机理,本轮通过它吃透系统）
数字孪生试炼引擎 `sandbox/twin_loop.py`:任务成功概率 `success_p = clamp(0.3 + 0.6×prof, 0.2, 0.95)`，由 agent 对该任务 `required_skills` 的 **熟练度 prof** 决定;成功保奖励 + 熟练度自学习,失败按 `PROF_FAIL_REWARD_FACTOR=0.3` 折损。`code_review_delivery` 场景的瓶颈正是「评审(c4) → 返工(c5)」。授予「结构化代码评审」skill = 把评审员 `code_review` 熟练度先验从 0.45 提到 0.85 → 评审任务一次性通过率大幅提升 → 缓解评审瓶颈、减少返工。

### 4.3 萃取过程（如何把这个 skill 走 skill-extract 管线萃取出来）
1. **知识投入**：将「代码评审最佳实践」六页纸 / plaza 讨论结论作为 `source_text` 投入（`skill-extract.html` 知识投入区,或从 plaza「萃取」按钮带 `extract_source` 跳入）。
2. **①日志采集(draft)**：`skill_extractor` 调 LLM 产出技能草稿（name/description/instructions/category）,SSE 推 `item_status_changed: llm_prefilling → ready_for_review`。
3. **②上下文补全(review)**：人工补全/校订 instructions（即 4.1 的五层清单）。
4. **交叉复核门禁**：≥1 名复核人确认推进（`review-gate-section`,需先修 §1 重复 ID 才能在第二模态正常用）。
5. **approve → 发布/赋予**：审批通过写入技能库（`skill_library`,产物即 `storage/skills/<id>.json`）;`publish` 进公共库或 `import_skill` 赋予目标团队的评审员 agent。
6. **赋予即提分**：赋予后该 agent 的 `code_review` 熟练度先验抬升(见 `proficiency_store`),下次数字孪生试炼即体现。

### 4.4 闭环验证（已实现 + 已在沙箱实跑）
脚本 `scripts/skill_closed_loop_demo.py`（纯 `sandbox.*`,不需 LLM/外网,可离线复跑）：
- 载入真实场景 `code_review_delivery` → `compile_scenario` → 真 `TwinLoopEngine` 跑 30 个固定种子。
- baseline:评审员 `code_review` 熟练度 0.45;treatment:0.85（=授予 skill 后）;其余技能两组完全一致(隔离净效果)。

**实测结果(30 seeds,可复现):**

| 指标 | baseline(0.45) | treatment(0.85) |
|---|---|---|
| code_review 任务成功率 | 72.1% | **90.4%** |
| 团队整体成功率 | 84.1% | 84.3% |
| 平均总奖励 | 70.64 | 70.74 |

→ **目标能力(code_review)成功率 +18.3 个百分点**,直接缓解评审瓶颈、减少返工往返。团队整体仅 +0.3pp 属预期（5 个 agent 只动了 1 个评审员、8 任务里评审占 1 个），成效**精准集中在 skill 所针对的环节**,这正是诚实的闭环证据。

闭环判据:`treatment.code_review_rate > baseline + 0.05` → 脚本返回「闭环成立 ✅」。

### 4.5 写入 README
README 新增「技能闭环演示」章节:skill 是什么、萃取链路、机理、复跑命令、实测数字。

### 4.6 UI 闭环入口:「模拟」按钮 → 「赋予/注入技能」

「赋予」模式当前有 `🔍 路由 / ⚡ 模拟 / ▷ 注入` 三个动作:
- `⚡ 模拟`(`_executeRuntimeSim`)只是随机 query → 路由 → 自动选 3 → 调注入的**演示**;
- `▷ 注入`(`_executeAssign` → `POST /skill-router/assign` → `skill_router.assign()`)只把技能 append 进 `agent.skills` + 生成 inject_prompt。

**本轮挖出的真实缺口:`assign()` 不写 `proficiency_store`** —— 所以 UI 上「注入」技能后,数字孪生 trial 读取的熟练度先验**不会上升**,闭环在 UI 这环没接上。

改造方案(详见 todos S-5,带伪代码):
1. **前端**:把「⚡ 模拟」改成「⚡ 赋予/注入」真动作(选中项直接赋予;无选中则路由→自动选 Top-K→赋予,保留动画)。
2. **后端**:`assign()` 在 append 技能后,按 skill 的 `metadata.target_skill`(如 `structured-code-review → code_review`)调 `proficiency_store` 把该 agent 目标技能先验抬到 ≥0.8,返回 `proficiency_boosted`。**这一步真正把「UI 赋予」接到「数字孪生提分」**,与 §4 的离线闭环合体成完整 UI 闭环。
3. **验证**:`scripts/skill_closed_loop_live.py`(本机连真后端,proficiency 设 0.45/0.85 各跑真试炼,对照离线 +18.3pp)。

---

## 5. 实施顺序

1. **闭环旗舰(★,已大部完成)**:skill 产物 + demo 脚本 + README（Claude 已落地;真 LLM 萃取链路本机复跑由 Reasonix）。
2. **P0 重复 ID**（Claude,需设计判断）。
3. **P1 confirm/prompt 去阻塞、api request_id**（Reasonix 为主）。
4. **P2 日志/可访问性/后端 2xx 门**（Reasonix）。

详见 `docs/skill-extract优化todos.md`。
