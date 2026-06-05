import { readFileSync } from 'node:fs';
import path from 'node:path';
import { describe, expect, it } from 'vitest';

function read(relPath) {
  return readFileSync(path.join(process.cwd(), relPath), 'utf8');
}

describe('plaza action paths', () => {
  it('keeps discussion conclusions connected to tasks, execution, evolution, verification, and skill extraction', () => {
    const source = read('src/frontend/js/plaza.js');
    const html = read('src/frontend/plaza.html');

    expect(html).toContain('id="plan-panel"');
    expect(source).toContain('window.dispatchTasks = async function()');
    expect(source).toContain('/dispatch`,');
    expect(source).toContain('window.dispatchAndExecute = async function()');
    expect(source).toContain('/dispatch-and-execute`,');
    expect(source).toContain('window.enterEvolution = async function()');
    expect(source).toContain('/evolve`,');
    expect(source).toContain('window.runVerificationQueue = async function()');
    expect(source).toContain('/verification-queue/run`,');
    expect(source).toContain('window.extractFromDisc = async function(event, discId)');
    expect(source).toContain("sessionStorage.setItem('extract_source'");
    expect(source).toContain("window.location.href = targetUrl.pathname + targetUrl.search");
  });
});
