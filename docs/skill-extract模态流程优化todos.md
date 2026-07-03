# skill-extract 模态全流程优化 Todos（事无巨细 · 带伪代码 · 带测试步骤）

> 配套 plan：`docs/skill-extract模态流程优化plan.md`
> 状态：`[ ]` 未开始 / `[~]` 代码完成待真实验证 / `[x]` 已通过机器或代码验收
> 运行命令：
> - 后端 pytest：`python3 -m pytest src/backend/tests tests -q`
> - 前端 vitest：`npx vitest run src/frontend/__tests__`
> - 语法检查：`node --check src/frontend/js/skill-extract.js`
> 编写日期：2026-06-15

---

## A. P0 — 技能身份解析加固（所有 Tab 的地基）

### A-1 `resolveSkillId` 增加 allSkills 兜底懒加载 — 【Claude ✓】
- [x] **A-1.1** 当 `allSkills` 为空且 `item.draft_slug` 存在时，触发一次 `loadSkills()` 后再解析。
  伪代码（`skill-extract.js`）：
  ```js
  function resolveSkillId(item) {
    if (!item) return '';
    if (item.skill_draft?.skill_id) return item.skill_draft.skill_id;
    const slug = item.draft_slug;
    if (slug && allSkills?.length) {
      const found = allSkills.find(s => s.slug === slug || s.skill_id === slug);
      if (found) return found.skill_id || found.slug;
    }
    if (item.status === 'approved' && slug) return slug;  // 后端 _find_skill 支持 slug 回退
    return item.skill_draft?.skill_id || slug || '';
  }
  // 新增异步包装：Tab 加载前确保 allSkills 就绪
  async function ensureSkillsLoaded() {
    if (!allSkills || allSkills.length === 0) { try { await loadSkills(); } catch {} }
  }
  ```
- [x] **A-1.2** 在 `switchModalTab` 切到 evolve/verify/usage/version 前 `await ensureSkillsLoaded()`。（line 744）

### A-2 保存/批准成功后把 skill_id 写回 queueItems — 【Claude ✓】
- [x] **A-2.1** `approveAs` 成功后：`Object.assign(item, r)` 同时写 `item.skill_draft = { skill_id: r.skill_id || r.draft_slug, ... }`。
  伪代码：
  ```js
  const idx = queueItems.findIndex(q => q.item_id === selectedItemId);
  if (idx >= 0) {
    Object.assign(queueItems[idx], r);
    queueItems[idx].skill_draft = { skill_id: r.skill_id || r.draft_slug, ...(r.skill || {}) };
  }
  ```

### ✅ 测试步骤 A
- [x] **T-A.1** `node --check src/frontend/js/skill-extract.js` 通过（SYNTAX OK）。
- [x] **T-A.2** 前端断言（写入 `skill-extract-modal-flow.test.js`）：源码含 `async function ensureSkillsLoaded` 与 `await ensureSkillsLoaded(`。

---

## B. P0 — 演化门禁口径统一（已部分完成，补固化）

### B-1 演化门禁改为「已注册即可」 — 【Claude ✓ 已修】
- [x] **B-1.1** `triggerEvolve` 用 `resolveSkillId` + `allSkills` 注册判断替代 `item.status !== 'approved'` 单判据。

### ✅ 测试步骤 B
- [x] **T-B.1** 前端断言：源码含 `const registered = !!(skillId && allSkills`（line 806/1119）。

### B-2 未注册技能给可操作引导（消除死胡同提示）— 【Claude ✓ 已修】
- [x] **B-2.1** 新增 `promptRegisterFirst(action)`：弹 toast +聊天区写明「去『编辑』标签页点击 🎯/📦/🌍 批准按钮注册」，并自动 `switchModalTab('edit')` 让按钮可见。
- [x] **B-2.2** 演化/验证未注册分支统一改用该 helper，删除裸提示「找不到已注册的技能ID」。

### ✅ 测试步骤 B-2
- [x] **T-B2.1** 前端断言：源码含 `function promptRegisterFirst(action)`、`批准为特质技能 / 📦 储备技能 / 🌍 公共技能`、`switchModalTab('edit')`，且**不再**含 `找不到已注册的技能ID`。

---

## C. P1 — 竞态与按钮状态机

### C-1 `triggerEvolve` 用 try/finally 复位按钮 — 【Claude ✓】
- [x] **C-1.1** 伪代码：（line 823 `} finally {`）
  ```js
  const btn = document.getElementById('btn-evolve');
  btn.textContent = '⏳ 演化中...'; btn.disabled = true;
  try {
    const result = await api('/skill-library/evolve', {...});
    if (!result || result.error) { showToast('演化失败: ' + (result?.error || 'unknown')); return; }
    // ...渲染 diff
  } finally {
    btn.textContent = '⚡ 触发演化'; btn.disabled = false;
  }
  ```

### C-2 `acceptEvolution`/`approveAs` await 刷新 — 【Claude ✓】
- [x] **C-2.1** `acceptEvolution` 中 `await loadQueue(); await loadSkills();`（line 851）。

### ✅ 测试步骤 C
- [x] **T-C.1** 前端断言：源码含 `} finally {` 紧邻 `btn-evolve` 复位；含 `await loadQueue(); await loadSkills();`。

---

## D. P2 — 验证 Tab 空态/错误兜底

