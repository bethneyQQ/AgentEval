# Milestone 2 Implementation Checklist

**版本**: v1.0
**时间范围**: Week 8-11 (4 周)
**目标**: 实现 ADEWorker 集成层，性能开销 < 5%

---

## 📊 进度概览

| 阶段 | 时间 | 状态 | 完成度 |
|------|------|------|--------|
| Week 8-9: Plugin System | 第 8-9 周 | 🔲 未开始 | 0% |
| Week 10: Trace & Session | 第 10 周 | 🔲 未开始 | 0% |
| Week 11: Integration & Test | 第 11 周 | 🔲 未开始 | 0% |

**图例**: 🔲 未开始 | 🔄 进行中 | ✅ 已完成 | ⚠️ 有风险 | ❌ 已阻塞

---

## Week 8-9: Plugin System 实现

**目标**: 构建可扩展的插件系统，支持动态加载与卸载

### Day 1-2: 核心接口设计与实现

#### Task 1.1: 创建项目骨架
- [ ] **优先级**: P0
- [ ] **负责人**: 平台工程师
- [ ] **工作量**: 0.5 天
- [ ] **依赖**: 无

**子任务**:
```bash
# 1. 创建项目目录结构
mkdir -p agenteval_plugin/{core,plugins,trace,session,utils,decorators}

# 2. 创建必要的 __init__.py
touch agenteval_plugin/__init__.py
touch agenteval_plugin/core/__init__.py
touch agenteval_plugin/plugins/__init__.py
touch agenteval_plugin/trace/__init__.py
touch agenteval_plugin/session/__init__.py
touch agenteval_plugin/utils/__init__.py

# 3. 创建 setup.py / pyproject.toml
cat > pyproject.toml <<EOF
[tool.poetry]
name = "agenteval-plugin"
version = "0.1.0"
description = "AgentEval Plugin for ADEWorker Integration"
authors = ["AgentEval Team <team@agenteval.com>"]

[tool.poetry.dependencies]
python = "^3.10"
pydantic = "^2.0"
aiohttp = "^3.9"

[tool.poetry.dev-dependencies]
pytest = "^7.4"
pytest-asyncio = "^0.21"
pytest-cov = "^4.1"
black = "^23.0"
ruff = "^0.1"
mypy = "^1.7"
EOF

# 4. 初始化 git
git init
echo "__pycache__/" > .gitignore
echo "*.pyc" >> .gitignore
echo ".pytest_cache/" >> .gitignore
echo "dist/" >> .gitignore
```

**验收标准**:
- [ ] 项目目录结构完整
- [ ] 可以成功执行 `poetry install`
- [ ] CI/CD 配置完成（GitHub Actions）

---

#### Task 1.2: 实现 Plugin Base Class
- [ ] **优先级**: P0
- [ ] **负责人**: 平台工程师
- [ ] **工作量**: 1 天
- [ ] **依赖**: Task 1.1

**实现文件**:
- `agenteval_plugin/core/plugin_base.py`

**实现内容**:
```python
# agenteval_plugin/core/plugin_base.py

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from pydantic import BaseModel

class PluginMetadata(BaseModel):
    """插件元信息"""
    id: str
    name: str
    version: str
    description: str
    author: str
    dependencies: list[str] = []

class PluginConfig(BaseModel):
    """插件配置"""
    enabled: bool = True
    priority: int = 100
    sampling_rate: float = 1.0
    async_mode: bool = True
    extra: Dict[str, Any] = {}

class AgentContext(BaseModel):
    """Agent 上下文"""
    agent_id: str
    agent_type: str
    agent_version: str
    session_id: str
    user_id: str
    task_id: str
    workspace_path: str
    start_time: float
    metadata: Dict[str, Any] = {}

# ... (其他 Context 类，参考设计文档)

class BasePlugin(ABC):
    """插件基类"""

    def __init__(self, config: Optional[PluginConfig] = None):
        self.config = config or PluginConfig()
        self._enabled = self.config.enabled

    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        pass

    # ... (钩子方法，参考设计文档)
```

**验收标准**:
- [ ] 所有 Context 类型定义完成（AgentContext, NodeContext, LLMContext, ToolContext）
- [ ] BasePlugin 抽象类定义完成
- [ ] 所有钩子方法签名定义完成
- [ ] Pydantic 模型验证通过
- [ ] 类型注解完整（mypy 检查通过）

**测试**:
```python
# tests/core/test_plugin_base.py

import pytest
from agenteval_plugin.core.plugin_base import BasePlugin, PluginMetadata

class TestPlugin(BasePlugin):
    @property
    def metadata(self):
        return PluginMetadata(
            id="test",
            name="Test",
            version="1.0.0",
            description="Test plugin",
            author="Test"
        )

def test_plugin_instantiation():
    plugin = TestPlugin()
    assert plugin.metadata.id == "test"
    assert plugin.config.enabled is True

def test_should_process_sampling():
    plugin = TestPlugin()
    plugin.config.sampling_rate = 0.5
    # 测试采样逻辑
    results = [plugin.should_process() for _ in range(1000)]
    ratio = sum(results) / len(results)
    assert 0.4 < ratio < 0.6  # 允许 10% 误差
```

---

