"""
Pytest configuration and shared fixtures for Claude Agent SDK tests
"""

import pytest
import os
from typing import AsyncGenerator, Dict, Any
from unittest.mock import Mock, AsyncMock, MagicMock

# Set test environment variables
os.environ["ANTHROPIC_API_KEY"] = "sk-ant-test-key-12345"
os.environ["LOG_LEVEL"] = "WARNING"  # Reduce noise in tests


@pytest.fixture
def mock_anthropic_api_key():
    """Provide a test API key"""
    return "sk-ant-test-key-12345"


@pytest.fixture
def mock_anthropic_client():
    """Mock Anthropic client for testing"""
    mock_client = MagicMock()

    # Mock messages.create
    mock_response = Mock()
    mock_response.content = [Mock(text="Test response from Claude")]
    mock_response.id = "msg_test_123"
    mock_response.model = "claude-sonnet-4"
    mock_response.usage = Mock(input_tokens=10, output_tokens=20)

    mock_client.messages.create = AsyncMock(return_value=mock_response)

    return mock_client


@pytest.fixture
def mock_yarnnn_client():
    """Mock YARNNN client for testing"""
    from claude_agent_sdk.integrations.yarnnn.client import YarnnnClient, Block, ContextItem, Proposal

    mock_client = AsyncMock(spec=YarnnnClient)

    # Mock query_substrate
    async def mock_query_substrate(basket_id, query, limit=20, filters=None):
        return [
            {
                "type": "block",
                "id": "block_1",
                "title": "Test Block",
                "body": "Test content",
                "semantic_type": "knowledge",
                "anchor_role": "orphan",
                "state": "mature"
            }
        ]

    mock_client.query_substrate = AsyncMock(side_effect=mock_query_substrate)

    # Mock create_proposal
    async def mock_create_proposal(basket_id, blocks=None, context_items=None, **kwargs):
        return Proposal(
            id="prop_test_123",
            basket_id=basket_id,
            status="PROPOSED",
            ops=[{"type": "create", "target": "block"}],
            confidence=kwargs.get("confidence", 0.7),
            reasoning=kwargs.get("reasoning", "Test proposal")
        )

    mock_client.create_proposal = AsyncMock(side_effect=mock_create_proposal)

    # Mock get_proposal
    async def mock_get_proposal(proposal_id):
        return Proposal(
            id=proposal_id,
            basket_id="basket_123",
            status="PROPOSED",
            ops=[{"type": "create"}],
            confidence=0.7,
            reasoning="Test"
        )

    mock_client.get_proposal = AsyncMock(side_effect=mock_get_proposal)

    return mock_client


@pytest.fixture
def sample_context_data():
    """Sample context data for testing"""
    return [
        {
            "content": "Python is a high-level programming language",
            "metadata": {"topic": "programming", "language": "python"}
        },
        {
            "content": "Rust focuses on safety and performance",
            "metadata": {"topic": "programming", "language": "rust"}
        }
    ]


@pytest.fixture
def sample_agent_config():
    """Sample agent configuration for testing"""
    return {
        "agent_id": "test_agent_001",
        "agent_type": "test",
        "agent_name": "Test Agent",
        "model": "claude-sonnet-4",
        "auto_approve": False,
        "confidence_threshold": 0.8
    }


@pytest.fixture
async def cleanup_sessions():
    """Cleanup any session state after tests"""
    yield
    # Cleanup code here if needed
