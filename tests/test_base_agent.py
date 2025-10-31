"""
Tests for BaseAgent

Tests the core BaseAgent functionality including initialization,
session management, and reasoning capabilities.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from claude_agent_sdk import BaseAgent
from claude_agent_sdk.integrations.memory import InMemoryProvider
from claude_agent_sdk.interfaces import Context


class TestAgent(BaseAgent):
    """Test agent implementation for testing"""

    async def execute(self, task: str, **kwargs):
        """Simple execute implementation"""
        if not self.current_session:
            self.current_session = self._start_session()

        # Query memory if available
        context_str = ""
        if self.memory:
            contexts = await self.memory.query(task, limit=5)
            if contexts:
                context_str = "\n".join([c.content for c in contexts])

        # Reason with Claude
        response = await self.reason(task, context=context_str)

        return {
            "response": response,
            "session_id": self.current_session.id
        }


class TestBaseAgentInitialization:
    """Test BaseAgent initialization"""

    def test_init_with_api_key(self, mock_anthropic_api_key):
        """Test initialization with API key"""
        agent = TestAgent(
            agent_id="test_001",
            anthropic_api_key=mock_anthropic_api_key
        )

        assert agent.agent_id == "test_001"
        assert agent.agent_type == "generic"
        assert agent.model == "claude-sonnet-4-5"
        assert agent.memory is None
        assert agent.governance is None
        assert agent.tasks is None

    def test_init_with_env_api_key(self):
        """Test initialization with API key from environment"""
        # API key is set in conftest.py
        agent = TestAgent(agent_id="test_002")

        assert agent.agent_id == "test_002"
        # Should not raise error about missing API key

    def test_init_auto_generate_agent_id(self, mock_anthropic_api_key):
        """Test auto-generation of agent ID"""
        agent = TestAgent(
            agent_type="test",
            anthropic_api_key=mock_anthropic_api_key
        )

        assert agent.agent_id.startswith("agent_test_")
        assert len(agent.agent_id) > len("agent_test_")

    def test_init_with_custom_config(self, mock_anthropic_api_key):
        """Test initialization with custom configuration"""
        agent = TestAgent(
            agent_id="custom_001",
            agent_type="knowledge",
            agent_name="Research Assistant",
            model="claude-opus-4",
            auto_approve=True,
            confidence_threshold=0.9,
            anthropic_api_key=mock_anthropic_api_key
        )

        assert agent.agent_id == "custom_001"
        assert agent.agent_type == "knowledge"
        assert agent.agent_name == "Research Assistant"
        assert agent.model == "claude-opus-4"
        assert agent.auto_approve is True
        assert agent.confidence_threshold == 0.9

    def test_init_with_memory_provider(self, mock_anthropic_api_key):
        """Test initialization with memory provider"""
        memory = InMemoryProvider()
        agent = TestAgent(
            agent_id="test_003",
            memory=memory,
            anthropic_api_key=mock_anthropic_api_key
        )

        assert agent.memory is memory
        assert isinstance(agent.memory, InMemoryProvider)

    def test_init_with_metadata(self, mock_anthropic_api_key):
        """Test initialization with custom metadata"""
        metadata = {
            "custom_field": "value",
            "environment": "test"
        }

        agent = TestAgent(
            agent_id="test_004",
            metadata=metadata,
            anthropic_api_key=mock_anthropic_api_key
        )

        assert agent.metadata == metadata
        assert agent.metadata["custom_field"] == "value"

    def test_init_missing_api_key(self):
        """Test that missing API key raises error"""
        # Temporarily remove env var
        import os
        old_key = os.environ.pop("ANTHROPIC_API_KEY", None)

        try:
            with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
                TestAgent(agent_id="test_005")
        finally:
            # Restore env var
            if old_key:
                os.environ["ANTHROPIC_API_KEY"] = old_key

    def test_repr(self, mock_anthropic_api_key):
        """Test string representation"""
        agent = TestAgent(
            agent_id="test_006",
            agent_type="knowledge",
            model="claude-sonnet-4",
            anthropic_api_key=mock_anthropic_api_key
        )

        repr_str = repr(agent)

        assert "TestAgent" in repr_str
        assert "test_006" in repr_str
        assert "knowledge" in repr_str
        assert "claude-sonnet-4" in repr_str


class TestBaseAgentSessions:
    """Test BaseAgent session management"""

    def test_start_session(self, mock_anthropic_api_key):
        """Test starting a new session"""
        agent = TestAgent(
            agent_id="session_test_001",
            anthropic_api_key=mock_anthropic_api_key
        )

        assert agent.current_session is None

        session = agent._start_session()

        assert session is not None
        assert session.agent_id == "session_test_001"
        assert session.status == "active"
        assert session.id.startswith("session_")

    def test_start_session_with_task_linking(self, mock_anthropic_api_key):
        """Test starting session with task linking"""
        agent = TestAgent(
            agent_id="session_test_002",
            anthropic_api_key=mock_anthropic_api_key
        )

        task_metadata = {
            "workspace_id": "ws_123",
            "basket_id": "basket_abc"
        }

        session = agent._start_session(
            task_id="work_session_456",
            task_metadata=task_metadata
        )

        assert session.task_id == "work_session_456"
        assert session.task_metadata == task_metadata

    def test_session_includes_metadata(self, mock_anthropic_api_key):
        """Test that session includes agent metadata"""
        agent = TestAgent(
            agent_id="session_test_003",
            agent_type="knowledge",
            agent_name="Test Bot",
            metadata={"custom": "value"},
            anthropic_api_key=mock_anthropic_api_key
        )

        session = agent._start_session()

        assert session.metadata["agent_type"] == "knowledge"
        assert session.metadata["agent_name"] == "Test Bot"
        assert session.metadata["custom"] == "value"

    def test_resume_session(self, mock_anthropic_api_key):
        """Test resuming an existing session"""
        agent = TestAgent(
            agent_id="session_test_004",
            session_id="session_existing_123",
            claude_session_id="claude_session_456",
            anthropic_api_key=mock_anthropic_api_key
        )

        assert agent.current_session is not None
        assert agent.current_session.id == "session_existing_123"
        assert agent.current_session.claude_session_id == "claude_session_456"


class TestBaseAgentReasoning:
    """Test BaseAgent reasoning capabilities"""

    @pytest.mark.asyncio
    async def test_reason_basic(self, mock_anthropic_api_key):
        """Test basic reasoning"""
        agent = TestAgent(
            agent_id="reason_test_001",
            anthropic_api_key=mock_anthropic_api_key
        )

        with patch.object(agent.claude.messages, 'create', new_callable=AsyncMock) as mock_create:
            mock_response = Mock()
            mock_response.content = [Mock(text="Test response")]
            mock_create.return_value = mock_response

            response = await agent.reason("What is Python?")

            assert response is not None
            mock_create.assert_called_once()

            # Check call arguments
            call_args = mock_create.call_args
            assert call_args.kwargs["model"] == "claude-sonnet-4-5"
            assert len(call_args.kwargs["messages"]) == 1
            assert call_args.kwargs["messages"][0]["content"] == "What is Python?"

    @pytest.mark.asyncio
    async def test_reason_with_context(self, mock_anthropic_api_key):
        """Test reasoning with context"""
        agent = TestAgent(
            agent_id="reason_test_002",
            anthropic_api_key=mock_anthropic_api_key
        )

        context = "Python is a high-level programming language"

        with patch.object(agent.claude.messages, 'create', new_callable=AsyncMock) as mock_create:
            mock_response = Mock()
            mock_response.content = [Mock(text="Response")]
            mock_create.return_value = mock_response

            await agent.reason("Tell me about Python", context=context)

            call_args = mock_create.call_args
            messages = call_args.kwargs["messages"]

            # Should have context message + task message
            assert len(messages) == 2
            assert "Relevant Context" in messages[0]["content"]
            assert context in messages[0]["content"]
            assert messages[1]["content"] == "Tell me about Python"

    @pytest.mark.asyncio
    async def test_reason_with_system_prompt(self, mock_anthropic_api_key):
        """Test reasoning with custom system prompt"""
        agent = TestAgent(
            agent_id="reason_test_003",
            anthropic_api_key=mock_anthropic_api_key
        )

        system_prompt = "You are a helpful assistant specialized in Python."

        with patch.object(agent.claude.messages, 'create', new_callable=AsyncMock) as mock_create:
            mock_response = Mock()
            mock_response.content = [Mock(text="Response")]
            mock_create.return_value = mock_response

            await agent.reason("Help me", system_prompt=system_prompt)

            call_args = mock_create.call_args
            assert call_args.kwargs["system"] == system_prompt

    @pytest.mark.asyncio
    async def test_reason_with_tools(self, mock_anthropic_api_key):
        """Test reasoning with tools"""
        agent = TestAgent(
            agent_id="reason_test_004",
            anthropic_api_key=mock_anthropic_api_key
        )

        tools = [
            {
                "name": "test_tool",
                "description": "A test tool",
                "input_schema": {"type": "object", "properties": {}}
            }
        ]

        with patch.object(agent.claude.messages, 'create', new_callable=AsyncMock) as mock_create:
            mock_response = Mock()
            mock_response.content = [Mock(text="Response")]
            mock_create.return_value = mock_response

            await agent.reason("Task", tools=tools)

            call_args = mock_create.call_args
            assert "tools" in call_args.kwargs
            assert len(call_args.kwargs["tools"]) == 1
            assert call_args.kwargs["tools"][0]["name"] == "test_tool"

    @pytest.mark.asyncio
    async def test_reason_error_tracking(self, mock_anthropic_api_key):
        """Test that reasoning errors are tracked in session"""
        agent = TestAgent(
            agent_id="reason_test_005",
            anthropic_api_key=mock_anthropic_api_key
        )

        agent.current_session = agent._start_session()

        with patch.object(agent.claude.messages, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.side_effect = RuntimeError("API Error")

            with pytest.raises(RuntimeError):
                await agent.reason("Task")

            # Error should be tracked in session
            assert len(agent.current_session.errors) == 1
            assert agent.current_session.errors[0]["type"] == "RuntimeError"
            assert "API Error" in agent.current_session.errors[0]["error"]


class TestBaseAgentExecution:
    """Test BaseAgent execution"""

    @pytest.mark.asyncio
    async def test_execute_basic(self, mock_anthropic_api_key):
        """Test basic execution"""
        agent = TestAgent(
            agent_id="exec_test_001",
            anthropic_api_key=mock_anthropic_api_key
        )

        with patch.object(agent.claude.messages, 'create', new_callable=AsyncMock) as mock_create:
            mock_response = Mock()
            mock_response.content = [Mock(text="Response")]
            mock_create.return_value = mock_response

            result = await agent.execute("Test task")

            assert result is not None
            assert "session_id" in result
            assert result["session_id"].startswith("session_")

    @pytest.mark.asyncio
    async def test_execute_with_memory(self, mock_anthropic_api_key):
        """Test execution with memory provider"""
        memory = InMemoryProvider()
        memory.add("Python is a programming language")

        agent = TestAgent(
            agent_id="exec_test_002",
            memory=memory,
            anthropic_api_key=mock_anthropic_api_key
        )

        with patch.object(agent.claude.messages, 'create', new_callable=AsyncMock) as mock_create:
            mock_response = Mock()
            mock_response.content = [Mock(text="Response")]
            mock_create.return_value = mock_response

            result = await agent.execute("Tell me about Python")

            # Should have queried memory
            assert mock_create.called

            # Check that context was provided
            call_args = mock_create.call_args
            messages = call_args.kwargs["messages"]
            # Should have context message
            assert any("Python" in str(msg) for msg in messages)

    @pytest.mark.asyncio
    async def test_execute_creates_session(self, mock_anthropic_api_key):
        """Test that execute creates a session"""
        agent = TestAgent(
            agent_id="exec_test_003",
            anthropic_api_key=mock_anthropic_api_key
        )

        assert agent.current_session is None

        with patch.object(agent.claude.messages, 'create', new_callable=AsyncMock) as mock_create:
            mock_response = Mock()
            mock_response.content = [Mock(text="Response")]
            mock_create.return_value = mock_response

            await agent.execute("Task")

            assert agent.current_session is not None
            assert agent.current_session.status == "active"


class TestBaseAgentDefaultSystemPrompt:
    """Test BaseAgent default system prompt"""

    def test_get_default_system_prompt(self, mock_anthropic_api_key):
        """Test default system prompt generation"""
        agent = TestAgent(
            agent_id="prompt_test_001",
            agent_type="test",
            anthropic_api_key=mock_anthropic_api_key
        )

        prompt = agent._get_default_system_prompt()

        assert prompt is not None
        assert "autonomous agent" in prompt.lower()
        assert agent.agent_id in prompt
        assert agent.agent_type in prompt

    def test_default_prompt_reflects_providers(self, mock_anthropic_api_key):
        """Test that default prompt reflects available providers"""
        memory = InMemoryProvider()

        agent = TestAgent(
            agent_id="prompt_test_002",
            memory=memory,
            anthropic_api_key=mock_anthropic_api_key
        )

        prompt = agent._get_default_system_prompt()

        assert "Memory: Available" in prompt
        assert "Governance: Not configured" in prompt
        assert "Tasks: Not configured" in prompt
