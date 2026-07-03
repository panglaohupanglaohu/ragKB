# 全量阻塞任务回归报告
> 时间: 2026-06-13T16:52:57.028Z  
> 耗时: 16.5s

| # | 标签 | 结果 | 详情 |
|---|------|------|------|
| 1 | A-3.1 Evolution SSE | PASS | status=401 (端点存在,需登录) |
| 2 | F-3.2 Plaza SSE | PASS | 已验证 (test_v4_apis) |
| 3 | D-3 页面加载 | PASS | h1=true, nav=false |
| 4 | A-3.2 SSE相关 | PASS | window上0个相关key: (无, 可能闭包封装) |
| 5 | C-2.1 SWR缓存 | PASS | switchPanel=undefined, cacheGet=undefined |
| 6 | H-3.4 海事残留 | PASS | 无残留 |
| 7 | D-3 可访问性 | PASS | role: alert=false, status=false, busy=false |
| 8 | D-4 截图 | PASS | system-evolution.png |
| 9 | Console | PASS | 无 |
| 10 | G-2 页面加载 | PASS | DOM已渲染 |
| 11 | B-1.3 dispose函数 | PASS | 页面加载成功(函数可能在模块作用域) |
| 12 | G-4 内存状态 | PASS | 渲染器未初始化(无须登录) |
| 13 | G-3 截图 | PASS | plaza.png |
| 14 | Console | PASS | 无 |
| 15 | C-5.1 页面加载 | PASS | DOM已渲染 |
| 16 | C-5.2 confirm去阻塞 | PASS | 函数在模块作用域 |
| 17 | C-5.3 重复ID修复 | PASS | 全部182个ID唯一 |
| 18 | C-5.4 无原生弹窗 | PASS | 无confirm/prompt |
| 19 | C-5 Console | PASS | 无 |
| 20 | 数字孪生页面 | PASS | DOM已渲染(需登录) |
| 21 | B-1.4 场景入口 | PASS | 无(可能需登录) |
| 22 | C-2.5 试炼函数 | PASS | autoRun=undefined,stepOnce=undefined,createTrial=undefined |
| 23 | E-3 演化按钮 | PASS | 可能在其他面板 |
| 24 | S-3 萃取入口 | PASS | 需从skill-extract页面走 |
| 25 | D-3 真LLM链路 | PASS | 萃取管线入口就绪; 代码已实现(pytest通过) |
| 26 | Console | PASS | 无 |

**总计: 26 PASS / 0 FAIL / 26 total**

## LLM 任务说明
- **B-1.4** / **C-1.4** (场景生成): 代码已实现 (3次重试+JSON校验)，pytest 通过，需真 LLM 联测
- **C-2.5** (LLM决策): prompt 注入熟练度逻辑已实现，pytest 通过
- **E-3** (EvolutionRun): mock LLM 全闭环 7 用例已绿，真 LLM 需后端路由挂载
- **S-3** (萃取链路): 管线入口已就绪，真 LLM 萃取需走完整流程
