(function () {
  'use strict';

  var BASE = '/api/v1/evidence-runs';

  function cleanParams(params) {
    var query = new URLSearchParams();
    Object.keys(params || {}).forEach(function (key) {
      var value = params[key];
      if (value === undefined || value === null || value === '') return;
      query.set(key, String(value));
    });
    return query.toString();
  }

  async function request(path) {
    if (window.api && typeof window.api.request === 'function') {
      return window.api.request(path);
    }
    var response = await fetch(path, { credentials: 'same-origin' });
    if (!response.ok) return null;
    return response.json();
  }

  function normalizeList(payload) {
    if (!payload) return [];
    if (Array.isArray(payload)) return payload;
    return payload.evidence_runs || payload.items || [];
  }

  function list(filters) {
    var qs = cleanParams(filters || {});
    return request(BASE + (qs ? '?' + qs : '')).then(function (payload) {
      return normalizeList(payload);
    });
  }

  function byObject(entityType, entityId, options) {
    var qs = cleanParams({
      limit: (options && options.limit) || 50,
      offset: (options && options.offset) || 0,
    });
    var path = BASE + '/by-object/' + encodeURIComponent(entityType) + '/' + encodeURIComponent(entityId);
    return request(path + (qs ? '?' + qs : '')).then(function (payload) {
      return normalizeList(payload);
    });
  }

  function latestForObject(entityType, entityId) {
    return byObject(entityType, entityId, { limit: 1 }).then(function (runs) {
      return runs[0] || null;
    });
  }

  function get(evidenceId) {
    return request(BASE + '/' + encodeURIComponent(evidenceId)).then(function (payload) {
      return payload && (payload.evidence || payload);
    });
  }

  function statusTone(status) {
    status = String(status || '').toLowerCase();
    if (status === 'passed' || status === 'verified') return 'good';
    if (status === 'warning' || status === 'pending') return 'warn';
    if (status === 'blocked' || status === 'failed') return 'bad';
    return 'muted';
  }

  function summarize(run) {
    run = run || {};
    var runtime = run.runtime || {};
    return {
      id: run.evidence_id || '',
      type: run.evidence_type || '',
      status: run.status || '',
      tone: statusTone(run.status),
      createdAt: run.created_at || '',
      summary: run.summary || '',
      runtimeLabel: [runtime.mode, runtime.component || runtime.tool_name].filter(Boolean).join(' / '),
      command: run.command || '',
      exitCode: run.exit_code,
      artifact: run.artifact_dir || '',
      requestId: run.request_id || '',
      objectIds: {
        teamId: run.team_id || '',
        agentId: run.agent_id || '',
        skillId: run.skill_id || '',
        taskId: run.task_id || '',
        evolutionItemId: run.evolution_item_id || '',
        costTargetId: run.cost_target_id || '',
        plazaTopicId: run.plaza_topic_id || '',
      },
    };
  }

  window.evidenceRuns = {
    list: list,
    byObject: byObject,
    latestForObject: latestForObject,
    get: get,
    summarize: summarize,
    statusTone: statusTone,
  };
})();
