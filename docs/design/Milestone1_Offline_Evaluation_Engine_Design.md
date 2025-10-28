# Milestone 1: Offline 评估引擎 - 详细设计文档

**版本：** v1.0
**日期：** 2025-01-28
**状态：** 设计阶段
**开发周期：** 7 周

---

## 📋 目录

1. [总览](#1-总览)
2. [架构设计](#2-架构设计)
3. [核心模块详细设计](#3-核心模块详细设计)
4. [数据模型](#4-数据模型)
5. [配置系统](#5-配置系统)
6. [代码框架](#6-代码框架)
7. [详细任务分解](#7-详细任务分解)
8. [测试策略](#8-测试策略)
9. [开发规范](#9-开发规范)
10. [部署与运行](#10-部署与运行)

---

## 1. 总览

### 1.1 目标

构建一个完整的 **Offline Agent 评估引擎**，支持：
- ✅ 统一的 LLM 接入层（10+ 模型）
- ✅ 多种 Benchmark 适配（SWE-bench、InterCode、HumanEval）
- ✅ 并发批量评估能力
- ✅ 多维度指标计算
- ✅ 可视化报告生成

### 1.2 核心价值

| 价值点 | 说明 |
|--------|------|
| **模型横向对比** | 在相同 Benchmark 上公平对比多个 LLM |
| **可复现评估** | 固定环境、固定配置，确保结果可重复 |
| **快速验证** | 支持 PR Smoke Test（200-500 样本，< 1 小时） |
| **扩展性** | 轻松添加新模型、新 Benchmark |

### 1.3 核心指标

| 指标 | 目标值 | 度量方式 |
|------|--------|----------|
| 支持的 LLM 数量 | ≥ 10 | 配置文件统计 |
| 评估吞吐量 | > 100 tasks/hour | Benchmark 测试 |
| 并发任务数 | ≥ 5 | 并发测试 |
| 单元测试覆盖率 | > 80% | Coverage 报告 |
| 报告生成时间 | < 30s | 性能测试 |

### 1.4 交付物

| 交付物 | 说明 |
|--------|------|
| **CLI 工具** | 命令行评估工具（`agenteval run`） |
| **Python Package** | 可安装的 Python 包 |
| **配置示例** | 5+ 个评估场景配置 |
| **评估报告** | Baseline 多模型对比报告 |
| **文档** | 用户手册、API 文档、开发文档 |

---

## 2. 架构设计

### 2.1 整体架构

```
┌──────────────────────────────────────────────────────────────┐
│                         CLI Layer                             │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐ │
│  │ agenteval run  │  │ agenteval list │  │ agenteval      │ │
│  │                │  │                │  │ report         │ │
│  └────────────────┘  └────────────────┘  └────────────────┘ │
└──────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────┐
│                    Core Orchestration Layer                   │
│  ┌────────────────────────────────────────────────────────┐  │
│  │               BatchOrchestrator                        │  │
│  │  ├─ Task Scheduler                                     │  │
│  │  ├─ Concurrent Executor (asyncio)                      │  │
│  │  ├─ Progress Tracker                                   │  │
│  │  └─ Result Aggregator                                  │  │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────┐
│                      Adapter Layer                            │
│  ┌──────────────────┐  ┌──────────────────────────────────┐ │
│  │ Model Adapter    │  │  Benchmark Adapter               │ │
│  │ Factory          │  │  Registry                        │ │
│  │  ├─ LiteLLM      │  │  ├─ SWEBenchAdapter             │ │
│  │  ├─ OpenAI       │  │  ├─ InterCodeAdapter            │ │
│  │  ├─ Anthropic    │  │  ├─ HumanEvalAdapter            │ │
│  │  ├─ Custom       │  │  └─ CustomAdapter               │ │
│  └──────────────────┘  └──────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────┐
│                      Execution Layer                          │
│  ┌──────────────────┐  ┌──────────────────────────────────┐ │
│  │ Environment      │  │  Metrics Engine                  │ │
│  │ Manager          │  │  ├─ Basic Metrics                │ │
│  │  ├─ Docker       │  │  ├─ Quality Metrics              │ │
│  │  ├─ Isolation    │  │  ├─ Operational Metrics          │ │
│  │  └─ Cleanup      │  │  └─ Custom Metrics               │ │
│  └──────────────────┘  └──────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────┐
│                      Output Layer                             │
│  ┌──────────────────┐  ┌──────────────────────────────────┐ │
│  │ Export Engine    │  │  Storage                         │ │
│  │  ├─ HTML         │  │  ├─ SQLite (Local)               │ │
│  │  ├─ PDF          │  │  ├─ JSON Files                   │ │
│  │  ├─ CSV          │  │  └─ Reports                      │ │
│  │  └─ JSON         │  │                                  │ │
│  └──────────────────┘  └──────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

### 2.2 数据流设计

```
┌─────────────┐
│ Config YAML │
└─────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│  ConfigLoader                                               │
│  ├─ Parse YAML                                              │
│  ├─ Validate Schema                                         │
│  └─ Load Model & Benchmark Config                          │
└─────────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│  BatchOrchestrator                                          │
│  ├─ Create Task Queue                                       │
│  └─ Spawn Workers (max_concurrent)                          │
└─────────────────────────────────────────────────────────────┘
       │
       ├─────────────┬─────────────┬─────────────┐
       ▼             ▼             ▼             ▼
  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐
  │ Worker 1│  │ Worker 2│  │ Worker 3│  │ Worker N│
  └─────────┘  └─────────┘  └─────────┘  └─────────┘
       │
       │  For each task:
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│  Task Execution Pipeline                                    │
│                                                             │
│  1. BenchmarkAdapter.load_task()                            │
│      ├─ Load problem description                           │
│      └─ Prepare environment                                 │
│                                                             │
│  2. ModelAdapter.generate()                                 │
│      ├─ Format prompt                                       │
│      ├─ Call LLM API                                        │
│      └─ Parse response                                      │
│                                                             │
│  3. BenchmarkAdapter.execute()                              │
│      ├─ Run generated code/solution                         │
│      └─ Capture output                                      │
│                                                             │
│  4. BenchmarkAdapter.evaluate()                             │
│      ├─ Compare with expected output                        │
│      └─ Return pass/fail                                    │
│                                                             │
│  5. MetricsEngine.compute()                                 │
│      ├─ Calculate metrics                                   │
│      └─ Store result                                        │
└─────────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│  Result Aggregator                                          │
│  ├─ Collect all task results                                │
│  ├─ Aggregate metrics                                       │
│  └─ Generate summary statistics                             │
└─────────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│  Export Engine                                              │
│  ├─ Generate HTML Report (with charts)                      │
│  ├─ Generate PDF Report                                     │
│  ├─ Export CSV Data                                         │
│  └─ Save JSON Results                                       │
└─────────────────────────────────────────────────────────────┘
```

### 2.3 模块依赖关系

```
CLI
 ├─ depends on: BatchOrchestrator
 └─ depends on: ExportEngine

BatchOrchestrator
 ├─ depends on: ModelAdapterFactory
 ├─ depends on: BenchmarkAdapterRegistry
 ├─ depends on: MetricsEngine
 └─ depends on: EnvironmentManager

ModelAdapterFactory
 └─ depends on: LiteLLM (external)

BenchmarkAdapterRegistry
 ├─ depends on: SWEBenchAdapter
 ├─ depends on: InterCodeAdapter
 └─ depends on: HumanEvalAdapter

MetricsEngine
 └─ standalone (no dependencies)

ExportEngine
 ├─ depends on: Jinja2 (HTML)
 ├─ depends on: ReportLab (PDF)
 └─ depends on: Pandas (CSV)
```

---

## 3. 核心模块详细设计

### 3.1 Model Adapter Factory

#### 3.1.1 设计目标

- 统一封装 10+ LLM API
- 支持配置驱动添加新模型
- 统一的错误处理与重试机制
- Token 使用量与成本追踪

#### 3.1.2 类设计

```python
# agenteval/models/base.py

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from enum import Enum

class ModelCapability(Enum):
    """模型能力枚举"""
    TEXT_GENERATION = "text_generation"
    FUNCTION_CALLING = "function_calling"
    VISION = "vision"
    CODE_GENERATION = "code_generation"

@dataclass
class ModelInfo:
    """模型元信息"""
    name: str
    provider: str  # openai, anthropic, custom
    capabilities: List[ModelCapability]
    max_input_tokens: int
    max_output_tokens: int
    pricing: Dict[str, float]  # {"input_per_1m": 1.0, "output_per_1m": 3.0}
    supports_streaming: bool = True

@dataclass
class Message:
    """对话消息"""
    role: str  # system, user, assistant
    content: str

@dataclass
class Tool:
    """Function Calling 工具定义"""
    name: str
    description: str
    parameters: Dict[str, Any]  # JSON Schema

@dataclass
class GenerateResponse:
    """生成响应"""
    content: str
    finish_reason: str
    tool_calls: Optional[List[Dict]] = None
    usage: Optional[Dict[str, int]] = None  # prompt_tokens, completion_tokens
    cost: Optional[float] = None
    latency: Optional[float] = None

class ModelAdapter(ABC):
    """模型适配器基类"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._client = None

    @abstractmethod
    async def generate(
        self,
        messages: List[Message],
        tools: Optional[List[Tool]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs
    ) -> GenerateResponse:
        """生成响应"""
        pass

    @abstractmethod
    def get_model_info(self) -> ModelInfo:
        """获取模型信息"""
        pass

    def calculate_cost(self, usage: Dict[str, int]) -> float:
        """计算成本"""
        info = self.get_model_info()
        input_cost = (usage['prompt_tokens'] / 1_000_000) * info.pricing['input_per_1m']
        output_cost = (usage['completion_tokens'] / 1_000_000) * info.pricing['output_per_1m']
        return input_cost + output_cost
```

#### 3.1.3 LiteLLM 实现

```python
# agenteval/models/litellm_adapter.py

import litellm
from typing import List, Optional, Dict, Any
import time
from .base import ModelAdapter, Message, Tool, GenerateResponse, ModelInfo, ModelCapability

class LiteLLMAdapter(ModelAdapter):
    """基于 LiteLLM 的通用适配器"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.model_name = config['model_name']
        self.api_base = config.get('api_base')
        self.api_key = config.get('api_key')

        # 配置 LiteLLM
        if self.api_base:
            litellm.api_base = self.api_base
        if self.api_key:
            litellm.api_key = self.api_key

    async def generate(
        self,
        messages: List[Message],
        tools: Optional[List[Tool]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs
    ) -> GenerateResponse:
        """生成响应"""
        start_time = time.time()

        # 转换消息格式
        litellm_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]

        # 转换工具格式
        litellm_tools = None
        if tools:
            litellm_tools = [
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.parameters
                    }
                }
                for tool in tools
            ]

        try:
            # 调用 LiteLLM
            response = await litellm.acompletion(
                model=self.model_name,
                messages=litellm_messages,
                tools=litellm_tools,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )

            latency = time.time() - start_time

            # 提取响应内容
            choice = response.choices[0]
            content = choice.message.content or ""
            finish_reason = choice.finish_reason

            # 提取 tool calls
            tool_calls = None
            if hasattr(choice.message, 'tool_calls') and choice.message.tool_calls:
                tool_calls = [
                    {
                        "id": tc.id,
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                    for tc in choice.message.tool_calls
                ]

            # 提取 usage
            usage = None
            cost = None
            if hasattr(response, 'usage'):
                usage = {
                    'prompt_tokens': response.usage.prompt_tokens,
                    'completion_tokens': response.usage.completion_tokens,
                    'total_tokens': response.usage.total_tokens
                }
                cost = self.calculate_cost(usage)

            return GenerateResponse(
                content=content,
                finish_reason=finish_reason,
                tool_calls=tool_calls,
                usage=usage,
                cost=cost,
                latency=latency
            )

        except Exception as e:
            raise ModelGenerationError(f"Failed to generate response: {str(e)}")

    def get_model_info(self) -> ModelInfo:
        """获取模型信息（从配置加载）"""
        # 这里简化处理，实际应该从配置文件读取
        return ModelInfo(
            name=self.model_name,
            provider=self.config.get('provider', 'unknown'),
            capabilities=[ModelCapability.TEXT_GENERATION, ModelCapability.CODE_GENERATION],
            max_input_tokens=self.config.get('max_input_tokens', 128000),
            max_output_tokens=self.config.get('max_output_tokens', 4096),
            pricing=self.config.get('pricing', {"input_per_1m": 1.0, "output_per_1m": 3.0}),
            supports_streaming=True
        )

class ModelGenerationError(Exception):
    """模型生成错误"""
    pass
```

#### 3.1.4 Factory 实现

```python
# agenteval/models/factory.py

from typing import Dict, Any, Optional
from .base import ModelAdapter
from .litellm_adapter import LiteLLMAdapter
import yaml

class ModelAdapterFactory:
    """模型适配器工厂"""

    def __init__(self, config_path: str = "config/models.yaml"):
        self.config_path = config_path
        self.models_config = self._load_config()
        self._adapter_cache: Dict[str, ModelAdapter] = {}

    def _load_config(self) -> Dict[str, Any]:
        """加载模型配置"""
        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f)

    def get_adapter(self, model_name: str) -> ModelAdapter:
        """获取模型适配器（单例）"""
        if model_name in self._adapter_cache:
            return self._adapter_cache[model_name]

        if model_name not in self.models_config['models']:
            raise ValueError(f"Model {model_name} not found in config")

        model_config = self.models_config['models'][model_name]

        # 根据 provider 选择适配器类型
        adapter_type = model_config.get('adapter_type', 'litellm')

        if adapter_type == 'litellm':
            adapter = LiteLLMAdapter(model_config)
        else:
            raise ValueError(f"Unknown adapter type: {adapter_type}")

        self._adapter_cache[model_name] = adapter
        return adapter

    def list_models(self) -> Dict[str, Dict[str, Any]]:
        """列出所有可用模型"""
        return self.models_config['models']
```

#### 3.1.5 配置文件设计

```yaml
# config/models.yaml

models:
  claude-3-opus:
    adapter_type: litellm
    model_name: claude-3-opus-20240229
    provider: anthropic
    api_key: ${ANTHROPIC_API_KEY}  # 支持环境变量
    max_input_tokens: 200000
    max_output_tokens: 4096
    pricing:
      input_per_1m: 15.0
      output_per_1m: 75.0
    capabilities:
      - text_generation
      - function_calling
      - code_generation

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

  # ... 更多模型配置
```

---

### 3.2 Benchmark Adapter System

#### 3.2.1 设计目标

- 统一的 Benchmark 接口
- 支持多种评估场景（代码生成、代码修复、交互式执行）
- Docker 环境隔离
- 可扩展的适配器机制

#### 3.2.2 统一接口设计

```python
# agenteval/benchmarks/base.py

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Dict, Any, AsyncIterator
from enum import Enum

class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"
    TIMEOUT = "timeout"

@dataclass
class AdapterInfo:
    """适配器信息"""
    name: str
    version: str
    description: str
    supported_languages: List[str]

@dataclass
class BaseTask:
    """基础任务"""
    task_id: str
    task_type: str
    description: str
    metadata: Dict[str, Any]

@dataclass
class TaskResult:
    """任务结果"""
    task_id: str
    status: TaskStatus
    passed: bool
    output: str
    error_message: Optional[str] = None
    execution_time: Optional[float] = None
    metrics: Optional[Dict[str, Any]] = None

class UnifiedEnv(ABC):
    """统一的执行环境接口"""

    @abstractmethod
    async def execute(self, code: str, timeout: int = 60) -> Dict[str, Any]:
        """执行代码"""
        pass

    @abstractmethod
    async def cleanup(self):
        """清理环境"""
        pass

class BenchmarkAdapter(ABC):
    """Benchmark 适配器基类"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    @abstractmethod
    def get_adapter_info(self) -> AdapterInfo:
        """获取适配器信息"""
        pass

    @abstractmethod
    def create_environment(self, config: Optional[Dict] = None) -> UnifiedEnv:
        """创建执行环境"""
        pass

    @abstractmethod
    async def load_tasks(
        self,
        filter_config: Optional[Dict] = None
    ) -> List[BaseTask]:
        """加载任务列表"""
        pass

    @abstractmethod
    async def evaluate_task(
        self,
        task: BaseTask,
        model_output: str,
        env: UnifiedEnv
    ) -> TaskResult:
        """评估单个任务"""
        pass

    @abstractmethod
    async def cleanup(self):
        """清理资源"""
        pass
```

#### 3.2.3 SWE-bench Adapter 实现

```python
# agenteval/benchmarks/swe_bench_adapter.py

import json
import subprocess
import asyncio
from typing import List, Optional, Dict, Any
from pathlib import Path

from .base import (
    BenchmarkAdapter, BaseTask, TaskResult, UnifiedEnv,
    AdapterInfo, TaskStatus
)

class SWEBenchTask(BaseTask):
    """SWE-bench 任务"""
    instance_id: str
    repo: str
    base_commit: str
    problem_statement: str
    hints_text: str
    patch: str
    test_patch: str

    def __init__(self, data: Dict[str, Any]):
        super().__init__(
            task_id=data['instance_id'],
            task_type='repo_level_fix',
            description=data['problem_statement'],
            metadata=data
        )
        self.instance_id = data['instance_id']
        self.repo = data['repo']
        self.base_commit = data['base_commit']
        self.problem_statement = data['problem_statement']
        self.hints_text = data.get('hints_text', '')
        self.patch = data.get('patch', '')
        self.test_patch = data.get('test_patch', '')

class SWEBenchEnv(UnifiedEnv):
    """SWE-bench Docker 执行环境"""

    def __init__(self, task: SWEBenchTask, config: Dict[str, Any]):
        self.task = task
        self.config = config
        self.container_id = None
        self.timeout = config.get('timeout', 300)

    async def setup(self):
        """设置环境"""
        # 1. 拉取 repo 到指定 commit
        # 2. 启动 Docker 容器
        # 3. 挂载代码目录
        repo_path = await self._clone_repo()
        self.container_id = await self._start_container(repo_path)

    async def _clone_repo(self) -> Path:
        """克隆仓库到指定 commit"""
        cache_dir = Path(self.config.get('cache_dir', '/tmp/swe_bench'))
        cache_dir.mkdir(parents=True, exist_ok=True)

        repo_dir = cache_dir / self.task.repo.replace('/', '_') / self.task.base_commit

        if not repo_dir.exists():
            # 克隆仓库
            cmd = [
                'git', 'clone',
                f'https://github.com/{self.task.repo}.git',
                str(repo_dir)
            ]
            await asyncio.create_subprocess_exec(*cmd)

            # checkout 到指定 commit
            cmd = ['git', '-C', str(repo_dir), 'checkout', self.task.base_commit]
            await asyncio.create_subprocess_exec(*cmd)

        return repo_dir

    async def _start_container(self, repo_path: Path) -> str:
        """启动 Docker 容器"""
        # 使用 SWE-bench 官方镜像
        image = self.config.get('docker_image', 'swe-bench/python:3.9')

        cmd = [
            'docker', 'run', '-d',
            '-v', f'{repo_path}:/workspace',
            '--network', 'none',  # 网络隔离
            '--memory', '4g',
            '--cpus', '2',
            image,
            'tail', '-f', '/dev/null'  # 保持容器运行
        ]

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE
        )
        stdout, _ = await proc.communicate()
        container_id = stdout.decode().strip()

        return container_id

    async def execute(self, code: str, timeout: int = 60) -> Dict[str, Any]:
        """执行代码（应用 patch）"""
        if not self.container_id:
            await self.setup()

        # 1. 将生成的 patch 写入容器
        patch_file = '/workspace/generated.patch'
        cmd = [
            'docker', 'exec', self.container_id,
            'bash', '-c', f'cat > {patch_file} << "EOF"\n{code}\nEOF'
        ]
        await asyncio.create_subprocess_exec(*cmd)

        # 2. 应用 patch
        cmd = [
            'docker', 'exec', self.container_id,
            'git', '-C', '/workspace', 'apply', patch_file
        ]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)

        apply_success = proc.returncode == 0

        # 3. 运行测试
        test_cmd = self.config.get('test_command', 'pytest -xvs')
        cmd = [
            'docker', 'exec', self.container_id,
            'bash', '-c', f'cd /workspace && {test_cmd}'
        ]

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        test_stdout, test_stderr = await asyncio.wait_for(
            proc.communicate(),
            timeout=timeout
        )

        test_passed = proc.returncode == 0

        return {
            'apply_success': apply_success,
            'apply_stdout': stdout.decode(),
            'apply_stderr': stderr.decode(),
            'test_passed': test_passed,
            'test_stdout': test_stdout.decode(),
            'test_stderr': test_stderr.decode()
        }

    async def cleanup(self):
        """清理容器"""
        if self.container_id:
            cmd = ['docker', 'rm', '-f', self.container_id]
            await asyncio.create_subprocess_exec(*cmd)

class SWEBenchAdapter(BenchmarkAdapter):
    """SWE-bench 适配器"""

    def get_adapter_info(self) -> AdapterInfo:
        return AdapterInfo(
            name="swe-bench",
            version="1.0.0",
            description="SWE-bench: Software Engineering Benchmark",
            supported_languages=["python"]
        )

    def create_environment(self, config: Optional[Dict] = None) -> UnifiedEnv:
        """创建环境（延迟到 task 执行时）"""
        # 这里返回 None，实际环境在 evaluate_task 时创建
        return None

    async def load_tasks(
        self,
        filter_config: Optional[Dict] = None
    ) -> List[BaseTask]:
        """加载任务列表"""
        dataset_path = self.config.get('dataset_path', 'data/swe-bench-lite.json')

        with open(dataset_path, 'r') as f:
            data = json.load(f)

        tasks = [SWEBenchTask(item) for item in data]

        # 应用过滤
        if filter_config:
            max_samples = filter_config.get('max_samples')
            if max_samples:
                tasks = tasks[:max_samples]

            languages = filter_config.get('languages')
            if languages:
                # SWE-bench 主要是 Python，这里简化
                pass

        return tasks

    async def evaluate_task(
        self,
        task: BaseTask,
        model_output: str,
        env: UnifiedEnv
    ) -> TaskResult:
        """评估单个任务"""
        import time
        start_time = time.time()

        # 创建任务专属环境
        swe_task = task  # 类型转换
        task_env = SWEBenchEnv(swe_task, self.config)

        try:
            # 执行评估
            result = await task_env.execute(model_output, timeout=300)

            execution_time = time.time() - start_time

            # 判断是否通过
            passed = result['apply_success'] and result['test_passed']
            status = TaskStatus.PASSED if passed else TaskStatus.FAILED

            return TaskResult(
                task_id=task.task_id,
                status=status,
                passed=passed,
                output=result['test_stdout'],
                error_message=result['test_stderr'] if not passed else None,
                execution_time=execution_time,
                metrics={
                    'apply_success': result['apply_success'],
                    'test_passed': result['test_passed']
                }
            )

        except asyncio.TimeoutError:
            return TaskResult(
                task_id=task.task_id,
                status=TaskStatus.TIMEOUT,
                passed=False,
                output="",
                error_message="Execution timeout",
                execution_time=time.time() - start_time
            )

        except Exception as e:
            return TaskResult(
                task_id=task.task_id,
                status=TaskStatus.ERROR,
                passed=False,
                output="",
                error_message=str(e),
                execution_time=time.time() - start_time
            )

        finally:
            await task_env.cleanup()

    async def cleanup(self):
        """清理资源"""
        pass
```

#### 3.2.4 HumanEval Adapter 实现（简化版）

```python
# agenteval/benchmarks/humaneval_adapter.py

import json
import ast
import asyncio
from typing import List, Optional, Dict, Any
from pathlib import Path

from .base import (
    BenchmarkAdapter, BaseTask, TaskResult, UnifiedEnv,
    AdapterInfo, TaskStatus
)

class HumanEvalTask(BaseTask):
    """HumanEval 任务"""
    task_id: str
    prompt: str
    canonical_solution: str
    test: str
    entry_point: str

    def __init__(self, data: Dict[str, Any]):
        super().__init__(
            task_id=data['task_id'],
            task_type='code_generation',
            description=data['prompt'],
            metadata=data
        )
        self.prompt = data['prompt']
        self.canonical_solution = data['canonical_solution']
        self.test = data['test']
        self.entry_point = data['entry_point']

class HumanEvalEnv(UnifiedEnv):
    """HumanEval 执行环境（简化版，使用 subprocess）"""

    def __init__(self, task: HumanEvalTask, config: Dict[str, Any]):
        self.task = task
        self.config = config

    async def execute(self, code: str, timeout: int = 10) -> Dict[str, Any]:
        """执行代码并运行测试"""
        # 组合代码和测试
        full_code = code + "\n\n" + self.task.test + f"\n\ncheck({self.task.entry_point})"

        # 写入临时文件
        temp_file = Path(f"/tmp/humaneval_{self.task.task_id}.py")
        temp_file.write_text(full_code)

        # 执行
        cmd = ['python', str(temp_file)]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)

            # 检查是否通过
            passed = proc.returncode == 0

            return {
                'passed': passed,
                'stdout': stdout.decode(),
                'stderr': stderr.decode()
            }

        except asyncio.TimeoutError:
            proc.kill()
            return {
                'passed': False,
                'stdout': '',
                'stderr': 'Execution timeout'
            }

    async def cleanup(self):
        """清理临时文件"""
        temp_file = Path(f"/tmp/humaneval_{self.task.task_id}.py")
        if temp_file.exists():
            temp_file.unlink()

class HumanEvalAdapter(BenchmarkAdapter):
    """HumanEval 适配器"""

    def get_adapter_info(self) -> AdapterInfo:
        return AdapterInfo(
            name="humaneval",
            version="1.0.0",
            description="HumanEval: Code Generation Benchmark",
            supported_languages=["python"]
        )

    def create_environment(self, config: Optional[Dict] = None) -> UnifiedEnv:
        return None

    async def load_tasks(
        self,
        filter_config: Optional[Dict] = None
    ) -> List[BaseTask]:
        """加载任务列表"""
        dataset_path = self.config.get('dataset_path', 'data/humaneval.jsonl')

        tasks = []
        with open(dataset_path, 'r') as f:
            for line in f:
                data = json.loads(line)
                tasks.append(HumanEvalTask(data))

        # 应用过滤
        if filter_config:
            max_samples = filter_config.get('max_samples')
            if max_samples:
                tasks = tasks[:max_samples]

        return tasks

    async def evaluate_task(
        self,
        task: BaseTask,
        model_output: str,
        env: UnifiedEnv
    ) -> TaskResult:
        """评估单个任务"""
        import time
        start_time = time.time()

        humaneval_task = task
        task_env = HumanEvalEnv(humaneval_task, self.config)

        try:
            result = await task_env.execute(model_output, timeout=10)

            execution_time = time.time() - start_time

            passed = result['passed']
            status = TaskStatus.PASSED if passed else TaskStatus.FAILED

            return TaskResult(
                task_id=task.task_id,
                status=status,
                passed=passed,
                output=result['stdout'],
                error_message=result['stderr'] if not passed else None,
                execution_time=execution_time
            )

        except Exception as e:
            return TaskResult(
                task_id=task.task_id,
                status=TaskStatus.ERROR,
                passed=False,
                output="",
                error_message=str(e),
                execution_time=time.time() - start_time
            )

        finally:
            await task_env.cleanup()

    async def cleanup(self):
        pass
```

#### 3.2.5 Adapter Registry

```python
# agenteval/benchmarks/registry.py

from typing import Dict, Type
from .base import BenchmarkAdapter
from .swe_bench_adapter import SWEBenchAdapter
from .humaneval_adapter import HumanEvalAdapter
# from .intercode_adapter import InterCodeAdapter  # TODO

class BenchmarkAdapterRegistry:
    """Benchmark 适配器注册表"""

    _adapters: Dict[str, Type[BenchmarkAdapter]] = {}

    @classmethod
    def register(cls, name: str, adapter_class: Type[BenchmarkAdapter]):
        """注册适配器"""
        cls._adapters[name] = adapter_class

    @classmethod
    def get_adapter(cls, name: str, config: Dict) -> BenchmarkAdapter:
        """获取适配器实例"""
        if name not in cls._adapters:
            raise ValueError(f"Unknown benchmark adapter: {name}")

        adapter_class = cls._adapters[name]
        return adapter_class(config)

    @classmethod
    def list_adapters(cls) -> Dict[str, Type[BenchmarkAdapter]]:
        """列出所有适配器"""
        return cls._adapters.copy()

# 注册内置适配器
BenchmarkAdapterRegistry.register('swe-bench', SWEBenchAdapter)
BenchmarkAdapterRegistry.register('swe-bench-lite', SWEBenchAdapter)
BenchmarkAdapterRegistry.register('humaneval', HumanEvalAdapter)
# BenchmarkAdapterRegistry.register('intercode', InterCodeAdapter)  # TODO
```

---

### 3.3 Metrics Engine

#### 3.3.1 设计目标

- 计算多维度评估指标
- 支持自定义指标插件
- 高效的批量计算

#### 3.3.2 实现

```python
# agenteval/metrics/engine.py

from typing import List, Dict, Any, Callable
from dataclasses import dataclass
from ..benchmarks.base import TaskResult

@dataclass
class MetricResult:
    """指标结果"""
    name: str
    value: float
    category: str  # basic, quality, operational
    unit: str = ""

class MetricsEngine:
    """指标计算引擎"""

    def __init__(self):
        self._custom_metrics: Dict[str, Callable] = {}

    def register_metric(self, name: str, func: Callable):
        """注册自定义指标"""
        self._custom_metrics[name] = func

    def compute_basic_metrics(self, results: List[TaskResult]) -> List[MetricResult]:
        """计算基础指标"""
        total = len(results)
        passed = sum(1 for r in results if r.passed)
        failed = sum(1 for r in results if not r.passed and r.status.value != 'error')
        errors = sum(1 for r in results if r.status.value == 'error')
        timeouts = sum(1 for r in results if r.status.value == 'timeout')

        return [
            MetricResult(name="total_tasks", value=total, category="basic", unit="count"),
            MetricResult(name="passed_tasks", value=passed, category="basic", unit="count"),
            MetricResult(name="failed_tasks", value=failed, category="basic", unit="count"),
            MetricResult(name="error_tasks", value=errors, category="basic", unit="count"),
            MetricResult(name="timeout_tasks", value=timeouts, category="basic", unit="count"),
            MetricResult(name="pass_rate", value=passed / total if total > 0 else 0, category="basic", unit="%"),
            MetricResult(name="error_rate", value=errors / total if total > 0 else 0, category="basic", unit="%"),
        ]

    def compute_operational_metrics(self, results: List[TaskResult]) -> List[MetricResult]:
        """计算运营指标"""
        execution_times = [r.execution_time for r in results if r.execution_time]

        if not execution_times:
            return []

        avg_time = sum(execution_times) / len(execution_times)
        sorted_times = sorted(execution_times)
        p50_time = sorted_times[len(sorted_times) // 2]
        p95_time = sorted_times[int(len(sorted_times) * 0.95)]
        p99_time = sorted_times[int(len(sorted_times) * 0.99)]

        return [
            MetricResult(name="avg_execution_time", value=avg_time, category="operational", unit="s"),
            MetricResult(name="p50_execution_time", value=p50_time, category="operational", unit="s"),
            MetricResult(name="p95_execution_time", value=p95_time, category="operational", unit="s"),
            MetricResult(name="p99_execution_time", value=p99_time, category="operational", unit="s"),
        ]

    def compute_all_metrics(self, results: List[TaskResult]) -> Dict[str, Any]:
        """计算所有指标"""
        metrics = {}

        # 基础指标
        basic_metrics = self.compute_basic_metrics(results)
        metrics['basic'] = {m.name: m.value for m in basic_metrics}

        # 运营指标
        operational_metrics = self.compute_operational_metrics(results)
        metrics['operational'] = {m.name: m.value for m in operational_metrics}

        # 自定义指标
        if self._custom_metrics:
            custom_results = {}
            for name, func in self._custom_metrics.items():
                try:
                    custom_results[name] = func(results)
                except Exception as e:
                    custom_results[name] = f"Error: {str(e)}"
            metrics['custom'] = custom_results

        return metrics
```

---

### 3.4 Batch Orchestrator

#### 3.4.1 设计目标

- 并发执行多个评估任务
- 进度追踪与实时反馈
- 错误处理与重试
- 资源控制（限制并发数）

#### 3.4.2 实现

```python
# agenteval/orchestrator/batch.py

import asyncio
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import time
from tqdm.asyncio import tqdm

from ..models.factory import ModelAdapterFactory
from ..benchmarks.registry import BenchmarkAdapterRegistry
from ..benchmarks.base import BaseTask, TaskResult, TaskStatus
from ..metrics.engine import MetricsEngine

@dataclass
class EvaluationConfig:
    """评估配置"""
    name: str
    model_name: str
    benchmark_name: str
    max_concurrent: int = 5
    timeout: int = 300
    filter_config: Optional[Dict] = None
    retry_on_error: bool = True
    max_retries: int = 3

@dataclass
class EvaluationResult:
    """评估结果"""
    config: EvaluationConfig
    task_results: List[TaskResult]
    metrics: Dict[str, Any]
    total_time: float
    start_time: float
    end_time: float

class BatchOrchestrator:
    """批量评估编排器"""

    def __init__(self):
        self.model_factory = ModelAdapterFactory()
        self.metrics_engine = MetricsEngine()

    async def run_evaluation(
        self,
        config: EvaluationConfig
    ) -> EvaluationResult:
        """运行评估"""
        start_time = time.time()

        # 1. 加载模型适配器
        model_adapter = self.model_factory.get_adapter(config.model_name)

        # 2. 加载 Benchmark 适配器
        benchmark_adapter = BenchmarkAdapterRegistry.get_adapter(
            config.benchmark_name,
            {}  # TODO: 从配置加载
        )

        # 3. 加载任务列表
        tasks = await benchmark_adapter.load_tasks(config.filter_config)
        print(f"Loaded {len(tasks)} tasks")

        # 4. 并发执行任务
        task_results = await self._execute_tasks_concurrent(
            tasks=tasks,
            model_adapter=model_adapter,
            benchmark_adapter=benchmark_adapter,
            max_concurrent=config.max_concurrent,
            timeout=config.timeout
        )

        # 5. 计算指标
        metrics = self.metrics_engine.compute_all_metrics(task_results)

        end_time = time.time()

        return EvaluationResult(
            config=config,
            task_results=task_results,
            metrics=metrics,
            total_time=end_time - start_time,
            start_time=start_time,
            end_time=end_time
        )

    async def _execute_tasks_concurrent(
        self,
        tasks: List[BaseTask],
        model_adapter,
        benchmark_adapter,
        max_concurrent: int,
        timeout: int
    ) -> List[TaskResult]:
        """并发执行任务"""
        semaphore = asyncio.Semaphore(max_concurrent)

        async def execute_single_task(task: BaseTask) -> TaskResult:
            async with semaphore:
                return await self._execute_single_task(
                    task, model_adapter, benchmark_adapter, timeout
                )

        # 使用 tqdm 显示进度
        task_results = []
        for coro in tqdm.as_completed(
            [execute_single_task(task) for task in tasks],
            total=len(tasks),
            desc="Evaluating"
        ):
            result = await coro
            task_results.append(result)

        return task_results

    async def _execute_single_task(
        self,
        task: BaseTask,
        model_adapter,
        benchmark_adapter,
        timeout: int
    ) -> TaskResult:
        """执行单个任务"""
        try:
            # 1. 调用模型生成代码
            from ..models.base import Message
            messages = [Message(role="user", content=task.description)]

            response = await asyncio.wait_for(
                model_adapter.generate(messages),
                timeout=timeout
            )

            model_output = response.content

            # 2. 执行评估
            result = await benchmark_adapter.evaluate_task(
                task=task,
                model_output=model_output,
                env=None
            )

            return result

        except asyncio.TimeoutError:
            return TaskResult(
                task_id=task.task_id,
                status=TaskStatus.TIMEOUT,
                passed=False,
                output="",
                error_message="Task execution timeout"
            )

        except Exception as e:
            return TaskResult(
                task_id=task.task_id,
                status=TaskStatus.ERROR,
                passed=False,
                output="",
                error_message=str(e)
            )
```

---

### 3.5 Export Engine

#### 3.5.1 HTML 报告生成

```python
# agenteval/export/html_exporter.py

from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from typing import Dict, Any
from ..orchestrator.batch import EvaluationResult

class HTMLExporter:
    """HTML 报告导出器"""

    def __init__(self, template_dir: str = "templates"):
        self.env = Environment(loader=FileSystemLoader(template_dir))

    def export(self, result: EvaluationResult, output_path: str):
        """导出 HTML 报告"""
        template = self.env.get_template('evaluation_report.html')

        # 准备模板数据
        data = {
            'evaluation_name': result.config.name,
            'model_name': result.config.model_name,
            'benchmark_name': result.config.benchmark_name,
            'total_time': f"{result.total_time:.2f}s",
            'metrics': result.metrics,
            'task_results': result.task_results,
            # 添加图表数据
            'pass_rate_chart': self._generate_pass_rate_chart_data(result),
            'execution_time_chart': self._generate_execution_time_chart_data(result)
        }

        html_content = template.render(**data)

        Path(output_path).write_text(html_content)
        print(f"HTML report exported to: {output_path}")

    def _generate_pass_rate_chart_data(self, result: EvaluationResult) -> Dict:
        """生成通过率图表数据（ECharts 格式）"""
        basic_metrics = result.metrics['basic']

        return {
            'series': [
                {
                    'name': 'Pass Rate',
                    'type': 'pie',
                    'data': [
                        {'value': basic_metrics['passed_tasks'], 'name': 'Passed'},
                        {'value': basic_metrics['failed_tasks'], 'name': 'Failed'},
                        {'value': basic_metrics['error_tasks'], 'name': 'Error'},
                        {'value': basic_metrics['timeout_tasks'], 'name': 'Timeout'},
                    ]
                }
            ]
        }

    def _generate_execution_time_chart_data(self, result: EvaluationResult) -> Dict:
        """生成执行时间分布图表数据"""
        execution_times = [
            r.execution_time for r in result.task_results
            if r.execution_time is not None
        ]

        # 简化：直接返回数据，前端用 ECharts 渲染
        return {
            'data': execution_times
        }
```

#### 3.5.2 HTML 模板

```html
<!-- templates/evaluation_report.html -->
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{{ evaluation_name }} - Evaluation Report</title>
    <script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }
        .header {
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        .metric-card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }
        .metric-value {
            font-size: 32px;
            font-weight: bold;
            color: #1890ff;
        }
        .metric-name {
            font-size: 14px;
            color: #666;
            margin-top: 8px;
        }
        .chart-container {
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        #passRateChart, #executionTimeChart {
            width: 100%;
            height: 400px;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>{{ evaluation_name }}</h1>
        <p><strong>Model:</strong> {{ model_name }}</p>
        <p><strong>Benchmark:</strong> {{ benchmark_name }}</p>
        <p><strong>Total Time:</strong> {{ total_time }}</p>
    </div>

    <div class="metrics-grid">
        <div class="metric-card">
            <div class="metric-value">{{ metrics.basic.total_tasks }}</div>
            <div class="metric-name">Total Tasks</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">{{ metrics.basic.passed_tasks }}</div>
            <div class="metric-name">Passed</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">{{ "%.1f"|format(metrics.basic.pass_rate * 100) }}%</div>
            <div class="metric-name">Pass Rate</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">{{ "%.2f"|format(metrics.operational.avg_execution_time) }}s</div>
            <div class="metric-name">Avg Time</div>
        </div>
    </div>

    <div class="chart-container">
        <h2>Pass Rate Distribution</h2>
        <div id="passRateChart"></div>
    </div>

    <div class="chart-container">
        <h2>Execution Time Distribution</h2>
        <div id="executionTimeChart"></div>
    </div>

    <script>
        // Pass Rate Chart
        var passRateChart = echarts.init(document.getElementById('passRateChart'));
        passRateChart.setOption({
            tooltip: {trigger: 'item'},
            series: {{ pass_rate_chart.series | tojson }}
        });

        // Execution Time Chart
        var executionTimeChart = echarts.init(document.getElementById('executionTimeChart'));
        executionTimeChart.setOption({
            tooltip: {trigger: 'axis'},
            xAxis: {type: 'category'},
            yAxis: {type: 'value', name: 'Time (s)'},
            series: [{
                data: {{ execution_time_chart.data | tojson }},
                type: 'bar'
            }]
        });
    </script>
</body>
</html>
```

---

## 4. 数据模型

### 4.1 本地存储（SQLite）

```sql
-- evaluations 表
CREATE TABLE evaluations (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    model_name TEXT NOT NULL,
    benchmark_name TEXT NOT NULL,
    config_json TEXT,
    status TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);

-- tasks 表
CREATE TABLE tasks (
    id TEXT PRIMARY KEY,
    evaluation_id TEXT NOT NULL,
    task_id TEXT NOT NULL,
    task_type TEXT,
    status TEXT,
    passed BOOLEAN,
    output TEXT,
    error_message TEXT,
    execution_time REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (evaluation_id) REFERENCES evaluations(id)
);

-- metrics 表
CREATE TABLE metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    evaluation_id TEXT NOT NULL,
    metric_name TEXT NOT NULL,
    metric_value REAL,
    category TEXT,
    FOREIGN KEY (evaluation_id) REFERENCES evaluations(id)
);
```

---

## 5. 配置系统

### 5.1 评估配置文件

```yaml
# config/evaluations/swe_bench_claude.yaml

name: "SWE-bench Lite - Claude 3 Opus"
description: "Evaluate Claude 3 Opus on SWE-bench Lite"

model:
  name: claude-3-opus
  temperature: 0.0  # 确保可复现性
  max_tokens: 4096

benchmark:
  name: swe-bench-lite
  dataset_path: data/swe-bench-lite.json
  filter:
    max_samples: 100  # 仅运行前 100 个样本
    # languages: [python]  # 可选

execution:
  max_concurrent: 5
  timeout: 300  # 每个任务超时时间（秒）
  retry_on_error: true
  max_retries: 2

environment:
  docker_image: "swe-bench/python:3.9"
  cache_dir: "/tmp/swe_bench"
  test_command: "pytest -xvs"

output:
  export_formats: [html, csv, json]
  output_dir: "results/swe_bench_claude"
  save_individual_results: true
```

### 5.2 模型配置（参考前文 `config/models.yaml`）

---

## 6. 代码框架

### 6.1 项目目录结构

```
agenteval/
├── README.md
├── pyproject.toml
├── setup.py
├── requirements.txt
├── .env.example
├── .gitignore
│
├── agenteval/               # 主包
│   ├── __init__.py
│   ├── __version__.py
│   │
│   ├── cli/                 # CLI 工具
│   │   ├── __init__.py
│   │   ├── main.py          # 主入口
│   │   ├── run.py           # run 命令
│   │   ├── list.py          # list 命令
│   │   └── report.py        # report 命令
│   │
│   ├── models/              # 模型适配器
│   │   ├── __init__.py
│   │   ├── base.py          # 基类与接口
│   │   ├── factory.py       # 工厂类
│   │   └── litellm_adapter.py
│   │
│   ├── benchmarks/          # Benchmark 适配器
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── registry.py
│   │   ├── swe_bench_adapter.py
│   │   ├── humaneval_adapter.py
│   │   └── intercode_adapter.py  # TODO
│   │
│   ├── orchestrator/        # 编排器
│   │   ├── __init__.py
│   │   └── batch.py
│   │
│   ├── metrics/             # 指标计算
│   │   ├── __init__.py
│   │   └── engine.py
│   │
│   ├── export/              # 导出引擎
│   │   ├── __init__.py
│   │   ├── html_exporter.py
│   │   ├── csv_exporter.py
│   │   └── pdf_exporter.py  # TODO
│   │
│   ├── storage/             # 数据存储
│   │   ├── __init__.py
│   │   └── sqlite_storage.py
│   │
│   └── utils/               # 工具函数
│       ├── __init__.py
│       ├── config_loader.py
│       └── logger.py
│
├── config/                  # 配置文件
│   ├── models.yaml
│   └── evaluations/
│       ├── swe_bench_claude.yaml
│       ├── humaneval_gpt4.yaml
│       └── ...
│
├── templates/               # HTML 模板
│   └── evaluation_report.html
│
├── data/                    # 数据集（.gitignore）
│   ├── swe-bench-lite.json
│   ├── humaneval.jsonl
│   └── ...
│
├── results/                 # 结果输出（.gitignore）
│   └── ...
│
└── tests/                   # 测试代码
    ├── __init__.py
    ├── test_models/
    ├── test_benchmarks/
    ├── test_orchestrator/
    └── test_metrics/
```

### 6.2 CLI 入口

```python
# agenteval/cli/main.py

import click
from .run import run_command
from .list import list_command
from .report import report_command

@click.group()
@click.version_option()
def cli():
    """AgentEval - Agent Evaluation System"""
    pass

cli.add_command(run_command, name='run')
cli.add_command(list_command, name='list')
cli.add_command(report_command, name='report')

if __name__ == '__main__':
    cli()
```

```python
# agenteval/cli/run.py

import click
import asyncio
from pathlib import Path
import yaml

from ..orchestrator.batch import BatchOrchestrator, EvaluationConfig
from ..export.html_exporter import HTMLExporter

@click.command()
@click.argument('config_file', type=click.Path(exists=True))
@click.option('--output-dir', '-o', default='results', help='Output directory')
def run_command(config_file, output_dir):
    """Run evaluation from config file"""
    # 加载配置
    with open(config_file, 'r') as f:
        config_dict = yaml.safe_load(f)

    # 创建 EvaluationConfig
    eval_config = EvaluationConfig(
        name=config_dict['name'],
        model_name=config_dict['model']['name'],
        benchmark_name=config_dict['benchmark']['name'],
        max_concurrent=config_dict['execution'].get('max_concurrent', 5),
        timeout=config_dict['execution'].get('timeout', 300),
        filter_config=config_dict['benchmark'].get('filter')
    )

    # 运行评估
    orchestrator = BatchOrchestrator()
    result = asyncio.run(orchestrator.run_evaluation(eval_config))

    # 导出报告
    output_path = Path(output_dir) / f"{eval_config.name}.html"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    exporter = HTMLExporter()
    exporter.export(result, str(output_path))

    click.echo(f"✅ Evaluation completed!")
    click.echo(f"📊 Report: {output_path}")
    click.echo(f"📈 Pass Rate: {result.metrics['basic']['pass_rate'] * 100:.1f}%")
```

---

## 7. 详细任务分解

### Week 1: 基础框架搭建 + Model Adapter Factory

#### Day 1-2: 项目初始化

**任务：**
- ✅ 创建项目目录结构
- ✅ 配置 `pyproject.toml` 和依赖管理（Poetry）
- ✅ 配置 CI/CD（GitHub Actions）
- ✅ 配置代码质量工具（Black、Ruff、mypy）

**产出：**
- 可运行的项目骨架
- CI 自动检查代码质量

**示例 `pyproject.toml`：**

```toml
[tool.poetry]
name = "agenteval"
version = "0.1.0"
description = "Agent Evaluation System - Offline Engine"
authors = ["EE Team"]

[tool.poetry.dependencies]
python = "^3.10"
litellm = "^1.0.0"
click = "^8.0.0"
pyyaml = "^6.0"
jinja2 = "^3.1.0"
pandas = "^2.0.0"
tqdm = "^4.65.0"
asyncio = "*"

[tool.poetry.dev-dependencies]
pytest = "^7.0.0"
pytest-asyncio = "^0.21.0"
pytest-cov = "^4.0.0"
black = "^23.0.0"
ruff = "^0.1.0"
mypy = "^1.0.0"

[tool.poetry.scripts]
agenteval = "agenteval.cli.main:cli"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
```

#### Day 3-4: Model Adapter Factory 实现

**任务：**
- ✅ 实现 `ModelAdapter` 基类
- ✅ 实现 `LiteLLMAdapter`
- ✅ 实现 `ModelAdapterFactory`
- ✅ 编写配置文件 `config/models.yaml`
- ✅ 编写单元测试

**测试用例：**

```python
# tests/test_models/test_litellm_adapter.py

import pytest
from agenteval.models.factory import ModelAdapterFactory
from agenteval.models.base import Message

@pytest.mark.asyncio
async def test_litellm_adapter_generate():
    factory = ModelAdapterFactory('config/models.yaml')
    adapter = factory.get_adapter('claude-3-opus')

    messages = [Message(role="user", content="Write a Python function to add two numbers")]
    response = await adapter.generate(messages, temperature=0.0)

    assert response.content is not None
    assert len(response.content) > 0
    assert response.usage is not None
    assert response.cost is not None
```

#### Day 5: 配置系统

**任务：**
- ✅ 实现配置加载器 `ConfigLoader`
- ✅ 支持环境变量替换（`${ENV_VAR}`）
- ✅ 配置校验（JSON Schema）

### Week 2: Model Adapter 完善与测试

#### Day 6-8: 多模型适配

**任务：**
- ✅ 添加 10+ 模型配置
- ✅ 测试每个模型的连通性
- ✅ 处理各模型的特殊情况（token 限制、API 格式差异）

**模型清单：**
1. Claude 3 Opus / Sonnet / Haiku
2. GPT-4 Turbo / GPT-4o / GPT-3.5-turbo
3. Qwen-Max / Qwen-Plus
4. DeepSeek-Chat / DeepSeek-Coder
5. Gemini Pro

#### Day 9-10: 错误处理与重试

**任务：**
- ✅ 实现重试机制（指数退避）
- ✅ 实现降级策略（主模型失败后使用备用模型）
- ✅ 编写异常测试用例

### Week 3-4: Benchmark Adapters 实现

#### Week 3: SWE-bench Adapter

**Day 11-13: SWE-bench 基础实现**

**任务：**
- ✅ 实现 `SWEBenchAdapter`
- ✅ 实现 `SWEBenchEnv`（Docker 隔离）
- ✅ 实现 Git 仓库克隆与管理
- ✅ 实现 Patch 应用与测试执行

**Day 14-15: SWE-bench 测试与优化**

**任务：**
- ✅ 在 1 个样本上测试完整流程
- ✅ 优化 Docker 容器管理（复用、清理）
- ✅ 处理 timeout 与资源限制

#### Week 4: HumanEval + InterCode Adapters

**Day 16-18: HumanEval Adapter**

**任务：**
- ✅ 实现 `HumanEvalAdapter`
- ✅ 实现代码执行与测试
- ✅ 在完整数据集上测试

**Day 19-20: InterCode Adapter（可选）**

**任务：**
- ✅ 实现 `InterCodeAdapter` (Bash 场景)
- ✅ 实现交互式执行
- ✅ 测试

### Week 5: Metrics Engine + Batch Orchestrator

#### Day 21-22: Metrics Engine

**任务：**
- ✅ 实现基础指标计算
- ✅ 实现运营指标计算
- ✅ 支持自定义指标插件
- ✅ 编写单元测试

#### Day 23-25: Batch Orchestrator

**任务：**
- ✅ 实现 `BatchOrchestrator`
- ✅ 实现并发任务调度（asyncio + Semaphore）
- ✅ 实现进度追踪（tqdm）
- ✅ 实现结果聚合

**测试：**
- 5 个并发任务测试
- 超时处理测试
- 错误恢复测试

### Week 6: Export Engine + CLI

#### Day 26-27: Export Engine

**任务：**
- ✅ 实现 HTML 报告生成（Jinja2 + ECharts）
- ✅ 实现 CSV 导出（Pandas）
- ✅ 设计美观的报告模板

#### Day 28-30: CLI 工具

**任务：**
- ✅ 实现 `agenteval run` 命令
- ✅ 实现 `agenteval list` 命令（列出模型、Benchmark）
- ✅ 实现 `agenteval report` 命令（查看历史报告）
- ✅ 编写 CLI 使用文档

### Week 7: 集成测试 + 文档 + Baseline 评估

#### Day 31-32: 端到端集成测试

**任务：**
- ✅ SWE-bench Lite + Claude 3 Opus（100 样本）
- ✅ HumanEval + GPT-4（全量）
- ✅ 对比多个模型

#### Day 33-34: 文档编写

**任务：**
- ✅ 用户手册（安装、使用、配置）
- ✅ API 文档（自动生成）
- ✅ 开发文档（如何添加模型、Benchmark）

#### Day 35: Baseline 评估与发布

**任务：**
- ✅ 运行多模型 Baseline 评估
- ✅ 生成对比报告
- ✅ 发布 v0.1.0

---

## 8. 测试策略

### 8.1 测试层级

#### 单元测试（Unit Tests）

**覆盖范围：**
- 所有核心类的公共方法
- 边界条件与异常处理

**工具：** pytest + pytest-cov

**目标：** 覆盖率 > 80%

**示例：**

```python
# tests/test_models/test_factory.py

def test_factory_get_adapter():
    factory = ModelAdapterFactory()
    adapter = factory.get_adapter('claude-3-opus')
    assert adapter is not None

def test_factory_unknown_model():
    factory = ModelAdapterFactory()
    with pytest.raises(ValueError):
        factory.get_adapter('unknown-model')
```

#### 集成测试（Integration Tests）

**覆盖范围：**
- Model Adapter + Benchmark Adapter 集成
- 完整的评估流程

**示例：**

```python
# tests/integration/test_evaluation_pipeline.py

@pytest.mark.asyncio
async def test_humaneval_pipeline():
    config = EvaluationConfig(
        name="Test HumanEval",
        model_name="claude-3-opus",
        benchmark_name="humaneval",
        max_concurrent=2,
        filter_config={'max_samples': 5}
    )

    orchestrator = BatchOrchestrator()
    result = await orchestrator.run_evaluation(config)

    assert len(result.task_results) == 5
    assert result.metrics['basic']['total_tasks'] == 5
```

#### 端到端测试（E2E Tests）

**覆盖范围：**
- CLI 命令执行
- 报告生成

**示例：**

```bash
# tests/e2e/test_cli.sh

#!/bin/bash
set -e

# 运行评估
agenteval run config/evaluations/test_humaneval.yaml

# 检查报告文件
if [ ! -f "results/Test HumanEval.html" ]; then
    echo "Report not found"
    exit 1
fi

echo "E2E test passed"
```

### 8.2 性能测试

**目标：**
- 评估吞吐量 > 100 tasks/hour
- 并发 5 任务无异常

**工具：** pytest-benchmark

```python
# tests/performance/test_throughput.py

def test_evaluation_throughput(benchmark):
    def run_evaluation():
        config = EvaluationConfig(...)
        orchestrator = BatchOrchestrator()
        result = asyncio.run(orchestrator.run_evaluation(config))

    result = benchmark(run_evaluation)
    assert result.stats.mean < 36  # 100 tasks/hour = 36s/task
```

### 8.3 CI/CD 配置

```yaml
# .github/workflows/ci.yml

name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          pip install poetry
          poetry install

      - name: Run linters
        run: |
          poetry run black --check .
          poetry run ruff check .
          poetry run mypy agenteval

      - name: Run tests
        run: |
          poetry run pytest --cov=agenteval --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

---

## 9. 开发规范

### 9.1 代码风格

- **格式化：** Black（行宽 100）
- **Linter：** Ruff
- **类型检查：** mypy（严格模式）

### 9.2 命名规范

- **类名：** PascalCase（`ModelAdapter`）
- **函数名：** snake_case（`get_adapter`）
- **常量：** UPPER_SNAKE_CASE（`MAX_RETRIES`）
- **私有方法：** 前缀 `_`（`_load_config`）

### 9.3 文档字符串

```python
def evaluate_task(self, task: BaseTask, model_output: str) -> TaskResult:
    """评估单个任务

    Args:
        task: 任务对象
        model_output: 模型生成的输出

    Returns:
        TaskResult: 评估结果

    Raises:
        TimeoutError: 执行超时
        EvaluationError: 评估失败
    """
    pass
```

### 9.4 Git 提交规范

```
feat: Add SWE-bench adapter
fix: Fix timeout handling in orchestrator
docs: Update README with installation guide
test: Add unit tests for metrics engine
refactor: Extract common code in adapters
perf: Optimize Docker container reuse
```

---

## 10. 部署与运行

### 10.1 安装

```bash
# 克隆仓库
git clone https://github.com/your-org/AgentEval.git
cd AgentEval

# 安装依赖
pip install poetry
poetry install

# 配置环境变量
cp .env.example .env
# 编辑 .env 填入 API Keys
```

### 10.2 运行评估

```bash
# 运行单个评估
agenteval run config/evaluations/swe_bench_claude.yaml

# 查看可用模型
agenteval list models

# 查看可用 Benchmark
agenteval list benchmarks

# 查看历史报告
agenteval report --list
```

### 10.3 Docker 部署（可选）

```dockerfile
# Dockerfile

FROM python:3.10-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y git docker.io

# 安装 Python 依赖
COPY pyproject.toml poetry.lock ./
RUN pip install poetry && poetry install --no-dev

# 复制代码
COPY . .

ENTRYPOINT ["poetry", "run", "agenteval"]
```

```bash
# 构建镜像
docker build -t agenteval:latest .

# 运行
docker run -v $(pwd)/config:/app/config \
           -v $(pwd)/results:/app/results \
           -v /var/run/docker.sock:/var/run/docker.sock \
           --env-file .env \
           agenteval:latest run config/evaluations/test.yaml
```

---

## 附录

### A. 依赖清单

| 依赖 | 版本 | 用途 |
|------|------|------|
| litellm | ^1.0.0 | 统一 LLM 接口 |
| click | ^8.0.0 | CLI 框架 |
| pyyaml | ^6.0 | YAML 配置解析 |
| jinja2 | ^3.1.0 | HTML 模板 |
| pandas | ^2.0.0 | 数据处理与导出 |
| tqdm | ^4.65.0 | 进度条 |
| asyncio | * | 异步编程 |
| pytest | ^7.0.0 | 测试框架 |
| docker | ^6.0.0 | Docker 操作 |

### B. 参考资源

- [LiteLLM Documentation](https://docs.litellm.ai/)
- [SWE-bench GitHub](https://github.com/princeton-nlp/SWE-bench)
- [HumanEval Paper](https://arxiv.org/abs/2107.03374)
- [InterCode GitHub](https://github.com/princeton-nlp/intercode)

---

**文档结束**

**下一步：** 开始 Week 1 Day 1 任务 - 项目初始化
