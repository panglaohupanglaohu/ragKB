<!-- docs-signoff: author="Fable 5" kind="llm" doc="todos" ts="2026-07-12T03:00:00Z" -->
# 物竞天择 · 前端二版 Todos（视觉/交互精修层）

> 配套 [`物竞天择前端二版plan.md`](物竞天择前端二版plan.md)（F2）。
> 状态：`[ ]` 待办 / `[~]` 进行中 / `[x]` 完成。
> **前提**：CodeBuddy 前端一版已把 v3 功能跑通（赛制分派、策略计算、曲线/谱系数据、3D 事件）。本清单只做**呈现精修**，不改数据契约与全局 API。
> 主入口文件：`src/frontend/Agent-digital-twin.html`（`#rp-eco`）、`src/frontend/js/digital-twin/eco-console.js`、新 `eco-console-v2.css`、`js/office/office-scene.js`。

---

## 契约冻结（不许动，防返工）

| 冻结项 | 说明 |
|---|---|
| 结果字段 | `final_ranking / generations / eras / lineage / population_stats / coordination_lift / heterosis / timeline` |
| 全局 API | `eco2RunDrill / eco2SetRaceMode / MATCHUP_STRATEGIES / registerMatchupStrategy / eco2RenderResult` |
| 赛制枚举 | `division / confrontation / mixed`（含 tournament/melee 别名） |
| 布局约束 | `#rp-eco` 与 `#rp-secs` 同级、在布局容器内（bug-028） |

---

## FV-0: 文档【Fable 5 ✅】

- [x] **FV-0.1** 前端二版 plan（F2-0~F2-10）+ 本 todos 写就；docs-signoff ts=2026-07-12；`node scripts/check-docs-signoff.cjs --strict` 本文件 OK。

## FV-1: 设计语言落地

- [ ] **FV-1.1** 生境语义色板变量
  文件：`Agent-digital-twin.html`（`:root` 与 `body.office-mode`）或 `eco-console-v2.css`
  落点：新增 `--eco-life/--eco-gen/--eco-env/--eco-scarce/--eco-death/--eco-hybrid`，深色映射到现有 token，office-mode 给对比度校准过的浅色值。
  验收：深/浅两主题下变量都解析；amber/green 小字在浅底对比 ≥4.5:1（正文）/3:1（图形）。
- [ ] **FV-1.2** 尺度/动效 token + v2 CSS 骨架
  落点：8px 栅格、圆角 3 级、阴影 2 级、字号阶；`--eco-ease:cubic-bezier(.4,0,.2,1)`；`@media (prefers-reduced-motion)` 全局降级钩子；新建 `eco-console-v2.css` 并在 HTML 引入。
  验收：`node --check`/HTML 校验；reduced-motion 下无位移动画。
- [ ] **FV-1.3** `?ecoui=v2` 特性开关
  落点：URL 参数或 localStorage 决定加载 v2 IA/样式；缺省=一版；开关可来回切不报错。
  验收：`?ecoui=v2` 走二版，无参数走一版，两者都能渲染结果。

## FV-2: IA 框架（长滚动→场景化）

- [ ] **FV-2.1** Control Header（sticky 常驻）
  落点：`#rp-eco` 顶部固定条——赛制三档（⚔️分场/🤝多队/🌍混合，接 `eco2SetRaceMode`）+ 团队/对比种群选择 + 环境剧本 chips + 🧬开始（接 `eco2RunDrill`）。
  验收：滚动场景体时 Header 不动；三档切换驱动竞技场景自适应。
- [ ] **FV-2.2** 四场景 Tab（role=tablist，键盘可达）
  落点：🌍生境/🏆竞技/📈演化/🌳血系；切 Tab 只换 Scene Body，不重建 Header/Dock；演练前默认生境、完成自动跳竞技。
  验收：键盘←→切 Tab、aria-selected 正确；切 Tab 不丢回放状态。
- [ ] **FV-2.3** Replay Dock（sticky 底部常驻）
  落点：进度条 + ⏯ + 1x/4x/16x + 帧 KPI + 世代游标；接一版回放引擎（`eco-replay`）。
  验收：跨 Tab 常驻；拖动 seek 生效；速度切换生效。

## FV-3: 🌍 生境场景

- [ ] **FV-3.1** KPI 卡精修：count-up 补间 + 趋势微箭头（vs 上代）+ 语义色 + hover 口径 tooltip。
- [ ] **FV-3.2** 环境压力台：滑杆填充轨道 + 拖动数值气泡 + 剧本 chips 选中态 + 写回配置成功微反馈（复用现有 predator/abundance/drift/capacity 滑杆 id）。
- [ ] **FV-3.3** 种群面板：按 population 分组可折叠 + 血条掉血补间 + 意图 emoji 淡入 + 死亡置灰划线可逆 + hover 个体详情卡（复用 `eco2-pop-row` 数据，换结构/动效）。

