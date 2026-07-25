<!-- docs-signoff: author="grok-4.5" kind="llm" doc="plan" ts="2026-07-24T01:40:00Z" -->

# 拟生记忆架构 Plan — 动态 · 可遗忘 · 可传递 · 感情即选择压

> 完整设计见会话 plan；本文件为仓库落盘版。P0+P1 已落地核心代码。

## 核心判断

1. **前瞻意图（原「未发送队列」）不是记忆层**，是过程缓冲 (prospective)。
2. **情绪电荷**是场（调制巩固/检索），不存事实。
3. **层**：感觉痕迹 · 情节 · 语义核；**可巩固、可遗忘、可传递**。
4. **感情** = 适应度 → 电荷 → 巩固概率（物竞选择压）。

## 分期

| 期 | 内容 | 状态 |
|----|------|------|
| P0 | systems 视图、文案正名、API 兼容 | ✅ |
| P1 | semantic + consolidate_tick + forget_tick + fitness | ✅ |
| P2 | 拓扑慢漂移 + eco EventBus + working | ✅ |
| P3 | 传递叙事 + 中枢分栏 + 遗忘审计 + 工作台 pane | ✅ |
| 增强 | vector-lite + README | ✅ |

## 成功标准

- UI 不再把前瞻意图叫「记忆层」
- consolidate/forget 有单测
- 任务结果写电荷并可注入 tone
