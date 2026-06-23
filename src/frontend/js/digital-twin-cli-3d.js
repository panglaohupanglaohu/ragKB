import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

if(!THREE){document.getElementById('env-3d-info').textContent='⚠ Three.js 加载失败'}

let scene,camera,renderer,controls,clock;
let dustMesh,agentMeshes=[],myceliumGroup;
let currentRoom='council';
let initialized=false;
let _camGoal=null,_tgtGoal=null;

// ── 文字标签 canvas ──
function makeLabel(text){
  const c=document.createElement('canvas');c.width=512;c.height=128;
  const ctx=c.getContext('2d');
  ctx.font='bold 36px "Noto Sans SC",sans-serif';
  ctx.fillStyle='#ffffff';ctx.textAlign='center';ctx.textBaseline='middle';
  ctx.fillText(text,256,64);
  return c;
}

function makeColorLabel(text,hexColor){
  const c=document.createElement('canvas');c.width=512;c.height=128;
  const ctx=c.getContext('2d');
  ctx.font='bold 36px "Noto Sans SC",sans-serif';
  ctx.fillStyle=hexColor;ctx.textAlign='center';ctx.textBaseline='middle';
  ctx.fillText(text,256,64);
  return c;
}

// ── 智能体人形 (来自 plaza-dark.html createAgentFigure) ──
function createAgentFigure(name,hexColor,isChairman=false){
  const group=new THREE.Group();
  const col=new THREE.Color(hexColor);
  const scale=isChairman?1.3:1.0;
  const outlineMat=new THREE.MeshBasicMaterial({color:col,transparent:true,opacity:0.7,side:THREE.DoubleSide});
  const glowMat=new THREE.MeshBasicMaterial({color:col,transparent:true,opacity:0.28,side:THREE.DoubleSide});
  // Head ring (照搬 plaza.html TorusGeometry)
  const headR=0.34*scale,headTube=0.035*scale;
  const head=new THREE.Mesh(new THREE.TorusGeometry(headR,headTube,12,32),outlineMat);
  head.position.y=2.0*scale;group.add(head);
  // Head glow
  const headGlow=new THREE.Mesh(new THREE.TorusGeometry(headR,headTube*4,12,32),glowMat);
  headGlow.position.copy(head.position);group.add(headGlow);
  // Body U-arc (照搬 plaza.html TubeGeometry)
  const pts=[];
  for(let i=0;i<=32;i++){const t=i/32,a=Math.PI*t;
    pts.push(new THREE.Vector3(-Math.cos(a)*0.48*scale,(1.25-Math.sin(a)*0.65)*scale,0));}
  const curve=new THREE.CatmullRomCurve3(pts);
  group.add(new THREE.Mesh(new THREE.TubeGeometry(curve,32,0.035*scale,8,false),outlineMat));
  group.add(new THREE.Mesh(new THREE.TubeGeometry(curve,32,0.12*scale,8,false),glowMat));
  // Light
  const pl=new THREE.PointLight(col,isChairman?0.95:0.55,isChairman?8:5.5);
  pl.position.y=1.4*scale;group.add(pl);
  // Ground ring
  const glowRing=new THREE.Mesh(new THREE.RingGeometry(0.35*scale,0.55*scale,32),
    new THREE.MeshBasicMaterial({color:col,transparent:true,opacity:0.22,side:THREE.DoubleSide}));
  glowRing.rotation.x=-Math.PI/2;glowRing.position.y=0.01;group.add(glowRing);
  group.userData.glowRing=glowRing;
  // 进化光圈（破茧成蝶）：演练中该 agent 行动时，一道光环从底座分步升到头部、到顶张开淡出，
  // 取代整体放大缩小，体现"跃迁/演化"。默认隐藏，由 _pulseQueue 的 body 脉冲驱动。
  const ascendRing=new THREE.Mesh(new THREE.RingGeometry(0.30*scale,0.40*scale,48),
    new THREE.MeshBasicMaterial({color:col,transparent:true,opacity:0,side:THREE.DoubleSide,depthWrite:false}));
  ascendRing.rotation.x=-Math.PI/2;ascendRing.position.y=0.06;group.add(ascendRing);
  group.userData.ascendRing=ascendRing;
  group.userData.ascendBaseY=0.06;
  group.userData.ascendHeadY=2.0*scale;
  // Name sprite
  const css='#'+col.getHexString();
  const tex=new THREE.CanvasTexture(makeColorLabel(name,css));tex.minFilter=THREE.LinearFilter;
  const sprite=new THREE.Sprite(new THREE.SpriteMaterial({map:tex,transparent:true,depthTest:false}));
  sprite.position.y=(isChairman?3.12:2.84)*scale;sprite.scale.set(2.7,0.72,1);group.add(sprite);
  group.userData.label=name;
  return group;
}

// ── 技能水晶 (来自 skill-extract.html) ──
function createSkillNode(name,hexColor,radius=0.2){
  const g=new THREE.Group();const col=new THREE.Color(hexColor);
  // 内核
  const core=new THREE.Mesh(new THREE.OctahedronGeometry(radius,0),
    new THREE.MeshPhongMaterial({color:col,emissive:col,emissiveIntensity:0.4,transparent:true,opacity:0.8}));
  g.add(core);
  // 外壳线框
  const wire=new THREE.Mesh(new THREE.OctahedronGeometry(radius*1.4,0),
    new THREE.MeshBasicMaterial({color:col,wireframe:true,transparent:true,opacity:0.3}));
  g.add(wire);
  // 光环
  const ring=new THREE.Mesh(new THREE.RingGeometry(radius*1.2,radius*1.8,16),
    new THREE.MeshBasicMaterial({color:col,transparent:true,opacity:0.1,side:THREE.DoubleSide}));
  ring.rotation.x=-Math.PI/2;g.add(ring);
  g.userData.core=core;g.userData.wire=wire;
  return g;
}

// ── 菌丝网络 (照搬 skill-extract.html 的 buildVesselNerveScaffold) ──
function buildMycelium(col){
  const mg=new THREE.Group();
  const myceliumColor=new THREE.Color(col);
  function grow(origin,dir,len,thick,depth,maxD){
    if(depth>maxD||len<0.25)return;
    const pts=[origin.clone()];const steps=Math.max(Math.floor(len*5),3);
    const cur=origin.clone();const d=dir.clone().normalize();
    for(let i=1;i<=steps;i++){
      const t=i/steps;const wobble=Math.sin(t*7+depth*2.5)*0.08*(1+depth*0.3);
      const perpX=-d.z,perpZ=d.x;
      cur.add(d.clone().multiplyScalar(len/steps));
      cur.x+=perpX*wobble;cur.z+=perpZ*wobble;
      cur.y=origin.y+Math.sin(t*Math.PI)*0.06*len;
      pts.push(cur.clone());
    }
    const curve=new THREE.CatmullRomCurve3(pts);
    const depthRatio=1-depth/maxD;
    const mat=new THREE.MeshBasicMaterial({
      color:myceliumColor,transparent:true,opacity:0.06+depthRatio*0.18,side:THREE.DoubleSide
    });
    mg.add(new THREE.Mesh(new THREE.TubeGeometry(curve,Math.max(steps*2,4),thick,3,false),mat));
    const endPt=pts[pts.length-1];
    const branches=depth<2?2:1;
    for(let b=0;b<branches;b++){
      const spread=(b/branches)*Math.PI*1.4-Math.PI*0.7;
      const newDir=new THREE.Vector3(
        d.x*Math.cos(spread)-d.z*Math.sin(spread),0,
        d.x*Math.sin(spread)+d.z*Math.cos(spread)
      ).normalize();
      newDir.x+=(Math.random()-0.5)*0.35;newDir.z+=(Math.random()-0.5)*0.35;newDir.normalize();
      grow(endPt,newDir,len*(0.5+Math.random()*0.28),thick*0.6,depth+1,maxD);
    }
  }
  [0,1.57,3.14,4.71].forEach(angle=>{
    grow(new THREE.Vector3(0,0.06,0),new THREE.Vector3(Math.cos(angle),0,Math.sin(angle)),
      3.0+Math.random()*1.2,0.035+Math.random()*0.012,0,4);
  });
  return mg;
}

// ── 浮尘粒子 ──
function buildDust(count,radius,color){
  const pos=new Float32Array(count*3);
  for(let i=0;i<count;i++){pos[i*3]=(Math.random()-0.5)*radius;pos[i*3+1]=Math.random()*12;pos[i*3+2]=(Math.random()-0.5)*radius}
  const geo=new THREE.BufferGeometry();geo.setAttribute('position',new THREE.BufferAttribute(pos,3));
  return new THREE.Points(geo,new THREE.PointsMaterial({color,size:0.05,transparent:true,opacity:0.3}));
}

// ══════════════════════════════════════════════════
// 场景初始化
// ══════════════════════════════════════════════════
function initScene(){
  const canvas=document.getElementById('env-3d-canvas');
  const container=document.getElementById('env-3d-container');
  const W=container.clientWidth||800,H=container.clientHeight||600;

  scene=new THREE.Scene();
  scene.background=new THREE.Color(0x111820);
  scene.fog=new THREE.FogExp2(0x111820,0.012);

  camera=new THREE.PerspectiveCamera(50,W/H,0.1,200);
  camera.position.set(0,22,22);

  renderer=new THREE.WebGLRenderer({canvas,antialias:true});
  renderer.setClearColor(0x111820);
  renderer.setSize(W,H);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio,2));
  renderer.shadowMap.enabled=true;
  renderer.shadowMap.type=THREE.PCFSoftShadowMap;
  renderer.toneMapping=THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure=0.9;

  controls=new OrbitControls(camera,canvas);
  controls.enableDamping=true;controls.dampingFactor=0.06;
  controls.minDistance=6;controls.maxDistance=50;
  controls.maxPolarAngle=Math.PI/2.15;controls.target.set(0,0,0);

  clock=new THREE.Clock();
  if(!window._dt3dResizeObs){
    window._dt3dResizeObs=new ResizeObserver(()=>{const w=container.clientWidth,h=container.clientHeight;if(w&&h){camera.aspect=w/h;camera.updateProjectionMatrix();renderer.setSize(w,h)}});
    window._dt3dResizeObs.observe(container);
  }

  initialized=true;
  buildRoom('council');
  animate();
}

