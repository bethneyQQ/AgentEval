"""
Evaluation Plugin

Core plugin for collecting agent execution traces.
"""

import time
import uuid
from typing import Any, Dict, Optional
import logging

from ..core.plugin_base import (
    BasePlugin, PluginMetadata, PluginConfig,
    AgentContext, NodeContext, LLMContext, ToolContext
)
from ..trace.trace_models import TraceEvent
from ..trace.trace_collector import get_trace_collector
from ..session.session_mapper import session_mapper

logger = logging.getLogger(__name__)


class EvaluationPlugin(BasePlugin):
    """Core evaluation plugin for trace collection"""

    def __init__(self, config: Optional[PluginConfig] = None):
        super().__init__(config)
        self.trace_collector = None  # Will be initialized lazily

        # Track active traces and spans
        self.active_traces: Dict[str, str] = {}  # task_id -> trace_id
        self.active_spans: Dict[str, str] = {}   # span_key -> span_id
        self.trace_start_times: Dict[str, float] = {}  # trace_id -> start_time

    def _ensure_collector(self):
        """Ensure trace collector is initialized"""
        if self.trace_collector is None:
            try:
                self.trace_collector = get_trace_collector()
            except ValueError:
                logger.warning("TraceCollector not initialized, traces will not be collected")

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            id="evaluation_plugin",
            name="AgentEval Evaluation Plugin",
            version="1.0.0",
            description="Collects agent execution traces for evaluation",
            author="AgentEval Team",
            dependencies=[]
        )

    async def on_agent_start(self, context: AgentContext) -> None:
        """Agent start event"""
        self._ensure_collector()
        if not self.trace_collector:
            return

        trace_id = str(uuid.uuid4())
        self.active_traces[context.task_id] = trace_id
        self.trace_start_times[trace_id] = context.start_time

        # Create session mapping
        session_mapper.create_mapping(
            user_session_id=context.session_id,
            agent_session_id=context.session_id,  # Same in this case
            trace_id=trace_id,
            user_id=context.user_id,
            task_id=context.task_id,
            workspace_path=context.workspace_path,
            created_at=context.start_time
        )

        event = TraceEvent(
            trace_id=trace_id,
            span_id=str(uuid.uuid4()),
            parent_span_id=None,
            name=f"agent.{context.agent_type}.start",
            start_time=context.start_time,
            end_time=None,
            attributes={
                'agent.id': context.agent_id,
                'agent.type': context.agent_type,
                'agent.version': context.agent_version,
                'session.id': context.session_id,
                'user.id': context.user_id,
                'task.id': context.task_id,
                'workspace.path': context.workspace_path,
                **context.metadata
            },
            events=[
                {
                    'name': 'agent.started',
                    'timestamp': context.start_time,
                    'attributes': {}
                }
            ],
            status='ok'
        )

        await self.trace_collector.collect(event)
        logger.debug(f"Agent started: trace_id={trace_id}, task_id={context.task_id}")

    async def on_agent_end(
        self,
        context: AgentContext,
        result: Any,
        error: Optional[Exception] = None
    ) -> None:
        """Agent end event"""
        self._ensure_collector()
        if not self.trace_collector:
            return

        trace_id = self.active_traces.get(context.task_id)
        if not trace_id:
            logger.warning(f"No active trace for task {context.task_id}")
            return

        end_time = time.time()
        start_time = self.trace_start_times.get(trace_id, context.start_time)
        duration = end_time - start_time

        event = TraceEvent(
            trace_id=trace_id,
            span_id=str(uuid.uuid4()),
            parent_span_id=None,
            name=f"agent.{context.agent_type}.end",
            start_time=start_time,
            end_time=end_time,
            attributes={
                'agent.id': context.agent_id,
                'agent.type': context.agent_type,
                'duration': duration,
                'status': 'error' if error else 'success',
                'error': str(error) if error else None
            },
            events=[
                {
                    'name': 'agent.completed' if not error else 'agent.failed',
                    'timestamp': end_time,
                    'attributes': {
                        'error': str(error) if error else None
                    }
                }
            ],
            status='error' if error else 'ok'
        )

        await self.trace_collector.collect(event)

        # Cleanup
        del self.active_traces[context.task_id]
        del self.trace_start_times[trace_id]

        logger.debug(f"Agent ended: trace_id={trace_id}, duration={duration:.2f}s, status={'error' if error else 'ok'}")

    async def on_node_start(
        self,
        agent_context: AgentContext,
        node_context: NodeContext
    ) -> None:
        """Node start event"""
        self._ensure_collector()
        if not self.trace_collector:
            return

        trace_id = self.active_traces.get(agent_context.task_id)
        if not trace_id:
            return

        span_id = str(uuid.uuid4())
        span_key = f"{agent_context.task_id}_{node_context.node_name}"
        self.active_spans[span_key] = span_id

        event = TraceEvent(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=None,
            name=f"node.{node_context.node_name}.start",
            start_time=node_context.start_time,
            end_time=None,
            attributes={
                'node.name': node_context.node_name,
                'task.id': agent_context.task_id,
                'input_state_keys': list(node_context.input_state.keys())
            },
            events=[
                {
                    'name': 'node.started',
                    'timestamp': node_context.start_time,
                    'attributes': {}
                }
            ],
            status='ok'
        )

        await self.trace_collector.collect(event)
        logger.debug(f"Node started: {node_context.node_name}")

    async def on_node_end(
        self,
        agent_context: AgentContext,
        node_context: NodeContext,
        output_state: Dict[str, Any],
        error: Optional[Exception] = None
    ) -> None:
        """Node end event"""
        self._ensure_collector()
        if not self.trace_collector:
            return

        trace_id = self.active_traces.get(agent_context.task_id)
        span_key = f"{agent_context.task_id}_{node_context.node_name}"
        span_id = self.active_spans.get(span_key)

        if not trace_id or not span_id:
            return

        end_time = time.time()
        duration = end_time - node_context.start_time

        event = TraceEvent(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=None,
            name=f"node.{node_context.node_name}.end",
            start_time=node_context.start_time,
            end_time=end_time,
            attributes={
                'node.name': node_context.node_name,
                'duration': duration,
                'output_state_keys': list(output_state.keys()) if output_state else [],
                'status': 'error' if error else 'success',
                'error': str(error) if error else None
            },
            events=[
                {
                    'name': 'node.completed' if not error else 'node.failed',
                    'timestamp': end_time,
                    'attributes': {
                        'error': str(error) if error else None
                    }
                }
            ],
            status='error' if error else 'ok'
        )

        await self.trace_collector.collect(event)

        # Cleanup
        del self.active_spans[span_key]

        logger.debug(f"Node ended: {node_context.node_name}, duration={duration:.2f}s")

    async def on_llm_start(
        self,
        agent_context: AgentContext,
        llm_context: LLMContext
    ) -> None:
        """LLM call start event"""
        self._ensure_collector()
        if not self.trace_collector:
            return

        trace_id = self.active_traces.get(agent_context.task_id)
        if not trace_id:
            return

        event = TraceEvent(
            trace_id=trace_id,
            span_id=str(uuid.uuid4()),
            parent_span_id=None,
            name="llm.call.start",
            start_time=llm_context.start_time,
            end_time=None,
            attributes={
                'llm.model': llm_context.model_name,
                'llm.temperature': llm_context.temperature,
                'llm.max_tokens': llm_context.max_tokens,
                'llm.prompt_length': len(llm_context.prompt)
            },
            events=[
                {
                    'name': 'llm.started',
                    'timestamp': llm_context.start_time,
                    'attributes': {}
                }
            ],
            status='ok'
        )

        await self.trace_collector.collect(event)

    async def on_llm_end(
        self,
        agent_context: AgentContext,
        llm_context: LLMContext,
        response: str,
        token_usage: Dict[str, int],
        error: Optional[Exception] = None
    ) -> None:
        """LLM call end event"""
        self._ensure_collector()
        if not self.trace_collector:
            return

        trace_id = self.active_traces.get(agent_context.task_id)
        if not trace_id:
            return

        end_time = time.time()
        duration = end_time - llm_context.start_time

        event = TraceEvent(
            trace_id=trace_id,
            span_id=str(uuid.uuid4()),
            parent_span_id=None,
            name="llm.call.end",
            start_time=llm_context.start_time,
            end_time=end_time,
            attributes={
                'llm.model': llm_context.model_name,
                'llm.duration': duration,
                'llm.response_length': len(response) if response else 0,
                'llm.token_usage': token_usage,
                'status': 'error' if error else 'success',
                'error': str(error) if error else None
            },
            events=[
                {
                    'name': 'llm.completed' if not error else 'llm.failed',
                    'timestamp': end_time,
                    'attributes': {
                        'error': str(error) if error else None
                    }
                }
            ],
            status='error' if error else 'ok'
        )

        await self.trace_collector.collect(event)
        logger.debug(f"LLM call completed: model={llm_context.model_name}, duration={duration:.2f}s")

    async def cleanup(self) -> None:
        """Cleanup resources"""
        if self.trace_collector:
            await self.trace_collector.stop()
