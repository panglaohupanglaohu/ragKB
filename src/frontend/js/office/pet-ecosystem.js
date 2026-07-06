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
      const pet = buildPet(petConfig, this.makeLabel);
      const route = (petConfig.behavior && petConfig.behavior.route) || [[0, 0]];
      pet.group.position.set(route[0][0], 0, route[0][1]);
      this.scene.add(pet.group);
      
      // 创建行为
      pet.behavior = createBehavior(pet, petConfig, {});
      pet.config = petConfig;
      this.pets[petConfig.id] = pet;
    }

    // 设置 onDetect 回调（猫发现老鼠时念台词）
    for (const pet of Object.values(this.pets)) {
      const chaseTargets = (pet.config.behavior && pet.config.behavior.chase_targets) || [];
      if (chaseTargets.length > 0 && pet.config.speak && pet.config.speak.provider === 'llm') {
        pet.behavior.onDetect = (detectingPet, target) => {
          this._onPetDetect(detectingPet, target);
        };
      }
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

  async _onPetDetect(detectingPet, target) {
    const config = detectingPet.config;
    const speak = config.speak || {};
    
    if (speak.provider !== 'llm') return;
    if (this._catSpeakCooldown > Date.now()) return;
    this._catSpeakCooldown = Date.now() + (speak.cooldown_sec || 10) * 1000;
    
    // 占位
    this._catBubbleHold = Date.now() + 10000;
    detectingPet.drawBubble('🐱 喵…（思索中）');
    
    try {
      const doFetch = (typeof window._af === 'function') ? window._af : (window._agFetch || fetch);
      const r = await doFetch('/api/v1/agent-config/llm/cat-speak', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ context: `Pet ${config.name} detected ${target.config.name}` }),
      });
      const d = await r.json();
      if (d && d.reply) {
        this._catBubbleHold = Date.now() + 10000;
        detectingPet.drawBubble('🐱 ' + d.reply);
        // TTS
        if (window.OfficeAPI && window.OfficeAPI.onCatComment) {
          window.OfficeAPI.onCatComment(d.reply, config.voice);
        }
      } else {
        detectingPet.drawBubble('🐱 ' + (speak.fallback || '喵~'));
      }
    } catch (e) {
      console.error('[PetEcosystem] speak failed:', e);
      detectingPet.drawBubble('🐱 ' + (speak.fallback || '喵~'));
    }
  }

  dispose() {
    for (const pet of Object.values(this.pets)) {
      this.scene.remove(pet.group);
    }
    this.pets = {};
  }
}