#### Task 1.3: 实现 Plugin Manager
- [ ] **优先级**: P0
- [ ] **负责人**: 平台工程师
- [ ] **工作量**: 1.5 天
- [ ] **依赖**: Task 1.2

**实现文件**:
- `agenteval_plugin/core/plugin_manager.py`

**核心功能**:
1. 插件注册/注销
2. 插件启用/禁用
3. 钩子触发（异步执行）
4. 优先级管理
5. 异常隔离

**实现要点**:
```python
# 关键代码片段

class PluginManager:
    def __init__(self):
        self._plugins: Dict[str, BasePlugin] = {}
        self._enabled_plugins: Dict[str, BasePlugin] = {}
        self._hook_handlers: Dict[str, List[BasePlugin]] = {
            'on_agent_start': [],
            'on_agent_end': [],
            # ... 其他钩子
        }

    async def _trigger_hook(self, hook_name: str, *args, **kwargs):
        """通用钩子触发（关键优化点）"""
        handlers = self._hook_handlers.get(hook_name, [])
        tasks = []

        for plugin in handlers:
            if not plugin.should_process():
                continue

            try:
                handler = getattr(plugin, hook_name)
                if plugin.config.async_mode:
                    # 异步执行，不阻塞主流程
                    tasks.append(asyncio.create_task(
                        self._safe_execute(handler, *args, **kwargs)
                    ))
                else:
                    # 同步执行
                    await self._safe_execute(handler, *args, **kwargs)
            except Exception as e:
                logger.error(f"Error in {hook_name}: {e}")

        # 等待所有异步任务（但不阻塞太久）
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
```

**验收标准**:
- [ ] 单例模式正确实现
- [ ] 插件注册/注销功能完成
- [ ] 所有钩子触发方法实现
- [ ] 异步执行逻辑正确
- [ ] 异常不会传播到主流程
- [ ] 优先级排序生效

**测试**:
```python
# tests/core/test_plugin_manager.py

@pytest.mark.asyncio
async def test_plugin_manager_singleton():
    manager1 = PluginManager()
    manager2 = PluginManager()
    assert manager1 is manager2

@pytest.mark.asyncio
async def test_hook_async_execution():
    manager = PluginManager()
    plugin = MockPlugin()
    manager.register_plugin(plugin)

    start = time.time()
    await manager.trigger_agent_start(mock_context)
    duration = time.time() - start

    # 验证：即使插件执行很慢，也不会阻塞主流程
    assert duration < 0.1  # 应该几乎立即返回

@pytest.mark.asyncio
async def test_plugin_exception_isolation():
    manager = PluginManager()

    class BrokenPlugin(BasePlugin):
        async def on_agent_start(self, context):
            raise RuntimeError("Plugin error!")

    manager.register_plugin(BrokenPlugin())

    # 验证：插件异常不会导致主流程崩溃
    try:
        await manager.trigger_agent_start(mock_context)
    except RuntimeError:
        pytest.fail("Plugin exception leaked to main flow!")
```

---

### Day 3-4: 装饰器系统实现

#### Task 2.1: 实现 Agent 装饰器
- [ ] **优先级**: P0
- [ ] **负责人**: 平台工程师
- [ ] **工作量**: 1 天
- [ ] **依赖**: Task 1.3

**实现文件**:
- `agenteval_plugin/decorators/agent_decorator.py`

**核心功能**:
1. 包装 `arun` / `astream_run` 方法
2. 自动创建 AgentContext
3. 触发 on_agent_start / on_agent_end 钩子
4. 支持流式输出（astream_run）

**实现要点**:
```python
# 关键代码片段

def instrument_agent(agent_type: str, agent_version: str = "1.0.0"):
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(self, user_input, *args, **kwargs):
            # 构造 AgentContext
            context = AgentContext(
                agent_id=f"{agent_type}_{user_input.task_id}",
                agent_type=agent_type,
                agent_version=agent_version,
                # ... 其他字段
            )

            # 触发 on_agent_start
            await plugin_manager.trigger_agent_start(context)

            result = None
            error = None
            try:
                # 执行原方法
                result = await func(self, user_input, *args, **kwargs)

                # 处理流式输出
                if inspect.isasyncgen(result):
                    async def wrapped_generator():
                        try:
                            async for item in result:
                                yield item
                        finally:
                            await plugin_manager.trigger_agent_end(context, None, None)

                    return wrapped_generator()
                else:
                    return result
            except Exception as e:
                error = e
                raise
            finally:
                if not inspect.isasyncgen(result):
                    await plugin_manager.trigger_agent_end(context, result, error)

        return wrapper
    return decorator
```

**验收标准**:
- [ ] arun 方法装饰器完成
- [ ] astream_run 方法装饰器完成
- [ ] 流式输出场景钩子触发正确
- [ ] 异常场景 on_agent_end 仍然触发
- [ ] 性能开销 < 1ms

**测试**:
```python
# tests/decorators/test_agent_decorator.py

@pytest.mark.asyncio
async def test_instrument_agent_arun():
    class MockAgent:
        @instrument_agent(agent_type="TestAgent")
        async def arun(self, user_input):
            await asyncio.sleep(0.1)
            return "result"

    agent = MockAgent()
    mock_input = UserInput(task_id="t1", task_desc="test")

    result = await agent.arun(mock_input)
    assert result == "result"

    # 验证钩子被触发
    # (需要 Mock PluginManager)

@pytest.mark.asyncio
async def test_instrument_agent_astream():
    class MockAgent:
        @instrument_agent(agent_type="TestAgent")
        async def astream_run(self, user_input):
            for i in range(3):
                yield i

    agent = MockAgent()
    mock_input = UserInput(task_id="t1", task_desc="test")

    results = []
    async for item in agent.astream_run(mock_input):
        results.append(item)

    assert results == [0, 1, 2]
    # 验证 on_agent_end 在生成器结束时触发
```