## FV-4: 🏆 竞技场景（赛制自适应，重点）

- [ ] **FV-4.1** 分场：🏅家族精英榜（奖牌名次 + 基因 chips + 协作雷达缩略）+ 近交多样性告警条。
- [ ] **FV-4.2** 多队：coordination_lift 卡（正=配合增益/负=负担，色随正负）+ 首发均值/全员均值对比。
- [ ] **FV-4.3** **排兵策略热力矩阵**：策略×局分表（局分暖色映射）+ 每策略对位流缩略图（谁打谁·赢绿输红）+ 「🔀全策略对比」触发。数据接 `MATCHUP_STRATEGIES`/一版计算。
- [ ] **FV-4.4** **能力性格诊断徽章**：厚/尖/稳/专/脆/运气（plan V3-1.2b 诊断矩阵）+ 一句判读 + 改进指向。
- [ ] **FV-4.5** 混合：纪元螺旋图（棘轮上探 + 环境加压色温）+ 杂种优势对照标记（`heterosis`/`eras`）。

## FV-5: 📈 演化场景

- [ ] **FV-5.1** 统一 SVG 图元库（柱/线/面/游标/tooltip）——`js/digital-twin/eco-charts.js`，供三比与谱系共用。
- [ ] **FV-5.2** 三比曲线子 tab：环比（柱+Δ箭头+%）/ 同比（分组折线，纪元或队分色、同相位对齐）/ 综合比（主曲线+分量堆叠切换）。数据接 `generations[]`（`diversity/era/fitness_rate`）。
- [ ] **FV-5.3** 曲线游标联动回放 + 世代纪事时间轴（含猫解说）。

## FV-6: 🌳 血系场景

- [ ] **FV-6.1** 遗传学七图（接一版 `eco-genetics` 计算 + `eco-charts` 图元）：血系树（系谱系数着色）/遗传力条/联姻散点/近交-杂优曲线/均值回归轨迹（收敛动画）/奠基者溯源/学派-政治-地理热力图。
- [ ] **FV-6.2** 每图判词卡：由计算值生成的客观陈述+预测（如"回归半衰期约 N 代"），不褒不贬。

## FV-7: 动效与回放电影感

- [ ] **FV-7.1** 单时钟源（rAF）四处同步：帧→3D + KPI count + 种群行 + 当前 Tab 曲线游标。
- [ ] **FV-7.2** 世代/纪元过场：epoch 翻牌+猫播报；混合 era 螺旋上升过场（棘轮+色温）。
- [ ] **FV-7.3** 性能：600 帧回放 DOM 复用（不每帧 innerHTML）、SVG 一次绘制游标单独移动；单帧 <8ms；reduced-motion 降级。

## FV-8: 状态 / 无障碍 / 收口

- [ ] **FV-8.1** 四状态：empty（三步引导）/loading（骨架屏）/error（区分创建/演练/超时 + 重启后端指引）/partial（多队缺场标注）。
- [ ] **FV-8.2** 无障碍：WCAG AA（深/浅双主题）+ 统一 focus ring + Tab/滑杆/回放 ARIA + SVG title/desc。
- [ ] **FV-8.3** 沙箱验证：全部改动文件 `node --check` + vitest（若拆纯函数：IA 状态机/图元库）；HTML div 平衡校验。
- [ ] **FV-8.4**【CodeBuddy 本机】浏览器 `?office3d=1&ecoui=v2` 三档各跑一场视觉冒烟：四场景切换流畅、回放四处同步、策略矩阵/诊断徽章/谱系七图/三比曲线渲染正确、office-mode 浅色可读、旧房间视图与一版零回归。

---

## 执行顺序

```
FV-0(✅)→ FV-1(设计语言)→ FV-2(IA 框架)→ [FV-3 生境 ∥ FV-4 竞技 ∥ FV-5 演化 ∥ FV-6 血系]
  → FV-7(动效/回放)→ FV-8(状态/无障碍/收口)
```

## 归属

| 工作面 | 归属 |
|---|---|
| F2 plan/todos、语义色板、IA 场景化框架、四场景精修、SVG 图元库、动效同步、状态/无障碍、沙箱级校验 | 【Fable 5】 |
| 前端一版功能落地（赛制/策略/曲线/谱系/3D 数据）、本机浏览器视觉冒烟与零回归复验 | 【CodeBuddy】 |
