<!-- docs-signoff: author="Copilot" kind="llm" doc="todos" ts="2026-07-06T21:22:22Z" -->
# 宠物团队生态仿真 Todos — Predator / Prey 行为模型

> 配套 [宠物团队生态仿真plan.md](宠物团队生态仿真plan.md)。
> 状态：`[ ]` 待办 / `[~]` 进行中 / `[x]` 完成。
> **责任标注**：`⟦CodeBuddy⟧` = CodeBuddy 已完成的可插拔地基；`⟦Copilot⟧` = 本次 Predator/Prey 行为模型改造（我干的）。

---

## Phase 0: 可插拔地基（CodeBuddy 已完成，本次不重做）

- [x] **PE-1** `storage/pet_config.json` — 默认配置（猫小虎 + 吱吱，含模型/行为/台词/语音全参数） ⟦CodeBuddy⟧
- [x] **PE-2** `src/backend/agents/pet_ecosystem.py` — PetEcosystem 管理器（加载/保存/CRUD + 深度合并 + 单例） ⟦CodeBuddy⟧
- [x] **PE-3** `src/backend/agents/pet_routes.py` — REST API（GET config / PUT·POST·DELETE pets / PUT ecosystem，5 端点） ⟦CodeBuddy⟧
- [x] **PE-4** `main.py` 挂载 pet_routes 路由 ⟦CodeBuddy⟧
- [x] **PE-5** `pet-config.js` — 配置页 JS（加载/渲染/保存/删除/新增/互动矩阵，内联于 pet-config.html） ⟦CodeBuddy⟧
- [x] **PE-6** `src/frontend/pet-config.html` — 配置页 HTML（全参数表单 + 路线编辑器 + 互动矩阵 + vite 注册） ⟦CodeBuddy⟧
- [x] **PE-7** `pet-factory.js` — 模型工厂 `buildPet(config)`（替代 buildCat/buildMouse，全参数从 config 读取） ⟦CodeBuddy⟧
- [x] **PE-8** `pet-behavior.js` — 行为 AI v1（硬编码 patrol/flee/chase + 警告光圈 + 台词触发） ⟦CodeBuddy⟧
- [x] **PE-10** `pet-ecosystem.js` — 生态管理器（init 从后端加载配置 / step / pick / onDetect→LLM→TTS） ⟦CodeBuddy⟧

---

## Phase A: 配置 Schema 扩展（Predator/Prey）

> 目标：把论文的心理状态/感知/意图参数落到配置，向后兼容（缺省退回旧 patrol/flee）。

- [x] **PP-1** 小虎（predator）配置扩展 ⟦Copilot⟧
  文件：[storage/pet_config.json](../storage/pet_config.json) — `pets[0]`（id=`xiaohu_cat`）
  落点：在现有 `model`/`behavior`/`speak`/`voice`/`click_action` **同级**新增 3 个块（`behavior.route` 保留作巡游路线）：
  ```jsonc
  "role": "predator",
  "perception":   { "detect_radius": 6.0, "vision_cone_deg": 300 },
  "mental_state": { "hunger_full_sec": 20, "hunt_hunger_threshold": 0.3 },
  "intention":    { "beta_turn_cost": 0.2, "persistence_threshold": 1.5, "catch_radius": 0.8 }
  ```
  验收：`python3 -c "import json;c=json.load(open('storage/pet_config.json'));p=c['pets'][0];assert p['role']=='predator' and p['intention']['catch_radius']==0.8"`

- [x] **PP-2** 吱吱（prey）配置扩展 ⟦Copilot⟧
  文件：同上 — `pets[1]`（id=`squeak_mouse`）
  落点：新增（保留 `behavior.route`/`flee_speed_multiplier`）：
  ```jsonc
  "role": "prey",
  "perception":   { "detect_radius": 6.0, "vision_cone_deg": 300 },
  "mental_state": { "fear_scale_D0": 6.0, "f_escape": 0.55, "f_calm": 0.35 }
  ```
  验收：`python3 -c "import json;c=json.load(open('storage/pet_config.json'));p=c['pets'][1];assert p['role']=='prey' and p['mental_state']['f_escape']>p['mental_state']['f_calm']"`

