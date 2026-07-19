import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { buildExtractRouting } from './extract-routing.js';

/* ═══════════ GLOBALS ═══════════ */
const API = '/api/v1/agent-config';
// E-3: TTS 日志收敛 — 默认静默
const DEBUG_TTS = false;
const tlog = (...a) => { if (DEBUG_TTS) console.log(...a); };
const twarn = (...a) => { if (DEBUG_TTS) console.warn(...a); };
let curPlaza = null, curDisc = null, curDiscData = null, evtSrc = null;
let allTeams = [], allParticipants = [];
let knownPlazas = [];
let curVerificationState = null;
let curConsensusState = null;
let curEscalationState = null;
const escalationFetchBlocked = new Set();
const escalationFetchInFlight = new Set();
let discussionSignalTimer = null;
// 用户正在交互 plan-panel（滚动/点击）时，延迟重渲染避免闪烁
let _planPanelBusy = false;
let _planPanelBusyTimer = null;
// SSE reconnect state
let _sseRetryTimer = null, _sseRetryDelay = 1000, _sseClosedByUs = false;
const SSE_MAX_DELAY = 10000;
// Rendered-message dedup (guards against SSE history replay on reconnect)
const _seenMsgKeys = new Set();
function msgKey(m) { return m?.id || `${m?.round_number || 0}|${m?.agent_id || ''}|${String(m?.content ?? '').slice(0, 40)}`; }
function markMsgSeen(m) { _seenMsgKeys.add(msgKey(m)); }
const Q = new URLSearchParams(window.location.search);
const deepLinkPlazaId = Q.get('plaza_id') || '';
const deepLinkDiscussionId = Q.get('discussion_id') || '';
const $ = id => document.getElementById(id);
const esc = s => String(s ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
const asItems = payload => Array.isArray(payload) ? payload : Array.isArray(payload?.items) ? payload.items : [];

function stripQueryParams(keys) {
  if (!Array.isArray(keys) || !keys.length) return;
  try {
    const u = new URL(window.location.href);
    let changed = false;
    keys.forEach(k => {
      if (u.searchParams.has(k)) {
        u.searchParams.delete(k);
        changed = true;
      }
    });
    if (changed) window.history.replaceState({}, '', `${u.pathname}${u.search}${u.hash}`);
  } catch (e) {
    // ignore URL cleanup failures
  }
}

function normalizePlazaSelectionOnError() {
  curPlaza = null;
  curDisc = null;
  curDiscData = null;
  curVerificationState = null;
  curConsensusState = null;
  curEscalationState = null;
  localStorage.removeItem('plaza_curPlaza');
  localStorage.removeItem('plaza_curDisc');
  clearDiscussionSignals();
  clearSpeechPlayback();
  teardownSSE();
  renderArena3D([]);
  $('disc-list').innerHTML = '<div style="color:var(--dim);font-size:10px">先选择广场</div>';
  $('msg-log').innerHTML = '<div style="text-align:center;padding:40px 0;color:var(--dim);font-size:10px;letter-spacing:1px;font-family:var(--font-mono)">SELECT PLAZA · CREATE DISCUSSION<br>全员自动入座</div>';
  $('plan-panel').style.display = 'none';
  $('btn-start').disabled = true;
  $('btn-start').textContent = '开始';
  $('status-text').textContent = '';
}

function isKnownPlaza(id) {
  if (!id) return false;
  return knownPlazas.some(p => p.id === id);
}

function activePlazaIdFromDOM() {
  return document.querySelector('#plaza-list .plaza-card.active')?.dataset?.plazaId || '';
}

function activeDiscussionIdFromDOM() {
  return document.querySelector('#disc-list .disc-item.active')?.dataset?.discussionId || '';
}

function escalationCtxKey(plazaId, discussionId) {
  return `${String(plazaId || '')}::${String(discussionId || '')}`;
}

function toast(m) {
  const text = String(m ?? '');
  const shouldDecorate = /失败|错误|异常|不可用|未找到|无法|无效|请求失败/.test(text);
  const finalText = shouldDecorate && window.api?.decorateErrorMessage ? window.api.decorateErrorMessage(text) : text;
  const t = document.createElement('div'); t.className = 'toast'; t.textContent = finalText;
  $('toasts').appendChild(t); setTimeout(() => t.remove(), 3500);
}
const MODAL_TEXT_INPUT_EVENTS = [
  'keydown', 'keyup', 'keypress',
  'copy', 'cut', 'paste',
  'beforeinput', 'input',
  'compositionstart', 'compositionupdate', 'compositionend'
];

function isModalTextInput(target) {
  return !!target?.closest?.('input, textarea, select, [contenteditable="true"]');
}

function installModalInputGuards(modal) {
  if (!modal || modal._plazaInputGuardsInstalled) return;
  const guard = event => {
    if (isModalTextInput(event.target)) event.stopPropagation();
  };
  MODAL_TEXT_INPUT_EVENTS.forEach(type => modal.addEventListener(type, guard));
  modal._plazaInputGuardsInstalled = true;
}

function openM(id) {
  const modal = $(id);
  if (!modal) return;
  installModalInputGuards(modal);
  modal.classList.add('open');
}
function closeM(id) { $(id)?.classList.remove('open') }
window.openM = openM; window.closeM = closeM;

// P0: 防止文本选择/复制时误关闭模态框 — 全局检测选择状态
;(function() {
  var _closeSelGuard = function(e) {
    if (window.getSelection && !window.getSelection().isCollapsed) return;
    var overlay = e.target.closest ? e.target.closest('.modal-overlay') : null;
    if (!overlay || e.target !== overlay) return;
    // 检查事件源是否来自 input/textarea 内部(拖选后鼠标落在遮罩上)
    var active = document.activeElement;
    if (active && (active.tagName === 'INPUT' || active.tagName === 'TEXTAREA' || active.isContentEditable)) {
      // 输入框内操作不关弹窗
      e.preventDefault(); e.stopPropagation(); return;
    }
    if (overlay.id) { closeM(overlay.id); return; }
    var modal = overlay.closest('.modal') || overlay.parentElement;
    if (modal && modal.id) { closeM(modal.id); }
  };
  document.addEventListener('click', _closeSelGuard, true);
})();

// E-1: 通用确认弹层 — 替代 confirm() 阻塞调用
function showConfirm(msg, onOk) {
  var m = $('m-confirm');
  if (!m) {
    m = document.createElement('div');
    m.id = 'm-confirm';
    m.className = 'modal-overlay';
    m.setAttribute('role', 'dialog');
    m.setAttribute('aria-modal', 'true');
    m.onclick = function(e) { if (e.target === m) closeM('m-confirm'); };
    m.innerHTML = '<div class="modal" style="max-width:360px">' +
      '<h3 style="margin-bottom:10px">确认操作</h3>' +
      '<div id="confirm-msg" style="font-size:12px;padding:12px 0;color:var(--text);line-height:1.6"></div>' +
      '<div class="modal-actions">' +
      '<button class="btn-cancel" onclick="closeM(\'m-confirm\')">取消</button>' +
      '<button id="confirm-ok-btn" class="btn-primary">确认</button></div></div>';
    document.body.appendChild(m);
    // E-4.2: Esc 关闭 + 焦点归还
    m.addEventListener('keydown', function(e) { if (e.key === 'Escape') { closeM('m-confirm'); } });
  }
  $('confirm-msg').textContent = msg;
  var okBtn = $('confirm-ok-btn');
  var handler = function() { closeM('m-confirm'); onOk(); };
  okBtn.onclick = handler;
  openM('m-confirm');
  setTimeout(function() { okBtn.focus(); }, 100);
}
window.showConfirm = showConfirm;
async function api(url, opts) { return window.api.request ? window.api.request(url, opts) : null; }
async function listApi(path, limit = 200, offset = 0) {
  if (window.api?.list) return asItems(await window.api.list(path, limit, offset));
  return asItems(await api(path));
}

/* ── Team colors: muted tones on concrete ── */
const teamColors = {
  build_system: 0x6A8E6A,
  ai_coding: 0x6A7A9E,
  energy_first_principle: 0xB08840
};
const teamCSS = {
  build_system: '#6A8E6A',
  ai_coding: '#6A7A9E',
  energy_first_principle: '#B08840'
};
const teamNames = {
  build_system: 'BUILD',
  ai_coding: '编程',
  energy_first_principle: '能源'
};
function tColor(tid) { return teamColors[tid] || 0x7A7470; }

// 鲜艳调色板（与数字孪生 3D 一致）：让每个 agent 有独立亮色，避免未知团队全灰
const VIVID_AGENT_COLORS = [0x22d3ee, 0x34d399, 0xa78bfa, 0xfbbf24, 0xf472b6, 0x60a5fa, 0xfb923c, 0x4ade80];
let _plazaSeatColorIdx = 0;
function nextVividColor() { const c = VIVID_AGENT_COLORS[_plazaSeatColorIdx % VIVID_AGENT_COLORS.length]; _plazaSeatColorIdx++; return c; }

/* ═══════════ THREE.JS — 浅色清水混凝土议事厅 (Taste light) ═══════════ */
const canvas = $('three-canvas');
// E-4.1: 屏幕阅读器可访问
if (canvas) canvas.setAttribute('aria-label', '议事厅 3D 场景');
const container = $('arena-container');
const scene = new THREE.Scene();

// Light arena sky / fog (cold off-white, matches page taste-light)
const PLAZA_BG = 0xE8EDF3;
const bgColor = new THREE.Color(PLAZA_BG);
scene.background = bgColor;
scene.fog = new THREE.FogExp2(PLAZA_BG, 0.0048);

const camera = new THREE.PerspectiveCamera(45, 1, 0.1, 200);
camera.position.set(0, 14, 28);

const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
renderer.setClearColor(PLAZA_BG);
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFShadowMap;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.12;

const controls = new OrbitControls(camera, canvas);
controls.enableDamping = true;
controls.dampingFactor = 0.06;
controls.minDistance = 10;
controls.maxDistance = 55;
controls.maxPolarAngle = Math.PI / 2.1;
controls.target.set(0, 1, 0);

/* ── Lights: soft daylight over pale concrete ── */
scene.add(new THREE.AmbientLight(0xD8DEE8, 0.42));

// Main: cool skylight
const mainLight = new THREE.DirectionalLight(0xF5F7FA, 0.72);
mainLight.position.set(3, 30, 5);
mainLight.castShadow = true;
mainLight.shadow.mapSize.set(2048, 2048);
mainLight.shadow.camera.near = 1; mainLight.shadow.camera.far = 60;
mainLight.shadow.camera.left = -25; mainLight.shadow.camera.right = 25;
mainLight.shadow.camera.top = 25; mainLight.shadow.camera.bottom = -25;
mainLight.shadow.bias = -0.001;
mainLight.shadow.normalBias = 0.02;
mainLight.shadow.radius = 2.5;
scene.add(mainLight);

// Hemisphere: pale sky / soft ground bounce
scene.add(new THREE.HemisphereLight(0xF0F4F8, 0xC5CDD8, 0.38));

// Raking light — edge definition without dark vignette
const rakingLight = new THREE.SpotLight(0xFFFFFF, 0.28, 80, Math.PI / 7, 0.55, 1.1);
rakingLight.position.set(-18, 24, -6);
rakingLight.target.position.set(0, 0.8, 0);
rakingLight.castShadow = true;
scene.add(rakingLight);
scene.add(rakingLight.target);

/* ── Material factories ── */
function concreteMat(color, rough = 0.92) {
  return new THREE.MeshStandardMaterial({ color, roughness: rough, metalness: 0.0 });
}
function bronzeMat(color = 0x8A929C, rough = 0.4) {
  return new THREE.MeshStandardMaterial({
    color, roughness: rough, metalness: 0.45,
    emissive: new THREE.Color(color).multiplyScalar(0.02), emissiveIntensity: 0.15
  });
}

/* ── Ground (light stone field) ── */
const ground = new THREE.Mesh(
  new THREE.CircleGeometry(35, 64),
  concreteMat(0xDCE2EA)
);
ground.rotation.x = -Math.PI / 2;
ground.receiveShadow = true;
scene.add(ground);

/* ── Tiered Arena: stepped pale concrete ── */
const tierDefs = [
  { innerR: 14, outerR: 19, y: 2.4, stepH: 1.0, color: 0xC8D0DA },
  { innerR: 9,  outerR: 13, y: 1.5, stepH: 0.8, color: 0xD4DBE4 },
  { innerR: 5,  outerR: 8,  y: 0.7, stepH: 0.6, color: 0xE2E8F0 },
];
tierDefs.forEach(tier => {
  // Ring surface
  const top = new THREE.Mesh(
    new THREE.RingGeometry(tier.innerR, tier.outerR, 96),
    concreteMat(tier.color, 0.88)
  );
  top.rotation.x = -Math.PI / 2; top.position.y = tier.y;
  top.receiveShadow = true;
  scene.add(top);

  // Inner wall (slightly cooler / darker for form reading)
  const wall = new THREE.Mesh(
    new THREE.CylinderGeometry(tier.innerR, tier.innerR, tier.stepH, 96, 1, true),
    concreteMat(new THREE.Color(tier.color).multiplyScalar(0.88), 0.92)
  );
  wall.position.y = tier.y - tier.stepH / 2;
  wall.receiveShadow = true; wall.castShadow = true;
  scene.add(wall);

  // Outer wall
  const outer = new THREE.Mesh(
    new THREE.CylinderGeometry(tier.outerR, tier.outerR, tier.y, 96, 1, true),
    concreteMat(new THREE.Color(tier.color).multiplyScalar(0.92), 0.92)
  );
  outer.position.y = tier.y / 2;
  scene.add(outer);

  // Formwork seam — soft slate line on light stone
  const seam = new THREE.Mesh(
    new THREE.RingGeometry(tier.innerR - 0.01, tier.outerR + 0.01, 96),
    new THREE.MeshBasicMaterial({ color: 0x1A2030, transparent: true, opacity: 0.06, side: THREE.DoubleSide })
  );
  seam.rotation.x = -Math.PI / 2; seam.position.y = tier.y + 0.005;
  scene.add(seam);
});

// Center arena floor — soft polished slab (议事台面)
const centerFloor = new THREE.Mesh(
  new THREE.CircleGeometry(4.5, 64),
  concreteMat(0xF7F9FC, 0.55)
);
centerFloor.rotation.x = -Math.PI / 2; centerFloor.position.y = 0.01;
centerFloor.receiveShadow = true;
scene.add(centerFloor);

// Formwork grid on dais
for (let i = -4; i <= 4; i++) {
  const lineMat = new THREE.MeshBasicMaterial({ color: 0x1A2030, transparent: true, opacity: 0.055, side: THREE.DoubleSide });
  const hLine = new THREE.Mesh(new THREE.PlaneGeometry(9, 0.015), lineMat);
  hLine.rotation.x = -Math.PI / 2; hLine.position.set(0, 0.015, i);
  scene.add(hLine);
  const vLine = new THREE.Mesh(new THREE.PlaneGeometry(9, 0.015), lineMat.clone());
  vLine.rotation.x = -Math.PI / 2; vLine.rotation.z = Math.PI / 2;
  vLine.position.set(i, 0.015, 0);
  scene.add(vLine);
}

/* ═══ 议事长座椅 — 浅色层叠石台 ═══ */
const throneGroup = new THREE.Group();

// Layer 1: Large pale concrete base
const base1 = new THREE.Mesh(new THREE.BoxGeometry(2.4, 0.12, 2.0), concreteMat(0xD8DEE8, 0.88));
base1.position.y = 0.06; base1.rotation.y = Math.PI / 24;
base1.castShadow = true; base1.receiveShadow = true;
throneGroup.add(base1);

// Layer 2: Cool graphite plate (accent contrast)
const base2 = new THREE.Mesh(new THREE.BoxGeometry(2.0, 0.06, 1.7), bronzeMat(0x7B8798));
base2.position.set(0.08, 0.18, -0.05); base2.rotation.y = -Math.PI / 30;
base2.castShadow = true;
throneGroup.add(base2);

// Layer 3: Concrete step
const base3 = new THREE.Mesh(new THREE.BoxGeometry(1.6, 0.15, 1.3), concreteMat(0xE8EDF3, 0.84));
base3.position.set(-0.04, 0.30, -0.02); base3.rotation.y = Math.PI / 40;
base3.castShadow = true;
throneGroup.add(base3);

// Seat: soft slate slab
const seatMesh = new THREE.Mesh(new THREE.BoxGeometry(1.3, 0.07, 0.85), bronzeMat(0x6B7585, 0.35));
seatMesh.position.set(0, 0.56, 0.08);
seatMesh.castShadow = true;
throneGroup.add(seatMesh);

// Armrests: asymmetric
const armL = new THREE.Mesh(new THREE.BoxGeometry(0.10, 0.06, 0.75), concreteMat(0xD0D7E0, 0.86));
armL.position.set(-0.62, 0.82, 0.05);
throneGroup.add(armL);
const armR = new THREE.Mesh(new THREE.BoxGeometry(0.10, 0.06, 0.70), bronzeMat(0x7B8798, 0.35));
armR.position.set(0.62, 0.72, 0.05);
throneGroup.add(armR);

// Soft key light on chairman seat (not harsh white beam)
const throneLight = new THREE.SpotLight(0xFFFFFF, 0.85, 22, Math.PI / 16, 0.22, 1.6);
throneLight.position.set(0.18, 12.6, -0.42);
throneLight.target.position.set(0.04, 0.72, 0.08);
throneLight.castShadow = true;
throneLight.shadow.mapSize.set(1024, 1024);
throneLight.shadow.bias = -0.0005;
throneGroup.add(throneLight);
throneGroup.add(throneLight.target);

const crossFill = new THREE.SpotLight(0xF0F4F8, 0.22, 12, Math.PI / 22, 0.25, 1.5);
crossFill.position.set(-0.95, 10.8, -1.2);
crossFill.target.position.set(0.0, 0.58, 0.04);
throneGroup.add(crossFill);
throneGroup.add(crossFill.target);

throneGroup.position.set(0, 0, 0);
scene.add(throneGroup);

/* ═══════════ AGENT FIGURE — 发光轮廓 ═══════════ */
const agentMeshes = new Map();
const sceneAgents = [];

function makeTextCanvas(text, color) {
  const c = document.createElement('canvas');
  c.width = 384; c.height = 104;
  const ctx = c.getContext('2d');
  ctx.clearRect(0, 0, 384, 104);
  ctx.font = '800 34px "Noto Sans SC", sans-serif';
  ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
  // Light scene: dark ink labels (readable on pale concrete)
  ctx.fillStyle = color || '#1A2030';
  ctx.fillText(text, 192, 52);
  return c;
}

function createAgentFigure(name, hexColor, isChairman = false) {
  const group = new THREE.Group();
  const col = new THREE.Color(hexColor);
  const scale = isChairman ? 1.3 : 1.0;
  group.userData.labelColor = `#${col.getHexString()}`;
  group.userData.bubbleOffsetY = (isChairman ? 3.15 : 2.9) * scale;

  // Light room: slightly stronger stroke, softer glow halo
  const outlineMat = new THREE.MeshBasicMaterial({ color: col, transparent: true, opacity: 0.82, side: THREE.DoubleSide });
  const glowMat = new THREE.MeshBasicMaterial({ color: col, transparent: true, opacity: 0.18, side: THREE.DoubleSide });

  // Head ring
  const headR = 0.34 * scale, headTube = 0.035 * scale;
  const head = new THREE.Mesh(new THREE.TorusGeometry(headR, headTube, 12, 32), outlineMat);
  head.position.y = 2.0 * scale;
  group.add(head);

  // Head glow
  const headGlow = new THREE.Mesh(new THREE.TorusGeometry(headR, headTube * 4, 12, 32), glowMat);
  headGlow.position.copy(head.position);
  group.add(headGlow);

  // Body U-arc
  const pts = [];
  for (let i = 0; i <= 32; i++) {
    const t = i / 32, a = Math.PI * t;
    pts.push(new THREE.Vector3(-Math.cos(a) * 0.48 * scale, (1.25 - Math.sin(a) * 0.65) * scale, 0));
  }
  const curve = new THREE.CatmullRomCurve3(pts);
  group.add(new THREE.Mesh(new THREE.TubeGeometry(curve, 32, 0.035 * scale, 8, false), outlineMat));
  group.add(new THREE.Mesh(new THREE.TubeGeometry(curve, 32, 0.12 * scale, 8, false), glowMat));

  // Light
  const pLight = new THREE.PointLight(col, isChairman ? 0.45 : 0.28, isChairman ? 7 : 5);
  pLight.position.y = 1.4 * scale;
  group.add(pLight);

  // Ground ring
  const glowRing = new THREE.Mesh(
    new THREE.RingGeometry(0.35 * scale, 0.55 * scale, 32),
    new THREE.MeshBasicMaterial({ color: col, transparent: true, opacity: 0.16, side: THREE.DoubleSide })
  );
  glowRing.rotation.x = -Math.PI / 2; glowRing.position.y = 0.01;
  group.add(glowRing);
  group.userData.glowRing = glowRing;

  // Name
  const tex = new THREE.CanvasTexture(makeTextCanvas(name, '#1A2030'));
  tex.minFilter = THREE.LinearFilter;
  const sprite = new THREE.Sprite(new THREE.SpriteMaterial({ map: tex, transparent: true, depthTest: false }));
  sprite.position.y = (isChairman ? 3.12 : 2.84) * scale;
  sprite.scale.set(2.7, 0.72, 1);
  group.add(sprite);

  return group;
}

/* ── Dispose helpers: release GPU resources to avoid leak on re-render ── */
function disposeObject3D(obj) {
  obj.traverse(node => {
    if (node.geometry) node.geometry.dispose();
    const mats = Array.isArray(node.material) ? node.material : (node.material ? [node.material] : []);
    mats.forEach(m => {
      if (m.map) m.map.dispose();        // CanvasTexture（智能体名字 / 团队标签贴图）
      m.dispose();
    });
  });
}
function disposeSceneAgents() {
  sceneAgents.forEach(g => { scene.remove(g); disposeObject3D(g); });
  sceneAgents.length = 0;
  agentMeshes.clear();
}

/* ── Place agents ── */
function renderArena3D(participants) {
  allParticipants = participants || [];
  disposeSceneAgents();
  if (!allParticipants.length) return;

  const groups = {};
  allParticipants.forEach(p => {
    const t = p.team_id || '_none';
    if (!groups[t]) groups[t] = [];
    groups[t].push(p);
  });

  let chairman = null;
  if (curDiscData?.moderator_agent_id) chairman = allParticipants.find(p => p.agent_id === curDiscData.moderator_agent_id);
  if (!chairman) chairman = allParticipants.find(p => p.niche_role === 'moderator');
  if (!chairman && allParticipants.length) chairman = allParticipants[0];
  const seated = allParticipants.filter(p => !chairman || p.agent_id !== chairman.agent_id);

  // 鲜艳配色：每次重建场景从头分配，议事长用亮金，其余循环亮色（像数字孪生）
  _plazaSeatColorIdx = 0;

  // Chairman on Scarpa throne
  if (chairman) {
    const fig = createAgentFigure(chairman.agent_name || '议事长', 0xfbbf24, true);
    fig.position.set(0, 0.0, 0.5);
    scene.add(fig); sceneAgents.push(fig);
    agentMeshes.set(chairman.agent_id, { group: fig });
  }

  // Agents on tiers
  if (seated.length > 0) {
    const ringRadii = [6.5, 11, 16.5];
    const ringHeights = [0.7, 1.5, 2.4];
    const ringMax = [8, 12, 20];
    const rings = [[], [], []];
    let ri = 0;
    seated.forEach(ag => {
      while (ri < 2 && rings[ri].length >= ringMax[ri]) ri++;
      rings[Math.min(ri, 2)].push(ag);
    });
    rings.forEach((ring, rIdx) => {
      if (!ring.length) return;
      ring.forEach((ag, ai) => {
        const angle = (ai / ring.length) * Math.PI * 2 - Math.PI / 2;
        const fig = createAgentFigure(ag.agent_name || ag.agent_id, nextVividColor());
        fig.position.set(ringRadii[rIdx] * Math.cos(angle), ringHeights[rIdx], ringRadii[rIdx] * Math.sin(angle));
        fig.lookAt(0, ringHeights[rIdx], 0);
        fig.rotation.x = 0; fig.rotation.z = 0;
        scene.add(fig); sceneAgents.push(fig);
        agentMeshes.set(ag.agent_id, { group: fig });
      });
    });
  }

  // Team labels
  Object.keys(groups).forEach(tid => {
    const agents = groups[tid].filter(p => !chairman || p.agent_id !== chairman.agent_id);
    if (!agents.length) return;
    let sumA = 0;
    agents.forEach(ag => { const e = agentMeshes.get(ag.agent_id); if (e) sumA += Math.atan2(e.group.position.z, e.group.position.x); });
    const avg = sumA / agents.length;
    const tex = new THREE.CanvasTexture(makeTextCanvas(teamNames[tid] || tid, teamCSS[tid] || '#7A7470'));
    tex.minFilter = THREE.LinearFilter;
    const label = new THREE.Sprite(new THREE.SpriteMaterial({ map: tex, transparent: true, depthTest: false }));
    label.position.set(23 * Math.cos(avg), 3.5, 23 * Math.sin(avg));
    label.scale.set(2.5, 0.6, 1);
    scene.add(label); sceneAgents.push(label);
  });
}

/* ── Speaking ── */
function highlightSpeaker(agentId, speaking) {
  const e = agentMeshes.get(agentId);
  if (!e) return;
  const ring = e.group.userData.glowRing;
  if (ring) { ring.material.opacity = speaking ? 0.35 : 0.08; const s = speaking ? 1.4 : 1; ring.scale.set(s, s, 1); }
}

let bubbles = [];
let speechQueue = [];
let speechPlaybackActive = false;
let speechPlaybackToken = 0;
const MAX_VISIBLE_BUBBLES = 3;
const MAX_BUBBLE_LINES = 5;
const MAX_WINDOW_CHARS = 100;
const SPEECH_GAP_MS = 250;
const bubbleProjectPos = new THREE.Vector3();
let bubbleContainerRect = null;
let lastBubbleCameraState = '';

// Audio autoplay unlock: create silent AudioContext on first user gesture
let _audioUnlocked = false;
function unlockAudio() {
  if (_audioUnlocked) return;
  _audioUnlocked = true;
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    const buf = ctx.createBuffer(1, 1, 22050);
    const src = ctx.createBufferSource();
    src.buffer = buf; src.connect(ctx.destination); src.start(0);
  } catch(e) {}
}
document.addEventListener('click', unlockAudio, { once: true });
document.addEventListener('touchstart', unlockAudio, { once: true });

