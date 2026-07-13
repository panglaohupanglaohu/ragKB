/**
 * eco-genetics.js — v3 谱系遗传学化纯函数库（XV-6.1）
 *
 * 从 result.lineage（后代→双亲+世代）+ final_ranking（含 survival/skill/collab）计算六个遗传学维度：
 * D1 遗传力 h²（亲子回归斜率）
 * D2 同类选配（配偶 survival 排名相关）
 * D3 近交衰退 vs 杂种优势（系谱系数 + 跨队后代对照）
 * D4 均值回归（领先血系向均值收敛速度 + 回归半衰期）
 * D5 奠基者贡献（初代对末代基因池贡献）
 * D6 系谱协作演化（collab 基因沿血系传递）
 * + 学派聚类（skill 高频共现簇）
 */
(function (root) {
  'use strict';

  // ═══ D1: 遗传力 h²（亲子回归斜率）═══
  // trait: 'survival_ticks' 或 collab 维度名
  function heritability(lineage, ranking, trait) {
    if (!lineage || !lineage.length || !ranking) return null;
    var rankMap = {};
    ranking.forEach(function (r) { rankMap[r.agent_id] = r; });
    var pairs = [];   // {parentTrait, childTrait}
    lineage.forEach(function (rec) {
      var child = rankMap[rec.child];
      if (!child) return;
      var parents = (rec.parents || []).map(function (pid) { return rankMap[pid]; }).filter(Boolean);
      if (!parents.length) return;
      var parentTrait;
      if (trait === 'survival_ticks') {
        parentTrait = parents.reduce(function (s, p) { return s + (p.survival_ticks || 0); }, 0) / parents.length;
      } else {
        // collab 维度
        parentTrait = parents.reduce(function (s, p) {
          return s + ((p.collab_genome && p.collab_genome[trait]) || 0.5);
        }, 0) / parents.length;
      }
      var childTrait;
      if (trait === 'survival_ticks') {
        childTrait = child.survival_ticks || 0;
      } else {
        childTrait = (child.collab_genome && child.collab_genome[trait]) || 0.5;
      }
      pairs.push({ parent: parentTrait, child: childTrait });
    });
    if (pairs.length < 2) return null;
    // 线性回归斜率 = h²
    var n = pairs.length;
    var sumX = pairs.reduce(function (s, p) { return s + p.parent; }, 0);
    var sumY = pairs.reduce(function (s, p) { return s + p.child; }, 0);
    var sumXY = pairs.reduce(function (s, p) { return s + p.parent * p.child; }, 0);
    var sumXX = pairs.reduce(function (s, p) { return s + p.parent * p.parent; }, 0);
    var denom = n * sumXX - sumX * sumX;
    if (Math.abs(denom) < 1e-10) return null;
    var slope = (n * sumXY - sumX * sumY) / denom;
    return { h2: Math.round(slope * 1000) / 1000, pairs: pairs.length, trait: trait };
  }

  // ═══ D2: 同类选配（配偶 survival 排名相关系数）═══
  function assortativeMating(lineage, ranking) {
    if (!lineage || !lineage.length || !ranking) return null;
    var rankMap = {};
    ranking.forEach(function (r, i) { rankMap[r.agent_id] = r; });
    // 收集配对双方的 survival_ticks
    var pairs = [];
    var seen = {};
    lineage.forEach(function (rec) {
      if (!rec.parents || rec.parents.length < 2) return;
      var key = rec.parents.slice().sort().join('|');
      if (seen[key]) return;
      seen[key] = 1;
      var p1 = rankMap[rec.parents[0]], p2 = rankMap[rec.parents[1]];
      if (p1 && p2) {
        pairs.push({ a: p1.survival_ticks || 0, b: p2.survival_ticks || 0 });
      }
    });
    if (pairs.length < 3) return null;
    // Pearson 相关系数
    var n = pairs.length;
    var sumA = pairs.reduce(function (s, p) { return s + p.a; }, 0);
    var sumB = pairs.reduce(function (s, p) { return s + p.b; }, 0);
    var meanA = sumA / n, meanB = sumB / n;
    var num = pairs.reduce(function (s, p) { return s + (p.a - meanA) * (p.b - meanB); }, 0);
    var denA = Math.sqrt(pairs.reduce(function (s, p) { return s + (p.a - meanA) * (p.a - meanA); }, 0));
    var denB = Math.sqrt(pairs.reduce(function (s, p) { return s + (p.b - meanB) * (p.b - meanB); }, 0));
    if (denA < 1e-10 || denB < 1e-10) return null;
    var r = num / (denA * denB);
    return { r: Math.round(r * 1000) / 1000, pairs: pairs.length };
  }

  // ═══ D3: 近交系数 / 杂种优势 ═══
  function coefficientOfRelationship(lineage, ranking) {
    if (!lineage || !lineage.length) return null;
    var rankMap = {};
    ranking.forEach(function (r) { rankMap[r.agent_id] = r; });
    // 统计跨队 vs 队内后代
    var hybrid = [], inbred = [];
    lineage.forEach(function (rec) {
      if (!rec.parents || rec.parents.length < 2) return;
      var p1 = rankMap[rec.parents[0]], p2 = rankMap[rec.parents[1]];
      if (!p1 || !p2) return;
      var child = rankMap[rec.child];
      if (!child) return;
      if (p1.population !== p2.population) {
        hybrid.push(child.survival_ticks || 0);
      } else {
        inbred.push(child.survival_ticks || 0);
      }
    });
    var hybridAvg = hybrid.length ? hybrid.reduce(function (a, b) { return a + b; }, 0) / hybrid.length : 0;
    var inbredAvg = inbred.length ? inbred.reduce(function (a, b) { return a + b; }, 0) / inbred.length : 0;
    return {
      hybrid_count: hybrid.length,
      inbred_count: inbred.length,
      hybrid_avg: Math.round(hybridAvg * 10) / 10,
      inbred_avg: Math.round(inbredAvg * 10) / 10,
      heterosis_delta: Math.round((hybridAvg - inbredAvg) * 10) / 10
    };
  }

  // ═══ D4: 均值回归（领先血系向均值收敛速度 + 回归半衰期）═══
  function regressionToMean(lineage, ranking) {
    if (!lineage || !lineage.length || !ranking) return null;
    var rankMap = {};
    ranking.forEach(function (r) { rankMap[r.agent_id] = r; });
    // 按世代分组计算每代均值
    var genMeans = {};
    ranking.forEach(function (r) {
      var g = r.generation || 0;
      if (!genMeans[g]) genMeans[g] = { sum: 0, count: 0 };
      genMeans[g].sum += r.survival_ticks || 0;
      genMeans[g].count += 1;
    });
    var gens = Object.keys(genMeans).map(Number).sort(function (a, b) { return a - b; });
    if (gens.length < 2) return null;
    var means = gens.map(function (g) { return genMeans[g].sum / genMeans[g].count; });

    // 追踪领先血系（初代 top-k 的后代轨迹）
    var topK = ranking.filter(function (r) { return !r.generation || r.generation === 0; })
      .sort(function (a, b) { return b.survival_ticks - a.survival_ticks; }).slice(0, 3);
    if (!topK.length) return null;

    // 构建后代映射
    var childMap = {};   // parent_id -> [child_id, ...]
    lineage.forEach(function (rec) {
      (rec.parents || []).forEach(function (pid) {
        if (!childMap[pid]) childMap[pid] = [];
        childMap[pid].push(rec.child);
      });
    });

    // 追踪领先血系的后代每代均值
    var trajectory = [];
    function descendantsAtGen(ids, targetGen) {
      var current = ids;
      for (var g = 1; g <= targetGen; g++) {
        var next = [];
        current.forEach(function (id) {
          (childMap[id] || []).forEach(function (cid) { next.push(cid); });
        });
        current = next;
      }
      return current;
    }
    for (var g = 0; g < gens.length; g++) {
      var descIds = g === 0 ? topK.map(function (r) { return r.agent_id; }) : descendantsAtGen(topK.map(function (r) { return r.agent_id; }), g);
      var descRanks = descIds.map(function (id) { return rankMap[id]; }).filter(Boolean);
      if (descRanks.length) {
        var descAvg = descRanks.reduce(function (s, r) { return s + (r.survival_ticks || 0); }, 0) / descRanks.length;
        trajectory.push({ gen: g, descAvg: Math.round(descAvg * 10) / 10, popMean: Math.round(means[g] * 10) / 10 });
      }
    }

    // 回归半衰期：领先优势衰减一半所需的代数
    var halfLife = null;
    if (trajectory.length >= 2) {
      var initialAdvantage = trajectory[0].descAvg - trajectory[0].popMean;
      if (initialAdvantage > 0) {
        for (var i = 1; i < trajectory.length; i++) {
          var adv = trajectory[i].descAvg - trajectory[i].popMean;
          if (adv <= initialAdvantage / 2) {
            halfLife = trajectory[i].gen - trajectory[0].gen;
            break;
          }
        }
        if (halfLife === null) halfLife = '>'.concat(String(trajectory.length - 1));
      }
    }

    return { trajectory: trajectory, half_life: halfLife, initial_advantage: trajectory[0] ? Math.round((trajectory[0].descAvg - trajectory[0].popMean) * 10) / 10 : 0 };
  }

  // ═══ D5: 奠基者贡献（初代对末代基因池贡献）═══
  function founderContribution(lineage, ranking) {
    if (!ranking || !ranking.length) return null;
    var maxGen = Math.max.apply(null, ranking.map(function (r) { return r.generation || 0; }));
    if (maxGen === 0) return null;   // 只有一代，无谱系
    var founders = ranking.filter(function (r) { return !r.generation || r.generation === 0; });
    var lastGen = ranking.filter(function (r) { return r.generation === maxGen; });
    if (!founders.length || !lastGen.length) return null;

    // 构建后代映射
    var childMap = {};
    lineage.forEach(function (rec) {
      (rec.parents || []).forEach(function (pid) {
        if (!childMap[pid]) childMap[pid] = [];
        childMap[pid].push(rec.child);
      });
    });

    // 追踪每个奠基者的后代在末代中的数量
    function descendantsAtGen(ids, targetGen) {
      var current = ids;
      for (var g = 1; g <= targetGen; g++) {
        var next = [];
        current.forEach(function (id) {
          (childMap[id] || []).forEach(function (cid) { next.push(cid); });
        });
        current = next;
      }
      return current;
    }
    var lastGenIds = lastGen.map(function (r) { return r.agent_id; });
    var contributions = founders.map(function (f) {
      var desc = descendantsAtGen([f.agent_id], maxGen);
      var inLast = desc.filter(function (id) { return lastGenIds.indexOf(id) >= 0; });
      return { founder: f.agent_id, descendants_in_last_gen: inLast.length, pct: Math.round(inLast.length / lastGen.length * 100) };
    }).sort(function (a, b) { return b.descendants_in_last_gen - a.descendants_in_last_gen; });

    // 瓶颈世代（存活骤降）
    var genCounts = {};
    ranking.forEach(function (r) {
      var g = r.generation || 0;
      genCounts[g] = (genCounts[g] || 0) + 1;
    });
    var bottleneck = null;
    var gens = Object.keys(genCounts).map(Number).sort(function (a, b) { return a - b; });
    for (var i = 1; i < gens.length; i++) {
      if (genCounts[gens[i]] < genCounts[gens[i - 1]] * 0.5) {
        bottleneck = { gen: gens[i], count: genCounts[gens[i]], prev_count: genCounts[gens[i - 1]] };
        break;
      }
    }
    return { contributions: contributions, bottleneck: bottleneck, max_gen: maxGen };
  }

  // ═══ D6: 系谱协作演化（collab 基因沿血系传递）═══
  function collabLineageFlow(lineage, ranking) {
    if (!lineage || !lineage.length || !ranking) return null;
    var rankMap = {};
    ranking.forEach(function (r) { rankMap[r.agent_id] = r; });
    var dims = ['share_tendency', 'signal_tendency', 'follow_tendency', 'mate_choosiness'];
    var flow = {};
    dims.forEach(function (d) { flow[d] = { parent_sum: 0, child_sum: 0, count: 0 }; });
    lineage.forEach(function (rec) {
      var child = rankMap[rec.child];
      if (!child) return;
      var parents = (rec.parents || []).map(function (pid) { return rankMap[pid]; }).filter(Boolean);
      if (!parents.length) return;
      dims.forEach(function (d) {
        var pAvg = parents.reduce(function (s, p) {
          return s + ((p.collab_genome && p.collab_genome[d]) || 0.5);
        }, 0) / parents.length;
        var cVal = (child.collab_genome && child.collab_genome[d]) || 0.5;
        flow[d].parent_sum += pAvg;
        flow[d].child_sum += cVal;
        flow[d].count += 1;
      });
    });
    var result = {};
    dims.forEach(function (d) {
      if (flow[d].count > 0) {
        result[d] = {
          parent_avg: Math.round(flow[d].parent_sum / flow[d].count * 1000) / 1000,
          child_avg: Math.round(flow[d].child_sum / flow[d].count * 1000) / 1000,
          delta: Math.round((flow[d].child_sum - flow[d].parent_sum) / flow[d].count * 1000) / 1000,
          count: flow[d].count
        };
      }
    });
    return result;
  }

  // ═══ 学派聚类（skill 高频共现簇）═══
  function schoolClusters(ranking) {
    if (!ranking || !ranking.length) return [];
    // 统计 skill 共现
    var cooccur = {};   // "s1|s2" -> count
    ranking.forEach(function (r) {
      var skills = (r.skill_genome || []).slice();
      for (var i = 0; i < skills.length; i++) {
        for (var j = i + 1; j < skills.length; j++) {
          var key = skills[i] < skills[j] ? skills[i] + '|' + skills[j] : skills[j] + '|' + skills[i];
          cooccur[key] = (cooccur[key] || 0) + 1;
        }
      }
    });
    // 阈值：共现 >= 2 视为同簇
    var pairs = Object.keys(cooccur).filter(function (k) { return cooccur[k] >= 2; })
      .map(function (k) { return { a: k.split('|')[0], b: k.split('|')[1], count: cooccur[k] }; })
      .sort(function (a, b) { return b.count - a.count; });
    // 简单并查集聚类
    var parent = {};
    function find(x) { while (parent[x] && parent[x] !== x) { parent[x] = parent[parent[x]] || parent[x]; x = parent[x]; } return x; }
    function union(a, b) { var ra = find(a), rb = find(b); if (ra !== rb) parent[ra] = rb; }
    pairs.forEach(function (p) { parent[p.a] = p.a; parent[p.b] = p.b; });
    pairs.forEach(function (p) { union(p.a, p.b); });
    var clusters = {};
    Object.keys(parent).forEach(function (k) {
      var root = find(k);
      if (!clusters[root]) clusters[root] = [];
      clusters[root].push(k);
    });
    return Object.values(clusters).filter(function (c) { return c.length >= 2; })
      .map(function (c) { return { skills: c, size: c.length }; })
      .sort(function (a, b) { return b.size - a.size; });
  }

  // ═══ v4 XG-9: 计划技能覆盖热力 ═══
  // rows = agents, cols = plan steps/skills; cell 1 if agent holds skill
  function planCoverageHeatmap(ranking, contract) {
    if (!ranking || !ranking.length) return { agents: [], skills: [], matrix: [], coverage: 0 };
    var niches = (contract && contract.niches) || [];
    var skills = [];
    niches.forEach(function (n) {
      (n.demanded_skills || []).forEach(function (s) {
        if (skills.indexOf(s) < 0) skills.push(s);
      });
    });
    if (!skills.length && contract && contract.skill_universe) {
      skills = (contract.skill_universe || []).slice();
    }
    var agents = ranking.map(function (r) {
      return {
        agent_id: r.agent_id,
        alive: !!r.alive,
        survival_ticks: r.survival_ticks || 0,
        skills: r.skill_genome || []
      };
    });
    var matrix = agents.map(function (a) {
      var set = {};
      (a.skills || []).forEach(function (s) { set[s] = 1; });
      return skills.map(function (sk) { return set[sk] ? 1 : 0; });
    });
    var total = agents.length * Math.max(skills.length, 1);
    var hits = 0;
    matrix.forEach(function (row) { row.forEach(function (v) { hits += v; }); });
    return {
      agents: agents.map(function (a) { return a.agent_id; }),
      skills: skills,
      matrix: matrix,
      coverage: total ? Math.round(hits / total * 1000) / 1000 : 0,
      niches: niches.map(function (n) { return { title: n.title, skills: n.demanded_skills || [] }; })
    };
  }

  // ═══ v4: 分 skill 遗传力（亲代是否持有 → 子代是否持有，回归近似）═══
  function perSkillHeritability(lineage, ranking, skill) {
    if (!lineage || !lineage.length || !ranking || !skill) return null;
    var rankMap = {};
    ranking.forEach(function (r) { rankMap[r.agent_id] = r; });
    var pairs = [];
    lineage.forEach(function (rec) {
      var child = rankMap[rec.child];
      if (!child) return;
      var parents = (rec.parents || []).map(function (pid) { return rankMap[pid]; }).filter(Boolean);
      if (!parents.length) return;
      var pHas = parents.filter(function (p) {
        return (p.skill_genome || []).indexOf(skill) >= 0;
      }).length / parents.length;
      var cHas = (child.skill_genome || []).indexOf(skill) >= 0 ? 1 : 0;
      pairs.push({ parent: pHas, child: cHas });
    });
    if (pairs.length < 2) return null;
    var n = pairs.length;
    var sumX = pairs.reduce(function (s, p) { return s + p.parent; }, 0);
    var sumY = pairs.reduce(function (s, p) { return s + p.child; }, 0);
    var sumXY = pairs.reduce(function (s, p) { return s + p.parent * p.child; }, 0);
    var sumXX = pairs.reduce(function (s, p) { return s + p.parent * p.parent; }, 0);
    var denom = n * sumXX - sumX * sumX;
    if (Math.abs(denom) < 1e-10) return { h2: 0, pairs: n, skill: skill };
    var slope = (n * sumXY - sumX * sumY) / denom;
    return { h2: Math.round(slope * 1000) / 1000, pairs: n, skill: skill };
  }

  // ═══ v4: 垂直(遗传) vs 水平(学习) 传递比 ═══
  // timeline.steps[].skill_origins: [{agent_id, skill, origin: learn|inherit|mutate}]
  function verticalVsHorizontalTransfer(timeline) {
    var steps = (timeline && timeline.steps) || [];
    var counts = { learn: 0, inherit: 0, mutate: 0, other: 0 };
    steps.forEach(function (fr) {
      (fr.skill_origins || []).forEach(function (ev) {
        var o = (ev && ev.origin) || 'other';
        if (counts[o] != null) counts[o] += 1;
        else counts.other += 1;
      });
    });
    // lineage 作为垂直传递的代理计数（若 timeline 无 inherit 事件）
    var vertical = counts.inherit;
    var horizontal = counts.learn;
    var total = vertical + horizontal + counts.mutate + counts.other;
    return {
      learn: counts.learn,
      inherit: counts.inherit,
      mutate: counts.mutate,
      other: counts.other,
      vertical_ratio: total ? Math.round(vertical / total * 1000) / 1000 : 0,
      horizontal_ratio: total ? Math.round(horizontal / total * 1000) / 1000 : 0,
      total: total
    };
  }

  // ═══ 导出 ═══
  root.heritability = heritability;
  root.assortativeMating = assortativeMating;
  root.coefficientOfRelationship = coefficientOfRelationship;
  root.regressionToMean = regressionToMean;
  root.founderContribution = founderContribution;
  root.collabLineageFlow = collabLineageFlow;
  root.schoolClusters = schoolClusters;
  root.planCoverageHeatmap = planCoverageHeatmap;
  root.perSkillHeritability = perSkillHeritability;
  root.verticalVsHorizontalTransfer = verticalVsHorizontalTransfer;

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
      heritability: heritability, assortativeMating: assortativeMating,
      coefficientOfRelationship: coefficientOfRelationship, regressionToMean: regressionToMean,
      founderContribution: founderContribution, collabLineageFlow: collabLineageFlow,
      schoolClusters: schoolClusters,
      planCoverageHeatmap: planCoverageHeatmap,
      perSkillHeritability: perSkillHeritability,
      verticalVsHorizontalTransfer: verticalVsHorizontalTransfer
    };
  }
})(typeof window !== 'undefined' ? window : globalThis);