- [x] **PP-3** 后端合并兼容新字段 ⟦Copilot⟧
  文件：[src/backend/agents/pet_ecosystem.py](../src/backend/agents/pet_ecosystem.py) — `_deep_merge`（已递归，本任务只加**校验+默认**）
  落点：在 `get_config()` 返回前，为每个 pet 补全缺省块（不写回磁盘，仅内存补全）：
  ```python
  _PET_DEFAULTS = {
      "role": "prey",
      "perception": {"detect_radius": 6.0, "vision_cone_deg": 300},
      "mental_state": {"hunger_full_sec": 20, "hunt_hunger_threshold": 0.3,
                        "fear_scale_D0": 6.0, "f_escape": 0.55, "f_calm": 0.35},
      "intention": {"beta_turn_cost": 0.2, "persistence_threshold": 1.5, "catch_radius": 0.8},
  }
  def get_config(self):
      for pet in self._config.get("pets", []):
          for k, dv in _PET_DEFAULTS.items():
              if isinstance(dv, dict):
                  pet[k] = {**dv, **pet.get(k, {})}   # 用户值覆盖默认
              else:
                  pet.setdefault(k, dv)
      return self._config
  ```
  验收：`python -m py_compile src/backend/agents/pet_ecosystem.py`；对一个**无新字段**的旧配置调用 `get_config()`，断言补全后 `pet["intention"]["catch_radius"]==0.8`（写进 `tests/` 现有 pet 测试或临时 `-c` 脚本）。

## Phase B: 行为内核重写（意图生成器）— pet-behavior.js

> 文件：[src/frontend/js/office/pet-behavior.js](../src/frontend/js/office/pet-behavior.js)
> 把当前 `createBehavior().step()` 的硬编码巡逻/逃跑，重构为
> **心理状态更新 → 意图生成（优先级 + 单项记忆）→ 行为例程 → 运动动画**。
> `ctx` 由 `pet-ecosystem.js` 传入 `{ allPets, onDetect }`，`allPets[id]` 含 `.group` 与 `.config`（有 `role`）。
> 动画函数 `_walkAnimate/_idleAnimate` 已存在，直接复用。

- [x] **PP-4** 心理状态更新（Hunger H / Fear F，论文 §4.2） ⟦Copilot⟧
  落点：`createBehavior` 内新增闭包 `state` + `updateMentalState(dt,t,ctx)`：
  ```js
  const role = config.role || (config.behavior?.chase_targets?.length ? 'predator' : 'prey');
  const percep = config.perception||{}, ms = config.mental_state||{}, intent = config.intention||{};
  const state = { hunger:0, fear:0, lastCatchT:0, intention:'wander',
                  memory:null, targetId:null, waypoint:route.length>1?1:0, dwell:0 };

  function updateMentalState(dt, t, ctx){
    if(role==='predator'){
      // 论文 H = min(1, elapsed_since_catch / hunger_full)
      state.hunger = Math.min(1, (t - state.lastCatchT) / (ms.hunger_full_sec||20));
    } else {
      // 论文 F^i = min(D0 / d, 1)
      const pred = nearestByRole(ctx, 'predator');
      const d = pred ? dist2D(pet.group.position, pred.group.position) : Infinity;
      state.fear = Math.min(1, (ms.fear_scale_D0||6.0)/d);
      state._pred = pred; state._predDist = d;
    }
  }
  // 工具：nearestByRole(ctx,role) 遍历 ctx.allPets，按 config.role 过滤取最近；dist2D 用 (x,z)
  ```
  验收：`node --check src/frontend/js/office/pet-behavior.js`；PP-8 的自检文件断言：`t=0` 时 H=0，`t=hunger_full` 时 H=1；prey 距离 d=D0 时 F=1、d=2·D0 时 F=0.5。

- [x] **PP-5** 意图生成器（优先级 + 单项短期记忆防抖，论文 §5） ⟦Copilot⟧
  落点：新增 `generateIntention(ctx)`，优先级 **avoid > (predator:hunt / prey:escape) > wander**：
  ```js
  function generateIntention(ctx){
    // 1) avoid（最高）：碰撞敏感区内有他者 → 压栈当前意图
    if(imminentCollision(ctx)){
      if(state.intention!=='avoid'){ state.memory = {intention:state.intention, targetId:state.targetId}; }
      state.intention='avoid'; return;
    }
    // avoid 解除 → 弹栈恢复（防 dithering）
    if(state.intention==='avoid'){
      if(state.memory){ state.intention=state.memory.intention; state.targetId=state.memory.targetId; state.memory=null; }
      else state.intention='wander';
    }
    if(role==='predator'){
      const prey = selectPrey(ctx);                 // PP-7 代价函数选目标
      const hungry = state.hunger > (ms.hunt_hunger_threshold??0.3);
      if(prey && (hungry || inVision(prey))){ state.intention='hunt'; return; }
    } else {
      const fEsc = ms.f_escape??0.55, fCalm = ms.f_calm??0.35;
      if(state.fear > fEsc){ state.intention='escape'; state.targetId=state._pred?.config.id; return; }
      if(state.intention==='escape' && state.fear >= fCalm){ return; } // 滞回区维持
    }
    state.intention='wander'; state.targetId=null;
  }
  // imminentCollision(ctx): 除当前追/逃目标外，任何他者进入 collision_box(≈0.8) → true
  // inVision(other): 夹角<vision_cone_deg/2 且距离<detect_radius
  ```
  验收：`node --check`；自检断言：avoid 打断 hunt 后、碰撞解除，`state.intention` 恢复为 `hunt`（不掉回 wander）。

