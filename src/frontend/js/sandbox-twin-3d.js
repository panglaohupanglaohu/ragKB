/**
 * sandbox-twin-3d.js — SECS 演练总台 3D 场景
 * 从数字孪生拉取 6 个房间，场景选择后实际切换 3D 场景
 * 加载方式: <script type="module" src="/js/sandbox-twin-3d.js"></script>
 */
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

// ── 全局状态 ──
let scene, camera, renderer, controls, clock;
let initialized = false;
let agentFigures = [];
let commLineGroup;
let centerLabel;
let dustParticles;
let stepNumber = 0;
let currentRoomId = 'training-ground';
let currentRoomName = '演练场';

// 房间 ID → 名称映射
const ROOM_MAP = {
  'council-hall':    { name: '议事厅', bg: 0x1A2026, accent: 0xD4A44A, fog: 0.0076 },
  'extraction-lab':  { name: '萃取室', bg: 0x0D1520, accent: 0x6B9FD4, fog: 0.009 },
  'workshop':        { name: '工作坊', bg: 0x141E2A, accent: 0x9B8EC4, fog: 0.008 },
  'knowledge-base':  { name: '知识库', bg: 0x181A1F, accent: 0xD4A44A, fog: 0.007 },
  'training-ground': { name: '演练场', bg: 0x111820, accent: 0x6BC47F, fog: 0.008 },
  'rest-area':       { name: '休息区', bg: 0x1C1A18, accent: 0xE8A060, fog: 0.006 },
};

// 5 角色定义
const ROLES = [
  { id: 'planner',     name: 'Planner',    color: '#6BC47F', label: '规划者' },
  { id: 'retriever',   name: 'Retriever',  color: '#6B9FD4', label: '检索者' },
  { id: 'coordinator', name: 'Coordinator',color: '#D4A44A', label: '协调者' },
  { id: 'executor',    name: 'Executor',   color: '#9B8EC4', label: '执行者' },
  { id: 'critic',      name: 'Critic',     color: '#E07070', label: '校验者' },
];

// ── 工具函数 ──

function makeLabel(text, hexColor) {
  const c = document.createElement('canvas');
  c.width = 256; c.height = 64;
  const ctx = c.getContext('2d');
  ctx.font = 'bold 28px "Noto Sans SC", sans-serif';
  ctx.fillStyle = hexColor || '#ffffff';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText(text, 128, 32);
  return c;
}

function mkMat(color, opts) {
  return new THREE.MeshStandardMaterial(Object.assign({ color: new THREE.Color(color), roughness: 0.7, metalness: 0.1 }, opts));
}

function mkBasic(color, opts) {
  return new THREE.MeshBasicMaterial(Object.assign({ color: new THREE.Color(color) }, opts));
}

// ── Agent 人形 ──
function createAgentFigure(role, index, total) {
  const group = new THREE.Group();
  const col = new THREE.Color(role.color);
  const angle = (Math.PI * 2 * index) / total - Math.PI / 2;
  const radius = 5.5;
  const x = radius * Math.cos(angle);
  const z = radius * Math.sin(angle);

  const headRing = new THREE.Mesh(new THREE.TorusGeometry(0.32, 0.04, 12, 32), mkBasic(role.color, { transparent: true, opacity: 0.8 }));
  headRing.position.y = 2.0; group.add(headRing);

  const headGlow = new THREE.Mesh(new THREE.TorusGeometry(0.32, 0.14, 12, 32), mkBasic(role.color, { transparent: true, opacity: 0.25 }));
  headGlow.position.y = 2.0; group.add(headGlow);

  const pts = [];
  for (let i = 0; i <= 24; i++) { const t = i / 24; pts.push(new THREE.Vector3(-Math.cos(Math.PI * t) * 0.42, 1.1 - Math.sin(Math.PI * t) * 0.55, 0)); }
  const body = new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts), 24, 0.03, 8, false), mkBasic(role.color, { transparent: true, opacity: 0.7 }));
  group.add(body);

  const groundRing = new THREE.Mesh(new THREE.RingGeometry(0.4, 0.55, 32), mkBasic(role.color, { transparent: true, opacity: 0.25, side: THREE.DoubleSide }));
  groundRing.rotation.x = -Math.PI / 2; groundRing.position.y = 0.02; group.add(groundRing);
  group.userData.glowRing = groundRing;

  const tex = new THREE.CanvasTexture(makeLabel(role.name, role.color)); tex.minFilter = THREE.LinearFilter;
  const sprite = new THREE.Sprite(new THREE.SpriteMaterial({ map: tex, transparent: true, depthTest: false }));
  sprite.position.y = 2.9; sprite.scale.set(1.8, 0.48, 1); group.add(sprite);

  group.position.set(x, 0, z); group.lookAt(0, 0.8, 0);
  group.userData.role = role.id;
  group.userData.active = false;
  group.userData.pulsePhase = Math.random() * Math.PI * 2;
  return group;
}