function wait(ms) {
  return new Promise(resolve => {
    const check = () => {
      if (!speechPaused) { resolve(); return; }
      setTimeout(check, 100);
    };
    setTimeout(check, ms);
  });
}

function buildSpeechWindows(text) {
  const normalized = String(text ?? '')
    .replace(/\r/g, '')
    .replace(/[ \t]+\n/g, '\n')
    .trim();
  if (!normalized) return [];
  // Split into natural paragraphs (double newline or explicit breaks)
  const paragraphs = normalized.split(/\n{2,}/).map(p => p.trim()).filter(Boolean);
  // If only one paragraph, split by sentence boundaries to group ~6 lines
  const sentences = paragraphs.length > 1
    ? paragraphs
    : normalized.split(/(?<=[。！？!?；;…])\s*/).map(s => s.trim()).filter(Boolean);
  // Group sentences into windows of ~MAX_WINDOW_CHARS / ~MAX_BUBBLE_LINES
  const windows = [];
  let buf = [];
  let bufLen = 0;
  let bufLines = 0;
  for (const s of sentences) {
    const sLines = Math.ceil(s.length / 28); // ~28 chars per visual line at 380px
    if (buf.length && (bufLen + s.length > MAX_WINDOW_CHARS || bufLines + sLines > MAX_BUBBLE_LINES)) {
      windows.push(buf.join('\n'));
      buf = []; bufLen = 0; bufLines = 0;
    }
    buf.push(s); bufLen += s.length; bufLines += sLines;
  }
  if (buf.length) windows.push(buf.join('\n'));
  return windows.length ? windows : [normalized];
}

function getSpeechWindowDuration(text, isFinal) {
  const readableLength = text.replace(/\s/g, '').length;
  const base = 1600 + readableLength * 52;
  return Math.max(2400, Math.min(isFinal ? 5500 : 4500, base));
}

function getQueuedSpeechDuration() {
  return speechQueue.reduce((total, item) => {
    const itemDuration = (item.windows || []).reduce((sum, windowText, index) => {
      return sum + getSpeechWindowDuration(windowText, index === item.windows.length - 1) + (index < item.windows.length - 1 ? SPEECH_GAP_MS : 0);
    }, 0);
    return total + itemDuration;
  }, 0);
}

function trimBubbleHistory() {
  while (bubbles.length > MAX_VISIBLE_BUBBLES) {
    const oldest = bubbles.shift();
    if (!oldest) break;
    oldest.bubble.classList.remove('show');
    setTimeout(() => oldest.bubble.remove(), 400);
    highlightSpeaker(oldest.agentId, false);
  }
}

function getBubbleContainerRect() {
  if (!bubbleContainerRect) bubbleContainerRect = container.getBoundingClientRect();
  return bubbleContainerRect;
}

function invalidateBubbleLayout() {
  bubbleContainerRect = null;
  bubbles.forEach(b => { b._measureDirty = true; });
}

function getBubbleCameraState() {
  return [
    camera.position.x.toFixed(3),
    camera.position.y.toFixed(3),
    camera.position.z.toFixed(3),
    camera.quaternion.x.toFixed(4),
    camera.quaternion.y.toFixed(4),
    camera.quaternion.z.toFixed(4),
    camera.quaternion.w.toFixed(4),
    controls.target.x.toFixed(3),
    controls.target.y.toFixed(3),
    controls.target.z.toFixed(3),
  ].join('|');
}

function positionVisibleBubbles() {
  bubbles.forEach(positionSpeechBubble);
}

function positionSpeechBubble(entry) {
  const bubbleEntry = agentMeshes.get(entry.agentId);
  if (!bubbleEntry?.group?.parent || !entry.bubble?.isConnected) return;
  bubbleEntry.group.getWorldPosition(bubbleProjectPos);
  bubbleProjectPos.y += bubbleEntry.group.userData.bubbleOffsetY || 4.2;
  const projected = bubbleProjectPos.clone().project(camera);
  if (entry._measureDirty || !entry._bubbleW || !entry._bubbleH) {
    const bubbleRect = entry.bubble.getBoundingClientRect();
    entry._bubbleW = bubbleRect.width || entry._bubbleW || 120;
    entry._bubbleH = bubbleRect.height || entry._bubbleH || 60;
    entry._measureDirty = false;
  }
  const rect = getBubbleContainerRect();
  const bw = entry._bubbleW || 120;
  const bh = entry._bubbleH || 60;
  const sx = (projected.x * 0.5 + 0.5) * rect.width;
  const sy = (-projected.y * 0.5 + 0.5) * rect.height;
  entry.bubble.style.left = Math.max(8, Math.min(sx - bw / 2, rect.width - bw - 8)) + 'px';
  entry.bubble.style.top = Math.max(8, Math.min(sy - bh - 12, rect.height - bh - 8)) + 'px';
  const hidden = projected.z > 1 || projected.z < -1 || projected.x < -1.15 || projected.x > 1.15 || projected.y < -1.15 || projected.y > 1.15;
  entry.bubble.style.display = hidden ? 'none' : 'block';
}

function showSpeechBubble(agentId, name, text) {
  speechQueue.push({ agentId, name, windows: buildSpeechWindows(text) });
  processSpeechQueue();
}

async function processSpeechQueue() {
  if (speechPlaybackActive) return;
  speechPlaybackActive = true;
  const token = speechPlaybackToken;
  while (speechQueue.length && token === speechPlaybackToken) {
    const item = speechQueue.shift();
    if (!item?.windows?.length) continue;
    await playSpeechItem(item, token);
  }
  if (token === speechPlaybackToken) speechPlaybackActive = false;
}

