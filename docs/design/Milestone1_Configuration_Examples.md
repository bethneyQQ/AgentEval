# Milestone 1 配置示例

本文档提供 Milestone 1 开发过程中需要的各类配置文件示例。

---

## 1. 评估配置示例

### 1.1 HumanEval - GPT-4 Turbo

```yaml
# config/evaluations/humaneval_gpt4.yaml

name: "HumanEval - GPT-4 Turbo"
description: "Evaluate GPT-4 Turbo on HumanEval benchmark"

model:
  name: gpt-4-turbo
  temperature: 0.0  # 确保可复现性
  max_tokens: 2048

benchmark:
  name: humaneval
  dataset_path: data/humaneval.jsonl
  filter:
    max_samples: 164  # 完整数据集
    # languages: [python]  # 可选，默认只有 Python

execution:
  max_concurrent: 5
  timeout: 60  # 每个任务超时时间（秒）
  retry_on_error: false  # HumanEval 不需要重试
  max_retries: 0

output:
  export_formats: [html, csv, json]
  output_dir: "results/humaneval_gpt4"
  save_individual_results: true
```

### 1.2 HumanEval - Claude 3 Opus（快速测试）

```yaml
# config/evaluations/humaneval_claude_quick.yaml

name: "HumanEval Quick Test - Claude 3 Opus"
description: "Quick test on 10 HumanEval samples"

model:
  name: claude-3-opus
  temperature: 0.0
  max_tokens: 2048

benchmark:
  name: humaneval
  dataset_path: data/humaneval.jsonl
  filter:
    max_samples: 10  # 仅测试 10 个样本

execution:
  max_concurrent: 3
  timeout: 60

output:
  export_formats: [html]
  output_dir: "results/humaneval_claude_quick"
```

### 1.3 SWE-bench Lite - Claude 3 Opus

```yaml
# config/evaluations/swe_bench_claude.yaml

name: "SWE-bench Lite - Claude 3 Opus"
description: "Evaluate Claude 3 Opus on SWE-bench Lite (sample)"

model:
  name: claude-3-opus
  temperature: 0.0
  max_tokens: 4096

benchmark:
  name: swe-bench-lite
  dataset_path: data/swe-bench-lite.json
  filter:
    max_samples: 10  # 仅测试 10 个样本（完整集有 300+）
    # repos: [django/django, flask/flask]  # 可选：仅测试特定仓库

execution:
  max_concurrent: 2  # SWE-bench 需要 Docker，并发不宜过高
  timeout: 300  # 5 分钟超时
  retry_on_error: true
  max_retries: 1

environment:
  docker_image: "swe-bench/python:3.9"
  cache_dir: "/tmp/swe_bench"
  test_command: "pytest -xvs"  # 可根据项目调整

output:
  export_formats: [html, json]
  output_dir: "results/swe_bench_claude"
  save_individual_results: true
```

### 1.4 SWE-bench Lite - Qwen-Max

```yaml
# config/evaluations/swe_bench_qwen.yaml

name: "SWE-bench Lite - Qwen-Max"
description: "Evaluate Qwen-Max on SWE-bench Lite"

model:
  name: qwen-max
  temperature: 0.0
  max_tokens: 4096

benchmark:
  name: swe-bench-lite
  dataset_path: data/swe-bench-lite.json
  filter:
    max_samples: 10

execution:
  max_concurrent: 2
  timeout: 300
  retry_on_error: true
  max_retries: 1

environment:
  docker_image: "swe-bench/python:3.9"
  cache_dir: "/tmp/swe_bench"
  test_command: "pytest -xvs"

output:
  export_formats: [html, json]
  output_dir: "results/swe_bench_qwen"
```

### 1.5 多模型对比 - HumanEval

```yaml
# config/evaluations/humaneval_comparison.yaml

name: "HumanEval Multi-Model Comparison"
description: "Compare multiple models on HumanEval (10 samples)"

# 注意：此配置需要 CLI 工具支持批量运行多个模型
# 或者手动运行多次，每次切换不同模型

models:
  - name: gpt-4-turbo
  - name: claude-3-opus
  - name: qwen-max
  - name: deepseek-chat

benchmark:
  name: humaneval
  dataset_path: data/humaneval.jsonl
  filter:
    max_samples: 10

execution:
  max_concurrent: 3
  timeout: 60

# 通用配置
model:
  temperature: 0.0
  max_tokens: 2048

output:
  export_formats: [html, csv]
  output_dir: "results/humaneval_comparison"
  generate_comparison_report: true  # 生成对比报告
```

