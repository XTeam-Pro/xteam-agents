"""SessionManager - Manages collaborative sessions between humans and AI."""

import asyncio
from datetime import datetime
from uuid import UUID

import structlog

from xteam_agents.models.magic import (
    CollaborativeSession,
    HumanResponse,
    SessionStatus,
)

logger = structlog.get_logger()


class SessionManager:
    """Manages collaborative sessions with async response waiting."""

    def __init__(self) -> None:
        self._sessions: dict[UUID, CollaborativeSession] = {}
        self._task_sessions: dict[UUID, UUID] = {}  # task_id -> session_id
        self._response_events: dict[UUID, asyncio.Event] = {}  # escalation_id -> event
        self._responses: dict[UUID, HumanResponse] = {}  # escalation_id -> response

    def create_session(
        self, task_id: UUID, human_id: str = "default"
    ) -> CollaborativeSession:
        """Create a new collaborative session for a task."""
        # Return existing session if one exists
        existing_id = self._task_sessions.get(task_id)
        if existing_id and existing_id in self._sessions:
            session = self._sessions[existing_id]
            if not session.is_expired() and session.status == SessionStatus.ACTIVE:
                return session

        session = CollaborativeSession(
            task_id=task_id,
            human_id=human_id,
        )
        self._sessions[session.id] = session
        self._task_sessions[task_id] = session.id

        logger.info(
            "session_created",
            session_id=str(session.id),
            task_id=str(task_id),
        )
        return session

    def get_session(self, session_id: UUID) -> CollaborativeSession | None:
        return self._sessions.get(session_id)

    def get_session_for_task(self, task_id: UUID) -> CollaborativeSession | None:
        session_id = self._task_sessions.get(task_id)
        if session_id:
            return self._sessions.get(session_id)
        return None

    def add_message(
        self, session_id: UUID, role: str, content: str
    ) -> None:
        """Add a message to the session transcript."""
        session = self._sessions.get(session_id)
        if session:
            session.add_message(role, content)

    def submit_response(
        self, escalation_id: UUID, response: HumanResponse
    ) -> bool:
        """Submit a human response, signaling the waiting coroutine."""
        self._responses[escalation_id] = response

        event = self._response_events.get(escalation_id)
        if event:
            event.set()
            logger.info(
                "response_submitted",
                escalation_id=str(escalation_id),
                response_type=response.response_type.value,
            )
            return True

        logger.warning(
            "response_submitted_no_waiter",
            escalation_id=str(escalation_id),
        )
        return False

    async def wait_for_response(
        self, escalation_id: UUID, timeout: int = 300
    ) -> HumanResponse | None:
        """Wait asynchronously for a human response with timeout."""
        event = asyncio.Event()
        self._response_events[escalation_id] = event

        try:
            await asyncio.wait_for(event.wait(), timeout=timeout)
            response = self._responses.pop(escalation_id, None)
            return response
        except asyncio.TimeoutError:
            logger.warning(
                "response_timeout",
                escalation_id=str(escalation_id),
                timeout=timeout,
            )
            return None
        finally:
            self._response_events.pop(escalation_id, None)

    def close_session(self, session_id: UUID) -> None:
        """Close a collaborative session."""
        session = self._sessions.get(session_id)
        if session:
            session.status = SessionStatus.CLOSED
            session.updated_at = datetime.utcnow()
            logger.info("session_closed", session_id=str(session_id))

    def list_active_sessions(self) -> list[CollaborativeSession]:
        """List all active (non-expired) sessions."""
        return [
            s
            for s in self._sessions.values()
            if s.status == SessionStatus.ACTIVE and not s.is_expired()
        ]

    def cleanup_expired(self) -> int:
        """Clean up expired sessions. Returns count of cleaned sessions."""
        expired_ids = [
            sid for sid, s in self._sessions.items() if s.is_expired()
        ]
        for sid in expired_ids:
            session = self._sessions[sid]
            session.status = SessionStatus.EXPIRED
            # Remove task mapping
            task_id_to_remove = None
            for tid, s_id in self._task_sessions.items():
                if s_id == sid:
                    task_id_to_remove = tid
                    break
            if task_id_to_remove:
                del self._task_sessions[task_id_to_remove]

        return len(expired_ids)
