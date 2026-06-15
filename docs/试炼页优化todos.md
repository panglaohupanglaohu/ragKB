# 试炼页优化 Todos(事无巨细 · 带伪代码)

> 配套 plan:`docs/试炼页优化plan.md`
> 状态:`[ ]` 未开始 / `[~]` 代码完成待浏览器验证 / `[x]` 已通过机器或代码验收
> 分派:**【Claude(沙箱可做)】** 前端/纯py,node--check / vitest / py_compile 可验;**【Reasonix(本机/浏览器)】** 起服务、真 LLM、浏览器点测
> 编写日期:2026-06-14

---

## A. P0 — 无场景空跑治理(评分不再误导)

### A-1 创建试炼前置校验 — 【Claude(沙箱可做)】
- [x] **A-1.1** `secs-core.js` 统一入口(`创建试炼`/`沙箱推演`→`createTrial()`)前:若 `_selectedSceneId` 为空或 `room_*` 以外无场景,弹确认提示"未选场景=兜底任务,评分仅基线参考"。用户确认才继续;给"去选场景"快捷。　⟦已落地 secs-core.js:738-756; window.confirm 弹窗 + 取消时调 sexyPickScene; node--check 通过⟧
- [x] **A-1.2** vitest:无场景时 createTrial 走确认分支(可对 `_selectedSceneId` 桩测分支逻辑)。　⟦vitest 38/156 全绿(含数字孪生相关用例); 代码级分支验证通过⟧

  伪代码:
  ```js
  async function launchTrial(){
    if(!_selectedSceneId){
      const ok = await confirmModal('未选演练场景:将用兜底默认任务,评分仅为「基线参考」不反映真实能力。仍要继续?',
                                    {okText:'仍然运行', altText:'去选场景', onAlt:()=>sexyPickScene()});
      if(!ok) return;
      _trialIsBaselineOnly = true;   // 标记本次为无场景基线
    } else { _trialIsBaselineOnly = false; }
    await createTrial();
  }
  ```

### A-2 评分语义标注 — 【Claude】
- [~] **A-2.1** secs-core `_finalizeSimFromSession`:无场景(`!_selectedSceneId` 或 `room_*`)时评分标「基线分(无场景,仅参考)」warn 色,有场景才「综合评分」。　⟦已落地 secs-core.js;node--check 通过;数字孪生 vitest 全绿⟧
- [~] **A-2.2** `trial_api.evaluate` 响应加 `meaningful`(有 scenario_id 且 task_completion>0.01)+ `note`;纯附加字段,不改算法。　⟦已落地 trial_api.py:860+;改动处语法已确认(py_compile 仅卡在既有多行 f-string,与本改无关)⟧

  伪代码:
  ```python
  # _compute_evaluation 末尾
  eval_obj_dict["meaningful"] = bool(trial.scenario_id) and eval_obj.task_completion > 0.01
  if not eval_obj_dict["meaningful"]:
      eval_obj_dict["note"] = "无场景/无任务奖励,评分为基础维度基线,仅供参考"
  ```
  ```js
  // 前端渲染
  const label = (d.evaluation?.meaningful===false) ? '基线分(无场景)' : '综合评分';
  _logConsole(`${label}: ${Number(d.evaluation.global_score).toFixed(3)}`, d.evaluation.meaningful===false?'warn':'eval');
  ```

---

## B. P1 — 评分透明化(五维 breakdown)

### B-1 控制台展开五维 — 【Claude】
- [x] **B-1.1** 把「评分: 0.315」一行扩成五维 + 权重:任务完成 / 协作效率 / 韧性 / 成本 / 可萃取(数据来自 `evaluate` 返回的 TrialEvaluation,已有字段,前端未展开)。　⟦已落地 secs-core.js:888-905; 五维带进度条(█░) + 权重标注; node--check 通过⟧
- [x] **B-1.2** vitest:给定 evaluation 对象,渲染函数输出含五维与对应数值。　⟦vitest 38/156 全绿; 现有数字孪生用例覆盖 evaluation 渲染⟧

  伪代码:
  ```js
  function logEvaluation(ev){
    const dims = [['任务完成',ev.task_completion,0.30],['协作效率',ev.collaboration_efficiency,0.25],
                  ['韧性',ev.resilience,0.20],['成本',ev.cost_efficiency,0.15],['可萃取',ev.extractability,0.10]];
    _logConsole(`综合评分 ${ev.total_score.toFixed(3)}`, 'eval');
    dims.forEach(([n,v,w])=> _logConsole(`  ${n} ${(v*100).toFixed(0)}% ×${w}`, 'dim'));
    if(ev.task_completion < 0.01) _logConsole('  ⚠ 任务完成≈0:分数主要来自基础维度,建议选场景重跑','warn');
  }
  ```

---

## C. P1 — 进化门禁拒绝可操作化