---

## 2. 模型配置完整示例

```yaml
# config/models.yaml

# ============================================================
# OpenAI 系列
# ============================================================

models:
  gpt-4-turbo:
    adapter_type: litellm
    model_name: gpt-4-turbo-preview
    provider: openai
    api_key: ${OPENAI_API_KEY}
    max_input_tokens: 128000
    max_output_tokens: 4096
    pricing:
      input_per_1m: 10.0
      output_per_1m: 30.0
    capabilities:
      - text_generation
      - function_calling
      - code_generation
    supports_streaming: true

  gpt-4o:
    adapter_type: litellm
    model_name: gpt-4o
    provider: openai
    api_key: ${OPENAI_API_KEY}
    max_input_tokens: 128000
    max_output_tokens: 4096
    pricing:
      input_per_1m: 5.0
      output_per_1m: 15.0
    capabilities:
      - text_generation
      - function_calling
      - code_generation
      - vision

  gpt-3.5-turbo:
    adapter_type: litellm
    model_name: gpt-3.5-turbo
    provider: openai
    api_key: ${OPENAI_API_KEY}
    max_input_tokens: 16385
    max_output_tokens: 4096
    pricing:
      input_per_1m: 0.5
      output_per_1m: 1.5

# ============================================================
# Anthropic Claude 系列
# ============================================================

  claude-3-opus:
    adapter_type: litellm
    model_name: claude-3-opus-20240229
    provider: anthropic
    api_key: ${ANTHROPIC_API_KEY}
    max_input_tokens: 200000
    max_output_tokens: 4096
    pricing:
      input_per_1m: 15.0
      output_per_1m: 75.0
    capabilities:
      - text_generation
      - function_calling
      - code_generation
      - vision

  claude-3-sonnet:
    adapter_type: litellm
    model_name: claude-3-sonnet-20240229
    provider: anthropic
    api_key: ${ANTHROPIC_API_KEY}
    max_input_tokens: 200000
    max_output_tokens: 4096
    pricing:
      input_per_1m: 3.0
      output_per_1m: 15.0

  claude-3-haiku:
    adapter_type: litellm
    model_name: claude-3-haiku-20240307
    provider: anthropic
    api_key: ${ANTHROPIC_API_KEY}
    max_input_tokens: 200000
    max_output_tokens: 4096
    pricing:
      input_per_1m: 0.25
      output_per_1m: 1.25

# ============================================================
# 阿里通义千问系列
# ============================================================

  qwen-max:
    adapter_type: litellm
    model_name: qwen/qwen-max
    provider: dashscope
    api_key: ${DASHSCOPE_API_KEY}
    api_base: https://dashscope.aliyuncs.com/compatible-mode/v1
    max_input_tokens: 32000
    max_output_tokens: 8192
    pricing:
      input_per_1m: 0.5
      output_per_1m: 1.5

  qwen-plus:
    adapter_type: litellm
    model_name: qwen/qwen-plus
    provider: dashscope
    api_key: ${DASHSCOPE_API_KEY}
    api_base: https://dashscope.aliyuncs.com/compatible-mode/v1
    max_input_tokens: 32000
    max_output_tokens: 8192
    pricing:
      input_per_1m: 0.2
      output_per_1m: 0.6

# ============================================================
# DeepSeek 系列
# ============================================================

  deepseek-chat:
    adapter_type: litellm
    model_name: deepseek/deepseek-chat
    provider: deepseek
    api_key: ${DEEPSEEK_API_KEY}
    api_base: https://api.deepseek.com/v1
    max_input_tokens: 64000
    max_output_tokens: 4096
    pricing:
      input_per_1m: 0.14
      output_per_1m: 0.28

  deepseek-coder:
    adapter_type: litellm
    model_name: deepseek/deepseek-coder
    provider: deepseek
    api_key: ${DEEPSEEK_API_KEY}
    api_base: https://api.deepseek.com/v1
    max_input_tokens: 64000
    max_output_tokens: 4096
    pricing:
      input_per_1m: 0.14
      output_per_1m: 0.28
    capabilities:
      - code_generation

# ============================================================
# Google Gemini 系列（可选）
# ============================================================

  gemini-pro:
    adapter_type: litellm
    model_name: gemini/gemini-pro
    provider: google
    api_key: ${GOOGLE_API_KEY}
    max_input_tokens: 32000
    max_output_tokens: 8192
    pricing:
      input_per_1m: 0.5
      output_per_1m: 1.5
```

