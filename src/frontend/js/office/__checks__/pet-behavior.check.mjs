/**
 * pet-behavior.check.mjs — pet-behavior.js 自检（node 原生 assert，无框架）
 * 覆盖 PP-4(心理状态) / PP-5(意图+记忆) / PP-7(代价函数) / PP-8(捕获)。
 * 运行: node src/frontend/js/office/__checks__/pet-behavior.check.mjs
 */
import assert from 'node:assert/strict';
import {
  createBehavior, computeHunger, computeFear, preyCost, angleWrap,
} from '../pet-behavior.js';

// ── 纯公式（PP-4 / PP-7）──
assert.equal(computeHunger(0, 20), 0, 'H(0)=0');
assert.equal(computeHunger(20, 20), 1, 'H(full)=1');
assert.equal(computeHunger(40, 20), 1, 'H 饱和于 1');
assert.equal(computeFear(6, 6), 1, 'F(d=D0)=1');
assert.equal(computeFear(12, 6), 0.5, 'F(d=2·D0)=0.5');
assert.equal(computeFear(3, 6), 1, 'F 饱和于 1');
// 正前方(E≈0) 代价 < 正后方(E≈π)
assert.ok(preyCost(5, 0, 0.2) < preyCost(5, Math.PI, 0.2), '正前方猎物代价更低');
assert.equal(angleWrap(Math.PI * 3), Math.PI, 'angleWrap 归一');

// ── 测试替身：最小 pet（无 THREE，parts 空）──
function fakePet(id, role, x, z, extra = {}) {
  return {
    config: {
      id, role,
      behavior: { route: [[x, z], [x + 10, z], [x, z + 10]], speed: 1.6, ...(extra.behavior || {}) },
      perception: { detect_radius: 6, vision_cone_deg: 300 },
      mental_state: { hunger_full_sec: 20, hunt_hunger_threshold: 0.3, fear_scale_D0: 6, f_escape: 0.55, f_calm: 0.35 },
      intention: { beta_turn_cost: 0.2, persistence_threshold: 1.5, catch_radius: 0.8 },
      model: {},
      ...extra.config,
    },
    group: { position: { x, y: 0, z }, rotation: { y: 0 } },
    parts: {},
  };
}

// ── PP-5: 意图优先级 + 单项记忆防抖 ──
// predator 正在 hunt，避碰打断后恢复 hunt（不掉回 wander）
{
  const cat = fakePet('cat', 'predator', 0, 0);
  const mouse = fakePet('mouse', 'prey', 2, 0);   // 正前方(heading=+π/2→世界 +x)
  cat.behavior = createBehavior(cat, cat.config);
  mouse.behavior = createBehavior(mouse, mouse.config);
  const allPets = { cat, mouse };
  // 先让猫进入 hunt（猫朝向 +x, 老鼠在 +x 视野内）
  cat.behavior.step(0.016, 1, { allPets });
  assert.equal(cat.behavior.intention, 'hunt', 'predator 视野内猎物→hunt');
  // 插入一个贴脸障碍（非目标）→ 触发 avoid，压栈 hunt
  const obstacle = fakePet('obstacle', 'prey', 0.3, 0);
  obstacle.config.role = 'obstacle';   // 非 prey，不会被选为猎物
  cat.behavior.step(0.016, 1.1, { allPets: { cat, mouse, obstacle } });
  assert.equal(cat.behavior.intention, 'avoid', '贴脸障碍→avoid');
  assert.ok(cat.behavior.state.memory, 'avoid 压栈了记忆');
  // 障碍移除 → 弹栈恢复 hunt
  cat.behavior.step(0.016, 1.2, { allPets });
  assert.equal(cat.behavior.intention, 'hunt', 'avoid 解除→恢复 hunt(不 dithering)');
}

// ── prey 逃逸滞回 ──
{
  const cat = fakePet('cat', 'predator', 0, 0);
  const mouse = fakePet('mouse', 'prey', 3, 0);   // d=3 → F=6/3=1 > f_escape
  mouse.behavior = createBehavior(mouse, mouse.config);
  cat.behavior = createBehavior(cat, cat.config);
  mouse.behavior.step(0.016, 0, { allPets: { cat, mouse } });
  assert.equal(mouse.behavior.intention, 'escape', 'prey 近距离→escape');
}

// ── PP-8: 捕获事件触发一次 ──
{
  const cat = fakePet('cat', 'predator', 0, 0);
  const mouse = fakePet('mouse', 'prey', 0.5, 0);  // d=0.5 < catch_radius=0.8
  cat.behavior = createBehavior(cat, cat.config);
  mouse.behavior = createBehavior(mouse, mouse.config);
  let catches = 0;
  cat.behavior.onCatch = () => { catches++; };
  cat.config.mental_state.hunt_hunger_threshold = 0;  // 保证进入 hunt
  cat.behavior.step(0.016, 5, { allPets: { cat, mouse } });
  assert.equal(cat.behavior.intention, 'hunt', '近距离猎物→hunt');
  assert.equal(catches, 1, '捕获触发一次');
  assert.equal(cat.behavior.state.hunger, 0, '捕获后 hunger 归零');
  // 未拉开距离 → 不重复触发
  cat.behavior.step(0.016, 5.1, { allPets: { cat, mouse } });
  assert.equal(catches, 1, '未拉开距离不重复捕获');
}

console.log('pet-behavior.check.mjs: ALL PASS');
