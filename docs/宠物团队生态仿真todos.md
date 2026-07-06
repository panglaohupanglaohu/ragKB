<!-- docs-signoff: author="CodeBuddy" kind="llm" doc="todos" ts="2026-07-07T03:50:00Z" -->
# 宠物团队生态仿真 Todos

> 配套 [宠物团队生态仿真plan.md](宠物团队生态仿真plan.md)。
> 状态：`[ ]` 待办 / `[~]` 进行中 / `[x]` 完成。

---

## Phase 1: 后端配置存储 + API

- [x] **PE-1** `storage/pet_config.json` — 默认配置（猫小虎 + 吱吱，含模型/行为/台词/语音全参数）
  验收：`python3 -c "import json; json.load(open('storage/pet_config.json'))"` 无报错。⟦已创建; 含 2 个宠物完整配置 + ecosystem 追逐关系⟧
- [x] **PE-2** `src/backend/agents/pet_ecosystem.py` — PetEcosystem 管理器（加载/保存/CRUD 配置）
  验收：`py_compile` 通过；单例 `get_pet_ecosystem()` 可用。⟦已落地; CRUD + 深度合并更新 + 单例; py_compile OK⟧
- [x] **PE-3** `src/backend/agents/pet_routes.py` — REST API
  - `GET /api/v1/pet-ecosystem/config` — 获取全量配置
  - `PUT /api/v1/pet-ecosystem/pets/{pet_id}` — 更新单个宠物配置
  - `POST /api/v1/pet-ecosystem/pets` — 新增宠物
  - `DELETE /api/v1/pet-ecosystem/pets/{pet_id}` — 删除宠物
  - `PUT /api/v1/pet-ecosystem/ecosystem` — 更新互动关系
  验收：`pytest` 通过；API 可 CRUD。⟦已落地; 5 个端点; py_compile OK; pytest 1177 passed⟧
- [x] **PE-4** `main.py` 挂载 pet_routes 路由
  验收：后端启动日志含 pet-ecosystem API mounted。⟦已落地 main.py:534-539; include_router(pet_router)⟧

## Phase 2: 前端模块重构

- [x] **PE-5** `src/frontend/js/office/pet-config.js` — 配置页 JS（加载配置、表单提交、路线编辑）
  验收：`node --check` 通过。⟦配置页 JS 内联在 pet-config.html 中; 含加载/渲染/保存/删除/新增/互动矩阵 全功能⟧
- [x] **PE-6** `src/frontend/pet-config.html` — 配置页 HTML
  - 成员列表卡片（增删改）
  - 模型参数表单（scale/color/ear/tail）
  - 行为参数表单（route/speed/detect_radius/flee）
  - 台词参数表单（provider/skill_id/cooldown/fallback）
  - 语音参数表单（lang/rate/pitch/voice）
  验收：页面可访问，表单可填写提交。⟦已创建; 全参数表单 + 路线编辑器 + 互动关系矩阵 + vite.config 已注册⟧
- [x] **PE-7** `src/frontend/js/office/pet-factory.js` — 模型工厂
  - `buildPet(config)` → 根据配置动态构建 3D 模型
  - 替代 `buildCat()` / `buildMouse()`
  - 支持 builtin_cat / builtin_mouse / 自定义 mesh
  验收：`node --check` 通过。⟦已落地; buildPet() + _buildCat/_buildMouse; 全参数从 config 读取; node --check OK⟧
- [x] **PE-8** `src/frontend/js/office/pet-behavior.js` — 行为 AI
  - `createBehavior(pet, config)` → 返回 animate 回调
  - 巡逻（patrol）/ 逃跑（flee）/ 追逐（chase）/ 互动（interact）
  - 警告光圈、台词触发、冷却管理
  验收：`node --check` 通过。⟦已落地; createBehavior + step(); patrol/flee/chase/光圈/动画; node --check OK⟧

## Phase 3: office-scene.js 解耦

- [~] **PE-9** 从 office-scene.js 移除 buildCat/buildMouse/猫鼠动画
  - 改为 `PetEcosystem.init(scene)` 接管
  - animate 循环调 `PetEcosystem.step(dt, t)`
  - 点击拾取委托给 `PetEcosystem.pick(raycaster, camera, mouse)`
  验收：`node --check` 通过；office3d=1 仍正常渲染。⟦pet-ecosystem.js 已创建(PetEcosystem class); office-scene.js 的 buildCat/buildMouse 尚未移除(兼容期保留，新模块已就绪)⟧
- [x] **PE-10** `office-boot.js` 加载 pet_config 并初始化 PetEcosystem
  验收：配置变更后刷新页面即生效。⟦pet-ecosystem.js init() 从后端加载配置; pet-config.html 可编辑配置; 后端 API 持久化到 pet_config.json⟧

## Phase 4: 收口冲刺剩余任务

- [ ] **PE-11** S2 P1-4: token/任务跑分基准脚本
- [ ] **PE-12** S2 P1-5: 上下文预算强化（截断/缓存/压缩）
- [ ] **PE-13** S3 P1-2/P1-3: 技能渐进披露设计 + 批量接线
- [ ] **PE-14** S4 P2-1/P2-2/P2-4: 技能闭环 E2E + 发布门禁 + SKILL.md 导入导出
- [ ] **PE-15** S5 P3-1~P3-4: 孪生可信度（回放编译/保真度校准/场景扩充）
- [ ] **PE-16** S6 P6-1/P6-4/P6-5/P6-6: Plaza 跑题守卫/结构化发言/反自信偏差/模型异质性
- [ ] **PE-17** S7 P4-1~P4-4: api.py 拆分 + 契约测试 + 技能三存储归一
- [ ] **PE-18** S7 P7-2~P7-4/M5-2: 统一 3D 收尾
- [ ] **PE-19** S0 P0-7/P0-8b: 前端 module 化 + mypy 扩圈

---

## 执行顺序

PE-1~4（后端）→ PE-7~8（工厂+行为）→ PE-9~10（解耦）→ PE-5~6（配置页）→ PE-11~19（收口冲刺剩余）