---

#### Task 2.2: 实现 Node 装饰器
- [ ] **优先级**: P0
- [ ] **负责人**: 平台工程师
- [ ] **工作量**: 0.5 天
- [ ] **依赖**: Task 2.1

**实现文件**:
- `agenteval_plugin/decorators/node_decorator.py`

**核心功能**:
1. 包装 LangGraph 节点方法
2. 触发 on_node_start / on_node_end
3. 从 state 中提取 AgentContext

**实现要点**:
```python
def instrument_node(node_name: str):
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(self, state, *args, **kwargs):
            # 从 state 中提取 AgentContext
            agent_context = getattr(state, '_agent_context', None)
            if not agent_context:
                return await func(self, state, *args, **kwargs)

            node_context = NodeContext(
                node_name=node_name,
                start_time=time.time(),
                input_state=state.dict() if hasattr(state, 'dict') else {}
            )

            await plugin_manager.trigger_node_start(agent_context, node_context)

            output_state = None
            error = None
            try:
                output_state = await func(self, state, *args, **kwargs)
                return output_state
            except Exception as e:
                error = e
                raise
            finally:
                await plugin_manager.trigger_node_end(
                    agent_context, node_context, output_state, error
                )

        return wrapper
    return decorator
```

**验收标准**:
- [ ] 节点装饰器正确包装同步/异步方法
- [ ] AgentContext 从 state 中提取正确
- [ ] 输入/输出状态记录正确

---

#### Task 2.3: 实现 LLM 装饰器（可选）
- [ ] **优先级**: P1
- [ ] **负责人**: 平台工程师
- [ ] **工作量**: 0.5 天
- [ ] **依赖**: Task 2.2

**说明**: 由于 adeworker 使用 LangChain，可以通过 LangChain 的 Callback 机制实现 LLM 钩子，此任务优先级较低。

---

### Day 5-6: 单元测试与文档

#### Task 3.1: 单元测试完善
- [ ] **优先级**: P0
- [ ] **负责人**: QA 工程师
- [ ] **工作量**: 1 天
- [ ] **依赖**: Task 1.3, 2.2

**测试范围**:
- [ ] `plugin_base.py` 覆盖率 > 90%
- [ ] `plugin_manager.py` 覆盖率 > 85%
- [ ] `agent_decorator.py` 覆盖率 > 85%
- [ ] `node_decorator.py` 覆盖率 > 85%

**关键测试场景**:
```python
# tests/integration/test_plugin_system.py

@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_plugin_workflow():
    """端到端测试：插件注册 → 装饰 Agent → 执行任务 → 钩子触发"""

    # 1. 创建 Mock Plugin
    class TrackerPlugin(BasePlugin):
        def __init__(self):
            super().__init__()
            self.events = []

        @property
        def metadata(self):
            return PluginMetadata(
                id="tracker",
                name="Tracker",
                version="1.0.0",
                description="Track events",
                author="Test"
            )

        async def on_agent_start(self, context):
            self.events.append(('agent_start', context.task_id))

        async def on_node_start(self, agent_context, node_context):
            self.events.append(('node_start', node_context.node_name))

        async def on_agent_end(self, context, result, error):
            self.events.append(('agent_end', context.task_id))

    # 2. 注册插件
    plugin = TrackerPlugin()
    plugin_manager.register_plugin(plugin)

    # 3. 创建装饰后的 Agent
    class TestAgent:
        @instrument_agent(agent_type="TestAgent")
        async def arun(self, user_input):
            await self.step1()
            return "done"

        @instrument_node(node_name="step1")
        async def step1(self):
            await asyncio.sleep(0.01)

    # 4. 执行任务
    agent = TestAgent()
    await agent.arun(UserInput(task_id="t1", task_desc="test"))

    # 5. 验证事件顺序
    assert plugin.events == [
        ('agent_start', 't1'),
        ('node_start', 'step1'),
        ('agent_end', 't1')
    ]
```

**验收标准**:
- [ ] 总体测试覆盖率 > 80%
- [ ] 所有 P0 功能有测试覆盖
- [ ] 集成测试通过

---

#### Task 3.2: API 文档编写
- [ ] **优先级**: P1
- [ ] **负责人**: 技术文档工程师
- [ ] **工作量**: 0.5 天
- [ ] **依赖**: Task 3.1

**文档内容**:
1. Plugin API Reference
   - BasePlugin 接口说明
   - 各个钩子方法的参数与返回值
   - 示例代码

2. 装饰器使用指南
   - `@instrument_agent` 用法
   - `@instrument_node` 用法
   - 最佳实践

**交付物**:
- `docs/api/PLUGIN_API.md`
- `docs/guides/PLUGIN_DEVELOPMENT_GUIDE.md`

---

### Day 7: 集成测试与 Review

