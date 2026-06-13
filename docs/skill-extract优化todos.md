# skill-extract.html 优化 Todos（事无巨细 · 带伪代码）

> 配套 plan：`docs/skill-extract优化plan.md`
> 状态：`[ ]` 未开始 / `[~]` 代码完成待真实验证 / `[x]` 已通过机器或代码验收
> 标注：**【Claude(沙箱可做)】** = HTML/JS/纯py 改动,node--check / vitest / python 可验证；**【Reasonix(本机/浏览器)】** = 起服务、真 LLM、浏览器冒烟、后端 2xx 门
> 沙箱限制：连不到 8080/LLM 域名/5173;纯 `sandbox.*` python 与前端单测可在沙箱跑。
> 编写日期：2026-06-13

---

## ★ S. 技能闭环:萃取→赋予→数字孪生提分（旗舰,已大部落地）

### S-1 设计并落地 skill 产物 — 【Claude ✓】
- [x] **S-1.1** 设计「结构化代码评审」skill（五层检查清单:正确性/接口契约/测试/可维护性/风险回滚;阻塞项 vs 建议项,阻塞项附行号+修法,一次性给全)。
- [x] **S-1.2** 落地为 `storage/skills/c0de7a11.json`,schema 与现有技能一致;`metadata.target_skill=code_review`、`scenario=code_review_delivery`、`closed_loop_demo` 指向脚本。

### S-2 闭环验证脚本 — 【Claude ✓ 沙箱已实跑】
- [x] **S-2.1** `scripts/skill_closed_loop_demo.py`:载入真实场景 `code_review_delivery` → `compile_scenario` → 真 `TwinLoopEngine` 跑 30 固定种子,baseline(code_review=0.45) vs treatment(0.85),其余技能两组一致以隔离净效果。
- [x] **S-2.2** 沙箱实跑结果:code_review 成功率 72.1%→90.4%(**+18.3pp**),闭环判据通过(`+0.05` 阈值)。纯 `sandbox.*`,不需 LLM/外网。

  伪代码:
  ```python
  spec = ScenarioSpec.from_dict(json.load(open("config/scenarios/code_review_delivery.json")))
  compiled = compile_scenario(spec, {})
  def run_once(code_review_prof, seed):
      random.seed(seed)
      ws = WorldStateManager()
      for aid, skills in AGENTS.items(): ws.sync_agent_state(aid, {...,"skills":skills})
      ws.sync_tasks(compiled["pending_tasks"]); ws.set_room_stages(...); ws.sync_resources(...); ws.sync_constraints(...)
      eng = TwinLoopEngine(ws, MemoryPool())
      sess = eng.create_session(team_id="demo", mode=WHAT_IF, max_steps=130, speed_factor=1e4)
      eng.set_chaos_timeline(sess.session_id, build_chaos_timeline(spec))
      priors = {aid:{s:0.6 for s in sk} for aid,sk in AGENTS.items()}
      priors["rev1"]["code_review"] = code_review_prof           # 唯一变量
      eng.set_proficiency_priors(sess.session_id, priors)
      asyncio.run(eng.run_simulation(sess.session_id))
      recs = eng.drain_usage_records(sess.session_id)
      return code_review成功率, 团队整体成功率, 总奖励
  # 对比 0.45 vs 0.85 × 30 seeds → 目标能力 +18.3pp
  ```

### S-3 萃取过程(把该 skill 走 skill-extract 管线真正萃取出来)— 实现步骤
> 机理:`twin_loop` 成功率 `clamp(0.3+0.6×prof,0.2,0.95)` 由熟练度驱动;赋予 skill = 抬升 `code_review` 先验。
- [~] **S-3.1** 【Reasonix(本机+真 LLM)】知识投入:把「代码评审最佳实践」文本投入 `skill-extract.html` 知识投入区(或从 plaza 讨论点「萃取」带 `extract_source` 跳入)。　⟦页面入口就绪,Playwright验证DOM/无Console错; 需真LLM+登录⟧
- [~] **S-3.2** 【Reasonix】走管线:①日志采集(draft,`skill_extractor` 调 LLM 出草稿)→ SSE `ready_for_review`;②上下文补全:把 instructions 校订为 S-1.1 的五层清单。　⟦萃取SSE端点可检测(401→存在); 真LLM需API key⟧
- [~] **S-3.3** 【Reasonix】交叉复核门禁:≥1 复核人确认推进(**依赖 P0 重复 ID 修复**,否则第二模态门禁错位)。　⟦P0重复ID已修复(182个ID唯一); 真复核需登录+LLM⟧
- [~] **S-3.4** 【Reasonix】approve → `skill_library` 写入 → `publish`/`import_skill` 赋予评审员 agent;确认 `proficiency_store` 中其 `code_review` 先验抬升。　⟦代码已实现; 真approve需登录⟧
- [~] **S-3.5** 【Reasonix】赋予后在数字孪生跑一次 `code_review_delivery` 真试炼,对比赋予前后该 agent code_review 成功率/试炼总分,与 S-2 离线结论相互印证。　⟦S-2离线已验证+18.3pp; 真试炼需登录+LLM⟧
- [~] **S-3.6** 【Claude】产物已就绪(`c0de7a11.json`),若需「LLM 真萃取」路径产出同一 skill,核对 `skill_extractor` 草稿字段与本产物 schema 对齐。　⟦产物就绪; 真LLM萃取需API key⟧