- [x] **PP-6** 行为例程拆分 + step 分派（按 role） ⟦Copilot⟧
  落点：把原 `step()` 主体拆成 4 个例程，`step` 只做「更新→生成→分派」：
  ```js
  function step(dt, t, ctx){
    updateMentalState(dt,t,ctx); generateIntention(ctx);
    ({ avoid:routineAvoid, hunt:routineHunt, escape:routineEscape, wander:routineWander }
      [state.intention] || routineWander)(dt,t,ctx);
  }
  // routineWander: 复用现有沿 route 巡游 + dwell 停留（原 patrol 逻辑搬入）
  // routineAvoid: 朝「远离最近障碍」方向转向，前进量随夹角衰减（原 align 逻辑）
  // 移动+动画统一走 moveToward(targetXZ, speed, dt, t)，内部调 _walkAnimate/_idleAnimate
  ```
  验收：`node --check`；office3d=1 手动跑一轮，小虎巡游/吱吱巡游动画无回归（walk/idle 正常）。

## Phase C: Predator 捕猎闭环

- [x] **PP-7** 猎物代价函数 + 持久化选目标（论文 §6.1） ⟦Copilot⟧
  文件：`pet-behavior.js`
  落点：新增 `selectPrey(ctx)`，代价 $C_k=d_k(1+\beta_2 E_k/\pi)$（单猎物省略集群项）：
  ```js
  function selectPrey(ctx){
    let best=null, bestCost=Infinity;
    const heading = pet.group.rotation.y + Math.PI/2;         // 世界朝向
    for(const p of Object.values(ctx.allPets)){
      if(p.config.role!=='prey') continue;
      const dx=p.group.position.x-pet.group.position.x, dz=p.group.position.z-pet.group.position.z;
      const d=Math.hypot(dx,dz);
      let E=Math.abs(angleWrap(Math.atan2(dx,dz)-heading));    // 转向代价 ∈[0,π]
      const cost = d*(1 + (intent.beta_turn_cost??0.2)*E/Math.PI);
      if(cost<bestCost){ bestCost=cost; best=p; }
    }
    // 持久化：仅当新目标代价比「当前目标代价」低超过阈值才切换（论文 fickle/devoted）
    if(state.targetId && ctx.allPets[state.targetId]){
      const cur=ctx.allPets[state.targetId]; /* 计算 cur 的 cost */
      if(best && best!==cur && (curCost-bestCost) <= (intent.persistence_threshold??1.5)) best=cur;
    }
    state.targetId = best?.config.id || null;
    return best;
  }
  ```
  验收：`node --check`；自检：猫朝 +x，正前方猎物（E≈0）代价 < 正后方猎物（E≈π）代价。

- [x] **PP-8** 捕获判定 + onCatch 回调（suck-in 简化，论文 §6.1） ⟦Copilot⟧
  文件：`pet-behavior.js`（判定）+ 自检文件
  落点：`routineHunt` 移动后判定；用 `state._caught` 去重（一次捕获只触发一次）：
  ```js
  function routineHunt(dt,t,ctx){
    const target = ctx.allPets[state.targetId]; if(!target){ return routineWander(dt,t,ctx); }
    const sp = (config.behavior?.speed||1.6) * (1 + 0.5*state.hunger);   // 越饿越快
    moveToward(target.group.position, sp, dt, t);
    const d = dist2D(pet.group.position, target.group.position);
    if(d < (intent.catch_radius??0.8) && !state._caught){
      state._caught = true; state.hunger = 0; state.lastCatchT = t;
      if(behaviorApi.onCatch) behaviorApi.onCatch(pet, target);      // 交给 ecosystem
    } else if(d > (intent.catch_radius??0.8)*2){ state._caught = false; }  // 拉开后复位
  }
  ```
  新增自检文件 [src/frontend/js/office/__checks__/pet-behavior.check.mjs](../src/frontend/js/office/__checks__/pet-behavior.check.mjs)（node 原生 assert，无框架），覆盖 PP-4/5/7/8 公式。
  验收：`node src/frontend/js/office/__checks__/pet-behavior.check.mjs` 退出码 0（所有 assert 通过）。

