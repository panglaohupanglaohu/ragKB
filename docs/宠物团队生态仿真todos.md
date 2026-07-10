<!-- docs-signoff: author="Copilot" kind="llm" doc="todos" ts="2026-07-08T05:00:00Z" -->
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

## Phase G: 页面配置唯一真相源（voice 兜底移除）

> 配套 plan §9。目标：TTS 完全由 `/pet-config.html` 页面配置驱动，移除前端 voice 配置兜底默认值，缺字段抛异常暴露问题。

- [x] **PP-13** 清理 `pet_config.json` 嵌套副本 + 移除 catSpeak voice 兜底 ⟦Copilot⟧
  改动：
  1. [storage/pet_config.json](../storage/pet_config.json) — 删除 `pets[0]`（小虎）内部错误嵌套的 `pets` 数组和 `ecosystem` 对象（历史垃圾副本）。
  2. [src/frontend/js/office/voice-config-validator.js](../src/frontend/js/office/voice-config-validator.js)（新增）— 纯函数 `validateVoiceConfig(vc)` 返回 `{ok, error}`，覆盖 edge-tts/gpt-sovits/browser/unknown 四种 provider 校验。
  3. [src/frontend/js/office/office-boot.js](../src/frontend/js/office/office-boot.js) — `catSpeak` 调用 `validateVoiceConfig`，不 ok 则 `console.error(v.error)` 并 return；移除 `?? 1.8`/`?? 1.1`/`?? 0.95`/`|| 15` 等兜底；移除硬编码「婷婷」→「Google 普通话」音色回退链。`_catSpeakBackend` 的 edge-tts 缺 `edge_voice` 报错；`speed_factor` 不再 `?? 1.0`。保留引擎失败回退 browser（容错非兜底）。
  验收：`node --check office-boot.js`；`npm run build`；缺 voice 配置时 console 报具体缺什么字段。

- [x] **PP-14** voice 配置校验 + pet_config 数据完整性测试 ⟦Copilot⟧
  新增测试：
  1. [tests/test_pet_ecosystem.py](../tests/test_pet_ecosystem.py) — 9 个用例：配置文件存在性、顶层结构、无嵌套副本、小虎 edge-tts 字段齐全、临时文件加载、_DEFAULT_SEED 落盘、get_config 默认值补全、_DEFAULT_SEED 结构。
  2. [src/frontend/js/office/__checks__/voice-config-validator.check.mjs](../src/frontend/js/office/__checks__/voice-config-validator.check.mjs) — 10 个 assert：缺 vc/缺 provider/edge-tts 缺 edge_voice/browser 缺字段/字段空字符串/未知 provider/三种 provider 正常配置/REQUIRED_BROWSER_FIELDS 完整性。
  验收：`pytest tests/test_pet_ecosystem.py -q` → 9 passed；`node voice-config-validator.check.mjs` → ALL PASS。

---

## Phase H: 生态仿真端到端可用性修复（2026-07-08）

> 三处缺口都直接阻塞生态仿真跑通：模型凭据丢失 → 小虎 `cat-speak` LLM 401；CSP 阻断 blob: → TTS 无声；团队批量删除按钮失效 → `pet_squad` 无法清理/管理。均与行为模型逻辑无关，属"装配/持久化/UI 链路"修复。

