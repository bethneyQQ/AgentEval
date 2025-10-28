# Milestone 1 快速开始指南

本指南帮助开发者快速了解如何开始实施 Milestone 1。

---

## 📚 前置阅读

在开始之前，请务必阅读：
1. [PRD - 产品需求文档](../PRD_Agent_Evaluation_System.md)
2. [Milestone 1 详细设计](./Milestone1_Offline_Evaluation_Engine_Design.md)

---

## 🎯 Milestone 1 目标概览

**目标：** 构建完整的 Offline Agent 评估引擎

**时间：** 7 周

**核心交付物：**
- ✅ CLI 工具（`agenteval run/list/report`）
- ✅ 支持 10+ LLM
- ✅ 支持 3+ Benchmark（SWE-bench、HumanEval、InterCode）
- ✅ HTML/CSV 报告生成
- ✅ 单元测试覆盖率 > 80%

---

## 🚀 Day 1: 项目初始化（2小时）

### Step 1: 创建项目骨架

```bash
# 创建项目目录
cd /home/shared/zqq/AgentEval
mkdir -p agenteval/{cli,models,benchmarks,orchestrator,metrics,export,storage,utils}
mkdir -p config/{evaluations}
mkdir -p templates
mkdir -p tests/{test_models,test_benchmarks,test_orchestrator,test_metrics,integration,e2e}
mkdir -p data
mkdir -p results

# 创建 __init__.py 文件
find agenteval tests -type d -exec touch {}/__init__.py \;
```

### Step 2: 配置 Poetry

创建 `pyproject.toml`：

```toml
[tool.poetry]
name = "agenteval"
version = "0.1.0"
description = "Agent Evaluation System - Offline Engine"
authors = ["EE Team"]
readme = "README.md"

[tool.poetry.dependencies]
python = "^3.10"
litellm = "^1.0.0"
click = "^8.0.0"
pyyaml = "^6.0"
jinja2 = "^3.1.0"
pandas = "^2.0.0"
tqdm = "^4.65.0"
asyncio = "*"
python-dotenv = "^1.0.0"

[tool.poetry.group.dev.dependencies]
pytest = "^7.0.0"
pytest-asyncio = "^0.21.0"
pytest-cov = "^4.0.0"
black = "^23.0.0"
ruff = "^0.1.0"
mypy = "^1.0.0"

[tool.poetry.scripts]
agenteval = "agenteval.cli.main:cli"

[tool.black]
line-length = 100
target-version = ['py310']

[tool.ruff]
line-length = 100
target-version = "py310"

[tool.mypy]
python_version = "3.10"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
```

### Step 3: 安装依赖

```bash
pip install poetry
poetry install
```

### Step 4: 配置环境变量

创建 `.env.example`：

```bash
# LLM API Keys
ANTHROPIC_API_KEY=your_anthropic_key
OPENAI_API_KEY=your_openai_key
DASHSCOPE_API_KEY=your_dashscope_key
DEEPSEEK_API_KEY=your_deepseek_key

# Evaluation Config
AGENTEVAL_CACHE_DIR=/tmp/agenteval
AGENTEVAL_RESULTS_DIR=./results
```

复制并填写实际 API Key：

```bash
cp .env.example .env
# 编辑 .env 填入实际的 API Keys
```

### Step 5: 配置 Git

创建 `.gitignore`：

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
.pytest_cache/
.coverage
htmlcov/

# Virtual environments
.venv/
venv/

# IDEs
.vscode/
.idea/
*.swp

# Environment
.env

# Data
data/
results/
*.db

# OS
.DS_Store
```

---

## 📝 Day 2-3: Model Adapter Factory（1天）

### 目标

实现统一的 LLM 接入层，支持多种模型。

### 核心文件

1. `agenteval/models/base.py` - 基类与接口
2. `agenteval/models/litellm_adapter.py` - LiteLLM 适配器
3. `agenteval/models/factory.py` - 工厂类
4. `config/models.yaml` - 模型配置

### 实现步骤

#### Step 1: 实现基类（1小时）

参考设计文档中的 `base.py`，实现：
- `ModelCapability` 枚举
- `ModelInfo` 数据类
- `Message` 数据类
- `Tool` 数据类
- `GenerateResponse` 数据类
- `ModelAdapter` 抽象基类

#### Step 2: 实现 LiteLLM Adapter（2小时）

参考设计文档中的 `litellm_adapter.py`，实现：
- `LiteLLMAdapter` 类
- `generate()` 方法
- `get_model_info()` 方法
- 错误处理与重试

#### Step 3: 实现 Factory（1小时）

参考设计文档中的 `factory.py`，实现：
- `ModelAdapterFactory` 类
- 从 YAML 加载配置
- 单例模式（缓存已创建的 adapter）

#### Step 4: 配置文件（1小时）

创建 `config/models.yaml`，添加：
- Claude 3 Opus/Sonnet/Haiku
- GPT-4 Turbo/GPT-4o
- Qwen-Max
- DeepSeek-Chat

#### Step 5: 单元测试（3小时）

创建 `tests/test_models/test_factory.py`：

```python
import pytest
from agenteval.models.factory import ModelAdapterFactory
from agenteval.models.base import Message

def test_factory_list_models():
    factory = ModelAdapterFactory()
    models = factory.list_models()
    assert len(models) > 0
    assert 'claude-3-opus' in models

def test_factory_get_adapter():
    factory = ModelAdapterFactory()
    adapter = factory.get_adapter('claude-3-opus')
    assert adapter is not None

def test_factory_unknown_model():
    factory = ModelAdapterFactory()
    with pytest.raises(ValueError):
        factory.get_adapter('unknown-model')