// ── 通信连线 ──
function createCommLine(from, to, color) {
  const group = new THREE.Group();
  const start = from.position.clone(); start.y = 1.2;
  const end = to.position.clone(); end.y = 1.2;
  const mid = new THREE.Vector3().addVectors(start, end).multiplyScalar(0.5); mid.y += 1.8;
  const curve = new THREE.QuadraticBezierCurve3(start, mid, end);
  const geom = new THREE.BufferGeometry(); geom.setFromPoints(curve.getPoints(32));
  const mat = new THREE.LineBasicMaterial({ color: new THREE.Color(color), transparent: true, opacity: 0.15 });
  const line = new THREE.Line(geom, mat);
  group.add(line);
  group.userData.material = mat;
  group.userData.baseOpacity = 0.15;
  group.userData.activeOpacity = 0.6;
  return group;
}

// ── 粒子 ──
function buildDust(count, radius, colorHex) {
  const pos = new Float32Array(count * 3);
  for (let i = 0; i < count; i++) { pos[i * 3] = (Math.random() - 0.5) * radius; pos[i * 3 + 1] = Math.random() * 10; pos[i * 3 + 2] = (Math.random() - 0.5) * radius; }
  const geo = new THREE.BufferGeometry(); geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  return new THREE.Points(geo, new THREE.PointsMaterial({ color: colorHex || 0x6BC47F, size: 0.04, transparent: true, opacity: 0.25 }));
}

// ══════════════════════════════════════════════════
// 6 个房间建造函数
// ══════════════════════════════════════════════════

function addBaseLighting(ambientColor, hemSky, hemGround, hemIntensity) {
  scene.add(new THREE.AmbientLight(ambientColor, 0.18));
  scene.add(new THREE.HemisphereLight(hemSky, hemGround, hemIntensity || 0.06));
}

function buildTrainingGround() {
  addBaseLighting(0x8899aa, 0x8899bb, 0x334455);
  const dl = new THREE.DirectionalLight(0xccddee, 0.5); dl.position.set(3, 18, 5); scene.add(dl);

  const floor = new THREE.Mesh(new THREE.CircleGeometry(8, 64), mkMat(0x2a3040, { roughness: 0.85 }));
  floor.rotation.x = -Math.PI / 2; scene.add(floor);

  const grid = new THREE.PolarGridHelper(7.5, 24, 12, 64, 0x4a5568, 0x4a5568);
  grid.position.y = 0.01; scene.add(grid);

  const outer = new THREE.Mesh(new THREE.TorusGeometry(7.2, 0.06, 8, 64), mkBasic(0x5cb6c4, { transparent: true, opacity: 0.25 }));
  outer.rotation.x = -Math.PI / 2; outer.position.y = 0.03; scene.add(outer);

  const inner = new THREE.Mesh(new THREE.TorusGeometry(3.0, 0.04, 8, 48), mkBasic(0x6bc47f, { transparent: true, opacity: 0.2 }));
  inner.rotation.x = -Math.PI / 2; inner.position.y = 0.03; scene.add(inner);

  // 障碍柱
  for (let i = 0; i < 6; i++) {
    const a = (Math.PI * 2 * i) / 6;
    const p = new THREE.Mesh(new THREE.CylinderGeometry(0.2, 0.3, 1.8, 8), mkMat(0x4a5060, { roughness: 0.5, metalness: 0.5 }));
    p.position.set(Math.cos(a) * 4.5, 0.9, Math.sin(a) * 4.5); scene.add(p);
  }

  return { accent: 0x6bc47f };
}

