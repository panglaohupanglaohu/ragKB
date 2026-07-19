<!-- docs-signoff: author="Grok" kind="llm" doc="todos" ts="2026-07-15T17:40:22Z" -->
# 任务 Token 治理 — Todos（v2.4 R10 杠杆一行表 + 参数旋钮）

> 配套 [`任务Token治理plan.md`](任务Token治理plan.md)  
> 北极星：任务执行 token · **算法真省** · UI 不堆调研文案。

---

## R0–R9（已完成）

- [x] R0–R6 四车道 + prepare 接线 + workbench  
- [x] R7 catalog 可证实现卡  
- [x] R8 计量诚实化  
- [x] R9 六源算法入 prepare  

---

## R10: 杠杆菜单精简 + 可调参数（完成）

- [x] **R10.1** README 迁入 Token 治理长文（管线 / 对照表 / API / 参数 / 计量）  
- [x] **R10.2** `lever_params.py` schema + `settings.params` load/save/clamp  
- [x] **R10.3** catalog 挂 `params` 当前值；GET `/levers` 回填  
- [x] **R10.4** `prepare_request` 读 params → compress/rtk/progressive/skill/codegraph/cache  
- [x] **R10.5** POST `/levers` 收 `params`；budget 键双写 `BudgetGuard`  
- [x] **R10.6** 前端一行管线表：接线 · 启用 · 试跑 · 旋钮（去长描述）  
- [x] **R10.7** CSS 紧凑 `.tg-pipe-table` + knobs  
- [x] **R10.8** pytest：clamp、max_tool_chars 对比、system 截断、budget 写读  
- [x] **R10.9** plan/todos 签名更新  
- [x] **R10.10** 收口：试跑前自动保存旋钮；budget `submit` 开关；dirty 提示；试跑列精简回写；预算面板只读；测试隔离 settings  
- [x] **R10.11** 去掉独立「效果验证」菜单 → 试跑报告末尾告警+建议；账单与试跑合并；细节中文；成本竞标并入主轴末位  
- [x] **R10.12** 效率视角/优化建议/成本构成/消耗明细合并为「⑤ 分析台」；筛选条共用；演进棘轮副轴折叠  

**验收**

1. 杠杆区每行：ON/接线/试跑/旋钮，无大段调研文案  
2. 改 `alert_threshold` 保存 → `settings.budget` 生效  
3. 降 `max_tool_chars` 试跑：rtk 更狠  
4. `pytest tests/test_token_governance.py` 33 绿  
5. 改旋钮后不点保存直接试跑 → 仍用新参数（自动保存）  
6. 无独立预算验证面板；试跑表「说明」可读；页序 杠杆→试跑/账单→竞标  
7. 分析四块同屏：效率 · 建议 · 构成/趋势 · 明细  
- [x] **R11** 5h 连续优化 H0–H4 全完成（见 `任务Token治理-5h连续优化todos.md`）  


---

## 非目标

- 论文 / research 线  
- Plaza 讨论阶段 token 优化  
- 外挂完整 RTK/OpenWolf 二进制为硬依赖  
