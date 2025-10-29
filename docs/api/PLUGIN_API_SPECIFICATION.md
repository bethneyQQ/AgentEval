# AgentEval Plugin API Specification

**版本**: v1.0.0
**更新日期**: 2025-01-28
**状态**: Draft

---

## 📋 目录

1. [概述](#1-概述)
2. [核心类型定义](#2-核心类型定义)
3. [Plugin Base API](#3-plugin-base-api)
4. [Plugin Manager API](#4-plugin-manager-api)
5. [装饰器 API](#5-装饰器-api)
6. [Trace Collector API](#6-trace-collector-api)
7. [Session Mapper API](#7-session-mapper-api)
8. [工具类 API](#8-工具类-api)
9. [配置 API](#9-配置-api)
10. [示例代码](#10-示例代码)

---

## 1. 概述

AgentEval Plugin 提供了一套完整的 API，用于：
- 创建自定义插件
- 管理插件生命周期
- 收集 Agent 执行轨迹
- 上报评估数据

### 1.1 安装

```bash
pip install agenteval-plugin
```

### 1.2 快速开始

```python
from agenteval_plugin import init_agenteval_plugin, PluginConfig
from agenteval_plugin.plugins.evaluation_plugin import EvaluationPlugin
from agenteval_plugin.core.plugin_manager import plugin_manager

# 初始化
config = PluginConfig(enabled=True, config_file='./config.yaml')
init_agenteval_plugin(config)

# 注册插件
plugin_manager.register_plugin(EvaluationPlugin())

# 使用装饰器
from agenteval_plugin.decorators import instrument_agent

class MyAgent:
    @instrument_agent(agent_type="MyAgent", agent_version="1.0.0")
    async def arun(self, user_input):
        return "done"
```

---

## 2. 核心类型定义

### 2.1 PluginMetadata

**描述**: 插件元信息

**定义**:
```python
from pydantic import BaseModel

class PluginMetadata(BaseModel):
    id: str                       # 插件唯一标识
    name: str                     # 插件名称
    version: str                  # 版本号（语义化版本）
    description: str              # 插件描述
    author: str                   # 作者
    dependencies: list[str] = []  # 依赖的其他插件 ID
```

**示例**:
```python
metadata = PluginMetadata(
    id="my_custom_plugin",
    name="My Custom Plugin",
    version="1.0.0",
    description="A custom plugin for specific metrics",
    author="John Doe",
    dependencies=["evaluation_plugin"]
)
```

---

### 2.2 PluginConfig

**描述**: 插件配置

**定义**:
```python
class PluginConfig(BaseModel):
    enabled: bool = True                # 是否启用插件
    priority: int = 100                 # 优先级（数字越小越优先）
    sampling_rate: float = 1.0          # 采样率（0.0-1.0）
    async_mode: bool = True             # 是否异步执行
    extra: Dict[str, Any] = {}          # 额外配置
```

**参数说明**:
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `enabled` | `bool` | `True` | 是否启用插件 |
| `priority` | `int` | `100` | 优先级，数字越小越早执行 |
| `sampling_rate` | `float` | `1.0` | 采样率，1.0 = 100% |
| `async_mode` | `bool` | `True` | 是否异步执行钩子（推荐） |
| `extra` | `dict` | `{}` | 自定义配置项 |

**示例**:
```python
config = PluginConfig(
    enabled=True,
    priority=50,           # 优先级高于默认
    sampling_rate=0.1,     # 10% 采样
    async_mode=True,
    extra={
        'custom_endpoint': 'http://custom-server:8080'
    }
)
```

---

### 2.3 AgentContext

**描述**: Agent 执行上下文

**定义**:
```python
class AgentContext(BaseModel):
    agent_id: str           # Agent 实例 ID
    agent_type: str         # Agent 类型（DevAgent, ChatAgent, etc.）
    agent_version: str      # Agent 版本
    session_id: str         # 会话 ID
    user_id: str            # 用户 ID
    task_id: str            # 任务 ID
    workspace_path: str     # 工作空间路径
    start_time: float       # 开始时间（Unix timestamp）
    metadata: Dict[str, Any] = {}  # 额外元数据
```

**字段说明**:
- `agent_id`: 全局唯一的 Agent 实例标识，格式：`{agent_type}_{task_id}`
- `agent_type`: Agent 类型，如 `DevAgent`、`PMAgent`
- `agent_version`: Agent 版本，建议使用语义化版本
- `session_id`: 会话 ID，对应 adeworker 的 `user_session_id`
- `user_id`: 用户 ID
- `task_id`: 任务 ID，对应 adeworker 的任务标识
- `workspace_path`: 代码仓库路径
- `start_time`: Agent 启动时间（秒级 Unix timestamp）
- `metadata`: 自定义元数据，如任务描述、优先级等

**示例**:
```python
context = AgentContext(
    agent_id="DevAgent_task_12345",
    agent_type="DevAgent",
    agent_version="1.0.0",
    session_id="session_abc",
    user_id="user_001",
    task_id="task_12345",
    workspace_path="/home/user/workspace/my_project",
    start_time=1706400000.0,
    metadata={
        'task_desc': 'Implement user authentication',
        'priority': 'high'
    }
)
```

---

### 2.4 NodeContext

**描述**: LangGraph 节点上下文

**定义**:
```python
class NodeContext(BaseModel):
    node_name: str                   # 节点名称
    start_time: float                # 开始时间
    input_state: Dict[str, Any]      # 输入状态（简化版）
```

**示例**:
```python
node_context = NodeContext(
    node_name="gen_code",
    start_time=1706400010.0,
    input_state={
        'requirement_doc': {...},
        'solution_doc': {...}
    }
)
```

---

### 2.5 LLMContext

**描述**: LLM 调用上下文

**定义**:
```python
class LLMContext(BaseModel):
    model_name: str         # 模型名称
    prompt: str             # Prompt（可能被脱敏）
    temperature: float      # Temperature 参数
    max_tokens: int         # 最大 Token 数
    start_time: float       # 开始时间
```

**示例**:
```python
llm_context = LLMContext(
    model_name="claude-3-opus",
    prompt="请实现一个用户认证功能...",
    temperature=0.7,
    max_tokens=4096,
    start_time=1706400015.0
)
```

---

### 2.6 ToolContext

**描述**: 工具调用上下文

**定义**:
```python
class ToolContext(BaseModel):
    tool_name: str                  # 工具名称
    tool_input: Dict[str, Any]      # 工具输入参数
    start_time: float               # 开始时间
```

**示例**:
```python
tool_context = ToolContext(
    tool_name="execute_bash",
    tool_input={'command': 'ls -la'},
    start_time=1706400020.0
)
```

---

## 3. Plugin Base API

### 3.1 BasePlugin (抽象基类)

**描述**: 所有插件的基类

**定义**:
```python
from abc import ABC, abstractmethod

class BasePlugin(ABC):
    def __init__(self, config: Optional[PluginConfig] = None):
        """
        初始化插件

        Args:
            config: 插件配置，如果为 None 则使用默认配置
        """
        pass

    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """
        返回插件元信息

        Returns:
            PluginMetadata: 插件元信息
        """
        pass

    # ===== 生命周期钩子 =====

    async def on_agent_start(self, context: AgentContext) -> None:
        """
        Agent 启动时触发

        Args:
            context: Agent 上下文
        """
        pass

    async def on_agent_end(
        self,
        context: AgentContext,
        result: Any,
        error: Optional[Exception] = None
    ) -> None:
        """
        Agent 结束时触发

        Args:
            context: Agent 上下文
            result: Agent 执行结果（可能为 None）
            error: 如果发生异常，则为异常对象
        """
        pass

    async def on_node_start(
        self,
        agent_context: AgentContext,
        node_context: NodeContext
    ) -> None:
        """
        节点开始时触发

        Args:
            agent_context: Agent 上下文
            node_context: 节点上下文
        """
        pass

    async def on_node_end(
        self,
        agent_context: AgentContext,
        node_context: NodeContext,
        output_state: Dict[str, Any],
        error: Optional[Exception] = None
    ) -> None:
        """
        节点结束时触发

        Args:
            agent_context: Agent 上下文
            node_context: 节点上下文
            output_state: 节点输出状态
            error: 如果发生异常，则为异常对象
        """
        pass

    async def on_llm_start(
        self,
        agent_context: AgentContext,
        llm_context: LLMContext
    ) -> None:
        """
        LLM 调用开始时触发

        Args:
            agent_context: Agent 上下文
            llm_context: LLM 上下文
        """
        pass

    async def on_llm_end(
        self,
        agent_context: AgentContext,
        llm_context: LLMContext,
        response: str,
        token_usage: Dict[str, int],
        error: Optional[Exception] = None
    ) -> None:
        """
        LLM 调用结束时触发

        Args:
            agent_context: Agent 上下文
            llm_context: LLM 上下文
            response: LLM 响应文本
            token_usage: Token 使用情况，如 {'prompt_tokens': 100, 'completion_tokens': 50}
            error: 如果发生异常，则为异常对象
        """
        pass

    async def on_tool_call(
        self,
        agent_context: AgentContext,
        tool_context: ToolContext,
        result: Any,
        error: Optional[Exception] = None
    ) -> None:
        """
        工具调用时触发

        Args:
            agent_context: Agent 上下文
            tool_context: 工具上下文
            result: 工具执行结果
            error: 如果发生异常，则为异常对象
        """
        pass

    async def on_state_update(
        self,
        agent_context: AgentContext,
        old_state: Dict[str, Any],
        new_state: Dict[str, Any]
    ) -> None:
        """
        状态更新时触发

        Args:
            agent_context: Agent 上下文
            old_state: 旧状态
            new_state: 新状态
        """
        pass

    async def on_error(
        self,
        agent_context: AgentContext,
        error: Exception,
        error_context: Dict[str, Any]
    ) -> None:
        """
        错误发生时触发

        Args:
            agent_context: Agent 上下文
            error: 异常对象
            error_context: 错误上下文（如发生错误的位置）
        """
        pass

    # ===== 辅助方法 =====

    def should_process(self) -> bool:
        """
        判断是否应该处理当前事件（考虑采样率）

        Returns:
            bool: True 表示应该处理，False 表示跳过
        """
        pass

    async def cleanup(self) -> None:
        """
        清理资源（插件卸载时调用）
        """
        pass
```

**使用示例**:
```python
class MyCustomPlugin(BasePlugin):
    """自定义插件示例"""

    def __init__(self, config: Optional[PluginConfig] = None):
        super().__init__(config)
        self.event_count = 0

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            id="my_custom_plugin",
            name="My Custom Plugin",
            version="1.0.0",
            description="Counts agent events",
            author="John Doe"
        )

    async def on_agent_start(self, context: AgentContext) -> None:
        """记录 Agent 启动事件"""
        self.event_count += 1
        print(f"Agent started: {context.agent_type}, total events: {self.event_count}")

    async def on_agent_end(
        self,
        context: AgentContext,
        result: Any,
        error: Optional[Exception] = None
    ) -> None:
        """记录 Agent 结束事件"""
        status = "success" if error is None else "failed"
        print(f"Agent {context.agent_type} {status}")

    async def cleanup(self) -> None:
        """清理资源"""
        print(f"Plugin cleanup, total events processed: {self.event_count}")
```

---

## 4. Plugin Manager API

### 4.1 PluginManager (单例)

**描述**: 插件管理器，负责插件的注册、卸载、启用、禁用及钩子触发

**获取实例**:
```python
from agenteval_plugin.core.plugin_manager import plugin_manager
```

---

### 4.2 register_plugin()

**签名**:
```python
def register_plugin(self, plugin: BasePlugin) -> None:
    """
    注册插件

    Args:
        plugin: 插件实例

    Raises:
        ValueError: 如果插件 ID 已存在（会覆盖）
    """
```

**示例**:
```python
from agenteval_plugin.core.plugin_manager import plugin_manager

plugin = MyCustomPlugin()
plugin_manager.register_plugin(plugin)
```

---

### 4.3 unregister_plugin()

**签名**:
```python
def unregister_plugin(self, plugin_id: str) -> None:
    """
    注销插件

    Args:
        plugin_id: 插件 ID

    Note:
        会自动调用插件的 cleanup() 方法
    """
```

**示例**:
```python
plugin_manager.unregister_plugin("my_custom_plugin")
```

---

### 4.4 enable_plugin()

**签名**:
```python
def enable_plugin(self, plugin_id: str) -> None:
    """
    启用插件

    Args:
        plugin_id: 插件 ID

    Raises:
        ValueError: 如果插件未注册
    """
```

**示例**:
```python
plugin_manager.enable_plugin("my_custom_plugin")
```

---

### 4.5 disable_plugin()

**签名**:
```python
def disable_plugin(self, plugin_id: str) -> None:
    """
    禁用插件（不会注销）

    Args:
        plugin_id: 插件 ID
    """
```

**示例**:
```python
plugin_manager.disable_plugin("my_custom_plugin")
```

---

### 4.6 get_plugin()

**签名**:
```python
def get_plugin(self, plugin_id: str) -> Optional[BasePlugin]:
    """
    获取插件实例

    Args:
        plugin_id: 插件 ID

    Returns:
        Optional[BasePlugin]: 插件实例，如果不存在则返回 None
    """
```

**示例**:
```python
plugin = plugin_manager.get_plugin("my_custom_plugin")
if plugin:
    print(f"Plugin enabled: {plugin.config.enabled}")
```

---

### 4.7 get_active_plugins()

**签名**:
```python
def get_active_plugins(self) -> List[BasePlugin]:
    """
    获取所有激活的插件

    Returns:
        List[BasePlugin]: 激活的插件列表
    """
```

**示例**:
```python
active_plugins = plugin_manager.get_active_plugins()
print(f"Active plugins: {[p.metadata.name for p in active_plugins]}")
```

---

### 4.8 触发钩子方法

**说明**: 以下方法由装饰器或框架自动调用，一般不需要手动调用

```python
async def trigger_agent_start(self, context: AgentContext) -> None:
    """触发 on_agent_start 钩子"""

async def trigger_agent_end(
    self,
    context: AgentContext,
    result: Any,
    error: Optional[Exception] = None
) -> None:
    """触发 on_agent_end 钩子"""

async def trigger_node_start(
    self,
    agent_context: AgentContext,
    node_context: NodeContext
) -> None:
    """触发 on_node_start 钩子"""

async def trigger_node_end(
    self,
    agent_context: AgentContext,
    node_context: NodeContext,
    output_state: Dict[str, Any],
    error: Optional[Exception] = None
) -> None:
    """触发 on_node_end 钩子"""

async def trigger_llm_start(
    self,
    agent_context: AgentContext,
    llm_context: LLMContext
) -> None:
    """触发 on_llm_start 钩子"""

async def trigger_llm_end(
    self,
    agent_context: AgentContext,
    llm_context: LLMContext,
    response: str,
    token_usage: Dict[str, int],
    error: Optional[Exception] = None
) -> None:
    """触发 on_llm_end 钩子"""

# ... 其他触发方法
```

---

## 5. 装饰器 API

### 5.1 @instrument_agent()

**描述**: 装饰 Agent 的 `arun()` 或 `astream_run()` 方法

**签名**:
```python
def instrument_agent(
    agent_type: str,
    agent_version: str = "1.0.0"
) -> Callable:
    """
    装饰 Agent 方法

    Args:
        agent_type: Agent 类型名称
        agent_version: Agent 版本

    Returns:
        装饰器函数
    """
```

**使用示例**:
```python
from agenteval_plugin.decorators import instrument_agent

class DevAgent:
    @instrument_agent(agent_type="DevAgent", agent_version="1.0.0")
    async def arun(self, user_input):
        # Agent 逻辑
        return result

    @instrument_agent(agent_type="DevAgent", agent_version="1.0.0")
    async def astream_run(self, user_input):
        # 流式输出
        for item in results:
            yield item
```

**注意事项**:
- 装饰器会自动创建 `AgentContext`
- 会在方法执行前后触发 `on_agent_start` 和 `on_agent_end`
- 支持流式输出（async generator）
- 异常会被捕获并传递给插件，但不会被吞掉

---

### 5.2 @instrument_node()

**描述**: 装饰 LangGraph 节点方法

**签名**:
```python
def instrument_node(node_name: str) -> Callable:
    """
    装饰节点方法

    Args:
        node_name: 节点名称

    Returns:
        装饰器函数
    """
```

**使用示例**:
```python
from agenteval_plugin.decorators import instrument_node

class DevAgent:
    @instrument_node(node_name="prepare_context")
    def _node_prepare_context(self, state):
        # 节点逻辑
        return updated_state

    @instrument_node(node_name="gen_code")
    async def _node_gen_code(self, state):
        # 异步节点
        return updated_state
```

**注意事项**:
- 需要从 `state` 中提取 `_agent_context`（由 `@instrument_agent` 注入）
- 支持同步和异步方法
- 会触发 `on_node_start` 和 `on_node_end`

---

### 5.3 @instrument_llm_call()

**描述**: 装饰 LLM 调用方法（可选）

**签名**:
```python
def instrument_llm_call() -> Callable:
    """
    装饰 LLM 调用方法

    Returns:
        装饰器函数
    """
```

**使用示例**:
```python
from agenteval_plugin.decorators import instrument_llm_call

class MyAgent:
    @instrument_llm_call()
    async def call_llm(self, prompt, **kwargs):
        response = await self.llm.ainvoke(prompt, **kwargs)
        return response
```

**注意事项**:
- 对于 LangChain，推荐使用 Callbacks 机制而非此装饰器

---

## 6. Trace Collector API

### 6.1 TraceCollector

**描述**: 轨迹收集器，负责批量上报 Trace 数据

**获取实例**:
```python
from agenteval_plugin.trace.trace_collector import get_trace_collector

config = {
    'enabled': True,
    'endpoint': 'http://localhost:8000/api/v1/traces',
    'batch': {'max_size': 100, 'max_wait_seconds': 1.0}
}
collector = get_trace_collector(config)
```

---

### 6.2 start()

**签名**:
```python
async def start(self) -> None:
    """
    启动收集器（启动后台线程）
    """
```

**示例**:
```python
await collector.start()
```

---

### 6.3 stop()

**签名**:
```python
async def stop(self) -> None:
    """
    停止收集器（清空队列并关闭）
    """
```

**示例**:
```python
await collector.stop()
```

---

### 6.4 collect()

**签名**:
```python
async def collect(self, event: TraceEvent) -> None:
    """
    收集事件（非阻塞）

    Args:
        event: Trace 事件

    Note:
        如果队列满，会丢弃事件并记录警告日志
    """
```

**示例**:
```python
from agenteval_plugin.trace.trace_collector import TraceEvent

event = TraceEvent(
    trace_id="trace-123",
    span_id="span-456",
    parent_span_id=None,
    name="agent.start",
    start_time=time.time(),
    end_time=None,
    attributes={'agent_type': 'DevAgent'},
    events=[],
    status='ok'
)

await collector.collect(event)
```

---

### 6.5 TraceEvent

**定义**:
```python
@dataclass
class TraceEvent:
    trace_id: str                       # Trace ID (UUID)
    span_id: str                        # Span ID (UUID)
    parent_span_id: Optional[str]       # 父 Span ID
    name: str                           # 事件名称
    start_time: float                   # 开始时间
    end_time: Optional[float]           # 结束时间
    attributes: Dict[str, Any]          # 属性字典
    events: List[Dict[str, Any]]        # 事件列表
    status: str = "ok"                  # 状态（ok / error）
```

---

## 7. Session Mapper API

### 7.1 SessionMapper

**描述**: Session 与 Trace 的映射器

**获取实例**:
```python
from agenteval_plugin.session.session_mapper import session_mapper
```

---

### 7.2 create_mapping()

**签名**:
```python
def create_mapping(
    self,
    user_session_id: str,
    agent_session_id: str,
    trace_id: str,
    user_id: str,
    task_id: str,
    workspace_path: str,
    created_at: float
) -> SessionMapping:
    """
    创建 Session 映射

    Args:
        user_session_id: 用户会话 ID
        agent_session_id: Agent 会话 ID
        trace_id: Trace ID
        user_id: 用户 ID
        task_id: 任务 ID
        workspace_path: 工作空间路径
        created_at: 创建时间

    Returns:
        SessionMapping: 映射对象
    """
```

**示例**:
```python
mapping = session_mapper.create_mapping(
    user_session_id="session_abc",
    agent_session_id="agent_session_xyz",
    trace_id="trace-123",
    user_id="user_001",
    task_id="task_12345",
    workspace_path="/home/user/workspace",
    created_at=time.time()
)
```

---

### 7.3 get_mapping()

**签名**:
```python
def get_mapping(self, session_id: str) -> Optional[SessionMapping]:
    """
    获取映射（支持 user_session_id 或 agent_session_id）

    Args:
        session_id: 会话 ID

    Returns:
        Optional[SessionMapping]: 映射对象，如果不存在则返回 None
    """
```

**示例**:
```python
mapping = session_mapper.get_mapping("session_abc")
if mapping:
    print(f"Trace ID: {mapping.trace_id}")
```

---

### 7.4 get_trace_id()

**签名**:
```python
def get_trace_id(self, session_id: str) -> Optional[str]:
    """
    根据 session_id 获取 trace_id

    Args:
        session_id: 会话 ID

    Returns:
        Optional[str]: Trace ID，如果不存在则返回 None
    """
```

**示例**:
```python
trace_id = session_mapper.get_trace_id("session_abc")
```

---

## 8. 工具类 API

### 8.1 DataRedactor (数据脱敏)

**描述**: 数据脱敏工具

**引入**:
```python
from agenteval_plugin.privacy.redactor import DataRedactor
```

---

#### 8.1.1 redact_text()

**签名**:
```python
@classmethod
def redact_text(cls, text: str) -> str:
    """
    文本脱敏

    Args:
        text: 原始文本

    Returns:
        str: 脱敏后的文本
    """
```

**示例**:
```python
text = "My API key is sk-1234567890abcdefghijklmnopqrstuv"
redacted = DataRedactor.redact_text(text)
# 输出: "My API key is sk-***REDACTED***"
```

---

#### 8.1.2 redact_dict()

**签名**:
```python
@classmethod
def redact_dict(cls, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    字典脱敏

    Args:
        data: 原始字典

    Returns:
        Dict[str, Any]: 脱敏后的字典
    """
```

**示例**:
```python
data = {
    'username': 'john',
    'password': 'secret123',
    'api_key': 'sk-xxxxx'
}
redacted = DataRedactor.redact_dict(data)
# 输出: {'username': 'john', 'password': '***REDACTED***', 'api_key': '***REDACTED***'}
```

---

### 8.2 AsyncHTTPClient

**描述**: 异步 HTTP 客户端

**引入**:
```python
from agenteval_plugin.utils.http_client import AsyncHTTPClient
```

**初始化**:
```python
client = AsyncHTTPClient(
    base_url="http://localhost:8000",
    api_key="your-api-key",
    timeout=30
)
```

---

#### 8.2.1 post()

**签名**:
```python
async def post(
    self,
    path: str,
    data: Any,
    headers: Optional[Dict[str, str]] = None
) -> Any:
    """
    POST 请求

    Args:
        path: API 路径
        data: 请求数据
        headers: 额外的请求头

    Returns:
        响应对象

    Raises:
        RuntimeError: 如果所有重试都失败
    """
```

**示例**:
```python
response = await client.post(
    '/api/v1/traces',
    data={'traces': [...]},
    headers={'Content-Encoding': 'gzip'}
)
```

---

## 9. 配置 API

### 9.1 init_agenteval_plugin()

**描述**: 初始化插件系统

**签名**:
```python
def init_agenteval_plugin(
    config: Optional[PluginConfig] = None,
    config_file: Optional[str] = None
) -> None:
    """
    初始化 AgentEval Plugin

    Args:
        config: PluginConfig 对象
        config_file: 配置文件路径（YAML 格式）

    Note:
        config 和 config_file 至少提供一个
    """
```

**示例**:
```python
# 方式 1: 使用配置对象
from agenteval_plugin import init_agenteval_plugin, PluginConfig

config = PluginConfig(enabled=True)
init_agenteval_plugin(config)

# 方式 2: 使用配置文件
init_agenteval_plugin(config_file='./agenteval_plugin.yaml')
```

---

### 9.2 配置文件格式

**文件名**: `agenteval_plugin.yaml`

**示例**:
```yaml
# 全局配置
global:
  enabled: true
  log_level: INFO

# Trace Collector 配置
trace_collector:
  enabled: true
  endpoint: "http://localhost:8000/api/v1/traces"
  api_key: "${AGENTEVAL_API_KEY}"

  batch:
    max_size: 100
    max_wait_seconds: 1.0
    max_queue_size: 10000

  retry:
    max_attempts: 3
    backoff_factor: 2.0
    max_backoff_seconds: 60

  sampling:
    rate: 1.0
    rules:
      - condition: "error == true"
        rate: 1.0
      - condition: "duration > 60"
        rate: 1.0

  local_cache:
    enabled: true
    cache_dir: /tmp/agenteval_cache
    max_size_mb: 1000

# 数据脱敏配置
privacy:
  enabled: true
  sensitive_fields:
    - password
    - token
    - api_key
  redact_patterns:
    - pattern: "sk-[a-zA-Z0-9]{32,}"
      replacement: "sk-***REDACTED***"

# 性能优化配置
performance:
  async_mode: true
  use_compression: true
```

---

## 10. 示例代码

### 10.1 完整的自定义插件示例

```python
# custom_metrics_plugin.py

from agenteval_plugin.core.plugin_base import (
    BasePlugin, PluginMetadata, PluginConfig,
    AgentContext, NodeContext
)
from typing import Optional, Any, Dict
import time

class CustomMetricsPlugin(BasePlugin):
    """自定义指标插件"""

    def __init__(self, config: Optional[PluginConfig] = None):
        super().__init__(config)

        # 指标存储
        self.metrics = {
            'total_agents': 0,
            'total_nodes': 0,
            'total_duration': 0.0,
            'error_count': 0
        }

        # 活跃的 Agent（用于计算持续时间）
        self.active_agents: Dict[str, float] = {}

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            id="custom_metrics_plugin",
            name="Custom Metrics Plugin",
            version="1.0.0",
            description="Collects custom metrics for agent execution",
            author="Your Name",
            dependencies=[]
        )

    async def on_agent_start(self, context: AgentContext) -> None:
        """Agent 启动：记录启动时间"""
        self.metrics['total_agents'] += 1
        self.active_agents[context.agent_id] = context.start_time
        print(f"[Metrics] Agent started: {context.agent_id}")

    async def on_agent_end(
        self,
        context: AgentContext,
        result: Any,
        error: Optional[Exception] = None
    ) -> None:
        """Agent 结束：计算持续时间"""
        start_time = self.active_agents.pop(context.agent_id, None)
        if start_time:
            duration = time.time() - start_time
            self.metrics['total_duration'] += duration
            print(f"[Metrics] Agent ended: {context.agent_id}, duration: {duration:.2f}s")

        if error:
            self.metrics['error_count'] += 1
            print(f"[Metrics] Agent failed: {context.agent_id}, error: {error}")

    async def on_node_start(
        self,
        agent_context: AgentContext,
        node_context: NodeContext
    ) -> None:
        """节点启动：计数"""
        self.metrics['total_nodes'] += 1

    async def cleanup(self) -> None:
        """清理：打印汇总指标"""
        print("\n" + "="*60)
        print("CUSTOM METRICS SUMMARY")
        print("="*60)
        print(f"Total Agents: {self.metrics['total_agents']}")
        print(f"Total Nodes: {self.metrics['total_nodes']}")
        print(f"Total Duration: {self.metrics['total_duration']:.2f}s")
        print(f"Error Count: {self.metrics['error_count']}")
        if self.metrics['total_agents'] > 0:
            avg_duration = self.metrics['total_duration'] / self.metrics['total_agents']
            print(f"Average Duration: {avg_duration:.2f}s")
        print("="*60)

# 使用示例
if __name__ == "__main__":
    from agenteval_plugin.core.plugin_manager import plugin_manager

    # 注册插件
    plugin = CustomMetricsPlugin()
    plugin_manager.register_plugin(plugin)

    # ... 运行 Agent ...

    # 清理
    await plugin.cleanup()
```

---

### 10.2 集成到 adeworker 的完整示例

```python
# adeworker/backend/worker/infra/startup/startup.py

import os
from agenteval_plugin import init_agenteval_plugin
from agenteval_plugin.plugins.evaluation_plugin import EvaluationPlugin
from agenteval_plugin.core.plugin_manager import plugin_manager

async def startup():
    """应用启动函数"""

    # ... 其他启动逻辑 ...

    # 初始化 AgentEval Plugin
    if os.getenv('AGENTEVAL_ENABLED', 'false').lower() == 'true':
        print("Initializing AgentEval Plugin...")

        # 从配置文件初始化
        config_file = os.getenv('AGENTEVAL_CONFIG_FILE', '/etc/agenteval/config.yaml')
        init_agenteval_plugin(config_file=config_file)

        # 注册 EvaluationPlugin
        plugin_manager.register_plugin(EvaluationPlugin())

        print("AgentEval Plugin initialized successfully!")

# adeworker/backend/worker/agent/dev_agent/agent.py

from agenteval_plugin.decorators import instrument_agent, instrument_node

class BaseDevAgent(BaseAgent):
    """开发 Agent"""

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

    @instrument_node(node_name="prepare_context")
    def _node_prepare_context(self, state: DevState) -> DevState:
        """准备上下文"""
        # ... 原有逻辑 ...
        return state

    @instrument_node(node_name="understand_repo")
    def _node_understand_repo(self, state: DevState) -> DevState:
        """理解代码仓库"""
        # ... 原有逻辑 ...
        return state

    @instrument_node(node_name="gen_requirement")
    def _node_gen_requirement(self, state: DevState) -> DevState:
        """生成需求文档"""
        # ... 原有逻辑 ...
        return state

    # ... 其他节点方法装饰 ...
```

---

## 附录

### A. 钩子触发顺序

```
Agent Execution Flow:
  ├─ on_agent_start
  │
  ├─ on_node_start (prepare_context)
  │   ├─ on_llm_start (如果调用 LLM)
  │   ├─ on_llm_end
  │   └─ on_node_end
  │
  ├─ on_node_start (understand_repo)
  │   ├─ on_llm_start
  │   ├─ on_llm_end
  │   ├─ on_tool_call (FileReader)
  │   └─ on_node_end
  │
  ├─ on_node_start (gen_requirement)
  │   └─ on_node_end
  │
  ├─ on_node_start (gen_code)
  │   └─ on_node_end
  │
  └─ on_agent_end
```

### B. 性能优化建议

1. **启用异步模式**: `async_mode=True` (默认)
2. **调整采样率**: 生产环境建议 `sampling_rate=0.1` (10%)
3. **增加批量大小**: `batch.max_size=200` (减少网络请求)
4. **启用压缩**: `performance.use_compression=true`
5. **使用本地缓存**: 防止数据丢失

### C. 故障排查

**问题：插件未生效**
- 检查 `AGENTEVAL_ENABLED` 环境变量
- 检查配置文件路径
- 查看日志：`tail -f /var/log/agenteval/plugin.log`

**问题：性能开销过大**
- 降低采样率：`sampling_rate=0.1`
- 检查是否启用了 `async_mode`
- 检查批量上报配置

**问题：数据未上报**
- 检查网络连接
- 查看本地缓存：`ls /tmp/agenteval_cache`
- 检查 API Key 是否正确

---

**文档结束**
