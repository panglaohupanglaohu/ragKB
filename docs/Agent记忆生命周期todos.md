<!-- docs-signoff: author="grok-4.5" kind="llm" doc="todos" ts="2026-07-24T06:00:00Z" -->
# Agent 记忆生命周期 TODOs

状态：`[ ]` 未开始 / `[~]` 进行中 / `[x]` 完成

## P0 地基

- [x] **L-0.1** 生命周期状态机 + audit.jsonl + tombstone  
- [x] **L-0.2** destroy / seal / unseal / save 动作  
- [x] **L-0.3** Persona xiaoman|shenmian|hybrid + autonomy 默认表  
- [x] **L-0.4** API hub `/api/v1/agent-memory` + 兼容 memory-core  
- [x] **L-0.5** 站级菜单 Agent记忆 + `agent-memory.html`  
- [x] **L-0.6** pytest lifecycle + core  

## P1 共享与传递

- [x] **L-1.1** share_grants ACL + layer_mask（默认无 affect；沈弥安强制剥离）  
- [x] **L-1.2** 共享矩阵 UI（授权/撤销）  
- [x] **L-1.3** transfer 执行 will + 意图交接 auto/ask/drop + 凭吊  
- [x] **L-1.4** 传递台 UI + 历史记录  
- [x] **L-1.5** pytest share+transfer  

## P2 自主运行时

- [x] **L-2.1** chat 注入 tone_hint + recall（`chat_harness`，plaza phase 跳过）  
- [x] **L-2.2** 任务完成/失败 EventBus → 自动 log + feel  
- [x] **L-2.3** tool_loop 感知写入 + 达阈值 auto compress  
- [x] **L-2.4** runtime API `/runtime/recall` `/runtime/record`  
- [x] **L-2.5** AAS 经验桥接可选（`AG_MEMORY_AAS_BRIDGE=1` 或 metadata.bridge_to_memory）  

## P3 文档与打磨

- [x] **L-3.1** docs plan/todos 签名  
- [x] **L-3.2** README 记忆章节  
- [x] **L-3.3** agent-detail：状态/Persona/中枢深链/lifecycle 动作  
- [x] **L-3.4** 全套 pytest 绿  
- [x] **L-3.5** 首次使用 auto-bind；对话写记忆；沈弥安反思固化  
- [x] **L-3.6** 中枢 URL 深链 team/agent/seg；配置页→中枢带参  
- [x] **L-3.7** vitest agent-memory-page  
- [x] **L-3.8** 共享预览 + co_writer 协作写；总览健康分  
- [x] **L-3.9** 对话后沈弥安节流反思  
