# Agent Evaluation System - 设计文档导航

**项目名称**: Agent Evaluation System
**版本**: 1.0
**最后更新**: 2025-01-28

---

## 📚 文档目录

本目录包含了 Agent Evaluation System 的完整设计文档，涵盖架构、实施计划、扩展指南等各个方面。

### 核心设计文档

| 文档 | 说明 | 状态 |
|------|------|------|
| [**00_architecture_overview.md**](./00_architecture_overview.md) | 📐 **总体架构设计** - 系统架构总览、技术栈选型、数据流设计 | ✅ 完成 |
| [**05_extensibility_guide.md**](./05_extensibility_guide.md) | 🔌 **可扩展性指南** - 如何添加新LLM、新Benchmark、自定义插件、告警通道 | ✅ 完成 |
| [**06_implementation_timeline.md**](./06_implementation_timeline.md) | 📅 **实施计划** - 详细的时间线、任务分解、资源需求、风险管理 | ✅ 完成 |
| [**07_database_schema.md**](./07_database_schema.md) | 🗄️ **数据库设计** - PostgreSQL Schema、Redis数据结构、S3存储方案 | ✅ 完成 |

### Milestone 详细设计

| 文档 | 说明 | 状态 |
|------|------|------|
| [**Milestone1_Offline_Evaluation_Engine_Design.md**](./Milestone1_Offline_Evaluation_Engine_Design.md) | 📦 **Milestone 1：Offline 评估引擎** - Model Adapter Factory、Benchmark Adapter、Orchestrator、Metrics Engine、Export Engine | ✅ 完成 |
| [**Milestone1_Quick_Start.md**](./Milestone1_Quick_Start.md) | 🚀 **Milestone 1 快速开始指南** - Day-by-day 实施步骤、环境配置、常见问题 | ✅ 完成 |
| [**Milestone1_Implementation_Checklist.md**](./Milestone1_Implementation_Checklist.md) | ✅ **Milestone 1 实施清单** - 详细任务清单、进度追踪、验收标准 | ✅ 完成 |
| [**Milestone1_Configuration_Examples.md**](./Milestone1_Configuration_Examples.md) | ⚙️ **Milestone 1 配置示例** - 评估配置、模型配置、环境变量、CI/CD 配置 | ✅ 完成 |
| **02_milestone2_adeworker_integration.md** | Milestone 2：adeworker 集成层（插件系统、数据收集、会话映射） | 📝 待完成 |
| **03_milestone3_online_tracing.md** | Milestone 3：Online Tracing 系统（分布式追踪、实时聚合、告警、Dashboard） | 📝 待完成 |

### API与接口文档（待完成）

| 文档 | 说明 | 优先级 |
|------|------|--------|
| **04_api_specification.md** | API 规范（REST API、WebSocket、GraphQL、数据模型Schema） | P1 |

---

## 🎯 快速导航

### 我想了解...

#### **系统整体架构**
👉 阅读 [总体架构设计](./00_architecture_overview.md)
- 三个 Milestone 的关系
- 技术栈选型理由
- 数据流和组件交互
- 部署架构

#### **开始 Milestone 1 开发**（⭐ 新增）
👉 阅读 [Milestone 1 快速开始指南](./Milestone1_Quick_Start.md)
- Day 1 项目初始化步骤
- 每周开发任务分解
- 环境配置与依赖安装
- 常见问题 FAQ

👉 阅读 [Milestone 1 详细设计](./Milestone1_Offline_Evaluation_Engine_Design.md)
- 完整的架构设计与数据流
- 8个核心模块的详细设计与代码框架
- 测试策略与开发规范

👉 使用 [Milestone 1 实施清单](./Milestone1_Implementation_Checklist.md) 追踪进度

👉 参考 [Milestone 1 配置示例](./Milestone1_Configuration_Examples.md) 编写配置

#### **如何扩展系统**
👉 阅读 [可扩展性指南](./05_extensibility_guide.md)
- 添加新的 LLM（如 Gemini、Llama 3）
- 集成新的 Benchmark（如 MBPP、CodeContests）
- 开发自定义插件
- 添加新的告警通道（如企业微信、Telegram）

#### **实施计划和时间安排**
👉 阅读 [实施计划时间线](./06_implementation_timeline.md)
- 详细的任务分解（30+ 任务）
- 每周工作安排
- 里程碑验收标准
- 资源需求和风险评估

#### **数据库和存储**
👉 阅读 [数据库设计](./07_database_schema.md)
- PostgreSQL + TimescaleDB Schema
- Redis 数据结构
- S3/MinIO 对象存储
- Migration 脚本
- 查询优化示例

---

## 📊 项目概览

### 核心目标

构建一个**统一的 Agent 评估系统**，支持：
1. **Offline 模式**：基于 Benchmark 的离线评估（SWE-bench、HumanEval、InterCode 等）
2. **Online 模式**：生产环境的实时轨迹追踪与监控
3. **多模型支持**：统一接口支持 10+ LLM（GPT-4、Claude、Qwen、DeepSeek 等）
4. **深度集成**：与 adeworker 智能体框架无缝集成

### 实施周期

**总工期**: 17 周（约 4 个月）

