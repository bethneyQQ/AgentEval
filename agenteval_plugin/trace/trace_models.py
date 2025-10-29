"""
Trace Data Models

Defines the data structures for trace collection following OpenTelemetry-like conventions.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from dataclasses import dataclass, asdict


@dataclass
class TraceEvent:
    """Trace event for agent execution"""
    trace_id: str  # UUID for the entire agent execution
    span_id: str  # UUID for this specific operation
    parent_span_id: Optional[str]  # Parent span ID for nested operations
    name: str  # Event name (e.g., "agent.start", "node.gen_code")
    start_time: float  # Unix timestamp
    end_time: Optional[float]  # Unix timestamp (None if not completed)
    attributes: Dict[str, Any]  # Key-value attributes
    events: List[Dict[str, Any]]  # List of sub-events
    status: str = "ok"  # "ok" or "error"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


class SpanAttributes(BaseModel):
    """Span attributes following semantic conventions"""
    # Agent related
    agent_id: Optional[str] = None
    agent_type: Optional[str] = None
    agent_version: Optional[str] = None

    # Session related
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    task_id: Optional[str] = None
    workspace_path: Optional[str] = None

    # Node related
    node_name: Optional[str] = None

    # LLM related
    llm_model: Optional[str] = None
    llm_temperature: Optional[float] = None
    llm_max_tokens: Optional[int] = None
    llm_prompt_length: Optional[int] = None
    llm_response_length: Optional[int] = None
    llm_token_usage: Optional[Dict[str, int]] = None

    # Performance related
    duration: Optional[float] = None
    status: Optional[str] = None

    # Custom attributes
    extra: Dict[str, Any] = Field(default_factory=dict)


class SpanEvent(BaseModel):
    """Span event"""
    name: str
    timestamp: float
    attributes: Dict[str, Any] = Field(default_factory=dict)


class Span(BaseModel):
    """Span representing a unit of work"""
    span_id: str
    trace_id: str
    parent_span_id: Optional[str] = None
    name: str
    start_time: float
    end_time: Optional[float] = None
    attributes: SpanAttributes
    events: List[SpanEvent] = Field(default_factory=list)
    status: str = "ok"  # ok, error


class Trace(BaseModel):
    """Trace representing entire agent execution"""
    trace_id: str
    spans: List[Span]
    start_time: float
    end_time: Optional[float] = None
    status: str = "ok"
