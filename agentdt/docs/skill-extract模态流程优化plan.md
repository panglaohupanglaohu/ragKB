# skill-extract 模态全流程优化 Plan（编辑→演化→验证→效果→版本→智线）

> 目标页面：`http://localhost:5173/skill-extract.html` 的技能详情模态
> 覆盖 Tab：**编辑(edit) · 演化(evolve) · 验证(verify) · 效果(usage) · 版本(version) · 智线(pipeline)**
> 前端：`src/frontend/js/skill-extract.js` + `src/frontend/skill-extract.html`
> 后端：`agents/skill_extractor.py`(萃取队列) · `agents/skill_evolver.py`(演化) · `agents/skill_verifier.py`(验证) · `agents/skill_library.py`(技能库/版本/发布门禁) · 路由集中在 `agents/api.py`
> 编写日期：2026-06-15
> 分派：**【Claude】**=JS/HTML/纯py 改动，可用 `node --check` / `vitest` / `pytest` 验证；**【本机】**=起真后端、真 LLM、浏览器冒烟

---

## 0. 背景与本轮目标

本页模态是「一个萃取草稿 → 注册技能 → 持续演化/验证/版本管理」的全生命周期工作台。最近连续暴露的真实缺陷都集中在**「队列项(item) 与 已注册技能(skill) 两套身份不一致」**：

1. 演化 Tab 用 `item.status` 判断能否演化，但徽章用 `allSkills` 里注册技能的 `lifecycle_stage` —— 两者口径不一致 →「阶段 approved 却提示要先批准入库」。（已修）
2. 改名后只改了 `edit-name`，模态顶部 `modal-title` 不刷新 →「验证页名称没变」。（已修）
3. `resolveSkillId` 多级回退，但 `allSkills` 异步未就绪时回退到 slug，后端 `_find_skill` 不一定认 → 偶发「找不到已注册的技能ID」。

本轮把六个 Tab 的「数据来源、空态、错误态、字段口径」全部对齐，并补齐自动化测试，使本模块前端 vitest + 后端 pytest 全绿。

---

## 1. 各 Tab 现状与缺陷清单

### 1.1 编辑 Tab（edit）
- `_openDetail` 拉 `GET /teams/{tid}/skill-extract/{item_id}` 回填 `#edit-*`。
- `saveEdits` → `POST .../edit`；`approveAs(type)` → `POST .../approve`。
- **缺陷**：
  - (P0) `resolveSkillId` 在 `allSkills` 未加载时易回空 → 其它 Tab 全部连环失败。
  - (P1) 保存/批准成功后未把 `skill_id` 写回本地 `queueItems`，切 Tab 仍可能解析不到。

### 1.2 演化 Tab（evolve）
- `loadEvolveTab` 读 `allSkills` 显示统计 + `loadEvolveSuggestions`；`triggerEvolve`→`POST /skill-library/evolve`；`acceptEvolution`→`POST /skill-library/apply-evolution`。
- **缺陷**：
  - (P0) 演化门禁与徽章口径不一致（已修，补测试固化）。
  - (P1) `triggerEvolve` 出错时按钮文案/disabled 不保证复位。
  - (P1) `acceptEvolution` 未 `await loadQueue()/loadSkills()`，存在竞态。

### 1.3 验证 Tab（verify）
- `loadVerifyTab` 重置 UI；`triggerVerify`→`POST /skill-library/verify` 返回 `VerificationResult`。
- **缺陷**：
  - (P1) 同样依赖 `resolveSkillId`，未注册时直接「找不到技能ID」，无引导。
  - (P2) `pass_rate/passed/failed/test_details/process_log` 字段空值未兜底，后端返回精简结构时 UI 报 undefined。

### 1.4 效果 Tab（usage）
- `loadUsageTab` 读 `GET /teams/{tid}/skills` 找当前技能，渲染 `usage_count/effectiveness/quality_score/last_used_at`。
- **缺陷**：
  - (P2) 找不到注册技能时整页空白（应回退用 item 草稿统计 + 友好空态）。

### 1.5 版本 Tab（version）
- `loadVersionTab`→`GET /skill-library/{skill_id}/evolution-history`（期望 `lineage`）；`rollbackVersion`→`POST /skill-library/version/rollback`。
- **缺陷**：
  - (P1) 前端期望 `data.lineage`，后端 `/evolution-history` 与 `/versions` 结构不一，需对齐或前端双兼容。
  - (P2) 无版本时空态缺失。

### 1.6 智线 Tab（pipeline）
- `loadPipelineTab`→`loadItemPipeline`→`GET {PIPELINE_API}/pipelines/{id}` + events，渲染 stepper/门禁/复核/todos/事件。
- **缺陷**：
  - (P2) pipeline 不存在时（纯萃取草稿未进管线）报错，需懒创建或空态。

---

## 2. 修复策略（统一口径）

**核心原则：所有 Tab 取技能身份只走一个函数 `resolveSkillId(item)`，且该函数在 `allSkills` 未就绪时能触发一次同步加载兜底。**

1. **身份解析加固**：`resolveSkillId` 增加「approve 返回值写回 `item.skill_draft.skill_id`」与「allSkills 兜底懒加载」；保存/批准后把后端返回的 `skill_id` 合并进 `queueItems`。
2. **门禁口径统一**：能否演化/验证/版本，统一判据 = `resolveSkillId(item)` 非空（即已在库注册），不再单看 `item.status`。
3. **错误态/空态兜底**：每个 Tab 的渲染函数对 `undefined/[]` 做兜底，给出可读空态文案与「去注册/去验证」引导。
4. **竞态修复**：`acceptEvolution`、`approveAs` 中对刷新调用 `await`。
5. **按钮状态机**：`triggerEvolve/triggerVerify` 用 `try/finally` 复位按钮。

---

## 3. 测试策略（本模块全绿目标）

### 3.1 前端 vitest（`src/frontend/__tests__/`）
沿用现有「读取源码字符串断言关键链路存在」的轻量风格（无需 DOM 运行时），新增：
- `skill-extract-modal-flow.test.js`：断言六个 Tab 的加载函数、API 端点、空态/错误兜底、身份统一口径关键代码均存在。
- 现有 4 个 skill-extract 相关用例保持通过。

### 3.2 后端 pytest（`src/backend/tests/` 或 `tests/`）
- `test_skill_evolver_flow.py`：`evolve_skill` + `apply_evolution` 返回结构与版本自增（用 Fake LLM，纯内存）。
- `test_skill_extract_identity.py`：approve 后 `to_dict()`/registry 能用 slug 与 skill_id 双向 `_find_skill`。
- 复用现有 `test_skill_verifier.py`、`test_skill_publish_gate.py`。

### 3.3 运行命令
- 后端：`python3 -m pytest src/backend/tests tests -q`
- 前端：`npx vitest run src/frontend/__tests__`

---

## 4. 实施顺序

1. P0 身份解析加固（编辑+演化门禁）→ 固化为前端测试。
2. P1 竞态 + 按钮状态机 + 保存/批准写回。
3. P2 各 Tab 空态/错误兜底（验证/效果/版本/智线）。
4. 补后端 pytest，跑全量回归至全绿。
5. 浏览器逐 Tab 冒烟（本机），按 todos 的「演示步骤」执行。

详见 `docs/skill-extract模态流程优化todos.md`。
