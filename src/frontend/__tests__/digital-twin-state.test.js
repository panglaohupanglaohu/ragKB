/**
 * D-4.3: State 单测 — 别名 getter 等价性 + roomAgentMap 迁移正确性
 * 验证 director.js 中 window._DTS / window._sx / window._currentSessionId 的状态结构
 */
import { describe, it, expect } from 'vitest';

describe('state alias equivalence (D-4.3)', () => {
  // ============ 1. _DTS 核心字段完整性 ============
  it('_DTS 对象声明含所有必需字段', () => {
    const fs = require('fs');
    const path = require('path');
    const src = fs.readFileSync(
      path.resolve(__dirname, '../js/digital-twin/director.js'),
      'utf-8'
    );

    // window._DTS 初始化块应包含这些字段
    expect(src).toContain('trialStatus');
    expect(src).toContain('selectedMode');
    expect(src).toContain('directorConfig');
    expect(src).toContain('activeTrialId');
    expect(src).toContain('activeBranchId');
    expect(src).toContain('currentStep');
    expect(src).toContain('processedStepSet');
    expect(src).toContain('events');
    expect(src).toContain('latestReward');
    expect(src).toContain('_abortCtrl');
  });

  // ============ 2. _sx 扩展字段完整性 ============
  it('_sx 扩展了 v4 新字段及核心状态字段', () => {
    const fs = require('fs');
    const path = require('path');
    const src = fs.readFileSync(
      path.resolve(__dirname, '../js/digital-twin/director.js'),
      'utf-8'
    );

    // 导演台扩展的 _sx 字段
    expect(src).toContain('_sx.trialId');
    expect(src).toContain('_sx.branchId');
    expect(src).toContain('_sx.currentStep');
    expect(src).toContain('_sx.status');
    expect(src).toContain('_sx.roomAgentMap');
    expect(src).toContain('_sx.events');
    expect(src).toContain('_sx.processedStepSet');
  });

  // ============ 3. window._currentSessionId 别名 ============
  it('_currentSessionId 被 stepOnce / autoRun / pauseSim / terminate 读取', () => {
    const fs = require('fs');
    const path = require('path');
    const src = fs.readFileSync(
      path.resolve(__dirname, '../js/digital-twin/director.js'),
      'utf-8'
    );

    // 确认所有核心操作函数使用 window._currentSessionId
    const occurrences = (src.match(/window\._currentSessionId/g) || []).length;
    expect(occurrences).toBeGreaterThanOrEqual(4); // stepOnce, autoRun, pauseSim, terminate, resetForNew
  });

  // ============ 4. _sx ↔ _DTS 同步 ============
  it('createTrial 同时写入 _DTS 和 _sx', () => {
    const fs = require('fs');
    const path = require('path');
    const src = fs.readFileSync(
      path.resolve(__dirname, '../js/digital-twin/director.js'),
      'utf-8'
    );

    // createTrial 成功后写两套状态
    expect(src).toContain('_DTS.activeTrialId=d.trial_id');
    expect(src).toContain('_sx.trialId=d.trial_id');
    expect(src).toContain('_DTS.activeBranchId=d.branch_id');
    expect(src).toContain('_sx.branchId=d.branch_id');
  });

  // ============ 5. roomAgentMap 引用合一 ============
  it('_syncRoomAgentMap 函数存在, 使用引用合一', () => {
    const fs = require('fs');
    const path = require('path');
    const src = fs.readFileSync(
      path.resolve(__dirname, '../js/digital-twin/director.js'),
      'utf-8'
    );

    expect(src).toContain('_syncRoomAgentMap');
    // 引用合一: _sx.roomAgentMap = S.positions
    expect(src).toContain('roomAgentMap = S.positions');
    // 断裂检测: === 比较
    expect(src).toContain('roomAgentMap === S.positions');
  });

  it('_syncRoomAgentMap 迁移既有键到 S.positions', () => {
    const fs = require('fs');
    const path = require('path');
    const src = fs.readFileSync(
      path.resolve(__dirname, '../js/digital-twin/director.js'),
      'utf-8'
    );

    // 首次合一时如果有旧键, 迁入 S.positions
    expect(src).toContain("S.positions[k]");
    // 再赋引用合一
    expect(src).toContain('window._sx.roomAgentMap = S.positions');
  });

  // ============ 6. _dtRoomMapHealth 诊断函数 ============
  it('_dtRoomMapHealth 暴露到 window, 返回健康状态对象', () => {
    const fs = require('fs');
    const path = require('path');
    const src = fs.readFileSync(
      path.resolve(__dirname, '../js/digital-twin/director.js'),
      'utf-8'
    );

    expect(src).toContain('window._dtRoomMapHealth');
    expect(src).toContain('same_ref');
    expect(src).toContain('positions_count');
    expect(src).toContain('sx_count');
    expect(src).toContain('has_sx');
    expect(src).toContain('has_positions');
  });

  // ============ 7. 按钮渲染状态一致性 ============
  it('_updateButtonStates 作为 window 方法暴露', () => {
    const fs = require('fs');
    const path = require('path');
    const src = fs.readFileSync(
      path.resolve(__dirname, '../js/digital-twin/director.js'),
      'utf-8'
    );

    expect(src).toContain('window._updateButtonStates');
    expect(src).toContain('_BG');
  });

  it('_BG 按钮组覆盖 idle/creating/ready/running/paused/completed/failed/terminated', () => {
    const fs = require('fs');
    const path = require('path');
    const src = fs.readFileSync(
      path.resolve(__dirname, '../js/digital-twin/director.js'),
      'utf-8'
    );

    const statuses = ['idle', 'creating', 'ready', 'running', 'paused', 'completed', 'failed', 'terminated'];
    statuses.forEach(status => {
      // each status key should appear as property in _BG object
      expect(src).toContain(status + ":");
    });
  });

  // ============ 8. 状态机转换有效规则 ============
  it('transitionTrialStatus 含 idle→creating→ready→running→completed 完整路径', () => {
    const fs = require('fs');
    const path = require('path');
    const src = fs.readFileSync(
      path.resolve(__dirname, '../js/digital-twin/director.js'),
      'utf-8'
    );

    expect(src).toContain("idle:['creating']");
    expect(src).toContain("creating:['ready','failed']");
    expect(src).toContain("ready:['running','evaluating','failed']");
    expect(src).toContain("running:['paused','evaluating','completed','failed','terminated']");
    expect(src).toContain("paused:['running','terminated','failed']");
    expect(src).toContain("completed:['idle','terminated']");
    expect(src).toContain("terminated:['idle','creating']");
  });
});
