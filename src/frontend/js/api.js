/**
 * AgentsGroup2026 — Shared API Client
 * Unified fetch wrapper with error handling, offline detection,
 * and pagination support. Load before page-specific scripts.
 * Exposes window.api with .request(), .get(), .post(), .put(), .del(), .list()
 */
(function () {
  'use strict';

  var nativeFetch = window.fetch ? window.fetch.bind(window) : null;
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

  api.setCsrfToken = function (token) {
    api._csrfToken = token || '';
    api._csrfPromise = api._csrfToken ? Promise.resolve(api._csrfToken) : null;
    return api._csrfToken;
  };

  api.clearCsrfToken = function () {
    api._csrfToken = null;
    api._csrfPromise = null;
  };

  function withCredentials(opts) {
    opts = opts || {};
    if (!opts.credentials) opts.credentials = 'same-origin';
    return opts;
  }

  function isStateChanging(method) {
    method = (method || 'GET').toUpperCase();
    return method === 'POST' || method === 'PUT' || method === 'DELETE' || method === 'PATCH';
  }

  function getRequestUrl(input) {
    if (typeof input === 'string') return input;
    if (input && typeof input.url === 'string') return input.url;
    return '';
  }

  function isSameOrigin(input) {
    var url = getRequestUrl(input);
    if (!url) return false;
    try {
      return new URL(url, window.location.origin).origin === window.location.origin;
    } catch (e) {
      return false;
    }
  }

  function hasHeader(headers, name) {
    if (!headers || typeof headers.has !== 'function') return false;
    return headers.has(name) || headers.has(name.toLowerCase());
  }

  async function prepareRequest(input, opts) {
    if (!isSameOrigin(input)) {
      return [input, opts];
    }

    var requestLike = (typeof Request !== 'undefined') && input instanceof Request;
    var method = (opts && opts.method) || (requestLike ? input.method : 'GET');
    var headers = new Headers((opts && opts.headers) || (requestLike ? input.headers : undefined) || undefined);

    if (isStateChanging(method)) {
      await api.fetchCsrfToken();
      if (api._csrfToken && !hasHeader(headers, api._csrfHeaderName)) {
        headers.set(api._csrfHeaderName, api._csrfToken);
      }
    }

    var finalOpts = {};
    if (opts) {
      Object.keys(opts).forEach(function (key) {
        if (key !== 'headers') finalOpts[key] = opts[key];
      });
    }
    finalOpts.headers = headers;
    if (!finalOpts.credentials) {
      finalOpts.credentials = (requestLike && input.credentials) || 'same-origin';
    }

    if (requestLike) {
      return [new Request(input, finalOpts), undefined];
    }
    return [input, finalOpts];
  }

  /**
   * Fetch a fresh CSRF token from the server and cache it.
   */
  api.fetchCsrfToken = function () {
    if (api._csrfToken) return Promise.resolve(api._csrfToken);
    if (api._csrfPromise) return api._csrfPromise;
    api._csrfPromise = nativeFetch('/api/v1/auth/csrf-token', withCredentials())
      .then(function (r) { return r.json(); })
      .then(function (d) {
        return api.setCsrfToken(d.csrf_token || '');
      })
      .catch(function () {
        api._csrfPromise = null;
        return '';
      });
    return api._csrfPromise;
  };
  /**
   * Main request function.
   * @param {string} url  - Full or relative URL
   * @param {object} [opts] - fetch options (method, headers, body)
   * @returns {object|null} - Parsed JSON response, or null on error
   */
  api.request = async function (url, opts) {
    try {
      var prepared = await prepareRequest(url, opts);
      var r = await nativeFetch(prepared[0], prepared[1]);
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
    var opts = {
      method: method,
      headers: { 'Content-Type': 'application/json' },
    };
    if (body !== undefined) opts.body = JSON.stringify(body);
    return api.request(url, opts);
  };

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

  api.logout = async function () {
    var result = await api.post('/api/v1/auth/logout');
    api.clearCsrfToken();
    return result;
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
    var prepared = await prepareRequest(url, opts);
    return nativeFetch(prepared[0], prepared[1]);
  };

  if (nativeFetch) {
    window.fetch = async function (input, opts) {
      var prepared = await prepareRequest(input, opts);
      return nativeFetch(prepared[0], prepared[1]);
    };
  }

  // Pre-fetch at load time
  api.fetchCsrfToken();
})();