- [x] **PP-15** 模型 API key 改用环境变量引用方案（根除重启后 key 丢失）⟦Copilot⟧
  根因：[`ModelConfig.to_dict()`](../src/backend/agents/models.py) 把 `api_key` 脱敏成 `****1234` 供 API 返回，但 [`team_store._serialize_team()`](../src/backend/agents/team_store.py) 复用 `to_dict()` 落盘，重启后 `_deserialize_model()` 把脱敏值当真实 key 读回（或强制清空），导致小虎 `cat-speak` 的 LLM 调用 401/无效 key。
  改动：
  1. [src/backend/agents/models.py](../src/backend/agents/models.py) — `to_dict()` 对 `env:VAR_NAME` 前缀原样保留落盘；真实 key 仍脱敏返回 API。新增 `get_resolved_api_key()` 运行时解析 `env:` 前缀。
  2. [src/backend/agents/team_store.py](../src/backend/agents/team_store.py) — `_deserialize_model()` 恢复 `env:` 引用，脱敏值不恢复。
  3. [src/backend/agents/secret_store.py](../src/backend/agents/secret_store.py) — `resolve_api_key()` 支持 `env:` 前缀解析。
  4. [src/backend/agents/api.py](../src/backend/agents/api.py) + [src/backend/channels/evolution_executor.py](../src/backend/channels/evolution_executor.py) — 所有 LLM 调用点改用 `model.get_resolved_api_key()` / `resolve_api_key()`。
  5. [src/backend/agents/env_loader.py](../src/backend/agents/env_loader.py)（新增）— 无第三方依赖的 `.env` 加载器；[src/backend/main.py](../src/backend/main.py) 启动时调用。
  6. [scripts/setup_keys.sh](../scripts/setup_keys.sh)（新增）— macOS/Linux 交互式创建环境变量脚本。
  7. [scripts/setup_keys.ps1](../scripts/setup_keys.ps1)（新增）— Windows PowerShell 等价脚本。
  8. [src/frontend/agent-team-config.html](../src/frontend/agent-team-config.html) — 编辑模型弹窗 key 字段加 `env:VAR_NAME` 用法提示。
  测试：[tests/test_model_env_key.py](../tests/test_model_env_key.py) — 17 个用例覆盖序列化/解析/往返/.env 加载，全过。

- [x] **PP-16** CSP 允许 blob: 音频播放（修复 TTS 语音失效）⟦Copilot⟧
  根因：[src/frontend/Agent-digital-twin.html](../src/frontend/Agent-digital-twin.html) 的 Content-Security-Policy 缺 `media-src blob:`，导致 edge-tts/gpt-sovits 后端返回的音频经 `URL.createObjectURL()` 生成 `blob:http://localhost:5173/...` 后被浏览器 CSP 阻断，小虎念台词无声音。
  修复：CSP 加 `media-src 'self' data: blob:;`。
  验收：office3d=1 模式下小虎 onDetect/onCatch 触发 TTS，控制台无 CSP 违规报错，音频正常播放。

- [x] **PP-17** 团队批量删除按钮修复 + 多选 checkbox 回填 ⟦Copilot⟧
  根因：[src/frontend/js/tasks-view.js](../src/frontend/js/tasks-view.js) 的 `window.deleteTeam` 依赖 `deleteSelectedTeams` 函数和 `.ov-team-cb` checkbox，但这两者在前端重构中已被删除，导致「删除选中团队」按钮点击无反应。
  修复：
  1. [src/frontend/js/agent-team-config.js](../src/frontend/js/agent-team-config.js) — 团队卡片渲染处（`teamCards`）加回 `<input type="checkbox" class="ov-team-cb" value="${team_id}">`，`onclick="event.stopPropagation()"` 防止点 checkbox 触发卡片切换团队。
  2. [src/frontend/js/tasks-view.js](../src/frontend/js/tasks-view.js) — 补回 `window.deleteSelectedTeams`：收集 `.ov-team-cb:checked` → `showConfirm` 确认 → 循环 `DELETE ${A}/teams/${id}` → 统计 ok/fail → `loadTeams()` 刷新。原 `window.deleteTeam` 保留，有勾选时优先走批量，无勾选兜底删下拉选中团队。
  测试（API 层模拟 `deleteSelectedTeams` 的 DELETE 序列）：用 panglaohu token 对 10 个历史残留团队（5 个 "Updated Team" + 5 个 "Test Team Alpha"）执行批量 DELETE，全部返回 `200 {"deleted":"<id>"}`，删除后团队总数 16→6，同名残留 0。前端 `deleteSelectedTeams` 的请求序列与该 API 测试完全一致。

