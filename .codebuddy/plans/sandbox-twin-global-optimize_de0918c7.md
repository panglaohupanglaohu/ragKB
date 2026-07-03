---
name: sandbox-twin-global-optimize
overview: 从全局视角优化 sandbox-twin 模块：补齐内联帮助/引导文案让用户理解每个 UI 区域的功能和使用方法，激活 Lite 模式让仿真不依赖 Docker 也能跑通数据闭环，修复 KPI 数据源绑定让 0/— 变成真实数据流，增加首次使用引导。
todos:
  - id: fix-kpi-bug
    content: 修复 P0 Bug 1：JS loadStats 中 strip-* 元素 id 改为 kpi-*（4 行），让 KPI 栏能显示后端真实数据
    status: completed
  - id: fix-runtime-bug
    content: 修复 P0 Bug 2：renderRuntimeStatus 中 runtime-detail 改为 runtime-drawer__inner（1 行），让 Runtime 详情正确渲染
    status: completed
  - id: add-guide-banner
    content: 添加用户引导横幅：Lite 模式说明 + 一键演示按钮 + 关闭记忆（HTML + CSS + JS）
    status: completed
    dependencies:
      - fix-kpi-bug
      - fix-runtime-bug
  - id: improve-empty-states
    content: 改写空状态文案为引导性 CTA：KPI 栏提示、SOP 空态、历史空态、运行时提示
    status: completed
    dependencies:
      - add-guide-banner
  - id: evolve-loop-visual
    content: SECS Loop 回流可视化：仿真完成时更新回流箭头 label 为"SOP 已沉淀"，EVOLVE 节点标记 done 态
    status: completed
    dependencies:
      - fix-kpi-bug
  - id: runtime-friendly
    content: Runtime 状态友好化：docker n/a→未安装，missing→镜像缺失，抽屉加 Lite 模式说明
    status: completed
    dependencies:
      - fix-runtime-bug
  - id: verify
    content: 整体验证：启动后端，打开 sandbox-twin.html，确认 KPI 有数据、引导横幅可见、点击一键演示能跑通仿真全流程
    status: completed
    dependencies:
      - improve-empty-states
      - evolve-loop-visual
      - runtime-friendly
---

