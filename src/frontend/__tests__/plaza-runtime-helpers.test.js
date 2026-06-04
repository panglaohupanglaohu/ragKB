import { readFileSync } from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import { describe, expect, it } from 'vitest';

function read(relPath) {
  return readFileSync(path.join(process.cwd(), relPath), 'utf8');
}

function loadHelpers(contextOverrides = {}) {
  const source = read('src/frontend/js/plaza.js');
  const start = source.indexOf('function latestDiscussionRound()');
  const end = source.indexOf('function renderVerificationState()');
  if (start < 0 || end < 0) throw new Error('Plaza helper block not found');
  const context = {
    curDisc: '',
    curDiscData: {},
    result: null,
    ...contextOverrides,
  };
  vm.runInNewContext(
    `${source.slice(start, end)}
result = {
  latestDiscussionRound,
  summarizeVerificationStatus,
  normalizeVerificationState,
  normalizeConsensusState,
  normalizeEscalationState,
};`,
    context
  );
  return context.result;
}

describe('plaza runtime helpers', () => {
  it('prefers explicit discussion round over message-derived round', () => {
    const helpers = loadHelpers({
      curDiscData: {
        current_round: 4,
        messages: [{ round_number: 7 }, { round_number: 9 }],
      },
    });
    expect(helpers.latestDiscussionRound()).toBe(4);
  });

  it('summarizes verification queue fallback from items payload', () => {
    const helpers = loadHelpers();
    const state = helpers.normalizeVerificationState({
      items: [{ status: 'pending' }, { status: 'pending' }, { status: 'resolved' }],
      alerts: [{ item_id: 'ev-1' }],
    });
    expect(state.queue_count).toBe(3);
    expect(state.alert_count).toBe(1);
    expect(state.status_counts).toEqual({ pending: 2, resolved: 1 });
  });

  it('fills consensus defaults from current discussion context', () => {
    const helpers = loadHelpers({
      curDisc: 'disc-7',
      curDiscData: { messages: [{ round_number: 2 }, { round_number: 3 }] },
    });
    const state = helpers.normalizeConsensusState({});
    expect(state.discussion_id).toBe('disc-7');
    expect(state.round_number).toBe(3);
    expect(state.score).toBe(0.5);
    expect(state.can_early_exit).toBe(false);
  });

  it('derives escalation totals from items when counters are absent', () => {
    const helpers = loadHelpers();
    const state = helpers.normalizeEscalationState({
      items: [{ status: 'pending' }, { status: 'resolved' }, { status: 'pending' }],
    });
    expect(state.total).toBe(3);
    expect(state.pending_count).toBe(2);
  });
});
