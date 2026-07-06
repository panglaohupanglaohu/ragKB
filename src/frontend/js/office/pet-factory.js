/**
 * pet-factory.js — 宠物 3D 模型工厂（可插拔）
 * 根据配置动态构建 3D 模型，替代硬编码的 buildCat/buildMouse。
 * 
 * 用法:
 *   import { buildPet } from './pet-factory.js';
 *   const pet = buildPet(config, THREE);  // → { group, parts, drawBubble }
 */
import * as THREE from 'three';

/**
 * 根据配置构建宠物 3D 模型
 * @param {Object} config — pet_config.json 中的单个 pet 配置
 * @param {Function} makeLabel — 名牌创建函数
 * @returns {Object} { group, parts, drawBubble }
 */
export function buildPet(config, makeLabel) {
  const modelType = (config.model && config.model.type) || 'builtin_cat';
  const builders = {
    builtin_cat: () => _buildCat(config, makeLabel),
    builtin_mouse: () => _buildMouse(config, makeLabel),
  };
  const builder = builders[modelType] || builders.builtin_cat;
  return builder();
}

// ── 猫模型 ──
function _buildCat(config, makeLabel) {
  const m = config.model || {};
  const g = new THREE.Group();
  const furColor = parseInt(m.fur_color || '0xf2f2f2');
  const furMat = new THREE.MeshStandardMaterial({ color: furColor, roughness: 0.85 });

  // 腿
  const legs = [];
  for (const [lx, lz] of [[0.17, 0.09], [0.17, -0.09], [-0.17, 0.09], [-0.17, -0.09]]) {
    const leg = new THREE.Mesh(new THREE.ConeGeometry(0.06, 0.26, 8), furMat);
    leg.position.set(lx, 0.13, lz); leg.rotation.x = Math.PI; leg.castShadow = true;
    g.add(leg); legs.push(leg);
  }
  // 身体
  _box(0.56, 0.24, 0.26, 0, 0.32, 0, furMat, g);
  // 头
  _box(0.28, 0.26, 0.26, 0.42, 0.50, 0, furMat, g);
  // 耳朵
  const earX = m.ear_position_x ?? 0.52;
  const earY = m.ear_position_y ?? 0.69;
  const ears = [];
  for (const s of [-1, 1]) {
    const ear = new THREE.Mesh(new THREE.ConeGeometry(0.08, 0.16, 4), furMat);
    ear.position.set(earX, earY, 0.095 * s); ear.castShadow = true;
    g.add(ear); ears.push(ear);
  }
  // 尾巴
  const tail = _box(0.07, 0.44, 0.07, -0.34, 0.5, 0, furMat, g);
  tail.rotation.z = 0.5;

  // 气泡
  const bubble = _makeBubble(g);

  // 名牌
  g.add(makeLabel(config.name || '猫'));

  g.scale.setScalar(m.scale || 1.0);
  return { group: g, parts: { legs, ears, tail }, drawBubble: bubble.draw };
}

