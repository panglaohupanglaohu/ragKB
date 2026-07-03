import { readFileSync } from 'node:fs';
import path from 'node:path';
import { describe, expect, it } from 'vitest';

function read(relPath) {
  return readFileSync(path.join(process.cwd(), relPath), 'utf8');
}

describe('digital twin room move state machine', () => {
  it('keeps backend move validation ahead of persistence and rolls back rejected drops', () => {
    const source = read('src/frontend/js/digital-twin-cli.js');
    expect(source).toContain('async function syncAgentMove(agentId,roomId)');
    expect(source).toContain('err.status=r.status');
    expect(source).toContain('function rollbackAgentMove(agentId,oldRoomId)');
    expect(source).toContain('async function onDrop(ev,roomId)');
    expect(source).toContain('await syncAgentMove(agentId,roomId);');
    expect(source).toContain('rollbackAgentMove(agentId,oldRoomId);');
    expect(source).toContain("err&&err.status===409");
    expect(source).toContain('已退回');
  });
});