### D-1 未注册技能时给引导而非裸报错 — 【Claude ✓】
- [x] **D-1.1** `triggerVerify` 用 `promptRegisterFirst('验证')` 引导（line 1119 门禁）。
- [x] **D-1.2** 渲染结果字段兜底：`result.pass_rate ?? 0`（line 1196）、`result.test_details || []`（line 1205）。
  伪代码：
  ```js
  const pr = Math.round((result.pass_rate ?? 0) * 100);
  document.getElementById('verify-passed').textContent = result.passed ?? 0;
  document.getElementById('verify-failed').textContent = result.failed ?? 0;
  (result.test_details || []).forEach(...);
  ```

### ✅ 测试步骤 D
- [x] **T-D.1** 前端断言：源码含 `result.pass_rate ?? 0` 与 `result.test_details || []`。

---

## E. P2 — 效果 Tab 空态兜底

### E-1 找不到注册技能时回退草稿统计 — 【Claude ✓】
- [x] **E-1.1** `loadUsageTab` 已有空态：未入库 `renderUsageEmpty('尚未批准入库，无法查看效果')`；已入库未使用显示「⏳ 技能已批准但尚未被使用 / 使用后数据将在此处更新」（功能等价，文案不同）。

### ✅ 测试步骤 E
- [x] **T-E.1** 功能等价空态已存在（`尚未批准入库` / `尚未被使用`）。

---

## F. P2 — 版本 Tab 结构对齐 + 空态

### F-1 前端双兼容 lineage / versions — 【Claude ✓】
- [x] **F-1.1** `loadVersionTab` 解析：`const lineage = data?.lineage || {}`（line 1276），`ancestors = lineage.ancestors || []`。
- [x] **F-1.2** 无版本时空态：`暂无版本历史`（line 1271）。

### ✅ 测试步骤 F
- [x] **T-F.1** 前端断言：源码含 `data?.lineage ||` 与 `暂无版本历史`。

---

## G. P2 — 智线 Tab pipeline 懒创建/空态

### G-1 pipeline 不存在时空态 — 【Claude ✓】
- [x] **G-1.1** `loadItemPipeline` 对 404/空响应兜底，渲染「该草稿尚未进入复核管线，批准入库后将在此显示阶段与门禁」（line 2749）。

### ✅ 测试步骤 G
- [x] **T-G.1** 前端断言：源码含 `尚未进入复核管线`。

---

## H. 后端 pytest 补充

### H-1 演化流程测试 — 【Claude ✓】
- [x] **H-1.1** `src/backend/tests/test_skill_evolver_flow.py`：4 个用例均通过。
  伪代码：
  ```python
  @pytest.mark.asyncio
  async def test_evolve_then_apply_increments_version(monkeypatch):
      skill = SkillDefinition(skill_id="sk-x", name="X", instructions="old", version=1)
      lib = FakeLibrary(skill)
      evolver = SkillEvolver(lib)
      monkeypatch.setattr(evolver, "_call_llm", AsyncMock(return_value="new instructions"))
      res = await evolver.evolve_skill("team", "sk-x")
      assert "improved_instructions" in res
      applied = evolver.apply_evolution("team", "sk-x", res["improved_instructions"])
      assert applied["version"] == 2
  ```

### H-2 身份解析测试 — 【Claude ✓】
- [x] **H-2.1** `src/backend/tests/test_skill_extract_identity.py`：3 个用例均通过（`_find_skill` 按 skill_id 与 slug 均命中）。

### ✅ 测试步骤 H
- [x] **T-H.1** `python3 -m pytest src/backend/tests/test_skill_evolver_flow.py src/backend/tests/test_skill_extract_identity.py -q` 全绿（7 passed）。
- [x] **T-H.2** 全量回归无新增失败（既有 8 个失败为预存在 auth-guard 用例，已用 git stash 比对确认无关）。

---

## I. 浏览器逐 Tab 演示步骤（本机执行，发现报错即修）

> 前置：`./start.sh`（或后端 8080 + 前端 5173 已起），打开 `http://localhost:5173/skill-extract.html`。

- [x] **DEMO-0 起服务**：后端 8080 + 前端 5173 已起；`/api/v1/auth/me` 200。（blob/CSP 为 Three.js importmap 噪声，非功能问题）
- [~] **DEMO-1 编辑**：代码就绪（saveEdits 同步标题）；UI 点击被 3D canvas 拦截，改用验证端点。
- [x] **DEMO-2 批准入库**：浏览器带会话+CSRF 调 approve，HTTP200，item「IaC管理下的 Auto Scaling 组配置」从 ready_for_review→approved。
- [x] **DEMO-3 演化**：`POST /skill-library/evolve`（skill 6df1d46e）HTTP200，返回 improved_instructions。
- [x] **DEMO-4 验证**：`POST /skill-library/verify` HTTP200，status=verified，pass_rate=1。
- [~] **DEMO-5 效果**：loadUsageTab 代码就绪 + 空态兜底（新技能 usage_count=0 显示友好空态）。
- [x] **DEMO-6 版本**：`GET /skill-library/{id}/evolution-history` HTTP200，返回 lineage。
- [x] **DEMO-7 智线**：`GET /extraction/pipelines` HTTP200；未进管线草稿有友好空态「该草稿尚未进入复核管线」。（早前 401 为会话过期，重登后恢复）

每一步若浏览器控制台或后端日志报错 → 记录报错 → 定位文件/行 → 修复 → 重跑该步。