// ── 清空场景 (properly dispose geometries/materials) ──
function clearScene(){
  scene.traverse(obj=>{
    if(obj.geometry)obj.geometry.dispose();
    if(obj.material){if(Array.isArray(obj.material))obj.material.forEach(m=>m.dispose());else obj.material.dispose()}
  });
  while(scene.children.length>0)scene.remove(scene.children[0]);
  agentMeshes=[];dustMesh=null;myceliumGroup=null;
}

// ══════════════════════════════════════════════════
// 6 个房间场景构建
// ══════════════════════════════════════════════════
function buildRoom(roomId){
  if(!initialized)return;
  clearScene();currentRoom=roomId;window._currentRoomId=roomId;

  var isKnown = false;
  switch(roomId){
    case'council':buildCouncil();isKnown=true;break;
    case'extraction':buildExtraction();isKnown=true;break;
    case'workshop':buildWorkshop();isKnown=true;break;
    case'library':buildLibrary();isKnown=true;break;
    case'arena':buildArena();isKnown=true;break;
    case'rest':buildRest();isKnown=true;break;
  }
  // D-1.3: 场景房间/自定义房间 → 通用圆形布局
  if(!isKnown) buildGenericRoom(roomId);

  // ── 添加智能体 (来自选中团队) ──
  // 议事厅和工作坊自己处理智能体摆放，跳过通用逻辑
  var roomName = (typeof window.getRoomName==='function') ? window.getRoomName(roomId) : roomId;
  if(roomId==='council'||roomId==='workshop'||roomId==='rest'){
    document.getElementById('env-3d-info').textContent=
      roomName+' — '+(window.S?window.S.agents.filter(a=>window.S.selectedTeams&&window.S.selectedTeams.includes(a._teamId)).length:0)+' 个智能体';
    return;
  }
  if(isKnown) addAgentsToScene();
  document.getElementById('env-3d-info').textContent=
    roomName+' — '+(agentMeshes.length)+' 个智能体';
}

function addAgentsToScene(){
  const S=window.S;if(!S)return;
  const colors=['#22d3ee','#34d399','#a78bfa','#fbbf24','#f472b6','#60a5fa'];
  const visibleAgents=S.agents.filter(a=>S.selectedTeams&&S.selectedTeams.includes(a._teamId));
  const agents=visibleAgents.length?visibleAgents:S.agents;
  agents.forEach((ag,i)=>{
    const angle=(Math.PI*2*i)/Math.max(agents.length,1)-Math.PI/2;
    const r=4+Math.min(agents.length,12)*0.6;
    const fig=createAgentFigure(ag.name||'Agent',colors[i%colors.length],i===0);
    fig.position.set(r*Math.cos(angle),0,r*Math.sin(angle));
    fig.userData.baseY=0;
    fig.lookAt(0,0,0);
    fig.userData.agentId=ag.agent_id;
    scene.add(fig);agentMeshes.push(fig);
  });
}

// D-1.3: 场景房间通用3D视图 — 圆形平台 + 阶段标记 + 智能体环
function buildGenericRoom(roomId){
  var room = (window.S&&window.S.rooms||[]).find(function(r){return r.id===roomId;});
  var roomName = room ? (room.icon||'🏠')+' '+room.name : roomId;
  var stage = room ? (room.stage!=null ? '阶段 '+room.stage : '') : '';

  // 深色圆形平台
  var platGeo = new THREE.CylinderGeometry(6, 6.5, 0.3, 48);
  var plat = new THREE.Mesh(platGeo, new THREE.MeshStandardMaterial({color:0x1a2744,roughness:0.8,metalness:0.3}));
  plat.position.y=-0.15;plat.receiveShadow=true;scene.add(plat);

  // 外环
  var ringGeo = new THREE.TorusGeometry(6, 0.08, 16, 80);
  var ring = new THREE.Mesh(ringGeo, new THREE.MeshStandardMaterial({color:0x22d3ee,emissive:0x0a3d4a,roughness:0.3}));
  ring.rotation.x=Math.PI/2;ring.position.y=0.02;scene.add(ring);

  // 中心支柱 + 铭牌
  var poleGeo = new THREE.CylinderGeometry(0.2, 0.3, 4, 16);
  var pole = new THREE.Mesh(poleGeo, new THREE.MeshStandardMaterial({color:0x334155,roughness:0.6,metalness:0.5}));
  pole.position.y=2;pole.castShadow=true;scene.add(pole);
  var capGeo = new THREE.SphereGeometry(0.6, 24, 24);
  var cap = new THREE.Mesh(capGeo, new THREE.MeshStandardMaterial({color:0x22d3ee,emissive:0x0a3d4a,roughness:0.2,metalness:0.8}));
  cap.position.y=4.3;scene.add(cap);

  // 粒子环（旋转光晕）
  var pts=[];for(var i=0;i<80;i++){var a=Math.PI*2*i/80;pts.push(new THREE.Vector3(5.5*Math.cos(a),2.5+Math.sin(i*0.3)*0.3,5.5*Math.sin(a)));}
  var pGeo=new THREE.BufferGeometry().setFromPoints(pts);
  var pLine=new THREE.Line(pGeo,new THREE.LineBasicMaterial({color:0x22d3ee,transparent:true,opacity:0.3}));
  scene.add(pLine);

  // 场景房间的智能体：按位置放置
  var S=window.S;if(S){
    var colors=['#22d3ee','#34d399','#a78bfa','#fbbf24','#f472b6','#60a5fa'];
    var inRoom = S.agents.filter(function(a){return S.positions&&S.positions[a.agent_id]===roomId;});
    if(!inRoom.length) inRoom = S.agents.filter(function(a){return S.selectedTeams&&S.selectedTeams.includes(a._teamId);});
    if(!inRoom.length) inRoom = S.agents;
    inRoom.forEach(function(ag,i){
      var angle=(Math.PI*2*i)/Math.max(inRoom.length,1)-Math.PI/2;
      var r=2.5+Math.min(inRoom.length,10)*0.4;
      var fig=createAgentFigure(ag.name||'Agent',colors[i%colors.length],i===0);
      fig.position.set(r*Math.cos(angle),0.5,r*Math.sin(angle));
      fig.userData.baseY=0.5;
      fig.lookAt(0,1.2,0);
      fig.userData.agentId=ag.agent_id;
      scene.add(fig);agentMeshes.push(fig);
    });
  }

  var info = roomName+' — '+(agentMeshes.length)+' 个智能体';
  if(stage) info += ' · '+stage;
  document.getElementById('env-3d-info').textContent=info;
}