async function playSpeechItem(item, token) {
  const entry = agentMeshes.get(item.agentId);
  if (!entry) return;
  panCameraToAgent(item.agentId);
  bubbles.forEach(b => b.bubble.classList.add('history'));
  removeBubble(item.agentId);
  highlightSpeaker(item.agentId, true);
  const b = document.createElement('div');
  b.className = 'speech-bubble speaking'; b.dataset.agent = item.agentId;
  b.setAttribute('aria-hidden', 'true');  // E-4.3: 装饰性气泡，避免重复朗读
  b.style.setProperty('--bubble-color', entry.group.userData.labelColor || '#D7DEE4');
  b.innerHTML = `<div class="sb-name">${esc(item.name)}</div><div class="sb-text"></div>`;
  const bubbleState = { agentId: item.agentId, bubble: b, textNode: b.querySelector('.sb-text'), _measureDirty: true };
  container.appendChild(b);
  requestAnimationFrame(() => {
    b.classList.add('show');
    bubbleState._measureDirty = true;
    positionSpeechBubble(bubbleState);
  });
  bubbles.push(bubbleState);
  trimBubbleHistory();
  positionSpeechBubble(bubbleState);
  for (let index = 0; index < item.windows.length; index += 1) {
    if (token !== speechPlaybackToken || !bubbleState.bubble.isConnected) return;
    if (index === 0) {
      bubbleState.textNode.textContent = item.windows[index];
    } else {
      bubbleState.textNode.textContent += '\n' + item.windows[index];
    }
    bubbleState.textNode.scrollTop = bubbleState.textNode.scrollHeight;
    bubbleState._measureDirty = true;
    positionSpeechBubble(bubbleState);
    await ttsSpeak(item.windows[index], token, item.name);
    if (index < item.windows.length - 1) await wait(SPEECH_GAP_MS);
  }
  if (token !== speechPlaybackToken || !bubbleState.bubble.isConnected) return;
  bubbleState.bubble.classList.remove('speaking');
  bubbleState.bubble.classList.add('history');
  highlightSpeaker(item.agentId, false);
}

function removeBubble(aid) {
  bubbles = bubbles.filter(b => { if (b.agentId === aid) { b.bubble.classList.remove('show'); setTimeout(() => b.bubble.remove(), 400); return false; } return true; });
}

function clearSpeechPlayback() {
  speechQueue = [];
  speechPlaybackToken += 1;
  speechPlaybackActive = false;
  speechPaused = false;
  _ttsErrorShown = false; // 重置 TTS 错误提示标记
  window._ttsWarned = false; // 重置全站 TTS 警告标记
  updatePauseUI();
  if (ttsAudio) { ttsAudio.pause(); ttsAudio = null; }
  if (window.speechSynthesis) speechSynthesis.cancel();
  bubbles.forEach(b => {
    b.bubble.classList.remove('show');
    setTimeout(() => b.bubble.remove(), 400);
    highlightSpeaker(b.agentId, false);
  });
  bubbles = [];
}

/* ═══════════ TTS ENGINE (GPT-SoVITS + Web Speech fallback) ═══════════ */
let ttsMuted = localStorage.getItem('plaza_ttsMuted') === 'true'; // default to unmuted
let speechPaused = false;
let ttsAudio = null; // current playing Audio element
let ttsPlaybackSerial = 0;
let _ttsErrorShown = false; // 本轮讨论只展示一次 TTS 错误提示
const ttsBtn = document.getElementById('tts-toggle');
const ttsIconOn = document.getElementById('tts-icon-on');
const ttsIconOff = document.getElementById('tts-icon-off');
const pauseBtn = document.getElementById('pause-toggle');
const pauseIcon = document.getElementById('pause-icon');
const playIcon = document.getElementById('play-icon');

function updateTtsUI() {
  ttsBtn.classList.toggle('muted', ttsMuted);
  ttsIconOn.style.display = ttsMuted ? 'none' : 'block';
  ttsIconOff.style.display = ttsMuted ? 'block' : 'none';
}
function updatePauseUI() {
  pauseBtn.classList.toggle('paused', speechPaused);
  pauseIcon.style.display = speechPaused ? 'none' : 'block';
  playIcon.style.display = speechPaused ? 'block' : 'none';
}
ttsBtn.addEventListener('click', () => {
  ttsMuted = !ttsMuted;
  localStorage.setItem('plaza_ttsMuted', String(ttsMuted));
  updateTtsUI();
  if (ttsMuted && ttsAudio) { ttsAudio.pause(); ttsAudio = null; }
  if (ttsMuted && window.speechSynthesis) speechSynthesis.cancel();
});
pauseBtn.addEventListener('click', () => {
  speechPaused = !speechPaused;
  updatePauseUI();
  if (speechPaused) {
    if (ttsAudio) ttsAudio.pause();
    if (window.speechSynthesis) speechSynthesis.pause();
  } else {
    if (ttsAudio) ttsAudio.play().catch(err => console.warn('Audio resume failed:', err?.message || err));
    if (window.speechSynthesis) speechSynthesis.resume();
  }
});
updateTtsUI();
updatePauseUI();

function stopCurrentTtsAudio() {
  if (!ttsAudio) return;
  ttsAudio.pause();
  ttsAudio.src = '';
  ttsAudio = null;
}

// Web Speech voice cache — loaded lazily with async fallback
let _ttsCachedZhVoices = null;
let _ttsVoicesLoaded = false;
function _ttsEnsureVoices() {
  if (!window.speechSynthesis) return [];
  const voices = speechSynthesis.getVoices();
  if (voices.length > 0) {
    _ttsVoicesLoaded = true;
    _ttsCachedZhVoices = voices.filter(v => v.lang && v.lang.startsWith('zh'));
    return _ttsCachedZhVoices;
  }
  // voices not loaded yet — try to trigger loading
  if (!_ttsVoicesLoaded) {
    speechSynthesis.getVoices(); // trigger side-effect in some browsers
  }
  return _ttsCachedZhVoices || [];
}

// Eager-load voices on first user gesture + voiceschanged event
function _ttsInitVoices() {
  if (!window.speechSynthesis) return;
  const load = () => {
    const voices = speechSynthesis.getVoices();
    if (voices.length > 0) {
      _ttsCachedZhVoices = voices.filter(v => v.lang && v.lang.startsWith('zh'));
      _ttsVoicesLoaded = true;
    }
  };
  speechSynthesis.addEventListener('voiceschanged', load, { once: true });
  load(); // may succeed synchronously
}
document.addEventListener('click', _ttsInitVoices, { once: true });
document.addEventListener('touchstart', _ttsInitVoices, { once: true });

function ttsFallbackSpeak(text, speed, serial) {
  if (ttsMuted || !window.speechSynthesis || serial !== ttsPlaybackSerial) return Promise.resolve(false);
  const zhVoices = _ttsEnsureVoices();
  return new Promise(resolve => {
    const utt = new SpeechSynthesisUtterance(text);
    utt.lang = 'zh-CN';
    utt.rate = speed;
    utt.pitch = 0.82;
    utt.volume = 0.85;
    const finish = played => resolve(serial === ttsPlaybackSerial ? played : false);
    if (!zhVoices.length) {
      // Last resort: try default voice with zh-CN lang (may sound wrong but better than nothing)
      utt.onend = () => finish(true);
      utt.onerror = () => finish(false);
      speechSynthesis.speak(utt);
      if (speechPaused) speechSynthesis.pause();
      return;
    }
    // Prefer male voice, but fallback to any Chinese voice
    const maleKeywords = ['reed', 'rocko', 'grandpa', 'eddy', 'yu-shu', 'wan-lung', 'kangkang', 'yunxi', 'yunjian', 'yunyang', 'male', 'xiaochen', 'sin-ji'];
    const maleVoice = zhVoices.find(v => maleKeywords.some(k => v.name.toLowerCase().includes(k)));
    const voice = maleVoice || zhVoices[0];
    utt.voice = voice;
    utt.onend = () => finish(true);
    utt.onerror = () => finish(false);
    speechSynthesis.speak(utt);
    if (speechPaused) speechSynthesis.pause();
  });
}

async function ttsSpeak(text, playbackToken, agentName) {
  if (ttsMuted || playbackToken !== speechPlaybackToken) {
    twarn('[TTS] Skipped: muted=', ttsMuted, 'tokenMatch=', playbackToken === speechPlaybackToken);
    return false;
  }
  const serial = ++ttsPlaybackSerial;
  stopCurrentTtsAudio();
  if (window.speechSynthesis) speechSynthesis.cancel();
  tlog('[TTS] Fetching audio for:', agentName, text.slice(0, 30));

  try {
    const resp = await (window._agFetch || fetch)('/api/v1/tts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, text_lang: 'zh', speed_factor: 1.0, agent_name: agentName || '' })
    });
    if (!resp.ok) {
      const errText = await resp.text().catch(() => '');
      throw new Error(`TTS ${resp.status}${errText ? ': ' + errText.slice(0, 80) : ''}`);
    }
    const blob = await resp.blob();
    tlog('[TTS] Got blob:', blob.size, 'bytes');
    if (ttsMuted || playbackToken !== speechPlaybackToken || serial !== ttsPlaybackSerial) {
      twarn('[TTS] Cancelled after fetch: muted=', ttsMuted, 'tokenMatch=', playbackToken === speechPlaybackToken, 'serialMatch=', serial === ttsPlaybackSerial);
      return false;
    }

    await new Promise((resolve, reject) => {
      let settled = false;
      const finish = callback => {
        if (settled) return;
        settled = true;
        clearTimeout(safetyTimer);
        callback();
      };
      const url = URL.createObjectURL(blob);
      const audio = new Audio(url);
      ttsAudio = audio;
      audio.volume = 0.85;

      // Safety timeout: if onended never fires, resolve after estimated duration + buffer
      const safetyTimer = setTimeout(() => {
        twarn('[TTS] Safety timeout - forcing resolve');
        audio.pause(); audio.src = '';
        URL.revokeObjectURL(url);
        if (ttsAudio === audio) ttsAudio = null;
        finish(resolve);
      }, 30000); // 30s max per segment

      audio.onended = () => {
        URL.revokeObjectURL(url);
        if (ttsAudio === audio) ttsAudio = null;
        finish(resolve);
      };
      audio.onerror = () => {
        URL.revokeObjectURL(url);
        if (ttsAudio === audio) ttsAudio = null;
        finish(() => reject(new Error('audio-error')));
      };

      // Once we know the duration, set a tighter timeout
      audio.onloadedmetadata = () => {
        if (!settled && audio.duration && isFinite(audio.duration)) {
          clearTimeout(safetyTimer);
          const tightTimer = setTimeout(() => {
            if (!settled) {
              twarn('[TTS] Duration timeout - forcing resolve after', audio.duration, 's');
              audio.pause(); audio.src = '';
              URL.revokeObjectURL(url);
              if (ttsAudio === audio) ttsAudio = null;
              finish(resolve);
            }
          }, (audio.duration + 2) * 1000);
        }
      };

      const abortPlayback = () => {
        audio.pause();
        audio.src = '';
        URL.revokeObjectURL(url);
        if (ttsAudio === audio) ttsAudio = null;
        finish(resolve);
      };

      const startPlayback = async () => {
        if (ttsMuted || playbackToken !== speechPlaybackToken || serial !== ttsPlaybackSerial) {
          abortPlayback();
          return;
        }
        try {
          await audio.play();
          tlog('[TTS] Playing audio successfully');
        } catch (err) {
          // Retry once after short delay (autoplay policy may clear after gesture)
          if (err?.name === 'NotAllowedError') {
            twarn('[TTS] Autoplay blocked, retrying in 200ms...');
            await new Promise(r => setTimeout(r, 200));
            if (ttsMuted || playbackToken !== speechPlaybackToken || serial !== ttsPlaybackSerial) {
              abortPlayback(); return;
            }
            try { await audio.play(); tlog('[TTS] Retry play succeeded'); return; } catch(e2) {}
          }
          console.error('[TTS] audio.play() failed:', err?.message || err);
          URL.revokeObjectURL(url);
          if (ttsAudio === audio) ttsAudio = null;
          finish(resolve); // resolve instead of reject to continue queue
        }
      };

      if (speechPaused) {
        const waitUntilResumed = () => {
          if (ttsMuted || playbackToken !== speechPlaybackToken || serial !== ttsPlaybackSerial) {
            abortPlayback();
            return;
          }
          if (!speechPaused) {
            startPlayback();
            return;
          }
          setTimeout(waitUntilResumed, 100);
        };
        waitUntilResumed();
      } else {
        startPlayback();
      }
    });
    return true;
  } catch (err) {
    console.warn('Edge-TTS playback failed, using Web Speech:', err?.message || err);
    const fallbackOk = await ttsFallbackSpeak(text, 1.0, serial);
    if (!fallbackOk && !ttsMuted) {
      // Both Edge-TTS and Web Speech failed — show user-facing warning (once per session)
      if (!window._ttsWarned) {
        window._ttsWarned = true;
        toast('语音播报不可用：请检查网络或浏览器语音设置');
      }
    }
    return fallbackOk;
  }
}

/* ═══════════ CAMERA LOOK-AT (smooth pan to speaker from fixed seat) ═══════════ */
const CAM_LOOK_SPEED = 0.04; // lerp factor per frame
const camDefaultTarget = new THREE.Vector3(0, 1, 0); // center (PM throne)
let camTargetLookAt = camDefaultTarget.clone();
let camCurrentLookAt = camDefaultTarget.clone();
let camPanning = false;

function panCameraToAgent(agentId) {
  // If moderator (PM) speaks, keep looking at center — no movement
  if (curDiscData?.moderator_agent_id === agentId) return;
  const entry = agentMeshes.get(agentId);
  if (!entry) return;
  const pos = entry.group.position;
  // Look at a point slightly above the agent (where the bubble appears)
  camTargetLookAt.set(pos.x, pos.y + 2, pos.z);
  camPanning = true;
}

function updateCameraLookAt() {
  if (!camPanning) return;
  const dx = camTargetLookAt.x - camCurrentLookAt.x;
  const dy = camTargetLookAt.y - camCurrentLookAt.y;
  const dz = camTargetLookAt.z - camCurrentLookAt.z;
  if (Math.abs(dx) < 0.01 && Math.abs(dy) < 0.01 && Math.abs(dz) < 0.01) {
    camCurrentLookAt.copy(camTargetLookAt);
    camPanning = false;
  } else {
    camCurrentLookAt.x += dx * CAM_LOOK_SPEED;
    camCurrentLookAt.y += dy * CAM_LOOK_SPEED;
    camCurrentLookAt.z += dz * CAM_LOOK_SPEED;
  }
  controls.target.copy(camCurrentLookAt);
}

/* ═══════════ ANIMATION ═══════════ */
const animStartMs = performance.now();
// D-1: 隐藏标签页暂停渲染
let _renderPaused = false;
document.addEventListener('visibilitychange', () => { _renderPaused = document.hidden; });
let _emptyFrameSkip = 0;
function animate() {
  requestAnimationFrame(animate);
  // D-1: 后台不渲染
  if (_renderPaused) return;
  // D-2: 空场景降帧（每4帧渲染一次）
  if (!allParticipants.length && !bubbles.length) {
    _emptyFrameSkip = (_emptyFrameSkip + 1) % 4;
    if (_emptyFrameSkip !== 0) return;
  }
  const t = (performance.now() - animStartMs) / 1000;
  updateCameraLookAt();
  controls.update();

  // Only update bubble positions when the camera transform or target actually changes
  const cameraState = getBubbleCameraState();
  if (cameraState !== lastBubbleCameraState) {
    positionVisibleBubbles();
    lastBubbleCameraState = cameraState;
  }

  // Chairman breathing
  if (allParticipants.length && curDiscData?.moderator_agent_id) {
    const ch = agentMeshes.get(curDiscData.moderator_agent_id);
    if (ch) ch.group.position.y = Math.sin(t * 0.6) * 0.02;
  }

  // Water shimmer
  throneGroup.children.forEach(c => {
    if (c.material?.metalness > 0.5 && c.material?.transparent) {
      c.material.opacity = 0.45 + Math.sin(t * 1.5) * 0.08;
    }
  });

  renderer.render(scene, camera);
}

function onResize() {
  const w = container.clientWidth, h = container.clientHeight;
  if (!w || !h) return;
  camera.aspect = w / h; camera.updateProjectionMatrix(); renderer.setSize(w, h);
  invalidateBubbleLayout();
  positionVisibleBubbles();
}
window.addEventListener('resize', onResize);
new ResizeObserver(onResize).observe(container);
onResize(); animate();

/* ═══════════ PLAZA CRUD ═══════════ */
async function loadPlazas() {
  const ps = await listApi(`${API}/plaza`, 200, 0);
  knownPlazas = Array.isArray(ps) ? ps : [];
  const list = $('plaza-list');
  if (!ps || !ps.length) {
    list.innerHTML = '<div style="padding:20px;color:var(--dim);text-align:center;font-size:10px">无广场</div>';
    return [];
  }
  list.innerHTML = ps.map(p =>
    `<div class="plaza-card ${p.id === curPlaza ? 'active' : ''}" data-plaza-id="${esc(p.id)}" onclick="selectPlaza('${esc(p.id)}')">
      <div class="nm">${esc(p.name)}</div>
      <div class="mt"><span>${p.participant_count} 人</span><span>${p.discussion_count} 题</span></div>
      <button class="btn-edit" title="编辑广场" onclick="event.stopPropagation();openEditPlaza('${esc(p.id)}')">✎</button>
      <button class="btn-del" title="删除广场" onclick="event.stopPropagation();deletePlaza('${esc(p.id)}','${esc(p.name)}')">×</button>
    </div>`
  ).join('');
  return ps;
}