- [x] **PP-9** onCatch 联动：吱吱 respawn + 小虎得意台词/TTS ⟦Copilot⟧
  文件：[src/frontend/js/office/pet-ecosystem.js](../src/frontend/js/office/pet-ecosystem.js)
  落点：`_buildAll()` 里为 predator 设 `pet.behavior.onCatch`（复用现有 `_onPetDetect` 的 LLM/TTS 通路，改文案为"得意"）：
  ```js
  if(pet.config.role==='predator'){
    pet.behavior.onCatch = (predator, prey) => {
      // 1) 吱吱瞬移到离猫最远的路点 + 恐惧清零
      const route = prey.config.behavior.route;
      let best=0,bd=-1; route.forEach(([x,z],i)=>{const d=Math.hypot(x-predator.group.position.x,z-predator.group.position.z); if(d>bd){bd=d;best=i;}});
      prey.group.position.set(route[best][0],0,route[best][1]);
      prey.behavior.state.fear = 0; prey.behavior.state.dwell = 1.0;
      // 2) 小虎念得意台词（cat-speak，context=抓到老鼠）+ TTS
      this._onPetDetect(predator, prey, {context:'抓到了老鼠吱吱，得意洋洋', tone:'gloat'});
    };
  }
  ```
  `_onPetDetect` 增加可选 `opts` 参数，透传 `context` 给 `/llm/cat-speak`。
  验收：`node --check src/frontend/js/office/pet-ecosystem.js`；office3d=1 手动演练：小虎靠近吱吱到 `catch_radius` 内 → 吱吱瞬移远角、小虎气泡出现古诗、TTS 播报。

## Phase D: office-scene.js 彻底解耦（延续旧 PE-9）

- [x] **PP-10** 移除 office-scene.js 硬编码猫鼠 ⟦Copilot⟧
  文件：[src/frontend/js/office/office-scene.js](../src/frontend/js/office/office-scene.js)
  落点（逐段删除，改由 `PetEcosystem` 接管）：
  1. 删 `buildCat()`(≈L435) / `buildMouse()`(≈L517) 及 `const cat/squeak = build…()`(≈L602)。
  2. 删 animate 内「猫巡逻」块(≈L962-1002) 与「老鼠吱吱」块(≈L1004-1078)，改为 `petEco.step(dt, t)`。
  3. 删拾取里 cat/squeak 分支(≈L303-336)，改为 `const hit = petEco.pick(raycaster,camera,mouse); if(hit) handlePetClick(hit)`。
  4. `showCatBubble/onRewardUpdate` 里 `cat.drawBubble` 改 `petEco.pets['xiaohu_cat']?.drawBubble`。
  5. 顶部 `import { PetEcosystem } from './pet-ecosystem.js'`，初始化 `const petEco = new PetEcosystem(scene, makeLabel); await petEco.init()`（或在 boot 注入）。
  6. 清理孤儿：`CAT_ROUTE`/`MOUSE_ROUTE`/`_catSpeakLLM`/`_catBubbleHold` 若无其他引用则一并删。
  验收：`node --check src/frontend/js/office/office-scene.js`；`grep -n "buildCat\|buildMouse\|CAT_ROUTE\|MOUSE_ROUTE" office-scene.js` 无残留；office3d=1 渲染/点击/台词/TTS 全正常。

- [x] **PP-11** office-boot.js 拾取/评分联动改走 PetEcosystem ⟦Copilot⟧
  文件：[src/frontend/js/office/office-boot.js](../src/frontend/js/office/office-boot.js)
  落点：`_isCat/_isMouse`(≈L126) 与猫气泡/评分波动(≈L163,L297) 改用 `petEco` 事件；点击小虎→对话框、点击吱吱→气泡、评分波动→小虎评价（复用 `onRewardUpdate`）。
  验收：`node --check`；三条联动手动验证正常。

