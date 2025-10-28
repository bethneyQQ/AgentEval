# Agent Evaluation System - 可扩展性指南

**版本**: 1.0
**日期**: 2025-01-28
**目标读者**: 开发者、架构师

---

## 📖 概述

本文档详细介绍了 Agent Evaluation System 的四个核心扩展点：

1. **添加新的 LLM 支持**
2. **集成新的 Benchmark**
3. **开发自定义插件**
4. **添加新的告警通道**

每个扩展点都采用**配置优先、代码最小化**的设计原则。

---

## 🤖 1. 添加新 LLM 支持

### 1.1 基于 LiteLLM（推荐，0 代码）

如果模型已被 LiteLLM 支持（参考 [LiteLLM Providers](https://docs.litellm.ai/docs/providers)），只需添加配置。

#### 步骤 1：编辑 `config/models.yaml`

```yaml
models:
  # 示例：添加 DeepSeek Coder
  deepseek-coder:
    provider: deepseek
    litellm_name: deepseek/deepseek-coder
    adapter_type: litellm  # 使用 LiteLLMAdapter

    capabilities:
      supports_streaming: true
      supports_system_message: true
      supports_function_calling: true
      supports_vision: false
      max_input_tokens: 64000
      max_output_tokens: 4096

    pricing:
      input_per_1m: 0.14
      output_per_1m: 0.28

    api_config:
      api_key_env: DEEPSEEK_API_KEY  # 从环境变量读取
      api_base_env: DEEPSEEK_API_BASE  # 可选，支持自定义 base URL
      timeout: 60
```

#### 步骤 2：设置环境变量

```bash
export DEEPSEEK_API_KEY="your-api-key"
```

#### 步骤 3：验证

```bash
# 测试模型连接
python -m core.model_adapters.cli test deepseek-coder

# 运行简单评估
python -m cli.batch_evaluator \
  --model deepseek-coder \
  --task humaneval:0 \
  --output test_output.json
```

#### 完成！无需编写任何代码。

---

### 1.2 不支持的模型（需要自定义 Adapter）

如果模型不在 LiteLLM 支持列表，需要实现自定义 Adapter。

#### 步骤 1：创建 Adapter 类

```python
# core/model_adapters/custom/my_model_adapter.py

from core.model_adapters.base import UnifiedModelAdapter
from core.model_adapters.models import ModelResponse, ModelChunk, ModelCapabilities
from typing import List, AsyncGenerator

class MyModelAdapter(UnifiedModelAdapter):
    """自定义模型适配器示例"""

    def __init__(self, model_name: str, config: Dict):
        self.model_name = model_name
        self.api_key = os.getenv(config.get('api_key_env'))
        self.api_base = os.getenv(config.get('api_base_env', ''),
                                  'https://api.mymodel.com/v1')
        self.client = MyModelClient(api_key=self.api_key, base_url=self.api_base)

    async def generate(
        self,
        messages: List[Message],
        tools: Optional[List[ToolDefinition]] = None,
        **kwargs
    ) -> ModelResponse:
        """同步生成"""
        # 调用模型 API
        response = await self.client.chat.completions.create(
            model=self.model_name,
            messages=[m.dict() for m in messages],
            **kwargs
        )

        # 转换为标准格式
        return ModelResponse(
            content=response.choices[0].message.content,
            finish_reason=response.choices[0].finish_reason,
            prompt_tokens=response.usage.prompt_tokens,
            completion_tokens=response.usage.completion_tokens,
            total_tokens=response.usage.total_tokens,
            cost_usd=self.estimate_cost(
                response.usage.prompt_tokens,
                response.usage.completion_tokens
            ),
            model=self.model_name,
            latency_ms=(response.created - request_start_time) * 1000
        )

    async def stream_generate(
        self,
        messages: List[Message],
        tools: Optional[List[ToolDefinition]] = None,
        **kwargs
    ) -> AsyncGenerator[ModelChunk, None]:
        """流式生成"""
        async for chunk in await self.client.chat.completions.create(
            model=self.model_name,
            messages=[m.dict() for m in messages],
            stream=True,
            **kwargs
        ):
            if chunk.choices[0].delta.content:
                yield ModelChunk(
                    delta=chunk.choices[0].delta.content,
                    finish_reason=chunk.choices[0].finish_reason
                )

    def get_capabilities(self) -> ModelCapabilities:
        """返回模型能力"""
        return ModelCapabilities(
            supports_streaming=True,
            supports_function_calling=True,
            max_input_tokens=32000,
            max_output_tokens=4096,
            input_price_per_1m=1.0,
            output_price_per_1m=3.0
        )

    def count_tokens(self, messages: List[Message]) -> int:
        """Token 计数"""
        # 使用 tiktoken 或模型自带的计数器
        import tiktoken
        enc = tiktoken.get_encoding("cl100k_base")

        total = 0
        for msg in messages:
            total += len(enc.encode(msg.content))
        return total

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """成本估算"""
        caps = self.get_capabilities()
        return (
            input_tokens / 1_000_000 * caps.input_price_per_1m +
            output_tokens / 1_000_000 * caps.output_price_per_1m
        )
```

#### 步骤 2：注册 Adapter

```yaml
# config/models.yaml
models:
  my-custom-model:
    provider: custom
    adapter_type: custom  # 使用自定义 Adapter
    adapter_class: core.model_adapters.custom.my_model_adapter.MyModelAdapter

    capabilities:
      supports_function_calling: true
      max_input_tokens: 32000

    pricing:
      input_per_1m: 1.0
      output_per_1m: 3.0

    api_config:
      api_key_env: MY_MODEL_API_KEY
      api_base_env: MY_MODEL_API_BASE
```

#### 步骤 3：在 AdapterFactory 注册

```python
# core/model_adapters/registry.py

class ModelRegistry:
    def get_adapter(self, model_name: str) -> UnifiedModelAdapter:
        config = self.models[model_name]
        adapter_type = config.get('adapter_type')

        if adapter_type == 'litellm':
            return LiteLLMAdapter(...)
        elif adapter_type == 'react':
            return ReActAdapter(...)
        elif adapter_type == 'custom':
            # 动态导入自定义 Adapter
            adapter_class_path = config['adapter_class']
            module_path, class_name = adapter_class_path.rsplit('.', 1)
            module = importlib.import_module(module_path)
            AdapterClass = getattr(module, class_name)
            return AdapterClass(model_name, config)
        else:
            raise ValueError(f"Unknown adapter type: {adapter_type}")
```

---

## 🧪 2. 集成新 Benchmark

### 2.1 实现 BenchmarkAdapter

所有 Benchmark 必须实现 `BenchmarkAdapter` 接口。

#### 步骤 1：创建 Adapter 类

```python
# core/benchmark_adapters/my_benchmark_adapter.py

from core.adapters import BenchmarkAdapter, AdapterInfo
from core.environment import UnifiedEnv
from core.task_types import BaseTask, SingleTurnTask, TaskResult
from typing import List, Dict

class MyBenchmarkAdapter(BenchmarkAdapter):
    """自定义 Benchmark 适配器"""

    def get_adapter_info(self) -> AdapterInfo:
        return AdapterInfo(
            name="my_benchmark",
            version="1.0.0",
            description="My custom benchmark for XYZ tasks",
            supported_task_types=["single_turn"],
            required_capabilities=["code_execution"]
        )

    def initialize(self) -> bool:
        """初始化（下载数据集、检查依赖等）"""
        try:
            # 下载数据集
            self._download_dataset()
            # 检查依赖
            self._check_dependencies()
            return True
        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            return False

    def create_environment(self, task_config: Dict) -> UnifiedEnv:
        """创建执行环境"""
        return MyBenchmarkEnvironment(task_config)

    def load_tasks(self, task_filter: Dict = None) -> List[BaseTask]:
        """加载任务"""
        # 从数据集加载
        dataset = self._load_dataset()

        # 过滤
        if task_filter:
            dataset = self._apply_filter(dataset, task_filter)

        # 转换为 Task 对象
        tasks = []
        for item in dataset:
            task = MyBenchmarkTask(
                task_id=item['id'],
                prompt=item['prompt'],
                expected_output=item['expected'],
                metadata=item.get('metadata', {})
            )
            tasks.append(task)

        return tasks

    def convert_results(self, results: List[TaskResult]) -> StandardizedResult:
        """转换为标准化输出"""
        return StandardizedResult(
            run_id=self.run_id,
            task_ids=[r.task_id for r in results],
            success=all(r.success for r in results),
            total_tasks=len(results),
            successful_tasks=sum(1 for r in results if r.success),
            # ... 其他字段
        )
```

#### 步骤 2：实现 Task 类

```python
class MyBenchmarkTask(SingleTurnTask):
    """单个任务"""

    def __init__(self, task_id: str, prompt: str, expected_output: str, metadata: Dict):
        self.task_id = task_id
        self.prompt = prompt
        self.expected_output = expected_output
        self.metadata = metadata

    async def execute(self, model_adapter, config) -> TaskResult:
        """执行任务"""
        # 1. 调用模型
        response = await model_adapter.generate(
            messages=[{"role": "user", "content": self.prompt}]
        )

        # 2. 验证结果
        is_correct = self._validate(response.content, self.expected_output)

        # 3. 返回结果
        return TaskResult(
            task_id=self.task_id,
            success=is_correct,
            output=response.content,
            metrics={
                'tokens': response.total_tokens,
                'cost': response.cost_usd,
                'latency_ms': response.latency_ms
            }
        )

    def _validate(self, output: str, expected: str) -> bool:
        """验证逻辑"""
        # 实现自定义验证（精确匹配、模糊匹配、代码执行等）
        return output.strip() == expected.strip()
```

#### 步骤 3：实现 Environment

```python
class MyBenchmarkEnvironment(UnifiedEnv):
    """执行环境"""

    def reset(self) -> Observation:
        """重置环境"""
        self.state = EnvironmentState()
        return Observation(content="Environment ready")

    def step(self, action: Action) -> Tuple[Observation, Reward, bool, Info]:
        """执行动作"""
        # 执行代码、运行测试等
        result = self._execute_action(action)

        observation = Observation(content=result.output)
        reward = 1.0 if result.success else 0.0
        done = result.is_terminal
        info = {"details": result.metadata}

        return observation, reward, done, info

    def success(self) -> bool:
        """任务是否成功"""
        return self.state.is_success
```

#### 步骤 4：注册 Adapter

```python
# core/unified_task_registry.py

# 在 AdapterRegistry 中注册
adapter_registry.register("my_benchmark", MyBenchmarkAdapter())
```

#### 步骤 5：配置使用

```yaml
# config/examples/my_benchmark_evaluation.yaml
evaluation:
  name: "My Benchmark Evaluation"

  tasks:
    source: my_benchmark  # 使用新 Adapter
    filter:
      category: "math"
      difficulty: "hard"
      max_instances: 100

  models:
    - gpt-4-turbo
    - claude-3.5-sonnet
```

---

## 🔌 3. 开发自定义插件

### 3.1 插件结构

```python
# integrations/adeworker/plugins/my_custom_plugin.py

from integrations.plugin_system.base import AgentPlugin, PluginMetadata, PluginPriority
from integrations.plugin_system.models import AgentContext, TurnData, MessageChunk

class MyCustomPlugin(AgentPlugin):
    """自定义插件示例"""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="my_custom_plugin",
            version="1.0.0",
            author="Your Name",
            description="Tracks custom metrics for my team",
            dependencies=[],  # 依赖其他插件（可选）
            priority=PluginPriority.NORMAL,
            enabled=True
        )

    def __init__(self, config: Dict):
        self.config = config
        self.custom_storage = []

    # ========== 生命周期钩子 ==========

    async def on_load(self, config: Dict) -> bool:
        """插件加载时"""
        logger.info(f"Loading {self.metadata.name}")
        # 初始化数据库连接、加载配置等
        return True

    async def on_enable(self) -> bool:
        """插件启用时"""
        logger.info(f"Enabling {self.metadata.name}")
        return True

    # ========== Agent 执行钩子 ==========

    async def on_agent_start(self, context: AgentContext):
        """Agent 开始执行"""
        logger.info(f"Agent started: {context.agent_type}")

        # 示例：记录开始时间
        self.custom_storage.append({
            'event': 'start',
            'task_id': context.task_id,
            'timestamp': time.time()
        })

    async def on_message_chunk(self, chunk: MessageChunk):
        """流式消息片段"""
        # 示例：统计 thinking 时间
        if chunk.type == 'thinking':
            thinking_length = len(chunk.content)
            logger.debug(f"Thinking: {thinking_length} chars")

    async def on_tool_call(self, tool_use):
        """工具调用"""
        # 示例：记录工具使用频率
        tool_name = tool_use.name
        logger.info(f"Tool called: {tool_name}")

        # 发送到自定义分析平台
        await self._send_to_analytics({
            'event': 'tool_call',
            'tool': tool_name,
            'timestamp': time.time()
        })

    async def on_agent_end(self, final_result):
        """Agent 执行结束"""
        # 计算自定义指标
        duration = time.time() - self.start_time
        logger.info(f"Task completed in {duration:.2f}s")

        # 生成报告
        await self._generate_custom_report(final_result)

    # ========== 自定义方法 ==========

    async def _send_to_analytics(self, data: Dict):
        """发送到自定义分析平台"""
        async with aiohttp.ClientSession() as session:
            await session.post(
                self.config['analytics_url'],
                json=data
            )

    async def _generate_custom_report(self, result):
        """生成自定义报告"""
        report = {
            'task_id': result.task_id,
            'success': result.success,
            'custom_metrics': self.calculate_custom_metrics()
        }

        # 保存到文件或数据库
        with open(f"/tmp/reports/{result.task_id}.json", 'w') as f:
            json.dump(report, f)
```

### 3.2 注册与配置

```yaml
# adeworker/config/evaluation.yaml
evaluation:
  plugins:
    - name: my_custom_plugin
      enabled: true
      config:
        analytics_url: https://analytics.mycompany.com/api/events
        report_path: /tmp/reports
        custom_threshold: 100
```

### 3.3 高级用法：插件间通信

```python
class PluginA(AgentPlugin):
    async def on_agent_start(self, context):
        # 发布事件
        await self.emit_event('task_started', {'task_id': context.task_id})

class PluginB(AgentPlugin):
    async def on_load(self, config):
        # 订阅事件
        await self.subscribe_event('task_started', self.handle_task_start)

    async def handle_task_start(self, event_data):
        logger.info(f"PluginB received event: {event_data}")
```

---

## 📢 4. 添加新告警通道

### 4.1 实现 Notifier

```python
# core/alerting/notifiers/my_notifier.py

from core.alerting.notifiers.base import Notifier
from typing import Dict

class MyCustomNotifier(Notifier):
    """自定义通知器"""

    def __init__(self, config: Dict):
        self.webhook_url = config.get('webhook_url')
        self.api_key = config.get('api_key')
        self.channel_id = config.get('channel_id')

    async def send(self, message: str, config: Dict):
        """发送通知"""
        # 构建请求
        payload = {
            'channel': self.channel_id,
            'message': message,
            'priority': config.get('priority', 'normal')
        }

        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

        # 发送 HTTP 请求
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.webhook_url,
                json=payload,
                headers=headers
            ) as response:
                if response.status != 200:
                    raise Exception(f"Failed to send notification: {response.status}")

                logger.info(f"Notification sent via MyCustomNotifier")
```

### 4.2 注册 Notifier

```python
# core/alerting/alert_engine.py

class AlertEngine:
    def _init_notifiers(self) -> Dict[str, Notifier]:
        return {
            'slack': SlackNotifier(self.config.get('slack', {})),
            'dingtalk': DingTalkNotifier(self.config.get('dingtalk', {})),
            'email': EmailNotifier(self.config.get('email', {})),

            # 新增自定义通知器
            'my_custom': MyCustomNotifier(self.config.get('my_custom', {})),
        }
```

### 4.3 配置使用

```yaml
# config/alert_rules.yaml
alert_rules:
  - name: high_cost_alert
    condition: trace.total_cost > 10.0
    notifications:
      - channel: my_custom  # 使用自定义通知器
        template: |
          🚨 High Cost Alert
          Task: {{task_id}}
          Cost: ${{total_cost}}
```

---

## 🛠️ 开发最佳实践

### 1. 代码规范

- **类型注解**：所有公共 API 必须有类型注解
- **文档字符串**：使用 Google 风格的 docstring
- **错误处理**：使用自定义异常类，避免裸 except
- **日志记录**：使用结构化日志（`structlog`）

### 2. 测试要求

- **单元测试**：覆盖率 >80%
- **集成测试**：至少 1 个端到端场景
- **性能测试**：验证性能开销 <5%

### 3. 文档要求

- **README**：每个扩展模块需要 README
- **示例**：提供完整的使用示例
- **配置说明**：列出所有配置项及默认值

---

## 📚 参考资源

### 官方文档

- [LiteLLM Providers](https://docs.litellm.ai/docs/providers)
- [OpenTelemetry](https://opentelemetry.io/docs/)
- [TimescaleDB](https://docs.timescale.com/)

### 示例代码

- `core/model_adapters/litellm_adapter.py` - 标准 ModelAdapter 实现
- `core/swe_bench_adapter.py` - 完整的 BenchmarkAdapter 示例
- `integrations/adeworker/plugins/evaluation_plugin.py` - 插件示例
- `core/alerting/notifiers/slack.py` - Notifier 示例

---

## 🤝 社区贡献

我们欢迎社区贡献新的扩展！

### 贡献流程

1. **Fork 仓库**
2. **创建分支**: `git checkout -b feature/my-extension`
3. **实现扩展**（按照本指南）
4. **编写测试** + **更新文档**
5. **提交 PR**

### PR 检查清单

- [ ] 代码符合规范（通过 linting）
- [ ] 测试覆盖率 >80%
- [ ] 文档完整（README + 示例）
- [ ] 向后兼容
- [ ] 性能测试通过

---

**相关文档**：
- [总体架构](./00_architecture_overview.md)
- [API 规范](./04_api_specification.md)
- [实施计划](./06_implementation_timeline.md)