window.selectPlaza = async function(id) {
  if (!id) return false;
  // Close any existing SSE connection
  teardownSSE();
  clearSpeechPlayback();
  // 先拉取广场详情，仅在没有参与者时才自动入座（兼容旧广场）
  let plaza = await api(`${API}/plaza/${id}`);
  if (!plaza) {
    if (window.api?._lastError?.status === 404) {
      if (deepLinkPlazaId === id) stripQueryParams(['plaza_id', 'discussion_id']);
      if (localStorage.getItem('plaza_curPlaza') === id) localStorage.removeItem('plaza_curPlaza');
      if (localStorage.getItem('plaza_curDisc')) localStorage.removeItem('plaza_curDisc');
      const fallback = knownPlazas.find(p => p.id !== id);
      if (fallback?.id) {
        toast('目标广场不存在，已切换到可用广场');
        return window.selectPlaza(fallback.id);
      }
      normalizePlazaSelectionOnError();
      toast('目标广场不存在，请重新创建或选择其他广场');
    }
    return false;
  }

  curPlaza = id;
  curDisc = null;
  curDiscData = null;
  curVerificationState = null;
  curConsensusState = null;
  curEscalationState = null;
  localStorage.setItem('plaza_curPlaza', id);
  localStorage.removeItem('plaza_curDisc');
  await loadPlazas();

  if (!plaza.participants || !plaza.participants.length) {
    await api(`${API}/plaza/${id}/auto-seat`, { method: 'POST' });
    plaza = await api(`${API}/plaza/${id}`);
    if (!plaza) return false;
  }
  renderArena3D(plaza.participants || []);
  renderDiscList(await listApi(`${API}/plaza/${id}/discussions`, 200, 0));
  $('msg-log').innerHTML = '<div style="text-align:center;padding:40px 0;color:var(--dim);font-size:10px;font-family:var(--font-mono)">创建讨论开始议事</div>';
  $('plan-panel').style.display = 'none';
  $('btn-start').disabled = true; $('status-text').textContent = '';
  return true;
};

/* ═══════════ AGENT TREE HELPERS ═══════════ */
let _agentTreeData = []; // cached teams-tree

function renderAgentTree(teams) {
  _agentTreeData = teams;
  const el = $('agent-tree');
  if (!teams.length) { el.innerHTML = '<div style="color:var(--dim);font-size:10px;padding:8px">无团队</div>'; return; }
  el.innerHTML = teams.map((t, ti) => {
    const agents = t.agents.map((a, ai) =>
      `<div class="tree-agent">
        <input type="checkbox" id="cb-a-${ti}-${ai}" data-team="${esc(t.team_id)}" data-aid="${esc(a.agent_id)}" data-aname="${esc(a.name)}" data-arole="${esc(a.role)}" onchange="onAgentCheck()">
        <label for="cb-a-${ti}-${ai}">${esc(a.name)}</label>
        <span class="agent-role">${esc(a.role)}</span>
      </div>`
    ).join('');
    return `<div class="tree-team">
      <div class="tree-team-header" onclick="toggleTreeTeam(this)">
        <span class="tree-arrow">▶</span>
        <input type="checkbox" id="cb-t-${ti}" onclick="event.stopPropagation();toggleTeamAll(${ti},this.checked)" data-ti="${ti}">
        <label for="cb-t-${ti}" onclick="event.stopPropagation()">${esc(t.name)}</label>
        <span class="tree-count">${t.agents.length}</span>
      </div>
      <div class="tree-agents" id="tree-agents-${ti}">${agents}</div>
    </div>`;
  }).join('');
}

window.toggleTreeTeam = function(header) {
  const arrow = header.querySelector('.tree-arrow');
  const agents = header.nextElementSibling;
  const open = agents.classList.toggle('open');
  arrow.classList.toggle('open', open);
};

window.toggleTeamAll = function(ti, checked) {
  const agents = document.querySelectorAll(`#tree-agents-${ti} input[type="checkbox"]`);
  agents.forEach(cb => cb.checked = checked);
  onAgentCheck();
};

window.onAgentCheck = function() {
  const checked = getSelectedAgents();
  $('agent-sel-count').textContent = checked.length ? `(${checked.length} 已选)` : '';
  // Update chairperson dropdown
  const sel = $('inp-chair');
  const prevVal = sel.value;
  sel.innerHTML = '<option value="">— 未指定 —</option>' +
    checked.map(a => `<option value="${esc(a.agent_id)}">${esc(a.agent_name)} (${esc(a.role || a.team_id)})</option>`).join('');
  // Restore previous selection if still valid
  if (checked.some(a => a.agent_id === prevVal)) sel.value = prevVal;
  // Update team-level checkbox states
  _agentTreeData.forEach((t, ti) => {
    const teamCbs = document.querySelectorAll(`#tree-agents-${ti} input[type="checkbox"]`);
    const teamHeader = document.querySelector(`#cb-t-${ti}`);
    if (teamHeader) {
      const all = teamCbs.length;
      const chk = [...teamCbs].filter(c => c.checked).length;
      teamHeader.checked = chk === all && all > 0;
      teamHeader.indeterminate = chk > 0 && chk < all;
    }
  });
};

function getSelectedAgents() {
  const cbs = document.querySelectorAll('#agent-tree input[type="checkbox"][data-aid]:checked');
  return [...cbs].map(cb => ({
    agent_id: cb.dataset.aid,
    agent_name: cb.dataset.aname,
    role: cb.dataset.arole,
    team_id: cb.dataset.team,
  }));
}

/* ═══════════ PLAZA CRUD ═══════════ */

window.openCreatePlaza = async function() {
  openM('m-plaza');
  $('inp-pn').value = ''; $('inp-pd').value = '';
  $('agent-sel-count').textContent = '';
  $('inp-chair').innerHTML = '<option value="">— 请先勾选智能体 —</option>';
  // Fetch agent tree
  renderAgentTree(await listApi(`${API}/teams-tree`, 200, 0));
  $('inp-pn').focus();
};

window.doCreatePlaza = async function() {
  const name = $('inp-pn').value.trim();
  if (!name) { toast('请输入名称'); return; }
  const selectedAgents = getSelectedAgents();
  if (!selectedAgents.length) { toast('请至少选择一个智能体'); return; }
  const chairId = $('inp-chair').value;
  const body = {
    name,
    description: $('inp-pd').value.trim(),
    selected_agents: selectedAgents,
    chairperson_agent_id: chairId,
  };
  const r = await api(`${API}/plaza`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
  if (r) { closeM('m-plaza'); toast('广场已创建'); await loadPlazas(); selectPlaza(r.id); }
};

/* ═══════════ EDIT PLAZA ═══════════ */
let _editPlazaId = null;
let _editAgentTreeData = [];
let _editOriginalAgentIds = new Set();

function renderEditAgentTree(teams, currentParticipants) {
  _editAgentTreeData = teams;
  const currentIds = new Set((currentParticipants || []).map(p => p.agent_id));
  _editOriginalAgentIds = new Set(currentIds);
  const el = $('edit-agent-tree');
  if (!teams.length) { el.innerHTML = '<div style="color:var(--dim);font-size:10px;padding:8px">无团队</div>'; return; }
  el.innerHTML = teams.map((t, ti) => {
    const agents = t.agents.map((a, ai) => {
      const checked = currentIds.has(a.agent_id) ? 'checked' : '';
      return `<div class="tree-agent">
        <input type="checkbox" id="ecb-a-${ti}-${ai}" data-team="${esc(t.team_id)}" data-aid="${esc(a.agent_id)}" data-aname="${esc(a.name)}" data-arole="${esc(a.role)}" ${checked} onchange="onEditAgentCheck()">
        <label for="ecb-a-${ti}-${ai}">${esc(a.name)}</label>
        <span class="agent-role">${esc(a.role)}</span>
      </div>`;
    }).join('');
    const allChecked = t.agents.every(a => currentIds.has(a.agent_id));
    const someChecked = t.agents.some(a => currentIds.has(a.agent_id));
    return `<div class="tree-team">
      <div class="tree-team-header" onclick="toggleEditTreeTeam(this)">
        <span class="tree-arrow">▶</span>
        <input type="checkbox" id="ecb-t-${ti}" ${allChecked ? 'checked' : ''} onclick="event.stopPropagation();toggleEditTeamAll(${ti},this.checked)" data-ti="${ti}">
        <label for="ecb-t-${ti}" onclick="event.stopPropagation()">${esc(t.name)}</label>
        <span class="tree-count">${t.agents.length}</span>
      </div>
      <div class="tree-agents ${someChecked ? 'open' : ''}" id="edit-tree-agents-${ti}">${agents}</div>
    </div>`;
  }).join('');
  onEditAgentCheck();
}

window.toggleEditTreeTeam = function(header) {
  const arrow = header.querySelector('.tree-arrow');
  const agents = header.nextElementSibling;
  const open = agents.classList.toggle('open');
  arrow.classList.toggle('open', open);
};

window.toggleEditTeamAll = function(ti, checked) {
  document.querySelectorAll(`#edit-tree-agents-${ti} input[type="checkbox"]`).forEach(cb => cb.checked = checked);
  onEditAgentCheck();
};

window.onEditAgentCheck = function() {
  const cbs = document.querySelectorAll('#edit-agent-tree input[type="checkbox"][data-aid]:checked');
  $('edit-agent-sel-count').textContent = cbs.length ? `(${cbs.length} 已选)` : '';
  _editAgentTreeData.forEach((t, ti) => {
    const teamCbs = document.querySelectorAll(`#edit-tree-agents-${ti} input[type="checkbox"]`);
    const hdr = document.querySelector(`#ecb-t-${ti}`);
    if (hdr) {
      const all = teamCbs.length;
      const chk = [...teamCbs].filter(c => c.checked).length;
      hdr.checked = chk === all && all > 0;
      hdr.indeterminate = chk > 0 && chk < all;
    }
  });
};

function getEditSelectedAgents() {
  const cbs = document.querySelectorAll('#edit-agent-tree input[type="checkbox"][data-aid]:checked');
  return [...cbs].map(cb => ({
    agent_id: cb.dataset.aid,
    agent_name: cb.dataset.aname,
    role: cb.dataset.arole,
    team_id: cb.dataset.team,
  }));
}

window.openEditPlaza = async function(plazaId) {
  _editPlazaId = plazaId;
  openM('m-edit-plaza');
  $('edit-agent-sel-count').textContent = '';
  $('edit-agent-tree').innerHTML = '<div style="color:var(--dim);font-size:10px;padding:8px">加载中...</div>';
  const [tree, plaza] = await Promise.all([
    listApi(`${API}/teams-tree`, 200, 0),
    api(`${API}/plaza/${plazaId}`)
  ]);
  $('edit-plaza-title').textContent = `编辑广场 — ${plaza?.name || ''}`;
  renderEditAgentTree(tree, plaza?.participants || []);
};

window.doSaveEditPlaza = async function() {
  if (!_editPlazaId) return;
  const selected = getEditSelectedAgents();
  if (!selected.length) { toast('请至少保留一个智能体'); return; }
  const newIds = new Set(selected.map(a => a.agent_id));
  // Remove agents no longer selected
  const toRemove = [..._editOriginalAgentIds].filter(id => !newIds.has(id));
  // Add newly selected agents
  const toAdd = selected.filter(a => !_editOriginalAgentIds.has(a.agent_id));
  let ok = true;
  for (const aid of toRemove) {
    const r = await api(`${API}/plaza/${_editPlazaId}/participants/${aid}`, { method: 'DELETE' });
    if (!r) ok = false;
  }
  if (toAdd.length) {
    const batch = toAdd.map(a => ({ agent_id: a.agent_id, agent_name: a.agent_name, role: a.role, team_id: a.team_id, seat_tier: 'middle', niche_role: 'panelist' }));
    const r = await api(`${API}/plaza/${_editPlazaId}/participants/batch`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(batch) });
    if (!r) ok = false;
  }
  closeM('m-edit-plaza');
  toast(ok ? '广场参与者已更新' : '部分操作失败');
  await loadPlazas();
  if (curPlaza === _editPlazaId) selectPlaza(_editPlazaId);
};

window.deletePlaza = async function(id, name) {
  showConfirm(`确定删除广场「${name}」？所有讨论数据将一并删除。`, async () => {
    const r = await api(`${API}/plaza/${id}`, { method: 'DELETE' });
    if (r) {
      toast('广场已删除');
      if (curPlaza === id) { curPlaza = null; curDisc = null; curDiscData = null; localStorage.removeItem('plaza_curPlaza'); localStorage.removeItem('plaza_curDisc'); renderArena3D([]); $('msg-log').innerHTML = ''; $('disc-list').innerHTML = '<div style="color:var(--dim);font-size:10px">先选择广场</div>'; }
      await loadPlazas();
    }
  });
};

/* ═══════════ DISCUSSIONS ═══════════ */
function renderDiscList(ds) {
  $('disc-list').innerHTML = ds.map(d => {
    const closedActions = d.status === 'closed'
      ? `<div class="disc-actions"><button class="disc-act" onclick="reopenDisc(event, '${esc(d.id)}')">重新讨论</button><button class="disc-act" onclick="extractFromDisc(event, '${esc(d.id)}')">萃取</button><button class="disc-act" onclick="exportDiscPDF(event, '${esc(d.id)}')">网页</button></div>`
      : '';
    return `<div class="disc-item ${d.id === curDisc ? 'active' : ''}" data-discussion-id="${esc(d.id)}" onclick="selectDisc('${esc(d.id)}')">
      <div class="dh"><div class="tp">${esc(d.topic)}</div><button class="disc-del" onclick="deleteDisc(event, '${esc(d.id)}')">删除</button></div>
      <div class="dm"><span class="pill pill-${d.status}">${statusTxt(d.status)}</span><span>${d.message_count} 消息</span></div>
      ${closedActions}
    </div>`;
  }).join('') || '<div style="color:var(--dim);font-size:10px">无讨论</div>';
}
function statusTxt(s) { return { open: '待启动', in_progress: '进行中', summarizing: '总结中', closed: '已结束' }[s] || s; }

window.deleteDisc = async function(event, discId) {
  event?.stopPropagation();
  if (!curPlaza) return;
  showConfirm('删除这个讨论？', async () => {
    const deletingCurrent = curDisc === discId;
    if (deletingCurrent) teardownSSE();
    const result = await api(`${API}/plaza/${curPlaza}/discussions/${discId}`, { method: 'DELETE' });
    if (!result) { toast('删除失败'); return; }
    if (deletingCurrent) {
      curDisc = null; curDiscData = null; curVerificationState = null;
      clearSpeechPlayback();
      $('msg-log').innerHTML = '<div style="text-align:center;padding:40px 0;color:var(--dim);font-size:10px;font-family:var(--font-mono)">创建讨论开始议事</div>';
      $('plan-panel').style.display = 'none'; $('btn-start').disabled = true; $('btn-start').textContent = '开始'; $('status-text').textContent = '';
    }
    const plaza = await api(`${API}/plaza/${curPlaza}`);
    if (plaza) {
      renderDiscList(await listApi(`${API}/plaza/${curPlaza}/discussions`, 200, 0));
      renderArena3D(plaza.participants || []);
    }
    toast('讨论已删除');
  });
};