// ── 议事厅 (照搬 plaza.html 安藤忠雄清水混凝土议事厅) ──
function buildCouncil(){
  _camGoal=new THREE.Vector3(0,14,28);_tgtGoal=new THREE.Vector3(0,1,0);
  // 场景氛围 (照搬 plaza.html)
  scene.background=new THREE.Color(0x1A2026);
  scene.fog=new THREE.FogExp2(0x1A2026,0.0076);
  renderer.setClearColor(0x1A2026);
  renderer.toneMappingExposure=1.0;
  // 光照 (照搬 plaza.html: restrained Ando-style)
  scene.add(new THREE.AmbientLight(0x9099A2,0.06));
  const mainLight=new THREE.DirectionalLight(0xC7D0D8,0.46);
  mainLight.position.set(3,30,5);mainLight.castShadow=true;
  mainLight.shadow.mapSize.set(2048,2048);
  mainLight.shadow.camera.near=1;mainLight.shadow.camera.far=60;
  mainLight.shadow.camera.left=-25;mainLight.shadow.camera.right=25;
  mainLight.shadow.camera.top=25;mainLight.shadow.camera.bottom=-25;
  mainLight.shadow.bias=-0.001;mainLight.shadow.normalBias=0.02;
  scene.add(mainLight);
  scene.add(new THREE.HemisphereLight(0x98A2AB,0x353D46,0.04));
  // Raking architectural light
  const rakingLight=new THREE.SpotLight(0xCCD4DC,0.12,70,Math.PI/8,0.65,1.3);
  rakingLight.position.set(-18,24,-6);
  rakingLight.target.position.set(0,0.8,0);
  rakingLight.castShadow=true;scene.add(rakingLight);scene.add(rakingLight.target);
  // 地面 (照搬 plaza.html: 清水混凝土 0xA9AFB5)
  const ground=new THREE.Mesh(new THREE.CircleGeometry(35,64),
    new THREE.MeshStandardMaterial({color:0xA9AFB5,roughness:0.92,metalness:0}));
  ground.rotation.x=-Math.PI/2;ground.receiveShadow=true;scene.add(ground);
  // 阶梯式环形看台 (照搬 plaza.html 三层)
  const tierDefs=[
    {innerR:14,outerR:19,y:2.4,stepH:1.0,color:0x7F8790},
    {innerR:9,outerR:13,y:1.5,stepH:0.8,color:0x939BA4},
    {innerR:5,outerR:8,y:0.7,stepH:0.6,color:0xAEB5BC}
  ];
  tierDefs.forEach(tier=>{
    // Ring surface
    const top=new THREE.Mesh(new THREE.RingGeometry(tier.innerR,tier.outerR,96),
      new THREE.MeshStandardMaterial({color:tier.color,roughness:0.88,metalness:0}));
    top.rotation.x=-Math.PI/2;top.position.y=tier.y;top.receiveShadow=true;scene.add(top);
    // Inner wall
    const wall=new THREE.Mesh(new THREE.CylinderGeometry(tier.innerR,tier.innerR,tier.stepH,96,1,true),
      new THREE.MeshStandardMaterial({color:new THREE.Color(tier.color).multiplyScalar(0.72),roughness:0.92,metalness:0}));
    wall.position.y=tier.y-tier.stepH/2;wall.receiveShadow=true;wall.castShadow=true;scene.add(wall);
    // Outer wall
    const outer=new THREE.Mesh(new THREE.CylinderGeometry(tier.outerR,tier.outerR,tier.y,96,1,true),
      new THREE.MeshStandardMaterial({color:new THREE.Color(tier.color).multiplyScalar(0.8),roughness:0.92,metalness:0}));
    outer.position.y=tier.y/2;scene.add(outer);
    // Formwork seam
    const seam=new THREE.Mesh(new THREE.RingGeometry(tier.innerR-0.01,tier.outerR+0.01,96),
      new THREE.MeshBasicMaterial({color:0x000000,transparent:true,opacity:0.075,side:THREE.DoubleSide}));
    seam.rotation.x=-Math.PI/2;seam.position.y=tier.y+0.005;scene.add(seam);
  });
  // 中央竞技场地板 (抛光混凝土)
  const centerFloor=new THREE.Mesh(new THREE.CircleGeometry(4.5,64),
    new THREE.MeshStandardMaterial({color:0xE2E6E9,roughness:0.72,metalness:0}));
  centerFloor.rotation.x=-Math.PI/2;centerFloor.position.y=0.01;centerFloor.receiveShadow=true;scene.add(centerFloor);
  // 模板格栅线
  for(let i=-4;i<=4;i++){
    const lineMat=new THREE.MeshBasicMaterial({color:0x000000,transparent:true,opacity:0.08,side:THREE.DoubleSide});
    const hLine=new THREE.Mesh(new THREE.PlaneGeometry(9,0.015),lineMat);
    hLine.rotation.x=-Math.PI/2;hLine.position.set(0,0.015,i);scene.add(hLine);
    const vLine=new THREE.Mesh(new THREE.PlaneGeometry(9,0.015),lineMat.clone());
    vLine.rotation.x=-Math.PI/2;vLine.rotation.z=Math.PI/2;vLine.position.set(i,0.015,0);scene.add(vLine);
  }
  // 议事长座椅 (Carlo Scarpa 层叠几何)
  const throneGroup=new THREE.Group();
  const base1=new THREE.Mesh(new THREE.BoxGeometry(2.4,0.12,2.0),
    new THREE.MeshStandardMaterial({color:0x9BA2A9,roughness:0.88,metalness:0}));
  base1.position.y=0.06;base1.rotation.y=Math.PI/24;base1.castShadow=true;base1.receiveShadow=true;throneGroup.add(base1);
  const base2=new THREE.Mesh(new THREE.BoxGeometry(2.0,0.06,1.7),
    new THREE.MeshStandardMaterial({color:0x5F666D,roughness:0.35,metalness:0.6}));
  base2.position.set(0.08,0.18,-0.05);base2.rotation.y=-Math.PI/30;base2.castShadow=true;throneGroup.add(base2);
  const base3=new THREE.Mesh(new THREE.BoxGeometry(1.6,0.15,1.3),
    new THREE.MeshStandardMaterial({color:0xB0B6BC,roughness:0.84,metalness:0}));
  base3.position.set(-0.04,0.30,-0.02);base3.rotation.y=Math.PI/40;base3.castShadow=true;throneGroup.add(base3);
  const seatMesh=new THREE.Mesh(new THREE.BoxGeometry(1.3,0.07,0.85),
    new THREE.MeshStandardMaterial({color:0x687078,roughness:0.32,metalness:0.6}));
  seatMesh.position.set(0,0.56,0.08);seatMesh.castShadow=true;throneGroup.add(seatMesh);
  const armL=new THREE.Mesh(new THREE.BoxGeometry(0.10,0.06,0.75),
    new THREE.MeshStandardMaterial({color:0xA6ADB4,roughness:0.86,metalness:0}));
  armL.position.set(-0.62,0.82,0.05);throneGroup.add(armL);
  const armR=new THREE.Mesh(new THREE.BoxGeometry(0.10,0.06,0.70),
    new THREE.MeshStandardMaterial({color:0x5E666E,roughness:0.32,metalness:0.6}));
  armR.position.set(0.62,0.72,0.05);throneGroup.add(armR);
  // 天光聚光灯 (照在议事长座位上)
  const throneLight=new THREE.SpotLight(0xF4F7FA,1.95,22,Math.PI/18,0.12,1.9);
  throneLight.position.set(0.18,12.6,-0.42);throneLight.target.position.set(0.04,0.72,0.08);
  throneLight.castShadow=true;throneLight.shadow.mapSize.set(1024,1024);throneLight.shadow.bias=-0.0005;
  throneGroup.add(throneLight);throneGroup.add(throneLight.target);
  const crossFill=new THREE.SpotLight(0xE6ECF1,0.16,10,Math.PI/24,0.18,1.8);
  crossFill.position.set(-0.95,10.8,-1.2);crossFill.target.position.set(0.0,0.58,0.04);
  throneGroup.add(crossFill);throneGroup.add(crossFill.target);
  throneGroup.position.set(0,0,0);scene.add(throneGroup);
  // ── 智能体站在台阶上 (照搬 plaza.html 逻辑) ──
  const csS=window.S;
  const csColors=['#22d3ee','#34d399','#a78bfa','#fbbf24','#f472b6','#60a5fa'];
  const ringRadii=[6.5,11,16.5];
  const ringHeightMultiplier=[0.4,0.7,1]; // 内圈0.4倍身高, 中圈0.7倍, 外圈1倍
  const ringMax=[8,12,20];
  if(csS&&csS.agents.length){
    const csAgents=csS.agents.filter(a=>csS.selectedTeams&&csS.selectedTeams.includes(a._teamId));
    const list=csAgents.length?csAgents:csS.agents;
    // 按容量填充: 内圈8个, 中圈12个, 外圈20个
    const rings=[[],[],[]];
    let ri=0;
    list.forEach(ag=>{
      while(ri<2&&rings[ri].length>=ringMax[ri])ri++;
      rings[Math.min(ri,2)].push(ag);
    });
    rings.forEach((ring,rIdx)=>{
      if(!ring.length)return;
      ring.forEach((ag,ai)=>{
        const angle=(ai/ring.length)*Math.PI*2-Math.PI/2;
        const isChair=rIdx===0&&ai===0;
        const fig=createAgentFigure(ag.name||'Agent',csColors[ai%csColors.length],isChair);
        const figScale=isChair?1.3:1.0;
        const figH=2.84*figScale; // 智能体自身高度
        const yPos=figH*ringHeightMultiplier[rIdx];
        fig.position.set(ringRadii[rIdx]*Math.cos(angle),yPos,ringRadii[rIdx]*Math.sin(angle));
        fig.userData.baseY=yPos;
        fig.lookAt(0,yPos,0);
        fig.rotation.x=0;fig.rotation.z=0;
        fig.userData.agentId=ag.agent_id;
        scene.add(fig);agentMeshes.push(fig);
      });
    });
  }
}

// ── 萃取室 (skill-extract.html 培养皿+菌丝网络) ──
function buildExtraction(){
  _camGoal=new THREE.Vector3(0,10,22);_tgtGoal=new THREE.Vector3(0,2,0);
  // 场景氛围 (照搬 skill-extract)
  scene.background=new THREE.Color(0x1A2026);
  scene.fog=new THREE.FogExp2(0x1A2026,0.016);
  renderer.setClearColor(0x1A2026);
  // 光照 (参考 council 提亮)
  scene.add(new THREE.AmbientLight(0x8090A0,0.12));
  const mainLight=new THREE.DirectionalLight(0xC0C8D0,0.5);
  mainLight.position.set(5,25,8);mainLight.castShadow=true;scene.add(mainLight);
  scene.add(new THREE.HemisphereLight(0x8899A2,0x2A2828,0.1));
  const accentLight=new THREE.PointLight(0x34d399,0.3,20);accentLight.position.set(0,8,0);scene.add(accentLight);
  // 基质层 (照搬 skill-extract: 0x1A2026)
  const substrate=new THREE.Mesh(new THREE.CircleGeometry(25,48),
    new THREE.MeshStandardMaterial({color:0x8A9095,roughness:0.88,metalness:0,transparent:true,opacity:0.95}));
  substrate.rotation.x=-Math.PI/2;scene.add(substrate);
  // 培养皿边缘 (照搬 skill-extract: 0x1E1A16)
  const rim=new THREE.Mesh(new THREE.TorusGeometry(25,0.15,6,48),
    new THREE.MeshBasicMaterial({color:0x1E1A16,transparent:true,opacity:0.6}));
  rim.rotation.x=-Math.PI/2;rim.position.y=0.08;scene.add(rim);
  // 同心纹理 (照搬 skill-extract: 0x221E18, opacity 0.08)
  [5,10,15,20].forEach(r=>{
    const ring=new THREE.Mesh(new THREE.RingGeometry(r-0.02,r+0.02,48),
      new THREE.MeshBasicMaterial({color:0x221E18,transparent:true,opacity:0.08}));
    ring.rotation.x=-Math.PI/2;ring.position.y=0.002;scene.add(ring);
  });
  // 菌丝网络 (照搬 skill-extract 的 buildVesselNerveScaffold 水平分枝)
  myceliumGroup=buildMycelium(0x34d399);scene.add(myceliumGroup);
  // 浮动技能水晶
  const S=window.S;const skills=(S&&S.skills||[]).slice(0,8);
  const skillColors=[0x34d399,0xfbbf24,0xa78bfa,0x22d3ee,0xf472b6,0x60a5fa,0x34d399,0xfbbf24];
  skills.forEach((sk,i)=>{
    const a=(Math.PI*2*i)/Math.max(skills.length,1);const r=6+i*0.8;
    const node=createSkillNode(sk.name||'skill',skillColors[i%skillColors.length],0.25);
    node.position.set(r*Math.cos(a),2+Math.random()*2,r*Math.sin(a));
    scene.add(node);
    const tex=new THREE.CanvasTexture(makeColorLabel(sk.name||'skill','#'+new THREE.Color(skillColors[i%skillColors.length]).getHexString()));
    tex.minFilter=THREE.LinearFilter;
    const sp=new THREE.Sprite(new THREE.SpriteMaterial({map:tex,transparent:true,depthTest:false}));
    sp.position.copy(node.position);sp.position.y+=0.6;sp.scale.set(2,0.5,1);scene.add(sp);
  });
  // 浮尘 (照搬 skill-extract: color 0x584838, size 0.1, opacity 0.3)
  dustMesh=buildDust(120,50,0x584838);scene.add(dustMesh);
}

