# Milestone 1 实施清单

**版本：** v1.0
**开始日期：** ______
**预计完成日期：** ______ （7周后）

---

## 使用说明

- ✅ 表示已完成
- 🚧 表示进行中
- ⏸️ 表示已暂停
- ❌ 表示已阻塞

**更新规则：** 每日站会后更新进度

---

## Week 1: 基础框架搭建 + Model Adapter Factory

### Day 1-2: 项目初始化

- [ ] **环境配置**
  - [ ] 创建项目目录结构
  - [ ] 配置 `pyproject.toml`
  - [ ] 安装 Poetry 和依赖
  - [ ] 配置 `.env` 文件
  - [ ] 配置 `.gitignore`

- [ ] **CI/CD 配置**
  - [ ] 配置 GitHub Actions（`.github/workflows/ci.yml`）
  - [ ] 配置 Black 代码格式化
  - [ ] 配置 Ruff Linter
  - [ ] 配置 mypy 类型检查
  - [ ] 配置 pytest 测试框架

- [ ] **验收**
  - [ ] `poetry install` 成功
  - [ ] CI 流程在 GitHub 上运行成功
  - [ ] 代码提交触发自动检查

**负责人：** ______
**实际完成日期：** ______

---

### Day 3-4: Model Adapter Factory 核心实现

#### 基类设计（`agenteval/models/base.py`）

- [ ] **数据结构**
  - [ ] `ModelCapability` 枚举
  - [ ] `ModelInfo` 数据类
  - [ ] `Message` 数据类
  - [ ] `Tool` 数据类（Function Calling）
  - [ ] `GenerateResponse` 数据类

- [ ] **接口定义**
  - [ ] `ModelAdapter` 抽象基类
  - [ ] `generate()` 抽象方法
  - [ ] `get_model_info()` 抽象方法
  - [ ] `calculate_cost()` 方法

- [ ] **异常定义**
  - [ ] `ModelGenerationError`

**负责人：** ______
**实际完成日期：** ______

#### LiteLLM Adapter（`agenteval/models/litellm_adapter.py`）

- [ ] **核心实现**
  - [ ] `LiteLLMAdapter` 类
  - [ ] `generate()` 方法实现
  - [ ] 消息格式转换
  - [ ] Tool Calling 支持
  - [ ] Token 使用量提取
  - [ ] 成本计算

- [ ] **错误处理**
  - [ ] 异常捕获与转换
  - [ ] 超时处理
  - [ ] 重试机制（可选）

**负责人：** ______
**实际完成日期：** ______

#### Factory 实现（`agenteval/models/factory.py`）

- [ ] **核心功能**
  - [ ] `ModelAdapterFactory` 类
  - [ ] `_load_config()` 方法（YAML 解析）
  - [ ] `get_adapter()` 方法（单例模式）
  - [ ] `list_models()` 方法

- [ ] **环境变量支持**
  - [ ] 支持 `${ENV_VAR}` 替换

**负责人：** ______
**实际完成日期：** ______

---

### Day 5: 模型配置文件

#### 配置文件（`config/models.yaml`）

- [ ] **Claude 系列**
  - [ ] claude-3-opus
  - [ ] claude-3-sonnet
  - [ ] claude-3-haiku

- [ ] **OpenAI 系列**
  - [ ] gpt-4-turbo
  - [ ] gpt-4o
  - [ ] gpt-3.5-turbo

- [ ] **国产模型**
  - [ ] qwen-max
  - [ ] qwen-plus
  - [ ] deepseek-chat
  - [ ] deepseek-coder

- [ ] **验收**
  - [ ] 至少 10 个模型配置完整
  - [ ] 所有配置通过 YAML 校验
  - [ ] API Key 通过环境变量注入

**负责人：** ______
**实际完成日期：** ______

---

## Week 2: Model Adapter 测试与完善

### Day 6-8: 单元测试

#### 测试用例（`tests/test_models/`）

- [ ] **Factory 测试**
  - [ ] `test_factory_list_models()`
  - [ ] `test_factory_get_adapter()`
  - [ ] `test_factory_unknown_model()`
  - [ ] `test_factory_cache()`

