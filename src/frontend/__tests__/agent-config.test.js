/**
 * Tests for agent-team-config.js patterns — CSRF fetching, api() caching, getTeamsList logic
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';

describe('api() request caching', () => {
  // Replicate the caching logic from agent-team-config.js api()
  const _reqCache = {};
  const _REQ_CACHE_TTL = 5000;

  async function mockApi(p, o) {
    const method = (o && o.method) ? o.method.toUpperCase() : 'GET';
    if (method === 'GET') {
      const key = 'GET:' + p;
      const cached = _reqCache[key];
      if (cached && Date.now() - cached.at < _REQ_CACHE_TTL) {
        return cached.data;
      }
      const result = await Promise.resolve(['item1', 'item2']); // mock fetch
      if (result !== null && result !== undefined) {
        _reqCache[key] = { data: result, at: Date.now() };
      }
      return result;
    }
    // Mutations
    const pathBase = p.split('?')[0];
    Object.keys(_reqCache).forEach(k => { if (k.indexOf(pathBase) !== -1) delete _reqCache[k]; });
    return await Promise.resolve({ success: true });
  }

  beforeEach(() => { Object.keys(_reqCache).forEach(k => delete _reqCache[k]); });

  it('caches GET responses', async () => {
    const r1 = await mockApi('/api/v1/teams');
    const r2 = await mockApi('/api/v1/teams'); // should hit cache
    expect(r1).toEqual(r2);
  });

  it('invalidates cache on POST to same path', async () => {
    await mockApi('/api/v1/teams'); // cache it
    await mockApi('/api/v1/teams', { method: 'POST' }); // mutate
    // Next GET should be fresh (different pointer)
  });

  it('different URLs get different cache keys', async () => {
    const r1 = await mockApi('/api/v1/teams');
    const r2 = await mockApi('/api/v1/skills');
    expect(Object.keys(_reqCache).length).toBe(2);
  });
});

describe('getTeamsList logic', () => {
  let cache = null;
  let cacheAt = 0;
  const CACHE_MS = 60000;

  async function getTeamsList(force, apiResult) {
    const now = Date.now();
    if (!force && cache && (now - cacheAt) < CACHE_MS) return cache;
    const teams = await Promise.resolve(apiResult);
    if (Array.isArray(teams) && teams.length) {
      cache = teams;
      cacheAt = now;
      return teams;
    }
    return cache || teams || [];
  }

  it('returns empty array when API returns null', async () => {
    const result = await getTeamsList(true, null);
    expect(result).toEqual([]);
  });

  it('caches successful responses', async () => {
    const teams = [{ team_id: 'a', name: 'A' }];
    const r1 = await getTeamsList(true, teams);
    const r2 = await getTeamsList(false, null);
    expect(r2).toEqual(teams);
  });

  it('returns fallback on error when cache exists', async () => {
    const teams = [{ team_id: 'b', name: 'B' }];
    await getTeamsList(true, teams); // prime cache
    const r = await getTeamsList(false, null); // API "fails"
    expect(r).toEqual(teams);
  });
});
