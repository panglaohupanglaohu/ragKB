import { readFileSync } from 'node:fs';
import path from 'node:path';
import { describe, expect, it } from 'vitest';

function read(relPath) {
  return readFileSync(path.join(process.cwd(), relPath), 'utf8');
}

describe('skill-extract modal full tab flow', () => {
  const source = read('src/frontend/js/skill-extract.js');

  it('A: hardens skill identity resolution with ensureSkillsLoaded before dependent tabs', () => {
    expect(source).toContain('async function ensureSkillsLoaded()');
    expect(source).toContain('await ensureSkillsLoaded()');
    // switchModalTab must be async to await the loader
    expect(source).toContain('window.switchModalTab = async function(tab)');
  });

  it('A: writes skill_id back to queueItems after approve', () => {
    expect(source).toContain('queueItems[idx].skill_draft = { skill_id: r.skill_id || r.draft_slug');
  });

  it('B: evolve gate uses registered check, not item.status alone', () => {
    expect(source).toContain('const registered = !!(skillId && allSkills');
    expect(source).toContain("promptRegisterFirst('演化')");
  });

  it('B2: unregistered skill gets actionable guidance that points to the approve buttons', () => {
    expect(source).toContain('function promptRegisterFirst(action)');
    expect(source).toContain('批准为特质技能 / 📦 储备技能 / 🌍 公共技能');
    expect(source).toContain("switchModalTab('edit')");
    // verify tab uses the same helper
    expect(source).toContain("promptRegisterFirst('验证')");
    // dead-end toast must be gone
    expect(source).not.toContain('找不到已注册的技能ID');
  });

  it('C: triggerEvolve resets the button via try/finally', () => {
    // 允许 ASCII ... 或 Unicode 省略号 …
    expect(source).toMatch(/btn\.textContent = '⏳ 演化中(\.\.\.|…)'/);
    expect(source).toMatch(/} finally \{[\s\S]*btn\.textContent = '⚡ 触发演化'/);
  });

  it('C: acceptEvolution awaits refreshes to avoid stale UI', () => {
    expect(source).toContain('await loadQueue(); await loadSkills();');
  });

  it('C2: acceptEvolution auto-runs verify after apply (closed loop)', () => {
    expect(source).toContain('async function _runPostEvolutionVerify');
    expect(source).toContain('await _runPostEvolutionVerify(result.version)');
    expect(source).toContain("switchModalTab('verify')");
    expect(source).toContain('接受演化并验证');
  });

  it('D0: triggerVerify resets button via try/finally', () => {
    expect(source).toContain('let _verifyInFlight = false');
    expect(source).toMatch(/} finally \{[\s\S]*btn\.textContent = '🧪 开始验证'/);
  });

  it('D: verify gate aligns with registered check and falls back on null fields', () => {
    expect(source).toContain('(result.pass_rate ?? 0)');
    expect(source).toContain('result.passed ?? 0');
    expect(source).toContain('result.test_details || []');
  });

  it('F: version tab tolerates missing lineage and shows empty state', () => {
    expect(source).toContain('data?.lineage || {}');
    expect(source).toContain('暂无演化历史');
  });

  it('G: pipeline tab shows empty state when no pipeline exists', () => {
    expect(source).toContain('该草稿尚未进入复核管线');
  });

  it('keeps the per-tab loaders wired', () => {
    for (const fn of ['loadEvolveTab', 'loadVerifyTab', 'loadUsageTab', 'loadVersionTab', 'loadPipelineTab']) {
      expect(source).toContain(fn);
    }
  });
});
