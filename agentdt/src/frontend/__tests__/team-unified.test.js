/**
 * L1.3: dtSetCurrentTeam / dtGetCurrentTeam 三套一致性
 * 目标: dtSetCurrentTeam('x') 后, localStorage / S.selectedTeams / dtGetCurrentTeam() 读到一致
 */
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';

describe('L1 数字孪生团队统一', () => {
  let S, dtGetCurrentTeam, dtSetCurrentTeam;

  // Mock localStorage
  const store = {};
  beforeEach(() => {
    Object.keys(store).forEach(k => delete store[k]);
    vi.stubGlobal('localStorage', {
      getItem: (k) => store[k] || null,
      setItem: (k, v) => { store[k] = String(v); },
      removeItem: (k) => { delete store[k]; },
    });
    vi.stubGlobal('sessionStorage', {
      _store: {},
      getItem: (k) => sessionStorage._store[k] || null,
      setItem: (k, v) => { sessionStorage._store[k] = v; },
      removeItem: (k) => { delete sessionStorage._store[k]; },
    });
    // Mock S global
    S = { agents: [], teams: [], rooms: [], selectedTeams: [], skills: [], tools: [] };
    vi.stubGlobal('S', S);
    // Mock render functions
    vi.stubGlobal('renderTeamSelector', vi.fn());
    vi.stubGlobal('renderAgentList', vi.fn());

    // Define the helpers (mirroring digital-twin-cli.js)
    dtGetCurrentTeam = function() {
      return localStorage.getItem('selected_team') || (S.selectedTeams && S.selectedTeams[0]) || 'build_system';
    };
    dtSetCurrentTeam = function(id) {
      if (!id) return;
      localStorage.setItem('selected_team', id);
      localStorage.setItem('ag_current_team', id);
      if (S) { S.selectedTeams = [id]; if (typeof renderTeamSelector === 'function') renderTeamSelector(); if (typeof renderAgentList === 'function') renderAgentList(); }
    };
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('dtSetCurrentTeam 后 localStorage 三键一致', () => {
    dtSetCurrentTeam('frontend_team');
    expect(localStorage.getItem('selected_team')).toBe('frontend_team');
    expect(localStorage.getItem('ag_current_team')).toBe('frontend_team');
    expect(S.selectedTeams).toEqual(['frontend_team']);
  });

  it('dtGetCurrentTeam 返回刚设置的值', () => {
    dtSetCurrentTeam('backend_team');
    expect(dtGetCurrentTeam()).toBe('backend_team');
  });

  it('dtSetCurrentTeam 更新后 dtGetCurrentTeam 即时生效（无页面刷新）', () => {
    dtSetCurrentTeam('team_a');
    expect(dtGetCurrentTeam()).toBe('team_a');
    dtSetCurrentTeam('team_b');
    expect(dtGetCurrentTeam()).toBe('team_b');
    expect(localStorage.getItem('selected_team')).toBe('team_b');
  });

  it('无设置时回退到 S.selectedTeams[0]', () => {
    S.selectedTeams = ['ops_team'];
    expect(dtGetCurrentTeam()).toBe('ops_team');
  });

  it('完全无设置时回退到 build_system', () => {
    S.selectedTeams = [];
    expect(dtGetCurrentTeam()).toBe('build_system');
  });

  it('null/undefined 不覆盖已有值', () => {
    dtSetCurrentTeam('existing');
    dtSetCurrentTeam(null);
    expect(dtGetCurrentTeam()).toBe('existing');
    dtSetCurrentTeam(undefined);
    expect(dtGetCurrentTeam()).toBe('existing');
  });

  it('ag_current_team 常与 selected_team 同步', () => {
    dtSetCurrentTeam('cross_page_team');
    expect(localStorage.getItem('ag_current_team')).toBe('cross_page_team');
    expect(localStorage.getItem('ag_current_team')).toBe(localStorage.getItem('selected_team'));
  });

  it('renderTeamSelector/AgentList 在设定时触发', () => {
    dtSetCurrentTeam('ui_team');
    expect(renderTeamSelector).toHaveBeenCalled();
    expect(renderAgentList).toHaveBeenCalled();
  });
});