// ── 工作坊 (双层透明玻璃屏幕 + 智能体) ──
function buildWorkshop(){
  _camGoal=new THREE.Vector3(0,14,26);_tgtGoal=new THREE.Vector3(0,3,0);
  scene.background=new THREE.Color(0x0E1318);scene.fog=new THREE.FogExp2(0x0E1318,0.008);renderer.setClearColor(0x0E1318);
  // 光照 (参考 council 提亮)
  scene.add(new THREE.AmbientLight(0x9099A2,0.12));
  const dl=new THREE.DirectionalLight(0xC7D0D8,0.46);dl.position.set(4,20,6);dl.castShadow=true;
  dl.shadow.mapSize.set(1024,1024);scene.add(dl);
  scene.add(new THREE.HemisphereLight(0x8899A2,0x1A2026,0.1));
  const fillLight=new THREE.PointLight(0x60a5fa,0.2,18);fillLight.position.set(0,10,0);scene.add(fillLight);
  // 地面
  const ground=new THREE.Mesh(new THREE.CircleGeometry(22,64),
    new THREE.MeshStandardMaterial({color:0x7A8898,roughness:0.88,metalness:0}));
  ground.rotation.x=-Math.PI/2;ground.receiveShadow=true;scene.add(ground);
  [5,10,16].forEach(r=>{
    const ring=new THREE.Mesh(new THREE.RingGeometry(r-0.02,r+0.02,64),
      new THREE.MeshBasicMaterial({color:0x2A3040,transparent:true,opacity:0.15}));
    ring.rotation.x=-Math.PI/2;ring.position.y=0.003;scene.add(ring);
  });
  // ─── 屏幕放在智能体面前 (无玻璃, 仅彩色边框) ───
  const wsS=window.S;
  const wsColorHex=['#22d3ee','#34d399','#a78bfa','#fbbf24','#f472b6','#60a5fa'];
  const wsAgents=(wsS&&wsS.agents.length)?wsS.agents.filter(a=>wsS.selectedTeams&&wsS.selectedTeams.includes(a._teamId)):[];
  const agentList=wsAgents.length?wsAgents:(wsS&&wsS.agents.length?wsS.agents:[]);
  // ─── 中央三块共享看板屏幕 (上方悬浮, 大尺寸, 边缘相抵) ───
  const boardTexts=['协作讨论区','任务看板','知识汇总'];
  const boardColor=0x60a5fa;
  for(let i=0;i<3;i++){
    const angle=(Math.PI*2*i)/3-Math.PI/2;
    const br=2.8,bx=br*Math.cos(angle),bz=br*Math.sin(angle);
    const bW=3.2,bH=2.2,bY=7.0;
    // 边框
    const pts=[new THREE.Vector3(-bW/2,-bH/2,0),new THREE.Vector3(bW/2,-bH/2,0),
      new THREE.Vector3(bW/2,bH/2,0),new THREE.Vector3(-bW/2,bH/2,0),new THREE.Vector3(-bW/2,-bH/2,0)];
    const geom=new THREE.BufferGeometry().setFromPoints(pts);
    const line=new THREE.Line(geom,new THREE.LineBasicMaterial({color:boardColor,transparent:true,opacity:0.7}));
    line.position.set(bx,bY,bz);line.lookAt(0,bY,0);scene.add(line);
    // 标题
    const tex=new THREE.CanvasTexture(makeColorLabel(boardTexts[i],'#'+new THREE.Color(boardColor).getHexString()));
    tex.minFilter=THREE.LinearFilter;
    const sp=new THREE.Sprite(new THREE.SpriteMaterial({map:tex,transparent:true,depthTest:false}));
    sp.position.set(bx,bY,bz);sp.scale.set(2.4,0.65,1);scene.add(sp);
    const pl=new THREE.PointLight(boardColor,0.12,5);pl.position.set(bx,bY-0.8,bz);scene.add(pl);
  }
  // ─── 智能体+屏幕 分内/中/外三圈 ───
  const ringMax=[8,12,20];
  const agentRadii=[7,11,15.5]; // 智能体环半径 (加大以容纳宽屏)
  const screenRadii=[5,9,13.5]; // 屏幕在智能体内侧
  const screenW=3.8,screenH=1.0;
  const screenY=2.2;
  // 分配到圈
  const rings=[[],[],[]];
  let ri=0;
  agentList.forEach(ag=>{
    while(ri<2&&rings[ri].length>=ringMax[ri])ri++;
    rings[Math.min(ri,2)].push(ag);
  });
  rings.forEach((ring,rIdx)=>{
    if(!ring.length)return;
    ring.forEach((ag,ai)=>{
      const angle=(ai/ring.length)*Math.PI*2-Math.PI/2;
      const color=wsColorHex[ai%wsColorHex.length];
      const col=new THREE.Color(color);
      // 智能体
      const aR=agentRadii[rIdx];
      const fig=createAgentFigure(ag.name||'Agent',color,rIdx===0&&ai===0);
      fig.position.set(aR*Math.cos(angle),0,aR*Math.sin(angle));
      fig.userData.baseY=0;
      fig.lookAt(0,0,0);fig.userData.agentId=ag.agent_id;
      scene.add(fig);agentMeshes.push(fig);
      // 对应屏幕 (在智能体前方, 同角度)
      const sR=screenRadii[rIdx];
      const sx=sR*Math.cos(angle),sz=sR*Math.sin(angle);
      const pts=[new THREE.Vector3(-screenW/2,-screenH/2,0),new THREE.Vector3(screenW/2,-screenH/2,0),
        new THREE.Vector3(screenW/2,screenH/2,0),new THREE.Vector3(-screenW/2,screenH/2,0),new THREE.Vector3(-screenW/2,-screenH/2,0)];
      const geom=new THREE.BufferGeometry().setFromPoints(pts);
      const line=new THREE.Line(geom,new THREE.LineBasicMaterial({color:col,transparent:true,opacity:0.8}));
      line.position.set(sx,screenY,sz);line.lookAt(0,screenY,0);scene.add(line);
      fig.userData.screenPos=new THREE.Vector3(sx,screenY,sz);
      fig.userData.screenLine=line;
      const pl=new THREE.PointLight(col,0.08,2.5);pl.position.set(sx,screenY-0.5,sz);scene.add(pl);
    });
  });
  // fallback: 无智能体时
  if(!agentList.length){
    const wsAgentNames=['策划师','架构师','编码员','测试员','文档员'];
    for(let i=0;i<5;i++){
      const angle=(Math.PI*2*i)/5-Math.PI/2;
      const fig=createAgentFigure(wsAgentNames[i],wsColorHex[i],i===0);
      fig.position.set(7*Math.cos(angle),0,7*Math.sin(angle));
      fig.userData.baseY=0;fig.lookAt(0,0,0);scene.add(fig);agentMeshes.push(fig);
      const sx=5*Math.cos(angle),sz=5*Math.sin(angle);
      const pts=[new THREE.Vector3(-screenW/2,-screenH/2,0),new THREE.Vector3(screenW/2,-screenH/2,0),
        new THREE.Vector3(screenW/2,screenH/2,0),new THREE.Vector3(-screenW/2,screenH/2,0),new THREE.Vector3(-screenW/2,-screenH/2,0)];
      const geom=new THREE.BufferGeometry().setFromPoints(pts);
      const line=new THREE.Line(geom,new THREE.LineBasicMaterial({color:new THREE.Color(wsColorHex[i]),transparent:true,opacity:0.8}));
      line.position.set(sx,screenY,sz);line.lookAt(0,screenY,0);scene.add(line);
      fig.userData.screenPos=new THREE.Vector3(sx,screenY,sz);
      fig.userData.screenLine=line;
    }
  }
  // 浮尘
  dustMesh=buildDust(100,40,0x556680);scene.add(dustMesh);
}