#### Task 4.1: 集成测试（Mock adeworker）
- [ ] **优先级**: P0
- [ ] **负责人**: QA 工程师
- [ ] **工作量**: 0.5 天
- [ ] **依赖**: Task 3.1

**测试内容**:
```python
# tests/integration/test_mock_adeworker.py

@pytest.mark.integration
@pytest.mark.asyncio
async def test_mock_dev_agent_integration():
    """模拟 DevAgent 的完整流程"""

    # 1. 创建 Mock DevAgent（模拟 adeworker 的 DevAgent）
    class MockDevAgent:
        @instrument_agent(agent_type="DevAgent", agent_version="1.0.0")
        async def arun(self, user_input):
            state = {'input': user_input}
            state = await self._node_prepare(state)
            state = await self._node_code_gen(state)
            return state

        @instrument_node(node_name="prepare_context")
        async def _node_prepare(self, state):
            await asyncio.sleep(0.01)
            state['prepared'] = True
            return state

        @instrument_node(node_name="gen_code")
        async def _node_code_gen(self, state):
            await asyncio.sleep(0.01)
            state['code'] = "print('hello')"
            return state

    # 2. 执行任务
    agent = MockDevAgent()
    result = await agent.arun(UserInput(
        task_id="test_task",
        task_desc="Generate hello world"
    ))

    # 3. 验证结果
    assert result['prepared'] is True
    assert result['code'] == "print('hello')"

    # 4. 验证插件收集了数据
    # (检查 TrackerPlugin 的事件列表)
```

**验收标准**:
- [ ] Mock DevAgent 完整流程测试通过
- [ ] 所有钩子触发顺序正确
- [ ] 无内存泄漏

---

#### Task 4.2: Code Review
- [ ] **优先级**: P0
- [ ] **负责人**: 架构师 + 资深工程师
- [ ] **工作量**: 0.5 天
- [ ] **依赖**: Task 4.1

**Review 要点**:
- [ ] 代码风格一致（Black + Ruff）
- [ ] 类型注解完整（mypy 通过）
- [ ] 异常处理完善
- [ ] 日志记录合理
- [ ] 性能优化到位
- [ ] 安全性（无敏感信息泄露）

---

## Week 10: Trace Collector & Session Mapper

**目标**: 实现轨迹收集与会话映射功能

### Day 8-9: Trace Collector 实现

#### Task 5.1: TraceCollector 核心逻辑
- [ ] **优先级**: P0
- [ ] **负责人**: 平台工程师
- [ ] **工作量**: 1.5 天
- [ ] **依赖**: Week 8-9 完成

**实现文件**:
- `agenteval_plugin/trace/trace_collector.py`
- `agenteval_plugin/trace/models.py`

**核心功能**:
1. 异步队列（asyncio.Queue）
2. 批量上报（100 条或 1 秒触发）
3. 数据压缩（gzip）
4. 重试机制（指数退避）

**实现要点**:
```python
class TraceCollector:
    async def _batch_worker(self):
        """后台批量处理线程（关键优化点）"""
        while True:
            try:
                # 等待事件或超时
                try:
                    event = await asyncio.wait_for(
                        self.event_queue.get(),
                        timeout=self.max_wait_seconds
                    )
                    self.batch_buffer.append(event)
                except asyncio.TimeoutError:
                    pass

                # 检查是否需要 flush
                should_flush = (
                    len(self.batch_buffer) >= self.max_batch_size or
                    (len(self.batch_buffer) > 0 and
                     time.time() - self.last_flush_time >= self.max_wait_seconds)
                )

                if should_flush:
                    await self._flush()

            except Exception as e:
                logger.error(f"Error in batch worker: {e}")
```

**验收标准**:
- [ ] 异步队列正常工作
- [ ] 批量触发逻辑正确（100 条 OR 1 秒）
- [ ] 数据压缩率 > 70%
- [ ] 无内存泄漏（长时间运行）

**测试**:
```python
# tests/trace/test_trace_collector.py

@pytest.mark.asyncio
async def test_batch_trigger_by_size():
    """测试：批量大小触发"""
    collector = TraceCollector(config={'batch': {'max_size': 10}})
    await collector.start()

    # 添加 10 条事件
    for i in range(10):
        await collector.collect(TraceEvent(...))

    # 等待 flush
    await asyncio.sleep(0.1)

    # 验证：应该触发了 1 次上报
    assert collector.upload_count == 1

@pytest.mark.asyncio
async def test_batch_trigger_by_time():
    """测试：时间触发"""
    collector = TraceCollector(config={'batch': {'max_wait_seconds': 0.5}})
    await collector.start()

    # 添加 1 条事件
    await collector.collect(TraceEvent(...))

    # 等待 0.6 秒
    await asyncio.sleep(0.6)

    # 验证：应该触发了 1 次上报
    assert collector.upload_count == 1
```

---

#### Task 5.2: 数据脱敏功能
- [ ] **优先级**: P0
- [ ] **负责人**: 安全工程师
- [ ] **工作量**: 0.5 天
- [ ] **依赖**: Task 5.1

**实现文件**:
- `agenteval_plugin/privacy/redactor.py`

**核心功能**:
1. 敏感字段过滤（password, token, api_key）
2. 正则替换（API Key, GitHub Token, SSN）
3. 高性能（避免深度递归）

