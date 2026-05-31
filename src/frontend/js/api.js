/**
 * AgentsGroup2026 — Shared API Client
 * Unified fetch wrapper with error handling, offline detection,
 * and pagination support. Load before page-specific scripts.
 * Exposes window.api with .request(), .get(), .post(), .put(), .del(), .list()
 */
(function () {
  'use strict';

  var api = window.api = {};

  // Last error for debugging
  api._lastError = null;

  // Offline state (consumed by page-specific UI)
  api._offline = false;
  api._onOffline = null;  // callback when offline status changes
  api._onError = null;    // callback(msg) for 4xx/5xx

  // CSRF token (fetched from endpoint and cached)
  api._csrfToken = null;
  api._csrfPromise = null;
  api._csrfHeaderName = 'X-CSRF-Token';

  /**
   * Fetch a fresh CSRF token from the server and cache it.
   */
  api.fetchCsrfToken = function () {
    if (api._csrfToken) return Promise.resolve(api._csrfToken);
    if (api._csrfPromise) return api._csrfPromise;
    api._csrfPromise = fetch('/api/v1/auth/csrf-token')
      .then(function (r) { return r.json(); })
      .then(function (d) {
        api._csrfToken = d.csrf_token || '';
        return api._csrfToken;
      })
      .catch(function () {
        api._csrfPromise = null;
        return '';
      });
    return api._csrfPromise;
  };
  // Pre-fetch at load time
  api.fetchCsrfToken();

  /**
   * Main request function.
   * @param {string} url  - Full or relative URL
   * @param {object} [opts] - fetch options (method, headers, body)
   * @returns {object|null} - Parsed JSON response, or null on error
   */
  api.request = async function (url, opts) {
    // Auto-inject CSRF token for state-changing requests
    var method = (opts && opts.method) ? opts.method.toUpperCase() : 'GET';
    if (method === 'POST' || method === 'PUT' || method === 'DELETE' || method === 'PATCH') {
      await api.fetchCsrfToken();
      if (api._csrfToken) {
        opts = opts || {};
        opts.headers = opts.headers || {};
        if (!opts.headers[api._csrfHeaderName] && !opts.headers[api._csrfHeaderName.toLowerCase()]) {
          opts.headers[api._csrfHeaderName] = api._csrfToken;
        }
      }
    }
    try {
      var r = await fetch(url, opts);
      if (api._offline) {
        api._offline = false;
        if (api._onOffline) api._onOffline(false);
      }
      if (!r.ok) {
        var msg = '';
        try { var d = await r.json(); msg = d.detail || d.message || ''; } catch (e) { /* ignore parse errors */ }
        console.warn('API ' + r.status + ': ' + url, msg);
        api._lastError = { status: r.status, message: msg, url: url };
        if (api._onError) api._onError(msg || 'HTTP ' + r.status);
        api._lastViewError = msg || 'HTTP ' + r.status;
        return null;
      }
      api._lastError = null;
      return await r.json();
    } catch (e) {
      console.error('API error: ' + url, e);
      if (e.name === 'TypeError' || (e.message && e.message.indexOf('fetch') !== -1)) {
        api._offline = true;
        if (api._onOffline) api._onOffline(true);
      }
      api._lastError = { status: 0, message: e.message, url: url, network: true };
      if (api._onError) api._onError(e.message);
      api._lastViewError = e.message;
      return null;
    }
  };

  /**
   * Shorthand for GET requests
   */
  api.get = function (url) {
    return api.request(url);
  };

  /**
   * Shorthand for POST/PUT/DELETE with JSON body
   * Automatically includes CSRF token for state-changing requests.
   */
  api.send = async function (url, method, body) {
    await api.fetchCsrfToken();
    var opts = {
      method: method,
      headers: { 'Content-Type': 'application/json' },
    };
    if (api._csrfToken) {
      opts.headers[api._csrfHeaderName] = api._csrfToken;
    }
    if (body !== undefined) opts.body = JSON.stringify(body);
    return api.request(url, opts);
  };

  /**
   * Bootstrap: fetch CSRF token from server.
   */
  api.fetchCsrfToken();

  /**
   * POST shorthand
   */
  api.post = function (url, body) {
    return api.send(url, 'POST', body);
  };

  /**
   * PUT shorthand
   */
  api.put = function (url, body) {
    return api.send(url, 'PUT', body);
  };

  /**
   * DELETE shorthand
   */
  api.del = function (url) {
    var opts = { method: 'DELETE' };
    if (api._csrfToken) {
      opts.headers = opts.headers || {};
      opts.headers[api._csrfHeaderName] = api._csrfToken;
    }
    return api.request(url, opts);
  };

  /**
   * Pagination wrapper — adds limit/offset/query params to a list GET
   * Returns { items, total, limit, offset, has_more }
   */
  api.list = function (baseUrl, limit, offset) {
    limit = limit || 50;
    offset = offset || 0;
    var sep = baseUrl.indexOf('?') >= 0 ? '&' : '?';
    return api.request(baseUrl + sep + 'limit=' + limit + '&offset=' + offset);
  };

  // Global CSRF-aware fetch wrapper for direct fetch() calls in other scripts.
  // Usage: replace fetch(url, opts) with window._agFetch(url, opts) for state-changing requests.
  window._agFetch = async function (url, opts) {
    var method = (opts && opts.method) ? opts.method.toUpperCase() : 'GET';
    if (method === 'POST' || method === 'PUT' || method === 'DELETE' || method === 'PATCH') {
      await api.fetchCsrfToken();
      if (api._csrfToken) {
        opts = opts || {};
        opts.headers = opts.headers || {};
        if (!opts.headers[api._csrfHeaderName] && !opts.headers[api._csrfHeaderName.toLowerCase()]) {
          opts.headers[api._csrfHeaderName] = api._csrfToken;
        }
      }
    }
    return fetch(url, opts);
  };
})();
