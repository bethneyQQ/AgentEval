"""
Session Mapper

Maps ADEWorker sessions to AgentEval traces.
"""

from typing import Dict, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class SessionMapping:
    """Session to trace mapping"""
    user_session_id: str
    agent_session_id: str
    trace_id: str
    user_id: str
    task_id: str
    workspace_path: str
    created_at: float


class SessionMapper:
    """Maps sessions to traces"""

    def __init__(self):
        self._mappings: Dict[str, SessionMapping] = {}
        logger.info("SessionMapper initialized")

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
        """Create a new session mapping"""
        mapping = SessionMapping(
            user_session_id=user_session_id,
            agent_session_id=agent_session_id,
            trace_id=trace_id,
            user_id=user_id,
            task_id=task_id,
            workspace_path=workspace_path,
            created_at=created_at
        )

        # Store by both session IDs
        self._mappings[user_session_id] = mapping
        self._mappings[agent_session_id] = mapping

        logger.debug(f"Created session mapping: {user_session_id} -> {trace_id}")
        return mapping

    def get_mapping(self, session_id: str) -> Optional[SessionMapping]:
        """Get mapping by session ID"""
        return self._mappings.get(session_id)

    def get_trace_id(self, session_id: str) -> Optional[str]:
        """Get trace ID by session ID"""
        mapping = self.get_mapping(session_id)
        return mapping.trace_id if mapping else None

    def remove_mapping(self, session_id: str) -> None:
        """Remove mapping by session ID"""
        if session_id in self._mappings:
            mapping = self._mappings[session_id]
            # Remove both entries
            self._mappings.pop(mapping.user_session_id, None)
            self._mappings.pop(mapping.agent_session_id, None)
            logger.debug(f"Removed session mapping: {session_id}")

    def get_all_mappings(self) -> Dict[str, SessionMapping]:
        """Get all mappings"""
        # Return unique mappings (deduplicate by trace_id)
        unique = {}
        for mapping in self._mappings.values():
            unique[mapping.trace_id] = mapping
        return unique


# Global singleton
session_mapper = SessionMapper()