**验收标准**:
- [ ] 检出率 > 95%（使用测试数据集）
- [ ] 处理 1000 条记录 < 100ms
- [ ] 无误杀（正常数据不被脱敏）

**测试**:
```python
# tests/privacy/test_redactor.py

def test_redact_openai_key():
    text = "My API key is sk-1234567890abcdefghijklmnopqrstuv"
    redacted = DataRedactor.redact_text(text)
    assert "sk-1234567890abcdefghijklmnopqrstuv" not in redacted
    assert "sk-***REDACTED***" in redacted

def test_redact_dict():
    data = {
        'password': 'secret123',
        'username': 'john',
        'api_key': 'sk-xxxxx'
    }
    redacted = DataRedactor.redact_dict(data)
    assert redacted['password'] == '***REDACTED***'
    assert redacted['username'] == 'john'  # 不应被脱敏
```

---

#### Task 5.3: HTTP Client 与重试机制
- [ ] **优先级**: P0
- [ ] **负责人**: 平台工程师
- [ ] **工作量**: 0.5 天
- [ ] **依赖**: Task 5.1

**实现文件**:
- `agenteval_plugin/utils/http_client.py`

**核心功能**:
1. 异步 HTTP Client（基于 aiohttp）
2. 指数退避重试
3. 超时控制（30s）
4. 连接池管理

**实现要点**:
```python
class AsyncHTTPClient:
    async def post(self, path: str, data: Any, headers: Dict = None):
        retry_config = self.retry_config
        for attempt in range(retry_config.max_attempts):
            try:
                async with self.session.post(
                    f"{self.base_url}{path}",
                    data=data,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        return response
                    else:
                        logger.warning(f"Upload failed: {response.status}")
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} failed: {e}")

            # 指数退避
            if attempt < retry_config.max_attempts - 1:
                wait = min(
                    retry_config.backoff_factor ** attempt,
                    retry_config.max_backoff_seconds
                )
                await asyncio.sleep(wait)

        raise RuntimeError(f"Failed after {retry_config.max_attempts} attempts")
```

**验收标准**:
- [ ] 重试逻辑正确（最多 3 次）
- [ ] 指数退避生效
- [ ] 超时控制生效
- [ ] 连接池复用

---

### Day 10: Session Mapper & EvaluationPlugin

#### Task 6.1: SessionMapper 实现
- [ ] **优先级**: P0
- [ ] **负责人**: 平台工程师
- [ ] **工作量**: 0.5 天
- [ ] **依赖**: Task 5.1

**实现文件**:
- `agenteval_plugin/session/session_mapper.py`

**核心功能**:
1. Session → Trace 映射
2. 双向查询（user_session_id / agent_session_id → trace_id）
3. 内存管理（LRU 淘汰）

**验收标准**:
- [ ] 映射创建与查询功能正常
- [ ] 支持 10,000+ 并发会话
- [ ] 内存占用 < 100MB

---

#### Task 6.2: EvaluationPlugin 实现
- [ ] **优先级**: P0
- [ ] **负责人**: 平台工程师
- [ ] **工作量**: 0.5 天
- [ ] **依赖**: Task 5.1, 6.1

**实现文件**:
- `agenteval_plugin/plugins/evaluation_plugin.py`

**核心功能**:
1. 实现所有钩子方法
2. 创建 Trace/Span 事件
3. 调用 TraceCollector 收集数据
4. 管理 Trace/Span 生命周期

**验收标准**:
- [ ] 所有钩子方法实现完成
- [ ] Trace/Span 树结构正确
- [ ] 事件上报成功率 > 99%

**测试**:
```python
# tests/plugins/test_evaluation_plugin.py

@pytest.mark.asyncio
async def test_evaluation_plugin_full_workflow():
    """端到端测试：EvaluationPlugin"""

    # 1. 启动 TraceCollector（Mock 服务端）
    collector = TraceCollector(config=test_config)
    await collector.start()

    # 2. 注册 EvaluationPlugin
    plugin = EvaluationPlugin()
    plugin_manager.register_plugin(plugin)

    # 3. 模拟 Agent 执行
    context = AgentContext(...)
    await plugin.on_agent_start(context)

    node_context = NodeContext(...)
    await plugin.on_node_start(context, node_context)
    await plugin.on_node_end(context, node_context, {}, None)

    await plugin.on_agent_end(context, "result", None)

    # 4. 等待数据上报
    await asyncio.sleep(2)

    # 5. 验证：数据已上报到服务端
    assert len(mock_server.received_traces) > 0
```

---

### Day 11: 集成测试

#### Task 7.1: 端到端集成测试
- [ ] **优先级**: P0
- [ ] **负责人**: QA 工程师
- [ ] **工作量**: 1 天
- [ ] **依赖**: Task 6.2

**测试场景**:
1. **正常场景**: Agent 执行成功，数据正常上报
2. **异常场景**: Agent 执行失败，错误信息被记录
3. **网络故障**: 上报失败，数据被缓存到本地
4. **高并发**: 1000 个并发任务，无数据丢失

