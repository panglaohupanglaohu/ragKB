const { existsSync } = require("node:fs");
const { join } = require("node:path");
const { spawnSync } = require("node:child_process");

const root = join(__dirname, "..");
const candidates = process.platform === "win32"
  ? [
      join(root, ".venv", "Scripts", "python.exe"),
      join(root, "venv", "Scripts", "python.exe"),
      "python",
      "py",
    ]
  : [
      join(root, ".venv", "bin", "python"),
      join(root, "venv", "bin", "python"),
      "python3",
      "python",
    ];

const python = candidates.find((candidate) => candidate.includes(":") || candidate.startsWith("/") ? existsSync(candidate) : true);
const result = spawnSync(python, process.argv.slice(2), { stdio: "inherit" });

if (result.error) {
  console.error(result.error.message);
  process.exit(1);
}

process.exit(result.status ?? 1);