- [ ] **Adapter 测试**
  - [ ] `test_adapter_generate()`
  - [ ] `test_adapter_with_tools()`
  - [ ] `test_adapter_cost_calculation()`
  - [ ] `test_adapter_timeout()`
  - [ ] `test_adapter_error_handling()`

- [ ] **集成测试**
  - [ ] 测试至少 3 个模型的实际调用（需要 API Key）
  - [ ] 测试 Function Calling 功能

**负责人：** ______
**实际完成日期：** ______

### Day 9-10: 错误处理与优化

- [ ] **重试机制**
  - [ ] 实现指数退避重试
  - [ ] 配置最大重试次数
  - [ ] 记录重试日志

- [ ] **降级策略**（可选）
  - [ ] 主模型失败后使用备用模型

- [ ] **性能优化**
  - [ ] 连接池复用
  - [ ] 请求缓存（可选）

**负责人：** ______
**实际完成日期：** ______

### Week 2 验收

- [ ] ✅ 单元测试覆盖率 > 80%
- [ ] ✅ 至少 5 个模型实际调用成功
- [ ] ✅ 所有测试通过（`pytest --cov`）

---

## Week 3: Benchmark Adapters - HumanEval

### Day 11-12: 基类设计

#### 基类（`agenteval/benchmarks/base.py`）

- [ ] **枚举与数据类**
  - [ ] `TaskStatus` 枚举
  - [ ] `AdapterInfo` 数据类
  - [ ] `BaseTask` 数据类
  - [ ] `TaskResult` 数据类

- [ ] **接口定义**
  - [ ] `UnifiedEnv` 抽象基类
  - [ ] `BenchmarkAdapter` 抽象基类
  - [ ] `get_adapter_info()` 方法
  - [ ] `create_environment()` 方法
  - [ ] `load_tasks()` 方法
  - [ ] `evaluate_task()` 方法
  - [ ] `cleanup()` 方法

**负责人：** ______
**实际完成日期：** ______

### Day 13-14: HumanEval Adapter

#### 实现（`agenteval/benchmarks/humaneval_adapter.py`）

- [ ] **Task 定义**
  - [ ] `HumanEvalTask` 数据类
  - [ ] 从 JSONL 加载任务

- [ ] **执行环境**
  - [ ] `HumanEvalEnv` 类
  - [ ] `execute()` 方法（运行代码 + 测试）
  - [ ] 超时处理
  - [ ] 错误捕获

- [ ] **Adapter 实现**
  - [ ] `HumanEvalAdapter` 类
  - [ ] `load_tasks()` 实现
  - [ ] `evaluate_task()` 实现
  - [ ] 任务过滤（max_samples）

**负责人：** ______
**实际完成日期：** ______

### Day 15: Registry 与测试

#### Registry（`agenteval/benchmarks/registry.py`）

- [ ] **核心功能**
  - [ ] `BenchmarkAdapterRegistry` 类
  - [ ] `register()` 方法
  - [ ] `get_adapter()` 方法
  - [ ] `list_adapters()` 方法

- [ ] **注册内置 Adapter**
  - [ ] 注册 HumanEval

**负责人：** ______
**实际完成日期：** ______

#### 测试（`tests/test_benchmarks/`）

- [ ] **单元测试**
  - [ ] `test_humaneval_load_tasks()`
  - [ ] `test_humaneval_evaluate_task()`
  - [ ] `test_registry_get_adapter()`

- [ ] **集成测试**
  - [ ] 在 5 个 HumanEval 样本上完整测试

**负责人：** ______
**实际完成日期：** ______

### Week 3 验收

- [ ] ✅ HumanEval 在 5 个样本上测试通过
- [ ] ✅ 单元测试通过

---

## Week 4: Benchmark Adapters - SWE-bench

### Day 16-17: 环境准备

- [ ] **Docker 环境**
  - [ ] 安装 Docker
  - [ ] 配置 Docker 权限
  - [ ] 拉取 SWE-bench 官方镜像
  - [ ] 测试 Docker 容器启动与清理

- [ ] **数据集准备**
  - [ ] 下载 SWE-bench Lite 数据集
  - [ ] 解析 JSON 数据结构
  - [ ] 选择 1-2 个简单样本进行测试