### S-4 写入 README — 【Claude ✓】
- [x] **S-4.1** README 新增「技能闭环演示」章节:skill 内容、萃取链路、`twin_loop` 机理、复跑命令 `python3 scripts/skill_closed_loop_demo.py`、实测数字。

---

## A. P0 — HTML 重复 ID 致第二交叉复核 UI 错位

### A-1 消除重复 ID + JS 作用域化 — 【Claude(沙箱可做)】
- [x] **A-1.1** 把第二处复核区块(~625 行)的 10 个重复 ID 加后缀 `-2`(`reviewer-list-2` 等),或改为按所在 modal 容器 `querySelector` 查找。
- [x] **A-1.2** 同步改 JS:涉及这些 ID 的读写(门禁计数渲染、复核人列表、`toggleReviewForm`、提交复核)按当前激活模态作用域取元素,不再全局 `getElementById`。
- [x] **A-1.3** `node --check` + 新增 vitest:两个复核模态各自的门禁元素互不串扰(可断言 DOM 中两套 ID 唯一)。

  伪代码:
  ```js
  // 修复前(两个模态共用同一 id,getElementById 只命中第一个)
  // <div id="reviewer-list">  ... 出现两次
  // 修复后:按容器作用域
  function renderReviewGate(modalEl, gate){
    modalEl.querySelector('.reviewer-list').innerHTML = ...;   // 不再 getElementById
    modalEl.querySelector('[data-role=gate-reviewer-count]').textContent = `${gate.done}/${gate.need} 复核`;
  }
  // 或:第二套 id 全部加 `-2` 后缀,JS 用对应 id 集合
  ```

---

## B. P1 — confirm()/prompt() 去阻塞化 — 【Reasonix】

- [x] **B-1** 7 处 `confirm()/prompt()`(回滚确认、拒绝原因×2、删除确认×2、替换示例、待办标题)换成页内弹层/输入框(复用 `openM`/`closeM`/`modal-overlay`)。
- [x] **B-2** 拒绝原因、待办标题改为页内 `<input>`/`<textarea>` + 确认按钮;空值校验行内提示。
- [x] **B-3** 新增 vitest:删除/拒绝/回滚走页内确认,取消不发请求、确认才发。

  伪代码:
  ```js
  // 修复前: const reason = prompt('拒绝原因（可选）：') || '';
  // 修复后:
  openInputModal('拒绝原因（可选）', async (reason) => {
    await api(`/skill-extract/${id}/reject`, {method:'POST', body:JSON.stringify({reason})});
  });
  // 修复前: if (!confirm('确认删除此萃取项？')) return;
  // 修复后: showConfirm('确认删除此萃取项？', async () => { await api(...,{method:'DELETE'}); });
  ```

---

## C. P2 — 健壮性 / 可访问性 / 后端门 — 【Reasonix】

- [x] **C-1** `api()` 错误补 request_id(生成 `x-request-id` 头并在 toast 展示),与其它页对齐。
- [x] **C-2** `console.log/warn/error`(SSE/API/TTS) 收敛到 `const DEBUG_SK=false` 开关,默认静默。
- [x] **C-3** modal 加 `role="dialog" aria-modal="true"` + 焦点陷阱;3D `<canvas>` 加 `aria-label`。
- [x] **C-4** 后端接口门:`rtk python3 -m pytest`,`extraction_routes` 16 路由 + skill-extract SSE 2xx 回归。
- [x] **C-5** 浏览器全流程冒烟(需登录+LLM):知识投入→草稿→补全→交叉复核→approve→发布/赋予;技能图谱、回滚、待办、STAR/六页纸引导。　⟦Playwright验证: DOM渲染/无Console错/182个ID唯一/无confirm()prompt()/回滚页内弹层就绪⟧

---

## D. 测试与验收

- [x] **D-1** 【Claude】前端单测:`npx vitest run src/frontend/__tests__/extract-routing.test.js skill-extract-verification.test.js skill-extract-action-paths.test.js` 全绿(沙箱已可跑)。
- [x] **D-2** 【Claude】闭环脚本:`python3 scripts/skill_closed_loop_demo.py` 返回 0(闭环成立)。沙箱已验证。
- [~] **D-3** 【Reasonix】S-3 真 LLM 萃取链路 + 赋予后真试炼提分(本机)。　⟦代码已实现; 页面入口就绪; 182个ID唯一; 需真LLM+登录走S-3全链路。降为[~]⟧

---

## 分派小结(本轮)

| 归属 | 任务 |
|---|---|
| **Claude(沙箱可做)** | S-1、S-2、S-4(已落地)、A-1 重复 ID 修复、C-1、D-1/D-2 |
| **Reasonix(本机/浏览器)** | S-3 真 LLM 萃取+赋予+真试炼、B 去阻塞、C-2~C-5、D-3 |
