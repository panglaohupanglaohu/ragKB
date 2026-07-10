#!/usr/bin/env bash
# setup_keys.sh — mac/linux 交互式设置 API key 环境变量，写入项目根目录 .env
# 用法: bash scripts/setup_keys.sh
# 之后在 /agent-team-config.html 编辑模型时，API Key 字段填 env:VAR_NAME（如 env:DEEPSEEK_API_KEY）

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
ENV_FILE="$ROOT_DIR/.env"

echo "=== AgentsGroup2026 API Key 环境变量设置（mac/linux）==="
echo "目标文件: $ENV_FILE"
echo "已存在的变量会被更新，新变量会追加。"
echo ""

# 常见 provider → 环境变量名映射
declare -a KNOWN_KEYS=(
  "DEEPSEEK_API_KEY:DeepSeek"
  "OPENAI_API_KEY:OpenAI"
  "ANTHROPIC_API_KEY:Anthropic"
  "OPENROUTER_API_KEY:OpenRouter"
  "GITHUB_MODELS_API_KEY:GitHub Models"
  "QWEN_API_KEY:Qwen (通义千问)"
)

# 读取用户输入设置某个 key
set_key() {
  local var_name="$1"
  local label="$2"
  local current=""
  if [ -f "$ENV_FILE" ]; then
    current=$(grep -E "^${var_name}=" "$ENV_FILE" 2>/dev/null | head -1 | cut -d'=' -f2- | sed 's/^"//;s/"$//' || true)
  fi
  if [ -n "$current" ]; then
    echo "  当前 ${var_name}: ${current:0:4}****（已设置）"
  else
    echo "  当前 ${var_name}: （未设置）"
  fi
  read -rp "  输入 ${label} API Key（回车跳过，保持不变）: " value
  if [ -n "$value" ]; then
    write_kv "$var_name" "$value"
    echo "  ✓ ${var_name} 已保存"
  fi
}

# 写入或更新 KEY=VALUE 到 .env（去重）
write_kv() {
  local k="$1" v="$2"
  touch "$ENV_FILE"
  # 删除旧的同名行
  if grep -qE "^${k}=" "$ENV_FILE"; then
    # mac/linux 兼容 sed -i
    if [[ "$(uname)" == "Darwin" ]]; then
      sed -i '' "/^${k}=/d" "$ENV_FILE"
    else
      sed -i "/^${k}=/d" "$ENV_FILE"
    fi
  fi
  echo "${k}=\"${v}\"" >> "$ENV_FILE"
}

# 主菜单
while true; do
  echo ""
  echo "--- 已知 provider ---"
  for i in "${!KNOWN_KEYS[@]}"; do
    idx=$((i+1))
    IFS=':' read -r var label <<< "${KNOWN_KEYS[$i]}"
    status="未设置"
    if [ -f "$ENV_FILE" ] && grep -qE "^${var}=" "$ENV_FILE"; then
      status="已设置"
    fi
    echo "  $idx) $label ($var) [$status]"
  done
  echo "  c) 自定义变量名"
  echo "  l) 查看当前 .env"
  echo "  q) 完成"
  read -rp "选择: " choice
  case "$choice" in
    1|2|3|4|5|6)
      IFS=':' read -r var label <<< "${KNOWN_KEYS[$((choice-1))]}"
      set_key "$var" "$label"
      ;;
    c)
      read -rp "  变量名（如 MY_CUSTOM_KEY）: " cvar
      read -rp "  输入值: " cval
      if [ -n "$cvar" ] && [ -n "$cval" ]; then
        write_kv "$cvar" "$cval"
        echo "  ✓ $cvar 已保存"
      fi
      ;;
    l)
      echo "--- $ENV_FILE ---"
      if [ -f "$ENV_FILE" ]; then
        # 脱敏显示
        sed -E 's/(=.{0,4}).*/\1****/' "$ENV_FILE"
      else
        echo "  （文件不存在）"
      fi
      ;;
    q)
      echo ""
      echo "=== 完成 ==="
      echo ".env 已保存到: $ENV_FILE（已被 .gitignore 忽略）"
      echo ""
      echo "下一步：在 /agent-team-config.html 编辑模型时，API Key 字段填："
      echo "  env:VAR_NAME"
      echo "例如：env:DEEPSEEK_API_KEY"
      echo ""
      echo "重启后端后生效（后端启动时自动加载 .env）。"
      break
      ;;
    *)
      echo "无效选择"
      ;;
  esac
done
