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
    expect(source).toContain('function renderStructuredOutput(output)');
    expect(source).toContain('STRUCTURED OUTPUT');
    expect(source).toContain('renderStructuredOutput(r.output || (r.outputs || [])[0])');
    expect(source).toContain('window.extractFromDisc = async function(event, discId)');
    expect(source).toContain('/outputs`,');
    expect(source).toContain("output_type: 'skill_candidate'");
    expect(source).toContain("sessionStorage.setItem('plaza_structured_output'");
    expect(source).toContain('source_output_id');
    expect(source).toContain("sessionStorage.setItem('extract_source'");
    expect(source).toContain("window.location.href = targetUrl.pathname + targetUrl.search");
  });
});
