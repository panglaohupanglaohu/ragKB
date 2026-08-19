import { readFileSync } from 'node:fs';
import path from 'node:path';
import { describe, expect, it } from 'vitest';
import { applyPlazaTranslations, plazaT } from '../js/plaza-i18n.js';

describe('plaza i18n', () => {
  it('translates semantic keys in both languages', () => {
    expect(plazaT('plaza.create', {}, 'zh')).toBe('创建广场');
    expect(plazaT('plaza.create', {}, 'en')).toBe('Create plaza');
  });

  it('interpolates dynamic values without phrase replacement', () => {
    expect(plazaT('plaza.participants', { count: 3 }, 'zh')).toBe('3 人');
    expect(plazaT('plaza.participants', { count: 3 }, 'en')).toBe('3 participants');
  });

  it('falls back to the key for missing translations', () => {
    expect(plazaT('missing.key', {}, 'en')).toBe('missing.key');
  });

  it('does not use the removed DOM observer translation strategy', () => {
    const source = readFileSync(path.join(process.cwd(), 'src/frontend/js/plaza-i18n.js'), 'utf8');
    expect(source).not.toContain('MutationObserver');
    expect(source).not.toContain('addTexts');
  });

  it('translates hyphenated aria-label data attributes', () => {
    const element = {
      dataset: { plazaI18nAriaLabel: 'nav.aria' },
      setAttribute(name, value) { this[name] = value; }
    };
    const root = {
      querySelectorAll(selector) {
        return selector === '[data-plaza-i18n-aria-label]' ? [element] : [];
      }
    };
    applyPlazaTranslations(root);
    expect(element['aria-label']).toBe('主导航');
  });
});