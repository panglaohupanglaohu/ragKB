<!-- docs-signoff: author="CodeBuddy (GLM-5.2)" kind="llm" doc="plan" ts="2026-06-18T00:16:00Z" -->

# docs/ 写入签名规则（可验证）

> 适用范围：`docs/` 目录下所有 **plan / todos** 文件（文件名含 `plan`、`todos`、`计划`，`.bak` 除外）。
> 约束对象：**任何**向该目录写入或修改 plan/todos 的工具 / LLM / 系统 / 人。

---

## 1. 唯一规则

向 `docs/` 写入或修改 plan/todos 文件时，文件**第一行**必须是签名注释：

```
<!-- docs-signoff: author="<谁>" kind="<llm|tool|human>" doc="<plan|todos>" ts="<ISO-8601 UTC>" -->
```

| 字段 | 要求 | 示例 |
|------|------|------|
| `author` | 非空，写入方标识 | `CodeBuddy (GLM-5.2)`、`GitHub Copilot`、`张三` |
| `kind` | `llm` / `tool` / `human` 三选一 | `llm` |
| `doc` | `plan` / `todos` 二选一 | `plan` |
| `ts` | 写入时刻，ISO-8601 UTC | `2026-06-18T00:16:00Z` |

- 每次修改都要**更新 `ts`**。
- HTML 注释，渲染不可见，机器可解析。
- 签名块之前不允许有任何其他内容（包括空行）。

## 2. 校验

```bash
node scripts/check-docs-signoff.cjs            # 报告模式：malformed 失败，缺签名 WARN
node scripts/check-docs-signoff.cjs --strict   # 严格模式：缺签名也失败（CI / pre-commit）
node scripts/check-docs-signoff.cjs --fix      # 交互式补签：为缺签名的文件追加签名块
```

退出码非 0 即不合规。校验器逻辑：
- 第一行必须匹配 `<!-- docs-signoff: ... -->` 正则
- `author` 非空、`kind` / `doc` 取值合法
- `ts` 是合法 ISO-8601 且不超过当前时间 +5 分钟（防伪造未来时间）

## 3. 与 ponytail 集成（省 token）

ponytail 是 Claude Code 的 SessionStart hook，在会话启动时注入 `SKILL.md` 规则。本规则通过以下方式与 ponytail 协同：

### 省 token 的原理

ponytail 的注入机制是：`ponytail-activate.js` 在 SessionStart 时读取 `skills/ponytail/SKILL.md`，将其内容作为 hidden context 注入。Agent 后续每轮对话都带着这段上下文，不需要重复加载。

本规则的省 token 策略：
- **不把 SIGNING_RULE.md 全文注入 ponytail**（全文 ~2KB）
- **在 ponytail SKILL.md 末尾追加一行规则**（~120 字符），agent 写 docs/ 文件时自动遵守
- **校验由独立脚本兜底**，不依赖 agent 自觉

### 具体落地

1. 在 `ponytail/skills/ponytail/SKILL.md` 的 Rules 段追加一行：

```
- 写 docs/ 下的 plan/todos 文件时，第一行必须签名：<!-- docs-signoff: author="<你>" kind="llm" doc="<plan|todos>" ts="<ISO-8601 UTC>" -->
```

2. 在 `.github/copilot-instructions.md` 追加一段（非 ponytail 的 agent 也能读到）：

```
## docs/ 签名规则
写 docs/ 下 plan/todos 文件时，第一行必须是签名注释：<!-- docs-signoff: author="<谁>" kind="<llm|tool|human>" doc="<plan|todos>" ts="<ISO-8601 UTC>" -->。详见 docs/SIGNING_RULE.md。
```

3. pre-commit hook（可选，兜底校验）：

```bash
# .git/hooks/pre-commit
node scripts/check-docs-signoff.cjs --strict || exit 1
```

### 为什么这样省 token

| 方案 | 每轮 token 开销 | 强制力 |
|------|:-:|:-:|
| 全文注入 SIGNING_RULE.md | ~2KB | 靠 agent 自觉 |
| **一行规则注入 ponytail + 校验脚本兜底** | ~120 字符 | agent 遵守 + 脚本拦截 |
| 只靠校验脚本，不注入 | 0 | 只拦截不预防 |

选第二种：注入一行（预防）+ 校验脚本（拦截），两端闭环。

## 4. 现存历史文件

本规则对**新写入/被修改**的文件强制生效。存量未签名文件：
- 默认模式（`WARN`）：只报告不阻断
- `--fix` 模式：交互式补签
- 全部回填后可在 CI 切到 `--strict`
