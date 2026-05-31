/**
 * Tests for api.js — fetch wrapper with CSRF, offline detection, pagination
 * Uses vi.fn() to mock fetch and test request/response/error paths
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

// We test the api.js logic by replicating its IIFE behavior
// api.js exposes window.api with .request(), .get(), .post(), .put(), .del(), .list()

describe('api.js - request', () => {
  let api;

  beforeEach(() => {
    // Simulate api.js IIFE
    globalThis.fetch = vi.fn();
    globalThis.window = globalThis;

    // Re-create api like api.js does
    api = {
      _lastError: null,
      _offline: false,
      _onOffline: null,
      _onError: null,
      _csrfToken: null,
      _csrfPromise: null,
      _csrfHeaderName: 'X-CSRF-Token',

      fetchCsrfToken() {
        if (this._csrfToken) return Promise.resolve(this._csrfToken);
        if (this._csrfPromise) return this._csrfPromise;
        this._csrfPromise = fetch('/api/v1/auth/csrf-token')
          .then(r => r.json())
          .then(d => { this._csrfToken = d.csrf_token || ''; return this._csrfToken; })
          .catch(() => { this._csrfPromise = null; return ''; });
        return this._csrfPromise;
      },

      async request(url, opts) {
        const method = (opts && opts.method) ? opts.method.toUpperCase() : 'GET';
        if (method === 'POST' || method === 'PUT' || method === 'DELETE' || method === 'PATCH') {
          await this.fetchCsrfToken();
          if (this._csrfToken) {
            opts = opts || {};
            opts.headers = opts.headers || {};
            opts.headers[this._csrfHeaderName] = this._csrfToken;
          }
        }
        try {
          const r = await fetch(url, opts);
          if (this._offline) {
            this._offline = false;
            if (this._onOffline) this._onOffline(false);
          }
          if (!r.ok) {
            this._lastError = { status: r.status, message: '', url };
            if (this._onError) this._onError('HTTP ' + r.status);
            return null;
          }
          this._lastError = null;
          return await r.json();
        } catch (e) {
          if (e.name === 'TypeError' || (e.message && e.message.indexOf('fetch') !== -1)) {
            this._offline = true;
            if (this._onOffline) this._onOffline(true);
          }
          this._lastError = { status: 0, message: e.message, url, network: true };
          if (this._onError) this._onError(e.message);
          return null;
        }
      },

      async send(url, method, body) {
        await this.fetchCsrfToken();
        const opts = { method, headers: { 'Content-Type': 'application/json' } };
        if (this._csrfToken) opts.headers[this._csrfHeaderName] = this._csrfToken;
        if (body !== undefined) opts.body = JSON.stringify(body);
        return this.request(url, opts);
      },

      get(url) { return this.request(url); },
      post(url, body) { return this.send(url, 'POST', body); },
      put(url, body) { return this.send(url, 'PUT', body); },
      del(url) { return this.send(url, 'DELETE'); },

      list(baseUrl, limit, offset) {
        limit = limit || 50;
        offset = offset || 0;
        const sep = baseUrl.indexOf('?') >= 0 ? '&' : '?';
        return this.request(baseUrl + sep + 'limit=' + limit + '&offset=' + offset);
      },
    };
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('GET requests', () => {
    it('returns parsed JSON on success', async () => {
      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ teams: ['a', 'b'] }),
      });

      const result = await api.get('/api/v1/teams');
      expect(result).toEqual({ teams: ['a', 'b'] });
      expect(fetch).toHaveBeenCalledWith('/api/v1/teams', undefined);
    });

    it('returns null on 404', async () => {
      vi.mocked(fetch).mockResolvedValueOnce({
        ok: false,
        status: 404,
        json: async () => ({ detail: 'Not found' }),
      });

      const onError = vi.fn();
      api._onError = onError;

      const result = await api.get('/api/v1/teams');
      expect(result).toBeNull();
      expect(onError).toHaveBeenCalledWith('HTTP 404');
    });

    it('returns null and triggers offline on network error', async () => {
      vi.mocked(fetch).mockRejectedValueOnce(new TypeError('Failed to fetch'));

      const onOffline = vi.fn();
      api._onOffline = onOffline;

      const result = await api.get('/api/v1/teams');
      expect(result).toBeNull();
      expect(api._offline).toBe(true);
      expect(onOffline).toHaveBeenCalledWith(true);
    });
  });

  describe('POST requests', () => {
    it('includes CSRF token in headers', async () => {
      // Mock CSRF endpoint
      vi.mocked(fetch)
        .mockResolvedValueOnce({ // CSRF token fetch
          ok: true,
          json: async () => ({ csrf_token: 'test-csrf-token-123' }),
        })
        .mockResolvedValueOnce({ // actual POST
          ok: true,
          json: async () => ({ success: true }),
        });

      const result = await api.post('/api/v1/teams', { name: 'test' });
      expect(result).toEqual({ success: true });

      // Check CSRF was included
      const postCall = vi.mocked(fetch).mock.calls[1];
      expect(postCall[1].method).toBe('POST');
      expect(postCall[1].headers['X-CSRF-Token']).toBe('test-csrf-token-123');
    });

    it('does NOT inject CSRF for GET requests', async () => {
      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ data: 'ok' }),
      });

      // First call would be CSRF token fetch if triggered, but GET should skip it
      await api.get('/api/v1/teams');
      expect(fetch).toHaveBeenCalledTimes(1); // Only GET, no CSRF fetch
    });
  });

  describe('pagination', () => {
    it('appends limit and offset to URL', async () => {
      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ items: [], total: 0 }),
      });

      await api.list('/api/v1/teams', 25, 10);
      expect(fetch).toHaveBeenCalledWith('/api/v1/teams?limit=25&offset=10', undefined);
    });

    it('uses ? or & correctly', async () => {
      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ items: [], total: 0 }),
      });

      await api.list('/api/v1/teams?status=active', 50, 0);
      expect(fetch).toHaveBeenCalledWith('/api/v1/teams?status=active&limit=50&offset=0', undefined);
    });
  });

  describe('error recovery', () => {
    it('clears offline flag on successful request', async () => {
      api._offline = true;

      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ ok: true }),
      });

      await api.get('/api/v1/health');
      expect(api._offline).toBe(false);
    });
  });
});
