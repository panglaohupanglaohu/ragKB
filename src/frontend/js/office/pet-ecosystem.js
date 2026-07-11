/**
 * pet-ecosystem.js — 宠物生态前端管理器
 * 从后端加载 pet_config，用 PetFactory 构建模型，用 PetBehavior 驱动行为。
 * 替代 office-scene.js 中硬编码的 buildCat/buildMouse/猫鼠动画。
 * 
 * 用法:
 *   import { PetEcosystem } from './pet-ecosystem.js';
 *   const eco = new PetEcosystem(scene, makeLabel);
 *   await eco.init();
 *   eco.step(dt, t);  // 每帧调用
 *   eco.pick(raycaster, camera, mouse);  // 点击拾取
 */
import { buildPet } from './pet-factory.js';
import { createBehavior } from './pet-behavior.js';

export class PetEcosystem {
  constructor(scene, makeLabel) {
    this.scene = scene;
    this.makeLabel = makeLabel;
    this.pets = {};        // id → { group, parts, drawBubble, behavior, config }
    this.config = null;
    this._catSpeakCooldown = 0;
    this._catBubbleHold = 0;
  }

  async init() {
    try {
      const r = await fetch('/api/v1/pet-ecosystem/config');
      this.config = await r.json();
    } catch (e) {
      console.warn('[PetEcosystem] config load failed, using defaults', e);
      return;
    }
    this._buildAll();
  }

  _buildAll() {
    // 清理旧的
    for (const pet of Object.values(this.pets)) {
      this.scene.remove(pet.group);
    }
    this.pets = {};

    // 构建所有宠物
    for (const petConfig of (this.config.pets || [])) {
      // 归一 role：后端未回填 / 配置缺失时按 chase_targets 推断。
      // 必须在此写回 config.role，否则跨宠物查找(nearestByRole/selectPrey 读 p.config.role)失效
      if (!petConfig.role) {
        const hasChase = ((petConfig.behavior && petConfig.behavior.chase_targets) || []).length > 0;
        petConfig.role = hasChase ? 'predator' : 'prey';
      }
      const pet = buildPet(petConfig, this.makeLabel);
      const route = (petConfig.behavior && petConfig.behavior.route) || [[0, 0]];
      pet.group.position.set(route[0][0], 0, route[0][1]);
      this.scene.add(pet.group);
      
      // 创建行为
      pet.behavior = createBehavior(pet, petConfig, {});
      pet.config = petConfig;
      this.pets[petConfig.id] = pet;
    }

    // 捕食者：发现猎物念台词(onDetect) + 捕获猎物得意(onCatch) + 猎物 respawn
    for (const pet of Object.values(this.pets)) {
      const beh = pet.config.behavior || {};
      const isPredator = pet.config.role === 'predator'
        || ((beh.chase_targets || []).length > 0);
      if (!isPredator) continue;
      const canSpeak = pet.config.speak && pet.config.speak.provider === 'llm';
      if (canSpeak) {
        pet.behavior.onDetect = (predator, prey) => {
          if (!prey) return;
          this._onPetDetect(predator, prey, { context: `发现了${prey.config.name}，准备抓捕！` });
        };
      }
      pet.behavior.onCatch = (predator, prey) => {
        this._onCatch(predator, prey);
      };
    }
  }

  // 捕获：猎物瞬移远角 + 恐惧/追捕状态清零 + 捕食者得意台词/TTS
  _onCatch(predator, prey) {
    const route = (prey.config.behavior && prey.config.behavior.route) || [];
    if (route.length) {
      let best = 0, bd = -1;
      for (let i = 0; i < route.length; i++) {
        const d = Math.hypot(
          route[i][0] - predator.group.position.x,
          route[i][1] - predator.group.position.z,
        );
        if (d > bd) { bd = d; best = i; }
      }
      prey.group.position.set(route[best][0], 0, route[best][1]);
      if (prey.behavior && prey.behavior.state) {
        prey.behavior.state.waypoint = best;
        prey.behavior.state.fear = 0;
        prey.behavior.state.intention = 'wander';
        prey.behavior.state.dwell = 1.0;
      }
    }
    if (predator.config.speak && predator.config.speak.provider === 'llm') {
      this._onPetDetect(predator, prey, { context: `抓到了${prey.config.name}，得意洋洋`, force: true });
    }
  }

