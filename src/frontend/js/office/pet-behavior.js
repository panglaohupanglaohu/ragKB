/**
 * pet-behavior.js — 宠物行为 AI（Predator / Prey 意图生成器）
 *
 * 参照 Tu & Terzopoulos《Artificial Fishes》(SIGGRAPH '94) 的整体式智能体模型：
 *   每帧: 更新心理状态(hunger/fear) → 意图生成(优先级 + 单项短期记忆防抖) → 行为例程 → 运动动画。
 *
 * 角色:
 *   predator(小虎): 心理状态 = hunger H；意图 avoid > hunt > wander；捕猎代价函数选目标 + 捕获事件。
 *   prey(吱吱):     心理状态 = fear F；意图 avoid > escape > wander；恐惧驱动逃逸(带滞回)。
 *
 * 用法:
 *   import { createBehavior } from './pet-behavior.js';
 *   const behavior = createBehavior(pet, config, ecosystem);
 *   behavior.onDetect = (predator, prey) => {...};  // predator 首次锁定猎物
 *   behavior.onCatch  = (predator, prey) => {...};  // predator 捕获猎物
 *   behavior.step(dt, t, { allPets });              // 每帧调用
 */

// ── 纯函数（论文公式，无 DOM/THREE 依赖，供自检直接 import）──

/** 夹角归一到 [-π, π]。 */
export function angleWrap(a) {
  while (a > Math.PI) a -= Math.PI * 2;
  while (a < -Math.PI) a += Math.PI * 2;
  return a;
}

/** Predator 饥饿：H = min(1, elapsed / full)（论文 §4.2 简化版）。 */
export function computeHunger(elapsedSec, fullSec) {
  if (fullSec <= 0) return 1;
  return Math.min(1, Math.max(0, elapsedSec / fullSec));
}

/** Prey 恐惧：F = min(1, D0 / d)（论文 F^i = min(D0/d, 1)）。 */
export function computeFear(dist, D0) {
  if (dist <= 0) return 1;
  return Math.min(1, D0 / dist);
}

/** Predator 捕猎代价：C_k = d·(1 + β2·|E|/π)（论文 §6.1，单猎物省略集群项）。 */
export function preyCost(dist, turnAngle, beta) {
  return dist * (1 + beta * Math.abs(turnAngle) / Math.PI);
}

function dist2D(a, b) {
  return Math.hypot(a.x - b.x, a.z - b.z);
}

// ── 行为控制器 ──

/**
 * @param {Object} pet — buildPet 返回的 { group, parts, drawBubble }
 * @param {Object} config — pet_config 中该宠物的完整配置（含 role/perception/mental_state/intention）
 * @param {Object} ecosystem — 预留
 * @returns {Object} { step, onDetect, onCatch, state, intention, isFleeing }
 */
