# ADEWorker 集成指南

**版本**: v1.0.0
**更新日期**: 2025-01-28
**适用范围**: ADEWorker v1.0+

---

## 📋 目录

1. [概述](#1-概述)
2. [前置要求](#2-前置要求)
3. [安装步骤](#3-安装步骤)
4. [配置说明](#4-配置说明)
5. [代码集成](#5-代码集成)
6. [验证测试](#6-验证测试)
7. [故障排查](#7-故障排查)
8. [性能调优](#8-性能调优)
9. [常见问题](#9-常见问题)
10. [附录](#10-附录)

---

## 1. 概述

### 1.1 集成目标

将 AgentEval Plugin 集成到 ADEWorker 中，实现：
- ✅ 自动收集 Agent 执行轨迹
- ✅ 上报数据到 AgentEval 服务端
- ✅ 性能开销 < 5%
- ✅ 低侵入性（最小化代码修改）

### 1.2 架构图

```
┌─────────────────────────────────────────────────────────┐
│                    ADEWorker                             │
│  ┌───────────────────────────────────────────────────┐  │
│  │  DevAgent                                         │  │
│  │  ├─ @instrument_agent                             │  │
│  │  │   └─ arun() / astream_run()                    │  │
│  │  ├─ @instrument_node                              │  │
│  │  │   ├─ _node_prepare_context()                   │  │
│  │  │   ├─ _node_understand_repo()                   │  │
│  │  │   ├─ _node_gen_requirement()                   │  │
│  │  │   └─ ...                                        │  │
│  └───────────────────────────────────────────────────┘  │
│                          ↓                               │
│  ┌───────────────────────────────────────────────────┐  │
│  │  AgentEval Plugin (集成层)                        │  │
│  │  ├─ EvaluationPlugin                              │  │
│  │  ├─ TraceCollector (批量上报)                     │  │
│  │  └─ SessionMapper                                 │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                          ↓ HTTP
┌─────────────────────────────────────────────────────────┐
│              AgentEval Server                            │
│              (数据接收与存储)                             │
└─────────────────────────────────────────────────────────┘
```

### 1.3 修改范围

| 文件 | 修改类型 | 影响范围 |
|------|----------|----------|
| `requirements.txt` | 新增依赖 | 1 行 |
| `backend/worker/infra/startup/startup.py` | 初始化插件 | 5-10 行 |
| `backend/worker/agent/dev_agent/agent.py` | 添加装饰器 | 10-15 行 |
| `config/agenteval_plugin.yaml` | 新增配置文件 | 新文件 |
| `.env` | 新增环境变量 | 2 行 |

**总计**: 约 20-30 行代码修改，无核心逻辑变更

---

## 2. 前置要求

### 2.1 环境要求

- **Python**: 3.10+
- **ADEWorker**: v1.0+
- **依赖**:
  - `pydantic >= 2.0`
  - `aiohttp >= 3.9`
  - `asyncio`

### 2.2 AgentEval Server

确保 AgentEval Server 已部署并可访问：
```bash
# 测试连通性
curl http://agenteval-server:8000/api/v1/health
# 预期输出: {"status": "ok"}
```

### 2.3 权限要求

- [ ] 有权修改 ADEWorker 代码
- [ ] 可以安装 Python 包
- [ ] 可以访问 AgentEval Server
- [ ] 有 API Key（从 AgentEval 管理员获取）

---

## 3. 安装步骤

### 3.1 Step 1: 安装 agenteval-plugin 包

#### 方式 1: 通过 pip 安装（生产环境推荐）

```bash
# 1. 进入 ADEWorker 项目目录
cd /path/to/adeworker

# 2. 激活虚拟环境
source .venv/bin/activate

# 3. 安装插件包
pip install agenteval-plugin==0.1.0

# 4. 更新 requirements.txt
echo "agenteval-plugin==0.1.0" >> backend/requirements.txt
```

#### 方式 2: 从源码安装（开发环境）

```bash
# 1. 克隆 agenteval-plugin 仓库
git clone https://github.com/your-org/agenteval-plugin.git /tmp/agenteval-plugin

# 2. 进入目录并安装
cd /tmp/agenteval-plugin
pip install -e .

# 3. 在 ADEWorker 的 requirements.txt 中添加本地路径
echo "-e /tmp/agenteval-plugin" >> /path/to/adeworker/backend/requirements.txt
```

#### 验证安装

```bash
python -c "import agenteval_plugin; print(agenteval_plugin.__version__)"
# 预期输出: 0.1.0
```

---

### 3.2 Step 2: 创建配置文件

#### 创建配置目录

```bash
# 创建配置目录
sudo mkdir -p /etc/agenteval
sudo mkdir -p /var/lib/agenteval/cache
sudo mkdir -p /var/log/agenteval

# 设置权限（假设 ADEWorker 以 adeworker 用户运行）
sudo chown -R adeworker:adeworker /etc/agenteval
sudo chown -R adeworker:adeworker /var/lib/agenteval
sudo chown -R adeworker:adeworker /var/log/agenteval
```

#### 创建配置文件

```bash
cat > /etc/agenteval/config.yaml <<EOF
# AgentEval Plugin 配置文件
# 版本: v1.0

# 全局配置
global:
  enabled: true
  log_level: INFO
  log_file: /var/log/agenteval/plugin.log

# Trace Collector 配置
trace_collector:
  enabled: true

  # 上报端点（根据实际环境修改）
  endpoint: "http://agenteval-server:8000/api/v1/traces"

  # API Key（使用环境变量）
  api_key: "\${AGENTEVAL_API_KEY}"

  # 批量上报配置
  batch:
    max_size: 100          # 批量大小
    max_wait_seconds: 1.0  # 最大等待时间（秒）
    max_queue_size: 10000  # 队列最大长度

  # 重试配置
  retry:
    max_attempts: 3
    backoff_factor: 2.0
    max_backoff_seconds: 60

  # 采样配置
  sampling:
    rate: 0.1  # 生产环境建议 10% 采样
    # 智能采样规则
    rules:
      - condition: "error == true"
        rate: 1.0  # 错误场景全量采样
      - condition: "duration > 60"
        rate: 1.0  # 长时任务全量采样

  # 本地缓存配置（当无法上报时）
  local_cache:
    enabled: true
    cache_dir: /var/lib/agenteval/cache
    max_size_mb: 1000
    ttl_hours: 24

# 数据脱敏配置
privacy:
  enabled: true
  # 敏感字段过滤
  sensitive_fields:
    - "password"
    - "token"
    - "api_key"
    - "secret"
    - "private_key"
  # 正则替换规则
  redact_patterns:
    - pattern: "sk-[a-zA-Z0-9]{32,}"  # OpenAI API Key
      replacement: "sk-***REDACTED***"
    - pattern: "ghp_[a-zA-Z0-9]{36}"   # GitHub Token
      replacement: "ghp_***REDACTED***"
    - pattern: "AWS_ACCESS_KEY_ID=\\S+"
      replacement: "AWS_ACCESS_KEY_ID=***REDACTED***"

# 性能优化配置
performance:
  async_mode: true            # 异步执行（推荐）
  max_concurrent_uploads: 5   # 最大并发上传数
  use_compression: true       # 压缩上报数据（减少 70% 流量）

# 插件配置
plugins:
  - id: "evaluation_plugin"
    enabled: true
    priority: 100
    sampling_rate: 0.1  # 插件级采样率
    async_mode: true
EOF
```

---

### 3.3 Step 3: 配置环境变量

#### 修改 .env 文件

```bash
cd /path/to/adeworker

# 在 .env 文件中添加以下内容
cat >> .env <<EOF

# ===== AgentEval Plugin 配置 =====
# 是否启用 AgentEval Plugin
AGENTEVAL_ENABLED=true

# AgentEval API Key（从管理员获取）
AGENTEVAL_API_KEY=your-api-key-here

# AgentEval 配置文件路径
AGENTEVAL_CONFIG_FILE=/etc/agenteval/config.yaml
EOF
```

#### 验证环境变量

```bash
source .env
echo $AGENTEVAL_ENABLED
# 预期输出: true

echo $AGENTEVAL_API_KEY
# 预期输出: your-api-key-here
```

---

## 4. 配置说明

### 4.1 关键配置项

| 配置项 | 说明 | 推荐值 |
|--------|------|--------|
| `sampling.rate` | 采样率 | 开发: 1.0, 生产: 0.1 |
| `batch.max_size` | 批量大小 | 100-200 |
| `batch.max_wait_seconds` | 批量等待时间 | 1.0s |
| `performance.async_mode` | 异步执行 | true |
| `privacy.enabled` | 数据脱敏 | true |
| `local_cache.enabled` | 本地缓存 | true |

### 4.2 环境变量说明

| 环境变量 | 必填 | 说明 |
|----------|------|------|
| `AGENTEVAL_ENABLED` | 是 | 是否启用插件（true/false） |
| `AGENTEVAL_API_KEY` | 是 | API Key |
| `AGENTEVAL_CONFIG_FILE` | 否 | 配置文件路径（默认: /etc/agenteval/config.yaml） |

### 4.3 开发环境 vs 生产环境

```yaml
# 开发环境配置
trace_collector:
  sampling:
    rate: 1.0  # 全量采样，便于调试
  batch:
    max_size: 10  # 小批量，快速上报
global:
  log_level: DEBUG

# 生产环境配置
trace_collector:
  sampling:
    rate: 0.1  # 10% 采样，减少开销
  batch:
    max_size: 200  # 大批量，减少请求
global:
  log_level: INFO
```

---

## 5. 代码集成

### 5.1 Step 4: 修改启动脚本

**文件**: `backend/worker/infra/startup/startup.py`

```python
# 在文件顶部添加导入
import os
from agenteval_plugin import init_agenteval_plugin
from agenteval_plugin.plugins.evaluation_plugin import EvaluationPlugin
from agenteval_plugin.core.plugin_manager import plugin_manager

async def startup():
    """应用启动函数"""

    # ... 其他启动逻辑（保持不变） ...

    # ===== 添加以下代码块 =====
    # 初始化 AgentEval Plugin
    agenteval_enabled = os.getenv('AGENTEVAL_ENABLED', 'false').lower() == 'true'
    if agenteval_enabled:
        try:
            logger.info("Initializing AgentEval Plugin...")

            # 从配置文件初始化
            config_file = os.getenv('AGENTEVAL_CONFIG_FILE', '/etc/agenteval/config.yaml')
            init_agenteval_plugin(config_file=config_file)

            # 注册 EvaluationPlugin
            plugin_manager.register_plugin(EvaluationPlugin())

            logger.info("AgentEval Plugin initialized successfully!")
        except Exception as e:
            logger.error(f"Failed to initialize AgentEval Plugin: {e}")
            # 不影响主流程，继续启动
    # ===== 代码块结束 =====

    # ... 其他启动逻辑（保持不变） ...
```

**代码位置**: 在现有启动逻辑之后添加，通常在数据库初始化、Redis 连接之后

---

### 5.2 Step 5: 装饰 DevAgent 方法

**文件**: `backend/worker/agent/dev_agent/agent.py`

```python
# 在文件顶部添加导入
from agenteval_plugin.decorators import instrument_agent, instrument_node

class BaseDevAgent(BaseAgent):
    def __init__(self, llm, rules: str):
        # ... 原有代码（保持不变） ...
        pass

    # ===== 添加装饰器 =====

    @instrument_agent(agent_type="DevAgent", agent_version="1.0.0")
    async def arun(self, user_input: UserInput) -> DevState:
        """异步执行 workflow"""
        state = DevState(input=user_input)

        state = await self.workflow.ainvoke(
            input=state,
            config={"configurable": {"thread_id": user_input.task_id}}
        )

        return state

    @instrument_agent(agent_type="DevAgent", agent_version="1.0.0")
    async def astream_run(self, user_input: UserInput):
        """流式执行 workflow"""
        state = DevState(input=user_input)

        async for step_state in self.workflow.astream(
            input=state,
            config={"configurable": {"thread_id": user_input.task_id}},
            stream_mode="values"
        ):
            yield step_state

    # ===== 装饰节点方法 =====

    @instrument_node(node_name="prepare_context")
    def _node_prepare_context(self, state: DevState) -> DevState:
        """准备上下文"""
        # ... 原有代码（保持不变） ...
        return state

    @instrument_node(node_name="understand_repo")
    def _node_understand_repo(self, state: DevState) -> DevState:
        """理解代码仓库"""
        # ... 原有代码（保持不变） ...
        return state

    @instrument_node(node_name="gen_requirement")
    def _node_gen_requirement(self, state: DevState) -> DevState:
        """生成需求文档"""
        # ... 原有代码（保持不变） ...
        return state

    @instrument_node(node_name="gen_solution")
    def _node_gen_solution(self, state: DevState) -> DevState:
        """生成解决方案"""
        # ... 原有代码（保持不变） ...
        return state

    @instrument_node(node_name="gen_code")
    def _node_gen_code(self, state: DevState) -> DevState:
        """生成代码"""
        # ... 原有代码（保持不变） ...
        return state

    @instrument_node(node_name="execute_code")
    def _node_execute_code(self, state: DevState) -> DevState:
        """执行代码"""
        # ... 原有代码（保持不变） ...
        return state

    # ... 其他方法（保持不变） ...
```

**注意事项**:
- 只需添加装饰器，**不修改**方法内部逻辑
- 所有节点方法都应添加 `@instrument_node` 装饰器
- 装饰器放在方法定义的**正上方**

---

### 5.3 Step 6: (可选) 装饰其他 Agent

如果有其他 Agent（如 `PMAgent`、`ChatAgent`），也可以添加装饰器：

```python
# backend/worker/agent/pm_agent/agent.py

from agenteval_plugin.decorators import instrument_agent

class PMAgent(BaseAgent):
    @instrument_agent(agent_type="PMAgent", agent_version="1.0.0")
    async def arun(self, user_input: UserInput):
        # ... 原有代码 ...
        pass
```

---

## 6. 验证测试

### 6.1 Step 7: 重启 ADEWorker

```bash
# 停止 ADEWorker
./run.sh stop

# 重新构建（如果使用 Docker）
docker-compose build backend-service

# 启动 ADEWorker
./run.sh start

# 查看启动日志
docker-compose logs -f backend-service
```

**预期日志输出**:
```
INFO - Initializing AgentEval Plugin...
INFO - TraceCollector started
INFO - Registered plugin: AgentEval Evaluation Plugin v1.0.0
INFO - AgentEval Plugin initialized successfully!
```

---

### 6.2 Step 8: 执行测试任务

#### 方式 1: 通过 API 测试

```bash
curl -X 'POST' \
  'http://localhost:5001/api/cline/openai_compatible/v1/chat/completions?user_id=test_user&project_id=test_project&ade_id=test_ade' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -H 'x-loom-client: tester' \
  -H 'x-loom-sessionid: test_session_1' \
  -H 'x-loom-workspacepath: /home/ade/ws/test_project' \
  -d '{
  "model": "gpt-4",
  "messages": [
    {
      "role": "user",
      "content": "<task>实现一个 Hello World 函数</task>"
    }
  ],
  "temperature": 0.7,
  "stream": false
}'
```

#### 方式 2: 通过 Python 脚本测试

```python
# test_agenteval_integration.py

import asyncio
from worker.agent.dev_agent.agent import BaseDevAgent
from worker.agent.agent_base.model import UserInput

async def test_agenteval():
    # 创建 DevAgent
    agent = BaseDevAgent(llm=your_llm, rules="test_rules")

    # 执行任务
    user_input = UserInput(
        task_id="test_task_001",
        task_desc="实现一个 Hello World 函数",
        repo_ws_path="/tmp/test_repo",
        user_id="test_user",
        session_id="test_session_001"
    )

    result = await agent.arun(user_input)
    print(f"Task completed: {result.output.status}")

if __name__ == "__main__":
    asyncio.run(test_agenteval())
```

运行测试:
```bash
python test_agenteval_integration.py
```

---

### 6.3 Step 9: 验证数据上报

#### 检查日志

```bash
# 查看 AgentEval Plugin 日志
tail -f /var/log/agenteval/plugin.log

# 预期输出:
# [INFO] Created trace trace-xxx for task test_task_001
# [DEBUG] Flushing 3 events...
# [DEBUG] Uploaded 3 traces successfully
```

#### 检查 AgentEval Server

```bash
# 查询 Trace 数据
curl -X GET "http://agenteval-server:8000/api/v1/traces?task_id=test_task_001" \
  -H "Authorization: Bearer your-api-key"

# 预期输出: JSON 格式的 Trace 数据
{
  "traces": [
    {
      "trace_id": "trace-xxx",
      "spans": [...],
      "attributes": {
        "agent.type": "DevAgent",
        "task.id": "test_task_001"
      }
    }
  ]
}
```

#### 检查本地缓存（如果上报失败）

```bash
# 查看本地缓存文件
ls -lh /var/lib/agenteval/cache

# 如果有文件，说明上报失败，数据被缓存
# 检查网络连接和 API Key
```

---

### 6.4 Step 10: 性能验证

运行性能 Benchmark 测试：

```bash
# 运行性能测试脚本
python tests/performance/benchmark.py

# 预期输出:
# ============================================================
# BENCHMARK RESULTS
# ============================================================
# Baseline Mean: 12.5s
# With Plugin Mean: 12.8s
# Overhead (Mean): 2.4%
#
# Baseline P95: 18.3s
# With Plugin P95: 18.6s
# Overhead (P95): 1.6%
# ============================================================
#
# ✅ Performance test PASSED! Overhead < 5%
```

**验收标准**:
- [ ] 平均开销 < 5%
- [ ] P95 开销 < 5%
- [ ] 无内存泄漏
- [ ] 无异常崩溃

---

## 7. 故障排查

### 7.1 插件未启动

**症状**: 启动日志中没有 "AgentEval Plugin initialized"

**排查步骤**:
1. 检查环境变量
   ```bash
   echo $AGENTEVAL_ENABLED
   # 应该输出: true
   ```

2. 检查配置文件路径
   ```bash
   ls -l $AGENTEVAL_CONFIG_FILE
   # 应该存在
   ```

3. 查看错误日志
   ```bash
   docker-compose logs backend-service | grep -i agenteval
   ```

---

### 7.2 数据未上报

**症状**: Trace 数据未出现在 AgentEval Server

**排查步骤**:
1. 检查网络连通性
   ```bash
   curl http://agenteval-server:8000/api/v1/health
   ```

2. 检查 API Key
   ```bash
   echo $AGENTEVAL_API_KEY
   # 验证 Key 是否正确
   ```

3. 查看本地缓存
   ```bash
   ls -lh /var/lib/agenteval/cache
   # 如果有文件，说明上报失败
   ```

4. 查看插件日志
   ```bash
   tail -f /var/log/agenteval/plugin.log | grep -i error
   ```

**常见错误**:
- `401 Unauthorized`: API Key 错误
- `Connection refused`: 服务端不可达
- `Timeout`: 网络延迟过高

---

### 7.3 性能开销过大

**症状**: Agent 执行变慢 > 5%

**优化措施**:
1. 降低采样率
   ```yaml
   # config.yaml
   trace_collector:
     sampling:
       rate: 0.05  # 降低到 5%
   ```

2. 增加批量大小
   ```yaml
   batch:
     max_size: 200  # 增加到 200
   ```

3. 禁用某些钩子
   ```python
   # 在 EvaluationPlugin 中注释掉不需要的钩子
   # async def on_state_update(...):
   #     pass
   ```

4. 检查异步模式
   ```yaml
   performance:
     async_mode: true  # 确保为 true
   ```

---

### 7.4 内存泄漏

**症状**: 内存持续增长

**排查步骤**:
1. 使用 memory_profiler 监控
   ```bash
   pip install memory-profiler
   python -m memory_profiler test_agenteval_integration.py
   ```

2. 检查队列积压
   ```python
   # 添加监控代码
   from agenteval_plugin.trace.trace_collector import get_trace_collector

   collector = get_trace_collector()
   print(f"Queue size: {collector.event_queue.qsize()}")
   ```

3. 调整队列大小
   ```yaml
   batch:
     max_queue_size: 5000  # 减小队列
   ```

---

## 8. 性能调优

### 8.1 生产环境推荐配置

```yaml
# 生产环境配置（优化后）
trace_collector:
  # 采样率调整
  sampling:
    rate: 0.05  # 5% 采样（根据流量调整）
    rules:
      - condition: "error == true"
        rate: 1.0  # 错误全量采样

  # 批量优化
  batch:
    max_size: 200           # 大批量
    max_wait_seconds: 2.0   # 稍长的等待时间
    max_queue_size: 5000    # 适中的队列

  # 重试优化
  retry:
    max_attempts: 2  # 减少重试次数
    max_backoff_seconds: 30

# 性能优化
performance:
  async_mode: true
  max_concurrent_uploads: 3  # 降低并发
  use_compression: true
```

### 8.2 采样策略

根据业务场景选择合适的采样率：

| 场景 | 推荐采样率 | 说明 |
|------|-----------|------|
| 开发环境 | 100% | 全量采样，便于调试 |
| 测试环境 | 50% | 部分采样，验证功能 |
| 生产环境（低流量） | 10-20% | 适度采样 |
| 生产环境（高流量） | 1-5% | 低采样率，减少开销 |
| 错误场景 | 100% | 始终全量采样 |
| 长时任务 | 100% | 重要任务全量采样 |

### 8.3 监控指标

建议监控以下指标：

```python
# 添加到 Prometheus Metrics
from prometheus_client import Counter, Histogram

# Trace 上报计数
trace_uploaded = Counter(
    'agenteval_trace_uploaded_total',
    'Total number of traces uploaded'
)

# 上报延迟
upload_duration = Histogram(
    'agenteval_upload_duration_seconds',
    'Time spent uploading traces'
)

# 队列长度
queue_size = Gauge(
    'agenteval_queue_size',
    'Current queue size'
)
```

---

## 9. 常见问题

### Q1: 是否会影响 ADEWorker 的正常功能？

**A**: 不会。插件采用异常隔离设计，即使插件出错，也不会影响 Agent 执行。

---

### Q2: 如何临时禁用插件？

**A**: 有三种方式：

```bash
# 方式 1: 环境变量（推荐）
export AGENTEVAL_ENABLED=false

# 方式 2: 配置文件
# config.yaml
global:
  enabled: false

# 方式 3: 运行时禁用
from agenteval_plugin.core.plugin_manager import plugin_manager
plugin_manager.disable_plugin("evaluation_plugin")
```

---

### Q3: 数据会被脱敏吗？

**A**: 是的。默认会脱敏以下信息：
- API Key (如 `sk-xxxxx`)
- GitHub Token (如 `ghp_xxxxx`)
- Password 字段
- 自定义敏感字段

可在配置文件中自定义脱敏规则。

---

### Q4: 如何查看上报了哪些数据？

**A**: 查看日志：

```bash
# 开启 DEBUG 日志
# config.yaml
global:
  log_level: DEBUG

# 查看详细日志
tail -f /var/log/agenteval/plugin.log
```

---

### Q5: 插件会增加多少磁盘占用？

**A**:
- 插件包大小: ~5MB
- 日志文件: ~10MB/天（视采样率而定）
- 本地缓存: 最多 1GB（可配置）

---

### Q6: 如何升级插件版本？

**A**:

```bash
# 1. 停止 ADEWorker
./run.sh stop

# 2. 升级插件
pip install --upgrade agenteval-plugin

# 3. 更新 requirements.txt
echo "agenteval-plugin==0.2.0" > backend/requirements.txt

# 4. 重启
./run.sh start
```

---

### Q7: 支持哪些部署方式？

**A**: 支持所有主流部署方式：
- Docker / Docker Compose ✅
- Kubernetes ✅
- 裸金属部署 ✅
- Serverless (需调整配置) ✅

---

### Q8: 如何自定义插件？

**A**: 参考 [Plugin Development Guide](../guides/PLUGIN_DEVELOPMENT_GUIDE.md)

---

## 10. 附录

### 10.1 完整的集成检查清单

- [ ] **安装**
  - [ ] 安装 agenteval-plugin 包
  - [ ] 更新 requirements.txt

- [ ] **配置**
  - [ ] 创建配置目录
  - [ ] 创建配置文件 `/etc/agenteval/config.yaml`
  - [ ] 设置环境变量 `AGENTEVAL_ENABLED` 和 `AGENTEVAL_API_KEY`

- [ ] **代码修改**
  - [ ] 修改 `startup.py`（初始化插件）
  - [ ] 装饰 `DevAgent.arun()`
  - [ ] 装饰 `DevAgent.astream_run()`
  - [ ] 装饰所有节点方法

- [ ] **验证**
  - [ ] 重启 ADEWorker
  - [ ] 检查启动日志
  - [ ] 执行测试任务
  - [ ] 验证数据上报
  - [ ] 运行性能测试

- [ ] **上线**
  - [ ] Code Review
  - [ ] 集成测试通过
  - [ ] 性能测试通过（开销 < 5%）
  - [ ] 生产环境灰度发布

---

### 10.2 回滚步骤

如果需要回滚（移除插件）：

```bash
# 1. 移除装饰器
# 在 agent.py 中删除所有 @instrument_agent 和 @instrument_node

# 2. 移除初始化代码
# 在 startup.py 中删除 AgentEval Plugin 初始化代码块

# 3. 卸载插件包
pip uninstall agenteval-plugin

# 4. 删除环境变量
# 从 .env 中删除 AGENTEVAL_* 相关变量

# 5. 重启
./run.sh restart
```

---

### 10.3 联系支持

遇到问题？联系我们：

- **邮箱**: support@agenteval.com
- **Slack**: #agenteval-support
- **文档**: https://docs.agenteval.com
- **Issue**: https://github.com/your-org/agenteval-plugin/issues

---

### 10.4 参考资料

- [Plugin API Specification](../api/PLUGIN_API_SPECIFICATION.md)
- [Plugin Development Guide](../guides/PLUGIN_DEVELOPMENT_GUIDE.md)
- [Milestone 2 Design Document](../design/MILESTONE2_DESIGN.md)
- [ADEWorker 官方文档](https://github.com/your-org/adeworker)

---

**文档结束**

祝集成顺利！🎉