window.selectDisc = async function(discId, opts) {
  if (!curPlaza || !discId) return false;
  const disc = await api(`${API}/plaza/${curPlaza}/discussions/${discId}`);
  if (!disc) {
    if (window.api?._lastError?.status === 404) {
      if (deepLinkDiscussionId === discId) stripQueryParams(['discussion_id']);
      if (localStorage.getItem('plaza_curDisc') === discId) localStorage.removeItem('plaza_curDisc');
      if (curDisc === discId) curDisc = null;
      curDiscData = null;
      curVerificationState = null;
      curConsensusState = null;
      curEscalationState = null;
      $('btn-start').disabled = true;
      $('btn-start').textContent = '开始';
      $('status-text').textContent = '';
      $('plan-panel').style.display = 'none';
      toast('目标讨论不存在，请重新选择讨论');
    }
    return false;
  }

  curDisc = discId;
  escalationFetchBlocked.delete(escalationCtxKey(curPlaza, discId));
  _msgRenderLimit = 50;  // E-6.1: 切讨论时重置分页
  localStorage.setItem('plaza_curDisc', discId);
  if (!opts?.keepSpeech) clearSpeechPlayback();
  curDiscData = disc;
  const plaza = await api(`${API}/plaza/${curPlaza}`);
  if (plaza) { renderDiscList(await listApi(`${API}/plaza/${curPlaza}/discussions`, 200, 0)); renderArena3D(plaza.participants || []); }
  renderMessages(disc.messages || []);
  $('btn-start').disabled = !['open', 'closed'].includes(disc.status);
  $('btn-start').textContent = disc.status === 'open' ? '开始' : disc.status === 'closed' ? '重新讨论' : disc.status === 'in_progress' ? '进行中' : '总结中';
  $('status-text').textContent = disc.goal ? `目标: ${disc.goal}` : '';
  curVerificationState = null;
  clearDiscussionSignals();
  if (disc.status === 'closed' && disc.summary) {
    renderPlan(disc);
    refreshVerificationState(true);
    refreshConsensusState(true);
    refreshEscalationState(true);
  } else if (disc.plan && disc.plan.content) {
    renderLivePlan(disc.plan);
    refreshVerificationState(true);
    refreshConsensusState(true);
    refreshEscalationState(true);
  } else {
    $('plan-panel').style.display = 'none';
  }
  if (disc.status === 'in_progress' || disc.plan?.content || disc.summary) connectSSE(discId);
  return true;
};

// E-6.1: 消息分页 — 超长讨论只渲染近 N 条
var _msgRenderLimit = 50;
function renderMessages(msgs) {
  const log = $('msg-log');
  _seenMsgKeys.clear();
  if (!msgs.length) { log.innerHTML = '<div style="text-align:center;padding:40px 0;color:var(--dim);font-size:10px">点击「开始」启动讨论</div>'; _msgRenderLimit = 50; return; }
  var h = '', lr = -1;
  // 只渲染最近 _msgRenderLimit 条
  var start = Math.max(0, msgs.length - _msgRenderLimit);
  if (start > 0) {
    h += '<div id="load-earlier-bar" style="text-align:center;padding:6px;margin-bottom:8px">' +
      '<button class="btn btn-sm" onclick="expandMessages()" style="font-size:10px">📜 加载更早 (' + start + ' 条隐藏)</button></div>';
  }
  for (var i = start; i < msgs.length; i++) {
    var m = msgs[i];
    markMsgSeen(m);
    if (m.round_number !== lr && m.round_number > 0) { h += '<div class="round-sep">ROUND ' + m.round_number + '</div>'; lr = m.round_number; }
    var isMod = m.niche_role === 'moderator';
    var isUser = m.niche_role === 'human';
    var cls = isMod ? 'mod' : (isUser ? 'user' : '');
    var label = isMod ? ' · 议事长' : (isUser ? ' · 你' : '');
    h += '<div class="msg-entry ' + cls + '"><div class="me-name">' + esc(m.agent_name) + label + '</div><div class="me-text">' + mdLite(m.content) + '</div></div>';
  }
  log.innerHTML = h; log.scrollTop = log.scrollHeight;
}
function expandMessages() {
  _msgRenderLimit = Math.min(_msgRenderLimit + 100, 9999);
  if (curDiscData && curDiscData.messages) renderMessages(curDiscData.messages);
}

function mdLite(s) {
  return esc(s).replace(/\n/g, '<br>').replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>').replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/^(#{1,4})\s+(.+)/gm, (m, h, t) => `<strong style="font-size:${17 - h.length * 2}px">${t}</strong>`);
}

function verificationStatusLabel(status) {
  return {
    verify_pending: '待验证',
    dispatched: '待重做',
    failed: '失败',
    closed: '已关闭',
    verified: '已验证',
    in_progress: '进行中',
  }[status] || status || '未知';
}

function verificationStatusColor(status) {
  return {
    verify_pending: '#B08840',
    dispatched: '#8A9097',
    failed: '#C05C5C',
    closed: '#6A8E6A',
    verified: '#6A8E6A',
    in_progress: '#6A7A9E',
  }[status] || '#8A9097';
}

function verificationAlertLabel(alert) {
  if (!alert) return '';
  if (alert.alert_level === 'critical') return '需要人工介入';
  if (alert.next_action?.startsWith('run_verify_test:')) return '等待验证';
  if (alert.next_action === 'redispatch_build') return '等待重做';
  return alert.escalation_label || '需关注';
}

function consensusTrendLabel(trend) {
  return {
    rising: '收敛提升',
    stable: '基本稳定',
    falling: '分歧加深',
  }[trend] || trend || '未知';
}

function consensusTrendColor(trend) {
  return {
    rising: '#6A8E6A',
    stable: '#8A9097',
    falling: '#C05C5C',
  }[trend] || '#8A9097';
}

function escalationStatusLabel(status) {
  return {
    pending: '待处理',
    resolved: '已解决',
  }[status] || status || '未知';
}

function latestDiscussionRound() {
  const explicitRound = Number(curDiscData?.current_round || 0);
  if (explicitRound > 0) return explicitRound;
  const messages = Array.isArray(curDiscData?.messages) ? curDiscData.messages : [];
  return messages.reduce((maxRound, msg) => Math.max(maxRound, Number(msg?.round_number || 0)), 0);
}

function summarizeVerificationStatus(queue) {
  const counts = {};
  (queue || []).forEach(item => {
    const status = item.status || 'unknown';
    counts[status] = (counts[status] || 0) + 1;
  });
  return counts;
}

function normalizeVerificationState(payload = {}) {
  const queue = Array.isArray(payload.queue) ? payload.queue : Array.isArray(payload.items) ? payload.items : [];
  const alerts = Array.isArray(payload.alerts) ? payload.alerts : [];
  return {
    trigger: payload.trigger || '',
    queue,
    alerts,
    queue_count: payload.queue_count ?? payload.count ?? queue.length,
    alert_count: payload.alert_count ?? alerts.length,
    status_counts: payload.status_counts || summarizeVerificationStatus(queue),
    synced_item_ids: Array.isArray(payload.synced_item_ids) ? payload.synced_item_ids : [],
    updated_at: payload.updated_at || '',
  };
}

function normalizeConsensusState(payload = {}) {
  const consensus = payload?.consensus || {};
  const dissentingMessages = Array.isArray(payload?.dissenting_messages) ? payload.dissenting_messages : [];
  return {
    discussion_id: payload?.discussion_id || curDisc || '',
    round_number: payload?.round_number ?? (latestDiscussionRound() || 0),
    score: Number(consensus?.score ?? 0.5),
    agreement_count: Number(consensus?.agreement_count ?? 0),
    disagreement_count: Number(consensus?.disagreement_count ?? 0),
    neutral_count: Number(consensus?.neutral_count ?? 0),
    dissenting_agents: Array.isArray(consensus?.dissenting_agents) ? consensus.dissenting_agents : [],
    convergence_trend: consensus?.convergence_trend || 'stable',
    can_early_exit: Boolean(consensus?.can_early_exit),
    dissenting_messages: dissentingMessages,
  };
}

function normalizeEscalationState(payload = {}) {
  const items = Array.isArray(payload?.items) ? payload.items : [];
  return {
    items,
    total: Number(payload?.total ?? items.length),
    pending_count: Number(payload?.pending_count ?? items.filter(item => item?.status === 'pending').length),
  };
}

function renderVerificationState() {
  const root = $('plan-panel')?.querySelector('.plan-card');
  if (!root) return;
  const existing = root.querySelector('.verification-state');
  const state = curVerificationState;
  if (!state || (!state.queue_count && !state.alert_count)) {
    if (existing) existing.remove();
    return;
  }

  const scrollHost = $('plan-panel');
  const savedScroll = scrollHost ? scrollHost.scrollTop : 0;

  const counts = state.status_counts || {};
  const chips = [
    `<span class="verify-chip">队列 ${state.queue_count || 0}</span>`,
    `<span class="verify-chip">告警 ${state.alert_count || 0}</span>`,
    ...Object.entries(counts).map(([status, count]) => `<span class="verify-chip">${esc(verificationStatusLabel(status))} ${count}</span>`),
  ].join('');

  const listHtml = (state.queue || []).slice(0, 6).map(item => {
    const alert = (state.alerts || []).find(a => a.item_id === item.id);
    const badge = `<span class="verify-badge" style="color:${verificationStatusColor(item.status)};border-color:${verificationStatusColor(item.status)}40;background:${verificationStatusColor(item.status)}12">${esc(verificationStatusLabel(item.status))}</span>`;
    const escalation = item.escalation_label ? `<span class="verify-badge">${esc(item.escalation_label)}</span>` : '';
    const detail = alert?.verify_detail || item.verify_detail || item.verify_result || '';
    const action = verificationAlertLabel(alert);
    return `<div class="verify-item">
      <div class="row">
        <div>
          <div class="title">${esc(item.title || item.id || '未命名演进项')}</div>
          <div class="meta">${esc(item.id || '')}${item.verify_test_name ? ` · ${esc(item.verify_test_name)}` : ''}${item.retry_count ? ` · retry ${item.retry_count}/${item.max_retries || 0}` : ''}</div>
        </div>
        <div style="display:flex;gap:4px;flex-wrap:wrap;justify-content:flex-end">${badge}${escalation}</div>
      </div>
      ${detail ? `<div class="detail">${esc(detail)}</div>` : ''}
      ${action ? `<div class="meta" style="margin-top:4px;color:var(--text)">${esc(action)}</div>` : ''}
    </div>`;
  }).join('');

  const html = `<div class="plan-subsection verification-state">
    <div class="plan-subtitle">VERIFICATION</div>
    <div class="verify-summary">${chips}</div>
    <div class="verify-list">${listHtml || `<div class="verify-empty">当前没有待展示的验证项。</div>`}</div>
    <div class="verify-actions">
      <button class="plan-btn" onclick="refreshVerificationState()">刷新验证状态</button>
      <button class="plan-btn accent" onclick="runVerificationQueue()">运行验证队列</button>
    </div>
  </div>`;

  if (existing) existing.outerHTML = html;
  else root.insertAdjacentHTML('beforeend', html);

  if (scrollHost) scrollHost.scrollTop = savedScroll;
}

function renderConsensusState() {
  const root = $('plan-panel')?.querySelector('.plan-card');
  if (!root) return;
  const existing = root.querySelector('.consensus-state');
  const state = curConsensusState;
  if (!state) {
    if (existing) existing.remove();
    return;
  }

  // 保存滚动位置 — outerHTML 重建会丢失 scrollTop
  const scrollHost = $('plan-panel');
  const savedScroll = scrollHost ? scrollHost.scrollTop : 0;

  const scorePercent = Math.max(0, Math.min(100, Math.round((state.score || 0) * 100)));
  const trendColor = consensusTrendColor(state.convergence_trend);
  const summaryChips = [
    `<span class="verify-chip">轮次 ${esc(state.round_number || '全部')}</span>`,
    `<span class="verify-chip">同意 ${state.agreement_count}</span>`,
    `<span class="verify-chip">分歧 ${state.disagreement_count}</span>`,
    `<span class="verify-chip">中立 ${state.neutral_count}</span>`,
  ].join('');
  const dissentHtml = (state.dissenting_messages || []).slice(0, 4).map(item => `
    <div class="dissent-item">
      <div class="row">
        <div class="title">${esc(item.agent_name || item.agent_id || '未命名智能体')}</div>
        <div class="meta">R${esc(item.round_number || 0)}</div>
      </div>
      <div class="detail">${esc(item.content_preview || '')}</div>
    </div>
  `).join('');
  const html = `<div class="plan-subsection consensus-state">
    <div class="plan-subtitle">CONSENSUS</div>
    <div class="consensus-hero">
      <div>
        <div class="consensus-score">${scorePercent}<span>%</span></div>
        <div class="consensus-meta">${state.can_early_exit ? '已满足提前收敛条件' : '仍建议继续讨论或人工判断'}</div>
      </div>
      <div class="consensus-trend" style="color:${trendColor};border-color:${trendColor}40;background:${trendColor}12">${esc(consensusTrendLabel(state.convergence_trend))}</div>
    </div>
    <div class="consensus-meter"><div class="consensus-meter-fill" style="width:${scorePercent}%;background:${trendColor}"></div></div>
    <div class="verify-summary">${summaryChips}</div>
    <div class="consensus-grid">
      <div class="consensus-stat">
        <div class="label">EARLY EXIT</div>
        <div class="value">${state.can_early_exit ? 'YES' : 'NO'}</div>
      </div>
      <div class="consensus-stat">
        <div class="label">DISSENT</div>
        <div class="value">${state.dissenting_agents.length}</div>
      </div>
    </div>
    <div class="consensus-dissent">
      <div class="plan-subtitle" style="margin-bottom:4px">DISSENT NOTES</div>
      <div class="verify-list">${dissentHtml || `<div class="verify-empty">当前没有明显反方意见。</div>`}</div>
    </div>
    <div class="verify-actions">
      <button class="plan-btn" onclick="refreshConsensusState()">刷新共识</button>
    </div>
  </div>`;

  if (existing) existing.outerHTML = html;
  else root.insertAdjacentHTML('beforeend', html);

  // 恢复滚动位置
  if (scrollHost) scrollHost.scrollTop = savedScroll;
}

function renderEscalationState() {
  const root = $('plan-panel')?.querySelector('.plan-card');
  if (!root) return;
  const existing = root.querySelector('.escalation-state');
  const state = curEscalationState;
  if (!state) {
    if (existing) existing.remove();
    return;
  }

  const scrollHost = $('plan-panel');
  const savedScroll = scrollHost ? scrollHost.scrollTop : 0;

  const listHtml = (state.items || []).slice(0, 6).map(item => {
    const color = item.status === 'resolved' ? '#6A8E6A' : '#C05C5C';
    return `<div class="escalation-item">
      <div class="row">
        <div>
          <div class="title">${esc(item.agent_name || item.agent_id || '未命名智能体')}</div>
          <div class="meta">${item.round_number ? `R${esc(item.round_number)}` : 'R?'}${item.error ? ` · ${esc(item.error)}` : ''}</div>
        </div>
        <div style="display:flex;gap:4px;flex-wrap:wrap;justify-content:flex-end;align-items:center">
          <span class="verify-badge" style="color:${color};border-color:${color}40;background:${color}12">${esc(escalationStatusLabel(item.status))}</span>
          ${item.status === 'pending' ? `<button class="plan-btn danger" onclick="resolveEscalation(${Number(item.index)})">标记已处理</button>` : ''}
        </div>
      </div>
      ${item.prompt_preview ? `<div class="detail">${esc(item.prompt_preview)}</div>` : ''}
      ${item.discussion_topic ? `<div class="meta" style="margin-top:4px">${esc(item.discussion_topic)}</div>` : ''}
    </div>`;
  }).join('');

  const html = `<div class="plan-subsection escalation-state">
    <div class="plan-subtitle">ESCALATIONS</div>
    <div class="verify-summary">
      <span class="verify-chip">总计 ${state.total}</span>
      <span class="verify-chip">待处理 ${state.pending_count}</span>
    </div>
    <div class="verify-list">${listHtml || `<div class="verify-empty">当前讨论没有升级项。</div>`}</div>
    <div class="verify-actions">
      <button class="plan-btn" onclick="refreshEscalationState()">刷新升级项</button>
    </div>
  </div>`;

  if (existing) existing.outerHTML = html;
  else root.insertAdjacentHTML('beforeend', html);

  if (scrollHost) scrollHost.scrollTop = savedScroll;
}

function clearDiscussionSignals() {
  curConsensusState = null;
  curEscalationState = null;
  if (discussionSignalTimer) {
    clearTimeout(discussionSignalTimer);
    discussionSignalTimer = null;
  }
}

function _markPlanPanelBusy() {
  _planPanelBusy = true;
  if (_planPanelBusyTimer) clearTimeout(_planPanelBusyTimer);
  _planPanelBusyTimer = setTimeout(() => {
    _planPanelBusy = false;
    _planPanelBusyTimer = null;
    // 交互结束后，如果有待刷新的信号，补刷一次
    if (discussionSignalTimer) {
      clearTimeout(discussionSignalTimer);
      discussionSignalTimer = null;
      refreshConsensusState(true);
      refreshEscalationState(true);
    }
  }, 1500);
}

function scheduleDiscussionSignalRefresh(delay = 600) {
  if (!curPlaza || !curDisc || !$('plan-panel') || $('plan-panel').style.display === 'none') return;
  // 用户正在滚动/交互 → 跳过本次，交互结束后会补刷
  if (_planPanelBusy) return;
  if (discussionSignalTimer) clearTimeout(discussionSignalTimer);
  discussionSignalTimer = setTimeout(() => {
    discussionSignalTimer = null;
    if (_planPanelBusy) return;  // 定时器到期时再次检查
    refreshConsensusState(true);
    refreshEscalationState(true);
  }, delay);
}