**负责人：** ______
**实际完成日期：** ______

### Day 18-20: SWE-bench Adapter 实现

#### Task 与 Env（`agenteval/benchmarks/swe_bench_adapter.py`）

- [ ] **Task 定义**
  - [ ] `SWEBenchTask` 数据类
  - [ ] 解析 instance_id、repo、base_commit 等字段

- [ ] **执行环境**
  - [ ] `SWEBenchEnv` 类
  - [ ] `setup()` 方法（克隆仓库、启动容器）
  - [ ] `_clone_repo()` 方法（Git 操作）
  - [ ] `_start_container()` 方法（Docker 操作）
  - [ ] `execute()` 方法（应用 patch + 运行测试）
  - [ ] `cleanup()` 方法（清理容器）

- [ ] **Adapter 实现**
  - [ ] `SWEBenchAdapter` 类
  - [ ] `load_tasks()` 实现
  - [ ] `evaluate_task()` 实现

**负责人：** ______
**实际完成日期：** ______

### Day 21: 测试与优化

- [ ] **测试**
  - [ ] 在 1 个样本上完整测试
  - [ ] 验证 Docker 容器正确清理
  - [ ] 验证 Git 仓库缓存机制

- [ ] **优化**
  - [ ] 优化 Docker 容器复用
  - [ ] 优化 Git 仓库缓存

**负责人：** ______
**实际完成日期：** ______

### Week 4 验收

- [ ] ✅ 在 1 个 SWE-bench 样本上完整运行
- [ ] ✅ Docker 容器正确启动与清理
- [ ] ✅ 测试通过

---

## Week 5: Orchestrator + Metrics

### Day 22-23: Metrics Engine

#### 实现（`agenteval/metrics/engine.py`）

- [ ] **数据结构**
  - [ ] `MetricResult` 数据类

- [ ] **核心功能**
  - [ ] `MetricsEngine` 类
  - [ ] `compute_basic_metrics()` 方法
    - [ ] total_tasks
    - [ ] passed_tasks / failed_tasks / error_tasks / timeout_tasks
    - [ ] pass_rate / error_rate
  - [ ] `compute_operational_metrics()` 方法
    - [ ] avg_execution_time
    - [ ] p50 / p95 / p99_execution_time
  - [ ] `compute_all_metrics()` 方法

- [ ] **扩展功能**
  - [ ] `register_metric()` 方法（自定义指标）

**负责人：** ______
**实际完成日期：** ______

#### 测试（`tests/test_metrics/`）

- [ ] `test_compute_basic_metrics()`
- [ ] `test_compute_operational_metrics()`
- [ ] `test_custom_metric()`

**负责人：** ______
**实际完成日期：** ______

### Day 24-26: Batch Orchestrator

#### 实现（`agenteval/orchestrator/batch.py`）

- [ ] **数据结构**
  - [ ] `EvaluationConfig` 数据类
  - [ ] `EvaluationResult` 数据类

- [ ] **核心功能**
  - [ ] `BatchOrchestrator` 类
  - [ ] `run_evaluation()` 方法
    - [ ] 加载 Model Adapter
    - [ ] 加载 Benchmark Adapter
    - [ ] 加载任务列表
    - [ ] 并发执行任务
    - [ ] 计算指标
  - [ ] `_execute_tasks_concurrent()` 方法
    - [ ] asyncio.Semaphore 控制并发数
    - [ ] tqdm 进度条显示
  - [ ] `_execute_single_task()` 方法
    - [ ] 调用模型生成
    - [ ] 执行 Benchmark 评估
    - [ ] 错误处理

**负责人：** ______
**实际完成日期：** ______

#### 测试（`tests/test_orchestrator/`）

- [ ] `test_orchestrator_run_evaluation()`
- [ ] `test_orchestrator_concurrent_execution()`
- [ ] `test_orchestrator_timeout_handling()`

**负责人：** ______
**实际完成日期：** ______

### Week 5 验收

- [ ] ✅ 并发 5 个任务成功执行
- [ ] ✅ 进度条正常显示
- [ ] ✅ 指标计算正确

---

## Week 6: Export Engine + CLI

### Day 27-29: Export Engine

#### HTML Exporter（`agenteval/export/html_exporter.py`）

