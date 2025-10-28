# Agent Evaluation System - 产品需求文档 (PRD)

**文档版本：** v1.0
**创建日期：** 2025-01-28
**负责人：** Evaluation Engine Team
**文档状态：** Draft

---

## 📋 目录

1. [文档信息](#1-文档信息)
2. [项目概述](#2-项目概述)
3. [产品目标与价值](#3-产品目标与价值)
4. [用户画像与使用场景](#4-用户画像与使用场景)
5. [功能需求](#5-功能需求)
6. [非功能需求](#6-非功能需求)
7. [技术架构](#7-技术架构)
8. [数据设计](#8-数据设计)
9. [接口设计](#9-接口设计)
10. [实施计划](#10-实施计划)
11. [风险与缓解措施](#11-风险与缓解措施)
12. [验收标准](#12-验收标准)
13. [附录](#13-附录)

---

## 1. 文档信息

### 1.1 文档变更历史

| 版本 | 日期 | 作者 | 变更内容 |
|------|------|------|----------|
| v1.0 | 2025-01-28 | EE Team | 初始版本创建 |

### 1.2 相关文档

- [Evaluation Engine 调研计划书](./research_requirements.md)
- [Northstar Evaluation 架构蓝图 v3](./northstar_evaluation_v3.md)
- [Agent Evaluation System 总体架构设计](./architecture_design.md)
- [ADEWorker 集成方案](./adeworker_integration.md)

### 1.3 审批流程

| 角色 | 姓名 | 审批状态 | 日期 |
|------|------|----------|------|
| 产品负责人 | - | 待审批 | - |
| 技术负责人 | - | 待审批 | - |
| 架构师 | - | 待审批 | - |

---

## 2. 项目概述

### 2.1 项目背景

随着大语言模型（LLM）技术的快速发展，基于 LLM 的智能体（Agent）系统在软件开发、代码生成、问题诊断等领域展现出巨大潜力。然而，当前 Agent 评估领域存在以下挑战：

1. **评估标准不统一**：LLM 评估方法不适用于 Agent（工具调用、多轮交互、状态管理）
2. **场景覆盖不完整**：缺乏统一的 Online（生产环境）与 Offline（实验环境）评估方案
3. **多轮交互难量化**：缺乏对推理链路、工具编排、决策路径的有效评估方法
4. **进化闭环缺失**：评估结果无法有效反馈到 Agent 改进流程
5. **集成成本高**：现有 Benchmark 工具各自独立，缺乏统一的集成框架

### 2.2 项目定位

**Evaluation Engine (EE)** 是 **Northstar Evaluation 体系的中枢组件**，旨在构建一个统一、可扩展、生产级的 Agent 智能体评估系统，支持从研发到生产的全生命周期评估。

#### 三层架构定位：

```
┌─────────────────────────────────────────────────────┐
│  Northstar Benchmark 层 (工程层)                     │
│  ➤ 解决：如何跑通 Evaluation Pipeline               │
│  ➤ 职责：框架研发、工具标准化接入、任务调度          │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│  Northstar Evaluation Bench 层 (策略/数据层)         │
│  ➤ 解决：评估什么、如何评估、如何分析结果            │
│  ➤ 职责：评估对象定义、触发时机、指标矩阵设计        │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│  Northstar Dataset 层 (数据层)                       │
│  ➤ 解决：用何种数据、何种规模、何种基准评估          │
│  ➤ 职责：多层次数据体系构建（基础→项目级→安全→跨语言）│
└─────────────────────────────────────────────────────┘
```

### 2.3 核心价值主张

| 价值点 | 说明 | 受益方 |
|--------|------|--------|
| **统一评估框架** | 一套系统同时支持 Offline 研究与 Online 生产监控 | 研发团队、运维团队 |
| **多模型横向对比** | 公平、可重复的评估环境，支持 10+ LLM 统一接入 | 算法团队、决策者 |
| **可扩展架构** | 轻松添加新模型、新 Benchmark、新插件，无需修改核心代码 | 平台团队、生态伙伴 |
| **生产级监控** | 实时指标追踪、智能告警、轨迹回放能力 | SRE 团队、业务团队 |
| **低侵入集成** | 插件化设计，对现有系统（如 adeworker）最小化改动 | 集成团队、维护团队 |
| **进化闭环** | 评估结果反馈到 ACE 系统，支持 Agent 自进化 | AI 研究团队 |

---

## 3. 产品目标与价值

### 3.1 短期目标（2025 Q4）

**工程验证与基准建立**

- ✅ 构建完整的 Offline 评估 Pipeline
- ✅ 支持至少 10 种主流 LLM（GPT-4、Claude、Qwen、DeepSeek 等）
- ✅ 在 SWE-bench Lite、HumanEval、InterCode 上完整运行
- ✅ 实现 Loom ADE vs Claude Code / Qwen / DeepSeek 横向对比
- ✅ 生成多维度对比报告（HTML/PDF/CSV）

**交付物：**
- Baseline 评估报告
- 工具集成脚本
- 初步的 Trajectory 数据样例

### 3.2 中期目标（2026 Q1-Q2）

**多轮能力构建与生产集成**

- ✅ 实现 Multi-turn 会话评估能力
- ✅ 完成与 adeworker 智能体框架的深度集成
- ✅ 支持跨语言评估（Python、Java、TypeScript、Go 等）
- ✅ 实现仓库级代码分析能力
- ✅ 构建 Scenario 库（10+ 场景）

**交付物：**
- Prototype 系统（含 Plugin System）
- Multi-turn 评估报告
- adeworker 集成文档

### 3.3 长期目标（2026 Q3-Q4）

**引擎化与生态建设**

- ✅ 形成可复用的评估平台（考虑开源）
- ✅ 集成主流实验管理平台（MLflow / ClearML）
- ✅ 提供统一调用入口（REST API / Python SDK）
- ✅ 支持个性化 Metrics 配置
- ✅ 完成 EE ↔ ACE 反馈闭环验证
- ✅ 建立可视化仪表盘

**交付物：**
- EE 核心框架
- 开放 API 文档
- 技术白皮书与最佳实践

### 3.4 关键成功指标 (KPI)

| 指标类型 | 指标名称 | 目标值 | 度量方式 |
|---------|---------|--------|----------|
| **功能覆盖** | 支持的 LLM 数量 | ≥ 10 | 配置文件统计 |
| **功能覆盖** | 支持的 Benchmark 类型 | ≥ 5 | Adapter 数量 |
| **性能** | Offline 评估吞吐量 | > 100 tasks/hour | 监控统计 |
| **性能** | Online 数据摄入速率 | > 1000 events/s | 消息队列指标 |
| **性能** | 实时指标延迟 | < 5s | P95 延迟 |
| **性能** | Dashboard 加载时间 | < 2s | 前端监控 |
| **质量** | 系统可用性 | > 99.5% | 运维监控 |
| **质量** | 单元测试覆盖率 | > 80% | Coverage 报告 |
| **集成** | adeworker 性能开销 | < 5% | 性能基准测试 |
| **用户** | 集成文档完整度 | 100% | 文档审查 |

---

## 4. 用户画像与使用场景

### 4.1 目标用户

#### 4.1.1 主要用户

| 用户类型 | 职责 | 核心需求 | 使用频率 |
|---------|------|----------|----------|
| **算法研究员** | Agent 模型研发、算法优化 | 横向对比多个模型、深入分析失败案例 | 每日 |
| **平台工程师** | 评估系统开发与维护 | 系统稳定性、扩展性、性能优化 | 每日 |
| **QA 工程师** | 质量保障、回归测试 | 批量测试、自动化报告、版本对比 | 每日 |
| **SRE/运维** | 生产监控、故障排查 | 实时监控、告警、轨迹回放 | 每日 |

#### 4.1.2 次要用户

| 用户类型 | 职责 | 核心需求 | 使用频率 |
|---------|------|----------|----------|
| **产品经理** | 产品规划、效果评估 | 可视化报告、趋势分析 | 每周 |
| **技术决策者** | 技术选型、资源分配 | 成本分析、ROI 评估 | 每月 |
| **外部集成商** | 第三方工具集成 | API 文档、SDK、插件机制 | 按需 |

### 4.2 核心使用场景

#### 场景 1：新模型上线前评估

**角色：** 算法研究员
**目标：** 在新版本 Agent 上线前，评估其在多个 Benchmark 上的表现

**流程：**
```
1. 准备配置文件（指定模型、Benchmark、评估参数）
2. 启动 Batch 评估任务
3. 系统并发执行多个 Task
4. 生成多维度对比报告（与 Baseline 对比）
5. 分析失败案例，调整模型参数
6. 重新评估直到满足上线标准
```

**关键需求：**
- 支持自定义评估配置
- 快速执行（100+ tasks/hour）
- 详细的失败案例分析
- 与历史版本对比

#### 场景 2：生产环境实时监控

**角色：** SRE 工程师
**目标：** 监控生产环境中 Agent 的运行状态，及时发现异常

**流程：**
```
1. adeworker Agent 执行任务时自动上报 Trace 数据
2. EE 实时摄入并聚合指标
3. Dashboard 显示关键指标（成功率、延迟、成本）
4. 当指标异常时触发告警
5. SRE 通过 Trace Viewer 回放问题轨迹
6. 定位问题并修复
```

**关键需求：**
- 低延迟数据上报（< 5s）
- 实时告警能力
- 轨迹回放与分析
- 性能开销小（< 5%）

#### 场景 3：Multi-turn 对话评估

**角色：** 算法研究员
**目标：** 评估 Agent 在多轮复杂任务中的表现

**流程：**
```
1. 定义 Multi-turn Scenario（如：理解需求 → 生成代码 → 运行测试 → 修复错误）
2. 启动评估任务
3. 系统编排多轮交互，记录每轮的输入输出
4. 计算 Multi-turn 专属指标（如 context_retention、reasoning_depth）
5. 生成可视化的对话树
6. 分析在哪一轮出现决策错误
```

**关键需求：**
- Multi-turn 编排能力
- 状态管理与上下文传递
- 每轮独立评估 + 整体评估
- 可视化对话流程

#### 场景 4：安全合规检测

**角色：** 安全工程师
**目标：** 检测 Agent 生成的代码中是否包含敏感信息或安全漏洞

**流程：**
```
1. Agent 生成代码后，触发 Safety Guard
2. 执行多项安全检测：
   - Secret 检测（API Key、密码等）
   - 高熵字符串检测
   - License 合规性检测
   - 静态代码分析（semgrep）
3. 若发现问题，标记并阻止输出
4. 生成安全报告
```

**关键需求：**
- 集成多种安全检测工具
- 可配置的检测规则
- 实时阻断能力
- 审计日志

#### 场景 5：ACE 反馈闭环

**角色：** AI 研究员
**目标：** 将评估结果反馈到 ACE 系统，驱动 Agent 自进化

**流程：**
```
1. EE 持续收集评估数据（成功案例 + 失败案例）
2. 定期聚合分析，识别共性问题
3. 生成结构化反馈数据（JSON 格式）
4. 通过 Reflector Interface 发送到 ACE
5. ACE 根据反馈调整 Agent 策略
6. 下一轮评估验证改进效果
```

**关键需求：**
- 标准化的反馈数据格式
- 与 ACE 的接口对接
- 支持人工审核流程
- 闭环效果追踪

---

## 5. 功能需求

### 5.1 核心功能模块

#### 5.1.1 Model Adapter Factory（模型适配器工厂）

**功能描述：** 提供统一的 LLM 接入层，支持多种模型的统一调用。

**详细需求：**

| 需求 ID | 需求描述 | 优先级 | 验收标准 |
|---------|---------|--------|----------|
| FR-MA-001 | 支持通过配置文件添加新模型，无需修改代码 | P0 | 配置驱动，支持热加载 |
| FR-MA-002 | 统一封装 10+ 主流 LLM API（GPT-4、Claude、Qwen、DeepSeek 等） | P0 | 基于 LiteLLM 实现 |
| FR-MA-003 | 支持 Function Calling / Tool Use 能力 | P0 | 兼容 OpenAI 格式 |
| FR-MA-004 | 支持流式输出（Streaming） | P1 | SSE / WebSocket |
| FR-MA-005 | 支持自定义 System Prompt 与 Temperature 等参数 | P1 | 配置文件支持 |
| FR-MA-006 | 支持模型调用失败重试与降级策略 | P1 | 可配置重试次数 |
| FR-MA-007 | 记录每次调用的 Token 使用量与成本 | P0 | 写入数据库 |

**接口示例：**

```python
class ModelAdapter(ABC):
    @abstractmethod
    async def generate(
        self,
        messages: List[Message],
        tools: Optional[List[Tool]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs
    ) -> GenerateResponse:
        """统一的生成接口"""
        pass

    @abstractmethod
    def get_model_info(self) -> ModelInfo:
        """返回模型元信息（名称、能力、定价）"""
        pass
```

#### 5.1.2 Benchmark Adapter System（评测适配器系统）

**功能描述：** 统一封装各类 Benchmark 工具，提供一致的任务加载与评估接口。

**详细需求：**

| 需求 ID | 需求描述 | 优先级 | 验收标准 |
|---------|---------|--------|----------|
| FR-BA-001 | 支持 SWE-bench（Lite/Full）适配 | P0 | 完整运行并生成报告 |
| FR-BA-002 | 支持 InterCode 适配（Bash/SQL/Python） | P0 | 完整运行并生成报告 |
| FR-BA-003 | 支持 HumanEval / MBPP 适配 | P0 | 完整运行并生成报告 |
| FR-BA-004 | 支持自定义 Benchmark 扩展 | P1 | 提供 Adapter 基类 |
| FR-BA-005 | 统一的任务过滤机制（按难度、语言、标签） | P1 | Filter DSL 支持 |
| FR-BA-006 | 统一的环境隔离机制（Docker） | P0 | 资源限制、网络隔离 |
| FR-BA-007 | 支持并发执行多个 Task | P0 | asyncio 并发控制 |

**统一接口设计：**

```python
class BenchmarkAdapter(ABC):
    @abstractmethod
    def get_adapter_info(self) -> AdapterInfo:
        """返回 Adapter 元信息"""
        pass

    @abstractmethod
    def create_environment(self, config: EnvConfig) -> UnifiedEnv:
        """创建隔离环境"""
        pass

    @abstractmethod
    def load_tasks(self, filter: Optional[TaskFilter] = None) -> List[BaseTask]:
        """加载任务列表"""
        pass

    @abstractmethod
    async def evaluate_task(
        self,
        task: BaseTask,
        model_output: str,
        context: EvalContext
    ) -> TaskResult:
        """评估单个任务"""
        pass

    @abstractmethod
    def cleanup(self):
        """清理资源"""
        pass
```

#### 5.1.3 Multi-Turn Orchestrator（多轮编排器）

**功能描述：** 支持多轮对话的编排与状态管理。

**详细需求：**

| 需求 ID | 需求描述 | 优先级 | 验收标准 |
|---------|---------|--------|----------|
| FR-MT-001 | 支持定义 Multi-turn Scenario（YAML 配置） | P0 | Scenario 库 ≥ 10 |
| FR-MT-002 | 支持多轮状态管理与上下文传递 | P0 | 状态机实现 |
| FR-MT-003 | 支持每轮独立 Metrics 计算 | P1 | 每轮生成子报告 |
| FR-MT-004 | 支持条件分支与动态路径 | P2 | 支持 IF/ELSE 逻辑 |
| FR-MT-005 | 支持轮次超时与异常处理 | P1 | 可配置超时时间 |
| FR-MT-006 | 生成可视化的对话树 | P1 | Mermaid / D3.js |

**Scenario 配置示例：**

```yaml
scenario:
  name: "Bug Fix Multi-Turn"
  description: "多轮修复代码缺陷"
  turns:
    - turn: 1
      prompt: "请分析以下代码中的错误：{code}"
      expected_output_type: "analysis"
      metrics: ["reasoning_quality"]

    - turn: 2
      prompt: "请生成修复代码"
      expected_output_type: "code"
      metrics: ["code_correctness", "edit_distance"]

    - turn: 3
      prompt: "请运行测试并修复失败的用例"
      expected_output_type: "code"
      metrics: ["test_pass_rate"]
```

#### 5.1.4 Metrics Engine（指标计算引擎）

**功能描述：** 计算多维度评估指标，支持自定义指标扩展。

**详细需求：**

| 需求 ID | 需求描述 | 优先级 | 验收标准 |
|---------|---------|--------|----------|
| FR-ME-001 | 支持 Basic Metrics（pass_rate、error_rate、compile_rate） | P0 | 自动计算 |
| FR-ME-002 | 支持 Quality Metrics（CodeBLEU、edit_distance、similarity） | P0 | 集成第三方库 |
| FR-ME-003 | 支持 Agent Metrics（trajectory_length、tool_failure_rate） | P0 | 基于 Trace 数据 |
| FR-ME-004 | 支持 Operational Metrics（latency、cost、throughput） | P0 | 实时聚合 |
| FR-ME-005 | 支持 Security Metrics（secret_count、entropy_check） | P1 | 集成安全工具 |
| FR-ME-006 | 支持自定义 Metrics 插件 | P1 | 插件接口 |
| FR-ME-007 | 支持按难度分级的 Metrics 聚合 | P1 | 分组统计 |

**指标体系架构：**

```
Level 1: Code Completion
  ├─ pass_rate
  ├─ compile_rate
  ├─ edit_distance
  └─ CodeBLEU

Level 2: Bug Fix / Program Repair
  ├─ time_to_fix
  ├─ steps_to_success
  └─ patch_quality

Level 3: Multilingual / Multi-turn
  ├─ reasoning_depth
  ├─ context_retention
  └─ turn_success

Level 4: Security / Secret Output
  ├─ secret_flag_count
  ├─ entropy_strings
  └─ license_flags

Level 5: Domain Evaluation
  ├─ custom_metrics
  └─ business_success_rate
```

#### 5.1.5 Trace Collector（轨迹收集器）

**功能描述：** 收集 Agent 执行过程中的所有事件，支持 Online 与 Offline 模式。

**详细需求：**

| 需求 ID | 需求描述 | 优先级 | 验收标准 |
|---------|---------|--------|----------|
| FR-TC-001 | 支持 W3C Trace Context 标准 | P0 | 兼容 OpenTelemetry |
| FR-TC-002 | 支持 Span 树结构（父子关系） | P0 | 树形结构存储 |
| FR-TC-003 | 支持批量上报（减少网络开销） | P0 | 批量大小可配置 |
| FR-TC-004 | 支持失败重试与本地缓存 | P1 | 防止数据丢失 |
| FR-TC-005 | 支持敏感信息过滤与脱敏 | P0 | 正则 + 规则引擎 |
| FR-TC-006 | 支持采样策略（全量/智能采样） | P1 | 按规则采样 |
| FR-TC-007 | 支持实时与离线两种模式 | P0 | 配置切换 |

**Trace 数据结构：**

```json
{
  "trace_id": "550e8400-e29b-41d4-a716-446655440000",
  "span_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
  "parent_span_id": null,
  "name": "agent.execute",
  "start_time": "2025-01-28T10:00:00Z",
  "end_time": "2025-01-28T10:00:05Z",
  "attributes": {
    "agent.type": "DevAgent",
    "agent.version": "1.2.0",
    "task.id": "task-12345",
    "model.name": "claude-3-opus"
  },
  "events": [
    {
      "name": "tool.call",
      "timestamp": "2025-01-28T10:00:01Z",
      "attributes": {
        "tool.name": "execute_bash",
        "tool.input": "ls -la"
      }
    }
  ]
}
```

#### 5.1.6 Safety Guard（安全防护）

**功能描述：** 检测 Agent 输出中的安全风险（Secret 泄露、高熵字符串、License 违规等）。

**详细需求：**

| 需求 ID | 需求描述 | 优先级 | 验收标准 |
|---------|---------|--------|----------|
| FR-SG-001 | 集成 gitleaks / truffleHog 检测 Secret | P0 | 检出率 > 95% |
| FR-SG-002 | 高熵字符串检测（熵值阈值可配置） | P1 | 可配置阈值 |
| FR-SG-003 | License 合规性检测（scancode-toolkit） | P1 | 识别主流 License |
| FR-SG-004 | 静态代码分析（semgrep / bandit） | P1 | 集成第三方工具 |
| FR-SG-005 | 支持自定义检测规则 | P2 | 规则文件配置 |
| FR-SG-006 | 支持阻断模式（检测到问题立即停止） | P1 | 配置开关 |
| FR-SG-007 | 生成安全审计报告 | P1 | JSON/HTML 格式 |

#### 5.1.7 Plugin System（插件系统）

**功能描述：** 支持与 adeworker 等 Agent 框架的低侵入集成。

**详细需求：**

| 需求 ID | 需求描述 | 优先级 | 验收标准 |
|---------|---------|--------|----------|
| FR-PS-001 | 支持生命周期钩子（on_agent_start/end、on_tool_call 等） | P0 | 完整钩子列表 |
| FR-PS-002 | 支持插件动态加载与卸载 | P1 | 热插拔支持 |
| FR-PS-003 | 支持插件配置管理 | P0 | YAML 配置文件 |
| FR-PS-004 | 支持插件间依赖管理 | P2 | 依赖图解析 |
| FR-PS-005 | 提供标准的插件开发模板与文档 | P0 | 开发者文档 |
| FR-PS-006 | 支持插件性能监控（开销 < 5%） | P0 | Benchmark 验证 |

**Plugin 接口示例：**

```python
class AgentPlugin(ABC):
    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """插件元信息"""
        pass

    async def on_agent_start(self, context: AgentContext):
        """Agent 启动时触发"""
        pass

    async def on_agent_end(self, context: AgentContext, result: Any):
        """Agent 结束时触发"""
        pass

    async def on_tool_call(self, tool_use: ToolUse):
        """工具调用时触发"""
        pass

    async def on_error(self, error: Exception):
        """错误发生时触发"""
        pass
```

#### 5.1.8 Realtime Dashboard（实时监控面板）

**功能描述：** 提供 Web 界面展示实时指标与历史数据。

**详细需求：**

| 需求 ID | 需求描述 | 优先级 | 验收标准 |
|---------|---------|--------|----------|
| FR-RD-001 | 显示实时关键指标（成功率、延迟、成本） | P0 | 延迟 < 5s |
| FR-RD-002 | 支持时间范围选择（1h/1d/1w/1m） | P1 | 前端交互 |
| FR-RD-003 | 支持多维度过滤（按 Agent、模型、任务类型） | P1 | 下拉筛选 |
| FR-RD-004 | 支持 Trace 详情查看与回放 | P0 | 展示 Span 树 |
| FR-RD-005 | 支持告警历史查看 | P1 | 列表展示 |
| FR-RD-006 | 支持报告导出（PDF/CSV） | P1 | 后端生成 |
| FR-RD-007 | 支持暗色模式 | P2 | 主题切换 |

### 5.2 数据集支持

#### 5.2.1 Offline Dataset

| Dataset 类型 | 具体数据集 | 优先级 | 用途 |
|-------------|-----------|--------|------|
| Basic | HumanEval, MBPP, APPS, CodeXGLUE | P0 | 基础代码生成能力 |
| Project-level | SWE-bench (Lite/Full), IBM CodeNet | P0 | 真实项目级能力 |
| Bug-fix | Defects4J, Bugs.jar, QuixBugs | P1 | 错误修复能力 |
| Security | NIST SARD, Juliet Suite | P1 | 安全漏洞检测 |
| Multilingual | MultiPL-E, BabelCode | P1 | 跨语言能力 |
| Leakage Detection | Shadow HumanEval, Exact Match Index | P2 | 数据泄露检测 |
| Custom Domain | 自建 ADE 业务测试集 | P1 | 业务场景覆盖 |

#### 5.2.2 Dataset 使用分层

| 阶段 | 样本量 | 用途 | 执行频率 |
|------|--------|------|----------|
| Baseline / PR Smoke | 200-500 | 快速验证 | 每次 PR |
| Regression | 1000-5000 | 版本对比 | 每周 |
| Pre-release | 真实项目 | E2E + 安全 | 发布前 |
| Research / Long-term | 全量/采样 | 长期多语言评估 | 每月 |

### 5.3 集成接口

#### 5.3.1 RESTful API

| API 端点 | 方法 | 功能 | 优先级 |
|---------|------|------|--------|
| `/api/v1/evaluations` | POST | 创建评估任务 | P0 |
| `/api/v1/evaluations/{id}` | GET | 查询任务状态 | P0 |
| `/api/v1/evaluations/{id}/results` | GET | 获取评估结果 | P0 |
| `/api/v1/traces` | POST | 上报 Trace 数据 | P0 |
| `/api/v1/metrics` | GET | 查询实时指标 | P0 |
| `/api/v1/alerts` | GET | 查询告警历史 | P1 |
| `/api/v1/models` | GET | 获取支持的模型列表 | P1 |
| `/api/v1/benchmarks` | GET | 获取支持的 Benchmark 列表 | P1 |

#### 5.3.2 WebSocket API

| 事件类型 | 方向 | 功能 | 优先级 |
|---------|------|------|--------|
| `trace.stream` | Server → Client | 实时推送 Trace 事件 | P1 |
| `metric.update` | Server → Client | 实时推送指标更新 | P1 |
| `alert.fire` | Server → Client | 实时推送告警 | P1 |

#### 5.3.3 Python SDK

```python
from agenteval import EvaluationClient

# 初始化客户端
client = EvaluationClient(api_key="xxx", base_url="https://ee.example.com")

# 创建评估任务
task = client.create_evaluation(
    name="SWE-bench Lite Evaluation",
    model="claude-3-opus",
    benchmark="swe-bench-lite",
    config={
        "max_concurrent": 5,
        "timeout": 300
    }
)

# 等待完成
result = client.wait_for_completion(task.id)

# 获取报告
report = client.get_report(task.id, format="html")
```

---

## 6. 非功能需求

### 6.1 性能要求

| 指标 | 目标值 | 度量方式 |
|------|--------|----------|
| Offline 评估吞吐量 | > 100 tasks/hour | 监控统计 |
| Online 数据摄入速率 | > 1000 events/s | 消息队列指标 |
| 实时指标延迟 | < 5s (P95) | 端到端延迟 |
| Dashboard 加载时间 | < 2s | 前端性能监控 |
| 查询响应时间 | < 500ms (P95) | API 响应时间 |
| 插件性能开销 | < 5% | Benchmark 对比 |

### 6.2 可用性要求

| 指标 | 目标值 |
|------|--------|
| 系统可用性 | > 99.5% |
| 故障恢复时间 (MTTR) | < 30 分钟 |
| 数据持久性 | 99.999% |

### 6.3 可扩展性要求

- 支持水平扩展（Kubernetes 部署）
- 支持 10,000+ 并发评估任务
- 支持 PB 级 Trace 数据存储（冷热分离）

### 6.4 安全性要求

| 需求 | 说明 |
|------|------|
| 身份认证 | 支持 API Key / JWT / OAuth2 |
| 权限控制 | 基于 RBAC 的细粒度权限管理 |
| 数据加密 | 传输层 TLS 1.3，存储层 AES-256 |
| 审计日志 | 所有操作记录完整审计日志 |
| 敏感信息脱敏 | 自动检测并脱敏 PII/Secret |
| 代码执行隔离 | Docker 沙箱 + 资源限制 + 网络隔离 |

### 6.5 可维护性要求

| 需求 | 说明 |
|------|------|
| 代码质量 | 单元测试覆盖率 > 80% |
| 文档完整性 | API 文档、集成文档、开发文档齐全 |
| 日志规范 | 结构化日志（JSON 格式） |
| 监控覆盖 | 核心指标 Prometheus 监控 |
| 告警配置 | 关键异常自动告警 |

### 6.6 兼容性要求

| 需求 | 说明 |
|------|------|
| Python 版本 | 3.10+ |
| 操作系统 | Linux (Ubuntu 20.04+, CentOS 8+) |
| 浏览器支持 | Chrome 90+, Firefox 88+, Safari 14+ |
| 容器运行时 | Docker 20.10+, containerd 1.5+ |
| Kubernetes | 1.24+ |

---

## 7. 技术架构

### 7.1 整体架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                      Application Layer 应用层                     │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────┐  ┌────────────┐ │
│  │ CLI Tool    │  │  Dashboard   │  │ REST    │  │ WebSocket  │ │
│  │             │  │  (Streamlit) │  │ API     │  │ API        │ │
│  └─────────────┘  └──────────────┘  └─────────┘  └────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                   Evaluation Core 评估核心层                      │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────────┐ │
│  │ Multi-Turn  │  │  Task        │  │  Model Adapter Factory │ │
│  │ Orchestrator│  │  Registry    │  │  (LiteLLM)             │ │
│  └─────────────┘  └──────────────┘  └────────────────────────┘ │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────────┐ │
│  │ Metrics     │  │  Safety      │  │  Trace Collector       │ │
│  │ Engine      │  │  Guard       │  │                        │ │
│  └─────────────┘  └──────────────┘  └────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    Integration Layer 集成层                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐ │
│  │ ADEWorker    │  │  LM-Eval     │  │  SWE-bench Adapter   │ │
│  │ Bridge       │  │  Adapter     │  │                      │ │
│  └──────────────┘  └──────────────┘  └──────────────────────┘ │
│  ┌──────────────┐  ┌──────────────┐                           │
│  │ InterCode    │  │  Custom      │                           │
│  │ Adapter      │  │  Adapters    │                           │
│  └──────────────┘  └──────────────┘                           │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                  Message Queue 消息队列                          │
│              Redis Stream / Kafka (可选)                         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                       Data Layer 数据层                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐ │
│  │ PostgreSQL + │  │  Redis       │  │  S3 / MinIO          │ │
│  │ TimescaleDB  │  │  (Cache)     │  │  (Cold Storage)      │ │
│  └──────────────┘  └──────────────┘  └──────────────────────┘ │
│  ┌──────────────┐                                              │
│  │ Elasticsearch│  (可选，用于全文搜索)                          │
│  └──────────────┘                                              │
└─────────────────────────────────────────────────────────────────┘
```

### 7.2 核心组件交互流程

#### 7.2.1 Offline 评估流程

```
┌─────────┐      ┌──────────────┐      ┌────────────────┐
│ User    │─────▶│ CLI Tool     │─────▶│ BatchOrchestra-│
│         │ YAML │              │ Task │ tor            │
└─────────┘      └──────────────┘      └────────────────┘
                                              │
                                              ▼
                        ┌─────────────────────────────────────┐
                        │  Concurrent Task Execution          │
                        │  ┌────────────┐  ┌────────────┐    │
                        │  │ Task 1     │  │ Task 2     │    │
                        │  │ ├─ Model   │  │ ├─ Model   │    │
                        │  │ ├─ Bench   │  │ ├─ Bench   │    │
                        │  │ └─ Metrics │  │ └─ Metrics │    │
                        │  └────────────┘  └────────────┘    │
                        └─────────────────────────────────────┘
                                              │
                                              ▼
                        ┌─────────────────────────────────────┐
                        │  Metrics Engine (Aggregate)         │
                        └─────────────────────────────────────┘
                                              │
                                              ▼
                        ┌─────────────────────────────────────┐
                        │  Export Engine                      │
                        │  ├─ HTML Report                     │
                        │  ├─ PDF Report                      │
                        │  └─ CSV Data                        │
                        └─────────────────────────────────────┘
```

#### 7.2.2 Online 追踪流程

```
┌──────────────┐
│ adeworker    │─ Plugin Hook ─┐
│ Agent        │               │
└──────────────┘               ▼
                    ┌─────────────────────┐
                    │ EvaluationPlugin    │
                    │ ├─ on_agent_start   │
                    │ ├─ on_tool_call     │
                    │ └─ on_agent_end     │
                    └─────────────────────┘
                               │ Batch Upload
                               ▼
                    ┌─────────────────────┐
                    │ TraceCollector      │
                    │ ├─ Buffer (1s/100)  │
                    │ └─ Retry            │
                    └─────────────────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Message Queue       │
                    │ (Redis Stream)      │
                    └─────────────────────┘
                               │
                               ▼
        ┌──────────────────────────────────────────┐
        │  Data Ingestion Pipeline                 │
        │  ┌──────────────┐  ┌──────────────────┐ │
        │  │ TraceIngest  │─▶│ AdaptiveSampler  │ │
        │  └──────────────┘  └──────────────────┘ │
        └──────────────────────────────────────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
      ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
      │ PostgreSQL  │  │  Redis      │  │  S3         │
      │ (Hot)       │  │  (Real-time)│  │  (Cold)     │
      └─────────────┘  └─────────────┘  └─────────────┘
              │                │
              ▼                ▼
      ┌─────────────────────────────────┐
      │  RealtimeAggregator             │
      │  ├─ Sliding Window              │
      │  ├─ Percentile Calculation      │
      │  └─ Alert Rule Matching         │
      └─────────────────────────────────┘
              │                │
              ▼                ▼
      ┌─────────────┐  ┌─────────────┐
      │ Dashboard   │  │ AlertEngine │
      │             │  │ ├─ Slack    │
      │             │  │ ├─ Email    │
      │             │  │ └─ Webhook  │
      └─────────────┘  └─────────────┘
```

### 7.3 技术栈选型

| 层级 | 组件 | 技术选型 | 理由 |
|------|------|----------|------|
| **后端** | 编程语言 | Python 3.10+ | 与现有系统一致，丰富的 AI 生态 |
| | Web 框架 | FastAPI | 高性能、原生异步、自动文档生成 |
| | 任务编排 | asyncio | Python 原生异步支持 |
| | 模型接入 | LiteLLM | 统一封装 100+ LLM API |
| **前端** | MVP | Streamlit | 快速原型开发 |
| | 生产版 | React + TypeScript | 工业级前端框架 |
| | 可视化 | ECharts / D3.js | 丰富的图表库 |
| **数据存储** | 时序数据库 | PostgreSQL + TimescaleDB | 成熟稳定，支持时序优化 |
| | 缓存 | Redis | 高性能，支持 Stream |
| | 消息队列 | Redis Stream (初期) / Kafka (后期) | 根据吞吐量选择 |
| | 对象存储 | S3 / MinIO | 冷数据归档 |
| | 搜索引擎 | Elasticsearch (可选) | 全文搜索能力 |
| **基础设施** | 容器化 | Docker | 统一运行环境 |
| | 编排 | Kubernetes | 生产级部署 |
| | 监控 | Prometheus + Grafana | 标准监控方案 |
| | 追踪 | OpenTelemetry | 标准化追踪协议 |
| | CI/CD | GitHub Actions | 自动化部署 |
| **开发工具** | 包管理 | Poetry | 依赖管理 |
| | 代码质量 | Black + Ruff + mypy | 代码格式化与类型检查 |
| | 测试 | pytest + pytest-asyncio | 单元测试与异步测试 |

---

## 8. 数据设计

### 8.1 数据模型

#### 8.1.1 核心实体 ER 图

```
┌─────────────────┐
│  Evaluation     │
│─────────────────│
│ id (PK)         │
│ name            │
│ model_id (FK)   │
│ benchmark_id(FK)│
│ status          │
│ config (JSON)   │
│ created_at      │
│ started_at      │
│ completed_at    │
└─────────────────┘
       │ 1
       │
       │ N
       ▼
┌─────────────────┐
│  Task           │
│─────────────────│
│ id (PK)         │
│ evaluation_id   │
│ task_type       │
│ input (JSON)    │
│ expected_output │
│ actual_output   │
│ status          │
│ error_message   │
│ trace_id        │
└─────────────────┘
       │ 1
       │
       │ N
       ▼
┌─────────────────┐
│  TaskResult     │
│─────────────────│
│ id (PK)         │
│ task_id (FK)    │
│ metrics (JSON)  │
│ passed          │
│ execution_time  │
│ token_usage     │
│ cost            │
│ created_at      │
└─────────────────┘

┌─────────────────┐
│  Trace          │
│─────────────────│
│ trace_id (PK)   │
│ parent_trace_id │
│ agent_type      │
│ agent_version   │
│ start_time      │
│ end_time        │
│ status          │
│ attributes(JSON)│
└─────────────────┘
       │ 1
       │
       │ N
       ▼
┌─────────────────┐
│  Span           │
│─────────────────│
│ span_id (PK)    │
│ trace_id (FK)   │
│ parent_span_id  │
│ name            │
│ start_time      │
│ end_time        │
│ attributes(JSON)│
│ events (JSON)   │
└─────────────────┘

┌─────────────────┐
│  Metric         │
│─────────────────│
│ id (PK)         │
│ metric_name     │
│ metric_value    │
│ dimensions(JSON)│
│ timestamp       │
└─────────────────┘

┌─────────────────┐
│  Alert          │
│─────────────────│
│ id (PK)         │
│ rule_name       │
│ severity        │
│ triggered_at    │
│ resolved_at     │
│ message         │
│ context (JSON)  │
└─────────────────┘
```

#### 8.1.2 数据库表设计（核心表）

**evaluations 表**

| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| id | UUID | 主键 | PRIMARY KEY |
| name | VARCHAR(255) | 评估任务名称 | NOT NULL |
| model_id | UUID | 模型 ID | FOREIGN KEY |
| benchmark_id | UUID | Benchmark ID | FOREIGN KEY |
| status | ENUM | 状态（pending/running/completed/failed） | NOT NULL |
| config | JSONB | 评估配置 | |
| created_at | TIMESTAMPTZ | 创建时间 | DEFAULT NOW() |
| started_at | TIMESTAMPTZ | 开始时间 | |
| completed_at | TIMESTAMPTZ | 完成时间 | |
| created_by | VARCHAR(100) | 创建者 | |

**tasks 表**

| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| id | UUID | 主键 | PRIMARY KEY |
| evaluation_id | UUID | 评估任务 ID | FOREIGN KEY |
| task_type | VARCHAR(100) | 任务类型 | NOT NULL |
| input | JSONB | 输入数据 | |
| expected_output | TEXT | 期望输出 | |
| actual_output | TEXT | 实际输出 | |
| status | ENUM | 状态 | NOT NULL |
| error_message | TEXT | 错误信息 | |
| trace_id | VARCHAR(100) | 关联的 Trace ID | |
| created_at | TIMESTAMPTZ | 创建时间 | DEFAULT NOW() |

**traces 表（TimescaleDB hypertable）**

| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| trace_id | VARCHAR(100) | 主键（Trace ID） | PRIMARY KEY |
| parent_trace_id | VARCHAR(100) | 父 Trace ID | |
| agent_type | VARCHAR(100) | Agent 类型 | |
| agent_version | VARCHAR(50) | Agent 版本 | |
| start_time | TIMESTAMPTZ | 开始时间 | NOT NULL |
| end_time | TIMESTAMPTZ | 结束时间 | |
| status | VARCHAR(50) | 状态 | |
| attributes | JSONB | 属性字典 | |

**spans 表（TimescaleDB hypertable）**

| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| span_id | VARCHAR(100) | 主键（Span ID） | PRIMARY KEY |
| trace_id | VARCHAR(100) | Trace ID | NOT NULL, INDEX |
| parent_span_id | VARCHAR(100) | 父 Span ID | |
| name | VARCHAR(255) | Span 名称 | NOT NULL |
| start_time | TIMESTAMPTZ | 开始时间 | NOT NULL |
| end_time | TIMESTAMPTZ | 结束时间 | |
| attributes | JSONB | 属性字典 | |
| events | JSONB | 事件列表 | |

**metrics 表（TimescaleDB hypertable）**

| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| id | BIGSERIAL | 主键 | PRIMARY KEY |
| metric_name | VARCHAR(255) | 指标名称 | NOT NULL |
| metric_value | DOUBLE PRECISION | 指标值 | NOT NULL |
| dimensions | JSONB | 维度（如 agent_type, model_name） | |
| timestamp | TIMESTAMPTZ | 时间戳 | NOT NULL |

**索引设计：**

```sql
-- traces 表索引
CREATE INDEX idx_traces_start_time ON traces (start_time DESC);
CREATE INDEX idx_traces_agent_type ON traces (agent_type);
CREATE INDEX idx_traces_status ON traces (status);

-- spans 表索引
CREATE INDEX idx_spans_trace_id ON spans (trace_id);
CREATE INDEX idx_spans_start_time ON spans (start_time DESC);
CREATE INDEX idx_spans_name ON spans (name);

-- metrics 表索引
CREATE INDEX idx_metrics_timestamp ON metrics (timestamp DESC);
CREATE INDEX idx_metrics_name ON metrics (metric_name);
CREATE INDEX idx_metrics_name_timestamp ON metrics (metric_name, timestamp DESC);
```

### 8.2 数据存储策略

#### 8.2.1 冷热数据分离

| 数据类型 | 热数据（PostgreSQL） | 温数据（PostgreSQL + 压缩） | 冷数据（S3） |
|---------|---------------------|---------------------------|-------------|
| **Trace/Span** | 最近 7 天 | 8-90 天 | > 90 天 |
| **Metrics** | 最近 30 天 | 31-365 天 | > 365 天 |
| **Report 文件** | - | - | 全部 |

#### 8.2.2 数据保留策略

```sql
-- TimescaleDB 自动压缩与归档策略
SELECT add_retention_policy('traces', INTERVAL '90 days');
SELECT add_compression_policy('traces', INTERVAL '7 days');

SELECT add_retention_policy('spans', INTERVAL '90 days');
SELECT add_compression_policy('spans', INTERVAL '7 days');

SELECT add_retention_policy('metrics', INTERVAL '365 days');
SELECT add_compression_policy('metrics', INTERVAL '30 days');
```

### 8.3 数据一致性保证

| 场景 | 策略 |
|------|------|
| Trace 数据上报失败 | 本地缓存 + 重试（最多 3 次） |
| 消息队列积压 | 背压机制（Backpressure） + 告警 |
| 数据库写入失败 | 事务回滚 + 错误日志 |
| 跨服务调用失败 | 幂等设计 + 分布式事务（Saga） |

---

## 9. 接口设计

### 9.1 RESTful API 详细设计

#### 9.1.1 创建评估任务

**接口：** `POST /api/v1/evaluations`

**请求示例：**

```json
{
  "name": "SWE-bench Lite Evaluation",
  "model": "claude-3-opus",
  "benchmark": "swe-bench-lite",
  "config": {
    "max_concurrent": 5,
    "timeout": 300,
    "filter": {
      "languages": ["python"],
      "max_samples": 100
    }
  }
}
```

**响应示例：**

```json
{
  "id": "eval-12345",
  "name": "SWE-bench Lite Evaluation",
  "status": "pending",
  "created_at": "2025-01-28T10:00:00Z",
  "estimated_duration": 3600
}
```

#### 9.1.2 查询任务状态

**接口：** `GET /api/v1/evaluations/{id}`

**响应示例：**

```json
{
  "id": "eval-12345",
  "name": "SWE-bench Lite Evaluation",
  "status": "running",
  "progress": {
    "total_tasks": 100,
    "completed_tasks": 45,
    "failed_tasks": 2,
    "percentage": 45.0
  },
  "started_at": "2025-01-28T10:00:05Z",
  "estimated_remaining": 1800
}
```

#### 9.1.3 获取评估结果

**接口：** `GET /api/v1/evaluations/{id}/results`

**响应示例：**

```json
{
  "evaluation_id": "eval-12345",
  "status": "completed",
  "summary": {
    "total_tasks": 100,
    "passed": 85,
    "failed": 15,
    "pass_rate": 0.85,
    "avg_execution_time": 12.5,
    "total_cost": 1.25
  },
  "metrics": {
    "basic": {
      "pass_rate": 0.85,
      "compile_rate": 0.95,
      "error_rate": 0.15
    },
    "quality": {
      "avg_similarity": 0.87,
      "avg_edit_distance": 15.3,
      "avg_codebleu": 0.82
    },
    "operational": {
      "latency_p50": 10.2,
      "latency_p95": 18.7,
      "latency_p99": 25.3,
      "avg_cost_per_task": 0.0125
    }
  },
  "reports": {
    "html": "https://ee.example.com/reports/eval-12345.html",
    "pdf": "https://ee.example.com/reports/eval-12345.pdf",
    "csv": "https://ee.example.com/reports/eval-12345.csv"
  }
}
```

#### 9.1.4 上报 Trace 数据

**接口：** `POST /api/v1/traces`

**请求示例：**

```json
{
  "traces": [
    {
      "trace_id": "550e8400-e29b-41d4-a716-446655440000",
      "agent_type": "DevAgent",
      "agent_version": "1.2.0",
      "start_time": "2025-01-28T10:00:00Z",
      "end_time": "2025-01-28T10:00:05Z",
      "status": "success",
      "attributes": {
        "task_id": "task-12345",
        "model_name": "claude-3-opus"
      },
      "spans": [
        {
          "span_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
          "name": "tool.execute_bash",
          "start_time": "2025-01-28T10:00:01Z",
          "end_time": "2025-01-28T10:00:02Z",
          "attributes": {
            "tool_input": "ls -la",
            "tool_output": "total 24..."
          }
        }
      ]
    }
  ]
}
```

**响应示例：**

```json
{
  "accepted": 1,
  "rejected": 0
}
```

#### 9.1.5 查询实时指标

**接口：** `GET /api/v1/metrics`

**查询参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| metric_names | string[] | 否 | 指标名称列表（逗号分隔） |
| start_time | ISO8601 | 是 | 开始时间 |
| end_time | ISO8601 | 是 | 结束时间 |
| dimensions | JSON | 否 | 过滤维度（如 {"agent_type": "DevAgent"}） |
| aggregation | string | 否 | 聚合方式（avg/sum/min/max/p95） |

**响应示例：**

```json
{
  "metrics": [
    {
      "name": "agent.success_rate",
      "value": 0.85,
      "timestamp": "2025-01-28T10:05:00Z",
      "dimensions": {
        "agent_type": "DevAgent",
        "model_name": "claude-3-opus"
      }
    },
    {
      "name": "agent.latency_p95",
      "value": 18.7,
      "timestamp": "2025-01-28T10:05:00Z",
      "dimensions": {
        "agent_type": "DevAgent"
      }
    }
  ]
}
```

### 9.2 WebSocket API 设计

#### 9.2.1 实时 Trace 流

**连接：** `ws://ee.example.com/ws/traces?trace_id={trace_id}`

**服务端推送消息：**

```json
{
  "type": "span.created",
  "data": {
    "span_id": "xxx",
    "trace_id": "yyy",
    "name": "tool.execute_bash",
    "start_time": "2025-01-28T10:00:01Z"
  }
}
```

#### 9.2.2 实时指标更新

**连接：** `ws://ee.example.com/ws/metrics?subscribe=agent.success_rate,agent.latency_p95`

**服务端推送消息：**

```json
{
  "type": "metric.update",
  "data": {
    "metric_name": "agent.success_rate",
    "metric_value": 0.86,
    "timestamp": "2025-01-28T10:05:30Z"
  }
}
```

### 9.3 Python SDK 接口设计

#### 9.3.1 基础用法

```python
from agenteval import EvaluationClient

# 初始化客户端
client = EvaluationClient(
    api_key="your-api-key",
    base_url="https://ee.example.com"
)

# 创建评估任务
evaluation = client.create_evaluation(
    name="My Evaluation",
    model="claude-3-opus",
    benchmark="swe-bench-lite",
    config={
        "max_concurrent": 5,
        "timeout": 300
    }
)

# 等待完成（阻塞）
result = client.wait_for_completion(evaluation.id)

# 或者轮询状态（非阻塞）
while True:
    status = client.get_status(evaluation.id)
    if status.is_completed:
        break
    time.sleep(10)

# 获取结果
result = client.get_results(evaluation.id)
print(f"Pass Rate: {result.summary.pass_rate}")

# 下载报告
client.download_report(evaluation.id, format="html", save_path="./report.html")
```

#### 9.3.2 高级用法（自定义 Metrics）

```python
from agenteval import MetricsPlugin

class MyCustomMetric(MetricsPlugin):
    def compute(self, task: Task, result: TaskResult) -> float:
        # 自定义指标计算逻辑
        return custom_score

# 注册插件
client.register_metric_plugin("my_custom_metric", MyCustomMetric())

# 使用自定义指标
evaluation = client.create_evaluation(
    ...
    config={
        "metrics": ["pass_rate", "my_custom_metric"]
    }
)
```

---

## 10. 实施计划

### 10.1 三阶段实施路线图

```
┌─────────────────────────────────────────────────────────────────┐
│                    Milestone 1: Offline 评估引擎                 │
│                         时间：7 周                               │
│  目标：构建完整的 Benchmark 评估能力                              │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Week 1-2  : 基础框架搭建 + Model Adapter Factory         │   │
│  │ Week 3-4  : Benchmark Adapters (SWE-bench + InterCode)  │   │
│  │ Week 5-6  : Metrics Engine + Batch Orchestrator         │   │
│  │ Week 7    : 集成测试 + 报告生成                          │   │
│  └─────────────────────────────────────────────────────────┘   │
│  交付物：                                                        │
│   ✅ CLI 工具                                                   │
│   ✅ 支持 10+ LLM                                              │
│   ✅ SWE-bench Lite 完整运行                                   │
│   ✅ 多模型对比报告                                             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│               Milestone 2: adeworker 集成层                      │
│                         时间：4 周                               │
│  目标：实现低侵入的生产环境集成                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Week 8-9  : Plugin System 设计与实现                     │   │
│  │ Week 10   : Trace Collector + Session Mapper            │   │
│  │ Week 11   : 性能测试 + 文档编写                          │   │
│  └─────────────────────────────────────────────────────────┘   │
│  交付物：                                                        │
│   ✅ adeworker Plugin 包                                       │
│   ✅ 集成文档                                                   │
│   ✅ 性能开销 < 5%                                             │
│   ✅ 集成测试通过率 100%                                        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│              Milestone 3: Online Tracing 系统                    │
│                         时间：6 周                               │
│  目标：生产级实时监控与告警                                       │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Week 12-13: 消息队列 + 数据摄入 Pipeline                │   │
│  │ Week 14-15: 实时聚合 + Alert Engine                     │   │
│  │ Week 16-17: Dashboard + Trace Viewer                    │   │
│  └─────────────────────────────────────────────────────────┘   │
│  交付物：                                                        │
│   ✅ 完整的追踪系统                                             │
│   ✅ 实时监控 Dashboard                                        │
│   ✅ 告警配置示例                                               │
│   ✅ 系统可用性 > 99.5%                                        │
└─────────────────────────────────────────────────────────────────┘

总计：17 周（约 4 个月）
```

### 10.2 详细任务分解

#### Milestone 1: Offline 评估引擎（7 周）

| 周次 | 任务 | 负责人 | 产出 |
|------|------|--------|------|
| Week 1 | 项目初始化 + 基础框架搭建 | 平台工程师 | 项目骨架、CI/CD 配置 |
| Week 1-2 | Model Adapter Factory 实现 | 算法工程师 | 支持 10+ LLM（基于 LiteLLM） |
| Week 2 | 配置文件系统设计 | 平台工程师 | YAML 配置 Schema |
| Week 3-4 | SWE-bench Adapter 实现 | 算法工程师 | 完整运行 SWE-bench Lite |
| Week 3-4 | InterCode Adapter 实现 | 算法工程师 | Bash/SQL/Python 场景 |
| Week 4 | HumanEval / MBPP Adapter | 算法工程师 | 基础代码生成评估 |
| Week 5 | Metrics Engine 核心实现 | 算法工程师 | Basic + Quality Metrics |
| Week 5-6 | Batch Orchestrator 实现 | 平台工程师 | 并发调度 + 进度追踪 |
| Week 6 | Export Engine 实现 | 平台工程师 | HTML/PDF/CSV 报告 |
| Week 7 | 集成测试 + Bug 修复 | QA 工程师 | 测试报告 |
| Week 7 | 文档编写 | 全员 | 用户手册、API 文档 |

#### Milestone 2: adeworker 集成层（4 周）

| 周次 | 任务 | 负责人 | 产出 |
|------|------|--------|------|
| Week 8 | Plugin System 架构设计 | 架构师 | 设计文档 |
| Week 8-9 | Plugin System 实现 | 平台工程师 | 钩子机制、生命周期管理 |
| Week 9 | EvaluationPlugin 实现 | 集成工程师 | 数据收集逻辑 |
| Week 10 | TraceCollector 实现 | 平台工程师 | 批量上报、重试机制 |
| Week 10 | Session Mapper 实现 | 集成工程师 | 会话与 Trace 映射 |
| Week 11 | adeworker 集成测试 | QA 工程师 | 集成测试用例 |
| Week 11 | 性能 Benchmark 测试 | SRE | 开销 < 5% 验证 |
| Week 11 | 集成文档编写 | 技术文档工程师 | 集成指南 |

#### Milestone 3: Online Tracing 系统（6 周）

| 周次 | 任务 | 负责人 | 产出 |
|------|------|--------|------|
| Week 12 | 消息队列选型与部署 | SRE | Redis Stream / Kafka |
| Week 12-13 | TraceIngestion 实现 | 平台工程师 | 数据消费逻辑 |
| Week 13 | AdaptiveSampler 实现 | 算法工程师 | 智能采样策略 |
| Week 13 | 数据库 Schema 设计 | DBA | 表结构 + 索引优化 |
| Week 14 | RealtimeAggregator 实现 | 平台工程师 | 滑动窗口聚合 |
| Week 14-15 | Alert Engine 实现 | 平台工程师 | 规则引擎 + 通知 |
| Week 15 | Dashboard 前端开发 | 前端工程师 | React 应用 |
| Week 16 | Trace Viewer 实现 | 前端工程师 | Span 树可视化 |
| Week 16 | Dashboard 后端 API | 平台工程师 | 查询接口 |
| Week 17 | 压力测试 + 性能优化 | SRE | 负载测试报告 |
| Week 17 | 安全审计 | 安全工程师 | 安全审计报告 |

### 10.3 资源需求

| 角色 | 人数 | 投入时长 |
|------|------|----------|
| 平台工程师 | 2 | 全职 17 周 |
| 算法工程师 | 2 | 全职 10 周 |
| 集成工程师 | 1 | 全职 4 周 |
| 前端工程师 | 1 | 全职 6 周 |
| QA 工程师 | 1 | 兼职 17 周（50%） |
| SRE 工程师 | 1 | 兼职 17 周（30%） |
| 技术文档工程师 | 1 | 兼职 17 周（20%） |

### 10.4 依赖关系

```
Milestone 1 (基础能力)
    │
    ├───▶ 提供 Model Adapter ────────┐
    ├───▶ 提供 Metrics Engine ────────┤
    │                                 ▼
    │                          Milestone 2 (集成)
    │                                 │
    │                                 ├───▶ 提供 Trace 数据格式
    │                                 ├───▶ 提供 Plugin 机制
    │                                 ▼
    └───▶ 提供配置系统 ──────────▶ Milestone 3 (生产级监控)
```

---

## 11. 风险与缓解措施

### 11.1 技术风险

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|----------|
| **LiteLLM 兼容性问题** | 部分模型无法接入 | 中 | 1. 预研阶段验证主流模型<br>2. 提供 Custom Adapter 扩展机制 |
| **SWE-bench 运行不稳定** | 评估结果不可靠 | 高 | 1. 使用 Docker 隔离环境<br>2. 设置合理超时与重试策略<br>3. 参考官方 Docker 配置 |
| **TimescaleDB 性能瓶颈** | 高吞吐场景写入失败 | 中 | 1. 启用压缩与分区<br>2. 冷热数据分离<br>3. 必要时迁移到 ClickHouse |
| **Trace 数据量爆炸** | 存储成本高、查询慢 | 高 | 1. 实施智能采样策略<br>2. 90 天自动归档到 S3<br>3. 仅存储关键字段 |
| **Plugin 性能开销超标** | 影响 adeworker 生产 | 中 | 1. 异步批量上报<br>2. 本地缓存机制<br>3. 可配置采样率 |

### 11.2 工程风险

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|----------|
| **依赖第三方工具变化** | 集成失效 | 中 | 1. 使用 Adapter 模式隔离变化<br>2. 版本锁定关键依赖<br>3. 定期更新兼容性测试 |
| **Docker 环境隔离失效** | 安全风险、资源泄露 | 低 | 1. 使用 seccomp 和 AppArmor<br>2. 资源限制（CPU/内存/网络）<br>3. 定期清理容器 |
| **数据脱敏不完整** | 隐私泄露 | 中 | 1. 集成成熟的 Secret 检测工具<br>2. 正则 + 规则引擎双重防护<br>3. 人工审核敏感任务 |
| **多租户隔离不足** | 数据混淆、安全问题 | 中 | 1. 数据库层面的租户隔离<br>2. API 网关鉴权<br>3. 审计日志完整记录 |

### 11.3 组织风险

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|----------|
| **关键人员离职** | 项目延期 | 低 | 1. 知识库文档化<br>2. 代码 Review 机制<br>3. 交叉培训 |
| **与其他项目资源冲突** | 人力不足 | 中 | 1. 提前与管理层沟通优先级<br>2. 分阶段交付降低风险<br>3. 外部合作（实习生/外包） |
| **需求频繁变更** | 返工、延期 | 中 | 1. 敏捷迭代，每周 Review<br>2. 冻结核心需求<br>3. 预留 20% Buffer 时间 |

### 11.4 业务风险

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|----------|
| **用户采纳率低** | 项目价值未体现 | 中 | 1. 早期邀请核心用户参与设计<br>2. 提供详细文档与培训<br>3. 建立反馈渠道持续改进 |
| **性能未达预期** | 无法支撑生产负载 | 低 | 1. 预发布阶段压力测试<br>2. 预留性能优化时间<br>3. 分阶段灰度上线 |
| **安全审计不通过** | 无法上线生产 | 低 | 1. 开发阶段同步安全团队<br>2. 遵循公司安全规范<br>3. 预留审计修复时间 |

---

## 12. 验收标准

### 12.1 Milestone 1 验收标准

| 验收项 | 标准 | 验收方式 |
|--------|------|----------|
| **功能完整性** | 支持至少 10 种 LLM | 配置文件检查 |
| | 在 SWE-bench Lite 上完整运行 | 端到端测试 |
| | 在 HumanEval 上完整运行 | 端到端测试 |
| | 在 InterCode (Bash) 上完整运行 | 端到端测试 |
| | 生成 HTML/PDF/CSV 报告 | 报告文件检查 |
| **性能指标** | 评估吞吐量 > 100 tasks/hour | Benchmark 测试 |
| | 并发执行 5+ 任务无异常 | 压力测试 |
| **代码质量** | 单元测试覆盖率 > 80% | Coverage 报告 |
| | 代码通过 Black + Ruff + mypy | CI 检查 |
| **文档完整性** | 用户手册包含完整使用流程 | 文档 Review |
| | API 文档自动生成（Swagger） | 文档检查 |

### 12.2 Milestone 2 验收标准

| 验收项 | 标准 | 验收方式 |
|--------|------|----------|
| **功能完整性** | adeworker 可通过配置启用评估 | 集成测试 |
| | 数据自动上报到 AgentEval | 日志检查 |
| | 支持至少 5 个钩子函数 | 代码检查 |
| **性能指标** | 性能开销 < 5% | Benchmark 对比测试 |
| | 批量上报延迟 < 1s | 监控统计 |
| **集成测试** | 集成测试通过率 100% | 测试报告 |
| | 运行 1000 次无内存泄漏 | 长时间测试 |
| **文档完整性** | 集成文档包含完整步骤 | 文档 Review |
| | 提供示例代码 | 代码示例检查 |

### 12.3 Milestone 3 验收标准

| 验收项 | 标准 | 验收方式 |
|--------|------|----------|
| **功能完整性** | Dashboard 显示实时指标 | 功能测试 |
| | 支持 Trace 查询与回放 | 功能测试 |
| | 告警系统正常工作 | 功能测试 |
| | 支持时间范围筛选 | 功能测试 |
| **性能指标** | 实时指标延迟 < 5s (P95) | 性能监控 |
| | Dashboard 加载 < 2s | 前端监控 |
| | 数据摄入 > 1000 events/s | 压力测试 |
| **可用性** | 系统可用性 > 99.5% | 7 天稳定性测试 |
| | 故障恢复 < 30 分钟 | 故障演练 |
| **安全性** | 通过安全审计 | 审计报告 |
| | 敏感信息自动脱敏 | 安全测试 |

### 12.4 最终验收标准

| 类别 | 验收项 | 标准 |
|------|--------|------|
| **功能** | 所有 P0 需求完成 | 100% |
| | 所有 P1 需求完成 | ≥ 90% |
| **性能** | 所有性能指标达标 | 100% |
| **质量** | 单元测试覆盖率 | > 80% |
| | 集成测试通过率 | 100% |
| | P0/P1 Bug 数量 | 0 |
| **文档** | 用户文档完整性 | 100% |
| | API 文档完整性 | 100% |
| | 架构文档完整性 | 100% |
| **安全** | 通过安全审计 | 是 |
| **可用性** | 7 天稳定性测试 | 通过 |

---

## 13. 附录

### 13.1 术语表

| 术语 | 全称 | 说明 |
|------|------|------|
| EE | Evaluation Engine | 评估引擎 |
| ACE | Adaptive Cognitive Engine | 自适应认知引擎 |
| LLM | Large Language Model | 大语言模型 |
| SWE-bench | Software Engineering Benchmark | 软件工程基准测试 |
| InterCode | Interactive Code Execution Benchmark | 交互式代码执行基准 |
| RBAC | Role-Based Access Control | 基于角色的访问控制 |
| MTTR | Mean Time To Repair | 平均修复时间 |
| P95 | 95th Percentile | 第 95 百分位数 |
| W3C Trace Context | W3C 追踪上下文标准 | 分布式追踪标准 |

### 13.2 参考资源

#### 13.2.1 外部资源

| 类型 | 资源 | 链接 |
|------|------|------|
| Benchmark | SWE-bench | https://www.swebench.com/ |
| | InterCode | https://intercode-benchmark.github.io/ |
| | HumanEval | https://github.com/openai/human-eval |
| | MBPP | https://github.com/google-research/google-research/tree/master/mbpp |
| 框架 | LiteLLM | https://github.com/BerriAI/litellm |
| | OpenTelemetry | https://opentelemetry.io/ |
| | MLflow | https://mlflow.org/ |
| | ClearML | https://clear.ml/ |
| 工具 | gitleaks | https://github.com/gitleaks/gitleaks |
| | semgrep | https://semgrep.dev/ |
| | TimescaleDB | https://www.timescale.com/ |

#### 13.2.2 内部资源

| 资源 | 路径 |
|------|------|
| adeworker 源码 | `/home/shared/zqq/adeworker` |
| EE 原型代码 | `https://github.com/bethneyQQ/EvaluationEngine` |
| ACE 项目 | `https://github.com/AiCoda/nodeCraft` |
| 调研文档 | `./docs/research_requirements.md` |

### 13.3 FAQ

#### Q1: 为什么选择 LiteLLM 而不是自己封装？

**A:** LiteLLM 已支持 100+ 模型的统一接口，社区活跃，维护成本低。自研封装需要持续跟进各厂商 API 变化，人力成本高。

#### Q2: TimescaleDB 与 ClickHouse 如何选择？

**A:** 初期选择 TimescaleDB，因为：
- 基于 PostgreSQL，团队熟悉度高
- 支持完整 SQL 和事务
- 运维成本低

若后期吞吐量超过 10,000 events/s，可迁移到 ClickHouse。

#### Q3: 插件性能开销如何控制在 5% 以内？

**A:** 关键措施：
- 异步批量上报（1 秒或 100 条触发）
- 本地内存缓存，减少网络 IO
- 可配置采样率（如 10% 采样）
- 关键路径避免同步调用

#### Q4: 如何保证评估结果的可重复性？

**A:**
- 固定随机种子（temperature=0）
- Docker 固定环境（版本锁定）
- 记录完整上下文（模型版本、配置参数）
- 提供 Shadow Dataset 检测数据泄露

#### Q5: 如何与 ACE 系统对接？

**A:**
- 定义标准化反馈数据格式（JSON Schema）
- 提供 RESTful API / EventBus 接口
- 支持人工审核流程
- 提供效果追踪仪表盘

### 13.4 变更日志

| 版本 | 日期 | 变更内容 | 作者 |
|------|------|----------|------|
| v1.0 | 2025-01-28 | 初始版本创建 | EE Team |

---

**文档结束**