function renderPlanCard(planContent, revised = false) {
  const p = $('plan-panel'); p.style.display = '';
  const previousTeam = $('assign-team')?.value || '';
  const ctxTeam = (() => {
    try { return window.AGCtx?.get?.('team') || ''; } catch (e) { return ''; }
  })();
  const preferredTeam = previousTeam || ctxTeam || '';

  // 如果计划内容没变，跳过全量重建（避免滚动位置丢失 + 闪烁）
  const existingText = p.querySelector('.plan-text')?.textContent || '';
  const existingRevised = !!p.querySelector('.plan-card h4 span');
  if (existingText === planContent && existingRevised === revised && p.querySelector('.plan-card')) {
    // 计划没变，只刷新子面板（它们有自己的滚动保存）
    if (!_planPanelBusy) { renderConsensusState(); renderEscalationState(); renderVerificationState(); }
    return;
  }

  // 用户正在滚动/交互 → 只更新计划文字，不重建 DOM（避免闪烁 + 滚动跳变）
  if (_planPanelBusy && p.querySelector('.plan-text')) {
    p.querySelector('.plan-text').innerHTML = mdLite(planContent);
    return;
  }

  const opts = allTeams.map(t => {
    const selected = preferredTeam && t.team_id === preferredTeam ? ' selected' : '';
    return `<option value="${esc(t.team_id)}"${selected}>${esc(t.name)}</option>`;
  }).join('');
  // 保存滚动位置 — innerHTML 重建会丢失 scrollTop
  const savedScroll = p.scrollTop;
  p.innerHTML = `<div class="plan-card"><h4>执行计划${revised ? ' <span style="font-size:9px;color:var(--slit-glow);margin-left:6px">已修订</span>' : ''}</h4><div class="plan-text">${mdLite(planContent)}</div>
    <div class="assign-row"><span style="font-size:9px;color:var(--dim);font-family:var(--font-mono)">ASSIGN:</span>
    <select id="assign-team" onchange="try{AGCtx.set('team',this.value)}catch(e){}">${opts}</select><button class="plan-btn" onclick="assignPlan()">派发</button></div>
    <div class="plan-actions">
      <button class="plan-btn primary" onclick="dispatchTasks()">智能拆解</button>
      <button class="plan-btn primary" onclick="dispatchAndExecute()">拆解并执行</button>
      <button class="plan-btn accent" onclick="enterEvolution()">进入演化</button>
      <button class="plan-btn accent" onclick="enterCostGov()" title="将讨论结论作为成本治理输入">💰 成本治理</button>
      <button class="plan-btn" onclick="loadExecutionPlan()" title="结构化执行计划：逐步骤审查/批准/驳回/追问">📋 结构化审查</button>
      <button class="plan-btn" onclick="refreshPlan()">↓ 刷新计划</button>
    </div>
    <div id="exec-plan-body" style="margin-top:8px"></div></div>`;
  if (preferredTeam && $('assign-team')) {
    // Re-apply value defensively in case option order changes during rerender.
    $('assign-team').value = preferredTeam;
  }
  // innerHTML 重建后立即恢复滚动位置，再渲染子面板（子面板的 outerHTML 也会保存/恢复）
  p.scrollTop = savedScroll;
  renderConsensusState();
  renderEscalationState();
  renderVerificationState();
}

function renderPlan(disc) {
  const planContent = disc.plan?.content || disc.summary || '';
  renderPlanCard(planContent, false);
}

function renderLivePlan(plan) {
  const planContent = plan.content || '';
  renderPlanCard(planContent, true);
}

window.assignPlan = async function() {
  if (!curPlaza || !curDisc) return;
  const r = await api(`${API}/plaza/${curPlaza}/discussions/${curDisc}/assign`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ team_id: $('assign-team').value }) });
  if (r) { toast(`计划已派发: ${r.status}`); }
  else { const detail = window.api?._lastError?.message || ''; toast('派发失败' + (detail ? '：' + detail : '')); }
};

window.dispatchTasks = async function() {
  if (!curPlaza || !curDisc) return;
  const teamId = $('assign-team')?.value;
  if (!teamId) { toast('请选择团队'); return; }
  toast('正在智能拆解任务...');
  const r = await api(`${API}/plaza/${curPlaza}/discussions/${curDisc}/dispatch`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ team_id: teamId })
  });
  if (r && r.task_count) {
    toast(`已拆解 ${r.task_count} 个任务并派发到团队`);
    renderDispatchedTasks(r.tasks);
    renderStructuredOutput(r.output || (r.outputs || [])[0]);
  } else if (r) {
    toast('未拆解出任务：执行计划中没有可识别的任务条目');
  } else {
    const detail = window.api?._lastError?.message || '';
    toast('拆解失败' + (detail ? '：' + detail : ''));
  }
};

window.dispatchAndExecute = async function() {
  if (!curPlaza || !curDisc) return;
  const teamId = $('assign-team')?.value;
  if (!teamId) { toast('请选择团队'); return; }
  toast('正在拆解并立即执行...');
  const r = await api(`${API}/plaza/${curPlaza}/discussions/${curDisc}/dispatch-and-execute`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ team_id: teamId })
  });
  if (r && r.task_count) {
    toast(`已拆解 ${r.task_count} 个任务，正在执行中`);
    renderDispatchedTasks(r.tasks);
    renderStructuredOutput(r.output || (r.outputs || [])[0]);
  } else if (r) {
    toast('未拆解出任务：执行计划中没有可识别的任务条目');
  } else {
    const detail = window.api?._lastError?.message || '';
    toast('拆解执行失败' + (detail ? '：' + detail : ''));
  }
};

window.enterEvolution = async function() {
  if (!curPlaza || !curDisc) return;
  const teamId = $('assign-team')?.value;
  toast('正在进入系统演化...');
  // 直接 fetch 以便拿到后端真实原因（尚无执行计划 / 演化引擎未初始化 等），不再笼统报"失败"
  let r = null, detail = '';
  try {
    const resp = await (window._agFetch || fetch)(`${API}/plaza/${curPlaza}/discussions/${curDisc}/evolve`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, credentials: 'same-origin',
      body: JSON.stringify({ team_id: teamId || '' })
    });
    const d = await resp.json().catch(() => ({}));
    if (resp.ok) { r = d; }
    else { detail = String(d?.detail || d?.message || `HTTP ${resp.status}`); }
  } catch (e) { detail = e.message || '网络错误'; }
  if (r && r.status === 'evolving') {
    toast(`演化已启动: ${r.evolution_items || 0} 项演进需求`);
    if (r.tasks) renderDispatchedTasks(r.tasks);
    renderStructuredOutput(r.output || (r.outputs || [])[0]);
    await refreshVerificationState();
  } else {
    // 常见原因：尚无执行计划（先点"刷新计划"生成计划表）/ 演化引擎未初始化（重启后端）
    toast('演化启动失败' + (detail ? '：' + detail : '（请先生成执行计划）'));
  }
};

// ── 成本治理入口 ──
window.enterCostGov = async function() {
  if (!curPlaza || !curDisc) return;
  const teamId = $('assign-team')?.value;
  const disc = curDiscData || await api(`${API}/plaza/${curPlaza}/discussions/${curDisc}`);
  const planText = disc?.plan?.content || disc?.summary || '';
  // Record cost_governance output
  try {
    await api(`${API}/plaza/${curPlaza}/discussions/${curDisc}/outputs`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ type: 'cost_governance', team_id: teamId || '', summary: planText.slice(0,500) })
    });
  } catch(e) { /* non-critical */ }
  toast('正在跳转成本治理…');
  const targetUrl = new URL('/cost-dashboard.html', window.location.origin);
  targetUrl.searchParams.set('source', 'plaza');
  targetUrl.searchParams.set('plaza_id', curPlaza);
  targetUrl.searchParams.set('discussion_id', curDisc);
  if (teamId) targetUrl.searchParams.set('team_id', teamId);
  window.location.href = targetUrl.pathname + targetUrl.search;
};

window.refreshVerificationState = async function(silent = false) {
  if (!curPlaza || !curDisc) return;
  const [queue, alerts] = await Promise.all([
    api(`${API}/plaza/${curPlaza}/discussions/${curDisc}/verification-queue`),
    api(`${API}/plaza/${curPlaza}/discussions/${curDisc}/verification-alerts`),
  ]);
  curVerificationState = normalizeVerificationState({
    queue: queue?.items || [],
    queue_count: queue?.count || 0,
    alerts: alerts?.alerts || [],
    alert_count: alerts?.count || 0,
  });
  renderVerificationState();
  if (!silent && (curVerificationState.queue_count || curVerificationState.alert_count)) {
    toast(`验证队列 ${curVerificationState.queue_count} 项 · 告警 ${curVerificationState.alert_count} 项`);
  }
};

window.refreshConsensusState = async function(silent = false) {
  if (!curPlaza || !curDisc) return;
  const latestRound = latestDiscussionRound();
  const query = latestRound > 0 ? `?round_number=${latestRound}` : '';
  const payload = await api(`${API}/plaza/${curPlaza}/discussions/${curDisc}/consensus${query}`);
  if (!payload) return;
  curConsensusState = normalizeConsensusState(payload);
  renderConsensusState();
  if (!silent) toast(`共识 ${Math.round((curConsensusState.score || 0) * 100)}% · ${consensusTrendLabel(curConsensusState.convergence_trend)}`);
};

window.refreshEscalationState = async function(silent = false) {
  let plazaId = curPlaza || '';
  let discussionId = curDisc || '';

  // Self-heal context to survive stale closure state or invalid deep links.
  if (!plazaId || !isKnownPlaza(plazaId)) {
    plazaId = activePlazaIdFromDOM() || localStorage.getItem('plaza_curPlaza') || '';
  }
  if (!discussionId) {
    discussionId = activeDiscussionIdFromDOM() || localStorage.getItem('plaza_curDisc') || '';
  }

  if (!plazaId || !discussionId) return;
  if (knownPlazas.length && !isKnownPlaza(plazaId)) return;

  if (plazaId !== curPlaza) curPlaza = plazaId;
  if (discussionId !== curDisc) curDisc = discussionId;

  const ctxKey = escalationCtxKey(plazaId, discussionId);
  if (escalationFetchBlocked.has(ctxKey)) return;
  if (escalationFetchInFlight.has(ctxKey)) return;
  escalationFetchInFlight.add(ctxKey);

  try {
    const escalationUrl = `${API}/plaza/escalations?plaza_id=${encodeURIComponent(plazaId)}&discussion_id=${encodeURIComponent(discussionId)}`;
    const resp = await fetch(escalationUrl, { credentials: 'same-origin' });
    if (!resp.ok) {
      let msg = '';
      try {
        const d = await resp.json();
        msg = String(d?.detail || d?.message || '');
      } catch (_) {
        // no-op
      }
      // Some legacy discussions can miss escalation context on backend; stop retry storm for this context.
      if (resp.status === 404 && /广场不存在|讨论不存在/.test(msg)) {
        escalationFetchBlocked.add(ctxKey);
        if (!silent) toast('升级项上下文不可用，已暂停该讨论的升级项拉取');
        return;
      }
      if (!silent) toast(`升级项拉取失败 (HTTP ${resp.status})`);
      return;
    }
    const payload = await resp.json();
    curEscalationState = normalizeEscalationState(payload);
    renderEscalationState();
    if (!silent && curEscalationState.total) {
      toast(`升级项 ${curEscalationState.total} 条 · 待处理 ${curEscalationState.pending_count}`);
    }
  } finally {
    escalationFetchInFlight.delete(ctxKey);
  }
};

window.resolveEscalation = async function(index) {
  if (!Number.isFinite(Number(index))) return;
  const result = await api(`${API}/plaza/escalations/${Number(index)}/resolve`, { method: 'POST' });
  if (!result) {
    toast('升级项处理失败');
    return;
  }
  toast(`升级项 #${Number(index)} 已标记处理`);
  await refreshEscalationState(true);
};

window.runVerificationQueue = async function() {
  if (!curPlaza || !curDisc) return;
  toast('正在运行验证队列...');
  const r = await api(`${API}/plaza/${curPlaza}/discussions/${curDisc}/verification-queue/run`, {
    method: 'POST'
  });
  if (!r) { toast('验证队列运行失败'); return; }
  curVerificationState = normalizeVerificationState(r);
  renderVerificationState();
  const verified = r.verify?.count || 0;
  const closed = Array.isArray(r.closed) ? r.closed.length : 0;
  toast(`验证完成 ${verified} 项 · 关闭 ${closed} 项`);
};

function renderDispatchedTasks(tasks) {
  if (!tasks || !tasks.length) return;
  const p = $('plan-panel');
  const existing = p.querySelector('.dispatched-tasks');
  const html = `<div class="dispatched-tasks" style="margin-top:10px;border-top:1px solid var(--line);padding-top:8px">
    <h4 style="font-size:10px;color:var(--dim);margin-bottom:6px;letter-spacing:1px">TASKS (${tasks.length})</h4>
    ${tasks.map((t, i) => `<div style="display:flex;align-items:center;gap:6px;padding:4px 0;font-size:11px">
      <span style="width:8px;height:8px;border-radius:50%;background:${t.status==='running'?'var(--accent)':t.status==='completed'?'#67c23a':'var(--dim)'};flex-shrink:0"></span>
      <span style="color:var(--text);flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${esc(t.title)}</span>
      <span style="font-size:9px;color:var(--dim);font-family:var(--font-mono)">${t.metadata?.responsible||''}</span>
    </div>`).join('')}
  </div>`;
  if (existing) existing.outerHTML = html;
  else p.querySelector('.plan-card').insertAdjacentHTML('beforeend', html);
  renderVerificationState();
}

function renderStructuredOutput(output) {
  if (!output) return;
  const p = $('plan-panel');
  if (!p) return;
  const card = p.querySelector('.plan-card');
  if (!card) return;
  const existing = card.querySelector('.structured-output');
  const source = output.source || {};
  const targets = Array.isArray(output.target_ids) ? output.target_ids : [];
  const typeLabel = {
    task: '任务',
    task_execution: '任务执行',
    evolution_item: '演进项',
    skill_candidate: '技能候选',
    cost_governance: '成本治理项',
  }[output.type] || output.type || '输出';
  const html = `<div class="structured-output" style="margin-top:10px;border-top:1px solid var(--line);padding-top:8px">
    <h4 style="font-size:10px;color:var(--dim);margin-bottom:6px;letter-spacing:1px">STRUCTURED OUTPUT</h4>
    <div style="display:grid;grid-template-columns:80px 1fr;gap:4px 8px;font-size:11px;color:var(--dim);line-height:1.6">
      <span>类型</span><strong style="color:var(--text)">${esc(typeLabel)}</strong>
      <span>团队</span><strong style="color:var(--text)">${esc(output.team_id || '-')}</strong>
      <span>目标</span><span style="font-family:var(--font-mono);color:var(--text);word-break:break-all">${esc(targets.join(', ') || '-')}</span>
      <span>来源</span><span style="color:var(--text)">${esc(source.topic || source.discussion_id || '-')}</span>
    </div>
  </div>`;
  if (existing) existing.outerHTML = html;
  else card.insertAdjacentHTML('beforeend', html);
}

window.openCreateDisc = async function() {
  if (!curPlaza) { toast('请先选择广场'); return; }
  const plaza = await api(`${API}/plaza/${curPlaza}`);
  if (plaza?.participants) {
    const chair = plaza.participants.find(p => p.niche_role === 'moderator');
    $('inp-dm').innerHTML = plaza.participants.map(p => `<option value="${esc(p.agent_id)}"${chair && p.agent_id === chair.agent_id ? ' selected' : ''}>${esc(p.agent_name)}</option>`).join('');
  }
  openM('m-disc'); $('inp-dt').focus();
};

