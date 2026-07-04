/**
 * office-scene.js — Marvis 风格极简白办公室 (P7 v3)
 * v3: OrbitControls 交互 / 4列工位+中央共享区(玻璃护栏) / 背后屋顶视角 /
 *     Agent 落座椅子 / 猫定时巡逻 / Agent 递文件动画(数据传递可视化)。
 * 渲染 = OfficeState 的投影；本模块不持有业务状态。
 */
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

const C = {
  bg: 0xf4f5f6, floor: 0xffffff, furniture: 0xf7f7f8,
  agent: 0x1c1c1e,
  // IT 界蓝屏 = 故障；屏幕一律黑色系（开机=深灰微亮，关机=纯黑）
  screenOn: 0x16171b, screenOff: 0x0a0a0c,
};

// 4 列工位，列间距加宽，中央留共享区走廊（x ∈ [-2.9, 2.9]）
const COL_X = [-12.0, -6.2, 6.2, 12.0];
const ROW_Z0 = -7, ROW_DZ = 4.2;

export function createOfficeScene(canvas, container) {
  const W = container.clientWidth || 800, H = container.clientHeight || 600;
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(C.bg);

  // 视角: 智能体背后 + 屋顶俯视（参考图），OrbitControls 可拖拽/缩放/平移
  const aspect = W / H, frustum = 15;
  const camera = new THREE.OrthographicCamera(-frustum * aspect, frustum * aspect, frustum, -frustum, 0.1, 300);
  camera.position.set(0, 24, 30);
  camera.lookAt(0, 0, -2);

  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
  renderer.setSize(W, H);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;

  const controls = new OrbitControls(camera, renderer.domElement);
  controls.target.set(0, 0, -2);
  controls.enableDamping = true;
  controls.dampingFactor = 0.08;
  controls.minZoom = 0.5; controls.maxZoom = 3.5;
  controls.maxPolarAngle = Math.PI / 2.15;   // 不许钻到地板下面
  controls.update();

  // 白底光照: 环境光抬高、直射光降低 → 阴影浅而柔（shadow.radius 大半径软化）
  scene.add(new THREE.AmbientLight(0xffffff, 1.45));
  const sun = new THREE.DirectionalLight(0xffffff, 0.85);
  sun.position.set(14, 30, 12);
  sun.castShadow = true;
  sun.shadow.mapSize.set(2048, 2048);
  sun.shadow.radius = 8;
  sun.shadow.bias = -0.0004;
  const sc = sun.shadow.camera; sc.left = -30; sc.right = 30; sc.top = 30; sc.bottom = -30;
  scene.add(sun);

  const floor = new THREE.Mesh(
    new THREE.PlaneGeometry(70, 70),
    new THREE.MeshStandardMaterial({ color: C.floor, roughness: 0.95 })
  );
  floor.rotation.x = -Math.PI / 2; floor.receiveShadow = true;
  scene.add(floor);

  const props = new THREE.Group(); scene.add(props);
  const agentsGroup = new THREE.Group(); scene.add(agentsGroup);
  const edgesGroup = new THREE.Group(); scene.add(edgesGroup);

  const furnMat = () => new THREE.MeshStandardMaterial({ color: C.furniture, roughness: 0.9 });
  function box(w, h, d, x, y, z, mat, parent) {
    const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), mat || furnMat());
    m.position.set(x, y, z); m.castShadow = true; m.receiveShadow = true;
    (parent || props).add(m); return m;
  }

  // ── 工位: 屏幕朝 -z（Agent 背对摄像机，与参考图一致） ──
  function buildDesk(x, z) {
    const g = new THREE.Group(); g.position.set(x, 0, z);
    box(3.0, 0.16, 1.6, 0, 1.5, 0, null, g);
    [[-1.35, 0.7], [1.35, 0.7], [-1.35, -0.7], [1.35, -0.7]].forEach(([lx, lz]) =>
      box(0.12, 1.5, 0.12, lx, 0.75, lz, null, g));
    box(0.24, 0.5, 0.06, 0, 2.1, -0.45, null, g);
    const screen = box(1.5, 0.9, 0.07, 0, 2.5, -0.45,
      new THREE.MeshStandardMaterial({ color: C.screenOff, emissive: C.screenOff, emissiveIntensity: 0.4 }), g);
    // 办公椅: 座面+靠背+滚轮底座，Agent 坐在座面上
    box(1.0, 0.14, 1.0, 0, 0.9, 1.55, null, g);            // 座面 (顶面 y≈0.97)
    box(1.0, 1.0, 0.12, 0, 1.5, 2.05, null, g);            // 靠背
    box(0.14, 0.9, 0.14, 0, 0.45, 1.55, null, g);          // 支柱
    props.add(g);
    return {
      group: g, screen,
      seat: new THREE.Vector3(x, 0.97, z + 1.55),          // 座面高度 —— 不再坐地上
      aside: new THREE.Vector3(x + 1.6, 0, z + 1.2),
    };
  }

  // ── 白板讨论角（后方中央，面向工位区） ──
  const boardTex = makeBoardTexture([]);
  function buildWhiteboard() {
    const g = new THREE.Group(); g.position.set(0, 0, -13);
    box(0.16, 3.4, 0.16, -2.4, 1.7, 0, null, g);
    box(0.16, 3.4, 0.16, 2.4, 1.7, 0, null, g);
    const board = new THREE.Mesh(
      new THREE.BoxGeometry(5.2, 2.8, 0.1),
      new THREE.MeshStandardMaterial({ map: boardTex.texture, roughness: 0.6 })
    );
    board.position.set(0, 2.3, 0); board.castShadow = true; g.add(board);
    props.add(g);
    return { anchor: new THREE.Vector3(0, 0, -10.8) };
  }
  function makeBoardTexture(lines) {
    const cv = document.createElement('canvas'); cv.width = 512; cv.height = 300;
    const ctx = cv.getContext('2d');
    const texture = new THREE.CanvasTexture(cv);
    function draw(ls) {
      ctx.fillStyle = '#ffffff'; ctx.fillRect(0, 0, 512, 300);
      ctx.fillStyle = '#3b4048'; ctx.font = '22px sans-serif';
      ctx.fillText('执 行 计 划', 20, 36);
      ctx.strokeStyle = '#d5d9de'; ctx.beginPath(); ctx.moveTo(20, 48); ctx.lineTo(492, 48); ctx.stroke();
      ctx.font = '17px sans-serif';
      (ls || []).slice(-8).forEach((l, i) => ctx.fillText('· ' + l, 24, 80 + i * 27));
      texture.needsUpdate = true;
    }
    draw(lines);
    return { texture, draw };
  }

  // ── 中央共享区: 咖啡机 / 跑步机 / 马桶 一字排开，左右玻璃护栏 ──
  function buildSharedZone() {
    // 咖啡吧（共享区三件套沿走廊前后均匀分布: -6.5 / +0.5 / +7）
    const bar = new THREE.Group(); bar.position.set(0, 0, -6.5);
    box(3.6, 1.1, 1.3, 0, 0.55, 0, null, bar);
    box(0.7, 0.55, 0.55, 1.0, 1.4, 0, new THREE.MeshStandardMaterial({ color: 0xdddfe3 }), bar);
    for (let i = 0; i < 5; i++) {
      const cup = new THREE.Mesh(new THREE.CylinderGeometry(0.09, 0.07, 0.16, 10),
        new THREE.MeshStandardMaterial({ color: 0xb07040 }));
      cup.position.set(-1.4 + i * 0.4, 1.2, 0.2); cup.castShadow = true; bar.add(cup);
    }
    props.add(bar);
    // 跑步机: 左右两侧扶手（立柱 + 横杆），不是中间一根
    const tm = new THREE.Group(); tm.position.set(0, 0, 4);
    box(2.4, 0.24, 1.2, 0, 0.14, 0, new THREE.MeshStandardMaterial({ color: 0xe9ebee, roughness: 0.8 }), tm);
    for (const s of [-1, 1]) {
      box(0.1, 1.4, 0.1, -1.05, 0.8, 0.5 * s, null, tm);        // 前立柱
      box(1.6, 0.08, 0.1, -0.35, 1.5, 0.5 * s, null, tm);       // 侧扶手横杆
    }
    box(0.9, 0.5, 0.08, -1.05, 1.35, 0, null, tm);              // 前方仪表板
    props.add(tm);
    // 马桶
    const wc = new THREE.Group(); wc.position.set(0, 0, 14);
    const wcMat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.35 });
    box(0.9, 0.5, 1.1, 0, 0.25, 0, wcMat, wc);
    const bowl = new THREE.Mesh(new THREE.CylinderGeometry(0.42, 0.34, 0.3, 16), wcMat);
    bowl.position.set(0, 0.62, 0.15); bowl.castShadow = true; wc.add(bowl);
    box(0.8, 0.9, 0.22, 0, 0.95, -0.42, wcMat, wc);
    props.add(wc);
    // 玻璃护栏 ×2（半透明，拦出共享走廊）
    const glassMat = new THREE.MeshStandardMaterial({
      color: 0xbfd8e8, transparent: true, opacity: 0.22, roughness: 0.1, side: THREE.DoubleSide,
    });
    for (const s of [-1, 1]) {
      const glass = new THREE.Mesh(new THREE.BoxGeometry(0.08, 1.3, 26), glassMat);
      glass.position.set(2.35 * s, 0.75, 4); props.add(glass);
      box(0.1, 0.08, 26, 2.35 * s, 1.45, 4,
        new THREE.MeshStandardMaterial({ color: 0xcfd4da }), props);   // 顶部扶手
    }
    // anchor=使用位, queueDir=排队方向（后到者沿此方向站成一列）
    return {
      coffee: { anchor: new THREE.Vector3(1.3, 0, -5.4), queueDir: new THREE.Vector3(0, 0, 1), y: 0 },
      treadmill: { anchor: new THREE.Vector3(0, 0.3, 4), queueDir: new THREE.Vector3(1.1, 0, 0.6).normalize(), y: 0.3 },
      toilet: { anchor: new THREE.Vector3(0, 0.55, 14.7), queueDir: new THREE.Vector3(0, 0, -1), y: 0.55 },
    };
  }

  // ── Agent 造型: 采用 plaza 的霓虹线框模型（光环头 + U弧身 + 地面光圈 + 名牌） ──
  function buildAgentFigure(def) {
    const g = new THREE.Group();
    // 白底适配: 主体线条加深加实（deep 色 + 高不透明度），辉光收敛避免发灰
    const col = new THREE.Color(def.collar);
    const deep = col.clone().multiplyScalar(0.72);
    const outlineMat = new THREE.MeshBasicMaterial({ color: deep, transparent: true, opacity: 0.95, side: THREE.DoubleSide });
    const glowMat = new THREE.MeshBasicMaterial({ color: col, transparent: true, opacity: 0.16, side: THREE.DoubleSide });
    // Head ring + glow
    const head = new THREE.Mesh(new THREE.TorusGeometry(0.34, 0.035, 12, 32), outlineMat);
    head.position.y = 2.0; g.add(head);
    const headGlow = new THREE.Mesh(new THREE.TorusGeometry(0.34, 0.14, 12, 32), glowMat);
    headGlow.position.copy(head.position); g.add(headGlow);
    // Body U-arc
    const pts = [];
    for (let i = 0; i <= 32; i++) {
      const a = Math.PI * (i / 32);
      pts.push(new THREE.Vector3(-Math.cos(a) * 0.48, 1.25 - Math.sin(a) * 0.65, 0));
    }
    const curve = new THREE.CatmullRomCurve3(pts);
    g.add(new THREE.Mesh(new THREE.TubeGeometry(curve, 32, 0.035, 8, false), outlineMat));
    g.add(new THREE.Mesh(new THREE.TubeGeometry(curve, 32, 0.12, 8, false), glowMat));
    // Ground glow ring
    const glowRing = new THREE.Mesh(
      new THREE.RingGeometry(0.35, 0.55, 32),
      new THREE.MeshBasicMaterial({ color: col, transparent: true, opacity: 0.22, side: THREE.DoubleSide })
    );
    glowRing.rotation.x = -Math.PI / 2; glowRing.position.y = 0.01; g.add(glowRing);
    // 手上的文件（递交数据时可见）
    const file = new THREE.Mesh(new THREE.BoxGeometry(0.34, 0.05, 0.46),
      new THREE.MeshStandardMaterial({ color: 0xfefefe, roughness: 0.6 }));
    file.position.set(0.5, 1.05, 0.28); file.visible = false; g.add(file);
    g.add(makeLabel(def.name));
    agentsGroup.add(g);
    return { group: g, file, head };
  }
  function disposeFigure(f) {
    f.group.traverse((node) => {
      if (node.geometry) node.geometry.dispose();
      const mats = Array.isArray(node.material) ? node.material : (node.material ? [node.material] : []);
      mats.forEach((m) => { if (m.map) m.map.dispose(); m.dispose(); });
    });
    agentsGroup.remove(f.group);
  }
  function makeLabel(text) {
    const cv = document.createElement('canvas'); cv.width = 256; cv.height = 64;
    const ctx = cv.getContext('2d');
    ctx.font = 'bold 30px sans-serif'; ctx.textAlign = 'center';
    ctx.fillStyle = '#2a2e34'; ctx.fillText(String(text).slice(0, 12), 128, 42);
    const sp = new THREE.Sprite(new THREE.SpriteMaterial({ map: new THREE.CanvasTexture(cv), transparent: true }));
    sp.scale.set(2.6, 0.65, 1); sp.position.y = 2.6;
    return sp;
  }

  // ── 猫: 固定巡逻路线 + 每个点位随机停留（先让它动起来） ──
  const CAT_ROUTE = [
    [12, 10], [12, -4], [6, -9], [0, -11], [-6, -9], [-12, -4], [-12, 10], [-4, 13], [4, 13],
  ];
  function buildCat() {
    const g = new THREE.Group();
    const mat = new THREE.MeshStandardMaterial({ color: 0xf2f2f2, roughness: 0.8 });
    box(0.55, 0.3, 0.28, 0, 0.22, 0, mat, g);
    box(0.3, 0.26, 0.26, 0.36, 0.42, 0, mat, g);
    for (const s of [-1, 1]) box(0.08, 0.14, 0.06, 0.36 + 0.06 * s, 0.62, 0.09 * s, mat, g);
    const tail = box(0.08, 0.4, 0.08, -0.34, 0.44, 0, mat, g);
    tail.rotation.z = 0.5;
    g.position.set(CAT_ROUTE[0][0], 0, CAT_ROUTE[0][1]);
    scene.add(g);
    return { group: g, tail, waypoint: 1, dwell: 0, speed: 1.6 };
  }

  // ── 装配 ──
  const desks = [];
  const whiteboard = buildWhiteboard();
  const shared = buildSharedZone();
  const cat = buildCat();

  function deskFor(index) {
    while (desks.length <= index) {
      const i = desks.length, col = i % 4, row = Math.floor(i / 4);
      desks.push(buildDesk(COL_X[col], ROW_Z0 + row * ROW_DZ));
    }
    return desks[index];
  }

  // ── 状态投影 ──
  const figures = {};       // id -> {group, file, target, baseY, def, courier}
  const edgeMeshes = new Map();
  const processedEdges = new Set();
  let mirrorOn = false;

  function targetFor(agent, idxInMeeting, meetingCount, facilities) {
    if (agent.activity === 'meeting') {
      const n = Math.max(meetingCount, 1), a = whiteboard.anchor;
      const ang = -0.7 + (idxInMeeting / Math.max(n - 1, 1)) * 1.4;
      return { pos: new THREE.Vector3(a.x + Math.sin(ang) * 2.6, 0, a.z + Math.cos(ang) * 2.2), y: 0 };
    }
    const fac = shared[agent.activity];
    if (fac) {
      // 设施位: 占用者在使用位；排队者沿 queueDir 站成 FIFO 一列（间距 1.0）
      const fs = facilities && facilities[agent.activity];
      if (fs && fs.occupant === agent.id) return { pos: fac.anchor.clone(), y: fac.y };
      const qi = fs ? fs.queue.indexOf(agent.id) : -1;
      const slot = qi >= 0 ? qi + 1 : 1;
      return {
        pos: fac.anchor.clone().add(fac.queueDir.clone().multiplyScalar(1.0 + slot * 1.0)).setY(0),
        y: 0,
      };
    }
    const d = deskFor(agent.deskIndex);
    if (agent.activity === 'working') return { pos: d.seat.clone().setY(0), y: 0.97 };  // 坐椅面
    return { pos: d.aside.clone(), y: 0 };
  }

  function applyState(state) {
    const meetingIds = Object.values(state.agents)
      .filter((a) => a.activity === 'meeting').map((a) => a.id);
    for (const agent of Object.values(state.agents)) {
      let f = figures[agent.id];
      if (!f) {
        const built = buildAgentFigure(agent);
        f = figures[agent.id] = {
          group: built.group, file: built.file,
          target: new THREE.Vector3(), baseY: 0, def: agent, courier: null,
        };
        const t = targetFor(agent, 0, 1, state.facilities);
        f.group.position.copy(t.pos); f.baseY = t.y;
      }
      f.def = agent;
      const t = targetFor(agent, Math.max(meetingIds.indexOf(agent.id), 0), meetingIds.length, state.facilities);
      f.target.copy(t.pos); f.baseY = t.y;
      const desk = deskFor(agent.deskIndex);
      const on = agent.activity === 'working';
      desk.screen.material.color.setHex(on ? C.screenOn : C.screenOff);
      desk.screen.material.emissive.setHex(on ? C.screenOn : C.screenOff);
      desk.screen.material.emissiveIntensity = on ? 0.9 : 0.3;
    }
    // 花名册收窄（团队/成员筛选）→ 移除不在编的 Agent 并释放资源
    for (const id of Object.keys(figures)) {
      if (!state.agents[id]) {
        disposeFigure(figures[id]);
        delete figures[id];
      }
    }
    // 桌子随编制收缩: 拆除多余空桌（幽灵清退后不留一片空工位）
    const neededDesks = Object.values(state.agents)
      .reduce((m, a) => Math.max(m, a.deskIndex + 1), 0);
    while (desks.length > Math.max(neededDesks, 1)) {
      const d = desks.pop();
      props.remove(d.group);
      d.group.traverse((o) => {
        if (o.geometry) o.geometry.dispose();
        const mats = Array.isArray(o.material) ? o.material : (o.material ? [o.material] : []);
        mats.forEach((m) => { if (m.map) m.map.dispose(); m.dispose(); });
      });
    }
    // 新协作边 → 递文件动画任务（Agent 拿文件走到下游工位交接）
    for (const e of state.edges) {
      const key = e.from + '|' + e.to + '|' + Math.ceil(e.ttl);
      const routeKey = e.from + '|' + e.to;
      if (processedEdges.has(routeKey)) continue;
      const fa = figures[e.from], fb = figures[e.to];
      if (fa && fb && !fa.courier) {
        processedEdges.add(routeKey);
        setTimeout(() => processedEdges.delete(routeKey), 8000);   // 同一对 8s 内不重复跑腿
        fa.courier = { phase: 'go', toId: e.to, kind: e.kind };
        fa.file.visible = true;
      }
      void key;
    }
    // 协作轨迹线（历史热度的空间痕迹）
    const seen = new Set();
    for (const e of state.edges) {
      const key = e.from + '|' + e.to + '|' + e.kind;
      seen.add(key);
      const fa = figures[e.from], fb = figures[e.to];
      if (!fa || !fb) continue;
      let mesh = edgeMeshes.get(key);
      const p0 = fa.group.position.clone().setY(1.8);
      const p2 = fb.group.position.clone().setY(1.8);
      const mid = p0.clone().add(p2).multiplyScalar(0.5).setY(3.6);
      const curve = new THREE.QuadraticBezierCurve3(p0, mid, p2);
      if (!mesh) {
        mesh = new THREE.Mesh(
          new THREE.TubeGeometry(curve, 20, 0.045, 6, false),
          new THREE.MeshBasicMaterial({
            color: e.kind === 'help' ? 0x2bb8a8 : 0x4d9de0, transparent: true, opacity: 0.8,
          })
        );
        edgesGroup.add(mesh); edgeMeshes.set(key, mesh);
      } else {
        mesh.geometry.dispose();
        mesh.geometry = new THREE.TubeGeometry(curve, 20, 0.045, 6, false);
      }
      mesh.material.opacity = Math.max(e.ttl / 6, 0.1) * 0.8;
    }
    for (const [key, mesh] of edgeMeshes) {
      if (!seen.has(key)) {
        edgesGroup.remove(mesh); mesh.geometry.dispose(); mesh.material.dispose();
        edgeMeshes.delete(key);
      }
    }
    boardTex.draw(state.meeting.boardLines);
    if (state.mirror !== mirrorOn) {
      mirrorOn = state.mirror;
      // 镜像层视觉: 蓝图幽灵化（半透明 + 蓝调），形状可读，区分度靠色调与徽标
      const tint = new THREE.Color(0x9fb8d8);
      props.traverse((o) => {
        if (!o.isMesh) return;
        const m = o.material;
        if (mirrorOn) {
          o.userData._mirrorBak = {
            color: m.color.getHex(), transparent: m.transparent, opacity: m.opacity,
          };
          m.transparent = true;
          m.opacity = Math.min(m.opacity, 0.42);
          m.color.lerp(tint, 0.5);
        } else if (o.userData._mirrorBak) {
          const b = o.userData._mirrorBak;
          m.color.setHex(b.color);
          m.transparent = b.transparent;
          m.opacity = b.opacity;
          delete o.userData._mirrorBak;
        }
      });
      floor.material.color.setHex(mirrorOn ? 0xeef2f8 : C.floor);
      scene.background.setHex(mirrorOn ? 0xe8edf5 : C.bg);
    }
  }

  // ── 动画循环 ──
  const clock = new THREE.Clock();
  let disposed = false;
  const _v = new THREE.Vector3();

  function stepCourier(f, dt, t) {
    const c = f.courier;
    const to = figures[c.toId];
    if (!to) { f.courier = null; f.file.visible = false; return; }
    if (c.phase === 'go') {
      _v.copy(to.group.position).setY(0);
      _v.add(new THREE.Vector3(1.1, 0, 0.6));                 // 站到对方工位旁
      const cur = f.group.position;
      const dir = _v.clone().sub(cur).setY(0);
      if (dir.length() < 0.25) { c.phase = 'handover'; c.wait = 0.9; return; }
      dir.normalize().multiplyScalar(3.2 * dt);
      cur.add(dir);
      cur.y = Math.abs(Math.sin(t * 10)) * 0.08;              // 走路颠簸
      f.group.lookAt(_v.x, cur.y, _v.z);
      return;
    }
    if (c.phase === 'handover') {
      c.wait -= dt;
      if (c.wait <= 0) {
        f.file.visible = false;
        to.file.visible = true;                               // 文件交到对方手上
        setTimeout(() => { to.file.visible = false; }, 1500); // 对方收好文件
        c.phase = 'return';
      }
      return;
    }
    // return: 回自己的位置
    const back = f.target;
    const cur = f.group.position;
    const dir = back.clone().sub(cur).setY(0);
    if (dir.length() < 0.3) { f.courier = null; return; }
    dir.normalize().multiplyScalar(3.2 * dt);
    cur.add(dir); cur.y = 0;
    f.group.lookAt(back.x, 0, back.z);
  }

  function animate() {
    if (disposed) return;
    requestAnimationFrame(animate);
    const dt = Math.min(clock.getDelta(), 0.05);
    const t = clock.getElapsedTime();
    for (const f of Object.values(figures)) {
      if (f.courier) { stepCourier(f, dt, t); continue; }
      // 常规: 平滑走向目标 + 落座高度 + 轻微呼吸/跑步颠簸
      const act = f.def.activity;
      let bob = Math.sin(t * 2 + f.def.deskIndex) * 0.03;
      if (act === 'treadmill') bob = Math.abs(Math.sin(t * 8)) * 0.18;
      if (act === 'meeting' && f.def.id === (window.OfficeAPI && window.OfficeAPI._speakerId)) {
        bob = Math.abs(Math.sin(t * 6)) * 0.12;
      }
      _v.copy(f.target).setY(f.baseY + bob);
      f.group.position.lerp(_v, 0.06);
      if (act === 'working') f.group.lookAt(f.group.position.x, f.group.position.y, f.group.position.z - 4); // 面朝屏幕(-z)
    }
    // 猫巡逻: 头部引导转向——先转身对准目标，再沿自身朝向前进（不平移漂移）
    if (cat.dwell > 0) {
      cat.dwell -= dt;
      cat.tail.rotation.z = 0.5 + Math.sin(t * 3) * 0.3;      // 停下时甩尾巴
    } else {
      const [wx, wz] = CAT_ROUTE[cat.waypoint];
      const dx = wx - cat.group.position.x, dz = wz - cat.group.position.z;
      const dist = Math.hypot(dx, dz);
      if (dist < 0.35) {
        cat.waypoint = (cat.waypoint + 1) % CAT_ROUTE.length;
        cat.dwell = 1.5 + Math.random() * 3.5;
      } else {
        // 模型头朝 +x，故朝向角 = atan2(dz 分量在 -z, ...)——用 atan2(-dz? ) 校准: lookAt 等效角
        const desired = Math.atan2(dx, dz) - Math.PI / 2;      // 身体 +x 对准移动方向
        let diff = desired - cat.group.rotation.y;
        while (diff > Math.PI) diff -= Math.PI * 2;
        while (diff < -Math.PI) diff += Math.PI * 2;
        const turn = Math.max(-3.2 * dt, Math.min(3.2 * dt, diff));
        cat.group.rotation.y += turn;
        // 只有大致对准了才迈步；转身时几乎原地（前进量随夹角衰减）
        const align = Math.max(0, 1 - Math.abs(diff) / 0.9);
        if (align > 0) {
          const heading = cat.group.rotation.y + Math.PI / 2;   // 还原为世界方向角
          cat.group.position.x += Math.sin(heading) * cat.speed * dt * align;
          cat.group.position.z += Math.cos(heading) * cat.speed * dt * align;
          cat.group.position.y = Math.abs(Math.sin(t * 9)) * 0.05 * align;
        }
      }
    }
    controls.update();
    renderer.render(scene, camera);
  }
  animate();

  const resizeObs = new ResizeObserver(() => {
    const w = container.clientWidth, h = container.clientHeight;
    if (!w || !h) return;
    const asp = w / h;
    camera.left = -frustum * asp; camera.right = frustum * asp;
    camera.updateProjectionMatrix();
    renderer.setSize(w, h);
  });
  resizeObs.observe(container);

  return {
    applyState,
    dispose() {
      disposed = true; resizeObs.disconnect(); controls.dispose();
      renderer.dispose();
    },
  };
}