// ── 知识库 ──
function buildLibrary(){
  _camGoal=new THREE.Vector3(0,17,22);_tgtGoal=new THREE.Vector3(0,1,0);
  scene.background=new THREE.Color(0x111820);scene.fog=new THREE.FogExp2(0x111820,0.008);renderer.setClearColor(0x111820);
  scene.add(new THREE.AmbientLight(0xc8d4e0,0.7));
  const dl=new THREE.DirectionalLight(0xe8f0ff,0.7);dl.position.set(5,15,8);dl.castShadow=true;scene.add(dl);
  scene.add(new THREE.HemisphereLight(0xc8d4e0,0x111820,0.5));
  dustMesh=buildDust(150,40,0x8899aa);scene.add(dustMesh);
  const ground=new THREE.Mesh(new THREE.CircleGeometry(18,48),
    new THREE.MeshStandardMaterial({color:0x4A5A6E,roughness:0.8}));
  ground.rotation.x=-Math.PI/2;ground.receiveShadow=true;scene.add(ground);
  // 水晶书架环绕
  for(let i=0;i<8;i++){const a=(Math.PI*2*i)/8;const r=8;
    const shelf=new THREE.Mesh(new THREE.BoxGeometry(3,4,0.3),
      new THREE.MeshPhysicalMaterial({color:0x88ccff,transparent:true,opacity:0.25,
        roughness:0.05,metalness:0.1,transmission:0.7,thickness:0.3,
        emissive:0x4488cc,emissiveIntensity:0.05}));
    shelf.position.set(r*Math.cos(a),2,r*Math.sin(a));shelf.lookAt(0,2,0);shelf.castShadow=true;scene.add(shelf);
    // 水晶书架边框光
    const shelfLight=new THREE.PointLight(0x88ccff,0.15,3);
    shelfLight.position.set(r*Math.cos(a),3.5,r*Math.sin(a));scene.add(shelfLight);
    for(let j=0;j<5;j++){const bc=[0xa78bfa,0x60a5fa,0x34d399,0xfbbf24,0xf472b6][j];
      const book=new THREE.Mesh(new THREE.BoxGeometry(0.3,0.5+Math.random()*0.4,0.18),
        new THREE.MeshPhysicalMaterial({color:bc,transparent:true,opacity:0.6,
          roughness:0.1,metalness:0.2,emissive:bc,emissiveIntensity:0.15}));
      book.position.set(r*Math.cos(a)+Math.cos(a+Math.PI/2)*(j-2)*0.35,0.8+j*0.65,r*Math.sin(a)+Math.sin(a+Math.PI/2)*(j-2)*0.35);
      book.lookAt(0,book.position.y,0);scene.add(book)}}
  // 阅读桌
  const desk=new THREE.Mesh(new THREE.CylinderGeometry(2,2,0.1,16),
    new THREE.MeshStandardMaterial({color:0x1e2636}));desk.position.y=0.9;scene.add(desk);
  // 知识球
  for(let i=0;i<6;i++){const ko=new THREE.Mesh(new THREE.SphereGeometry(0.18,8,8),
    new THREE.MeshPhongMaterial({color:0xa78bfa,emissive:0xa78bfa,emissiveIntensity:0.5,transparent:true,opacity:0.4}));
    ko.position.set((Math.random()-0.5)*6,2.5+Math.random()*2,(Math.random()-0.5)*6);scene.add(ko)}
  scene.add(new THREE.PointLight(0xc8e0ff,0.5,12).translateY(5));
}

// ── 演练场 ──
function buildArena(){
  _camGoal=new THREE.Vector3(0,17,22);_tgtGoal=new THREE.Vector3(0,1,0);
  scene.background=new THREE.Color(0x111820);scene.fog=new THREE.FogExp2(0x111820,0.008);renderer.setClearColor(0x111820);
  scene.add(new THREE.AmbientLight(0xc8d4e0,0.7));
  const dl=new THREE.DirectionalLight(0xe8f0ff,0.7);dl.position.set(5,15,8);dl.castShadow=true;scene.add(dl);
  scene.add(new THREE.HemisphereLight(0xc8d4e0,0x111820,0.5));
  dustMesh=buildDust(150,40,0x8899aa);scene.add(dustMesh);
  const ground=new THREE.Mesh(new THREE.CylinderGeometry(10,10.5,0.4,8),
    new THREE.MeshStandardMaterial({color:0x828890,metalness:0.3,roughness:0.4}));
  ground.receiveShadow=true;scene.add(ground);
  // 围绳
  const col=0xf472b6;
  for(let i=0;i<4;i++){const a=(Math.PI*2*i)/4+Math.PI/4;
    const post=new THREE.Mesh(new THREE.CylinderGeometry(0.1,0.1,2.5,8),
      new THREE.MeshStandardMaterial({color:col,emissive:col,emissiveIntensity:0.1}));
    post.position.set(6*Math.cos(a),1.25,6*Math.sin(a));post.castShadow=true;scene.add(post);
    scene.add(new THREE.PointLight(col,0.15,6).translateY(3).translateX(6*Math.cos(a)).translateZ(6*Math.sin(a)));
  }
  for(let i=0;i<4;i++){const a1=(Math.PI*2*i)/4+Math.PI/4,a2=(Math.PI*2*((i+1)%4))/4+Math.PI/4;
    const pts=[new THREE.Vector3(6*Math.cos(a1),1.8,6*Math.sin(a1)),new THREE.Vector3(6*Math.cos(a2),1.8,6*Math.sin(a2))];
    scene.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(pts),new THREE.LineBasicMaterial({color:col,transparent:true,opacity:0.3})))}
  // 记分牌
  const board=new THREE.Mesh(new THREE.BoxGeometry(2.5,1.2,0.08),
    new THREE.MeshPhongMaterial({color:0x111118,emissive:col,emissiveIntensity:0.1}));
  board.position.set(0,5.5,0);scene.add(board);
  const sl=new THREE.Sprite(new THREE.SpriteMaterial({map:new THREE.CanvasTexture(makeColorLabel('A/B TEST','#f472b6')),transparent:true}));
  sl.position.set(0,5.5,0.1);sl.scale.set(3,0.8,1);scene.add(sl);
  // 靶子
  for(let i=0;i<3;i++){
    const dm=new THREE.Mesh(new THREE.CylinderGeometry(0.2,0.3,1.2,8),new THREE.MeshStandardMaterial({color:0x3a2030}));
    dm.position.set(-2.5+i*2.5,0.6,0);dm.castShadow=true;scene.add(dm);
    const dh=new THREE.Mesh(new THREE.SphereGeometry(0.2,8,8),new THREE.MeshStandardMaterial({color:0x4a2535}));
    dh.position.set(-2.5+i*2.5,1.5,0);scene.add(dh)}
}