- [ ] **核心功能**
  - [ ] `HTMLExporter` 类
  - [ ] `export()` 方法
  - [ ] `_generate_pass_rate_chart_data()` 方法
  - [ ] `_generate_execution_time_chart_data()` 方法

- [ ] **HTML 模板**（`templates/evaluation_report.html`）
  - [ ] 基础信息展示（模型、Benchmark、时间）
  - [ ] 指标卡片（总任务数、通过数、通过率、平均时间）
  - [ ] 通过率饼图（ECharts）
  - [ ] 执行时间分布图（ECharts）
  - [ ] 美化样式（CSS）

**负责人：** ______
**实际完成日期：** ______

#### CSV Exporter（`agenteval/export/csv_exporter.py`）

- [ ] **核心功能**
  - [ ] `CSVExporter` 类
  - [ ] `export()` 方法（使用 Pandas）
  - [ ] 导出任务详情
  - [ ] 导出指标汇总

**负责人：** ______
**实际完成日期：** ______

### Day 30-32: CLI 工具

#### CLI 主入口（`agenteval/cli/main.py`）

- [ ] **核心功能**
  - [ ] `cli()` 主命令组
  - [ ] 添加子命令（run / list / report）
  - [ ] 版本信息（`--version`）

**负责人：** ______
**实际完成日期：** ______

#### Run 命令（`agenteval/cli/run.py`）

- [ ] **核心功能**
  - [ ] `run_command()` 函数
  - [ ] 加载 YAML 配置文件
  - [ ] 创建 `EvaluationConfig`
  - [ ] 调用 `BatchOrchestrator`
  - [ ] 导出报告
  - [ ] 打印结果摘要

**负责人：** ______
**实际完成日期：** ______

#### List 命令（`agenteval/cli/list.py`）

- [ ] **核心功能**
  - [ ] `list_command()` 函数
  - [ ] `list models` - 列出所有可用模型
  - [ ] `list benchmarks` - 列出所有可用 Benchmark

**负责人：** ______
**实际完成日期：** ______

#### Report 命令（`agenteval/cli/report.py`）（可选）

- [ ] **核心功能**
  - [ ] `report_command()` 函数
  - [ ] `--list` - 列出历史报告
  - [ ] `--open` - 在浏览器中打开报告

**负责人：** ______
**实际完成日期：** ______

### Week 6 验收

- [ ] ✅ CLI 工具安装成功（`poetry run agenteval --version`）
- [ ] ✅ `agenteval list models` 正常输出
- [ ] ✅ `agenteval run` 完整执行并生成 HTML 报告

---

## Week 7: 集成测试、文档与发布

### Day 33-34: 端到端集成测试

#### E2E 测试场景

- [ ] **场景 1: HumanEval + GPT-4**
  - [ ] 配置文件：`config/evaluations/humaneval_gpt4.yaml`
  - [ ] 运行 10 个样本
  - [ ] 验证报告生成
  - [ ] 验证指标正确

- [ ] **场景 2: SWE-bench Lite + Claude 3 Opus**
  - [ ] 配置文件：`config/evaluations/swe_bench_claude.yaml`
  - [ ] 运行 5 个样本
  - [ ] 验证 Docker 环境
  - [ ] 验证报告生成

- [ ] **场景 3: 多模型对比**
  - [ ] 同时运行 GPT-4、Claude、Qwen
  - [ ] 生成对比报告

**负责人：** ______
**实际完成日期：** ______

### Day 35: 性能测试

- [ ] **吞吐量测试**
  - [ ] 运行 100 个 HumanEval 任务
  - [ ] 验证吞吐量 > 100 tasks/hour

- [ ] **并发测试**
  - [ ] 测试 max_concurrent = 10
  - [ ] 验证资源占用合理

**负责人：** ______
**实际完成日期：** ______

### Day 36-37: 文档编写

#### 用户文档

- [ ] **README.md**
  - [ ] 项目介绍
  - [ ] 安装指南
  - [ ] 快速开始
  - [ ] 使用示例

- [ ] **用户手册（`docs/user_guide.md`）**
  - [ ] 配置说明
  - [ ] 命令详解
  - [ ] 常见问题