---

## 3. 环境变量配置

```bash
# .env

# ============================================================
# LLM API Keys
# ============================================================

# OpenAI
OPENAI_API_KEY=sk-your-openai-api-key

# Anthropic
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key

# 阿里云 DashScope (Qwen)
DASHSCOPE_API_KEY=sk-your-dashscope-key

# DeepSeek
DEEPSEEK_API_KEY=sk-your-deepseek-key

# Google (可选)
GOOGLE_API_KEY=your-google-api-key

# ============================================================
# Evaluation System Config
# ============================================================

# 缓存目录（Docker 镜像、Git 仓库等）
AGENTEVAL_CACHE_DIR=/tmp/agenteval

# 结果输出目录
AGENTEVAL_RESULTS_DIR=./results

# 日志级别
AGENTEVAL_LOG_LEVEL=INFO

# ============================================================
# Docker 配置
# ============================================================

# Docker Host（通常不需要设置）
# DOCKER_HOST=unix:///var/run/docker.sock

# ============================================================
# 网络配置（可选）
# ============================================================

# 代理设置（如果需要）
# HTTP_PROXY=http://proxy.example.com:8080
# HTTPS_PROXY=http://proxy.example.com:8080
```

---

## 4. pytest 配置

```toml
# pyproject.toml 中的 pytest 配置

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]

# 覆盖率配置
addopts = [
    "--cov=agenteval",
    "--cov-report=html",
    "--cov-report=term-missing",
    "--cov-fail-under=80",
    "-v",
]

# 标记定义
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "integration: marks tests as integration tests",
    "e2e: marks tests as end-to-end tests",
    "requires_api_key: marks tests that require API keys",
]

# 环境变量
env = [
    "AGENTEVAL_TEST_MODE=1",
]
```

---

## 5. GitHub Actions CI 配置

```yaml
# .github/workflows/ci.yml

name: CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  lint:
    name: Lint & Format Check
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install Poetry
        run: |
          curl -sSL https://install.python-poetry.org | python3 -
          echo "$HOME/.local/bin" >> $GITHUB_PATH

      - name: Install dependencies
        run: poetry install

      - name: Run Black
        run: poetry run black --check .

      - name: Run Ruff
        run: poetry run ruff check .

      - name: Run mypy
        run: poetry run mypy agenteval

  test:
    name: Test
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.10', '3.11']

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install Poetry
        run: |
          curl -sSL https://install.python-poetry.org | python3 -
          echo "$HOME/.local/bin" >> $GITHUB_PATH

      - name: Install dependencies
        run: poetry install

      - name: Run tests
        run: poetry run pytest --cov --cov-report=xml

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
          fail_ci_if_error: false

  build:
    name: Build Package
    runs-on: ubuntu-latest
    needs: [lint, test]
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install Poetry
        run: |
          curl -sSL https://install.python-poetry.org | python3 -
          echo "$HOME/.local/bin" >> $GITHUB_PATH

      - name: Build package
        run: poetry build

      - name: Upload artifacts
        uses: actions/upload-artifact@v3
        with:
          name: dist
          path: dist/
```

---

## 6. Docker Compose 配置（可选，用于本地开发）

```yaml
# docker-compose.yml

version: '3.8'

services:
  agenteval:
    build:
      context: .
      dockerfile: Dockerfile
    volumes:
      - ./config:/app/config
      - ./data:/app/data
      - ./results:/app/results
      - /var/run/docker.sock:/var/run/docker.sock  # 允许容器内启动 Docker
    env_file:
      - .env
    command: run config/evaluations/test.yaml

  # 可选：添加数据库服务（Milestone 3 使用）
  # postgres:
  #   image: timescale/timescaledb:latest-pg15
  #   environment:
  #     POSTGRES_PASSWORD: password
  #     POSTGRES_DB: agenteval
  #   ports:
  #     - "5432:5432"
  #   volumes:
  #     - postgres_data:/var/lib/postgresql/data

# volumes:
#   postgres_data:
```

---

## 7. 使用示例

### 运行单个评估

```bash
# 1. 确保已配置环境变量
cp .env.example .env
# 编辑 .env 填入 API Keys

# 2. 运行评估
poetry run agenteval run config/evaluations/humaneval_gpt4.yaml

# 3. 查看报告
open results/humaneval_gpt4/HumanEval\ -\ GPT-4\ Turbo.html
```

