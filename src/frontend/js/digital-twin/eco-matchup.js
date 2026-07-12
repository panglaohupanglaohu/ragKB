/**
 * eco-matchup.js — v3 多队对抗排兵布阵策略表（XV-3.2）
 *
 * 可插拔策略注册表 + 统一局分裁定框架。
 * 策略只决定「怎么排」，胜负永远由已产出的 survival_ticks 决定。
 *
 * 策略接口:
 *   Strategy = { id, name, icon, desc, arrange(myRanked, oppRanked, ctx) -> [{lane, mine, opp}] }
 *   - myRanked/oppRanked: 已按 survival_ticks 降序的梯队
 *   - ctx: { laneDemands?: [skill_id,...], nicheCapacity?: int, env?: {...} }
 *   - 返回: 双方成员到 lane 的合法排列（无重复/遗漏）
 *
 * 局分裁定（框架统一做，策略不参与）:
 *   每个 lane 比 survival_ticks（同 lane 高者胜），汇总 W-L-D。
 */
(function (root) {
  'use strict';

  // ═══ 局分裁定（框架统一，策略不可覆盖） ═══
  function adjudicate(lanes) {
    var w = 0, l = 0, d = 0;
    for (var i = 0; i < lanes.length; i++) {
      var lane = lanes[i];
      if (!lane.mine || !lane.opp) continue;
      if (lane.mine.survival_ticks > lane.opp.survival_ticks) w++;
      else if (lane.mine.survival_ticks < lane.opp.survival_ticks) l++;
      else d++;
    }
    return { w: w, l: l, d: d, total: lanes.length };
  }

  // ═══ 内置 7 策略 ═══

  // ⚔️ head_on: 正面对决（基线）—— rank-i vs rank-i
  var headOn = {
    id: 'head_on', name: '正面对决', icon: '⚔️',
    desc: 'rank-i vs rank-i，纯实力硬碰。诚实基准线，其他策略局分减去 head_on 才知道策略贡献多少。',
    arrange: function (my, opp, ctx) {
      var n = Math.min(my.length, opp.length);
      var lanes = [];
      for (var i = 0; i < n; i++) {
        lanes.push({ lane: i + 1, mine: my[i], opp: opp[i] });
      }
      return lanes;
    }
  };

  // 🐎 tianji: 田忌错位最优（贪心=最优「优势洗牌」）
  // 算法: 两队排序；双指针从对手最强开始，用我方仍能击败他的最弱者去接；
  //        若我方最强都打不过当前对手，则弃——派我方最弱者去当炮灰。
  var tianji = {
    id: 'tianji', name: '田忌赛马', icon: '🐎',
    desc: '求最大化局分的错位排列（弃最弱对其最强，其余错位上顶）。弱队能否靠排兵翻盘；错位价值=最优局分−基线局分。',
    arrange: function (my, opp, ctx) {
      // my, opp 已按 survival_ticks 降序
      var myCopy = my.slice();
      var oppCopy = opp.slice();
      var n = Math.min(myCopy.length, oppCopy.length);
      var lanes = [];
      var myLo = 0, myHi = myCopy.length - 1;   // myCopy[myLo..myHi] 是可用区间
      // 对手从最强开始（opp[0] 最强），逐个分配
      for (var oi = 0; oi < n; oi++) {
        var oppCur = oppCopy[oi];
        if (myCopy[myLo].survival_ticks > oppCur.survival_ticks) {
          // 我方最弱的仍能赢对手 → 用最弱的去赢
          lanes.push({ lane: oi + 1, mine: myCopy[myLo], opp: oppCur });
          myLo++;
        } else {
          // 我方最弱的打不过 → 派最弱的当炮灰，留强者后续
          lanes.push({ lane: oi + 1, mine: myCopy[myHi], opp: oppCur });
          myHi--;
        }
      }
      return lanes;
    }
  };

  // 🔱 spearhead: 集中突破——top-k 主力全押到最可能赢的少数 lane
  var spearhead = {
    id: 'spearhead', name: '集中突破', icon: '🔱',
    desc: '把 top-k 主力全押到最可能赢的少数 lane，其余 lane 放弃。赌局部碾压，看能否以少胜多。',
    arrange: function (my, opp, ctx) {
      var n = Math.min(my.length, opp.length);
      var k = Math.ceil(n / 2) + 1;   // 锁定过半即赢的最小集
      if (k > n) k = n;
      // 算我方每人对各 lane（opp 排序固定）的赢面 margin
      var margins = [];
      for (var mi = 0; mi < my.length; mi++) {
        for (var oi = 0; oi < n; oi++) {
          margins.push({
            mi: mi, oi: oi,
            margin: my[mi].survival_ticks - (opp[oi] ? opp[oi].survival_ticks : -1)
          });
        }
      }
      margins.sort(function (a, b) { return b.margin - a.margin; });
      // 贪心选 top-k: 每个 lane 只选一人，每人只选一次
      var usedMy = {}, usedOpp = {};
      var lanes = [];
      var picked = 0;
      for (var i = 0; i < margins.length && picked < k; i++) {
        var m = margins[i];
        if (usedMy[m.mi] || usedOpp[m.oi]) continue;
        if (m.margin <= 0) continue;   // 只选能赢的
        lanes.push({ lane: m.oi + 1, mine: my[m.mi], opp: opp[m.oi] });
        usedMy[m.mi] = 1; usedOpp[m.oi] = 1;
        picked++;
      }
      // 剩余 lane 填我方最弱者（弃子）
      var remaining = my.filter(function (_, idx) { return !usedMy[idx]; });
      var rIdx = 0;
      for (var oi2 = 0; oi2 < n; oi2++) {
        if (usedOpp[oi2]) continue;
        if (rIdx < remaining.length) {
          lanes.push({ lane: oi2 + 1, mine: remaining[rIdx], opp: opp[oi2] });
          rIdx++;
        }
      }
      // 按 lane 排序
      lanes.sort(function (a, b) { return a.lane - b.lane; });
      return lanes;
    }
  };

  // 🛡 balanced: 均衡布防（maximin）—— 消灭负 margin 峰值
  // 启发式: 把我方按 survival_ticks 升序，均匀分配到 lane（弱者填弱 lane，强者补强 lane），
  //          目标是各 lane 胜率方差最小。小 n 用「轮转均衡」。
  var balanced = {
    id: 'balanced', name: '均衡布防', icon: '🛡',
    desc: '最小化各 lane 胜率方差，杜绝爆冷失分。无短板打法；牺牲上限换稳定。对手也重排时保底最高。',
    arrange: function (my, opp, ctx) {
      // 均衡: 我方升序，对手降序，交叉配对（让弱者碰强者是不可避免的，但均匀分摊）
      var myAsc = my.slice().sort(function (a, b) { return a.survival_ticks - b.survival_ticks; });
      var oppDesc = opp.slice();
      var n = Math.min(myAsc.length, oppDesc.length);
      var lanes = [];
      // 蛇形分配: 偶数轮正序，奇数轮反序，避免强者全堆一端
      var half = Math.ceil(n / 2);
      for (var i = 0; i < n; i++) {
        var myIdx = i % 2 === 0 ? i : (n - 1 - Math.floor(i / 2));
        if (myIdx >= myAsc.length) myIdx = i;
        lanes.push({ lane: i + 1, mine: myAsc[myIdx], opp: oppDesc[i] });
      }
      return lanes;
    }
  };

  // 🌊 attrition: 梯次消耗——按实力升序上场（弱者先耗生态位名额/捕食压力，强者后收割）
  // 诚实边界: 这是复盘近似（对已产出 survival_ticks 做时序加权估计），标注「估计值」
  var attrition = {
    id: 'attrition', name: '梯次消耗', icon: '🌊',
    desc: '按实力升序上场（弱者先耗生态位名额/捕食压力，强者后收割）。利用 niche_capacity 机制的时序博弈。⚠ 估计值——survival_ticks 在既定出场环境下产生，纯重排无法完整体现时序红利。',
    arrange: function (my, opp, ctx) {
      var myAsc = my.slice().sort(function (a, b) { return a.survival_ticks - b.survival_ticks; });
      var oppDesc = opp.slice();
      var n = Math.min(myAsc.length, oppDesc.length);
      var lanes = [];
      for (var i = 0; i < n; i++) {
        lanes.push({ lane: i + 1, mine: myAsc[i], opp: oppDesc[n - 1 - i] });   // 弱者碰强者（先牺牲），强者碰弱者（后收割）
      }
      return lanes;
    }
  };

  // 🎯 skill_counter: 克制反制——按 skill_genome 与 lane 需求的匹配度指派
  // 需 lane 带 demand_skill 标签（ctx.laneDemands）；无标签时退化为 head_on
  var skillCounter = {
    id: 'skill_counter', name: '克制反制', icon: '🎯',
    desc: '不看谁强，看谁对路——每条 lane 有生态位需求，派 skill_genome 最匹配的人去。专精克制通才。',
    arrange: function (my, opp, ctx) {
      var demands = (ctx && ctx.laneDemands) || null;
      var n = Math.min(my.length, opp.length);
      if (!demands || demands.length < n) {
        // 无需求标签 → 退化为正面对决
        return headOn.arrange(my, opp, ctx);
      }
      // 对每条 lane，算我方每人的匹配度 = skill_genome 包含 demand_skill ? 1 : 0
      // 做二分图最大权匹配（小 n 用贪心）
      var scores = [];
      for (var mi = 0; mi < my.length; mi++) {
        for (var li = 0; li < n; li++) {
          var skill = demands[li];
          var match = (my[mi].skill_genome || []).indexOf(skill) >= 0 ? 1 : 0;
          scores.push({ mi: mi, li: li, match: match, survival: my[mi].survival_ticks });
        }
      }
      // 先按 match 降序，再按 survival 降序
      scores.sort(function (a, b) {
        if (b.match !== a.match) return b.match - a.match;
        return b.survival - a.survival;
      });
      var usedMy = {}, usedLane = {};
      var lanes = [];
      for (var i = 0; i < scores.length; i++) {
        var s = scores[i];
        if (usedMy[s.mi] || usedLane[s.li]) continue;
        lanes.push({ lane: s.li + 1, mine: my[s.mi], opp: opp[s.li] });
        usedMy[s.mi] = 1; usedLane[s.li] = 1;
        if (lanes.length >= n) break;
      }
      lanes.sort(function (a, b) { return a.lane - b.lane; });
      return lanes;
    }
  };

  // 🎲 random: 随机（对照）—— 蒙特卡洛 M 次取期望
  var randomStrategy = {
    id: 'random', name: '随机对照', icon: '🎲',
    desc: '随机指派，多次取期望。一切策略的下限锚点——真实增益=策略局分−random期望局分。',
    arrange: function (my, opp, ctx) {
      var myShuffled = my.slice();
      // Fisher-Yates shuffle
      for (var i = myShuffled.length - 1; i > 0; i--) {
        var j = Math.floor(Math.random() * (i + 1));
        var tmp = myShuffled[i]; myShuffled[i] = myShuffled[j]; myShuffled[j] = tmp;
      }
      var n = Math.min(myShuffled.length, opp.length);
      var lanes = [];
      for (var k = 0; k < n; k++) {
        lanes.push({ lane: k + 1, mine: myShuffled[k], opp: opp[k] });
      }
      return lanes;
    }
  };

  // ═══ 可插拔注册表 ═══
  var MATCHUP_STRATEGIES = {};
  function registerMatchupStrategy(s) {
    if (!s || !s.id || typeof s.arrange !== 'function') return;
    MATCHUP_STRATEGIES[s.id] = s;
  }
  function getMatchupStrategy(id) { return MATCHUP_STRATEGIES[id] || null; }
  function listMatchupStrategies() {
    return Object.values(MATCHUP_STRATEGIES);
  }

  // 注册内置 7 策略
  [headOn, tianji, spearhead, balanced, attrition, skillCounter, randomStrategy].forEach(registerMatchupStrategy);

  // ═══ 全策略对比（诊断矩阵） ═══
  function runAllStrategies(myRanked, oppRanked, ctx) {
    var results = [];
    var strategies = listMatchupStrategies();
    for (var i = 0; i < strategies.length; i++) {
      var s = strategies[i];
      var lanes;
      if (s.id === 'random') {
        // 蒙特卡洛 M=200 取期望
        var M = 200;
        var totalW = 0, totalL = 0, totalD = 0;
        for (var m = 0; m < M; m++) {
          var rLanes = s.arrange(myRanked, oppRanked, ctx);
          var r = adjudicate(rLanes);
          totalW += r.w; totalL += r.l; totalD += r.d;
        }
        results.push({
          id: s.id, name: s.name, icon: s.icon, desc: s.desc,
          w: totalW / M, l: totalL / M, d: totalD / M,
          isExpected: true   // 标注为期望值
        });
      } else {
        lanes = s.arrange(myRanked, oppRanked, ctx);
        var r2 = adjudicate(lanes);
        results.push({
          id: s.id, name: s.name, icon: s.icon, desc: s.desc,
          w: r2.w, l: r2.l, d: r2.d,
          lanes: lanes   // 保留 lane 详情供展示
        });
      }
    }
    return results;
  }

  // ═══ 能力性格诊断判读 ═══
  function diagnosePersonality(results) {
    // results = runAllStrategies 输出
    var byId = {};
    results.forEach(function (r) { byId[r.id] = r; });
    var headOn = byId.head_on || {};
    var tianjiR = byId.tianji || {};
    var balancedR = byId.balanced || {};
    var spearheadR = byId.spearhead || {};
    var skillCounterR = byId.skill_counter || {};
    var attritionR = byId.attrition || {};
    var randomR = byId.random || {};

    var diagnoses = [];
    var headOnW = headOn.w || 0;
    var tianjiW = tianjiR.w || 0;
    var balancedW = balancedR.w || 0;
    var spearheadW = spearheadR.w || 0;
    var skillCounterW = skillCounterR.w || 0;
    var randomW = randomR.w || 0;

    if (headOnW > (randomW + 0.5) && balancedW > (randomW + 0.5)) {
      diagnoses.push({ tag: '厚且无短板', color: '#22c55e',
        desc: 'head_on 与 balanced 都赢——实力厚且无软肋，最可靠的强队' });
    }
    if (headOnW <= randomW && tianjiW > headOnW && balancedW <= randomW) {
      diagnoses.push({ tag: '脆弱战术胜', color: '#f87171',
        desc: 'head_on 输、tianji 赢、balanced 输——靠对手不重排；对手一优化就崩，别高估' });
    }
    if (headOnW <= randomW && spearheadW > headOnW) {
      diagnoses.push({ tag: '明星驱动', color: '#f59e0b',
        desc: 'head_on 输、spearhead 赢——深度不足，赢在尖子；关键攻坚可用，铺面易垮' });
    }
    if (skillCounterW > headOnW + 0.5) {
      diagnoses.push({ tag: '专精红利', color: '#22d3ee',
        desc: 'skill_counter 远超 head_on——武器是结构匹配，换环境需重估' });
    }
    var allNearRandom = results.every(function (r) {
      return Math.abs((r.w || 0) - randomW) < 0.5;
    });
    if (allNearRandom) {
      diagnoses.push({ tag: '排布无关', color: '#8b9ab5',
        desc: '各策略都≈random——要么碾压/被碾压，要么纯运气；别过度解读' });
    }
    if (!diagnoses.length) {
      diagnoses.push({ tag: '混合型', color: '#a78bfa',
        desc: '策略间有分化但无极端模式——团队性格需结合具体数据进一步分析' });
    }
    return diagnoses;
  }

  // ═══ 导出 ═══
  root.MATCHUP_STRATEGIES = MATCHUP_STRATEGIES;
  root.registerMatchupStrategy = registerMatchupStrategy;
  root.getMatchupStrategy = getMatchupStrategy;
  root.listMatchupStrategies = listMatchupStrategies;
  root.adjudicateMatchup = adjudicate;
  root.runAllMatchupStrategies = runAllStrategies;
  root.diagnoseMatchupPersonality = diagnosePersonality;

  // CommonJS (vitest)
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
      MATCHUP_STRATEGIES: MATCHUP_STRATEGIES,
      registerMatchupStrategy: registerMatchupStrategy,
      getMatchupStrategy: getMatchupStrategy,
      listMatchupStrategies: listMatchupStrategies,
      adjudicateMatchup: adjudicate,
      runAllMatchupStrategies: runAllStrategies,
      diagnoseMatchupPersonality: diagnosePersonality,
    };
  }
})(typeof window !== 'undefined' ? window : globalThis);
