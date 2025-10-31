"""
Tests for Session Management

Tests the AgentSession class and session-related functionality.
"""

import pytest
from datetime import datetime
from claude_agent_sdk.session import AgentSession, generate_agent_id


class TestAgentSession:
    """Test AgentSession class"""

    def test_session_creation(self):
        """Test basic session creation"""
        session = AgentSession(agent_id="test_agent_001")

        assert session.id.startswith("session_")
        assert session.agent_id == "test_agent_001"
        assert session.status == "active"
        assert session.tasks_completed == 0
        assert len(session.proposals_created) == 0
        assert len(session.errors) == 0
        assert isinstance(session.started_at, datetime)
        assert session.ended_at is None

    def test_session_with_claude_session_id(self):
        """Test session creation with Claude session ID"""
        session = AgentSession(
            agent_id="test_agent",
            claude_session_id="claude_session_123"
        )

        assert session.claude_session_id == "claude_session_123"

    def test_session_with_task_linking(self):
        """Test session creation with task linking"""
        task_metadata = {
            "workspace_id": "ws_123",
            "basket_id": "basket_abc"
        }

        session = AgentSession(
            agent_id="test_agent",
            task_id="work_session_456",
            task_metadata=task_metadata
        )

        assert session.task_id == "work_session_456"
        assert session.task_metadata == task_metadata
        assert session.task_metadata["workspace_id"] == "ws_123"

    def test_session_with_metadata(self):
        """Test session with custom metadata"""
        metadata = {
            "agent_type": "knowledge",
            "agent_name": "Research Bot",
            "custom_field": "value"
        }

        session = AgentSession(
            agent_id="test_agent",
            metadata=metadata
        )

        assert session.metadata == metadata
        assert session.metadata["agent_type"] == "knowledge"

    def test_add_proposal(self):
        """Test adding proposals to session"""
        session = AgentSession(agent_id="test_agent")

        session.add_proposal("prop_1")
        session.add_proposal("prop_2")

        assert len(session.proposals_created) == 2
        assert "prop_1" in session.proposals_created
        assert "prop_2" in session.proposals_created

    def test_add_proposal_deduplication(self):
        """Test that duplicate proposals aren't added"""
        session = AgentSession(agent_id="test_agent")

        session.add_proposal("prop_1")
        session.add_proposal("prop_1")
        session.add_proposal("prop_1")

        assert len(session.proposals_created) == 1
        assert session.proposals_created[0] == "prop_1"

    def test_add_error(self):
        """Test adding errors to session"""
        session = AgentSession(agent_id="test_agent")

        error = ValueError("Test error")
        session.add_error(error, context="testing")

        assert len(session.errors) == 1
        assert session.errors[0]["error"] == "Test error"
        assert session.errors[0]["type"] == "ValueError"
        assert session.errors[0]["context"] == "testing"
        assert "timestamp" in session.errors[0]

    def test_add_multiple_errors(self):
        """Test adding multiple errors"""
        session = AgentSession(agent_id="test_agent")

        session.add_error(ValueError("Error 1"), "context_1")
        session.add_error(RuntimeError("Error 2"), "context_2")
        session.add_error(KeyError("Error 3"))

        assert len(session.errors) == 3
        assert session.errors[0]["type"] == "ValueError"
        assert session.errors[1]["type"] == "RuntimeError"
        assert session.errors[2]["type"] == "KeyError"
        assert session.errors[2]["context"] is None

    def test_complete_session(self):
        """Test completing a session"""
        session = AgentSession(agent_id="test_agent")
        assert session.status == "active"
        assert session.ended_at is None

        session.complete()

        assert session.status == "completed"
        assert session.ended_at is not None
        assert isinstance(session.ended_at, datetime)

    def test_fail_session(self):
        """Test failing a session"""
        session = AgentSession(agent_id="test_agent")

        error = RuntimeError("Something went wrong")
        session.fail(error)

        assert session.status == "failed"
        assert session.ended_at is not None
        assert len(session.errors) == 1
        assert session.errors[0]["error"] == "Something went wrong"

    def test_fail_session_without_error(self):
        """Test failing a session without providing an error"""
        session = AgentSession(agent_id="test_agent")

        session.fail()

        assert session.status == "failed"
        assert session.ended_at is not None
        assert len(session.errors) == 0

    def test_to_dict(self):
        """Test converting session to dictionary"""
        session = AgentSession(
            agent_id="test_agent",
            claude_session_id="claude_123",
            metadata={"test": "value"}
        )

        session.tasks_completed = 5
        session.add_proposal("prop_1")
        session.add_proposal("prop_2")
        session.add_error(ValueError("test"))

        session_dict = session.to_dict()

        assert session_dict["id"] == session.id
        assert session_dict["agent_id"] == "test_agent"
        assert session_dict["claude_session_id"] == "claude_123"
        assert session_dict["status"] == "active"
        assert session_dict["tasks_completed"] == 5
        assert len(session_dict["proposals_created"]) == 2
        assert session_dict["error_count"] == 1
        assert session_dict["metadata"]["test"] == "value"
        assert session_dict["ended_at"] is None

    def test_to_dict_completed_session(self):
        """Test to_dict on completed session"""
        session = AgentSession(agent_id="test_agent")
        session.complete()

        session_dict = session.to_dict()

        assert session_dict["status"] == "completed"
        assert session_dict["ended_at"] is not None

    def test_session_workflow(self):
        """Test a complete session workflow"""
        # Create session
        session = AgentSession(agent_id="research_bot")
        assert session.status == "active"

        # Do work
        session.tasks_completed += 1
        session.add_proposal("prop_research_1")

        session.tasks_completed += 1
        session.add_proposal("prop_research_2")

        # Handle an error
        session.add_error(ValueError("Minor issue"), "task_2")

        # Complete session
        session.complete()

        # Verify final state
        assert session.status == "completed"
        assert session.tasks_completed == 2
        assert len(session.proposals_created) == 2
        assert len(session.errors) == 1
        assert session.ended_at is not None


class TestGenerateAgentId:
    """Test agent ID generation"""

    def test_generate_agent_id(self):
        """Test basic agent ID generation"""
        agent_id = generate_agent_id("knowledge")

        assert agent_id.startswith("agent_knowledge_")
        assert len(agent_id) > len("agent_knowledge_")

    def test_generate_unique_ids(self):
        """Test that generated IDs are unique"""
        ids = [generate_agent_id("test") for _ in range(10)]

        # All IDs should be unique
        assert len(ids) == len(set(ids))

    def test_generate_different_types(self):
        """Test generating IDs for different agent types"""
        knowledge_id = generate_agent_id("knowledge")
        content_id = generate_agent_id("content")
        code_id = generate_agent_id("code")

        assert "knowledge" in knowledge_id
        assert "content" in content_id
        assert "code" in code_id

        # All should be different
        assert knowledge_id != content_id != code_id
