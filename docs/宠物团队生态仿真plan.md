<!-- docs-signoff: author="CodeBuddy" kind="llm" doc="plan" ts="2026-07-07T03:40:00Z" -->
# 宠物团队生态仿真模块 — 可插拔架构 Plan

> 目标：将猫小虎 + 老鼠吱吱的 3D 模型、AI 行为、LLM 台词、TTS 语音、互动逻辑全部抽成独立可插拔模块，
> 通过页面配置管理宠物团队成员、行为参数、巡逻路线、台词 prompt、语音参数。

## 1. 架构设计

### 1.1 模块分层
```
PetEcosystem (生态管理器)
├── PetConfigStore (配置存储 — 后端 teams.json + 独立 pet_config.json)
├── PetFactory (工厂 — 根据配置动态构建 3D 模型)
│   ├── ModelBuilder (几何体构建 — 可插拔: cat/mouse/自定义)
│   ├── AnimationController (动画 — 可插拔: walk/idle/flee/patrol)
│   └── BehaviorAI (行为 AI — 可插拔: patrol/flee/chase/interact)
├── PetRouter (路由 — LLM 台词 + TTS 语音)
│   ├── SpeakProvider (发言 — 可插拔: LLM/硬编码/混合)
│   └── VoiceProvider (语音 — 可插拔: 婷婷/Google/en-US/自定义)
└── PetInteractions (互动 — 猫鼠追逐/评分评价/点击对话)
```

### 1.2 配置 Schema (pet_config.json)
```json
{
  "pets": [
    {
      "id": "xiaohu_cat",
      "name": "小虎",
      "species": "cat",
      "model": {
        "type": "builtin_cat",
        "scale": 1.0,
        "color": 0xf2f2f2,
        "ear_position": [0.52, 0.69],
        "ear_swing_amplitude": 0.3,
        "tail_length": 0.55,
        "custom_mesh": ""
      },
      "behavior": {
        "type": "patrol",
        "route": [[16,12],[16,-2],...],
        "speed": 1.6,
        "dwell_range": [1.5, 5.0],
        "detect_radius": 4.0,
        "flee": false,
        "chase": true
      },
      "speak": {
        "provider": "llm",
        "skill_id": "cat_speak_prompt",
        "trigger": "on_detect_mouse",
        "cooldown_sec": 10,
        "fallback": "喵~ 硕鼠硕鼠，无食我黍！"
      },
      "voice": {
        "lang": "zh-CN",
        "rate": 1.1,
        "pitch": 1.8,
        "volume": 0.9,
        "preferred_voice": "婷婷"
      },
      "click_action": {
        "type": "dialog",
        "personality": "叛逆高中生"
      }
    },
    {
      "id": "squeak_mouse",
      "name": "吱吱",
      "species": "mouse",
      "model": { "type": "builtin_mouse", "scale": 0.85, ... },
      "behavior": {
        "type": "patrol_flee",
        "route": [[-18,16],[-18,4],...],
        "speed": 2.2,
        "flee_radius": 4.0,
        "flee_speed_multiplier": 1.8,
        "warn_ring": true
      },
      "speak": { "provider": "none" },
      "voice": { "enabled": false },
      "click_action": { "type": "bubble" }
    }
  ],
  "ecosystem": {
    "chase_pairs": [["xiaohu_cat", "squeak_mouse"]],
    "coexistence": []
  }
}
```

### 1.3 前端页面
- `/pet-config.html` — 宠物团队配置页
  - 成员列表（增删改）
  - 每个宠物的模型/行为/台词/语音配置卡片
  - 巡逻路线可视化编辑（地图点选）
  - 互动关系矩阵（谁追谁、谁躲谁）

## 2. 实施步骤

### Phase 1: 后端配置存储 + API
- `src/backend/agents/pet_ecosystem.py` — PetEcosystem 管理器
- `src/backend/agents/pet_routes.py` — REST API (CRUD pet config)
- `storage/pet_config.json` — 默认配置（猫小虎 + 吱吱）

### Phase 2: 前端模块重构
- `src/frontend/js/office/pet-ecosystem.js` — 生态管理器前端
- `src/frontend/js/office/pet-factory.js` — 模型工厂（替代 buildCat/buildMouse）
- `src/frontend/js/office/pet-behavior.js` — 行为 AI（替代硬编码巡逻/逃跑）
- `src/frontend/pet-config.html` — 配置页面

### Phase 3: office-scene.js 解耦
- 从 office-scene.js 移除 buildCat/buildMouse/猫鼠动画
- 改为 PetEcosystem 接管，office-scene 只提供 scene/group 引用

### Phase 4: 收口冲刺剩余任务
- 完成所有未标注 [x] 的任务
