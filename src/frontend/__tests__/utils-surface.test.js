import { readFileSync } from 'node:fs';
import path from 'node:path';
import { describe, expect, it } from 'vitest';

function read(relPath) {
  return readFileSync(path.join(process.cwd(), relPath), 'utf8');
}

describe('utils.js shared surface', () => {
  it('keeps AG namespace exports and legacy aliases wired', () => {
    const source = read('src/frontend/js/utils.js');
    expect(source).toContain('var utils = window.AG = {};');
    expect(source).toContain('utils.throttle = function (fn, ms) {');
    expect(source).toContain('utils.showError = function (containerId, message) {');
    expect(source).toContain('utils.clearError = function (containerId) {');
    expect(source).toContain('window.openModal = utils.openModal;');
    expect(source).toContain('window.showViewLoading = utils.showViewLoading;');
  });
});