**测试脚本**:
```python
# tests/e2e/test_full_integration.py

@pytest.mark.e2e
@pytest.mark.asyncio
async def test_normal_scenario():
    """正常场景：完整流程"""
    # 1. 启动 Mock Server
    server = await start_mock_server()

    # 2. 配置 Plugin
    config = load_config('test_config.yaml')
    init_agenteval_plugin(config)

    # 3. 执行 Mock Agent
    agent = MockDevAgent()
    result = await agent.arun(UserInput(...))

    # 4. 等待数据上报
    await asyncio.sleep(2)

    # 5. 验证数据
    traces = server.get_received_traces()
    assert len(traces) == 1
    assert traces[0]['attributes']['agent.type'] == 'DevAgent'

@pytest.mark.e2e
@pytest.mark.asyncio
async def test_network_failure_scenario():
    """网络故障场景：本地缓存"""
    # 1. 关闭 Mock Server（模拟网络故障）

    # 2. 执行任务
    agent = MockDevAgent()
    await agent.arun(UserInput(...))

    # 3. 验证：数据被缓存到本地
    cache_files = list(Path('/tmp/agenteval_cache').glob('failed_*.json.gz'))
    assert len(cache_files) > 0

@pytest.mark.e2e
@pytest.mark.asyncio
async def test_high_concurrency():
    """高并发场景"""
    # 1. 启动 Mock Server
    server = await start_mock_server()

    # 2. 并发执行 1000 个任务
    tasks = [
        agent.arun(UserInput(task_id=f"task_{i}"))
        for i in range(1000)
    ]
    await asyncio.gather(*tasks)

    # 3. 等待所有数据上报
    await asyncio.sleep(10)

    # 4. 验证：所有数据都已上报
    traces = server.get_received_traces()
    assert len(traces) == 1000
```

**验收标准**:
- [ ] 所有场景测试通过
- [ ] 数据丢失率 < 0.1%
- [ ] 无内存泄漏

---

## Week 11: ADEWorker 集成与性能测试

**目标**: 完成真实集成，验证性能开销 < 5%

### Day 12-13: 代码集成

#### Task 8.1: 修改 adeworker 代码
- [ ] **优先级**: P0
- [ ] **负责人**: 集成工程师
- [ ] **工作量**: 1.5 天
- [ ] **依赖**: Week 10 完成

**修改文件列表**:
```bash
# 1. 添加依赖
# adeworker/backend/requirements.txt
agenteval-plugin==0.1.0

# 2. 启动时初始化插件
# adeworker/backend/worker/infra/startup/startup.py
from agenteval_plugin import init_agenteval_plugin
from agenteval_plugin.plugins.evaluation_plugin import EvaluationPlugin

async def startup():
    # ... 其他启动逻辑

    # 初始化 AgentEval Plugin
    if os.getenv('AGENTEVAL_ENABLED', 'false').lower() == 'true':
        init_agenteval_plugin(config_file='/etc/agenteval/config.yaml')
        plugin_manager.register_plugin(EvaluationPlugin())

# 3. 装饰 DevAgent 方法
# adeworker/backend/worker/agent/dev_agent/agent.py
from agenteval_plugin.decorators import instrument_agent, instrument_node

class BaseDevAgent(BaseAgent):

    @instrument_agent(agent_type="DevAgent", agent_version="1.0.0")
    async def arun(self, user_input: UserInput) -> DevState:
        # 原有逻辑不变
        ...

    @instrument_node(node_name="prepare_context")
    def _node_prepare_context(self, state: DevState) -> DevState:
        # 原有逻辑不变
        ...

    # ... 装饰其他节点方法
```

**验收标准**:
- [ ] 代码修改完成（约 10 处装饰器）
- [ ] 无编译错误
- [ ] 原有测试全部通过

---

#### Task 8.2: 配置文件与部署脚本
- [ ] **优先级**: P0
- [ ] **负责人**: SRE 工程师
- [ ] **工作量**: 0.5 天
- [ ] **依赖**: Task 8.1

**配置文件**:
```yaml
# /etc/agenteval/config.yaml

global:
  enabled: true
  log_level: INFO

trace_collector:
  enabled: true
  endpoint: "http://agenteval-server:8000/api/v1/traces"
  api_key: "${AGENTEVAL_API_KEY}"

  batch:
    max_size: 100
    max_wait_seconds: 1.0

  sampling:
    rate: 0.1  # 生产环境 10% 采样

  local_cache:
    enabled: true
    cache_dir: /var/lib/agenteval/cache

privacy:
  enabled: true
```

**部署脚本**:
```bash
# scripts/install_agenteval_plugin.sh

#!/bin/bash
set -e

# 1. 安装插件
pip install agenteval-plugin==0.1.0

# 2. 创建配置目录
mkdir -p /etc/agenteval
mkdir -p /var/lib/agenteval/cache

# 3. 复制配置文件
cp config/agenteval_plugin.yaml /etc/agenteval/config.yaml

# 4. 设置环境变量
export AGENTEVAL_ENABLED=true
export AGENTEVAL_API_KEY="your-api-key"

echo "AgentEval Plugin installed successfully!"
```

**验收标准**:
- [ ] 配置文件模板完整
- [ ] 部署脚本可用
- [ ] 环境变量文档完善

---

### Day 14-15: 性能测试

#### Task 9.1: Benchmark 测试
- [ ] **优先级**: P0
- [ ] **负责人**: SRE 工程师
- [ ] **工作量**: 1.5 天
- [ ] **依赖**: Task 8.2