@pytest.mark.asyncio
async def test_adapter_generate():
    factory = ModelAdapterFactory()
    adapter = factory.get_adapter('claude-3-opus')

    messages = [Message(role="user", content="Say hello")]
    response = await adapter.generate(messages, max_tokens=50)

    assert response.content is not None
    assert len(response.content) > 0
```

#### 验收标准

- ✅ 所有单元测试通过
- ✅ 至少 5 个模型配置正确
- ✅ 至少 1 个模型实际调用成功（需要 API Key）

---

## 📊 Week 2-3: Benchmark Adapters（2周）

### Week 2: HumanEval Adapter（相对简单，先实现）

#### Day 1-2: 基类与 HumanEval Adapter

**任务：**
1. 实现 `benchmarks/base.py`
2. 实现 `benchmarks/humaneval_adapter.py`
3. 下载 HumanEval 数据集到 `data/humaneval.jsonl`

**验收：**
- 在 5 个样本上测试通过

#### Day 3-4: Registry 与集成测试

**任务：**
1. 实现 `benchmarks/registry.py`
2. 编写集成测试

#### Day 5: 优化与文档

### Week 3: SWE-bench Adapter（复杂，需要 Docker）

#### Day 1-2: 环境准备

**任务：**
1. 配置 Docker 环境
2. 下载 SWE-bench Lite 数据集
3. 测试 Docker 容器启动

#### Day 3-5: Adapter 实现

**任务：**
1. 实现 `benchmarks/swe_bench_adapter.py`
2. 实现 Git 仓库管理
3. 实现 Docker 环境隔离
4. 实现 Patch 应用与测试执行

#### 验收标准

- ✅ 在 1 个 SWE-bench 样本上完整运行
- ✅ Docker 容器正确清理

---

## 🔄 Week 4: Orchestrator + Metrics（1周）

### Day 1-2: Metrics Engine

**文件：** `metrics/engine.py`

**任务：**
1. 实现基础指标计算（pass_rate、error_rate）
2. 实现运营指标计算（latency、P95）
3. 编写单元测试

### Day 3-5: Batch Orchestrator

**文件：** `orchestrator/batch.py`

**任务：**
1. 实现 `BatchOrchestrator` 类
2. 实现并发任务调度（asyncio）
3. 实现进度追踪（tqdm）
4. 实现错误处理

**验收：**
- ✅ 并发 5 个任务无异常
- ✅ 超时正确处理

---

## 📄 Week 5: Export + CLI（1周）

### Day 1-3: Export Engine

**任务：**
1. 实现 HTML 报告生成（Jinja2）
2. 设计美观的 HTML 模板（ECharts 图表）
3. 实现 CSV 导出

### Day 4-5: CLI 工具

**文件：** `cli/main.py`, `cli/run.py`

**任务：**
1. 实现 `agenteval run` 命令
2. 实现 `agenteval list` 命令
3. 编写 CLI 使用文档

**测试：**

```bash
# 测试 CLI
poetry run agenteval list models
poetry run agenteval list benchmarks
poetry run agenteval run config/evaluations/test.yaml
```

---

## 🧪 Week 6-7: 测试与优化（2周）

### Week 6: 集成测试

**任务：**
1. 完整流程测试（HumanEval + GPT-4）
2. 完整流程测试（SWE-bench Lite + Claude，10 样本）
3. 性能测试（吞吐量 > 100 tasks/hour）

### Week 7: 文档与发布

**任务：**
1. 编写用户手册
2. 编写开发文档
3. 运行 Baseline 评估（多模型对比）
4. 发布 v0.1.0

---

## 📋 每日检查清单

### 每天开始前

- [ ] 拉取最新代码：`git pull`
- [ ] 确认环境正常：`poetry install`
- [ ] 运行测试确保基础功能正常：`poetry run pytest`

### 每天结束前

- [ ] 运行代码格式化：`poetry run black .`
- [ ] 运行 Linter：`poetry run ruff check .`
- [ ] 运行类型检查：`poetry run mypy agenteval`
- [ ] 运行测试：`poetry run pytest --cov`
- [ ] 提交代码：`git commit -m "feat: xxx"`

---

## 🐛 常见问题

### Q1: LiteLLM 安装失败

**解决：**
```bash
# 尝试升级 pip
pip install --upgrade pip

# 或者从源码安装
pip install git+https://github.com/BerriAI/litellm.git
```

### Q2: Docker 权限问题

**解决：**
```bash
# 将当前用户添加到 docker 组
sudo usermod -aG docker $USER

# 重新登录生效
```

### Q3: API Key 环境变量未生效

**解决：**
```bash
# 确保加载了 .env 文件
poetry run python -c "from dotenv import load_dotenv; load_dotenv(); import os; print(os.getenv('ANTHROPIC_API_KEY'))"
```

---

## 📚 参考资源

### 官方文档

- [LiteLLM 文档](https://docs.litellm.ai/)
- [Click 文档](https://click.palletsprojects.com/)
- [Jinja2 文档](https://jinja.palletsprojects.com/)

### 数据集下载

- [HumanEval](https://github.com/openai/human-eval/tree/master/data)
- [SWE-bench](https://www.swebench.com/)

### 示例项目

- [LangChain Evaluation](https://github.com/langchain-ai/langchain/tree/master/libs/langchain/langchain/evaluation)

---

## 🎯 下一步

完成 Milestone 1 后，继续：
- [Milestone 2: adeworker 集成层](./Milestone2_ADEWorker_Integration_Design.md)
- [Milestone 3: Online Tracing 系统](./Milestone3_Online_Tracing_Design.md)

---

**祝开发顺利！有问题随时在团队频道提问。** 🚀