---

## Phase I: 生态仿真范式泛化（Perception → Intention → Behavior 作为 Agent 通用运行时）

> 配套 plan §10。目标：把「感知-意图-行为」从宠物 demo 提升为**所有 Agent 的统一执行模型**，让 skill 体系、Plaza 协作、孪生沙箱都从生态仿真视角来看。新旧运行时并存，按 Agent 配置选用，不一次性推翻现有代码。

- [ ] **PI-1** 抽象 `IntentionAgent` 基类（Python 侧） ⟦待认领⟧
  文件：[src/backend/agents/runtime/eco_loop.py](../src/backend/agents/runtime/eco_loop.py)（新增）
  落点：把 `pet-behavior.js` 的 `state.intention` + `generateIntention` + `memory` 抽象成 Python 基类：
  ```python
  class IntentionAgent:
      mental_state: dict       # 泛化的 Hunger/Fear：urgency/confidence/budget_pressure…
      perception: dict         # 感知信号：visible_agents/messages/token_budget…
      intention: dict | None   # {type, target, priority, memory}
      def perceive(self, ctx) -> dict: ...        # 子类重写：从上下文提取信号
      def generate_intention(self, perception) -> dict: ...  # 子类重写：优先级判定 + 单项记忆
      def execute_behavior(self, intention, ctx) -> Any: ... # 子类重写：执行意图对应的例程
      def tick(self, ctx):
          p = self.perceive(ctx)
          i = self.generate_intention(p)
          return self.execute_behavior(i, ctx)
  ```
  设计原则：心理状态/感知/意图生成器全可重写；意图对象 `{type, target, priority, memory}` 是头等公民，可被日志/统计/仿真复用。
  验收：`pytest` 覆盖基类 + 一个 `PetAgent(IntentionAgent)` 子类复刻猫鼠行为（Hunger/Fear 公式、avoid 单项记忆防抖、持久化阈值），行为与 `pet-behavior.check.mjs` 等价。

- [ ] **PI-2** PetEcosystem 后端切到 eco_loop ⟦待认领⟧
  文件：[src/backend/agents/pet_ecosystem.py](../src/backend/agents/pet_ecosystem.py)
  落点：`PetEcosystem` 的每 tick 调用改为 `agent.tick(ctx)`，前端 `pet-behavior.js` 保持不变（前后端行为等价，只是后端有了 Python 侧意图模型）。目的：让 eco_loop 在真实场景跑通，为接入 chat_harness 做准备。
  验收：猫鼠场景行为零回归（`pet-behavior.check.mjs` 全过）；后端日志可观测每个 pet 的 `intention` 序列。

- [ ] **PI-3** Agent 运行时接入 eco_loop ⟦待认领⟧
  文件：[src/backend/agents/chat_harness.py](../src/backend/agents/chat_harness.py)、[src/backend/agents/runtime/tool_loop.py](../src/backend/agents/runtime/tool_loop.py)
  落点：`chat_harness` 在 plan→act 前加 perception→intention 步骤；`tool_loop` 的"下一步动作"改为"执行当前意图的例程"。Agent 配置加 `runtime: "eco_loop" | "legacy"` 字段，默认 legacy，按需切换。
  保留旧路径作 fallback，不破坏现有 Agent。
  验收：一个非宠物 Agent（如 `pet_squad` 里的小虎作为 LLM Agent）能用 eco_loop 跑通"感知任务上下文 → 生成回应意图 → 执行发言/工具"闭环；旧 Agent 切回 legacy 行为不变。

