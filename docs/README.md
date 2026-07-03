# Documentation

这是仓库文档入口。默认以本页和 [VALIDATION.md](VALIDATION.md) 为准。

## 当前可信文档

| 文档 | 用途 | 状态 |
| --- | --- | --- |
| [VALIDATION.md](VALIDATION.md) | 安装、构建、lint、typecheck、测试命令与当前结果 | 当前基线 |
| [DOCUMENTATION_AUDIT.md](DOCUMENTATION_AUDIT.md) | 文档重复、过期、冲突和归档记录 | 当前审计 |
| [全仓库分阶段重构路线.md](全仓库分阶段重构路线.md) | 分阶段重构路线 | 当前路线，执行前仍需按 [VALIDATION.md](VALIDATION.md) 复核 |
| [SIGNING_RULE.md](SIGNING_RULE.md) | docs 下 plan/todos 签名规则 | 规则文档 |

## 需要验证的历史文档

`docs/` 下大量 `plan`、`todos`、优化方案和演示指南来自不同阶段，可能描述已变更或未完成的能力。除非某个文档被当前任务明确指定，否则先按 `needs verification` 处理。

重点需要验证的类别：

- Agent 数字孪生、SECS、v4 场景演练相关计划。
- plaza、skill-extract、system-evolution、frontend big change 相关计划。
- AWS 运维 E2E、成本优化、nightly 自动演进相关说明。
- 归档在 [archive/root-legacy](archive/root-legacy) 的根目录旧文档。

## 推荐工作流

1. 先读 [VALIDATION.md](VALIDATION.md)，确认当前可运行命令和遗留失败。
2. 再读 [全仓库分阶段重构路线.md](全仓库分阶段重构路线.md)，确认当前阶段目标。
3. 如需引用历史计划，先在 [DOCUMENTATION_AUDIT.md](DOCUMENTATION_AUDIT.md) 检查状态。
4. 修改 `docs/` 下 plan/todos 文件时，遵守 [SIGNING_RULE.md](SIGNING_RULE.md)。

## 文档维护规则

- 新文档必须说明状态：`current`、`needs verification`、`archived` 或 `deprecated`。
- 不确定的行为不要写成已支持；引用验证命令时链接到 [VALIDATION.md](VALIDATION.md)。
- 过期文档优先归档，不直接删除。
