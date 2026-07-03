/**
 * D-1.1: Scenario card selector smoke test
 * Verifies the card-based scenario selector renders correctly.
 */
import { readFileSync } from 'node:fs';
import path from 'node:path';
import { describe, expect, it } from 'vitest';

function read(relPath) {
  return readFileSync(path.join(process.cwd(), relPath), 'utf8');
}

describe('Scenario card selector (D-1.1)', () => {
  it('HTML uses card container not select dropdown', () => {
    const html = read('src/frontend/Agent-digital-twin.html');
    expect(html).toContain('id="dp-scenario-cards"');
    expect(html).toContain('mode-grid');
    // Should NOT have old select
    expect(html).not.toContain('id="dp-scenario-select"');
  });

  it('CSS has scenario-card styles', () => {
    const html = read('src/frontend/Agent-digital-twin.html');
    expect(html).toContain('.scenario-card');
    expect(html).toContain('.sc-match');
    expect(html).toContain('.sc-stars');
    expect(html).toContain('.sc-best');
    expect(html).toContain('.sc-free');
    expect(html).toContain('.sc-active');
  });

  it('loadScenarioList renders cards not options', () => {
    const src = read('src/frontend/js/digital-twin/v4-scenarios.js');
    expect(src).toContain('dp-scenario-cards');
    expect(src).toContain('scenario-card');
    expect(src).toContain('mode-icon');
    expect(src).toContain('mode-name');
    // Should NOT create option elements
    expect(src).not.toContain("createElement('option')");
  });

  it('onScenarioChange handles card click with highlight', () => {
    const src = read('src/frontend/js/digital-twin/v4-scenarios.js');
    expect(src).toContain("querySelectorAll('.scenario-card')");
    expect(src).toContain("classList.toggle('sc-active'");
    expect(src).toContain('getAttribute(\'data-scenario\')');
  });
});
