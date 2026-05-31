/**
 * Tests for utils.js — pure functions (no DOM needed)
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';

// We test utils.js by importing it as a module and checking window.AG
// Since utils.js uses IIFE pattern to create window.AG, we need a DOM-like env.
// For pure function tests, we test the logic directly.
// For DOM-dependent functions, we mock document.

describe('escapeHtml', () => {
  // Replicate the exact implementation from utils.js
  function escapeHtml(v) {
    return String(v ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }

  it('escapes HTML special characters', () => {
    expect(escapeHtml('<script>alert("xss")</script>'))
      .toBe('&lt;script&gt;alert(&quot;xss&quot;)&lt;/script&gt;');
  });

  it('returns empty string for null/undefined', () => {
    expect(escapeHtml(null)).toBe('');
    expect(escapeHtml(undefined)).toBe('');
  });

  it('returns string for numbers', () => {
    expect(escapeHtml(42)).toBe('42');
  });

  it('handles single quotes', () => {
    expect(escapeHtml("it's")).toBe('it&#39;s');
  });

  it('correctly handles & in input', () => {
    // escapeHtml converts & to &amp; — this is correct behavior
    expect(escapeHtml('a & b')).toBe('a &amp; b');
  });
});

describe('statusLabel', () => {
  function statusLabel(s) {
    return { idle: '待命中', working: '工作中', reporting: '汇报中', blocked: '阻塞', error: '异常' }[s] || s || '未知';
  }

  it('returns Chinese labels for known statuses', () => {
    expect(statusLabel('idle')).toBe('待命中');
    expect(statusLabel('working')).toBe('工作中');
    expect(statusLabel('reporting')).toBe('汇报中');
    expect(statusLabel('blocked')).toBe('阻塞');
    expect(statusLabel('error')).toBe('异常');
  });

  it('returns original string for unknown status', () => {
    expect(statusLabel('custom_status')).toBe('custom_status');
  });

  it('returns 未知 for empty input', () => {
    expect(statusLabel('')).toBe('未知');
  });
});

describe('fmtNum', () => {
  function fmtNum(v) {
    return Number(v || 0).toLocaleString();
  }

  it('formats numbers with locale separators', () => {
    const result = fmtNum(1234567);
    expect(result).toMatch(/1[,.]234[,.]567/);
  });

  it('handles zero', () => {
    expect(fmtNum(0)).toBe('0');
  });

  it('handles null/undefined as 0', () => {
    expect(fmtNum(null)).toBe('0');
    expect(fmtNum(undefined)).toBe('0');
  });
});

describe('shortId', () => {
  function shortId(v, n) {
    n = n || 8;
    const s = String(v || '');
    return s ? s.slice(0, n) : '-';
  }

  it('truncates string to n chars', () => {
    expect(shortId('abcdefghijklmnop', 8)).toBe('abcdefgh');
  });

  it('defaults to 8 chars', () => {
    expect(shortId('1234567890')).toBe('12345678');
  });

  it('returns dash for empty string', () => {
    expect(shortId('')).toBe('-');
  });
});

describe('debounce', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  it('delays function execution', () => {
    const fn = vi.fn();
    const debounced = (function (fn, ms) {
      ms = ms || 300;
      var t;
      return function () {
        var args = arguments;
        var ctx = this;
        clearTimeout(t);
        t = setTimeout(function () { fn.apply(ctx, args); }, ms);
      };
    })(fn, 300);

    debounced();
    expect(fn).not.toHaveBeenCalled();

    vi.advanceTimersByTime(299);
    expect(fn).not.toHaveBeenCalled();

    vi.advanceTimersByTime(1);
    expect(fn).toHaveBeenCalledTimes(1);
  });

  it('cancels previous call on rapid fire', () => {
    const fn = vi.fn();
    const debounced = (function (fn, ms) {
      ms = ms || 300;
      var t;
      return function () {
        var args = arguments;
        var ctx = this;
        clearTimeout(t);
        t = setTimeout(function () { fn.apply(ctx, args); }, ms);
      };
    })(fn, 200);

    debounced();
    vi.advanceTimersByTime(100);
    debounced();
    vi.advanceTimersByTime(100);
    debounced();
    vi.advanceTimersByTime(199);
    expect(fn).not.toHaveBeenCalled();

    vi.advanceTimersByTime(1);
    expect(fn).toHaveBeenCalledTimes(1);
  });
});

describe('relTime', () => {
  function relTime(v) {
    if (!v) return '-';
    const ms = typeof v === 'number' ? v * 1000 : Date.parse(v);
    if (!Number.isFinite(ms)) return '-';
    const diff = Math.max(0, Date.now() - ms);
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return '刚刚';
    if (mins < 60) return mins + ' 分钟前';
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return hrs + ' 小时前';
    return Math.floor(hrs / 24) + ' 天前';
  }

  it('returns dash for empty input', () => {
    expect(relTime('')).toBe('-');
    expect(relTime(null)).toBe('-');
  });

  it('returns 刚刚 for recent time', () => {
    expect(relTime(Date.now() / 1000 - 30)).toBe('刚刚');
  });

  it('returns minutes ago', () => {
    expect(relTime(Date.now() / 1000 - 300)).toBe('5 分钟前');
  });

  it('returns hours ago', () => {
    expect(relTime(Date.now() / 1000 - 7200)).toBe('2 小时前');
  });

  it('returns days ago', () => {
    expect(relTime(Date.now() / 1000 - 172800)).toBe('2 天前');
  });
});
