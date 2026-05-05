# AgentsGroup2026

> Standalone Agent Management, Evolution & Chat Platform
> Extracted from PoseidonX — 可独立部署，与任何系统集成

## 功能

- **智能体团队管理** — 创建/配置/管理 AI Agent 团队，支持工具、技能、权限绑定
- **系统自我演进** — 审查→发现→派发→构建→验证→关闭 闭环演进
- **Chat 对话改善** — 通过对话驱动系统改进，自动生成演进任务
- **OpenClaw 集成** — 连接外部 OpenClaw Agent，统一管理

## 快速开始

### 1. 安装依赖

```bash
# Python 后端
python -m venv venv
source venv/bin/activate  # macOS/Linux
pip install fastapi uvicorn[standard] pydantic httpx

# 前端
npm install
```

### 2. 启动服务

```bash
# 启动后端 (端口 8080)
cd src/backend && python main.py --port 8080

# 启动前端 (端口 5173，自动代理 API)
npm run dev
```

然后访问 http://localhost:5173

### 3. 与你的系统集成

#### 方式一：通过 Chat 改善系统

```python
import httpx

# 发送改善请求
resp = httpx.post("http://localhost:8080/api/v1/bridge-chat/send", json={
    "message": "优化系统的数据库查询性能",
    "session_id": "my-session",
    "agent_id": "build_pm"
})
print(resp.json()["reply"])
```

#### 方式二：通过 Evolution API 自动审查

```python
# 触发系统审查
resp = httpx.post("http://localhost:8080/api/v1/agent-teams/evolution/audit")
print(resp.json())  # {"passed": 10, "failed": 2, ...}

# 获取合规评级
resp = httpx.get("http://localhost:8080/api/v1/agent-teams/evolution/compliance-rating")
print(resp.json())  # {"grade": "B", "score": 75, ...}
```

#### 方式三：通过 OpenClaw 对接

```python
# 注册你的系统
resp = httpx.post("http://localhost:8080/api/v1/openclaw/connect", json={
    "system_name": "MyApp",
    "system_url": "http://localhost:3000",
    "api_token": "your-token",
    "capabilities": ["web_app", "database"]
})
```

## API 概览

| 路径 | 用途 |
|------|------|
| `GET /api/v1/health` | 健康检查 |
| `GET /api/v1/info` | 系统信息 |
| `POST /api/v1/bridge-chat/send` | 发送 Chat 消息 |
| `GET /api/v1/agent-config/teams` | 获取团队列表 |
| `POST /api/v1/agent-config/teams/{id}/agents` | 创建 Agent |
| `GET /api/v1/agent-teams/evolution/status` | 演进引擎状态 |
| `POST /api/v1/agent-teams/evolution/audit` | 运行审查 |
| `POST /api/v1/agent-teams/evolution/cycle` | 运行演进周期 |
| `GET /api/v1/agent-teams/evolution/compliance-rating` | 合规评级 |
| `POST /api/v1/openclaw/connect` | OpenClaw 对接 |

## 项目结构

```
AgentsGroup2026/
├── src/
│   ├── backend/
│   │   ├── main.py                  # FastAPI 入口
│   │   ├── agent_team_api.py        # 团队 + 演进 API
│   │   ├── agents/                  # Agent 管理模块
│   │   │   ├── api.py               # Agent Config REST API
│   │   │   ├── models.py            # 数据模型
│   │   │   ├── team_manager.py      # 团队管理器
│   │   │   ├── chat_harness.py      # LLM 对话引擎
│   │   │   ├── task_engine.py       # 任务引擎
│   │   │   └── ...
│   │   └── channels/                # Channel 模块
│   │       ├── marine_base.py       # Channel 基类
│   │       ├── system_evolution.py  # 系统演进引擎
│   │       └── bridge_chat.py       # Chat Channel
│   └── frontend/
│       ├── agent-team-config.html   # 主页面
│       ├── js/agent-team-config.js  # 页面逻辑
│       ├── css/                     # 样式
│       └── ...
├── config/settings.json             # 配置文件
├── package.json
├── pyproject.toml
└── vite.config.mjs
```

## 设计理念

AgentsGroup2026 提供的核心价值是 **Chat-Driven Evolution**:

1. 用户通过 Chat 描述需要改善的地方
2. Agent 分析并生成具体演进任务
3. Build 团队执行修改
4. 验证模块自动验证
5. 系统持续进化

这套闭环可以嵌入到任何系统中，让系统具备自我进化能力。