function buildCouncilHall() {
  addBaseLighting(0x9099A2, 0x98A2AB, 0x353D46, 0.04);
  const dl = new THREE.DirectionalLight(0xC7D0D8, 0.46); dl.position.set(3, 30, 5); scene.add(dl);

  const floor = new THREE.Mesh(new THREE.CircleGeometry(35, 64), mkMat(0xA9AFB5, { roughness: 0.92 }));
  floor.rotation.x = -Math.PI / 2; floor.receiveShadow = true; scene.add(floor);

  // 三层阶梯看台
  const tiers = [
    { iR: 14, oR: 19, y: 2.4, h: 1.0, c: 0x7F8790 },
    { iR: 9,  oR: 13, y: 1.5, h: 0.8, c: 0x939BA4 },
    { iR: 5,  oR: 8,  y: 0.7, h: 0.6, c: 0xAEB5BC },
  ];
  tiers.forEach(t => {
    const top = new THREE.Mesh(new THREE.RingGeometry(t.iR, t.oR, 96), mkMat(t.c, { roughness: 0.88 }));
    top.rotation.x = -Math.PI / 2; top.position.y = t.y; scene.add(top);
    const wall = new THREE.Mesh(new THREE.CylinderGeometry(t.iR, t.iR, t.h, 96, 1, true), mkMat(new THREE.Color(t.c).multiplyScalar(0.72).getHex(), { roughness: 0.92 }));
    wall.position.y = t.y - t.h / 2; scene.add(wall);
  });

  // 中央竞技场
  const center = new THREE.Mesh(new THREE.CircleGeometry(4.5, 64), mkMat(0xE2E6E9, { roughness: 0.72 }));
  center.rotation.x = -Math.PI / 2; center.position.y = 0.01; scene.add(center);

  return { accent: 0xD4A44A };
}

function buildExtractionLab() {
  addBaseLighting(0x334466, 0x4466aa, 0x112233);
  const dl = new THREE.DirectionalLight(0x6688cc, 0.35); dl.position.set(-5, 15, 3); scene.add(dl);
  const pl = new THREE.PointLight(0x6B9FD4, 0.4, 18); pl.position.set(0, 4, 0); scene.add(pl);

  const floor = new THREE.Mesh(new THREE.CircleGeometry(8, 64), mkMat(0x1a1e2a, { roughness: 0.6, metalness: 0.4 }));
  floor.rotation.x = -Math.PI / 2; scene.add(floor);

  // 六边形网格线
  const hexGrid = new THREE.PolarGridHelper(7.5, 12, 8, 64, 0x3a5588, 0x3a5588);
  hexGrid.position.y = 0.01; scene.add(hexGrid);

  // 萃取水晶柱
  for (let i = 0; i < 5; i++) {
    const a = (Math.PI * 2 * i) / 5;
    const x = Math.cos(a) * 5, z = Math.sin(a) * 5;
    const crystal = new THREE.Mesh(new THREE.OctahedronGeometry(0.35, 0), mkBasic(0x6B9FD4, { transparent: true, opacity: 0.7 }));
    crystal.position.set(x, 2.5, z);
    const wire = new THREE.Mesh(new THREE.OctahedronGeometry(0.45, 0), mkBasic(0x6B9FD4, { wireframe: true, transparent: true, opacity: 0.25 }));
    crystal.add(wire);
    scene.add(crystal);
    // 水晶底座
    const base = new THREE.Mesh(new THREE.CylinderGeometry(0.2, 0.25, 0.3, 8), mkMat(0x334466));
    base.position.set(x, 0.15, z); scene.add(base);
  }

  return { accent: 0x6B9FD4 };
}