export function createBehavior(pet, config, ecosystem) {
  const b = config.behavior || {};
  const percep = config.perception || {};
  const ms = config.mental_state || {};
  const intent = config.intention || {};
  const route = b.route || [];
  const baseSpeed = b.speed || 1.5;
  const dwellRange = b.dwell_range || [1.0, 3.0];

  // role 缺省：有 chase_targets 视为 predator
  const role = config.role || ((b.chase_targets && b.chase_targets.length) ? 'predator' : 'prey');
  const detectRadius = percep.detect_radius || b.detect_radius || b.flee_radius || 6.0;
  const visionHalf = (percep.vision_cone_deg || 300) * Math.PI / 180 / 2;
  const collisionBox = intent.collision_box ?? 0.8;
  const catchRadius = intent.catch_radius ?? 0.8;
  const betaTurn = intent.beta_turn_cost ?? 0.2;
  const persistTh = intent.persistence_threshold ?? 1.5;
  const fleeMult = b.flee_speed_multiplier || 1.8;
  const turnRate = role === 'prey' ? 4.5 : 3.2;
  // 可选关系限定（留空=对所有对应角色生效）
  const chaseTargets = b.chase_targets || [];
  const fleeFrom = b.flee_from || [];
  // 交互对手（predator↔prey）不算避碰障碍：捕食者要抓猎物、猎物靠 escape 处理
  const partnerRole = role === 'predator' ? 'prey' : 'predator';
  const isObstacle = (id, p) =>
    p !== pet && id !== state.targetId && (!p.config || p.config.role !== partnerRole);

  const state = {
    hunger: 0,
    fear: 0,
    lastCatchT: 0,
    intention: 'wander',
    memory: null,          // 单项短期记忆 I_s = { intention, targetId }
    targetId: null,
    waypoint: route.length > 1 ? 1 : 0,
    fleeWaypoint: 0,
    dwell: 0,
    _caught: false,
    _pred: null,
    _predDist: Infinity,
  };

  // ── 感知工具 ──
  function nearestByRole(ctx, wantRole, idFilter) {
    let best = null, bestD = Infinity;
    for (const [id, p] of Object.entries(ctx.allPets || {})) {
      if (p === pet) continue;
      if ((p.config && p.config.role) !== wantRole) continue;
      if (idFilter && idFilter.length && !idFilter.includes(id)) continue;
      const d = dist2D(pet.group.position, p.group.position);
      if (d < bestD) { bestD = d; best = p; }
    }
    return best;
  }

  function inVision(other) {
    const d = dist2D(pet.group.position, other.group.position);
    if (d > detectRadius) return false;
    const heading = pet.group.rotation.y + Math.PI / 2;
    const dx = other.group.position.x - pet.group.position.x;
    const dz = other.group.position.z - pet.group.position.z;
    const ang = Math.abs(angleWrap(Math.atan2(dx, dz) - heading));
    return ang <= visionHalf;
  }

  // 碰撞敏感区：除自己/当前目标/交互对手外，任何他者进入 collisionBox → 避碰
  function imminentCollision(ctx) {
    for (const [id, p] of Object.entries(ctx.allPets || {})) {
      if (!isObstacle(id, p)) continue;
      if (dist2D(pet.group.position, p.group.position) < collisionBox) return true;
    }
    return false;
  }

  // Predator 代价函数选目标（论文 §6.1；chase_targets 非空则只考虑列表内猎物）
  function selectPrey(ctx) {
    const heading = pet.group.rotation.y + Math.PI / 2;
    let best = null, bestCost = Infinity, curCost = Infinity;
    for (const [id, p] of Object.entries(ctx.allPets || {})) {
      if (!p.config || p.config.role !== 'prey') continue;
      if (chaseTargets.length && !chaseTargets.includes(id)) continue;
      const dx = p.group.position.x - pet.group.position.x;
      const dz = p.group.position.z - pet.group.position.z;
      const d = Math.hypot(dx, dz);
      const E = angleWrap(Math.atan2(dx, dz) - heading);
      const cost = preyCost(d, E, betaTurn);
      if (p.config.id === state.targetId) curCost = cost;
      if (cost < bestCost) { bestCost = cost; best = p; }
    }
    // 持久化：新目标须比当前目标代价低超过阈值才切换（论文 fickle/devoted）
    const cur = state.targetId && ctx.allPets[state.targetId];
    if (cur && best && best.config.id !== state.targetId && (curCost - bestCost) <= persistTh) {
      return cur;
    }
    return best;
  }

  function farthestWaypoint(fromPos) {
    if (!fromPos || route.length === 0) return state.waypoint;
    let best = 0, bd = -1;
    for (let i = 0; i < route.length; i++) {
      const d = Math.hypot(route[i][0] - fromPos.x, route[i][1] - fromPos.z);
      if (d > bd) { bd = d; best = i; }
    }
    return best;
  }

  // ── 心理状态更新（论文 §4.2）──
  function updateMentalState(dt, t, ctx) {
    if (role === 'predator') {
      state.hunger = computeHunger(t - state.lastCatchT, ms.hunger_full_sec || 20);
    } else {
      const pred = nearestByRole(ctx, 'predator', fleeFrom);
      const d = pred ? dist2D(pet.group.position, pred.group.position) : Infinity;
      state.fear = computeFear(d, ms.fear_scale_D0 || 6.0);
      state._pred = pred;
      state._predDist = d;
    }
  }

  // ── 意图生成器（论文 §5，带优先级 + 单项记忆防抖）──
  function generateIntention(ctx) {
    // 优先级 1: avoid（最高）——压栈当前意图
    if (imminentCollision(ctx)) {
      if (state.intention !== 'avoid') {
        state.memory = { intention: state.intention, targetId: state.targetId };
      }
      state.intention = 'avoid';
      return;
    }
    // avoid 解除 → 弹栈恢复（防 dithering）
    if (state.intention === 'avoid') {
      if (state.memory) {
        state.intention = state.memory.intention;
        state.targetId = state.memory.targetId;
        state.memory = null;
        return;   // 恢复被打断的意图，本帧不再重判（论文单项记忆）
      }
      state.intention = 'wander';
    }

    if (role === 'predator') {
      const prey = selectPrey(ctx);
      const hungry = state.hunger > (ms.hunt_hunger_threshold ?? 0.3);
      if (prey && (hungry || inVision(prey))) {
        state.targetId = prey.config.id;
        state.intention = 'hunt';
        return;
      }
    } else {
      const fEsc = ms.f_escape ?? 0.55;
      const fCalm = ms.f_calm ?? 0.35;
      if (state.fear > fEsc) {
        state.intention = 'escape';
        state.targetId = state._pred ? state._pred.config.id : null;
        return;
      }
      // 滞回区（fCalm ≤ F ≤ fEsc）维持逃逸，避免抖动
      if (state.intention === 'escape' && state.fear >= fCalm) return;
    }

    state.intention = 'wander';
    state.targetId = null;
  }

  // ── 运动：转向 + 前进 + 动画（返回移动前到目标的距离）──
  function moveToward(tx, tz, speed, dt, t) {
    const pos = pet.group.position;
    const dx = tx - pos.x, dz = tz - pos.z;
    const dist = Math.hypot(dx, dz);
    if (dist < 0.001) return dist;
    const desired = Math.atan2(dx, dz) - Math.PI / 2;
    const diff = angleWrap(desired - pet.group.rotation.y);
    pet.group.rotation.y += Math.max(-turnRate * dt, Math.min(turnRate * dt, diff));
    const align = Math.max(0, 1 - Math.abs(diff) / 0.9);
    if (align > 0) {
      const heading = pet.group.rotation.y + Math.PI / 2;
      pos.x += Math.sin(heading) * speed * dt * align;
      pos.z += Math.cos(heading) * speed * dt * align;
      _walkAnimate(pet, t, align, config);
    }
    return dist;
  }

  // ── 行为例程 ──
  function routineWander(dt, t, ctx) {
    if (route.length === 0) { _idleAnimate(pet, t); return; }
    if (state.dwell > 0) { state.dwell -= dt; _idleAnimate(pet, t); return; }
    const [wx, wz] = route[state.waypoint];
    const d = moveToward(wx, wz, baseSpeed, dt, t);
    if (d < 0.32) {
      state.waypoint = (state.waypoint + 1) % route.length;
      state.dwell = dwellRange[0] + Math.random() * (dwellRange[1] - dwellRange[0]);
    }
  }

  function routineHunt(dt, t, ctx) {
    const target = ctx.allPets[state.targetId];
    if (!target) { routineWander(dt, t, ctx); return; }
    const sp = baseSpeed * (1 + 0.5 * state.hunger);   // 越饿越快
    const tp = target.group.position;
    const d = moveToward(tp.x, tp.z, sp, dt, t);
    if (d < catchRadius && !state._caught) {
      state._caught = true;
      state.hunger = 0;
      state.lastCatchT = t;
      if (api.onCatch) api.onCatch(pet, target);
    } else if (d > catchRadius * 2) {
      state._caught = false;   // 拉开距离后允许下次捕获
    }
  }

  function routineEscape(dt, t, ctx) {
    _pulseWarnRing(pet, t, true);
    if (route.length === 0) { _idleAnimate(pet, t); return; }
    const [wx, wz] = route[state.fleeWaypoint];
    const sp = baseSpeed * fleeMult;
    const d = moveToward(wx, wz, sp, dt, t);
    if (d < 0.32) {
      state.fleeWaypoint = farthestWaypoint(state._pred && state._pred.group.position);
    }
  }

  function routineAvoid(dt, t, ctx) {
    // 朝「远离最近障碍」方向前进（转身时几乎原地）
    let threat = null, td = Infinity;
    for (const [id, p] of Object.entries(ctx.allPets || {})) {
      if (!isObstacle(id, p)) continue;
      const d = dist2D(pet.group.position, p.group.position);
      if (d < td) { td = d; threat = p; }
    }
    if (!threat) { routineWander(dt, t, ctx); return; }
    const away = {
      x: pet.group.position.x * 2 - threat.group.position.x,
      z: pet.group.position.z * 2 - threat.group.position.z,
    };
    moveToward(away.x, away.z, baseSpeed, dt, t);
  }

  // ── 每帧 ──
  function step(dt, t, ctx) {
    ctx = ctx || {};
    updateMentalState(dt, t, ctx);
    const prev = state.intention;
    generateIntention(ctx);

    // 上升沿事件
    if (state.intention === 'hunt' && prev !== 'hunt' && api.onDetect) {
      api.onDetect(pet, ctx.allPets[state.targetId]);
    }
    if (state.intention === 'escape' && prev !== 'escape') {
      state.fleeWaypoint = farthestWaypoint(state._pred && state._pred.group.position);
      state.dwell = 0;
    }
    if (state.intention !== 'escape') _pulseWarnRing(pet, t, false);

    switch (state.intention) {
      case 'avoid': routineAvoid(dt, t, ctx); break;
      case 'hunt': routineHunt(dt, t, ctx); break;
      case 'escape': routineEscape(dt, t, ctx); break;
      default: routineWander(dt, t, ctx);
    }
  }

  const api = {
    step,
    onDetect: null,   // 由 ecosystem 设置
    onCatch: null,    // 由 ecosystem 设置
    state,
    get intention() { return state.intention; },
    get isFleeing() { return state.intention === 'escape'; },
  };
  return api;
}

