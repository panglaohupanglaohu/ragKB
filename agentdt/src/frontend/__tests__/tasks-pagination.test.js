import { readFileSync } from 'node:fs';
import path from 'node:path';
import { describe, expect, it } from 'vitest';

function read(relPath) {
  return readFileSync(path.join(process.cwd(), relPath), 'utf8');
}

describe('tasks pagination consumers', () => {
  it('uses shared listTasks helper for team task reads', () => {
    const source = read('src/frontend/js/tasks-view.js');
    expect(source).toContain('async function listTasks(limit = 200, offset = 0)');
    expect(source).toContain("window.api.list(`${A}/teams/${tid}/tasks`,limit,offset)");
    expect(source).toContain('const tasks=await listTasks();');
    expect(source).toContain('const[tasks,stats]=await Promise.all([listTasks(),api(`${A}/tasks/stats`)])');
  });
});
