# 演进式成本优化「收口2」TODOS（事无巨细 + 伪代码）

> 配套 `docs/演进式成本优化收口2plan.md`。本轮 = 前端两处"下一步引导"缺口；重后端项单列延后。
> 标注：**[VSCode]** 机械低风险；**[人工核]** 需联机；**[需后端]** 要改后端 + 重启。

## T1 · 效率视角每团队「该动哪个杠杆」链接 ★★ [VSCode]（cost-dashboard.js renderEfficiencyView）
- [ ] 在 leverBar 之后，为**有消耗**的团队按主导杠杆追加一行下一步链接。
```js
var _pct=function(x){return Math.round((x||0)*100);};
var hasSpend = Number(team.tokens_consumed||0) > 0;
var leverHint = '';
if (hasSpend && ((lc.skill||0)+(lc.collab||0))>0){
  var skillHeavy = (lc.skill_pct||0) >= (lc.collab_pct||0);
  leverHint = skillHeavy
    ? '<div class="lever-next" style="font-size:10px;color:var(--sumi-3);margin-top:2px">技能杠杆重('+_pct(lc.skill_pct)+'%) → <a href="/skill-extract.html" style="color:var(--koke);text-decoration:none">去技能萃取固化重复 skill▸</a></div>'
    : '<div class="lever-next" style="font-size:10px;color:var(--sumi-3);margin-top:2px">协作杠杆重('+_pct(lc.collab_pct)+'%) → <a href="/plaza.html" style="color:var(--koke);text-decoration:none">去议事广场复盘协作▸</a></div>';
}
// 追加到 efficiency-team 单元格：... + leverBar + leverHint
```
- **验收**：技能占比高的行现"去技能萃取"，协作占比高现"去议事广场"，点击跳转。

## T2 · 效率视角「低效优先」排序 + 切换 ★ [VSCode]
- [ ] 默认排序改为「最需优化优先」：有消耗且效率最低在前，`no_data`（无消耗）沉底。
```js
state.effSort = state.effSort || 'worst';
function _effRank(t){var e=Number(t.token_efficiency||0);var spend=Number(t.tokens_consumed||0);
  if(spend<=0) return {g:2,v:0};            // 无消耗沉底
  return {g:0, v: state.effSort==='worst'? e : -e};}  // worst:升序 best:降序
teams.sort(function(a,b){var ra=_effRank(a),rb=_effRank(b); return ra.g-rb.g || ra.v-rb.v;});
```
- [ ] 面板标题旁加小按钮切换 `worst⇄best`，切换后 `renderEfficiencyView(state.sustainability)` 重渲染。
- **验收**：默认第一行=有消耗效率最低团队；切到「效率最高」回到最优在前；无数据团队始终垫底。

## T3 · 验收 ★ [VSCode]
- [ ] `node --check src/frontend/js/cost-dashboard.js` 通过；控制台无报错。
- [ ] 目检：效率视角链接跳对页；排序切换生效。

## 延后（[需后端] + [人工核]，见 plan 第 3 节）
- 13.1 归因零遗漏（4 路径强制 team_id）
- 13.4 Gate 运行时拦截（drill/批量前过闸 + warn 自动建议题）
- 13.5 优化任务完成后同意图复跑 before/after 回写
- 13.6 优化任务带 team_id 可见 + 目标进度同源棘轮

## 落地顺序
```
T1(杠杆下一步链接) → T2(低效优先排序) → T3(node --check + 目检)
```