- [ ] **PI-4** skill schema 加 `intention` 字段 ⟦待认领⟧
  文件：[src/backend/agents/skill_library.py](../src/backend/agents/skill_library.py)、[src/backend/agents/skill_router.py](../src/backend/agents/skill_router.py)
  落点：skill 定义加 `intention: str`（如 "answer_question" / "use_tool" / "delegate" / "verify"）；SkillRouter 增加"按意图过滤"前置阶段——先按当前 Agent 意图筛 skill 子集，再在子集内做 BM25/TF-IDF 文本相似度重排。新技能入库必须标 intention。
  验收：skill 按 intent 路由的命中率 ≥ 关键词路由基线（用现有 skill 库做 A/B 对比）；旧无 intention 字段的 skill 视为 "generic" 兜底，不破坏现有检索。

- [ ] **PI-5** Plaza 发言前声明意图 ⟦待认领⟧
  文件：[src/backend/agents/plaza_engine.py](../src/backend/agents/plaza_engine.py)
  落点：每轮发言前，每个 Agent 先调 `declare_intention(perception)` 产出意图声明（如 "补充论据" / "质疑" / "赞同" / "跑题"）；主持人收集全局意图分布做仲裁（谁先说、谁让步、谁补充、谁被拉回），再进入结构化发言。
  主持人对"跑题"意图有强制拉回权（对应 Phase F PE-16 P6-1 跑题守卫）。
  验收：Plaza 一轮议事产出的"意图分布"可被观测/统计（日志或 SSE 事件）；跑题意图被主持人识别并拉回的比例可度量。

- [ ] **PI-6** 孪生沙箱混沌注入扩展到感知/心理状态 ⟦待认领⟧
  文件：[src/backend/sandbox/twin_loop.py](../src/backend/sandbox/twin_loop.py)
  落点：现有混沌注入（断网/成员离场/技能退化）扩展两类：
  1. **感知扰动**：遮挡（部分 Agent 不可见）、延迟（消息延迟到达）、噪声（感知信号加噪声）。
  2. **心理状态扰动**：强行调高 urgency/confidence/budget_pressure，观察意图-行为链路鲁棒性。
  验收：孪生沙箱能注入"感知扰动"并观测到意图-行为变化（对比有/无扰动的 intention 序列与执行结果）。

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

---

## 修复记录（2026-07-07，从 GitHub 拉取覆盖本地后的落地修复）

> 背景：用 GitHub `ragKB` 最新 `main` 全量覆盖本地代码后，宠物生态出现三处"数据/装配"缺口。均为环境落地问题，非行为模型逻辑缺陷。

- [x] **FIX-1 缺失 `storage/pet_config.json` → 小虎/吱吱不加载（0 个生物）**
  根因：所有生物数据来自 [storage/pet_config.json](../storage/pet_config.json)，`pet_ecosystem.py` 无内置种子；该文件被 `.gitignore` 忽略、不进仓库，故拉取覆盖时不会带过来（开发机上是本地生成的）。
  修复：按 Phase A schema 重建 seed，含小虎（`xiaohu_cat`, role=predator, builtin_cat）+ 吱吱（`squeak_mouse`, role=prey, builtin_mouse），带 `perception`/`mental_state`/`intention`。`PetEcosystem` 为启动单例，需重启后端重载。
  验收：`GET /api/v1/pet-ecosystem/config` 返回 2 pets；pet-config.html 渲染两张卡片；日志 `🐾 PetEcosystem loaded 2 pets`。
  ⚠️ 遗留：seed 仍被 gitignore，跨机不同步——根治需二选一：纳入版本控制 **或** 在 `pet_ecosystem.py` 加内置默认种子（推荐后者）。

- [x] **FIX-2 `Visibility` 导入错误 → 宠物团队启动加载失败**
  文件：[src/backend/main.py](../src/backend/main.py)
  根因：`from agents.team_manager import AgentTeam, Visibility`，但 `team_manager` 未 re-export `Visibility`（定义在 `agents.models`）。
  修复：改为 `from agents.models import AgentProfile, AgentPersonality, AgentTeam, Visibility`。修复后团队 5→6、agents 34→36，`pet_squad` 正常加载。