**测试场景**:
1. **Baseline**: 运行 100 个任务，无插件
2. **With Plugin**: 运行 100 个任务，启用插件

**测试脚本**:
```python
# tests/performance/benchmark.py

import time
import statistics
from worker.agent.dev_agent.agent import BaseDevAgent

async def run_benchmark(agent, num_tasks=100):
    """运行 Benchmark"""
    times = []

    for i in range(num_tasks):
        user_input = UserInput(
            task_id=f"task_{i}",
            task_desc="Generate hello world function",
            repo_ws_path="/tmp/test_repo"
        )

        start = time.time()
        await agent.arun(user_input)
        duration = time.time() - start
        times.append(duration)

    return {
        'mean': statistics.mean(times),
        'median': statistics.median(times),
        'stdev': statistics.stdev(times),
        'p95': statistics.quantiles(times, n=20)[18],  # 95th percentile
        'p99': statistics.quantiles(times, n=100)[98]
    }

async def main():
    # 1. Baseline（无插件）
    print("Running baseline...")
    baseline_stats = await run_benchmark(agent_without_plugin)

    # 2. With Plugin
    print("Running with plugin...")
    plugin_stats = await run_benchmark(agent_with_plugin)

    # 3. 计算开销
    overhead_mean = (plugin_stats['mean'] - baseline_stats['mean']) / baseline_stats['mean'] * 100
    overhead_p95 = (plugin_stats['p95'] - baseline_stats['p95']) / baseline_stats['p95'] * 100

    print("\n" + "="*60)
    print("BENCHMARK RESULTS")
    print("="*60)
    print(f"Baseline Mean: {baseline_stats['mean']:.3f}s")
    print(f"With Plugin Mean: {plugin_stats['mean']:.3f}s")
    print(f"Overhead (Mean): {overhead_mean:.2f}%")
    print(f"\nBaseline P95: {baseline_stats['p95']:.3f}s")
    print(f"With Plugin P95: {plugin_stats['p95']:.3f}s")
    print(f"Overhead (P95): {overhead_p95:.2f}%")
    print("="*60)

    # 4. 验证：开销 < 5%
    assert overhead_mean < 5.0, f"Overhead too high: {overhead_mean:.2f}%"
    assert overhead_p95 < 5.0, f"P95 overhead too high: {overhead_p95:.2f}%"

    print("\n✅ Performance test PASSED! Overhead < 5%")

if __name__ == "__main__":
    asyncio.run(main())
```

**验收标准**:
- [ ] 平均开销 < 5%
- [ ] P95 开销 < 5%
- [ ] 内存峰值增长 < 10%
- [ ] CPU 使用率增长 < 5%

**性能报告模板**:
```markdown
# AgentEval Plugin 性能测试报告

## 测试环境
- CPU: 8 cores
- Memory: 16GB
- Python: 3.10
- 任务数量: 100

## 测试结果

| 指标 | Baseline | With Plugin | Overhead |
|------|----------|-------------|----------|
| 平均执行时间 | 12.5s | 12.9s | 3.2% |
| P95 执行时间 | 18.3s | 18.8s | 2.7% |
| P99 执行时间 | 22.1s | 22.6s | 2.3% |
| 内存峰值 | 512MB | 548MB | 7.0% |
| CPU 使用率 | 65% | 67% | 3.1% |

## 结论
✅ 所有性能指标满足要求（开销 < 5%）
```

---

#### Task 9.2: 长时间稳定性测试
- [ ] **优先级**: P1
- [ ] **负责人**: SRE 工程师
- [ ] **工作量**: 0.5 天
- [ ] **依赖**: Task 9.1

**测试场景**:
- 运行 1000+ 任务，持续 2+ 小时
- 监控内存/CPU 趋势
- 检查内存泄漏

**验收标准**:
- [ ] 内存稳定（无持续增长）
- [ ] 无异常崩溃
- [ ] 数据上报成功率 > 99%

---

### Day 16: 文档与 Demo

#### Task 10.1: 集成文档编写
- [ ] **优先级**: P0
- [ ] **负责人**: 技术文档工程师
- [ ] **工作量**: 0.5 天
- [ ] **依赖**: Task 9.2

**文档内容**:
1. **安装指南**
   - 依赖安装
   - 配置文件设置
   - 环境变量

2. **集成步骤**
   - 代码修改（装饰器添加）
   - 启动流程修改
   - 配置验证

3. **故障排查**
   - 常见问题 FAQ
   - 日志查看方法
   - 性能调优建议

**交付物**:
- `docs/integration/ADEWORKER_INTEGRATION_GUIDE.md`
- `README.md`

---

#### Task 10.2: 示例代码与 Demo
- [ ] **优先级**: P1
- [ ] **负责人**: 平台工程师
- [ ] **工作量**: 0.5 天
- [ ] **依赖**: Task 10.1