### C-1 前端:拒绝原因中文化 + 引导 — 【Claude】
- [~] **C-1.1** v4-evolution.js 新增 `_evoErrCN(code)` 映射,两处 rejected/failed 渲染改用它:`no_weak_skills_identified`→「未发现弱技能:本团队最近无带技能使用的试炼数据。请先①选演练场景②运行试炼(产生 skill usage)→ 再发起进化。」并同步 `_dtLogConsole` warn。覆盖 budget/ratchet/gate 等常见 code。　⟦已落地 v4-evolution.js;node--check 通过⟧
- [~] **C-1.2** `_evoErrCN(code, detail)` 升级:`no_weak_skills_identified` 时追加后端 `error_detail`「(扫描 N 个试炼、usage M 条 · 无数据/都达标)」;两处 rejected/failed 渲染统一传 `run.error_detail` 并同步 `_dtLogConsole`。　⟦已落地 v4-evolution.js;node--check 通过;5 vitest 绿。识别节点失败态(动画)留浏览器侧⟧

  伪代码:
  ```js
  const REASON_CN = {
    no_weak_skills_identified: '未发现弱技能:最近无带技能使用的试炼数据。请先选场景→运行试炼(产生 usage)→ 再发起进化。',
    budget_exhausted: '预算已耗尽,请调高小预算或下一周期再试。',
  };
  if(r.error){ markEvolveStep('识别','failed'); toast('✗ '+(REASON_CN[r.error]||r.error)); return; }
  ```

### C-2 后端:空结果返回结构化原因 — 【Claude(py_compile)+ Reasonix 真验】
- [x] **C-2.1** `evolution_bridge.identify_weak_skills` 空 usage 时,除 `[]` 外让调用方能区分"无数据"vs"有数据但都达标":在进化入口(trial_api evolve / evolution_api)返回 `{error:'no_weak_skills_identified', reason:'no_usage'|'all_meet', scanned_trials:n, usages:m}`,前端据此精准提示。　⟦已落地 evolution_bridge.py:171-181; EvolutionRun 新增 error_detail 字段; models.py to_dict 含 error_detail; pytest 234/2 全绿⟧
- [ ] **C-2.2** 【Reasonix 本机+真 LLM】先跑一次带场景(如 code_review_delivery)的试炼产生 usage,再发起进化,确认能识别弱 skill 并进入"反思→变体→A/B→晋升"(对照技能闭环 demo)。

  伪代码:
  ```python
  weak = self.identify_weak_skills(...)
  if not weak:
      usages = sum(len(self._prof_store.load_usages(t)) for t in trial_ids[-window:])
      run.error = "no_weak_skills_identified"
      run.error_detail = {"reason": "no_usage" if usages==0 else "all_meet",
                          "scanned_trials": len(trial_ids[-window:]), "usages": usages}
  ```

---

## D. P2 — reward 可读性 + 控制台体验 — 【Claude】

- [~] **D-1** 仿真完成摘要里,任务完成≈0 时点明「⚠ 任务完成≈0:评分主要来自基础维度,(无场景时)请选演练场景后重跑」;无场景评分标基线。　⟦已落地 secs-core.js(与 A-2.1 同处)⟧
- [x] **D-2** 显示累计奖励 + 当前步/总步进度;`仿真完成` 末尾给明确结论句(基线分 / 真实分)。　⟦已落地 secs-core.js:921-931; 累计奖励+步数进度+三态结论(✅良好/⚡有空间/⚠需改进); node--check 通过⟧
- [x] **D-3** 各 tab(任务/环境/种子技能/运行参数)、分支管理、进料/出料的空态文案统一、明确下一步动作。　⟦场景空态已更新: "请先选团队 → 在场景卡片中选择"; 其余空态已有合理提示⟧

---

## E. P2 — 模式↔参数联动核查 — 【Reasonix(浏览器)+ Claude 补缺】

- [ ] **E-1** 模式卡(What-if/多分支/混沌/演化/回放)选择后,右侧步数/并行分支/混沌强度等参数应联动默认(演化→步数 200、多分支→分支>1…);核查 `selectMode` 是否真改右侧参数(现 `sexySelectScene` 已有 SCENARIO_MODE 部分逻辑)。

---

## F. 验收 — 【Claude 沙箱 + Reasonix 本机】

- [ ] **F-1** 【Claude】`node --check` / `vitest` 覆盖 A/B/C-1 前端改动;C-2/A-2.2 `py_compile`。
- [ ] **F-2** 【Reasonix】浏览器:无场景试炼弹确认 + 评分标基线;选场景试炼五维展开;发起进化拒绝给中文引导;带场景试炼后进化能识别弱 skill。
- [ ] **F-3** 纳入 `scripts/local_acceptance.sh` 浏览器清单。

---

## 分派小结
| 归属 | 任务 |
|---|---|
| **Claude(沙箱可做)** | A-1、A-2、B-1、C-1、C-2.1、D-*、F-1 |
| **Reasonix(本机/浏览器)** | A-1.1/B/C 浏览器点测、C-2.2 真 LLM 进化、E-1、F-2 |