**负责人：** ______
**实际完成日期：** ______

#### 开发文档

- [ ] **开发指南（`docs/developer_guide.md`）**
  - [ ] 项目结构
  - [ ] 如何添加新模型
  - [ ] 如何添加新 Benchmark
  - [ ] 如何添加自定义指标

- [ ] **API 文档**
  - [ ] 自动生成（Sphinx / mkdocs）

**负责人：** ______
**实际完成日期：** ______

### Day 38: Baseline 评估与发布

- [ ] **Baseline 评估**
  - [ ] 运行多模型对比评估
  - [ ] 生成 Baseline 报告
  - [ ] 发布到 `results/baseline/`

- [ ] **版本发布**
  - [ ] 更新 `__version__.py`
  - [ ] 创建 Git Tag（v0.1.0）
  - [ ] 编写 Release Notes
  - [ ] 发布到 GitHub Releases

**负责人：** ______
**实际完成日期：** ______

---

## 最终验收清单

### 功能验收

- [ ] ✅ **Model Adapter Factory**
  - [ ] 支持至少 10 种 LLM
  - [ ] 统一的 API 接口
  - [ ] 成本计算正确

- [ ] ✅ **Benchmark Adapters**
  - [ ] SWE-bench Lite 完整运行
  - [ ] HumanEval 完整运行
  - [ ] 任务过滤功能正常

- [ ] ✅ **Batch Orchestrator**
  - [ ] 并发执行正常（max_concurrent = 5）
  - [ ] 进度追踪正常
  - [ ] 错误处理正常

- [ ] ✅ **Metrics Engine**
  - [ ] 基础指标计算正确
  - [ ] 运营指标计算正确

- [ ] ✅ **Export Engine**
  - [ ] HTML 报告美观且信息完整
  - [ ] CSV 导出正确

- [ ] ✅ **CLI 工具**
  - [ ] `agenteval run` 正常运行
  - [ ] `agenteval list` 正常输出

### 质量验收

- [ ] ✅ **测试**
  - [ ] 单元测试覆盖率 > 80%
  - [ ] 所有测试通过
  - [ ] 集成测试通过

- [ ] ✅ **代码质量**
  - [ ] Black 格式化通过
  - [ ] Ruff Linter 无警告
  - [ ] mypy 类型检查通过

- [ ] ✅ **文档**
  - [ ] 用户文档完整
  - [ ] 开发文档完整
  - [ ] API 文档自动生成

### 性能验收

- [ ] ✅ **吞吐量**
  - [ ] > 100 tasks/hour

- [ ] ✅ **并发**
  - [ ] 5 个并发任务无异常

### 交付物验收

- [ ] ✅ **代码仓库**
  - [ ] GitHub 仓库完整
  - [ ] CI/CD 流程正常

- [ ] ✅ **发布**
  - [ ] v0.1.0 版本发布
  - [ ] Release Notes 完整

- [ ] ✅ **Baseline 报告**
  - [ ] 多模型对比报告
  - [ ] 发布到指定位置

---

## 风险追踪

### 当前风险

| 风险 | 影响 | 概率 | 缓解措施 | 负责人 | 状态 |
|------|------|------|----------|--------|------|
| LiteLLM 兼容性问题 | 高 | 中 | 提前测试主流模型 | | |
| SWE-bench 环境复杂 | 高 | 高 | 参考官方 Docker 配置 | | |
| Docker 资源泄露 | 中 | 中 | 实施严格的清理策略 | | |
| API 配额限制 | 中 | 低 | 使用测试配额 + 限流 | | |

---

## 团队沟通

### 每日站会

- **时间：** 每天上午 10:00
- **形式：** 15 分钟站会
- **内容：**
  - 昨天完成了什么
  - 今天计划做什么
  - 有什么阻塞

### 周报

- **时间：** 每周五下午
- **形式：** 邮件 + 文档
- **内容：**
  - 本周完成的任务
  - 下周计划
  - 风险与问题

---

## 备注

**重要提示：**
1. 每完成一项任务，及时更新本清单
2. 遇到阻塞立即上报
3. 保持代码质量，不要为了赶进度牺牲质量
4. 多沟通，多协作

**最后更新：** ______

**当前总体进度：** _____ %