function buildWorkshop() {
  addBaseLighting(0x556688, 0x6677aa, 0x223344);
  const dl = new THREE.DirectionalLight(0xaab8d8, 0.4); dl.position.set(4, 16, -3); scene.add(dl);

  const floor = new THREE.Mesh(new THREE.PlaneGeometry(16, 16), mkMat(0x1e2430, { roughness: 0.75, metalness: 0.2 }));
  floor.rotation.x = -Math.PI / 2; scene.add(floor);

  // 方格地板线
  for (let i = -7; i <= 7; i += 2) {
    const hMat = mkBasic(0x445566, { transparent: true, opacity: 0.15, side: THREE.DoubleSide });
    const hl = new THREE.Mesh(new THREE.PlaneGeometry(15, 0.03), hMat);
    hl.rotation.x = -Math.PI / 2; hl.position.set(0, 0.015, i); scene.add(hl);
    const vl = new THREE.Mesh(new THREE.PlaneGeometry(15, 0.03), hMat.clone());
    vl.rotation.x = -Math.PI / 2; vl.rotation.z = Math.PI / 2; vl.position.set(i, 0.015, 0); scene.add(vl);
  }

  // 工作台
  for (let i = 0; i < 4; i++) {
    const a = (Math.PI * 2 * i) / 4 + Math.PI / 4;
    const x = Math.cos(a) * 6, z = Math.sin(a) * 6;
    const bench = new THREE.Mesh(new THREE.BoxGeometry(1.8, 0.15, 1.0), mkMat(0x5a5a70, { roughness: 0.5, metalness: 0.6 }));
    bench.position.set(x, 0.9, z); scene.add(bench);
    const leg1 = new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.08, 0.85, 8), mkMat(0x4a4a60));
    leg1.position.set(x - 0.6, 0.42, z); scene.add(leg1);
    const leg2 = new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.08, 0.85, 8), mkMat(0x4a4a60));
    leg2.position.set(x + 0.6, 0.42, z); scene.add(leg2);
  }

  return { accent: 0x9B8EC4 };
}

function buildKnowledgeBase() {
  addBaseLighting(0x665544, 0x887744, 0x332211);
  const dl = new THREE.DirectionalLight(0xddcc88, 0.35); dl.position.set(2, 14, 4); scene.add(dl);
  const pl = new THREE.PointLight(0xD4A44A, 0.3, 20); pl.position.set(0, 5, 0); scene.add(pl);

  const floor = new THREE.Mesh(new THREE.CircleGeometry(8, 64), mkMat(0x2a2518, { roughness: 0.9 }));
  floor.rotation.x = -Math.PI / 2; scene.add(floor);

  const grid = new THREE.PolarGridHelper(7.5, 12, 48, 64, 0x5a5030, 0x5a5030);
  grid.position.y = 0.01; scene.add(grid);

  // 书架柱
  for (let i = 0; i < 8; i++) {
    const a = (Math.PI * 2 * i) / 8;
    const x = Math.cos(a) * 6, z = Math.sin(a) * 6;
    const pillar = new THREE.Mesh(new THREE.CylinderGeometry(0.25, 0.35, 4.5, 12), mkMat(0x5a4830, { roughness: 0.8 }));
    pillar.position.set(x, 2.25, z); scene.add(pillar);
    // 书架横板
    for (let j = 0; j < 3; j++) {
      const shelf = new THREE.Mesh(new THREE.BoxGeometry(0.9, 0.06, 0.4), mkMat(0x6b5840));
      shelf.position.set(x, 1.0 + j * 1.3, z); shelf.rotation.y = a;
      scene.add(shelf);
    }
  }

  return { accent: 0xD4A44A };
}

function buildRestArea() {
  addBaseLighting(0x887766, 0x998877, 0x443322);
  const dl = new THREE.DirectionalLight(0xeeddcc, 0.4); dl.position.set(-2, 12, 6); scene.add(dl);
  const pl = new THREE.PointLight(0xE8A060, 0.35, 16); pl.position.set(0, 3, 0); scene.add(pl);

  const floor = new THREE.Mesh(new THREE.CircleGeometry(8, 64), mkMat(0x2e2822, { roughness: 0.9 }));
  floor.rotation.x = -Math.PI / 2; scene.add(floor);

  // 波浪装饰环
  for (let i = 0; i < 3; i++) {
    const r = 3 + i;
    const waveRing = new THREE.Mesh(new THREE.TorusGeometry(r, 0.04, 8, 64), mkBasic(0xE8A060, { transparent: true, opacity: 0.12 }));
    waveRing.rotation.x = -Math.PI / 2; waveRing.position.y = 0.02; scene.add(waveRing);
  }

  // 圆形坐垫
  for (let i = 0; i < 6; i++) {
    const a = (Math.PI * 2 * i) / 6;
    const x = Math.cos(a) * 4.5, z = Math.sin(a) * 4.5;
    const cushion = new THREE.Mesh(new THREE.CylinderGeometry(0.6, 0.7, 0.25, 16), mkMat(0x5a4030, { roughness: 0.95 }));
    cushion.position.set(x, 0.12, z); scene.add(cushion);
  }

  return { accent: 0xE8A060 };
}

