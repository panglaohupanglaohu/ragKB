# AgentsGroup2026

当前仓库的可信入口。

## 快速定位

- 文档入口：[docs/README.md](docs/README.md)
- 验证基线：[docs/VALIDATION.md](docs/VALIDATION.md)
- 文档审计：[docs/DOCUMENTATION_AUDIT.md](docs/DOCUMENTATION_AUDIT.md)
- 当前重构路线：[docs/全仓库分阶段重构路线.md](docs/%E5%85%A8%E4%BB%93%E5%BA%93%E5%88%86%E9%98%B6%E6%AE%B5%E9%87%8D%E6%9E%84%E8%B7%AF%E7%BA%BF.md)

## 环境

以 Windows PowerShell 在仓库根目录执行。

```powershell
npm install
venv\Scripts\python.exe -m pip install -e ".[dev]"
```

本仓库优先使用本地 Python 虚拟环境：`.venv`，其次 `venv`。当前验证记录见 [docs/VALIDATION.md](docs/VALIDATION.md)。

## 常用命令

```powershell
npm run lint
npm run typecheck
npm run build
npm test
```

注意：截至 `2026-06-26`，`lint` 和 `typecheck` 是当前可通过基线；`build` 和测试仍有已记录的遗留失败。不要把旧 README 或历史计划中的能力描述当成已验证事实。

## 文档状态

旧的长篇 README、HTML 导出版、根目录历史计划和 TODO 已归档到 [docs/archive/root-legacy](docs/archive/root-legacy)。归档内容仅作历史参考，默认视为 `needs verification`。