- [x] **FIX-3 `cat_speak_prompt` 技能缺失 → 小虎配置看不到"cat speak"、后端每次走 fallback**
  文件：[src/backend/main.py](../src/backend/main.py)、[src/backend/agents/api.py](../src/backend/agents/api.py)
  根因：`main.py` 构造 `pet_squad` 时既没把 `cat_speak_prompt` 加进 `team.skills`，也没加进 `xiaohu_cat.skills`；且 `pet_squad` 已 `_persist()` 到 `storage/teams/teams.json`，重启时构造块被 `"pet_squad" not in _teams` 跳过，改构造代码不足以修复已持久化的团队。
  修复：
  1. 构造块内 `pet_team.add_skill(_build_cat_speak_skill())` + 小虎 `skills` 追加 `cat_speak_prompt`（覆盖全新安装）。
  2. 新增**幂等回填块**（每次启动都跑、不受 `not in _teams` 守卫限制）：`team.skills` / `xiaohu_cat.skills` 缺 `cat_speak_prompt` 则补入并 `_persist()`（修复已持久化团队）。
  3. `cat_speak_prompt` 的 `instructions` = **Metal Gear 中 Mei Ling 谚语式英文口吻**（英文单行、可带简短出处、无中文/无"喵"）。
  4. 修正 [api.py](../src/backend/agents/api.py) `cat_speak` 里自相矛盾的 user_msg（原要 "Chinese proverb"，与 system 的 Mei Ling 英文冲突）→ 改为 "ONE line in ENGLISH … Mei Ling style"。
  验收：`storage/teams/teams.json` 中 `pet_squad.skills` 含 `cat_speak_prompt`（`has_instructions:true`）且 `xiaohu_cat.skills` 含该 id；`POST /api/v1/agent-config/llm/cat-speak` 读技能 instructions 作 system prompt（非 fallback），返回英文谚语。
  说明：小虎/吱吱在 agent-team-config 页需切换团队选择器到"宠物智能体团队"才显示（默认选中 Build System，非 bug）；从仿生生态跳转不会自动选中 pet_squad。
  ⚠️ 后端重启后已打开页面的 CSRF token 失效，`cat-speak` 会短暂 403，**刷新页面**即恢复。

- [x] **FIX-4 宠物 seed 内置化（根治跨机不同步）**
  文件：[src/backend/agents/pet_ecosystem.py](../src/backend/agents/pet_ecosystem.py)
  背景：FIX-1 只补了本机 `storage/pet_config.json`（gitignore，不跨机）。根治：把小虎/吱吱完整配置作为内置常量 `_DEFAULT_SEED`。
  落点：`_load()` 在「文件缺失/损坏/无 pets」时 `copy.deepcopy(_DEFAULT_SEED)` 并 `_save()` 落盘；`_DEFAULT_SEED` 含 Phase A 全字段（role/perception/mental_state/intention）。此后任何机器缺文件都会自动自带小虎+吱吱。
  验收：临时指向不存在路径实例化 `PetEcosystem` → seed 出 `[xiaohu_cat(predator), squeak_mouse(prey)]` 且写盘 True（已通过）。

- [x] **FIX-5 点击"猫台词"技能执行失败（404 Skill not found）**
  文件：[src/backend/agents/api.py](../src/backend/agents/api.py) — `execute_skill`
  根因：`POST /teams/{t}/agents/{a}/skills/{skill_name}/execute` 只用 `sr.get_by_slug()` 在**全局技能注册表**里找；`cat_speak_prompt` 只挂在 `team.skills`（team-local），注册表没有 → 404 → 前端 toast 失败。
  修复：注册表未命中时**回退团队本地技能**——`team.skills.get(name)` 或按 `name/skill_id/slug` 匹配。通用修复，任何 team-local 技能都可执行。
  验收：模拟解析——前端传名 "猫台词提示词 (Mei Ling)" 与 id `cat_speak_prompt` 均解析成功（已通过）；执行走 generic 分支返回 `status:ready`+instructions，不再 404。
