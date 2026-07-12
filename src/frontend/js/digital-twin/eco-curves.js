/**
 * eco-curves.js — v3 世代演化曲线三比纯函数（XV-5.2）
 *
 * 三比 = 环比(QoQ) / 同比(YoY) / 综合比(Composite)
 * 全部从 generations[] 数组计算，后端仅需补 diversity/era/fitness_rate 字段。
 */
(function (root) {
  'use strict';

  // ═══ 环比（QoQ）：逐代 Δ ═══
  function computeQoQ(generations) {
    if (!generations || !generations.length) return [];
    var series = [];
    for (var i = 0; i < generations.length; i++) {
      var cur = generations[i];
      var prev = i > 0 ? generations[i - 1] : null;
      var deltaBest = prev ? cur.best_survival_ticks - prev.best_survival_ticks : 0;
      var deltaAvg = prev ? cur.avg_survival_ticks - prev.avg_survival_ticks : 0;
      var deltaDiv = prev ? (cur.diversity || 0) - (prev.diversity || 0) : 0;
      series.push({
        gen: cur.generation,
        era: cur.era || 0,
        best: cur.best_survival_ticks || 0,
        avg: cur.avg_survival_ticks || 0,
        diversity: cur.diversity || 0,
        deltaBest: deltaBest,
        deltaAvg: deltaAvg,
        deltaDiv: deltaDiv,
        deltaBestPct: prev && prev.best_survival_ticks
          ? Math.round((deltaBest / prev.best_survival_ticks) * 100) : 0,
        deltaAvgPct: prev && prev.avg_survival_ticks
          ? Math.round((deltaAvg / prev.avg_survival_ticks) * 100) : 0,
        arrow: deltaBest > 0 ? '↑' : deltaBest < 0 ? '↓' : '→',
        arrowColor: deltaBest > 0 ? '#22c55e' : deltaBest < 0 ? '#f87171' : '#8b9ab5'
      });
    }
    return series;
  }

  // ═══ 同比（YoY）：同相位跨维对比 ═══
  // 混合竞争=按 era 分组，同世代序位对齐
  // 多队对抗=按 population 分组
  function computeYoY(generations, groupBy) {
    if (!generations || !generations.length) return { groups: [], aligned: [] };
    groupBy = groupBy || 'era';   // 'era' or 'population'
    var groups = {};
    generations.forEach(function (g) {
      var key;
      if (groupBy === 'population') {
        var ps = g.population_stats || {};
        var pops = Object.keys(ps);
        pops.forEach(function (pop) {
          if (!groups[pop]) groups[pop] = [];
          groups[pop].push({
            gen: g.generation,
            best: (ps[pop] && ps[pop].best) || g.best_survival_ticks || 0,
            avg: (ps[pop] && ps[pop].avg_survival_ticks) || g.avg_survival_ticks || 0
          });
        });
      } else {
        key = 'era' + (g.era || 0);
        if (!groups[key]) groups[key] = [];
        groups[key].push({
          gen: g.generation,
          best: g.best_survival_ticks || 0,
          avg: g.avg_survival_ticks || 0
        });
      }
    });
    // 同相位对齐：按世代序位（每组内的第 k 个世代对齐）
    var groupKeys = Object.keys(groups);
    var maxLen = Math.max.apply(null, groupKeys.map(function (k) { return groups[k].length; }));
    var aligned = [];
    for (var i = 0; i < maxLen; i++) {
      var row = { index: i };
      groupKeys.forEach(function (k) {
        if (groups[k][i]) {
          row[k] = groups[k][i];
        }
      });
      aligned.push(row);
    }
    return { groups: groupKeys.map(function (k) { return { key: k, data: groups[k] }; }), aligned: aligned };
  }

  // ═══ 综合比（Composite）：归一化上升指数 ═══
  // 公式: index = w1*fitness_rate + w2*avg_rate + w3*diversity + w4*ratchet_progress
  // 权重随环境压力自适应（越严酷，适应率权重越高）
  function computeComposite(generations, env) {
    if (!generations || !generations.length) return [];
    // 环境压力评估
    var predator = (env && env.predator_pressure) || 0;
    var drift = (env && env.drift_prob) || 0;
    var abundance = (env && env.abundance) || 1;
    var stress = Math.min(1, predator * 5 + drift * 2 + (1 - abundance) * 0.5);

    // 权重自适应：压力越高，适应率权重越大
    var w1 = 0.35 + stress * 0.15;   // fitness_rate (best)
    var w2 = 0.25 + stress * 0.10;   // avg_rate
    var w3 = 0.20 - stress * 0.05;   // diversity
    var w4 = 0.20;                    // ratchet_progress
    // 归一化
    var sum = w1 + w2 + w3 + w4;
    w1 /= sum; w2 /= sum; w3 /= sum; w4 /= sum;

    var maxRatchet = Math.max.apply(null, generations.map(function (g) {
      return g.ratchet_value || g.best_survival_ticks || 0;
    })) || 1;

    var series = [];
    for (var i = 0; i < generations.length; i++) {
      var g = generations[i];
      var fitnessRate = g.fitness_rate || (g.best_survival_ticks / maxRatchet);
      var avgRate = maxRatchet > 0 ? (g.avg_survival_ticks || 0) / maxRatchet : 0;
      var diversity = g.diversity || 0.5;
      var ratchetProgress = maxRatchet > 0 ? (g.ratchet_value || g.best_survival_ticks || 0) / maxRatchet : 0;

      var index = w1 * fitnessRate + w2 * avgRate + w3 * diversity + w4 * ratchetProgress;
      series.push({
        gen: g.generation,
        era: g.era || 0,
        index: Math.round(index * 1000) / 1000,
        components: {
          fitness_rate: Math.round(fitnessRate * 1000) / 1000,
          avg_rate: Math.round(avgRate * 1000) / 1000,
          diversity: Math.round(diversity * 1000) / 1000,
          ratchet_progress: Math.round(ratchetProgress * 1000) / 1000
        },
        weights: { w1: w1, w2: w2, w3: w3, w4: w4 },
        stress: Math.round(stress * 100) / 100
      });
    }
    return series;
  }

  // ═══ 导出 ═══
  root.computeQoQ = computeQoQ;
  root.computeYoY = computeYoY;
  root.computeComposite = computeComposite;

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = { computeQoQ: computeQoQ, computeYoY: computeYoY, computeComposite: computeComposite };
  }
})(typeof window !== 'undefined' ? window : globalThis);