window.doCreateDisc = async function() {
  const topic = $('inp-dt').value.trim();
  if (!topic) { toast('请输入话题'); return; }
  const desc = $('inp-dd').value.trim();
  if (desc.length > 2000) { toast('背景内容过长，请缩减到2000字以内'); return; }
  const body = { topic, goal: $('inp-dg').value.trim(), description: desc, moderator_agent_id: $('inp-dm').value, max_rounds: parseInt($('inp-dr').value) };
  try {
    const r = await api(`${API}/plaza/${curPlaza}/discussions`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
    if (!r) {
      const detail = window.api?._lastError?.message || '创建失败，请检查输入';
      toast(Array.isArray(detail) ? detail[0]?.msg || '创建失败，请检查输入' : detail);
      return;
    }
    closeM('m-disc'); $('inp-dt').value=''; $('inp-dg').value=''; $('inp-dd').value=''; toast('讨论已创建'); selectPlaza(curPlaza); setTimeout(() => selectDisc(r.id), 300);
  } catch(e) { toast('网络错误: ' + e.message); }
};

window.startDiscussion = async function() {
  if (!curPlaza || !curDisc) return;

  // 检查 LLM 配置是否就绪
  const llmStatus = await api('/api/v1/agent-config/llm/status').catch(() => null);
  if(!llmStatus || !llmStatus.provider){
    var shouldConfig = confirm('⚠️ LLM 提供商尚未配置，讨论将无法生成回复。\n\n是否前往「模型与连接」页面配置？');
    if(shouldConfig) window.location.href = '/agent-team-config.html?view=llm';
    $('btn-start').disabled = false;
    $('btn-start').textContent = curDiscData?.status === 'closed' ? '重新讨论' : '开始';
    return;
  }
  if(llmStatus.provider === 'local' && !llmStatus.model){
    toast('⚠️ LLM 提供商已配置为本地，但模型名未填。请在「LLM 配置」中补全模型信息。');
    $('btn-start').disabled = false;
    $('btn-start').textContent = curDiscData?.status === 'closed' ? '重新讨论' : '开始';
    return;
  }

  unlockAudio();
  const previousStatus = curDiscData?.status || 'open';
  $('btn-start').disabled = true; $('btn-start').textContent = '启动中…';
  const r = await api(`${API}/plaza/${curPlaza}/discussions/${curDisc}/start`, { method: 'POST' });
  if (r) connectSSE(curDisc);
  else {
    $('btn-start').disabled = false;
    $('btn-start').textContent = previousStatus === 'closed' ? '重新讨论' : '开始';
    toast('启动失败 — 请确认 LLM 已正确配置');
  }
};

window.sendInterject = async function() {
  if (!curPlaza || !curDisc) { toast('请先选择讨论'); return; }
  const input = $('chat-input');
  const msg = input.value.trim();
  if (!msg) return;
  input.value = '';
  const btn = document.querySelector('.chat-send-btn');
  btn.disabled = true; btn.textContent = '思考中…';
  // Immediately show user message for instant feedback
  if (!evtSrc) appendMsg({ agent_name: '用户', niche_role: 'human', content: msg });
  const r = await api(`${API}/plaza/${curPlaza}/discussions/${curDisc}/interject`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message: msg })
  });
  btn.disabled = false; btn.textContent = '发送';
  if (r) {
    // If no SSE, manually show moderator reply (user msg already shown above)
    if (!evtSrc) {
      if (r.moderator_reply) { appendMsg(r.moderator_reply); showSpeechBubble(r.moderator_reply.agent_id, r.moderator_reply.agent_name, r.moderator_reply.content); }
      if (r.nominated_reply) { appendMsg(r.nominated_reply); showSpeechBubble(r.nominated_reply.agent_id, r.nominated_reply.agent_name, r.nominated_reply.content); }
      if (r.extra_replies) { r.extra_replies.forEach(m => { appendMsg(m); showSpeechBubble(m.agent_id, m.agent_name, m.content); }); }
      if (r.moderator_resume) { appendMsg(r.moderator_resume); showSpeechBubble(r.moderator_resume.agent_id, r.moderator_resume.agent_name, r.moderator_resume.content); }
    }
    // 在议事长回复后显示操作按钮
    if (r.moderator_resume || r.moderator_reply) {
      appendModeratorActions(msg);
    }
    if (r.action === 'redirect') toast('议事长已纠偏并修订执行计划');
    if (r.action === 'new_discussion' && r.new_discussion?.id) {
      toast('议事长决定开一个新讨论');
      await selectPlaza(curPlaza);
      setTimeout(() => selectDisc(r.new_discussion.id), 200);
    }
  } else {
    toast('发送失败');
  }
};

function appendMsg(m) {
  const log = $('msg-log');
  if (log.querySelector('[style*="text-align:center"]')) log.innerHTML = '';
  const isMod = m.niche_role === 'moderator';
  const isUser = m.niche_role === 'human';
  const cls = isMod ? 'mod' : (isUser ? 'user' : '');
  const label = isMod ? ` · 议事长` : (isUser ? ' · 你' : '');
  const modAction = isMod ? `<div style="margin-top:6px;text-align:right"><button class="plan-btn" onclick="refreshPlan()" style="font-size:11px;padding:2px 10px">↻ 修订执行计划</button></div>` : '';
  log.insertAdjacentHTML('beforeend', `<div class="msg-entry ${cls}"><div class="me-name">${esc(m.agent_name)}${label}</div><div class="me-text">${mdLite(m.content)}</div>${modAction}</div>`);
  log.scrollTop = log.scrollHeight;
}

function appendModeratorActions(userQuestion) {
  const log = $('msg-log');
  // 移除旧的操作栏
  log.querySelectorAll('.mod-actions').forEach(el => el.remove());
  const safeQ = esc(userQuestion).replace(/'/g, '&#39;');
  log.insertAdjacentHTML('beforeend', `<div class="mod-actions" style="display:flex;gap:6px;padding:8px 14px;justify-content:flex-end;flex-wrap:wrap">
    <button class="plan-btn primary" onclick="continueDeepDiscussion('${safeQ}')">根据此话题继续深入讨论</button>
    <button class="plan-btn" onclick="refreshPlan()">↓ 刷新计划</button>
  </div>`);
  log.scrollTop = log.scrollHeight;
}

window.continueDeepDiscussion = async function(question) {
  if (!curPlaza || !question) return;
  toast('正在创建深入讨论…');
  const r = await api(`${API}/plaza/${curPlaza}/discussions`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      topic: `深入讨论: ${question.slice(0, 60)}`,
      goal: `围绕「${question}」进行深入分析，产出可执行的具体方案`,
      max_rounds: 3,
    })
  });
  if (r && r.id) {
    toast('深入讨论已创建，正在启动…');
    await selectPlaza(curPlaza);
    setTimeout(async () => {
      await selectDisc(r.id);
      // 自动启动讨论
      await api(`${API}/plaza/${curPlaza}/discussions/${r.id}/start`, { method: 'POST' });
      connectSSE(r.id);
    }, 300);
  } else {
    toast('创建失败');
  }
};

window.reopenDisc = async function(event, discId) {
  event?.stopPropagation();
  const id = discId || curDisc;
  if (!curPlaza || !id) return;
  try {
    await api(`${API}/plaza/${curPlaza}/discussions/${id}/start`, { method: 'POST' });
    toast('话题已重新开启');
    await selectPlaza(curPlaza);
    await selectDisc(id);
  } catch (e) { toast('重新开启失败: ' + (e.message || '服务异常')); }
};

/** Format Plaza discussion as TSE-friendly transcript (messages + summary/plan). */
function buildDiscExtractText(disc) {
  const lines = [];
  const topic = (disc && (disc.topic || disc.title)) || '讨论萃取';
  lines.push(`Topic: ${topic}`);
  if (disc?.goal) lines.push(`Goal: ${disc.goal}`);
  const msgs = Array.isArray(disc?.messages) ? disc.messages : [];
  msgs.forEach((m, i) => {
    const content = String(m?.content || m?.text || m?.body || '').trim();
    if (!content) return;
    const rnd = (m.round_number != null ? m.round_number : m.round);
    const round = (rnd != null && rnd !== '') ? rnd : Math.floor(i / 4);
    const name = m.agent_name || m.speaker_name || m.name || m.agent_id || `Speaker${i + 1}`;
    const role = m.role || m.niche_role || m.seat_role || 'participant';
    const signal = m.ritual_signal || m.signal || 'supplement';
    lines.push(`[Round ${round}] ${name} (${role}, signal=${signal}): ${content}`);
  });
  if (disc?.summary) {
    lines.push('');
    lines.push('--- Summary ---');
    lines.push(String(disc.summary).trim());
  }
  const planContent = disc?.plan?.content || (typeof disc?.plan === 'string' ? disc.plan : '');
  if (planContent) {
    lines.push('');
    lines.push('--- Execution Plan ---');
    lines.push(String(planContent).trim());
  }
  return lines.join('\n').trim();
}

window.extractFromDisc = async function(event, discId) {
  event?.stopPropagation();
  const id = discId || curDisc;
  if (!curPlaza || !id) return;
  toast('正在准备萃取…');
  const disc = await api(`${API}/plaza/${curPlaza}/discussions/${id}`);
  if (!disc) { toast('获取讨论失败'); return; }
  // 完整讨论可萃：消息 transcript 优先（TSE 时序输入）；无消息再退 summary/plan
  const sourceText = buildDiscExtractText(disc);
  const msgCount = Array.isArray(disc.messages) ? disc.messages.length : 0;
  if (!sourceText || sourceText.length < 10) {
    toast(msgCount ? '讨论内容过短，无法萃取' : '讨论无消息且无计划/总结，无法萃取');
    return;
  }
  const title = disc.topic || '讨论萃取';
  // Pass participating teams to extract page
  const plaza = await api(`${API}/plaza/${curPlaza}`);
  const routing = buildExtractRouting(plaza, disc);
  let recordedOutput = null;
  const outputPayload = {
    output_type: 'skill_candidate',
    target_ids: [],
    team_id: routing.preferredTeamId || '',
    status_value: 'prepared',
  };
  try {
    const outputResp = await api(`${API}/plaza/${curPlaza}/discussions/${id}/outputs`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(outputPayload),
    });
    recordedOutput = outputResp?.output || (outputResp?.outputs || [])[0] || null;
  } catch (e) {
    // 结构化 output 失败不挡萃取（旧逻辑会因此整段中断）
    console.warn('plaza output record failed', e);
  }
  if (recordedOutput) {
    renderStructuredOutput(recordedOutput);
    sessionStorage.setItem('plaza_structured_output', JSON.stringify(recordedOutput));
  } else {
    sessionStorage.removeItem('plaza_structured_output');
  }
  const extractPayload = {
    source_text: sourceText,
    source_title: title,
    source_type: 'chat',
    source_plaza_id: curPlaza,
    source_discussion_id: id,
    source_output_id: recordedOutput?.id || '',
    topic: title,
    // 结构化 messages 供 TSE Stage1 直接用（skill-extract → source_meta）
    messages: (disc.messages || []).map((m, i) => ({
      msg_id: m.id || m.msg_id || `m${i}`,
      speaker_id: m.agent_id || m.speaker_id || `spk_${i}`,
      speaker_name: m.agent_name || m.speaker_name || m.name || `Speaker${i + 1}`,
      role: m.role || m.niche_role || 'participant',
      niche_role: m.niche_role || 'analyst',
      ritual_signal: m.ritual_signal || m.signal || 'supplement',
      round_number: m.round_number != null ? m.round_number : (m.round != null ? m.round : Math.floor(i / 4)),
      content: m.content || m.text || '',
    })),
  };
  sessionStorage.setItem('extract_source', JSON.stringify(extractPayload));
  // 只有从讨论参与者中提取到团队信息时才过滤，避免空参与者导致默认跳到错误团队
  if (routing.teamIds.length) {
    sessionStorage.setItem('extract_teams', JSON.stringify(routing.teamIds));
  } else {
    sessionStorage.removeItem('extract_teams');  // 不清除的话 skill-extract 会显示所有团队
  }
  if (routing.preferredTeamId) {
    sessionStorage.setItem('extract_team_id', routing.preferredTeamId);
  } else {
    sessionStorage.removeItem('extract_team_id');
  }
  toast(`正在跳转萃取（${msgCount} 条消息）…`);
  const targetUrl = new URL('/skill-extract.html', window.location.origin);
  if (routing.preferredTeamId) targetUrl.searchParams.set('team_id', routing.preferredTeamId);
  // URL 备份：sessionStorage 丢了也能按 plaza/discussion 拉回正文
  targetUrl.searchParams.set('plaza_id', curPlaza);
  targetUrl.searchParams.set('discussion_id', id);
  targetUrl.searchParams.set('auto_extract', '1');
  window.location.href = targetUrl.pathname + targetUrl.search;
};

