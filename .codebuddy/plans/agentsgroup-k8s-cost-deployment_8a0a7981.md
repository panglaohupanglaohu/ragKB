---
name: agentsgroup-k8s-cost-deployment
overview: 搭建 kind 3节点 K8s 集群，部署 OpenCost + Prometheus，将 AgentsGroup 后端容器化部署到 K8s，打通真实成本数据采集链路，让 cost-dashboard 展示真实 Pod 成本。
todos:
  - id: explore-codebase
    content: 使用 [subagent:code-explorer] 复核 cost_aggregator.py 单例、main.py 启动逻辑、config/ 目录文件，确保工作项精确对齐
    status: completed
  - id: write-todo-md
    content: 编写 AgentCostContainerTodo.md，包含完整工作项：代码改动（AG_OPENCOST_URL）、Dockerfile/.dockerignore、kind 集群搭建、K8s 资源清单、OpenCost+Prometheus 部署、构建部署、数据链路验证
    status: completed
    dependencies:
      - explore-codebase
---

## 用户需求

将 AgentsGroup 后端容器化部署到 kind 搭建的 3 节点 K8s 集群中，部署 OpenCost + Prometheus 采集 Pod 成本数据，打通 OpenCost → CostAggregator → cost-dashboard 的真实数据链路，替代当前的 mock 兜底数据。

## 核心交付物

- **AgentCostContainerTodo.md**：无时间戳的工作项规划文档，涵盖从代码准备到数据链路验证的完整步骤
- **代码改动**：CostAggregator 支持 `AG_OPENCOST_URL` 环境变量
- **新建文件**：应用 Dockerfile、.dockerignore、kind 集群配置、K8s 部署清单（Namespace / Deployment / Service / ConfigMap / Secret）

## 技术方案

### 整体架构

```
┌──────────────────────────────────────────────────────────┐
│  kind 3-Node Cluster (macOS Docker Desktop)              │
│                                                          │
│  ┌─────────────────────┐  ┌────────────────────────────┐ │
│  │ OpenCost + Prometheus│  │ agentsgroup Namespace      │ │
│  │ (opencost namespace) │  │                            │ │
│  │                      │  │  ┌──────────────────────┐  │ │
│  │  采集 Pod CPU/RAM/   │  │  │ Deployment           │  │ │
│  │  GPU/Network/Storage │  │  │  labels:             │  │ │
│  │  → 计算成本          │  │  │   app=agentsgroup    │  │ │
│  │                      │  │  │   service=backend     │  │ │
│  └──────────┬───────────┘  │  │   environment=prod    │  │ │
│             │              │  │   team=platform       │  │ │
│  GET :9003  │              │  │   component=backend   │  │ │
│  /model/    │              │  └──────────────────────┘  │ │
│  allocation │              │                            │ │
│             ▼              │  8080: Service → Pod       │ │
│  ┌──────────────────────┐  │                            │ │
│  │ CostAggregator       │  │  ConfigMap:               │ │
│  │  AG_OPENCOST_URL=    │  │   model_pool.json         │ │
│  │  http://opencost.    │  │   settings.json           │ │
│  │  opencost:9003       │  │                            │ │
│  │                      │  │  Secret:                   │ │
│  │  每300秒轮询拉取     │  │   users.json              │ │
│  │  缓存600秒           │  │   API keys                │ │
│  └──────────┬───────────┘  │   admin password          │ │
│             │              └────────────────────────────┘ │
│             ▼                                            │
│  ┌──────────────────────┐                                │
│  │ cost-dashboard.html  │  FastAPI 同一进程服务静态文件  │
│  │ /api/v1/cost/*       │                                │
│  └──────────────────────┘                                │
└──────────────────────────────────────────────────────────┘
```

### 关键技术决策

1. **单容器 Python 镜像**：前端是纯静态文件，FastAPI 通过 `StaticFiles` 挂载 `/js`、`/css`，通过 `FileResponse` 路由 `.html` 页面。不需要 Nginx 或多阶段构建，一个 Python 容器即可服务前后端。

2. **`AG_OPENCOST_URL` 环境变量**：在 `get_cost_aggregator()` 单例中读取 `os.getenv("AG_OPENCOST_URL")`，传入 `CostAggregator(opencost_url=...)`。集群内 OpenCost Service 地址为 `http://opencost.opencost:9003`。

3. **kind 集群配置**：1 control-plane + 2 worker 节点，使用 Docker Desktop 的 daemon。镜像通过 `kind load docker-image` 直接加载到集群节点，无需推送到外部的 registry。

4. **OpenCost 部署**：Helm chart `opencost/opencost`，自带 Prometheus 依赖。OpenCost 通过 Prometheus 的 kube-state-metrics 和 node-exporter 采集 Pod 资源用量，按云厂商定价模型计算成本。

5. **Pod 标签策略**：Deployment 的 `spec.template.metadata.labels` 设置 `app`、`service`、`environment`、`team`、`component`，OpenCost 按这些标签维度聚合成本。同时设置 `cost.opencost.io/*` 前缀标签以兼容 OpenCost 的分配模型。

## Agent Extensions

### SubAgent

- **code-explorer**
- 用途：在生成 AgentCostContainerTodo.md 前，快速复核 `cost_aggregator.py` 的 `__init__` 签名、`get_cost_aggregator()` 单例实现、`main.py` 的启动流程、`config/` 目录文件列表，确保规划的工作项与实际代码精确对齐
- 预期结果：确认文件位置和代码结构后，输出的工作项引用精确的文件路径和行号