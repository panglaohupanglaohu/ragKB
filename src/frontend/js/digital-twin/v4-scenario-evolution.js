/**
 * AgentsGroup2026 — v4 场景化演练 × 技能进化 (Bootstrap)
 * D-0.1 状态收敛 + 加载场景/进化模块。
 * 加载顺序: secs-core.js → director.js → v4-scenarios.js → v4-evolution.js
 */

// ── D-0.1: _sx 扩展为唯一真源 + _currentSessionId 降级为别名 ──
(function(){
  if (!window._sx) return;
  var sx = window._sx;
  sx.scenarioId = sx.scenarioId || '';
  sx.scenarioSpec = sx.scenarioSpec || null;
  sx.generation = sx.generation || 0;
  sx.parentTrialId = sx.parentTrialId || '';
  sx.skillStats = sx.skillStats || null;
  sx.evolutionRunId = sx.evolutionRunId || null;
  try {
    var legacy = window._currentSessionId;
    if (legacy !== undefined && legacy !== null) sx.sessionId = sx.sessionId || legacy;
    delete window._currentSessionId;
    var warned = false;
    Object.defineProperty(window, '_currentSessionId', {
      get: function(){
        if (!warned) { console.warn('[DT][deprecated] _currentSessionId 已是 _sx.sessionId 的别名'); warned = true; }
        return sx.sessionId;
      },
      set: function(v){ sx.sessionId = v; },
      configurable: true
    });
  } catch(e) { console.warn('[DT] _currentSessionId 别名化失败(不影响功能):', e); }
})();