// ══════════════════════════════════════════════════
// 核心 API
// ══════════════════════════════════════════════════

function clearScene() {
  scene.traverse(o => { if (o.geometry) o.geometry.dispose(); if (o.material) { if (Array.isArray(o.material)) o.material.forEach(m => m.dispose()); else o.material.dispose(); } });
  while (scene.children.length > 0) scene.remove(scene.children[0]);
  agentFigures = [];
  commLineGroup = null;
  dustParticles = null;
  centerLabel = null;
}

function spawnAgents() {
  ROLES.forEach((role, i) => {
    const group = createAgentFigure(role, i, ROLES.length);
    scene.add(group);
    agentFigures.push({ group, role: role.id, color: role.color, commLines: new Map(), pulsePhase: Math.random() * Math.PI * 2 });
  });
}

function buildCommNetwork() {
  commLineGroup = new THREE.Group();
  for (let i = 0; i < agentFigures.length; i++) {
    for (let j = i + 1; j < agentFigures.length; j++) {
      const cl = createCommLine(agentFigures[i].group, agentFigures[j].group, agentFigures[i].color);
      commLineGroup.add(cl);
      agentFigures[i].commLines.set(agentFigures[j].role, cl);
      agentFigures[j].commLines.set(agentFigures[i].role, cl);
    }
  }
  scene.add(commLineGroup);
}

function buildRoom(roomId) {
  if (!initialized) return;
  clearScene();

  const info = ROOM_MAP[roomId] || ROOM_MAP['training-ground'];
  currentRoomId = roomId;
  currentRoomName = info.name;

  scene.background = new THREE.Color(info.bg);
  scene.fog = new THREE.FogExp2(info.bg, info.fog);
  renderer.setClearColor(info.bg);

  switch (roomId) {
    case 'council-hall':    buildCouncilHall(); break;
    case 'extraction-lab':  buildExtractionLab(); break;
    case 'workshop':        buildWorkshop(); break;
    case 'knowledge-base':  buildKnowledgeBase(); break;
    case 'rest-area':       buildRestArea(); break;
    default:                buildTrainingGround(); break;
  }

  // 中央步骤标签
  const stepTex = new THREE.CanvasTexture(makeLabel('步: ' + stepNumber, '#' + new THREE.Color(info.accent).getHexString()));
  stepTex.minFilter = THREE.LinearFilter;
  centerLabel = new THREE.Sprite(new THREE.SpriteMaterial({ map: stepTex, transparent: true, depthTest: false }));
  centerLabel.position.set(0, 2.8, 0);
  centerLabel.scale.set(1.6, 0.45, 1);
  scene.add(centerLabel);

  // 粒子
  dustParticles = buildDust(200, 14, info.accent);
  scene.add(dustParticles);

  spawnAgents();
  buildCommNetwork();
  updateInfo();
}

// ── 场景初始化 ──
function initScene() {
  const container = document.getElementById('scene-3d-container');
  const canvas = document.getElementById('scene-3d-canvas');
  if (!container || !canvas) return false;
  const W = container.clientWidth || 600;
  const H = container.clientHeight || 400;

  scene = new THREE.Scene();
  scene.background = new THREE.Color(0x111820);

  camera = new THREE.PerspectiveCamera(45, W / H, 0.5, 100);
  camera.position.set(0, 12, 16);

  renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: false });
  renderer.setSize(W, H);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

  controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true; controls.dampingFactor = 0.08;
  controls.minDistance = 5; controls.maxDistance = 30;
  controls.maxPolarAngle = Math.PI / 1.8; controls.target.set(0, 0.8, 0);
  controls.autoRotate = true; controls.autoRotateSpeed = 0.3;

  clock = new THREE.Clock();

  if (!window._sw3dResize) {
    window._sw3dResize = new ResizeObserver(() => {
      if (!container || !renderer) return;
      const w = container.clientWidth, h = container.clientHeight;
      if (w && h) { camera.aspect = w / h; camera.updateProjectionMatrix(); renderer.setSize(w, h); }
    });
    window._sw3dResize.observe(container);
  }

  initialized = true;
  buildRoom(currentRoomId);
  animate();
  return true;
}

