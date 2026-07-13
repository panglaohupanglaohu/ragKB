import { readFileSync } from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import { describe, expect, it } from 'vitest';

function loadGenetics() {
  const code = readFileSync(
    path.join(process.cwd(), 'src/frontend/js/digital-twin/eco-genetics.js'),
    'utf8',
  );
  const sandbox = { module: { exports: {} }, exports: {}, console };
  sandbox.globalThis = sandbox;
  sandbox.window = sandbox;
  vm.runInNewContext(code, sandbox, { filename: 'eco-genetics.js' });
  return sandbox.module.exports && Object.keys(sandbox.module.exports).length
    ? sandbox.module.exports
    : sandbox;
}

describe('eco-genetics v4', () => {
  it('source exports planCoverageHeatmap / perSkillHeritability / verticalVsHorizontalTransfer', () => {
    const source = readFileSync(
      path.join(process.cwd(), 'src/frontend/js/digital-twin/eco-genetics.js'),
      'utf8',
    );
    expect(source).toContain('function planCoverageHeatmap');
    expect(source).toContain('function perSkillHeritability');
    expect(source).toContain('function verticalVsHorizontalTransfer');
    expect(source).toContain('root.planCoverageHeatmap');
  });

  it('planCoverageHeatmap computes matrix and coverage', () => {
    const g = loadGenetics();
    const ranking = [
      { agent_id: 'a1', alive: true, survival_ticks: 40, skill_genome: ['coding', 'testing'] },
      { agent_id: 'a2', alive: true, survival_ticks: 30, skill_genome: ['coding'] },
    ];
    const contract = {
      niches: [
        { title: 'dev', demanded_skills: ['coding'] },
        { title: 'qa', demanded_skills: ['testing'] },
      ],
    };
    const h = g.planCoverageHeatmap(ranking, contract);
    expect(h.skills).toEqual(['coding', 'testing']);
    expect(h.matrix[0]).toEqual([1, 1]);
    expect(h.matrix[1]).toEqual([1, 0]);
    expect(h.coverage).toBeGreaterThan(0);
  });

  it('verticalVsHorizontalTransfer ratios', () => {
    const g = loadGenetics();
    const x = g.verticalVsHorizontalTransfer({
      steps: [
        { skill_origins: [{ origin: 'learn' }, { origin: 'learn' }] },
        { skill_origins: [{ origin: 'inherit' }] },
      ],
    });
    expect(x.learn).toBe(2);
    expect(x.inherit).toBe(1);
    expect(x.total).toBe(3);
  });

  it('plaza deep-link and eco bind paths present', () => {
    const plaza = readFileSync(path.join(process.cwd(), 'src/frontend/js/plaza.js'), 'utf8');
    const eco = readFileSync(path.join(process.cwd(), 'src/frontend/js/digital-twin/eco-console.js'), 'utf8');
    const tasks = readFileSync(path.join(process.cwd(), 'src/frontend/js/tasks-view.js'), 'utf8');
    expect(plaza).toContain('sendPlanToEcoField');
    expect(plaza).toContain('派发并送入物竞');
    expect(plaza).toContain('team_id');
    expect(plaza).toContain('/dispatch');
    expect(plaza).toContain('eco_bound_plan');
    expect(eco).toContain('eco2BindPlan');
    expect(eco).toContain('eco2ApplyTeamFromUrl');
    expect(eco).toContain('eco2BindTaskById');
    expect(eco).toContain('eco2ApplyIntegration');
    expect(eco).toContain('eco2DispatchWinner');
    expect(eco).toContain('planCoverageHeatmap');
    expect(tasks).toContain('sendTaskToEcoField');
    expect(tasks).toContain('🧬 物竞');
  });
});
