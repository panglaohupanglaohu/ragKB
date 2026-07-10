/**
 * voice-config-validator.js — 语音配置校验纯函数（可测试，无 DOM 依赖）
 * 设计原则：页面配置是唯一真相源，缺字段直接报错暴露问题，不设兜底默认值。
 */
export const REQUIRED_BROWSER_FIELDS = ['lang', 'rate', 'pitch', 'volume', 'preferred_voice', 'timeout_sec'];

/**
 * 校验 voice 配置，返回 { ok, error }。
 * - ok=true: 配置可用，caller 应继续播放
 * - ok=false: 配置缺字段或不合法，error 含可读原因；caller 应 console.error 并返回
 */
export function validateVoiceConfig(vc) {
  if (!vc) {
    return { ok: false, error: 'voice config missing — 请在 /pet-config.html 页面配置 voice 字段' };
  }
  if (!vc.provider) {
    return { ok: false, error: 'voice.provider missing — 请在 /pet-config.html 页面选择 TTS 引擎' };
  }
  if (vc.provider === 'edge-tts') {
    if (!vc.edge_voice) {
      return { ok: false, error: 'voice.edge_voice missing for edge-tts — 请在 /pet-config.html 页面选择 Edge 神经语音' };
    }
    return { ok: true };
  }
  if (vc.provider === 'gpt-sovits') {
    return { ok: true };
  }
  if (vc.provider === 'browser') {
    const missing = REQUIRED_BROWSER_FIELDS.filter(
      k => vc[k] === undefined || vc[k] === null || vc[k] === ''
    );
    if (missing.length) {
      return { ok: false, error: `voice config missing fields: ${missing.join(', ')} — 请在 /pet-config.html 页面补全` };
    }
    return { ok: true };
  }
  return { ok: false, error: `unknown voice.provider "${vc.provider}" — 请在 /pet-config.html 页面选择合法引擎` };
}