// ── 休息区 · 现代发光枯山水 (致敬龙安寺) ──
function buildRest(){
  _camGoal=new THREE.Vector3(0,15,22);_tgtGoal=new THREE.Vector3(0,0,-2);
  scene.background=new THREE.Color(0x0a0e16);scene.fog=new THREE.FogExp2(0x0a0e16,0.004);renderer.setClearColor(0x0a0e16);
  scene.add(new THREE.AmbientLight(0x6A5030,0.35));
  const moonLight=new THREE.DirectionalLight(0xCC8820,0.5);moonLight.position.set(-5,20,8);scene.add(moonLight);
  scene.add(new THREE.HemisphereLight(0xA07030,0x0a0e16,0.3));

  // ── 庭園地面 (矩形砂砾, 龙安寺 5:2 比例) ──
  const gW=32,gD=16;
  const sand=new THREE.Mesh(new THREE.PlaneGeometry(gW,gD),
    new THREE.MeshStandardMaterial({color:0x354A68,roughness:0.88}));
  sand.rotation.x=-Math.PI/2;sand.receiveShadow=true;scene.add(sand);

  // ── 发光耙纹 (平行线, 横向) ──
  const lnMat=new THREE.MeshBasicMaterial({color:0x2a4060,transparent:true,opacity:0.2});
  for(let z=-gD/2+0.3;z<gD/2;z+=0.35){
    const ln=new THREE.Mesh(new THREE.BoxGeometry(gW-0.4,0.008,0.025),lnMat);
    ln.position.set(0,0.005,z);scene.add(ln);
  }

  // ── 五组十五石 (龙安寺布局, 放大) ──
  const groups=[
    {stones:[{x:-11.6,z:-2.6,s:0.9},{x:-12.8,z:-4.1,s:0.65},{x:-10.6,z:-4.4,s:0.5},{x:-13,z:-1.7,s:0.45},{x:-11,z:-1.5,s:0.35}],color:0x4fc3f7},
    {stones:[{x:-5.5,z:2.6,s:0.75},{x:-6.5,z:1.7,s:0.55}],color:0x81d4fa},
    {stones:[{x:0.3,z:-1.2,s:1.05},{x:1.5,z:-2.3,s:0.65},{x:-0.9,z:-2.6,s:0.5}],color:0xb3e5fc},
    {stones:[{x:6.1,z:1.2,s:0.7},{x:7.1,z:0,s:0.5}],color:0x80cbc4},
    {stones:[{x:10.9,z:-3.2,s:0.85},{x:11.9,z:-4.4,s:0.6},{x:9.9,z:-4.1,s:0.42}],color:0xa5d6a7}
  ];
  groups.forEach(g=>{
    const cx=g.stones.reduce((s,st)=>s+st.x,0)/g.stones.length;
    const cz=g.stones.reduce((s,st)=>s+st.z,0)/g.stones.length;
    const maxR=Math.max(...g.stones.map(st=>st.s));
    // 同心发光耙纹 (围绕石组)
    for(let r=maxR+0.4;r<maxR+2.2;r+=0.35){
      const ring=new THREE.Mesh(new THREE.RingGeometry(r,r+0.025,36),
        new THREE.MeshBasicMaterial({color:g.color,transparent:true,opacity:0.25,side:THREE.DoubleSide}));
      ring.rotation.x=-Math.PI/2;ring.position.set(cx,0.008,cz);scene.add(ring);
    }
    // 苔藓光环 (最内圈, 模拟苔藓)
    const moss=new THREE.Mesh(new THREE.RingGeometry(maxR+0.1,maxR+0.35,36),
      new THREE.MeshBasicMaterial({color:0x2d6a4f,transparent:true,opacity:0.1,side:THREE.DoubleSide}));
    moss.rotation.x=-Math.PI/2;moss.position.set(cx,0.007,cz);scene.add(moss);
    // 石头
    g.stones.forEach(st=>{
      const geo=new THREE.DodecahedronGeometry(st.s,1);
      const pos=geo.attributes.position;
      for(let i=0;i<pos.count;i++){
        pos.setY(i,pos.getY(i)*0.55+Math.random()*0.04);
        pos.setX(i,pos.getX(i)*(0.85+Math.random()*0.3));
      }
      geo.computeVertexNormals();
      const mesh=new THREE.Mesh(geo,new THREE.MeshPhysicalMaterial({
        color:0x151a24,emissive:g.color,emissiveIntensity:0.12,
        transparent:true,opacity:0.65,roughness:0.3,metalness:0.1,
        transmission:0.15,thickness:0.5}));
      mesh.position.set(st.x,st.s*0.28,st.z);mesh.castShadow=true;scene.add(mesh);
    });
    // 石组底部柔光
    const gl=new THREE.PointLight(g.color,0.1,4);gl.position.set(cx,0.3,cz);scene.add(gl);
  });

  // ── 土墙 (三面, 渐变土色, 致敬龙安寺油土墙) ──
  const wallMat=new THREE.MeshStandardMaterial({color:0x1a1510,roughness:0.95,emissive:0x1a1510,emissiveIntensity:0.05});
  const bWall=new THREE.Mesh(new THREE.BoxGeometry(gW+0.6,1.8,0.3),wallMat);
  bWall.position.set(0,0.9,-gD/2-0.15);scene.add(bWall);
  const lWall=new THREE.Mesh(new THREE.BoxGeometry(0.3,1.8,gD+0.6),wallMat);
  lWall.position.set(-gW/2-0.15,0.9,0);scene.add(lWall);
  const rWall=new THREE.Mesh(new THREE.BoxGeometry(0.3,1.8,gD+0.6),wallMat);
  rWall.position.set(gW/2+0.15,0.9,0);scene.add(rWall);
  // 墙顶发光线
  [bWall,lWall,rWall].forEach(w=>{
    const topLine=new THREE.Mesh(
      new THREE.BoxGeometry(w===bWall?gW+0.6:0.3,0.02,w===bWall?0.3:gD+0.6),
      new THREE.MeshBasicMaterial({color:0x334455,transparent:true,opacity:0.2}));
    topLine.position.copy(w.position);topLine.position.y=1.81;scene.add(topLine);
  });

  // ── 缘侧 (观赏平台, 前方) ──
  const veranda=new THREE.Mesh(new THREE.BoxGeometry(gW+1,0.15,2.5),
    new THREE.MeshStandardMaterial({color:0x151a20,roughness:0.7}));
  veranda.position.set(0,0.075,gD/2+1.25);scene.add(veranda);
  // 缘侧前缘发光
  const vEdge=new THREE.Mesh(new THREE.BoxGeometry(gW+1,0.015,0.04),
    new THREE.MeshBasicMaterial({color:0x4fc3f7,transparent:true,opacity:0.25}));
  vEdge.position.set(0,0.16,gD/2);scene.add(vEdge);

  // ── 蹲踞 (つくばい, 现代水钵) ──
  const basin=new THREE.Mesh(new THREE.CylinderGeometry(0.4,0.5,0.3,16),
    new THREE.MeshPhysicalMaterial({color:0x151a24,emissive:0x4fc3f7,emissiveIntensity:0.15,
      transparent:true,opacity:0.5,roughness:0.4}));
  basin.position.set(gW/2+1.5,0.15,gD/2+1);scene.add(basin);
  const bWater=new THREE.Mesh(new THREE.CircleGeometry(0.35,16),
    new THREE.MeshBasicMaterial({color:0x4fc3f7,transparent:true,opacity:0.12}));
  bWater.rotation.x=-Math.PI/2;bWater.position.set(gW/2+1.5,0.31,gD/2+1);scene.add(bWater);
  const bLight=new THREE.PointLight(0x4fc3f7,0.08,2);bLight.position.set(gW/2+1.5,0.5,gD/2+1);scene.add(bLight);

  // ── 月亮 & 星空 ──
  const moon=new THREE.Mesh(new THREE.SphereGeometry(0.9,16,16),
    new THREE.MeshPhongMaterial({color:0xFFF8E8,emissive:0xC49040,emissiveIntensity:0.2,transparent:true,opacity:0.38}));
  moon.position.set(-5,10,-4);scene.add(moon);
  scene.add(new THREE.PointLight(0xCC7700,0.8,35).translateY(10));
  for(let i=0;i<30;i++){
    const st=new THREE.Mesh(new THREE.SphereGeometry(0.025,4,4),
      new THREE.MeshBasicMaterial({color:0xffffff,transparent:true,opacity:0.4+Math.random()*0.6}));
    st.position.set((Math.random()-0.5)*24,6+Math.random()*7,(Math.random()-0.5)*20);scene.add(st);
  }

  // ── 智能体: 坐在缘侧, 面朝枯山水 ──
  const S=window.S;if(!S)return;
  const colors=['#22d3ee','#34d399','#a78bfa','#fbbf24','#f472b6','#60a5fa'];
  const visibleAgents=S.agents.filter(a=>S.selectedTeams&&S.selectedTeams.includes(a._teamId));
  const agents=visibleAgents.length?visibleAgents:S.agents;
  // 缘侧两侧 + 左右墙边，交错3排
  const rows=[
    {z:gD/2+1.8,baseY:0.15},   // 前排 (缘侧后方)
    {z:gD/2+0.7,baseY:0.15},   // 中排 (缘侧前缘)
    {z:gD/2+2.8,baseY:0.15}    // 后排
  ];
  agents.forEach((ag,i)=>{
    const row=rows[i%rows.length];
    const rowAgents=agents.filter((_,j)=>j%rows.length===i%rows.length);
    const idxInRow=Math.floor(i/rows.length);
    const totalW=gW-2;
    const x=-totalW/2+totalW*(idxInRow+0.5)/Math.max(rowAgents.length,1);
    const fig=createAgentFigure(ag.name||'Agent',colors[i%colors.length],false);
    fig.scale.set(0.45,0.45,0.45);
    fig.position.set(x,row.baseY,row.z);
    fig.userData.baseY=row.baseY;
    fig.lookAt(x,row.baseY,0); // 面朝庭園
    fig.userData.agentId=ag.agent_id;
    scene.add(fig);agentMeshes.push(fig);
  });
  document.getElementById('env-3d-info').textContent='◌ 休息区 · 枯山水 — '+agents.length+' 个智能体';
}

// ══════════════════════════════════════════════════
// 智能体交互脉冲 + 粒子弧线
// ══════════════════════════════════════════════════
const _pulseQueue=[];
const _arcParticles=[];

window.pulse3DAgent=function(fromName,toName){
  if(!initialized)return;
  const fromFig=agentMeshes.find(m=>m.userData.label===fromName);
  const toFig=agentMeshes.find(m=>m.userData.label===toName);
  // Pulse glow ring on sender
  if(fromFig&&fromFig.userData.glowRing){
    _pulseQueue.push({mesh:fromFig.userData.glowRing,start:clock.getElapsedTime(),dur:1.5});
  }
  // Create arc particles between agents
  if(fromFig&&toFig&&scene){
    const startPos=fromFig.position.clone().add(new THREE.Vector3(0,1.5,0));
    const endPos=toFig.position.clone().add(new THREE.Vector3(0,1.5,0));
    const mid=startPos.clone().lerp(endPos,0.5).add(new THREE.Vector3(0,2.5,0));
    const curve=new THREE.QuadraticBezierCurve3(startPos,mid,endPos);
    const pts=curve.getPoints(20);
    const geo=new THREE.BufferGeometry().setFromPoints(pts);
    const mat=new THREE.LineBasicMaterial({color:0x22d3ee,transparent:true,opacity:0.6});
    const line=new THREE.Line(geo,mat);
    scene.add(line);
    _arcParticles.push({line,start:clock.getElapsedTime(),dur:2.0});
  }
};

// ══════════════════════════════════════════════════
// 屏幕内容更新 & 任务交接动画
// ══════════════════════════════════════════════════
const _screenSprites={};

function makeScreenCanvas(lines,hexColor){
  const c=document.createElement('canvas');c.width=1024;c.height=256;
  const ctx=c.getContext('2d');
  // 带鱼屏深色背景 + 圆角
  ctx.fillStyle='rgba(6,10,18,0.92)';
  ctx.roundRect(2,2,1020,252,6);ctx.fill();
  // 顶部状态条 (更细更亮)
  ctx.fillStyle=hexColor||'#22d3ee';
  ctx.fillRect(8,8,1008,2);
  // 左侧竖条装饰
  ctx.fillStyle=(hexColor||'#22d3ee')+'44';
  ctx.fillRect(8,14,2,232);
  // monospace终端风格文本
  const textLines=Array.isArray(lines)?lines:[lines];
  ctx.font='bold 20px "SF Mono","Fira Code",monospace';
  textLines.forEach((l,i)=>{
    // $ 命令行用亮色, 其他用稍暗色
    if(l.startsWith('$')){
      ctx.fillStyle='#ffffff';
    } else if(l.startsWith('[OK]') || l.includes('✓') || l.includes('PASS')){
      ctx.fillStyle='#34d399';
    } else if(l.startsWith('[WARN]')){
      ctx.fillStyle='#fbbf24';
    } else if(l.startsWith('>')){
      ctx.fillStyle=(hexColor||'#22d3ee')+'cc';
    } else {
      ctx.fillStyle=hexColor||'#22d3ee';
    }
    ctx.fillText(l,20,36+i*28,980);
  });
  return c;
}