**示例内容**:
```python
# examples/simple_integration.py

"""
AgentEval Plugin 集成示例
"""

import asyncio
from agenteval_plugin import init_agenteval_plugin, PluginConfig
from agenteval_plugin.plugins.evaluation_plugin import EvaluationPlugin
from agenteval_plugin.decorators import instrument_agent

# 1. 初始化插件
config = PluginConfig(
    enabled=True,
    config_file='./config.yaml'
)
init_agenteval_plugin(config)

# 2. 注册 EvaluationPlugin
from agenteval_plugin.core.plugin_manager import plugin_manager
plugin_manager.register_plugin(EvaluationPlugin())

# 3. 创建装饰后的 Agent
class MyAgent:
    @instrument_agent(agent_type="MyAgent", agent_version="1.0.0")
    async def arun(self, user_input):
        print(f"Processing task: {user_input.task_id}")
        await asyncio.sleep(1)
        return "done"

# 4. 运行任务
async def main():
    agent = MyAgent()
    result = await agent.arun(UserInput(
        task_id="demo_task",
        task_desc="Demo task"
    ))
    print(f"Result: {result}")

if __name__ == "__main__":
    asyncio.run(main())
```

**验收标准**:
- [ ] 示例代码可运行
- [ ] README 清晰易懂
- [ ] Demo 视频录制完成

---

### Day 17: 最终验收

#### Task 11.1: 最终测试与验收
- [ ] **优先级**: P0
- [ ] **负责人**: QA + 产品经理
- [ ] **工作量**: 1 天
- [ ] **依赖**: 所有前序任务

**验收检查清单**:

**功能验收**:
- [ ] Plugin System 所有功能正常
- [ ] Trace Collector 数据上报成功
- [ ] Session Mapper 映射正确
- [ ] ADEWorker 集成无错误

**性能验收**:
- [ ] 性能开销 < 5% ✅
- [ ] 内存无泄漏 ✅
- [ ] 高并发无问题 ✅

**测试验收**:
- [ ] 单元测试覆盖率 > 80% ✅
- [ ] 集成测试全部通过 ✅
- [ ] E2E 测试全部通过 ✅

**文档验收**:
- [ ] API 文档完整 ✅
- [ ] 集成指南完整 ✅
- [ ] 示例代码可用 ✅

**代码质量验收**:
- [ ] Black + Ruff 检查通过 ✅
- [ ] mypy 类型检查通过 ✅
- [ ] Code Review 通过 ✅

---

## 🎯 关键里程碑

| 里程碑 | 日期 | 交付物 | 状态 |
|--------|------|--------|------|
| M1: Plugin System 完成 | Day 7 | Plugin 核心代码 + 单元测试 | 🔲 |
| M2: Trace & Session 完成 | Day 11 | Trace Collector + EvaluationPlugin | 🔲 |
| M3: 集成与测试完成 | Day 17 | ADEWorker 集成 + 性能报告 | 🔲 |

---

## 📈 每日站会议题

**每日站会**（15 分钟）:
1. 昨天完成了什么？
2. 今天计划做什么？
3. 遇到什么阻塞？

**示例**:
```
Day 8 站会:
- 昨天完成：Plugin System 单元测试（覆盖率 85%）
- 今天计划：开始 TraceCollector 核心逻辑实现
- 阻塞：无
```

---

## ⚠️ 风险与缓解措施

| 风险 | 概率 | 影响 | 缓解措施 | 负责人 |
|------|------|------|----------|--------|
| LangGraph 装饰器不生效 | 中 | 高 | 预研验证 + 备选方案（猴子补丁） | 平台工程师 |
| 性能开销超标 | 中 | 高 | 提前 Profiling，逐步优化 | SRE |
| adeworker 代码冲突 | 低 | 中 | 提前沟通，最小化修改 | 集成工程师 |
| 依赖包冲突 | 低 | 中 | 使用虚拟环境隔离 | 平台工程师 |

---

## 📝 交付物清单

### 代码交付物
- [ ] `agenteval-plugin` Python 包（可 pip 安装）
- [ ] `agenteval_plugin/core/` - 核心模块
- [ ] `agenteval_plugin/plugins/` - 插件实现
- [ ] `agenteval_plugin/trace/` - Trace Collector
- [ ] `agenteval_plugin/session/` - Session Mapper
- [ ] `agenteval_plugin/decorators/` - 装饰器
- [ ] `tests/` - 测试代码（覆盖率 > 80%）

### 文档交付物
- [ ] `README.md` - 项目说明
- [ ] `docs/api/PLUGIN_API.md` - API 文档
- [ ] `docs/guides/PLUGIN_DEVELOPMENT_GUIDE.md` - 开发指南
- [ ] `docs/integration/ADEWORKER_INTEGRATION_GUIDE.md` - 集成指南
- [ ] `docs/performance/BENCHMARK_REPORT.md` - 性能报告

### 配置交付物
- [ ] `config/agenteval_plugin.yaml` - 配置模板
- [ ] `scripts/install_agenteval_plugin.sh` - 安装脚本
- [ ] `.env.example` - 环境变量示例

### 示例交付物
- [ ] `examples/simple_integration.py` - 简单集成示例
- [ ] `examples/custom_plugin.py` - 自定义插件示例
- [ ] `examples/advanced_usage.py` - 高级用法示例

---

## 📞 联系人

| 角色 | 姓名 | 邮箱 | 职责 |
|------|------|------|------|
| 项目负责人 | - | - | 总体协调 |
| 平台工程师 | - | - | Plugin System, Trace Collector |
| 集成工程师 | - | - | ADEWorker 集成 |
| QA 工程师 | - | - | 测试 |
| SRE 工程师 | - | - | 性能测试、部署 |
| 技术文档工程师 | - | - | 文档编写 |

---

**文档结束**
