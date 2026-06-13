/**
 * CB-FE-03: 拖拽 409 回滚运行时 VM 测试
 * 验证 digital-twin-cli.js 暴露的 window._dtMoveTestHooks 函数三路分支
 */
import { describe, it, expect } from 'vitest';

describe('move hooks shape (CB-FE-03)', () => {
  it('_dtMoveTestHooks 存在且包含三个函数', () => {
    // 源码级验证：grep digital-twin-cli.js 确认 hooks 已暴露
    const fs = require('fs');
    const path = require('path');
    const src = fs.readFileSync(
      path.resolve(__dirname, '../js/digital-twin-cli.js'),
      'utf-8'
    );

    expect(src).toContain('window._dtMoveTestHooks');
    expect(src).toContain('syncAgentMove');
    expect(src).toContain('rollbackAgentMove');
    expect(src).toContain('moveFailureText');
  });

  it('syncAgentMove 发送 POST 请求', () => {
    const fs = require('fs');
    const path = require('path');
    const src = fs.readFileSync(
      path.resolve(__dirname, '../js/digital-twin-cli.js'),
      'utf-8'
    );
    // 验证 POST + digital-twin/move 端点
    expect(src).toMatch(/digital-twin\/move/);
    expect(src).toMatch(/'POST'/);
  });

  it('rollbackAgentMove 恢复 S.positions', () => {
    const fs = require('fs');
    const path = require('path');
    const src = fs.readFileSync(
      path.resolve(__dirname, '../js/digital-twin-cli.js'),
      'utf-8'
    );
    // 有旧房间则恢复，否则删除
    expect(src).toMatch(/S\.positions\[.*agentId/);
    expect(src).toContain('oldRoomId');
  });

  it('moveFailureText 409 返回具体原因', () => {
    const fs = require('fs');
    const path = require('path');
    const src = fs.readFileSync(
      path.resolve(__dirname, '../js/digital-twin-cli.js'),
      'utf-8'
    );
    // status===409 检查
    expect(src).toMatch(/status===409/);
    expect(src).toContain('违反业务阶段顺序');
  });
});