window._dt3dUpdateScreen=function(agentName,lines,hexColor){
  if(!initialized||!scene)return;
  const fig=agentMeshes.find(m=>m.userData.label===agentName);
  if(!fig||!fig.userData.screenPos)return;
  // Remove old sprite
  if(_screenSprites[agentName]){
    scene.remove(_screenSprites[agentName]);
    _screenSprites[agentName].material.map.dispose();
    _screenSprites[agentName].material.dispose();
  }
  const pos=fig.userData.screenPos;
  const canvas=makeScreenCanvas(lines,hexColor||'#22d3ee');
  const tex=new THREE.CanvasTexture(canvas);tex.minFilter=THREE.LinearFilter;
  const mat=new THREE.SpriteMaterial({map:tex,transparent:true,depthTest:false});
  const sprite=new THREE.Sprite(mat);
  sprite.position.copy(pos);
  sprite.scale.set(4.0,0.9,1);
  scene.add(sprite);
  _screenSprites[agentName]=sprite;
  // Flash the screen border
  if(fig.userData.screenLine){
    fig.userData.screenLine.material.opacity=1.0;
    setTimeout(()=>{if(fig.userData.screenLine)fig.userData.screenLine.material.opacity=0.8},600);
  }
};

window._dt3dClearScreens=function(){
  Object.keys(_screenSprites).forEach(name=>{
    if(_screenSprites[name]){
      scene.remove(_screenSprites[name]);
      _screenSprites[name].material.map.dispose();
      _screenSprites[name].material.dispose();
    }
  });
  Object.keys(_screenSprites).forEach(k=>delete _screenSprites[k]);
};

window._dt3dGetAgentNames=function(){
  return agentMeshes.map(m=>m.userData?.label).filter(Boolean);
};

// ── 发言气泡 (议事厅专用: 在发言agent头上浮出💬图标) ──
let _activeBubble=null;
window._dt3dSpeakerBubble=function(agentName,show){
  if(_activeBubble){scene.remove(_activeBubble);_activeBubble.material.map.dispose();_activeBubble.material.dispose();_activeBubble=null}
  if(!show||!agentName)return;
  const fig=agentMeshes.find(m=>m.userData.label===agentName);
  if(!fig)return;
  const c=document.createElement('canvas');c.width=64;c.height=64;
  const ctx=c.getContext('2d');ctx.font='48px serif';ctx.textAlign='center';ctx.textBaseline='middle';ctx.fillText('💬',32,32);
  const tex=new THREE.CanvasTexture(c);tex.minFilter=THREE.LinearFilter;
  const mat=new THREE.SpriteMaterial({map:tex,transparent:true,depthTest:false});
  const spr=new THREE.Sprite(mat);
  spr.position.copy(fig.position).add(new THREE.Vector3(0,4.2,0));
  spr.scale.set(1.2,1.2,1);
  scene.add(spr);_activeBubble=spr;
};

// ── PK火花 (演练场专用: 红蓝对抗时中心闪烁) ──
window._dt3dPKSpark=function(redName,blueName){
  const redFig=agentMeshes.find(m=>m.userData.label===redName);
  const blueFig=agentMeshes.find(m=>m.userData.label===blueName);
  if(!redFig||!blueFig)return;
  const mid=redFig.position.clone().lerp(blueFig.position,0.5).add(new THREE.Vector3(0,3,0));
  // 放射8个小球
  const sparkGroup=new THREE.Group();
  for(let i=0;i<8;i++){
    const angle=(i/8)*Math.PI*2;
    const col=i%2===0?0xf472b6:0x60a5fa;
    const dot=new THREE.Mesh(new THREE.SphereGeometry(0.12,6,6),new THREE.MeshBasicMaterial({color:col,transparent:true,opacity:1}));
    dot.position.set(Math.cos(angle)*0.3,Math.sin(angle)*0.3,0);
    sparkGroup.add(dot);
  }
  sparkGroup.position.copy(mid);scene.add(sparkGroup);
  const t0=clock.getElapsedTime();
  _arcParticles.push({line:sparkGroup,start:t0,dur:1.5,isGroup:true,isSpark:true});
};

window._dt3dHandoff=function(fromName,toName,taskLabel,color){
  if(!initialized)return;
  const fromFig=agentMeshes.find(m=>m.userData.label===fromName);
  const toFig=agentMeshes.find(m=>m.userData.label===toName);
  if(!fromFig||!toFig)return;
  const hexColor=color||'#fbbf24';
  const col=new THREE.Color(hexColor);
  const t0=clock.getElapsedTime();

  // ── 起点agent 整体闪烁弹跳 ──
  _pulseQueue.push({mesh:fromFig,start:t0,dur:1.5,type:'body'});
  if(fromFig.userData.glowRing){
    _pulseQueue.push({mesh:fromFig.userData.glowRing,start:t0,dur:2.0});
  }

  // ── 粗虚线弧 (分段小圆柱) ──
  const startPos=fromFig.position.clone().add(new THREE.Vector3(0,2.2,0));
  const endPos=toFig.position.clone().add(new THREE.Vector3(0,2.2,0));
  const mid=startPos.clone().lerp(endPos,0.5).add(new THREE.Vector3(0,4.5,0));
  const curve=new THREE.QuadraticBezierCurve3(startPos,mid,endPos);
  const totalPts=curve.getPoints(80);
  // 分段绘制: 每隔几个点画一段, 形成虚线
  const dashGroup=new THREE.Group();
  const segLen=4, gapLen=3; // 4个点一段, 3个点间隔
  for(let i=0;i<totalPts.length-1;i++){
    const inDash=(i%(segLen+gapLen))<segLen;
    if(!inDash)continue;
    const p1=totalPts[i],p2=totalPts[i+1];
    const dir2=p2.clone().sub(p1);
    const len=dir2.length();
    if(len<0.001)continue;
    const cyl=new THREE.Mesh(
      new THREE.CylinderGeometry(0.08,0.08,len,4,1),
      new THREE.MeshBasicMaterial({color:col,transparent:true,opacity:0.9})
    );
    cyl.position.copy(p1).add(dir2.clone().multiplyScalar(0.5));
    cyl.quaternion.setFromUnitVectors(new THREE.Vector3(0,1,0),dir2.normalize());
    dashGroup.add(cyl);
  }
  scene.add(dashGroup);
  _arcParticles.push({line:dashGroup,start:t0,dur:3.5,isGroup:true});

  // ── 沿弧线飞行的光球粒子 (3个, 间隔出发) ──
  for(let pi=0;pi<3;pi++){
    const sphere=new THREE.Mesh(
      new THREE.SphereGeometry(0.15,8,8),
      new THREE.MeshBasicMaterial({color:0xffffff,transparent:true,opacity:1})
    );
    sphere.position.copy(startPos);
    scene.add(sphere);
    _arcParticles.push({line:sphere,start:t0+pi*0.4,dur:1.8,curve:curve,isTraveler:true});
  }

  // Task label
  if(taskLabel){
    const labelCanvas=makeColorLabel(taskLabel,hexColor);
    const labelTex=new THREE.CanvasTexture(labelCanvas);labelTex.minFilter=THREE.LinearFilter;
    const labelSprite=new THREE.Sprite(new THREE.SpriteMaterial({map:labelTex,transparent:true,depthTest:false}));
    labelSprite.position.copy(mid);
    labelSprite.scale.set(2.5,0.65,1);
    scene.add(labelSprite);
    setTimeout(()=>{scene.remove(labelSprite);labelSprite.material.map.dispose();labelSprite.material.dispose()},3500);
  }

  // ── 终点agent 闪烁弹跳 (延迟) + 摄像机摇过去 ──
  setTimeout(()=>{
    _pulseQueue.push({mesh:toFig,start:clock.getElapsedTime(),dur:1.5,type:'body'});
    if(toFig.userData.glowRing){
      _pulseQueue.push({mesh:toFig.userData.glowRing,start:clock.getElapsedTime(),dur:2.0});
    }
    if(window._dt3dFocusByName) window._dt3dFocusByName(toName);
  },800);
};