### 批量运行多个模型对比

```bash
#!/bin/bash
# scripts/run_comparison.sh

models=("gpt-4-turbo" "claude-3-opus" "qwen-max" "deepseek-chat")

for model in "${models[@]}"; do
    echo "Running evaluation for $model..."

    # 动态生成配置文件
    cat > /tmp/eval_${model}.yaml <<EOF
name: "HumanEval - $model"
model:
  name: $model
  temperature: 0.0
  max_tokens: 2048
benchmark:
  name: humaneval
  dataset_path: data/humaneval.jsonl
  filter:
    max_samples: 10
execution:
  max_concurrent: 3
  timeout: 60
output:
  export_formats: [html, csv]
  output_dir: "results/comparison_${model}"
EOF

    # 运行评估
    poetry run agenteval run /tmp/eval_${model}.yaml
done

echo "All evaluations completed!"
echo "Results saved in results/comparison_*/"
```

### 查看可用模型和 Benchmark

```bash
# 列出所有可用模型
poetry run agenteval list models

# 列出所有可用 Benchmark
poetry run agenteval list benchmarks
```

---

## 8. 常用命令速查

```bash
# 开发环境设置
poetry install                    # 安装依赖
poetry shell                      # 激活虚拟环境

# 代码质量检查
poetry run black .                # 格式化代码
poetry run ruff check .           # Linter 检查
poetry run mypy agenteval         # 类型检查

# 测试
poetry run pytest                 # 运行所有测试
poetry run pytest -v              # 详细输出
poetry run pytest --cov           # 测试 + 覆盖率
poetry run pytest -m "not slow"   # 跳过慢速测试
poetry run pytest -k "test_model" # 仅运行匹配的测试

# 评估运行
poetry run agenteval run config/evaluations/test.yaml
poetry run agenteval list models
poetry run agenteval list benchmarks

# 构建与发布
poetry build                      # 构建 wheel 包
poetry publish                    # 发布到 PyPI（需要配置）
```

---

## 9. 故障排查

### 问题 1: LiteLLM 安装失败

**症状：** `pip install litellm` 失败

**解决：**
```bash
# 升级 pip
pip install --upgrade pip

# 或从源码安装
pip install git+https://github.com/BerriAI/litellm.git
```

### 问题 2: API Key 未生效

**症状：** 运行评估时提示 "API key not found"

**解决：**
```bash
# 检查 .env 文件是否存在
ls -la .env

# 检查环境变量是否加载
poetry run python -c "from dotenv import load_dotenv; load_dotenv(); import os; print(os.getenv('OPENAI_API_KEY'))"

# 如果未加载，确保 litellm 支持从 .env 读取，或手动导出
export OPENAI_API_KEY="sk-xxx"
```

### 问题 3: Docker 权限问题

**症状：** "Permission denied while trying to connect to Docker daemon"

**解决：**
```bash
# 将用户添加到 docker 组
sudo usermod -aG docker $USER

# 重新登录生效
# 或临时使用 sudo
sudo poetry run agenteval run config/evaluations/swe_bench_claude.yaml
```

### 问题 4: 端口冲突

**症状：** Docker 容器启动失败

**解决：**
```bash
# 检查端口占用
sudo lsof -i :8080

# 清理所有停止的容器
docker container prune -f
```

---

## 10. 最佳实践

### 开发流程

1. **创建分支**
   ```bash
   git checkout -b feature/xxx
   ```

2. **编写代码**
   - 遵循代码规范
   - 编写单元测试

3. **本地验证**
   ```bash
   poetry run black .
   poetry run ruff check .
   poetry run mypy agenteval
   poetry run pytest
   ```

4. **提交代码**
   ```bash
   git add .
   git commit -m "feat: add xxx"
   git push origin feature/xxx
   ```

5. **创建 Pull Request**

### 测试策略

- **TDD（测试驱动开发）**：先写测试，再写实现
- **Mock 外部依赖**：使用 `unittest.mock` 或 `pytest-mock`
- **异步测试**：使用 `pytest-asyncio`

### 性能优化

- **并发控制**：根据机器性能调整 `max_concurrent`
- **缓存复用**：Git 仓库和 Docker 镜像缓存
- **批量处理**：减少网络请求次数

---

**配置文档结束**
