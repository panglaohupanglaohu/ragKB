/**
 * pet-behavior.js — 宠物行为 AI（可插拔）
 * 根据配置创建行为控制器，替代硬编码的猫巡逻/老鼠逃跑逻辑。
 * 
 * 用法:
 *   import { createBehavior } from './pet-behavior.js';
 *   const behavior = createBehavior(pet, config, ecosystem);
 *   // 每帧调用:
 *   behavior.step(dt, t, context);
 */
import * as THREE from 'three';

/**
 * 创建行为控制器
 * @param {Object} pet — buildPet 返回的 { group, parts, drawBubble }
 * @param {Object} config — pet_config 中的行为配置
 * @param {Object} ecosystem — 生态上下文 { allPets, chaseTargets, fleeFrom }
 * @returns {Object} { step, onDetect, isFleeing }
 */
export function createBehavior(pet, config, ecosystem) {
  const b = config.behavior || {};
  const route = b.route || [];
  const speed = b.speed || 1.5;
  const dwellRange = b.dwell_range || [1.0, 3.0];
  const detectRadius = b.detect_radius || b.flee_radius || 4.0;
  
  let waypoint = route.length > 1 ? 1 : 0;
  let dwell = 0;
  let fleeing = false;
  let wasFleeing = false;

  // 行为类型
  const behaviorType = b.type || 'patrol';
  const isFleeType = behaviorType.includes('flee');
  const isChaseType = behaviorType.includes('chase');

  function step(dt, t, ctx) {
    if (route.length === 0) return;
    
    const pos = pet.group.position;
    const allPets = ctx.allPets || {};
    
    // 检测逃跑/追逐目标
    let nearestThreat = null;
    let nearestThreatDist = Infinity;
    const fleeFrom = b.flee_from || [];
    for (const targetId of fleeFrom) {
      const target = allPets[targetId];
      if (!target) continue;
      const d = Math.hypot(pos.x - target.group.position.x, pos.z - target.group.position.z);
      if (d < detectRadius && d < nearestThreatDist) {
        nearestThreat = target;
        nearestThreatDist = d;
      }
    }
    
    wasFleeing = fleeing;
    fleeing = isFleeType && nearestThreat !== null;
    
    // 警告光圈
    if (pet.parts.warnRing) {
      if (fleeing) {
        const pulse = (Math.sin(t * 10) + 1) / 2;
        pet.parts.warnRing.material.opacity = 0.3 + pulse * 0.5;
        const rs = 1 + pulse * 0.3;
        pet.parts.warnRing.scale.set(rs, rs, rs);
      } else {
        pet.parts.warnRing.material.opacity += (0 - pet.parts.warnRing.material.opacity) * 0.15;
      }
    }
    
    // 刚进入逃跑 → 跳到离威胁最远的路点
    if (fleeing && !wasFleeing) {
      let bestWp = waypoint, bestDist = -1;
      const threatPos = nearestThreat.group.position;
      for (let i = 0; i < route.length; i++) {
        const d = Math.hypot(route[i][0] - threatPos.x, route[i][1] - threatPos.z);
        if (d > bestDist) { bestDist = d; bestWp = i; }
      }
      waypoint = bestWp;
      dwell = 0;
      // 触发检测回调（猫念台词）
      if (ctx.onDetect) ctx.onDetect(pet, nearestThreat);
    }
    
    if (dwell > 0) {
      dwell -= dt;
      // 停留动画
      _idleAnimate(pet, t);
    } else {
      const [wx, wz] = route[waypoint];
      const dx = wx - pos.x, dz = wz - pos.z;
      const dist = Math.hypot(dx, dz);
      if (dist < 0.3) {
        waypoint = (waypoint + 1) % route.length;
        dwell = fleeing ? 0 : (dwellRange[0] + Math.random() * (dwellRange[1] - dwellRange[0]));
      } else {
        const desired = Math.atan2(dx, dz) - Math.PI / 2;
        let diff = desired - pet.group.rotation.y;
        while (diff > Math.PI) diff -= Math.PI * 2;
        while (diff < -Math.PI) diff += Math.PI * 2;
        const turn = Math.max(-4.5 * dt, Math.min(4.5 * dt, diff));
        pet.group.rotation.y += turn;
        const align = Math.max(0, 1 - Math.abs(diff) / 0.9);
        if (align > 0) {
          const sp = fleeing ? speed * (b.flee_speed_multiplier || 1.8) : speed;
          const heading = pet.group.rotation.y + Math.PI / 2;
          pet.group.position.x += Math.sin(heading) * sp * dt * align;
          pet.group.position.z += Math.cos(heading) * sp * dt * align;
          _walkAnimate(pet, t, align, config);
        }
      }
    }
  }

  return {
    step,
    get isFleeing() { return fleeing; },
    onDetect: null, // 由外部设置
  };
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
