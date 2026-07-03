import { readFileSync } from 'node:fs';
import path from 'node:path';
import { afterEach, describe, expect, it, vi } from 'vitest';

function read(relPath) {
  return readFileSync(path.join(process.cwd(), relPath), 'utf8');
}

describe('mutating pages load the shared API client', () => {
  [
    'src/frontend/plaza.html',
    'src/frontend/agent-team-config.html',
    'src/frontend/system-evolution.html',
    'src/frontend/login.html',
    'src/frontend/skill-extract.html',
    'src/frontend/sandbox-twin.html',
    'src/frontend/digital-twin-cli.html',
    'src/frontend/extraction-pipeline.html',
    'src/frontend/tasks.html',
    'src/frontend/datacenter-ratchet-evolution.html',
  ].forEach((page) => {
    it(`${page} includes /js/api.js`, () => {
      expect(read(page)).toContain('/js/api.js');
    });
  });
});

describe('api.js shared fetch wrapper', () => {
  afterEach(() => {
    vi.restoreAllMocks();
    delete globalThis.window;
    delete globalThis.api;
    delete globalThis._agFetch;
  });

  it('injects CSRF into same-origin direct POST fetch calls', async () => {
    const source = read('src/frontend/js/api.js');
    const rawFetch = vi.fn()
      .mockResolvedValueOnce({ json: async () => ({ csrf_token: 'csrf-token-1' }) })
      .mockResolvedValueOnce({ ok: true, json: async () => ({ ok: true }) });

    globalThis.window = globalThis;
    globalThis.location = new URL('http://localhost:5173/plaza.html');
    globalThis.fetch = rawFetch;

    eval(source);
    await window.api.fetchCsrfToken();
    await window.fetch('/api/v1/plaza/p-1/discussions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: '{"topic":"test"}',
    });

    expect(rawFetch).toHaveBeenNthCalledWith(1, '/api/v1/auth/csrf-token', { credentials: 'same-origin' });
    const postCall = rawFetch.mock.calls[1];
    expect(postCall[0]).toBe('/api/v1/plaza/p-1/discussions');
    expect(postCall[1].credentials).toBe('same-origin');
    expect(postCall[1].headers.get('X-CSRF-Token')).toBe('csrf-token-1');
  });

  it('does not inject CSRF into cross-origin direct POST fetch calls', async () => {
    const source = read('src/frontend/js/api.js');
    const rawFetch = vi.fn()
      .mockResolvedValueOnce({ json: async () => ({ csrf_token: 'csrf-token-1' }) })
      .mockResolvedValueOnce({ ok: true, json: async () => ({ ok: true }) });

    globalThis.window = globalThis;
    globalThis.location = new URL('http://localhost:5173/plaza.html');
    globalThis.fetch = rawFetch;

    eval(source);
    await window.fetch('https://example.com/webhook', { method: 'POST' });

    const postCall = rawFetch.mock.calls[1];
    expect(postCall[0]).toBe('https://example.com/webhook');
    expect(postCall[1]?.headers?.get?.('X-CSRF-Token') || '').toBe('');
  });
});
