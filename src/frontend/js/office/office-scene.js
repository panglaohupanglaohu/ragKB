/**
 * office-scene.js — Marvis 风格极简白办公室 (P7-1/P7-2 首版)
 * 一个场景承载: 工位网格 / 白板讨论角 / 跑步机 / 茶水吧 / 协作光线 / 镜像层 / 猫。
 * 渲染 = OfficeState 的投影；本模块不持有业务状态。
 * 设计: docs/unified-office-3d-design.md
 */
import * as THREE from 'three';

const C = {
  bg: 0xf4f5f6, floor: 0xffffff, furniture: 0xf7f7f8, furnitureEdge: 0xe4e6e8,
  agent: 0x1c1c1e, screenOn: 0x3d8bff, screenOff: 0x15161a, line: 0x8f97a3,
};

export function createOfficeScene(canvas, container) {
  const W = container.clientWidth || 800, H = container.clientHeight || 600;
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(C.bg);

  // 等轴测感: 正交相机
  const aspect = W / H, frustum = 16;
  const camera = new THREE.OrthographicCamera(-frustum * aspect, frustum * aspect, frustum, -frustum, 0.1, 200);
  camera.position.set(20, 20, 20);
  camera.lookAt(0, 0, 0);

  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
  renderer.setSize(W, H);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;

  scene.add(new THREE.AmbientLight(0xffffff, 1.15));
  const sun = new THREE.DirectionalLight(0xffffff, 1.3);
  sun.position.set(14, 26, 10);
  sun.castShadow = true;
  sun.shadow.mapSize.set(2048, 2048);
  const sc = sun.shadow.camera; sc.left = -24; sc.right = 24; sc.top = 24; sc.bottom = -24;
  scene.add(sun);

  const floor = new THREE.Mesh(
    new THREE.PlaneGeometry(60, 60),
    new THREE.MeshStandardMaterial({ color: C.floor, roughness: 0.95 })
  );
  floor.rotation.x = -Math.PI / 2; floor.receiveShadow = true;
  scene.add(floor);

  const props = new THREE.Group(); scene.add(props);       // 家具（镜像层线框化对象）
  const agentsGroup = new THREE.Group(); scene.add(agentsGroup);
  const edgesGroup = new THREE.Group(); scene.add(edgesGroup);

  // ── 家具工厂 ──
  const furnMat = () => new THREE.MeshStandardMaterial({ color: C.furniture, roughness: 0.9 });
  function box(w, h, d, x, y, z, mat, parent) {
    const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), mat || furnMat());
    m.position.set(x, y, z); m.castShadow = true; m.receiveShadow = true;
    (parent || props).add(m); return m;
  }

  function buildDesk(x, z) {
    const g = new THREE.Group(); g.position.set(x, 0, z);
    box(3.0, 0.16, 1.6, 0, 1.5, 0, null, g);                       // 桌面
    [[-1.35, 0.7], [1.35, 0.7], [-1.35, -0.7], [1.35, -0.7]].forEach(([lx, lz]) =>
      box(0.12, 1.5, 0.12, lx, 0.75, lz, null, g));                 // 桌腿
    box(0.24, 0.5, 0.06, 0, 2.1, -0.45, null, g);                   // 屏幕支架
    const screen = box(1.5, 0.9, 0.07, 0, 2.5, -0.45,
      new THREE.MeshStandardMaterial({ color: C.screenOff, emissive: C.screenOff, emissiveIntensity: 0.4 }), g);
    box(1.0, 0.9, 1.0, 0, 0.45, 1.5, null, g);                      // 椅子
    props.add(g);
    return { group: g, screen, seat: new THREE.Vector3(x, 0, z + 1.5) };
  }

  // 白板讨论角（Plaza：无圆桌，站立会议）
  const boardTex = makeBoardTexture([]);
  function buildWhiteboard() {
    const g = new THREE.Group(); g.position.set(-11, 0, -4);
    box(0.16, 3.4, 0.16, -2.1, 1.7, 0, null, g);
    box(0.16, 3.4, 0.16, 2.1, 1.7, 0, null, g);
    const board = new THREE.Mesh(
      new THREE.BoxGeometry(4.6, 2.6, 0.1),
      new THREE.MeshStandardMaterial({ map: boardTex.texture, roughness: 0.6 })
    );
    board.position.set(0, 2.2, 0); board.castShadow = true; g.add(board);
    g.rotation.y = Math.PI / 3;
    props.add(g);
    return { group: g, anchor: new THREE.Vector3(-9.2, 0, -2.6) };
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

  // 跑步机（后台长任务）
  function buildTreadmill() {
    const g = new THREE.Group(); g.position.set(-11, 0, 3.5);
    box(2.4, 0.24, 1.2, 0, 0.14, 0, new THREE.MeshStandardMaterial({ color: 0xe9ebee, roughness: 0.8 }), g);
    box(0.14, 1.5, 0.9, -1.1, 0.9, 0, null, g);
    box(0.9, 0.1, 0.14, -0.72, 1.6, 0, null, g);
    g.rotation.y = Math.PI / 2.4;
    props.add(g);
    return { anchor: new THREE.Vector3(-11, 0.3, 3.5) };
  }

  // 茶水吧（等待/空闲）
  function buildCoffeeBar() {
    const g = new THREE.Group(); g.position.set(-10.5, 0, 9);
    box(4.2, 1.1, 1.4, 0, 0.55, 0, null, g);
    box(0.7, 0.55, 0.55, 1.2, 1.4, 0, new THREE.MeshStandardMaterial({ color: 0xdddfe3 }), g);
    for (let i = 0; i < 5; i++) {
      const cup = new THREE.Mesh(new THREE.CylinderGeometry(0.09, 0.07, 0.16, 10),
        new THREE.MeshStandardMaterial({ color: 0xb07040 }));
      cup.position.set(-1.6 + i * 0.42, 1.2, 0.2); cup.castShadow = true; g.add(cup);
    }
    props.add(g);
    return { anchor: new THREE.Vector3(-9.6, 0, 8.2) };
  }

  // ── Agent 造型: 深色小兽 + 项圈色 + 名牌（自有皮肤，替代 plaza 旧造型） ──
  function buildAgentFigure(def) {
    const g = new THREE.Group();
    const bodyMat = new THREE.MeshStandardMaterial({ color: C.agent, roughness: 0.55 });
    const body = new THREE.Mesh(new THREE.CapsuleGeometry(0.42, 0.5, 4, 12), bodyMat);
    body.position.y = 0.85; body.castShadow = true; g.add(body);
    const head = new THREE.Mesh(new THREE.SphereGeometry(0.4, 16, 12), bodyMat);
    head.position.y = 1.6; head.castShadow = true; g.add(head);
    for (const s of [-1, 1]) {                                   // 双角耳
      const ear = new THREE.Mesh(new THREE.ConeGeometry(0.13, 0.42, 8), bodyMat);
      ear.position.set(0.26 * s, 2.0, 0); ear.rotation.z = -0.5 * s; ear.castShadow = true; g.add(ear);
    }
    const collar = new THREE.Mesh(new THREE.TorusGeometry(0.35, 0.09, 8, 20),
      new THREE.MeshStandardMaterial({ color: def.collar, roughness: 0.4 }));
    collar.rotation.x = Math.PI / 2; collar.position.y = 1.22; g.add(collar);
    g.add(makeLabel(def.name));
    agentsGroup.add(g);
    return g;
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

  // 猫（Owner 钦点保留）: 自由漫游，无业务含义
  function buildCat() {
    const g = new THREE.Group();
    const mat = new THREE.MeshStandardMaterial({ color: 0xf2f2f2, roughness: 0.8 });
    box(0.55, 0.3, 0.28, 0, 0.22, 0, mat, g);
    const head = box(0.3, 0.26, 0.26, 0.36, 0.42, 0, mat, g);
    for (const s of [-1, 1]) box(0.08, 0.14, 0.06, 0.36 + 0.08 * s, 0.62, 0.08 * s, mat, g);
    const tail = box(0.08, 0.4, 0.08, -0.34, 0.44, 0, mat, g);
    tail.rotation.z = 0.5;
    g.position.set(6, 0, 8);
    scene.add(g);
    return { group: g, head, target: new THREE.Vector3(6, 0, 8), pause: 0 };
  }

  // 趣味角落: 马桶（参考图彩蛋——短暂离线的 Agent 在这里）
  function buildToiletCorner() {
    const g = new THREE.Group(); g.position.set(-10.5, 0, 14);
    const mat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.35 });
    box(0.9, 0.5, 1.1, 0, 0.25, 0, mat, g);                      // 底座
    const bowl = new THREE.Mesh(new THREE.CylinderGeometry(0.42, 0.34, 0.3, 16), mat);
    bowl.position.set(0, 0.62, 0.15); bowl.castShadow = true; g.add(bowl);
    box(0.8, 0.9, 0.22, 0, 0.95, -0.42, mat, g);                 // 水箱
    const paper = new THREE.Mesh(new THREE.CylinderGeometry(0.12, 0.12, 0.14, 12),
      new THREE.MeshStandardMaterial({ color: 0xf5f5f5 }));
    paper.rotation.z = Math.PI / 2; paper.position.set(0.8, 1.1, -0.3); g.add(paper);
    props.add(g);
    return { anchor: new THREE.Vector3(-9.4, 0, 13.4) };
  }

  // ── 布局装配 ──
  const desks = [];
  const whiteboard = buildWhiteboard();
  const treadmill = buildTreadmill();
  const coffeeBar = buildCoffeeBar();
  const toilet = buildToiletCorner();
  const cat = buildCat();

  function deskFor(index) {
    while (desks.length <= index) {
      const i = desks.length, col = i % 3, row = Math.floor(i / 3);
      desks.push(buildDesk(-1 + col * 4.6, -6 + row * 4.4));
    }
    return desks[index];
  }

  // ── 状态投影 ──
  const figures = {};   // agentId -> {group, target:Vector3, def}
  const edgeMeshes = new Map();
  let mirrorOn = false;

  function targetFor(agent, idxInMeeting, meetingCount) {
    if (agent.activity === 'meeting') {
      const n = Math.max(meetingCount, 1), a = whiteboard.anchor;
      const ang = -0.6 + (idxInMeeting / Math.max(n - 1, 1)) * 1.2;
      return new THREE.Vector3(a.x + Math.cos(ang) * 2.2, 0, a.z + Math.sin(ang) * 2.2 + 1.2);
    }
    if (agent.activity === 'treadmill') return treadmill.anchor.clone();
    if (agent.activity === 'coffee') {
      const j = agent.deskIndex % 4;
      if (j === 3) return toilet.anchor.clone();   // 趣味角: 部分离线 Agent 去马桶位
      return coffeeBar.anchor.clone().add(new THREE.Vector3(j * 0.9, 0, j * 0.4));
    }
    const d = deskFor(agent.deskIndex);
    if (agent.activity === 'working') return d.seat.clone();
    return d.seat.clone().add(new THREE.Vector3(1.2, 0, 1.2));   // idle: 桌旁
  }

  function applyState(state) {
    const meetingIds = Object.values(state.agents)
      .filter((a) => a.activity === 'meeting').map((a) => a.id);
    // Agent 增改
    for (const agent of Object.values(state.agents)) {
      let f = figures[agent.id];
      if (!f) {
        f = figures[agent.id] = { group: buildAgentFigure(agent), target: new THREE.Vector3(), def: agent };
        f.group.position.copy(targetFor(agent, 0, 1));
      }
      f.def = agent;
      f.target.copy(targetFor(agent, Math.max(meetingIds.indexOf(agent.id), 0), meetingIds.length));
      const desk = deskFor(agent.deskIndex);
      const on = agent.activity === 'working';
      desk.screen.material.color.setHex(on ? C.screenOn : C.screenOff);
      desk.screen.material.emissive.setHex(on ? C.screenOn : C.screenOff);
      desk.screen.material.emissiveIntensity = on ? 0.9 : 0.3;
    }
    // 协作光线（考察协作的可视化: 谁在帮谁/谁在沟通）
    const seen = new Set();
    for (const e of state.edges) {
      const key = e.from + '|' + e.to + '|' + e.kind;
      seen.add(key);
      const fa = figures[e.from], fb = figures[e.to];
      if (!fa || !fb) continue;
      let mesh = edgeMeshes.get(key);
      const p0 = fa.group.position.clone().setY(1.8);
      const p2 = fb.group.position.clone().setY(1.8);
      const mid = p0.clone().add(p2).multiplyScalar(0.5).setY(3.4);
      const curve = new THREE.QuadraticBezierCurve3(p0, mid, p2);
      if (!mesh) {
        mesh = new THREE.Mesh(
          new THREE.TubeGeometry(curve, 20, 0.05, 6, false),
          new THREE.MeshBasicMaterial({
            color: e.kind === 'help' ? 0x2bb8a8 : 0x4d9de0, transparent: true, opacity: 0.85,
          })
        );
        edgesGroup.add(mesh); edgeMeshes.set(key, mesh);
      } else {
        mesh.geometry.dispose();
        mesh.geometry = new THREE.TubeGeometry(curve, 20, 0.05, 6, false);
      }
      mesh.material.opacity = Math.max(e.ttl / 6, 0.12);
    }
    for (const [key, mesh] of edgeMeshes) {
      if (!seen.has(key)) {
        edgesGroup.remove(mesh); mesh.geometry.dispose(); mesh.material.dispose();
        edgeMeshes.delete(key);
      }
    }
    // 白板
    boardTex.draw(state.meeting.boardLines);
    // 镜像层（孪生进行中）: 家具线框化 — 生产/仿真必须肉眼可分
    if (state.mirror !== mirrorOn) {
      mirrorOn = state.mirror;
      props.traverse((o) => { if (o.isMesh) o.material.wireframe = mirrorOn; });
      floor.material.color.setHex(mirrorOn ? 0xeef2f8 : C.floor);
      scene.background.setHex(mirrorOn ? 0xe8edf5 : C.bg);
    }
  }

  // ── 动画循环 ──
  const clock = new THREE.Clock();
  let disposed = false;
  function animate() {
    if (disposed) return;
    requestAnimationFrame(animate);
    const t = clock.getElapsedTime();
    for (const f of Object.values(figures)) {
      f.group.position.lerp(f.target, 0.06);
      const act = f.def.activity;
      f.group.children[0].position.y = 0.85 +
        (act === 'treadmill' ? Math.abs(Math.sin(t * 8)) * 0.18 : Math.sin(t * 2 + f.def.deskIndex) * 0.03);
      if (act === 'meeting' && f.def.id === (window.OfficeAPI && window.OfficeAPI._speakerId)) {
        f.group.position.y = Math.abs(Math.sin(t * 6)) * 0.1;   // 发言者轻跳
      } else { f.group.position.y = 0; }
    }
    // 猫: 漫游
    if (cat.pause > 0) { cat.pause -= clock.getDelta(); }
    else if (cat.group.position.distanceTo(cat.target) < 0.3) {
      if (Math.random() < 0.01) {
        cat.target.set(4 + Math.random() * 8, 0, -8 + Math.random() * 17);
        cat.pause = Math.random() * 3;
      }
    } else {
      cat.group.position.lerp(cat.target, 0.008);
      cat.group.lookAt(cat.target.x, 0, cat.target.z);
    }
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
      disposed = true; resizeObs.disconnect();
      renderer.dispose();
    },
  };
}
