import { readFileSync } from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import { describe, expect, it, vi } from 'vitest';

function read(relPath) {
  return readFileSync(path.join(process.cwd(), relPath), 'utf8');
}

function buildContext(requestImpl) {
  const window = {
    api: {
      request: requestImpl,
    },
  };
  const context = vm.createContext({
    window,
    URLSearchParams,
    encodeURIComponent,
    fetch: vi.fn(),
  });
  vm.runInContext(read('src/frontend/js/evidence-runs.js'), context);
  return { context, window };
}

describe('evidence-runs shared helper', () => {
  it('queries evidence runs by linked object through the unified endpoint', async () => {
    const request = vi.fn().mockResolvedValue({
      evidence_runs: [{ evidence_id: 'EV-1', evidence_type: 'skill_verify', status: 'passed' }],
    });
    const { window } = buildContext(request);

    const runs = await window.evidenceRuns.byObject('skill', 'skill-001', { limit: 5 });

    expect(request).toHaveBeenCalledWith('/api/v1/evidence-runs/by-object/skill/skill-001?limit=5&offset=0');
    expect(runs).toHaveLength(1);
    expect(runs[0].evidence_id).toBe('EV-1');
  });

  it('summarizes runtime, status, request id, and linked object ids', () => {
    const { window } = buildContext(vi.fn());

    const summary = window.evidenceRuns.summarize({
      evidence_id: 'EV-2',
      evidence_type: 'tool_call',
      status: 'failed',
      request_id: 'req-1',
      runtime: { mode: 'in_process', tool_name: 'run_shell' },
      command: 'run_shell',
      exit_code: 1,
      task_id: 'task-1',
    });

    expect(summary.tone).toBe('bad');
    expect(summary.runtimeLabel).toBe('in_process / run_shell');
    expect(summary.requestId).toBe('req-1');
    expect(summary.objectIds.taskId).toBe('task-1');
  });
});