// ── 老鼠模型 ──
function _buildMouse(config, makeLabel) {
  const m = config.model || {};
  const g = new THREE.Group();
  const furColor = parseInt(m.fur_color || '0x9a9a9e');
  const pinkColor = parseInt(m.pink_color || '0xd9a0a8');
  const furMat = new THREE.MeshStandardMaterial({ color: furColor, roughness: 0.9 });
  const pinkMat = new THREE.MeshStandardMaterial({ color: pinkColor, roughness: 0.6 });

  // 腿
  const legs = [];
  for (const [lx, lz] of [[0.10, 0.05], [0.10, -0.05], [-0.10, 0.05], [-0.10, -0.05]]) {
    const leg = new THREE.Mesh(new THREE.ConeGeometry(0.035, 0.14, 6), furMat);
    leg.position.set(lx, 0.07, lz); leg.rotation.x = Math.PI; leg.castShadow = true;
    g.add(leg); legs.push(leg);
  }
  // 身体
  const body = new THREE.Mesh(new THREE.SphereGeometry(0.16, 12, 10), furMat);
  body.scale.set(1.3, 0.8, 0.7); body.position.set(0, 0.18, 0); body.castShadow = true;
  g.add(body);
  // 头
  const head = new THREE.Mesh(new THREE.SphereGeometry(0.11, 10, 8), furMat);
  head.position.set(0.22, 0.22, 0); head.castShadow = true; g.add(head);
  // 尖嘴
  const nose = new THREE.Mesh(new THREE.ConeGeometry(0.04, 0.10, 6), pinkMat);
  nose.position.set(0.33, 0.20, 0); nose.rotation.z = -Math.PI / 2; g.add(nose);
  // 耳朵
  const ears = [];
  for (const s of [-1, 1]) {
    const ear = new THREE.Mesh(new THREE.SphereGeometry(0.05, 8, 6), furMat);
    ear.position.set(0.18, 0.33, 0.06 * s); ear.castShadow = true;
    g.add(ear); ears.push(ear);
  }
  // 眼睛
  const eyeMat = new THREE.MeshBasicMaterial({ color: 0xe04040 });
  for (const s of [-1, 1]) {
    const eye = new THREE.Mesh(new THREE.SphereGeometry(0.018, 6, 4), eyeMat);
    eye.position.set(0.28, 0.25, 0.04 * s); g.add(eye);
  }
  // 尾巴（枢轴模式）
  const tailPivot = new THREE.Group();
  tailPivot.position.set(-0.18, 0.20, 0); g.add(tailPivot);
  const tailLen = m.tail_length || 0.55;
  const tail = new THREE.Mesh(
    new THREE.CylinderGeometry(m.tail_radius_top || 0.008, m.tail_radius_bottom || 0.018, tailLen, 6),
    pinkMat
  );
  tail.position.set(-tailLen / 2, 0, 0);
  tail.rotation.z = Math.PI / 2;
  tail.castShadow = true;
  tailPivot.add(tail);
  tailPivot.rotation.z = 0.5;

  // 警告光圈（可选）
  let warnRing = null;
  if (config.behavior && config.behavior.warn_ring) {
    const ringColor = parseInt(config.behavior.warn_ring_color || '0xe04040');
    warnRing = new THREE.Mesh(
      new THREE.RingGeometry(0.25, 0.40, 32),
      new THREE.MeshBasicMaterial({ color: ringColor, transparent: true, opacity: 0, side: THREE.DoubleSide })
    );
    warnRing.rotation.x = -Math.PI / 2; warnRing.position.y = 0.02;
    g.add(warnRing);
  }

  // 气泡
  const bubble = _makeBubble(g);
  // 名牌
  g.add(makeLabel(config.name || '老鼠'));

  g.scale.setScalar(m.scale || 0.85);
  return { group: g, parts: { legs, ears, tailPivot, warnRing }, drawBubble: bubble.draw };
}

// ── 通用工具 ──
function _box(w, h, d, x, y, z, mat, parent) {
  const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), mat || new THREE.MeshStandardMaterial({ color: 0xf7f7f8 }));
  m.position.set(x, y, z); m.castShadow = true; m.receiveShadow = true;
  (parent || null).add(m); return m;
}

function _makeBubble(parent) {
  const cv = document.createElement('canvas');
  cv.width = 512; cv.height = 320;
  const tex = new THREE.CanvasTexture(cv);
  const sp = new THREE.Sprite(new THREE.SpriteMaterial({ map: tex, transparent: true, depthTest: false }));
  sp.scale.set(5.5, 3.4375, 1); sp.position.y = 2.6; sp.visible = false;
  parent.add(sp);
  function draw(text) {
    const ctx = cv.getContext('2d');
    ctx.clearRect(0, 0, 512, 320);
    if (!text) { tex.needsUpdate = true; sp.visible = false; return; }
    ctx.font = '22px sans-serif';
    const lines = []; let cur = '';
    for (const ch of String(text)) {
      if (ch === '\n' || ctx.measureText(cur + ch).width > 460) {
        lines.push(cur); cur = ch === '\n' ? '' : ch;
        if (lines.length === 6) { cur += '…'; break; }
      } else cur += ch;
    }
    if (cur && lines.length < 6) lines.push(cur);
    const h = 28 + lines.length * 28;
    ctx.fillStyle = 'rgba(255,255,255,0.96)';
    ctx.strokeStyle = '#c8cdd4'; ctx.lineWidth = 3;
    ctx.beginPath(); ctx.roundRect(8, 8, 496, h, 16); ctx.fill(); ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(236, h + 8); ctx.lineTo(256, h + 30); ctx.lineTo(276, h + 8);
    ctx.closePath(); ctx.fill();
    ctx.fillStyle = '#2a2e34';
    lines.forEach((l, i) => ctx.fillText(l, 24, 42 + i * 30));
    tex.needsUpdate = true; sp.visible = true;
  }
  return { draw, sprite: sp };
}
