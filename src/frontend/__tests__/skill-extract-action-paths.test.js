import { readFileSync } from 'node:fs';
import path from 'node:path';
import { describe, expect, it } from 'vitest';

function read(relPath) {
  return readFileSync(path.join(process.cwd(), relPath), 'utf8');
}

describe('skill extraction action paths', () => {
  it('keeps the candidate lifecycle wired from extraction to verification and publish gate', () => {
    const source = read('src/frontend/js/skill-extract.js');
    const html = read('src/frontend/skill-extract.html');

    expect(html).toContain('id="btn-extract"');
    expect(html).toContain('onclick="startExtraction()"');
    expect(source).toContain('window.startExtraction = async function()');
    expect(source).toContain('/skill-extract/start');
    expect(source).toContain('window._openDetail = async function(itemId)');
    expect(source).toContain('switchModalTab');
    expect(source).toContain('window.approveAs = async function(skillType)');
    expect(source).toContain('/approve`,');
    expect(source).toContain('window.triggerVerify = async function()');
    expect(source).toContain("api('/skill-library/verify'");
    expect(source).toContain('沙箱 / 容器验证证据');
    expect(source).toContain('async function publishSkillWithGate(skillId, skillName)');
    expect(source).toContain("'/skill-library/publish-gate'");
    expect(source).toContain("'/skill-library/publish'");
  });
});