// ── 动画（无 THREE 依赖）──

function _pulseWarnRing(pet, t, active) {
  const ring = pet.parts && pet.parts.warnRing;
  if (!ring) return;
  if (active) {
    const pulse = (Math.sin(t * 10) + 1) / 2;
    ring.material.opacity = 0.3 + pulse * 0.5;
    const rs = 1 + pulse * 0.3;
    ring.scale.set(rs, rs, rs);
  } else {
    ring.material.opacity += (0 - ring.material.opacity) * 0.15;
  }
}

function _walkAnimate(pet, t, align, config) {
  const m = config.model || {};
  const earAmp = m.ear_swing_amplitude ?? 0.3;
  const earFreq = m.ear_swing_freq ?? 10;

  const hop = Math.abs(Math.sin(t * 14));
  pet.group.position.y = hop * 0.08 * align;

  if (pet.parts.legs) {
    pet.parts.legs.forEach((leg, i) => {
      leg.rotation.z = Math.sin(t * 14 + (i % 2 ? Math.PI : 0)) * 0.6 * align;
    });
  }
  if (pet.parts.tailPivot) {
    pet.parts.tailPivot.rotation.z = 0.5 + Math.sin(t * 12) * 0.2;
  } else if (pet.parts.tail) {
    pet.parts.tail.rotation.z = 0.5 + Math.sin(t * 6) * 0.12;
  }
  if (pet.parts.ears) {
    pet.parts.ears.forEach((ear, i) => {
      ear.rotation.x = Math.sin(t * earFreq + i * Math.PI) * earAmp * align;
    });
  }
}

function _idleAnimate(pet, t) {
  pet.group.position.y += (0 - pet.group.position.y) * 0.2;
  if (pet.parts.legs) pet.parts.legs.forEach(leg => { leg.rotation.z += (0 - leg.rotation.z) * 0.2; });
  if (pet.parts.tailPivot) pet.parts.tailPivot.rotation.z = 0.5 + Math.sin(t * 8) * 0.15;
  else if (pet.parts.tail) pet.parts.tail.rotation.z = 0.5 + Math.sin(t * 3) * 0.3;
  if (pet.parts.ears) pet.parts.ears.forEach((ear, i) => { ear.scale.setScalar(1 + Math.sin(t * 10 + i) * 0.1); });
}
