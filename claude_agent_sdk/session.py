"""
Session management for agents

Handles agent identity and Claude session tracking.
"""

import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class AgentSession(BaseModel):
    """
    Represents an agent execution session.

    An agent (persistent entity with agent_id) can have multiple sessions
    over time. Each session represents one execution context with Claude.

    Attributes:
        id: Unique session identifier
        agent_id: Persistent agent identifier
        claude_session_id: Claude conversation session ID (from SDK)
        task_id: Optional link to external task system (e.g., work session ID)
        task_metadata: Pass-through metadata from task system
        started_at: Session start timestamp
        ended_at: Session end timestamp (None if active)
        status: Session status
        metadata: Additional session metadata
    """

    id: str = Field(default_factory=lambda: f"session_{uuid.uuid4().hex[:12]}")
    agent_id: str
    claude_session_id: Optional[str] = None

    # Task linking (optional - for integration with task systems like YARNNN)
    task_id: Optional[str] = None
    task_metadata: Dict[str, Any] = Field(default_factory=dict)

    started_at: datetime = Field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = None
    status: str = "active"  # active, completed, failed
    metadata: Dict[str, Any] = Field(default_factory=dict)

    # Track work done in this session
    tasks_completed: int = 0
    proposals_created: List[str] = Field(default_factory=list)
    errors: List[Dict[str, Any]] = Field(default_factory=list)

    def add_proposal(self, proposal_id: str):
        """Add a proposal ID to this session"""
        if proposal_id not in self.proposals_created:
            self.proposals_created.append(proposal_id)

    def add_error(self, error: Exception, context: Optional[str] = None):
        """Add an error to this session"""
        self.errors.append({
            "error": str(error),
            "type": type(error).__name__,
            "context": context,
            "timestamp": datetime.utcnow().isoformat()
        })

    def complete(self):
        """Mark session as completed"""
        self.status = "completed"
        self.ended_at = datetime.utcnow()

    def fail(self, error: Optional[Exception] = None):
        """Mark session as failed"""
        self.status = "failed"
        self.ended_at = datetime.utcnow()
        if error:
            self.add_error(error)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/storage"""
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "claude_session_id": self.claude_session_id,
            "started_at": self.started_at.isoformat(),
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "status": self.status,
            "tasks_completed": self.tasks_completed,
            "proposals_created": self.proposals_created,
            "error_count": len(self.errors),
            "metadata": self.metadata
        }


def generate_agent_id(agent_type: str) -> str:
    """
    Generate a unique agent ID.

    Args:
        agent_type: Type of agent (knowledge, content, code, etc.)

    Returns:
        Unique agent identifier
    """
    unique_id = uuid.uuid4().hex[:8]
    return f"agent_{agent_type}_{unique_id}"