## Phase E: 配置页字段补全

- [x] **PP-12** pet-config.html 增 mental_state / intention 表单 ⟦Copilot⟧
  文件：[src/frontend/pet-config.html](../src/frontend/pet-config.html)
  落点：在行为卡片后新增两张卡片，字段与 PP-1/2 Schema 对齐；`role` 用下拉（predator/prey）。保存时并入 PUT `/api/v1/pet-ecosystem/pets/{id}` 的 body。
  验收：页面编辑 `catch_radius`/`f_escape` 等 → PUT 持久化到 `pet_config.json` → 刷新 office3d 生效。

---

## Phase F: 收口冲刺剩余任务（沿用旧编号，非本次行为模型范畴）

- [ ] **PE-11** S2 P1-4: token/任务跑分基准脚本 ⟦待认领⟧
- [ ] **PE-12** S2 P1-5: 上下文预算强化（截断/缓存/压缩） ⟦待认领⟧
- [ ] **PE-13** S3 P1-2/P1-3: 技能渐进披露设计 + 批量接线 ⟦待认领⟧
- [ ] **PE-14** S4 P2-1/P2-2/P2-4: 技能闭环 E2E + 发布门禁 + SKILL.md 导入导出 ⟦待认领⟧
- [ ] **PE-15** S5 P3-1~P3-4: 孪生可信度（回放编译/保真度校准/场景扩充） ⟦待认领⟧
- [ ] **PE-16** S6 P6-1/P6-4/P6-5/P6-6: Plaza 跑题守卫/结构化发言/反自信偏差/模型异质性 ⟦待认领⟧
- [ ] **PE-17** S7 P4-1~P4-4: api.py 拆分 + 契约测试 + 技能三存储归一 ⟦待认领⟧
- [ ] **PE-18** S7 P7-2~P7-4/M5-2: 统一 3D 收尾 ⟦待认领⟧
- [ ] **PE-19** S0 P0-7/P0-8b: 前端 module 化 + mypy 扩圈 ⟦待认领⟧

---

## 执行顺序

**本次（Predator/Prey 行为模型，Copilot）**：
PP-1~3（Schema）→ PP-4~6（意图生成器内核）→ PP-7~9（捕猎闭环）→ PP-10~11（解耦）→ PP-12（配置页）
每个 Phase 结束跑一次 `node scripts/check-docs-signoff.cjs --strict` 与相关 `node --check`/`py_compile`。

**地基（PE-1~8,10）已由 CodeBuddy 完成**；PE-11~19（收口冲刺）与行为模型无关，另行认领。

---

## 复查记录（Copilot，PP-1~12 全部完成）

**验证结果（全绿）**：
- `node src/frontend/js/office/__checks__/pet-behavior.check.mjs` → ALL PASS（H/F 公式、代价函数、意图+单项记忆防抖、捕获去重）。
- `npm run build`（vite）→ built 成功，含 `pet-config.html` 与 office/three bundle，无 import/语法错误。
- `pytest -q`（全量）→ **1450 passed, 7 skipped**。
- `node --check` → pet-behavior.js / pet-ecosystem.js / office-scene.js 全部通过。
- `grep buildCat|buildMouse|CAT_ROUTE|MOUSE_ROUTE|_catSpeakLLM office-scene.js` → 无残留。

**实现说明 / 与原 plan 的偏差**：
- PP-11：未改 office-boot.js。改为在 office-scene.js 内保留 `cat`/`squeak` 作为 **PetEcosystem 句柄**（`petEco.pets['xiaohu_cat'/'squeak_mouse']`），使既有的拾取(pick)、猫解说气泡(catNote)、猫诱导(catLure)、评分评价(onRewardUpdate) 全部零改动继续工作。office-boot 只用 `sceneApi` 方法，无需变更——等效满足 PP-11 且回归面更小。
- 实时 TTS：捕食者 `onDetect`(发现猎物) 与 `onCatch`(捕获) 均经 `OfficeAPI.onCatComment(text, voice)` → `catSpeak` → 浏览器 `SpeechSynthesis`（婷婷，实时无文件；后端 edge-tts/gpt-sovits 为可选）。LLM 失败也走 fallback 文案发声，保证"可用"。`onCatch` 用 `force` 跳过冷却，确保得意台词必发声。
- 捕获闭环：`d < catch_radius(0.8)` → 吱吱瞬移最远路点、F/H 归零；`_caught` 去重，拉开 2×半径后复位。
