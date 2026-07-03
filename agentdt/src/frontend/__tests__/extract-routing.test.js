import { describe, expect, it } from 'vitest';

import { buildExtractRouting, prioritizeExtractTeams } from '../js/extract-routing.js';

describe('extract routing helpers', () => {
  it('prefers the discussion moderator team when extracting from plaza', () => {
    const plaza = {
      participants: [
        { agent_id: 'agent-a', team_id: 'build_system' },
        { agent_id: 'agent-b', team_id: 'public_cloud_ops', niche_role: 'moderator' },
      ],
    };
    const discussion = { moderator_agent_id: 'agent-b' };

    const routing = buildExtractRouting(plaza, discussion);
    expect(routing.teamIds).toEqual(['build_system', 'public_cloud_ops']);
    expect(routing.preferredTeamId).toBe('public_cloud_ops');
  });

  it('falls back to the moderator-role participant team', () => {
    const plaza = {
      participants: [
        { agent_id: 'agent-a', team_id: 'build_system' },
        { agent_id: 'agent-b', team_id: 'public_cloud_ops', niche_role: 'moderator' },
      ],
    };

    const routing = buildExtractRouting(plaza, {});
    expect(routing.preferredTeamId).toBe('public_cloud_ops');
  });

  it('keeps only participant teams and moves the preferred one to the front', () => {
    const teams = [
      { team_id: 'build_system', name: 'Build' },
      { team_id: 'public_cloud_ops', name: '公有云运维' },
      { team_id: 'ai_coding', name: 'AI Coding' },
    ];

    const ordered = prioritizeExtractTeams(
      teams,
      ['build_system', 'public_cloud_ops'],
      'public_cloud_ops',
    );

    expect(ordered.map((team) => team.team_id)).toEqual(['public_cloud_ops', 'build_system']);
  });
});