window.exportDiscPDF = async function(event, discId) {
  event?.stopPropagation();
  const id = discId || curDisc;
  if (!curPlaza || !id) return;
  toast('正在生成网页…');
  const disc = await api(`${API}/plaza/${curPlaza}/discussions/${id}`);
  if (!disc) { toast('获取讨论失败'); return; }
  const title = disc.topic || '讨论记录';
  const msgs = disc.messages || [];
  let body = `<h1 style="font-size:18px;margin-bottom:4px">${esc(title)}</h1>`;
  if (disc.goal) body += `<p style="color:#666;font-size:12px;margin-bottom:8px">目标: ${esc(disc.goal)}</p>`;
  body += `<p style="color:#999;font-size:10px;margin-bottom:16px">状态: ${statusTxt(disc.status)} · ${msgs.length} 条消息</p><hr style="border:none;border-top:1px solid #ddd;margin:12px 0">`;
  let lr = -1;
  msgs.forEach(m => {
    if (m.round_number !== lr && m.round_number > 0) { body += `<div style="text-align:center;color:#999;font-size:10px;margin:12px 0">── ROUND ${m.round_number} ──</div>`; lr = m.round_number; }
    const label = m.niche_role === 'moderator' ? ' · 议事长' : (m.niche_role === 'human' ? ' · 你' : '');
    body += `<div style="margin-bottom:12px"><div style="font-weight:600;font-size:12px;color:#333;margin-bottom:2px">${esc(m.agent_name)}${label}</div><div style="font-size:12px;line-height:1.8;color:#444;white-space:pre-wrap">${esc(m.content)}</div></div>`;
  });
  if (disc.summary) { body += `<hr style="border:none;border-top:1px solid #ddd;margin:12px 0"><h2 style="font-size:14px;margin-bottom:6px">总结</h2><div style="font-size:12px;line-height:1.8;color:#444;white-space:pre-wrap">${esc(disc.summary)}</div>`; }
  if (disc.plan?.content) { body += `<hr style="border:none;border-top:1px solid #ddd;margin:12px 0"><h2 style="font-size:14px;margin-bottom:6px">执行计划</h2><div style="font-size:12px;line-height:1.8;color:#444;white-space:pre-wrap">${esc(disc.plan.content)}</div>`; }
  const html = `<!DOCTYPE html><html><head><meta charset="utf-8"><title>${esc(title)}</title><style>body{font-family:sans-serif;max-width:800px;margin:40px auto;padding:0 20px}@media print{body{margin:20px}}</style></head><body>${body}</body></html>`;
  const blob = new Blob([html], { type: 'text/html;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = `${title}.html`; a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
  toast('已下载网页文件');
};

window.refreshPlan = async function() {
  if (!curPlaza || !curDisc) return;
  toast('议事长正在重新梳理执行计划…');
  const r = await api(`${API}/plaza/${curPlaza}/discussions/${curDisc}/refresh-plan`, {
    method: 'POST',
  });
  if (r && r.plan) {
    if (curDiscData) curDiscData = { ...curDiscData, plan: r.plan };
    renderLivePlan(r.plan);
    if (r.message) { appendMsg(r.message); }
    scheduleDiscussionSignalRefresh(200);
    toast('执行计划已更新');
  } else {
    toast('刷新失败');
  }
};

/* ═══════════ P5-3 结构化执行计划面板（批准/驳回/逐步骤追问） ═══════════ */
const _PLAN_STEP_STATUS = {
  pending: { label: '待执行', color: 'var(--dim)' },
  dispatched: { label: '执行中', color: 'var(--slit-glow)' },
  completed: { label: '已完成', color: '#34d399' },
  failed: { label: '失败', color: '#ef4444' },
};

window.loadExecutionPlan = async function(rebuild = false) {
  if (!curPlaza || !curDisc) { toast('请先选择讨论'); return; }
  const body = $('exec-plan-body');
  if (body) body.innerHTML = '<div style="font-size:10px;color:var(--dim);padding:6px">加载结构化计划…</div>';
  const r = await api(`${API}/plaza/${curPlaza}/discussions/${curDisc}/execution-plan${rebuild ? '?rebuild=true' : ''}`);
  if (!r || !r.plan) { if (body) body.innerHTML = '<div style="font-size:10px;color:var(--dim);padding:6px">尚无结构化计划，先完成讨论或点「刷新计划」。</div>'; return; }
  renderExecutionPlan(r);
};

function renderExecutionPlan(r) {
  const body = $('exec-plan-body');
  if (!body) return;
  const plan = r.plan || {};
  const issues = r.issues || [];
  const steps = plan.steps || [];
  // 落地性审查缺项（按步聚合）
  const issueByStep = {};
  issues.forEach((i) => { (issueByStep[i.step] = issueByStep[i.step] || []).push(i.field || i.issue || ''); });
  const stepsHtml = steps.map((s) => {
    const st = _PLAN_STEP_STATUS[s.status] || _PLAN_STEP_STATUS.pending;
    const miss = issueByStep[s.step_id] || [];
    const missHtml = miss.length ? `<div style="font-size:9px;color:#ef4444;margin-top:2px">⚠ 缺: ${esc(miss.join(' / '))}</div>` : '';
    const skills = (s.required_skills || []).map((k) => `<span class="chip">${esc(k)}</span>`).join('');
    return `<div class="exec-step" style="border:1px solid var(--line);border-radius:6px;padding:6px 8px;margin-bottom:6px">
      <div style="display:flex;justify-content:space-between;align-items:center">
        <b style="font-size:11px">${s.index != null ? s.index + '. ' : ''}${esc(s.title || s.step_id)}</b>
        <span style="font-size:9px;color:${st.color}">● ${st.label}</span>
      </div>
      <div style="font-size:9px;color:var(--dim);margin-top:2px">角色: ${esc(s.responsible_role || '—')} · 验收: ${esc(s.acceptance || '—')}</div>
      ${skills ? `<div style="margin-top:3px">${skills}</div>` : ''}
      ${missHtml}
      <div style="margin-top:4px"><button class="plan-btn" style="font-size:9px;padding:2px 6px" onclick="askPlanStep('${esc(s.step_id)}','${esc((s.title || '').replace(/'/g, ''))}')">💬 追问此步骤</button></div>
    </div>`;
  }).join('') || '<div style="font-size:10px;color:var(--dim)">计划暂无步骤</div>';

  const approved = plan.status === 'approved' || plan.status === 'dispatched';
  const gate = issues.length
    ? `<div style="font-size:10px;color:#ef4444;margin-bottom:6px">落地性审查未通过：${issues.length} 处缺项，补齐后可批准（或强制批准保留人的最终决定权）。</div>`
    : `<div style="font-size:10px;color:#34d399;margin-bottom:6px">✅ 落地性审查通过，可批准派发。</div>`;

  // v4: 缓存计划供「送入物竞试验田」深链
  try {
    window.__LAST_EXECUTION_PLAN__ = plan;
    sessionStorage.setItem('eco_bound_plan', JSON.stringify(plan));
    sessionStorage.setItem('eco_bound_plan_meta', JSON.stringify({
      plaza_id: curPlaza || plan.plaza_id || '',
      discussion_id: curDisc || plan.discussion_id || '',
      plan_id: plan.plan_id || '',
    }));
  } catch (e) { /* ignore quota */ }

  body.innerHTML = `<div class="exec-plan" style="border-top:1px dashed var(--line);padding-top:8px">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px">
      <b style="font-size:11px">📋 结构化执行计划 <span style="font-size:9px;color:var(--dim)">rev.${plan.revision || 1} · ${esc(plan.status || 'draft')}</span></b>
    </div>
    ${gate}
    ${stepsHtml}
    <div class="plan-actions" style="margin-top:6px;display:flex;flex-wrap:wrap;gap:6px;align-items:center">
      ${approved
        ? '<span style="font-size:10px;color:#34d399">已批准 ✓</span>'
        : `<button class="plan-btn primary" onclick="approveExecutionPlan(false)">✅ 批准</button>${issues.length ? '<button class="plan-btn" onclick="approveExecutionPlan(true)" title="保留人的最终决定权，跳过审查">强制批准</button>' : ''}`}
      <button class="plan-btn" onclick="rejectExecutionPlan()" title="驳回并让议事长重新梳理计划（重议）">✖ 驳回·重议</button>
      <button class="plan-btn primary" onclick="sendPlanToEcoField()" title="先选团队并派发任务，再打开物竞（推荐从团队任务菜单进入）">🧬 派发并送入物竞</button>
    </div>
  </div>`;
}

/**
 * XG-11: Plaza → 先确保团队 + 智能拆解 → 带 team_id 打开物竞试验田
 * 推荐心智：拆解后也可在「团队任务」行点 🧬 物竞试验田。
 */
window.sendPlanToEcoField = async function () {
  const plan = window.__LAST_EXECUTION_PLAN__;
  if (!plan || !(plan.steps && plan.steps.length)) {
    toast('暂无结构化计划步骤，请先生成/批准执行计划');
    return;
  }
  const teamId = $('assign-team')?.value;
  if (!teamId) {
    toast('请先在上方选择要派发的智能体团队，再送入物竞');
    return;
  }
  const teamName = ($('assign-team')?.selectedOptions?.[0]?.textContent || teamId).trim();

  // 若计划尚未拆解出任务，先智能拆解（不 auto_start）
  let taskIds = Array.isArray(plan.task_ids) ? plan.task_ids.filter(Boolean) : [];
  if (!taskIds.length && plan.steps?.some(s => s.task_id)) {
    taskIds = plan.steps.map(s => s.task_id).filter(Boolean);
  }
  if (!taskIds.length) {
    toast('正在智能拆解并派发到团队…');
    const r = await api(`${API}/plaza/${curPlaza}/discussions/${curDisc}/dispatch`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ team_id: teamId }),
    });
    if (r && r.task_count) {
      taskIds = (r.tasks || []).map(t => t.task_id || t.id).filter(Boolean);
      renderDispatchedTasks(r.tasks);
      toast(`已拆解 ${r.task_count} 个任务 → 打开物竞试验田`);
    } else if (r) {
      toast('未拆解出任务：将仅带计划与团队进入物竞');
    } else {
      const detail = window.api?._lastError?.message || '';
      toast('拆解失败' + (detail ? '：' + detail : '') + '；仍将带团队进入物竞');
    }
  }

  try {
    sessionStorage.setItem('eco_bound_plan', JSON.stringify(plan));
    sessionStorage.setItem('eco_bound_plan_meta', JSON.stringify({
      plaza_id: curPlaza || plan.plaza_id || '',
      discussion_id: curDisc || plan.discussion_id || '',
      plan_id: plan.plan_id || '',
      team_id: teamId,
    }));
    sessionStorage.setItem('eco_bound_team', JSON.stringify({ id: teamId, name: teamName }));
  } catch (e) { /* ignore */ }

  const pid = encodeURIComponent(plan.plan_id || '');
  const plz = encodeURIComponent(curPlaza || plan.plaza_id || '');
  const disc = encodeURIComponent(curDisc || plan.discussion_id || '');
  const tid = encodeURIComponent(teamId);
  const tname = encodeURIComponent(teamName);
  const firstTask = taskIds[0] ? `&task_id=${encodeURIComponent(taskIds[0])}` : '';
  const url = `/Agent-digital-twin.html?office3d=1&team_id=${tid}&team_name=${tname}&plan_id=${pid}&plaza_id=${plz}&discussion_id=${disc}${firstTask}`;
  window.open(url, '_blank');
  toast('已打开物竞试验田（团队已绑定' + (taskIds[0] ? '，首任务已带入' : '') + '）。也可在团队「任务」菜单对单行点 🧬');
};

window.approveExecutionPlan = async function(force = false) {
  if (!curPlaza || !curDisc) return;
  const r = await api(`${API}/plaza/${curPlaza}/discussions/${curDisc}/execution-plan/approve`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ approved_by: localStorage.getItem('ag-user') || 'user', force: !!force }),
  });
  if (r && r.status === 'approved') { toast(force ? '已强制批准' : '计划已批准'); loadExecutionPlan(); }
  else toast('批准失败：落地性审查未通过，请补齐缺项或强制批准');
};

// 驳回 = 让议事长根据对话重新梳理计划（重议），随后重新加载结构化视图
window.rejectExecutionPlan = async function() {
  if (!curPlaza || !curDisc) return;
  toast('已驳回，议事长重新梳理计划…');
  await refreshPlan();
  loadExecutionPlan(true);
};

// 逐步骤追问：人↔Agent 对话锚定到具体步骤（复用讨论插话通道）
window.askPlanStep = async function(stepId, stepTitle) {
  if (!curPlaza || !curDisc) return;
  const q = window.prompt(`就步骤「${stepTitle || stepId}」向议事长/团队追问：`);
  if (!q || !q.trim()) return;
  const message = `【关于步骤 ${stepTitle || stepId}】${q.trim()}`;
  if (!evtSrc) appendMsg({ agent_name: '用户', niche_role: 'human', content: message });
  const r = await api(`${API}/plaza/${curPlaza}/discussions/${curDisc}/interject`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message }),
  });
  if (r) {
    if (!evtSrc) {
      if (r.moderator_reply) appendMsg(r.moderator_reply);
      if (r.nominated_reply) appendMsg(r.nominated_reply);
    }
    toast('已就该步骤追问');
  } else toast('追问失败');
};

/* ═══════════ SSE ═══════════ */
let _discEndTimer = null;
function teardownSSE() {
  _sseClosedByUs = true;
  if (_sseRetryTimer) { clearTimeout(_sseRetryTimer); _sseRetryTimer = null; }
  if (evtSrc) { try { evtSrc.close(); } catch (_) {} evtSrc = null; }
}
function connectSSE(discId) {
  if (_discEndTimer) { clearTimeout(_discEndTimer); _discEndTimer = null; }
  teardownSSE();
  if (!curPlaza) return;
  _sseClosedByUs = false;
  evtSrc = new EventSource(`${API}/plaza/${curPlaza}/discussions/${discId}/stream`);
  evtSrc.onopen = () => { _sseRetryDelay = 1000; };
  evtSrc.onerror = () => {
    if (_sseClosedByUs) return;               // 主动关闭不重连
    $('status-text').textContent = '连接中断，重连中…';
    if (evtSrc) { try { evtSrc.close(); } catch (_) {} evtSrc = null; }
    _sseRetryTimer = setTimeout(() => {
      if (curDisc === discId && !_sseClosedByUs) connectSSE(discId);  // 仍在同一讨论才重连
    }, _sseRetryDelay);
    _sseRetryDelay = Math.min(_sseRetryDelay * 2, SSE_MAX_DELAY);   // 1s→2s→5s…上限 10s
  };
  evtSrc.onmessage = (e) => {
    try {
      const d = JSON.parse(e.data);
      if (d.type === 'heartbeat') return;
      if (d.type === 'status') return;
      if (d.type === 'message') {
        const m = d.message, log = $('msg-log');
        if (_seenMsgKeys.has(msgKey(m))) return;  // 重放/重连去重（兼顾断点补漏，不重复插入）
        markMsgSeen(m);
        if (curDiscData) {
          const nextMessages = Array.isArray(curDiscData.messages) ? [...curDiscData.messages, m] : [m];
          curDiscData = {
            ...curDiscData,
            messages: nextMessages,
            current_round: Math.max(Number(curDiscData.current_round || 0), Number(m.round_number || 0)),
          };
        }
        if (log.querySelector('[style*="text-align:center"]')) log.innerHTML = '';
        const isMod = m.niche_role === 'moderator';
        const isUser = m.niche_role === 'human';
        const lastSep = log.querySelector('.round-sep:last-of-type');
        const lastR = lastSep ? parseInt(lastSep.textContent.match(/\d+/)?.[0] || 0) : -1;
        if (m.round_number > 0 && m.round_number !== lastR) log.insertAdjacentHTML('beforeend', `<div class="round-sep">ROUND ${m.round_number}</div>`);
        const cls = isMod ? 'mod' : (isUser ? 'user' : '');
        const label = isMod ? ' · 议事长' : (isUser ? ' · 你' : '');
        const modAction = isMod ? `<div style="margin-top:6px;text-align:right"><button class="plan-btn" onclick="refreshPlan()" style="font-size:11px;padding:2px 10px">↻ 修订执行计划</button></div>` : '';
        log.insertAdjacentHTML('beforeend', `<div class="msg-entry ${cls}"><div class="me-name">${esc(m.agent_name)}${label}</div><div class="me-text">${mdLite(m.content)}</div>${modAction}</div>`);
        log.scrollTop = log.scrollHeight;
        $('status-text').textContent = `R${m.round_number} · ${m.agent_name}`;
        if (!isUser) showSpeechBubble(m.agent_id, m.agent_name, m.content);
        scheduleDiscussionSignalRefresh(2000);
      }
      if (d.type === 'interjection_state') {
        $('status-text').textContent = d.state === 'paused' ? '纠偏中…' : '讨论继续';
        if (d.state === 'resumed') {
          // 议事长回复结束，显示操作按钮
          const lastUserMsg = [...$('msg-log').querySelectorAll('.msg-entry.user .me-text')].pop();
          const question = lastUserMsg ? lastUserMsg.textContent.trim() : '';
          if (question) appendModeratorActions(question);
        }
      }
      if (d.type === 'plan_updated' && d.plan) {
        if (curDiscData) curDiscData = { ...curDiscData, plan: d.plan };
        renderLivePlan(d.plan);
        scheduleDiscussionSignalRefresh(200);
      }
      if (d.type === 'verification_state_updated') {
        curVerificationState = normalizeVerificationState(d);
        renderVerificationState();
        const label = curVerificationState.alert_count
          ? `VERIFY · ${curVerificationState.alert_count} ALERT`
          : `VERIFY · ${curVerificationState.queue_count || 0} ITEM`;
        $('status-text').textContent = label;
        if (d.trigger === 'verification_queue_run') {
          toast(`验证队列已更新 · 告警 ${curVerificationState.alert_count} 项`);
        } else if (d.trigger === 'task_finalized') {
          toast(`任务执行结果已同步到验证队列`);
        } else if (d.trigger === 'discussion_evolved') {
          toast(`演进项已进入验证队列`);
        }
        scheduleDiscussionSignalRefresh(300);
      }
      if (d.type === 'discussion_start') { clearSpeechPlayback(); _seenMsgKeys.clear(); $('btn-start').disabled = true; $('btn-start').textContent = '进行中'; $('msg-log').innerHTML = ''; }
      if (d.type === 'round_start') $('status-text').textContent = `R${d.round}/${d.max_rounds}`;
      if (d.type === 'summarizing') { $('btn-start').textContent = '总结中'; $('status-text').textContent = '议事长总结中…'; }
      if (d.type === 'discussion_end') {
        $('btn-start').disabled = false; $('btn-start').textContent = '重新讨论'; $('status-text').textContent = 'DONE';
        teardownSSE();
        scheduleDiscussionSignalRefresh(200);
        const refreshDelay = Math.max(2600, Math.min(120000, 1500 + getQueuedSpeechDuration()));
        _discEndTimer = setTimeout(() => { _discEndTimer = null; selectDisc(discId, { keepSpeech: true }); }, refreshDelay);
      }
    } catch (err) { console.warn('SSE parse:', err); }
  };
}

/* ═══════════ INIT ═══════════ */
async function init() {
  try {
    allTeams = await api(`${API}/teams`) || [];
    const plazas = await loadPlazas(); renderArena3D([]);
    const savedPlaza = localStorage.getItem('plaza_curPlaza');
    const savedDisc = localStorage.getItem('plaza_curDisc');
    const initialPlaza = [deepLinkPlazaId, savedPlaza].find(id => id && plazas.some(p => p.id === id)) || '';
    const initialDisc = (deepLinkDiscussionId && deepLinkPlazaId && deepLinkPlazaId === initialPlaza)
      ? deepLinkDiscussionId
      : (savedDisc || '');
    if (!initialPlaza && (deepLinkPlazaId || savedPlaza)) {
      stripQueryParams(['plaza_id', 'discussion_id']);
      localStorage.removeItem('plaza_curPlaza');
      localStorage.removeItem('plaza_curDisc');
    }
    if (initialPlaza) {
      const ok = await selectPlaza(initialPlaza);
      if (ok && initialDisc) await selectDisc(initialDisc);
    }
  } catch(e) {
    console.error('[Plaza] init failed:', e);
    toast('初始化失败，请刷新或检查后端服务');
  }
}
init();

// 页面离开时关闭 SSE，避免悬挂连接与重连计时器
window.addEventListener('beforeunload', () => { teardownSSE(); });

// plan-panel 滚动/触摸时标记 busy，阻止重渲染闪烁
['scroll', 'touchstart', 'mousedown', 'wheel'].forEach(evt => {
  document.addEventListener(evt, (e) => {
    if (e.target.closest && e.target.closest('#plan-panel')) {
      _markPlanPanelBusy();
    }
  }, { passive: true });
});
