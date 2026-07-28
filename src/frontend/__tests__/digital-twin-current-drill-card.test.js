import { readFileSync } from 'node:fs';
import path from 'node:path';
import { describe, expect, it } from 'vitest';

function read(relPath) {
  return readFileSync(path.join(process.cwd(), relPath), 'utf8');
}

describe('digital twin L3 current drill card', () => {
  const cli = read('src/frontend/js/digital-twin-cli.js');
  const secs = read('src/frontend/js/digital-twin/secs-core.js');

  it('keeps global loadLiveMetrics unfiltered and maps by_status counts', () => {
    expect(cli).toContain('// 全局 KPI：不按 team/trial 过滤');
    expect(cli).toContain("`${API}/tasks/stats`");
    expect(cli).toContain("'/api/v1/extraction/stats'");
    expect(cli).not.toContain('tasks/stats?team_id=');
    expect(cli).toContain('function _mapTaskEngineStats(d)');
    expect(cli).toContain('by.running');
    expect(cli).toContain('by.completed');
    expect(cli).toContain('engine_running');
  });

  it('builds 当前演练 card from dtContext with team/scene/task/steps/reward', () => {
    expect(cli).toContain('function dtContext()');
    expect(cli).toContain('teamName:window._selectedTeamName');
    expect(cli).toContain('scenarioName:window._selectedSceneName');
    expect(cli).toContain('taskName:');
    expect(cli).toContain('bestReward');
    expect(cli).toContain('id="dt-current-drill-card"');
    expect(cli).toContain('◎ 当前演练');
    expect(cli).toContain('全局 KPI 不随团队过滤 · 本卡读 dtContext');
  });

  it('refreshes architecture dashboard via dtRefresh and SECS selection hooks', () => {
    expect(cli).toContain("else if(v==='view-architecture'){ if(typeof renderArchitecture==='function')renderArchitecture(); }");
    expect(cli).toContain('function renderArchitecture()');
    expect(cli).toContain('renderDashboard()');
    expect(secs).toContain("window.dtRefresh('team')");
    expect(secs).toContain("window.dtRefresh('scenario')");
    expect(secs).toContain("window.dtRefresh('task')");
    expect(secs).toContain('window._selectedSceneName = sceneName');
    expect(secs).toContain('window._selectedTaskTitle = taskTitle');
  });
});