  step(dt, t) {
    const ctx = {
      allPets: this.pets,
      onDetect: null, // 每个 pet 有自己的 onDetect
    };
    
    for (const pet of Object.values(this.pets)) {
      const petCtx = {
        allPets: this.pets,
        onDetect: pet.behavior.onDetect,
      };
      pet.behavior.step(dt, t, petCtx);
    }
  }

  pick(raycaster, camera, mouse) {
    const meshes = [];
    const petMap = {};  // mesh → { pet, config }
    
    for (const [id, pet] of Object.entries(this.pets)) {
      pet.group.traverse(o => {
        if (o.isMesh) {
          o.userData._petId = id;
          meshes.push(o);
        }
      });
    }
    
    const hits = raycaster.intersectObjects(meshes, false);
    if (hits.length === 0) return null;
    
    const hit = hits[0].object;
    const petId = hit.userData._petId;
    if (!petId) return null;
    
    return { petId, pet: this.pets[petId], config: this.pets[petId].config };
  }

  // bug-050: 猫台词净化——后端 LLM 降级时会返回大段中文系统文案
  // （"我是 AgentsGroup2026 智能体…收到您的消息…LLM 未连接"），
  // 旧版后端会把它原样传回。无论后端新旧，前端一律拦截并换 Mei Ling 风格短句，
  // 保证气泡与 TTS 永远是"一句台词"而不是系统日志。
  static sanitizeCatReply(reply, fallback) {
    const text = String(reply || '').trim();
    const degraded = !text
      || /收到您的消息|LLM 未连接|AgentsGroup2026 智能体|快速配置|DEEPSEEK_API_KEY/.test(text)
      || text.length > 120;
    if (!degraded) return text;
    const proverbs = [
      'A journey of a thousand miles begins with a single step.',
      'Even the smallest light can pierce the darkness.',
      'A bird does not sing because it has an answer. It sings because it has a song.',
      'Fall seven times, stand up eight.',
      'Still waters run deep.',
    ];
    return fallback || proverbs[Math.floor(Math.random() * proverbs.length)];
  }

  async _onPetDetect(detectingPet, target, opts = {}) {
    const config = detectingPet.config;
    const speak = config.speak || {};

    if (speak.provider !== 'llm') return;
    // 捕获得意(force)跳过冷却；其余受冷却限制
    if (!opts.force && this._catSpeakCooldown > Date.now()) return;
    this._catSpeakCooldown = Date.now() + (speak.cooldown_sec || 10) * 1000;

    // 占位
    this._catBubbleHold = Date.now() + 10000;
    detectingPet.drawBubble('🐱 喵…（思索中）');

    const speakAloud = (text) => {
      // 实时 TTS：路由到 OfficeAPI.onCatComment → catSpeak（浏览器 SpeechSynthesis / 后端 TTS）
      if (window.OfficeAPI && window.OfficeAPI.onCatComment) {
        window.OfficeAPI.onCatComment(text, config.voice);
      }
    };

    try {
      const doFetch = (typeof window._af === 'function') ? window._af : (window._agFetch || fetch);
      const context = opts.context || `Pet ${config.name} detected ${target ? target.config.name : ''}`;
      let r = await doFetch('/api/v1/agent-config/llm/cat-speak', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ context }),
      });
      // 403 → CSRF token 失效，刷新后重试一次
      if (r.status === 403 && typeof window._csrfReset === 'function') {
        await window._csrfReset();
        r = await doFetch('/api/v1/agent-config/llm/cat-speak', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ context }),
        });
      }
      const d = await r.json();
      // bug-051 诊断：HTTP 状态与服务端 error 一律进 console，猫哑巴时看这里
      if (!r.ok || (d && d.error)) console.warn('[cat-speak] HTTP', r.status, 'error:', d && (d.error || d.detail));
      // bug-050: 无论后端新旧，降级文案一律拦截净化
      const reply = PetEcosystem.sanitizeCatReply(d && d.reply, speak.fallback);
      this._catBubbleHold = Date.now() + 10000;
      detectingPet.drawBubble('🐱 ' + reply);
      speakAloud(reply);
    } catch (e) {
      console.error('[PetEcosystem] speak failed:', e);
      const fb = speak.fallback || '喵~';
      detectingPet.drawBubble('🐱 ' + fb);
      speakAloud(fb);
    }
  }

  dispose() {
    for (const pet of Object.values(this.pets)) {
      this.scene.remove(pet.group);
    }
    this.pets = {};
  }
}
