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

  it('P5-3: exposes structured execution-plan panel wired to approve/reject/step-question endpoints', () => {
    const source = read('src/frontend/js/plaza.js');
    // 入口 + 容器
    expect(source).toContain('onclick="loadExecutionPlan()"');
    expect(source).toContain('id="exec-plan-body"');
    // 加载结构化计划（含落地性 issues）
    expect(source).toContain('window.loadExecutionPlan = async function');
    expect(source).toContain('/execution-plan');
    expect(source).toContain('function renderExecutionPlan(r)');
    // 批准（含强制批准保留人的最终决定权）
    expect(source).toContain('window.approveExecutionPlan = async function');
    expect(source).toContain('/execution-plan/approve');
    // 驳回 = 重议
    expect(source).toContain('window.rejectExecutionPlan = async function');
    expect(source).toContain('await refreshPlan()');
    // 逐步骤追问（锚定步骤 → 讨论插话）
    expect(source).toContain('window.askPlanStep = async function');
    expect(source).toContain('【关于步骤');
    expect(source).toContain('/interject');
  });
});