// ── 奖励浮卡：在「对应 agent」头顶弹出 +value，上升淡出（直观，居中投射到该 agent）──
window._dt3dRewardPop=function(agentName, reward, idx){
  if(!initialized || !agentMeshes.length) return;
  let fig = agentName ? agentMeshes.find(m=>m.userData.label===agentName) : null;
  if(!fig && typeof idx==='number') fig = agentMeshes[idx % agentMeshes.length];
  if(!fig) fig = agentMeshes[Math.floor(Math.random()*agentMeshes.length)];
  const r = Number(reward)||0;
  const positive = r>=0;
  const mag = Math.min(Math.abs(r),1);
  const hex = positive ? (mag>0.4?'#34d399':'#a3e635') : '#f87171';
  const txt = (positive?'+':'')+r.toFixed(2);
  const tex = new THREE.CanvasTexture(makeColorLabel(txt,hex)); tex.minFilter=THREE.LinearFilter;
  const sp = new THREE.Sprite(new THREE.SpriteMaterial({map:tex,transparent:true,depthTest:false}));
  const baseY = fig.position.y + 2.6;
  sp.position.set(fig.position.x, baseY, fig.position.z);
  const s = 1.1 + mag*0.9; sp.scale.set(1.7*s,0.5*s,1);
  scene.add(sp);
  // 头顶脉冲，强化「这次奖励属于这个 agent」
  _pulseQueue.push({mesh:fig, start:clock.getElapsedTime(), dur:1.0, type:'body'});
  if(fig.userData.glowRing) _pulseQueue.push({mesh:fig.userData.glowRing, start:clock.getElapsedTime(), dur:1.4});
  // 自包含上升+淡出（不依赖主循环）
  const t0 = performance.now();
  (function _anim(){
    const k = (performance.now()-t0)/1300;
    if(k>=1){ scene.remove(sp); try{sp.material.map.dispose();sp.material.dispose();}catch(e){} return; }
    sp.position.y = baseY + k*1.8;
    sp.material.opacity = 1 - k*k;
    requestAnimationFrame(_anim);
  })();
};

// ══════════════════════════════════════════════════
// 动画循环
// ── 仿真运行时场景地面脉冲环 ──
let _simPulseRing=null;
const _roomThemeColor={council:'#22d3ee',extraction:'#34d399',workshop:'#fbbf24',library:'#a78bfa',arena:'#f472b6',rest:'#60a5fa'};
function _updateSimPulseRing(t){
  const running=window._secsSimRunning;
  if(running&&!_simPulseRing){
    const col=new THREE.Color(_roomThemeColor[currentRoom]||'#22d3ee');
    const ring=new THREE.Mesh(new THREE.RingGeometry(5,5.3,64),
      new THREE.MeshBasicMaterial({color:col,transparent:true,opacity:0,side:THREE.DoubleSide}));
    ring.rotation.x=-Math.PI/2;ring.position.y=0.02;
    scene.add(ring);_simPulseRing=ring;
  } else if(!running&&_simPulseRing){
    scene.remove(_simPulseRing);_simPulseRing.geometry.dispose();_simPulseRing.material.dispose();_simPulseRing=null;
  }
  if(_simPulseRing){
    const pulse=Math.sin(t*2)*0.5+0.5;
    _simPulseRing.material.opacity=0.08+pulse*0.18;
    const s=1+pulse*0.15;
    _simPulseRing.scale.set(s,s,1);
  }
}

// ══════════════════════════════════════════════════
function animate(){
  requestAnimationFrame(animate);
  if(!controls||!renderer)return;
  const t=clock.getElapsedTime();
  _updateSimPulseRing(t);
  // 相机平滑过渡
  if(_camGoal){camera.position.lerp(_camGoal,0.04);if(camera.position.distanceTo(_camGoal)<0.02){camera.position.copy(_camGoal);_camGoal=null}}
  if(_tgtGoal){controls.target.lerp(_tgtGoal,0.04);if(controls.target.distanceTo(_tgtGoal)<0.02){controls.target.copy(_tgtGoal);_tgtGoal=null}}
  controls.update();
  // 浮尘飘动
  if(dustMesh){const p=dustMesh.geometry.attributes.position.array;
    for(let i=0;i<p.length;i+=3){p[i+1]+=Math.sin(t*0.3+i)*0.002;if(p[i+1]>12)p[i+1]=0}
    dustMesh.geometry.attributes.position.needsUpdate=true}
  // 智能体轻微浮动 (基于 baseY 做相对偏移)
  agentMeshes.forEach((fig,i)=>{fig.position.y=(fig.userData.baseY||0)+Math.sin(t*0.8+i)*0.04});
  // 萃取漏斗旋转
  scene.children.forEach(c=>{if(c.userData&&c.userData.spin)c.rotation.y=t*0.5});
  // 菌丝脉动
  if(myceliumGroup){const wave=Math.sin(t*0.6)*0.5+0.5;
    myceliumGroup.children.forEach(m=>{if(m.material)m.material.opacity=0.05+wave*0.12})}
  // 交互脉冲动画
  for(let i=_pulseQueue.length-1;i>=0;i--){
    const p=_pulseQueue[i];const elapsed=t-p.start;
    if(elapsed>p.dur){
      if(p.type==='body'){
        // 复位进化光圈（回到底座、隐藏）
        const ring=p.mesh.userData&&p.mesh.userData.ascendRing;
        if(ring){ring.material.opacity=0;ring.position.y=(p.mesh.userData.ascendBaseY||0.06);ring.scale.set(1,1,1);}
      }
      else{p.mesh.material.opacity=0.22;p.mesh.scale.setScalar(1)}
      _pulseQueue.splice(i,1);continue;
    }
    const wave=Math.sin(elapsed/p.dur*Math.PI);
    if(p.type==='body'){
      // 破茧成蝶：一道光环分步从底座升到头部、到顶张开淡出（取代整体放大缩小，体现跃迁/演化）
      const ring=p.mesh.userData&&p.mesh.userData.ascendRing;
      if(ring){
        const N=14;                                          // 行程离散成的步数（"计算好步数"）
        const sp=Math.floor((elapsed/p.dur)*N)/(N-1);        // 0..1 按步推进
        const baseY=p.mesh.userData.ascendBaseY||0.06, headY=p.mesh.userData.ascendHeadY||2.0;
        ring.position.y=baseY+sp*(headY-baseY);
        const grow=1+sp*0.9; ring.scale.set(grow,grow,1);    // 上升时张开（到顶破茧）
        ring.material.opacity=0.6*Math.sin(sp*Math.PI);      // 底淡入→中段最亮→顶淡出
      }
    } else {
      p.mesh.material.opacity=0.22+0.6*wave;
      p.mesh.scale.setScalar(1+0.4*wave);
    }
  }
  // 弧线粒子消退
  for(let i=_arcParticles.length-1;i>=0;i--){
    const a=_arcParticles[i];const elapsed=t-a.start;
    if(elapsed<0)continue; // 尚未开始 (延迟粒子)
    if(elapsed>a.dur){
      if(a.isGroup){
        a.line.children.forEach(c=>{c.geometry.dispose();c.material.dispose()});
        scene.remove(a.line);
      } else {
        scene.remove(a.line);a.line.geometry.dispose();
        if(a.line.material)a.line.material.dispose();
      }
      _arcParticles.splice(i,1);continue;
    }
    // 飞行粒子: 沿曲线移动
    if(a.isTraveler&&a.curve){
      const progress=elapsed/a.dur;
      const pos=a.curve.getPoint(Math.min(progress,1));
      a.line.position.copy(pos);
      a.line.material.opacity=1-progress*0.5;
      a.line.scale.setScalar(1+Math.sin(progress*Math.PI)*0.5);
    }
    // 虚线段组: 整体淡出
    else if(a.isGroup){
      const fade=1-elapsed/a.dur;
      if(a.isSpark){
        // PK火花: 向外扩散
        const expand=1+elapsed/a.dur*3;
        a.line.scale.set(expand,expand,expand);
      }
      a.line.children.forEach(c=>{if(c.material)c.material.opacity=0.9*fade});
    }
    // 普通线: 淡出
    else {
      if(a.line.material)a.line.material.opacity=0.85*(1-elapsed/a.dur);
    }
  }
  renderer.render(scene,camera);
}

// ══════════════════════════════════════════════════
// 暴露给全局调用
// ══════════════════════════════════════════════════
window._dt3dBuildRoom=function(roomId){
  if(!initialized){initScene();setTimeout(()=>buildRoom(roomId),100)}
  else buildRoom(roomId);
};
window._dt3dSetCamera=function(px,py,pz,tx,ty,tz){
  if(!camera||!controls)return;
  _camGoal=new THREE.Vector3(px,py,pz);_tgtGoal=new THREE.Vector3(tx,ty,tz);
};
window._dt3dFocusAgent=function(agentId){
  const fig=agentMeshes.find(m=>m.userData.agentId===agentId);
  if(!fig||!camera)return;
  const pos=fig.position.clone();
  _camGoal=new THREE.Vector3(pos.x*1.5,6,pos.z*1.5+8);
  _tgtGoal=pos.clone().add(new THREE.Vector3(0,1.5,0));
};

// 按名字聚焦agent (摄像机平滑摇到该agent的屏幕前)
window._dt3dFocusByName=function(agentName){
  const fig=agentMeshes.find(m=>m.userData.label===agentName);
  if(!fig||!camera)return;
  const screenPos=fig.userData.screenPos;
  if(screenPos){
    // 摄像机在屏幕正前方偏上, 看向屏幕中心
    const dir=screenPos.clone().normalize();
    _camGoal=screenPos.clone().add(dir.multiplyScalar(3)).add(new THREE.Vector3(0,1.5,0));
    _tgtGoal=screenPos.clone();
  } else {
    const pos=fig.position.clone();
    _camGoal=new THREE.Vector3(pos.x*1.4,4,pos.z*1.4+6);
    _tgtGoal=pos.clone().add(new THREE.Vector3(0,1.8,0));
  }
};

// 全景视角: 拉远摄像机看到所有agent
window._dt3dOverview=function(){
  if(!camera)return;
  _camGoal=new THREE.Vector3(0,18,22);
  _tgtGoal=new THREE.Vector3(0,2,0);
};

// 首次进入环境空间时初始化
const observer=new MutationObserver(()=>{
  const panel=document.getElementById('view-environment');
  if(panel&&panel.classList.contains('active')&&!initialized){
    setTimeout(initScene,100);observer.disconnect();
  }
});
observer.observe(document.body,{subtree:true,attributes:true,attributeFilter:['class']});


