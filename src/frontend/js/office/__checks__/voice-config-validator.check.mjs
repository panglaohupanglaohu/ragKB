/**
 * voice-config-validator.check.mjs — voice-config-validator.js 自检（node 原生 assert，无框架）
 * 覆盖：缺 voice config / 缺 provider / edge-tts 缺 edge_voice / browser 缺字段 / 未知 provider / 正常配置
 * 运行: node src/frontend/js/office/__checks__/voice-config-validator.check.mjs
 */
import assert from 'node:assert/strict';
import { validateVoiceConfig, REQUIRED_BROWSER_FIELDS } from '../voice-config-validator.js';

// ── 1. 缺 voice config ──
assert.equal(validateVoiceConfig(null).ok, false, 'null vc 应失败');
assert.equal(validateVoiceConfig(undefined).ok, false, 'undefined vc 应失败');
assert.match(validateVoiceConfig(null).error, /voice config missing/);

// ── 2. 缺 provider ──
const noProvider = { lang: 'zh-CN', rate: 1.1 };
assert.equal(validateVoiceConfig(noProvider).ok, false, '缺 provider 应失败');
assert.match(validateVoiceConfig(noProvider).error, /voice\.provider missing/);

// ── 3. edge-tts 缺 edge_voice ──
const edgeNoVoice = { provider: 'edge-tts' };
assert.equal(validateVoiceConfig(edgeNoVoice).ok, false, 'edge-tts 缺 edge_voice 应失败');
assert.match(validateVoiceConfig(edgeNoVoice).error, /edge_voice missing/);

// ── 4. edge-tts 正常 ──
const edgeOk = { provider: 'edge-tts', edge_voice: 'zh-CN-YunjianNeural' };
assert.equal(validateVoiceConfig(edgeOk).ok, true, 'edge-tts 配置齐全应通过');

// ── 5. browser 缺字段 ──
const browserMissing = { provider: 'browser', lang: 'zh-CN' };
const r = validateVoiceConfig(browserMissing);
assert.equal(r.ok, false, 'browser 缺字段应失败');
assert.match(r.error, /missing fields/);
// 缺的字段应被列出
assert.match(r.error, /rate/);
assert.match(r.error, /pitch/);
assert.match(r.error, /preferred_voice/);

// ── 6. browser 字段值为空字符串也算缺 ──
const browserEmpty = { provider: 'browser', lang: '', rate: 1.1, pitch: 1.8, volume: 0.9, preferred_voice: 'X', timeout_sec: 15 };
assert.equal(validateVoiceConfig(browserEmpty).ok, false, 'lang="" 应判为缺字段');

// ── 7. browser 正常 ──
const browserOk = { provider: 'browser', lang: 'zh-CN', rate: 1.1, pitch: 1.8, volume: 0.9, preferred_voice: '婷婷', timeout_sec: 15 };
assert.equal(validateVoiceConfig(browserOk).ok, true, 'browser 字段齐全应通过');

// ── 8. gpt-sovits 不强制要求字段（由后端处理）──
const sovitsOk = { provider: 'gpt-sovits' };
assert.equal(validateVoiceConfig(sovitsOk).ok, true, 'gpt-sovits 最小配置应通过');

// ── 9. 未知 provider ──
const unknown = { provider: 'azure-tts' };
const ru = validateVoiceConfig(unknown);
assert.equal(ru.ok, false, '未知 provider 应失败');
assert.match(ru.error, /unknown voice\.provider/);

// ── 10. REQUIRED_BROWSER_FIELDS 完整性 ──
assert.deepEqual(REQUIRED_BROWSER_FIELDS, ['lang', 'rate', 'pitch', 'volume', 'preferred_voice', 'timeout_sec']);

console.log('✅ voice-config-validator.check.mjs — ALL PASS');
