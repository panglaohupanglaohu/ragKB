import { readFileSync } from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import { describe, expect, it } from 'vitest';

function read(relPath) {
  return readFileSync(path.join(process.cwd(), relPath), 'utf8');
}

describe('frontendBigChange TODO smoke coverage', () => {
  it('keeps sandbox collab graph fallback and self-heal hooks wired', () => {
    const source = read('src/frontend/js/sandbox-twin.js');
    expect(source).toContain('function renderCollabGraph(roles)');
    expect(source).toContain('function _renderCollabGraphInner(roles)');
    expect(source).toContain("console.error('[collab] 协作图渲染异常:'");
    expect(source).toContain('_renderCollabGraphInner(AGENT_ROLES); return;');
    expect(source).toContain('协作图渲染失败:');
    expect(source).toContain('window._collabSelfHealTimer');
    expect(source).toContain('window._collabGraphHealth = function ()');
    expect(source).toContain('function formatApiError(err, fallback)');
    expect(source).toContain('Array.isArray(err.detail)');
    expect(source).toContain('async function resolveExerciseTeamId()');
    expect(source).toContain("return exerciseState.teamId || 'build_system';");
    expect(source).not.toContain("team_id: 'default'");
    expect(source).toContain('function bootSandboxTwin()');
    expect(source).toContain('window._sandboxTwinBoot = bootSandboxTwin;');
    expect(source).toContain("window.addEventListener('DOMContentLoaded', bootSandboxTwin);");
    expect(source).toContain("console.warn('[collab] 检测到协作图为空，自愈重画')");
    expect(source).toContain('rebuildCollabGraphFromRoles(currentRoleMap)');
    expect(source).toContain('}, 5000);');
  });

  it('keeps sandbox SSE step data connected to the collaboration graph', () => {
    const source = read('src/frontend/js/sandbox-twin.js');
    expect(source).toContain("eventSource = new EventSource(API + '/sessions/' + sessionId + '/stream')");
    expect(source).toContain("if (data.agent_roles) ingestAgentRoles(data.agent_roles);");
    expect(source).toContain('driveCollabFromStep(data);');
    expect(source).toContain('consumeCollabStepMessages(data);');
    expect(source).toContain('function driveCollabFromStep(data)');
    expect(source).toContain('function consumeCollabStepMessages(data)');
    expect(source).toContain('var actions = data.agent_actions || {};');
    expect(source).toContain('collabBackendMessageTotal += stepMessages;');
    expect(source).toContain('var total = Math.max(edgeTotal, collabBackendMessageTotal);');
    expect(source).toContain('recordCollabEvent({ from: a1, to: a2 });');
    expect(source).toContain("var totalEl = document.getElementById('collab-msg-total');");
    expect(source).toContain("var cnt = document.getElementById('count-' + r.id);");
  });

  it('aliases roomAgentMap to S.positions and migrates existing keys', () => {
    const source = read('src/frontend/js/digital-twin/director.js');
    const intervals = [];
    const healthEl = { className: '', textContent: '', title: '' };
    const context = {
      window: {
        _sx: { roomAgentMap: { legacy_agent: 'legacy_room' } },
        addEventListener() {},
      },
      S: { positions: { current_agent: 'current_room' } },
      console: { log() {}, error() {}, warn() {} },
      setInterval(fn, ms) { intervals.push({ fn, ms }); return intervals.length; },
      clearInterval() {},
      document: {
        getElementById(id) { return id === 'dt-room-map-health' ? healthEl : null; },
        querySelectorAll() { return []; },
      },
      AbortController: function AbortController() {},
      fetch: async () => ({ json: async () => ({}), ok: true, status: 200 }),
    };
    context.globalThis = context;

    vm.runInNewContext(source, context);

    expect(context.window._sx.roomAgentMap).toBe(context.S.positions);
    expect(context.S.positions.legacy_agent).toBe('legacy_room');
    expect(context.window._dtRoomMapHealth()).toMatchObject({
      same_ref: true,
      positions_count: 2,
      sx_count: 2,
    });
    expect(healthEl.className).toContain('dt-health-badge--ok');
    expect(healthEl.textContent).toBe('单源 2');

    context.S.positions = { replaced_agent: 'new_room' };
    const repairedHealth = context.window._dtRoomMapHealth();
    expect(context.window._sx.roomAgentMap).toBe(context.S.positions);
    expect(context.S.positions.replaced_agent).toBe('new_room');
    expect(context.S.positions.legacy_agent).toBe('legacy_room');
    expect(context.S.positions.current_agent).toBe('current_room');
    expect(repairedHealth.same_ref).toBe(true);
    expect(repairedHealth.positions_count).toBe(3);
    expect(intervals.some((item) => item.ms === 2000)).toBe(true);
  });

  it('keeps the director and SECS manual-regression entry points present after file split', () => {
    const html = read('src/frontend/Agent-digital-twin.html');
    const director = read('src/frontend/js/digital-twin/director.js');
    const secs = read('src/frontend/js/digital-twin/secs-core.js');
    const v4 = read('src/frontend/js/digital-twin/v4-scenario-evolution.js');
    const all = `${html}\n${director}\n${secs}\n${v4}`;

    [
      'id="dp-scenario-select"',
      'id="dt-room-map-health"',
      'window._dtRoomMapHealth&&window._dtRoomMapHealth()',
      'onchange="onScenarioChange(this.value)"',
      'onclick="createTrial()"',
      'onclick="stepOnce()"',
      'onclick="autoRun()"',
      'onclick="pauseSim()"',
      'onclick="showInjectDropdown()"',
      "doInjectEvent('network_delay')",
      "doInjectEvent('agent_leave')",
      "doInjectEvent('task_change')",
      "doInjectEvent('skill_degraded')",
      "doInjectEvent('model_hallucination')",
      "doInjectEvent('logic_deadlock')",
      'function viewReport(){evaluateTrial()}',
      'onclick="extractSop()"',
      'onclick="feedbackAgents()"',
      'onclick="loadSkillStats()"',
      'onclick="startEvolution()"',
      'onclick="approveEvolution()"',
      'onclick="nextGeneration()"',
      'function generateScenarioFromDesc()',
      'id="secs-btn-launch"',
      'id="secs-btn-auto"',
      'id="secs-btn-pause"',
      'id="secs-btn-step"',
      'id="btn-inject-fault"',
      'id="btn-inject-task"',
      'id="btn-inject-join"',
      'id="btn-inject-leave"',
    ].forEach((needle) => expect(all).toContain(needle));
  });
});
