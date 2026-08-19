/* Login hero: a lightweight, self-contained version of the existing digital-twin visual language. */
/* Ported from StockAgents login page; agent model reuses the plaza/office visual language (head halo, U-arc body, floor ring). */
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

const canvas = document.getElementById('login-agent-canvas');
const stage = canvas && canvas.closest('.agent-stage');
if (!canvas || !stage) throw new Error('login agent canvas missing');
const agentPalette = ['#22d3ee', '#34d399', '#a78bfa', '#fbbf24', '#f472b6', '#60a5fa'];
const paletteColor = agentPalette[Math.floor(Math.random() * agentPalette.length)];
document.documentElement.style.setProperty('--agent-accent', paletteColor);

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x07131d);
scene.fog = new THREE.FogExp2(0x07131d, 0.055);
const camera = new THREE.PerspectiveCamera(38, 1, 0.1, 100);
// 参考登录页构图：从右前方略微俯视，让智能体像是在看向右侧控制台。
camera.position.set(2.65, 2.05, 10.4);
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: false });
renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.15;
const controls = new OrbitControls(camera, canvas);
controls.enableDamping = true;
controls.dampingFactor = 0.07;
controls.enablePan = false;
// 右键拖动也用于旋转数字孪生；登录页不弹出浏览器上下文菜单。
controls.mouseButtons.RIGHT = THREE.MOUSE.PAN;
canvas.addEventListener('contextmenu', (event) => event.preventDefault());
let rightDrag = null;
// 登录首帧：逆时针 50°，并以当前构图的 1.5 倍主视觉比例进入页面。
let manualYaw = THREE.MathUtils.degToRad(50);
let manualPitch = 0;
let manualRoll = THREE.MathUtils.degToRad(20);
canvas.addEventListener('pointerdown', (event) => {
  if (event.button !== 2) return;
  event.preventDefault();
  event.stopPropagation();
  rightDrag = { x: event.clientX, y: event.clientY };
  canvas.setPointerCapture?.(event.pointerId);
});
canvas.addEventListener('pointermove', (event) => {
  if (!rightDrag) return;
  const dx = event.clientX - rightDrag.x;
  const dy = event.clientY - rightDrag.y;
  rightDrag = { x: event.clientX, y: event.clientY };
  manualYaw += dx * 0.012;
  manualPitch = Math.max(-0.42, Math.min(0.42, manualPitch + dy * 0.008));
});
const stopRightDrag = (event) => {
  if (!rightDrag) return;
  rightDrag = null;
  canvas.releasePointerCapture?.(event.pointerId);
};
canvas.addEventListener('pointerup', stopRightDrag);
canvas.addEventListener('pointercancel', stopRightDrag);
controls.minDistance = 5.3;
controls.maxDistance = 12;
controls.target.set(-0.95, 0.82, 0);

scene.add(new THREE.AmbientLight(0x8bc9dc, 0.52));
const key = new THREE.DirectionalLight(0xa8f0ff, 1.6); key.position.set(3, 5, 5); scene.add(key);
const rim = new THREE.PointLight(0x1eb6df, 4.5, 12); rim.position.set(-4, 2, 2); scene.add(rim);
const violet = new THREE.PointLight(0x6955ff, 2.2, 10); violet.position.set(4, 0, -2); scene.add(violet);

const agent = new THREE.Group();
agent.position.set(-2.05, -1.65, 0);
agent.scale.setScalar(1.92);
scene.add(agent);

// Reuse the product's established plaza/office agent: a restrained head halo,
// U-arc body and floor ring. It stays legible at hero scale without becoming a
// bulky humanoid mascot.
const agentColor = new THREE.Color(paletteColor);
const outlineMat = new THREE.MeshBasicMaterial({ color: agentColor, transparent: true, opacity: 0.86, side: THREE.DoubleSide });
const glowMat = new THREE.MeshBasicMaterial({ color: agentColor, transparent: true, opacity: 0.16, side: THREE.DoubleSide });
const head = new THREE.Mesh(new THREE.TorusGeometry(0.7, 0.055, 12, 48), outlineMat); head.position.y = 2.72; agent.add(head);
const headGlow = new THREE.Mesh(new THREE.TorusGeometry(0.7, 0.18, 12, 48), glowMat); headGlow.position.copy(head.position); agent.add(headGlow);
const arcPoints = [];
for (let i = 0; i <= 40; i += 1) { const a = Math.PI * (i / 40); arcPoints.push(new THREE.Vector3(-Math.cos(a) * 0.98, 1.72 - Math.sin(a) * 1.12, 0)); }
const bodyCurve = new THREE.CatmullRomCurve3(arcPoints);
agent.add(new THREE.Mesh(new THREE.TubeGeometry(bodyCurve, 40, 0.07, 8, false), outlineMat));
agent.add(new THREE.Mesh(new THREE.TubeGeometry(bodyCurve, 40, 0.23, 8, false), glowMat));
const platformRing = new THREE.Mesh(new THREE.RingGeometry(0.7, 1.08, 48), new THREE.MeshBasicMaterial({ color: agentColor, transparent: true, opacity: 0.28, side: THREE.DoubleSide }));
platformRing.rotation.x = -Math.PI / 2; platformRing.position.y = 0.02; agent.add(platformRing);

const stars = new THREE.BufferGeometry();
const positions = new Float32Array(420 * 3);
for (let i = 0; i < 420; i += 1) { positions[i * 3] = (Math.random() - 0.5) * 18; positions[i * 3 + 1] = Math.random() * 9 - 3; positions[i * 3 + 2] = (Math.random() - 0.5) * 12 - 2; }
stars.setAttribute('position', new THREE.BufferAttribute(positions, 3));
scene.add(new THREE.Points(stars, new THREE.PointsMaterial({ color: 0x8adbea, size: 0.025, transparent: true, opacity: 0.56 })));

function resize() { const w = stage.clientWidth || 640; const h = stage.clientHeight || 360; camera.aspect = w / h; camera.updateProjectionMatrix(); renderer.setSize(w, h, false); }
new ResizeObserver(resize).observe(stage); resize();
const clock = new THREE.Clock();
function animate() {
  const t = clock.getElapsedTime();
  agent.rotation.y = manualYaw + Math.sin(t * 0.22) * 0.16;
  agent.rotation.x = manualPitch;
  agent.rotation.z = manualRoll;
  head.rotation.z = t * 0.4; headGlow.rotation.z = -t * 0.22;
  platformRing.rotation.z = -t * 0.18;
  agent.position.y = -1.65 + Math.sin(t * 1.1) * 0.045;
  controls.update(); renderer.render(scene, camera); requestAnimationFrame(animate);
}
animate();