```
Week 1-7   │████████████████████│ Milestone 1: Offline 评估引擎
Week 8-11  │████████│             Milestone 2: adeworker 集成
Week 12-17 │████████████│         Milestone 3: Online Tracing 系统
```

### 核心特性

- ✅ **统一评估框架**：一套系统同时支持研究和生产
- ✅ **多模型横向对比**：公平、可重复的评估环境
- ✅ **可扩展架构**：配置驱动，轻松添加新模型和 Benchmark
- ✅ **生产级监控**：实时指标、智能告警、轨迹回放
- ✅ **低侵入集成**：对现有系统最小化改动（<5% 性能开销）

---

## 🏗️ 架构图

### 整体分层架构

```
┌─────────────────────────────────────────┐
│  Application Layer (应用层)              │
│  • Benchmark CLI                         │
│  • Online Dashboard                      │
│  • REST API / WebSocket                  │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│  Evaluation Core (评估核心层)            │
│  • Multi-Turn Orchestrator               │
│  • Model Adapter Factory                 │
│  • Unified Task Registry                 │
│  • Metrics Engine                        │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│  Integration Layer (集成层)              │
│  • ADEWorker Bridge (Plugin System)      │
│  • LM-Eval / SWE-bench / InterCode       │
│  • Custom Adapters                       │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│  Data Layer (数据层)                     │
│  • PostgreSQL + TimescaleDB              │
│  • Redis (Cache + Queue)                 │
│  • S3/MinIO (Archive)                    │
└─────────────────────────────────────────┘
```

详细架构图请参考 [总体架构设计](./00_architecture_overview.md)。

---

## 🔧 技术栈

| 类别 | 技术 | 用途 |
|------|------|------|
| **后端语言** | Python 3.10+ | 核心开发语言 |
| **Web 框架** | FastAPI | API 服务 |
| **模型接入** | LiteLLM | 统一 LLM 接口 |
| **时序数据库** | PostgreSQL + TimescaleDB | Trace/Span/Metrics 存储 |
| **缓存** | Redis | 实时指标、会话映射 |
| **消息队列** | Redis Stream / Kafka | 事件流 |
| **对象存储** | S3 / MinIO | 归档数据 |
| **前端** | Streamlit / React | Dashboard |
| **容器化** | Docker + Kubernetes | 部署 |
| **监控** | Prometheus + Grafana | 系统监控 |

---

## 📖 阅读建议

### 对于**项目经理/产品经理**：
1. 先读 [总体架构](./00_architecture_overview.md) 了解全貌
2. 重点关注 [实施计划](./06_implementation_timeline.md) 中的时间线和资源需求
3. 查看验收标准和成功指标

### 对于**架构师/技术负责人**：
1. 从 [总体架构](./00_architecture_overview.md) 开始，理解系统分层
2. 深入阅读 [可扩展性指南](./05_extensibility_guide.md) 了解设计模式
3. 查看 [数据库设计](./07_database_schema.md) 理解数据流

### 对于**开发工程师**：
1. 根据分工查看对应的 Milestone 文档（01/02/03）
2. 参考 [可扩展性指南](./05_extensibility_guide.md) 学习如何添加新功能
3. 查看 [数据库设计](./07_database_schema.md) 了解数据模型

### 对于**运维工程师**：
1. 查看 [总体架构](./00_architecture_overview.md) 中的部署架构
2. 深入阅读 [数据库设计](./07_database_schema.md) 了解存储方案
3. 关注 [实施计划](./06_implementation_timeline.md) 中的基础设施需求

---

## 📝 文档维护

### 文档版本管理

所有文档遵循 **语义化版本号**：
- **主版本号**：架构重大变更
- **次版本号**：新增章节或重要更新
- **修订号**：文字修正、示例更新

### 贡献指南

如需更新文档：
1. 在文档末尾记录版本历史
2. 更新文档头部的日期和版本号
3. 如果是重大变更，在 README 中添加变更日志

### 文档规范

- **格式**：Markdown
- **图表**：Mermaid（代码形式，方便版本控制）
- **代码示例**：包含语言标识和注释
- **链接**：使用相对路径

---

## 🔗 外部资源

### 官方文档

- [LiteLLM Documentation](https://docs.litellm.ai/)
- [TimescaleDB Documentation](https://docs.timescale.com/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [OpenTelemetry](https://opentelemetry.io/docs/)

### 参考项目

- [LM Evaluation Harness](https://github.com/EleutherAI/lm-evaluation-harness)
- [SWE-bench](https://www.swebench.com/)
- [InterCode](https://github.com/princeton-nlp/intercode)

---

## 📞 联系方式

**项目负责人**: [待补充]
**技术咨询**: [待补充]
**文档反馈**: [待补充]

---

## 📅 更新日志

| 日期 | 版本 | 更新内容 | 作者 |
|------|------|----------|------|
| 2025-01-28 | 1.1 | 新增 Milestone 1 详细设计文档（4份）：详细设计、快速开始、实施清单、配置示例 | Claude Code |
| 2025-01-28 | 1.0 | 初始版本，创建核心设计文档 | Claude Code |

---

**祝您阅读愉快！如有问题，欢迎提 Issue 讨论。**