// ── 动画 ──
function animate() {
  requestAnimationFrame(animate);
  if (!initialized) return;
  const dt = Math.min(clock.getDelta(), 0.1);
  const t = clock.getElapsedTime();
  controls.update();

  agentFigures.forEach(af => {
    const gr = af.group.userData.glowRing;
    if (!gr) return;
    if (af.group.userData.active) {
      gr.material.opacity = 0.6 + Math.sin(t * 8 + af.pulsePhase) * 0.4;
      gr.scale.setScalar(1 + Math.sin(t * 8 + af.pulsePhase) * 0.2);
    } else {
      gr.material.opacity = 0.2 + Math.sin(t * 1.5 + af.pulsePhase) * 0.1;
      gr.scale.setScalar(1);
    }
  });

  if (commLineGroup) {
    commLineGroup.children.forEach(cl => {
      if (cl.userData.material) {
        const target = cl.userData._pulseTarget || cl.userData.baseOpacity;
        cl.userData.material.opacity += (target - cl.userData.material.opacity) * 0.1;
      }
    });
  }

  if (dustParticles) {
    dustParticles.rotation.y += dt * 0.03;
    dustParticles.position.y = Math.sin(t * 0.5) * 0.5;
  }

  renderer.render(scene, camera);
}

function updateInfo() {
  const el = document.getElementById('scene-3d-info');
  if (el) el.textContent = currentRoomName + ' · ' + agentFigures.length + ' Agent · 步 ' + stepNumber;
}

function updateStep(n) {
  stepNumber = n;
  if (centerLabel) {
    const info = ROOM_MAP[currentRoomId] || ROOM_MAP['training-ground'];
    const tex = new THREE.CanvasTexture(makeLabel('步: ' + n, '#' + new THREE.Color(info.accent).getHexString()));
    tex.minFilter = THREE.LinearFilter;
    centerLabel.material.map = tex;
    centerLabel.material.needsUpdate = true;
  }
  updateInfo();
}

function activateAgent(roleId, duration) {
  const af = agentFigures.find(a => a.role === roleId);
  if (!af) return;
  af.group.userData.active = true;
  clearTimeout(af._deactivateTimeout);
  af._deactivateTimeout = setTimeout(() => { af.group.userData.active = false; }, duration || 2000);
}

function pulseCommLine(fromRole, toRole, intensity) {
  const from = agentFigures.find(a => a.role === fromRole);
  const to = agentFigures.find(a => a.role === toRole);
  if (!from || !to) return;
  let cl = from.commLines.get(toRole) || to.commLines.get(fromRole);
  if (!cl) return;
  const target = cl.userData.activeOpacity * (intensity || 0.7);
  cl.userData._pulseTarget = target;
  clearTimeout(cl.userData._fadeTimeout);
  cl.userData._fadeTimeout = setTimeout(() => { cl.userData._pulseTarget = cl.userData.baseOpacity; }, 1500);
}

function setRoom(roomId) {
  const info = ROOM_MAP[roomId];
  if (!info) return;
  buildRoom(roomId);
  const el = document.getElementById('scene-3d-label');
  if (el) el.textContent = info.name;
}

function resetView() {
  if (!camera || !controls) return;
  camera.position.set(0, 12, 16); controls.target.set(0, 0.8, 0); controls.update();
}

function topView() {
  if (!camera || !controls) return;
  camera.position.set(0, 22, 0.5); controls.target.set(0, 0.8, 0); controls.update();
}

function frontView() {
  if (!camera || !controls) return;
  camera.position.set(0, 2, 18); controls.target.set(0, 0.8, 0); controls.update();
}

// ── 导出 ──
window._sw3d = {
  init: initScene,
  buildRoom,
  setRoom,
  updateStep,
  activateAgent,
  pulseCommLine,
  resetView,
  topView,
  frontView,
  getCurrentRoom: () => currentRoomId,
  getCurrentRoomName: () => currentRoomName,
  isInitialized: () => initialized,
};

window.sw3dTopView = topView;
window.sw3dFrontView = frontView;
window.sw3dResetView = resetView;

// 自动初始化
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => { setTimeout(() => initScene(), 300); });
} else {
  setTimeout(() => initScene(), 300);
}
