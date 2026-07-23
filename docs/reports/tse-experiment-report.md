# TSE 神经网络萃取 实验报告

## 执行时间
2026-07-23

## 系统状态

| 组件 | 状态 | 详情 |
|------|------|------|
| Plaza (AWS运维议事厅) | :green_circle: 有2条历史讨论 | ES缩放 + CentOS迁移 |
| Plaza (ORID模型) | :red_circle: LLM不可用→模拟模式 | 无API key，讨论产出为确定性模板 |
| TSE萃取管线 | :green_circle: 已部署+已训练checkpoint | epoch 5, train_loss=1.19, val_cat_acc=1.0 |
| 技能库 | :yellow_circle: 43条技能/全部draft | usage=0, effectiveness=0 |
| 萃取Pipeline | :yellow_circle: 124条/5条published | 多处于draft待审核 |
| 技能分类 | :yellow_circle: AWS队3条技能在reserve池 | 待验证与周期重算 |
| 技能演化 | :yellow_circle: 1次completed run | Build System队，baseline→best无改善 |
| 技能路由 | :red_circle: 0次路由/0次分配/0次反馈 | 技能未被任务使用 |

---

## 实验1: TSE萃取管线性能

### 配置
```
embed_dim=256, tcn_hidden=256, dilations=[1,2,4]
hash_seed=20260716, max_utterances=64
Checkpoint: demo/e5 (train_loss=1.186, val_cat_acc=1.0, val_tools_f1=0.08)
```

### 讨论1: AWS ES 实例缩放 (9 utterances)

| 指标 | 数值 |
|------|------|
| 总延迟 | 11.8ms |
| Stage1 编码 | 3.7ms |
| Stage2 TCN | 7.1ms |
| Stage3 注意力 | 0.4ms |
| Focus indices | [0,1,2,3,5,6,7,8] |
| 萃取技能数 | 2 |

**技能1**: `AWS ES 实例缩放`
- category: domain_knowledge
- 关联utterances: #1(架构师-纵向vs横向路径), #2(运维-IO风险), #4(成本-RI折扣)
- tools: python_boto3, cloudwatch_api, kubectl, terraform 等

**技能2**: `AWS ES 实例缩放 · 约束与避坑`
- category: domain_knowledge
- 来源: CHALLENGE信号(#7 运维操作员)的三条风险
- tools: 同上

### 讨论2: CentOS→Rocky迁移 (9 utterances)

| 指标 | 数值 |
|------|------|
| 总延迟 | 8.9ms |
| Stage1 编码 | 3.5ms |
| Stage2 TCN | 5.1ms |
| Stage3 注意力 | 0.2ms |
| Focus indices | [0,1,3,4,5,6,7,8] |
| 萃取技能数 | 2 |

**技能1**: `CentOS→Rocky迁移`
- category: domain_knowledge
- instructions: 分批迁移策略(10→30→80)、三种监控模式

**技能2**: `CentOS→Rocky迁移 · 约束与避坑`
- category: domain_knowledge
- 来源: CHALLENGE信号, OpenSSL 3.0兼容性 + NetworkManager迁移

---

## 实验2: 注意力权重分析

### 当前状态: 均匀分布
所有12个utterance的5个field注意力权重均为0.08 (=1/12)，说明模型在5个epoch后尚未学会区分"技能相关"与"技能无关"utterance。

```
                u0   u1   u2   u3   u4   u5   u6   u7   u8   u9   u10  u11
name           0.08 0.08 0.08 0.08 0.08 0.08 0.08 0.08 0.08 0.08 0.08 0.08
description    0.08 ...
category       0.08 ...
tools          0.08 ...
instructions   0.08 ...
```

### 原因分析
- 训练数据量不足: checkpoint仅来自5个epoch, 银标数据量约几十条讨论
- Field关键词种子(冷启动prior)强度不够 (0.3权重混合)
- val_tools_f1=0.08 证实tools预测未学会 —— 多标签分类(50个tools)需要更多数据

### 预期改善方向
- 增加训练数据至200+条 (transcript, skills) 对
- 增加epoch至20-30
- 调整冷启动prior权重(0.3→0.5或更高)

---

## 实验3: 技能分类系统

AWS运维团队(a7c36670)的技能三池分布:

| 池 | 技能数 | 典型技能 |
|----|--------|---------|
| exclusive (特有) | 0 | — |
| general (通用) | 0 | — |
| reserve (储备) | 3 | ES伸缩运维技能, ElasticSearch实例缩放, OS迁移动态预案钩子 |

原因: effectiveness=0, total_uses=0, meets_rubric=false — 技能从未被任务执行过，无法通过分类门槛。

---

## 实验4: 完整闭环可用节点

| 环节 | 状态 | 待解决 |
|------|------|--------|
| Plaza讨论 (ORID) | :red_circle: 需要LLM key | 配置OPENROUTER_API_KEY或启动Ollama |
| 技能萃取 (TSE) | :green_circle: encoder可用 | Stage 4 decoder需LLM; 离线模式已生成真实技能 |
| 技能索引 | :green_circle: 43条技能可检索 | attention需更多训练 |
| 技能赋予 | :green_circle: API可用 | 无skill→agent绑定记录 |
| 任务执行 | :red_circle: 0次执行 | 需要TSK任务创建和调度 |
| 技能演化 | :yellow_circle: 1次completed | 需要任务执行产生usage数据 |
| 技能验证 | :yellow_circle: API可用 | 需要verification queue运行 |

---

## 结论

1. **TSE萃取管线已部署并可用** — pure-numpy encoder在无LLM环境下11ms完成一次讨论的技能萃取, 离线synthesizer能产出4条有意义的技能

2. **闭环的核心断点** — Plaza讨论需要LLM才能运行ORID模式, 当前退化为模拟模式; 任务执行和演化因为没有任务数据而无法闭环

3. **需要LLM API key** — 配置OPENROUTER_API_KEY后可以:
   - Plaza运行真实ORID讨论
   - TSE Stage 4调用ChatHarness decoder
   - 任务执行调用LLM完成任务
   - 演化引擎收集usage数据驱动improvement

4. **神经网络的短板** — 当前checkpoint(5 epochs)的注意力仍是均匀分布, 需要更多训练数据(目标200+条silver data)才能让Skill Query Cross-Attention学会聚焦技能相关utterance
