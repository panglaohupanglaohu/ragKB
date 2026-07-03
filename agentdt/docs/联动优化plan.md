# 跨面板/跨页面 联动优化 Plan

> 起因:用户实测发现系统中存在大量"应联动而未联动"的选择项。例:数字孪生页左侧选了 Build System,右侧「选择演练团队」不变;环境空间是议事厅,右侧「选择演练场景」不跟随。
> 目标:系统性梳理所有"共享选择上下文",定义单一数据源 + 生产者→消费者联动规则,逐一补齐。
> 编写日期:2026-06-14
> 分派:**【Claude(沙箱可做)】** = 前端联动代码,node--check / vitest 可验证;**【Reasonix(本机/浏览器)】** = 浏览器逐项点测、跨页面真验证。

---

## 0. 问题本质:同一"选择上下文"被多处各自存一份,改一处不通知其他

经代码核查,系统里同一语义的选择被**多套互不知情的状态**重复持有,典型是"当前团队":

| 上下文 | 数字孪生页 | skill-extract | plaza | 跨页面 |
|---|---|---|---|---|
| **当前团队** | `S.selectedTeams`(左·多选) / `_selectedTeamId`(右SECS·单选) / `localStorage 'selected_team'`(CLI) — **三套** | `currentTeamId` + 顶栏 team-chips | 自有 team 选择 | 各页独立,**不共享**(切团队不跨页带过去) |
| **当前房间/场景** | `_3dCurrentRoom` / `window._currentRoomId` / SECS `_selectedSceneId` | — | — | — |
| **当前 agent** | `S.selected*` / SECS `skill-inject` | `selectedAgentId`(赋予页) | — | — |
| **当前讨论** | — | `extract_source`(来自 plaza 跳转) | `curDisc` | 靠 URL 参数传递 |

改一处不广播 → 出现用户看到的"左选了、右没动"。

---

## 1. 已修(本轮 Claude 落地)— 数字孪生页 团队/场景 联动

经核查,**SECS → 左**早已联动(`sexySelectTeam` 会回写 `S.selectedTeams`+飞房间),但**左 → SECS** 与 **环境空间 → SECS 场景**缺失。

- **左侧团队 → 右侧 SECS「选择演练团队」**:`toggleTeam` 选中团队后,调 `window.secsSyncTeamFromLeft(teamId)`(secs-core.js 新增,单向更新 SECS 团队按钮 + 技能注入选项 + 启动按钮,不回灌左侧避免循环)。
- **环境空间房间 → 右侧 SECS「选择演练场景」**:`switchRoom`/`showRoom` 切到议事厅等房间时,调 `window.secsSyncSceneFromRoom(roomId)` → 把场景默认跟随为 `room_<id>`(仅当用户未手动选过具体场景时,不覆盖显式选择)。场景体系本就支持 `room_` 前缀,故房间↔场景可直接映射。
- 验证:`node --check` 通过;数字孪生 vitest 16/16 全绿。浏览器逐项点测留本机。

> 说明:左侧是"多选团队"、右侧 SECS 是"单团队演练";联动规则取"刚选中的团队 / 取消后剩余的第一个"为 SECS 团队,符合"我选了 Build System 右边就该是 Build System"的直觉。

---

## 2. 待补联动(详见 todos)

### 2.1 数字孪生页内部"当前团队"三套统一(P1, Claude)
`selected_team`(localStorage)、`S.selectedTeams`、`_selectedTeamId` 收敛:以一个 helper 读/写当前团队,三处保持一致;CLI `set team` 也广播到左右面板。

### 2.2 跨页面"当前团队"共享(P1)
切换团队应跨页保持:用 `localStorage` 统一键(如 `ag_current_team`)+ `storage` 事件广播。各页加载时读它作为默认团队;顶栏 team-chips 切换时写它。

### 2.3 各页内其它跨面板联动核查(P2, 逐页点测)
- skill-extract「赋予」页:目标 agent 选择 ↔ 技能画像雷达 ↔ 路由结果(已部分联动,核查 agent 切换是否刷新画像)。
- plaza:选广场 ↔ 讨论列表 ↔ 3D 参与者(已联动,回归确认)。
- system-evolution:面板间 deep-link(item_id/panel)是否生效。

---

## 3. 推荐的统一机制(避免以后再漏)

引入极轻的"选择上下文总线"(无需框架):

```js
// shared selection context — 单一数据源 + 订阅广播 + 跨页持久化
window.AGCtx = {
  _s: { team:'', room:'', agent:'', scenario:'' },
  _subs: [],
  set(k, v){ if(this._s[k]===v) return; this._s[k]=v;
    try{ localStorage.setItem('ag_ctx_'+k, v); }catch(e){}
    this._subs.forEach(fn=>{ try{ fn(k, v); }catch(e){} }); },
  get(k){ return this._s[k] || localStorage.getItem('ag_ctx_'+k) || ''; },
  on(fn){ this._subs.push(fn); },
};
// 跨页:storage 事件把别的标签页/页面的改动同步进来
window.addEventListener('storage', e=>{ if(e.key?.startsWith('ag_ctx_')) AGCtx.set(e.key.slice(7), e.newValue); });
```

各面板:选择时 `AGCtx.set('team', id)`;关心团队的面板 `AGCtx.on((k,v)=>{ if(k==='team') 刷新自己 })`。这样新增面板只需订阅,不会再漏联动。属较大重构,作为 P1 演进项,先用 §1/§2 的点对点联动补齐当前可见缺口。

---

## 4. 实施顺序
1. ✅ 数字孪生 左↔右 团队、环境空间↔场景(本轮已落地)
2. 数字孪生内部三套"当前团队"统一(Claude)
3. 跨页面当前团队共享(Claude 前端 + Reasonix 跨页点测)
4. 逐页跨面板联动点测与补漏(Reasonix)
5. (演进)引入 `AGCtx` 选择上下文总线统一治理

详见 `docs/联动优化todos.md`。
