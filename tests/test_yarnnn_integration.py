"""
Tests for YARNNN Integration

Tests the YARNNN memory and governance providers with mocked client.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from claude_agent_sdk.integrations.yarnnn import YarnnnMemory, YarnnnGovernance
from claude_agent_sdk.integrations.yarnnn.client import Proposal as YarnnnProposal
from claude_agent_sdk.interfaces import Change, Proposal


class TestYarnnnMemory:
    """Test YARNNN Memory Provider"""

    @pytest.fixture
    def mock_yarnnn_client(self, mock_yarnnn_client):
        """Use the conftest mock_yarnnn_client fixture"""
        return mock_yarnnn_client

    def test_initialization(self):
        """Test YARNNN memory initialization"""
        with patch('claude_agent_sdk.integrations.yarnnn.memory.YarnnnClient'):
            memory = YarnnnMemory(
                basket_id="basket_123",
                api_url="https://test.yarnnn.com",
                api_key="test_key",
                workspace_id="ws_001"
            )

            assert memory.basket_id == "basket_123"
            assert memory.client is not None

    @pytest.mark.asyncio
    async def test_query(self, mock_yarnnn_client):
        """Test querying YARNNN memory"""
        with patch('claude_agent_sdk.integrations.yarnnn.memory.YarnnnClient', return_value=mock_yarnnn_client):
            memory = YarnnnMemory(basket_id="basket_123")

            results = await memory.query("AI governance")

            assert len(results) > 0
            assert results[0].content is not None
            assert results[0].metadata["source"] == "yarnnn"
            mock_yarnnn_client.query_substrate.assert_called_once()

    @pytest.mark.asyncio
    async def test_query_with_filters(self, mock_yarnnn_client):
        """Test querying with filters"""
        with patch('claude_agent_sdk.integrations.yarnnn.memory.YarnnnClient', return_value=mock_yarnnn_client):
            memory = YarnnnMemory(basket_id="basket_123")

            filters = {"anchor": "AI Ethics", "state": "mature"}
            results = await memory.query("governance", filters=filters, limit=10)

            # Verify filter was passed to client
            call_args = mock_yarnnn_client.query_substrate.call_args
            assert call_args.kwargs["filters"] == filters
            assert call_args.kwargs["limit"] == 10

    @pytest.mark.asyncio
    async def test_get_all(self, mock_yarnnn_client):
        """Test getting all blocks"""
        # Mock get_blocks method
        async def mock_get_blocks(basket_id, anchor=None, state=None, limit=50):
            return [
                {
                    "id": "block_1",
                    "title": "Test Block 1",
                    "body": "Content 1",
                    "semantic_type": "knowledge",
                    "state": "mature"
                },
                {
                    "id": "block_2",
                    "title": "Test Block 2",
                    "body": "Content 2",
                    "semantic_type": "meaning",
                    "state": "draft"
                }
            ]

        mock_yarnnn_client.get_blocks = AsyncMock(side_effect=mock_get_blocks)

        with patch('claude_agent_sdk.integrations.yarnnn.memory.YarnnnClient', return_value=mock_yarnnn_client):
            memory = YarnnnMemory(basket_id="basket_123")

            results = await memory.get_all()

            assert len(results) == 2
            assert results[0].metadata["title"] == "Test Block 1"
            assert results[1].metadata["title"] == "Test Block 2"

    @pytest.mark.asyncio
    async def test_get_all_with_filters(self, mock_yarnnn_client):
        """Test get_all with anchor and state filters"""
        async def mock_get_blocks(basket_id, anchor=None, state=None, limit=50):
            return []

        mock_yarnnn_client.get_blocks = AsyncMock(side_effect=mock_get_blocks)

        with patch('claude_agent_sdk.integrations.yarnnn.memory.YarnnnClient', return_value=mock_yarnnn_client):
            memory = YarnnnMemory(basket_id="basket_123")

            await memory.get_all(
                filters={"anchor": "AI Ethics", "state": "mature"},
                limit=25
            )

            call_args = mock_yarnnn_client.get_blocks.call_args
            assert call_args.kwargs["anchor"] == "AI Ethics"
            assert call_args.kwargs["state"] == "mature"
            assert call_args.kwargs["limit"] == 25

    @pytest.mark.asyncio
    async def test_summarize(self, mock_yarnnn_client):
        """Test summarizing YARNNN substrate"""
        # Mock get_blocks
        async def mock_get_blocks(basket_id, limit=100):
            return [
                {"state": "mature", "semantic_type": "knowledge"},
                {"state": "mature", "semantic_type": "knowledge"},
                {"state": "draft", "semantic_type": "meaning"},
            ]

        # Mock get_context_items
        async def mock_get_context_items(basket_id, limit=100):
            return [
                {"name": "Python"},
                {"name": "JavaScript"},
            ]

        mock_yarnnn_client.get_blocks = AsyncMock(side_effect=mock_get_blocks)
        mock_yarnnn_client.get_context_items = AsyncMock(side_effect=mock_get_context_items)

        with patch('claude_agent_sdk.integrations.yarnnn.memory.YarnnnClient', return_value=mock_yarnnn_client):
            memory = YarnnnMemory(basket_id="basket_123")

            summary = await memory.summarize()

            assert summary["total_blocks"] == 3
            assert summary["total_context_items"] == 2
            assert summary["states"]["mature"] == 2
            assert summary["states"]["draft"] == 1
            assert summary["semantic_types"]["knowledge"] == 2
            assert summary["semantic_types"]["meaning"] == 1
            assert summary["provider"] == "yarnnn"

    @pytest.mark.asyncio
    async def test_get_anchor(self, mock_yarnnn_client):
        """Test getting blocks under an anchor"""
        async def mock_get_blocks(basket_id, anchor=None, state=None, limit=100):
            return [{"title": f"Block under {anchor}"}]

        mock_yarnnn_client.get_blocks = AsyncMock(side_effect=mock_get_blocks)

        with patch('claude_agent_sdk.integrations.yarnnn.memory.YarnnnClient', return_value=mock_yarnnn_client):
            memory = YarnnnMemory(basket_id="basket_123")

            results = await memory.get_anchor("AI Ethics")

            assert len(results) > 0
            call_args = mock_yarnnn_client.get_blocks.call_args
            assert call_args.kwargs["anchor"] == "AI Ethics"

    @pytest.mark.asyncio
    async def test_get_concepts(self, mock_yarnnn_client):
        """Test getting concepts from substrate"""
        async def mock_get_context_items(basket_id, context_type=None, limit=100):
            return [
                {"name": "Python", "context_type": "concept"},
                {"name": "AI", "context_type": "concept"},
                {"name": "Governance", "context_type": "concept"},
            ]

        mock_yarnnn_client.get_context_items = AsyncMock(side_effect=mock_get_context_items)

        with patch('claude_agent_sdk.integrations.yarnnn.memory.YarnnnClient', return_value=mock_yarnnn_client):
            memory = YarnnnMemory(basket_id="basket_123")

            concepts = await memory.get_concepts()

            assert len(concepts) == 3
            assert "Python" in concepts
            assert "AI" in concepts
            assert "Governance" in concepts

    def test_format_block(self):
        """Test block formatting"""
        with patch('claude_agent_sdk.integrations.yarnnn.memory.YarnnnClient'):
            memory = YarnnnMemory(basket_id="basket_123")

            block = {
                "title": "Test Title",
                "body": "Test body content",
                "semantic_type": "knowledge",
                "state": "mature"
            }

            formatted = memory._format_block(block)

            assert "Test Title" in formatted
            assert "Test body content" in formatted
            assert "knowledge" in formatted
            assert "mature" in formatted


class TestYarnnnGovernance:
    """Test YARNNN Governance Provider"""

    @pytest.fixture
    def mock_yarnnn_client(self, mock_yarnnn_client):
        """Use the conftest mock_yarnnn_client fixture"""
        return mock_yarnnn_client

    def test_initialization(self):
        """Test YARNNN governance initialization"""
        with patch('claude_agent_sdk.integrations.yarnnn.governance.YarnnnClient'):
            governance = YarnnnGovernance(
                basket_id="basket_123",
                api_url="https://test.yarnnn.com",
                api_key="test_key",
                workspace_id="ws_001"
            )

            assert governance.basket_id == "basket_123"
            assert governance.client is not None

    @pytest.mark.asyncio
    async def test_propose(self, mock_yarnnn_client):
        """Test creating a proposal"""
        with patch('claude_agent_sdk.integrations.yarnnn.governance.YarnnnClient', return_value=mock_yarnnn_client):
            governance = YarnnnGovernance(basket_id="basket_123")

            changes = [
                Change(
                    operation="create",
                    target="block",
                    data={
                        "title": "Test Block",
                        "body": "Test content",
                        "semantic_type": "knowledge"
                    },
                    reasoning="Adding new knowledge"
                )
            ]

            proposal = await governance.propose(
                changes=changes,
                confidence=0.85,
                reasoning="Test proposal"
            )

            assert proposal.id == "prop_test_123"
            assert proposal.confidence == 0.85
            assert proposal.status == "pending"
            assert len(proposal.changes) == 1
            mock_yarnnn_client.create_proposal.assert_called_once()

    @pytest.mark.asyncio
    async def test_propose_with_metadata(self, mock_yarnnn_client):
        """Test creating proposal with metadata"""
        with patch('claude_agent_sdk.integrations.yarnnn.governance.YarnnnClient', return_value=mock_yarnnn_client):
            governance = YarnnnGovernance(basket_id="basket_123")

            changes = [
                Change(
                    operation="create",
                    target="block",
                    data={"title": "Test", "body": "Content"}
                )
            ]

            metadata = {
                "agent_session_id": "session_123",
                "agent_id": "agent_001",
                "work_session_id": "work_session_456"
            }

            proposal = await governance.propose(
                changes=changes,
                confidence=0.8,
                reasoning="Test",
                metadata=metadata
            )

            # Metadata should be included in proposal
            assert proposal.metadata["agent_session_id"] == "session_123"
            assert proposal.metadata["agent_id"] == "agent_001"
            assert proposal.metadata["work_session_id"] == "work_session_456"

    @pytest.mark.asyncio
    async def test_get_proposal_status(self, mock_yarnnn_client):
        """Test getting proposal status"""
        with patch('claude_agent_sdk.integrations.yarnnn.governance.YarnnnClient', return_value=mock_yarnnn_client):
            governance = YarnnnGovernance(basket_id="basket_123")

            proposal = await governance.get_proposal_status("prop_test_123")

            assert proposal.id == "prop_test_123"
            assert proposal.status == "pending"
            mock_yarnnn_client.get_proposal.assert_called_once_with("prop_test_123")

    @pytest.mark.asyncio
    async def test_wait_for_approval(self, mock_yarnnn_client):
        """Test waiting for proposal approval"""
        async def mock_wait(proposal_id, timeout=3600, poll_interval=5):
            return True

        mock_yarnnn_client.wait_for_approval = AsyncMock(side_effect=mock_wait)

        with patch('claude_agent_sdk.integrations.yarnnn.governance.YarnnnClient', return_value=mock_yarnnn_client):
            governance = YarnnnGovernance(basket_id="basket_123")

            approved = await governance.wait_for_approval("prop_test_123", timeout=10)

            assert approved is True
            mock_yarnnn_client.wait_for_approval.assert_called_once()

    @pytest.mark.asyncio
    async def test_wait_for_rejection(self, mock_yarnnn_client):
        """Test waiting for rejected proposal"""
        async def mock_wait(proposal_id, timeout=3600, poll_interval=5):
            return False

        mock_yarnnn_client.wait_for_approval = AsyncMock(side_effect=mock_wait)

        with patch('claude_agent_sdk.integrations.yarnnn.governance.YarnnnClient', return_value=mock_yarnnn_client):
            governance = YarnnnGovernance(basket_id="basket_123")

            approved = await governance.wait_for_approval("prop_test_123")

            assert approved is False

    def test_map_status(self):
        """Test status mapping"""
        with patch('claude_agent_sdk.integrations.yarnnn.governance.YarnnnClient'):
            governance = YarnnnGovernance(basket_id="basket_123")

            assert governance._map_status("DRAFT") == "pending"
            assert governance._map_status("PROPOSED") == "pending"
            assert governance._map_status("UNDER_REVIEW") == "pending"
            assert governance._map_status("APPROVED") == "approved"
            assert governance._map_status("COMMITTED") == "approved"
            assert governance._map_status("REJECTED") == "rejected"
            assert governance._map_status("UNKNOWN_STATUS") == "pending"

    def test_create_session_metadata(self):
        """Test creating standardized session metadata"""
        metadata = YarnnnGovernance.create_session_metadata(
            agent_session_id="session_123",
            agent_id="agent_001",
            work_session_id="work_456",
            workspace_id="ws_789",
            task_id="task_999",
            custom_field="custom_value"
        )

        assert metadata["agent_session_id"] == "session_123"
        assert metadata["agent_id"] == "agent_001"
        assert metadata["work_session_id"] == "work_456"
        assert metadata["workspace_id"] == "ws_789"
        assert metadata["task_id"] == "task_999"
        assert metadata["custom_field"] == "custom_value"

    def test_create_session_metadata_partial(self):
        """Test creating metadata with only some fields"""
        metadata = YarnnnGovernance.create_session_metadata(
            agent_session_id="session_123",
            custom="value"
        )

        assert metadata["agent_session_id"] == "session_123"
        assert metadata["custom"] == "value"
        assert "work_session_id" not in metadata

    @pytest.mark.asyncio
    async def test_propose_insight(self, mock_yarnnn_client):
        """Test convenience method for proposing single insight"""
        with patch('claude_agent_sdk.integrations.yarnnn.governance.YarnnnClient', return_value=mock_yarnnn_client):
            governance = YarnnnGovernance(basket_id="basket_123")

            proposal = await governance.propose_insight(
                title="AI Ethics",
                body="Important considerations for AI development",
                confidence=0.9,
                reasoning="Adding AI ethics knowledge",
                tags=["AI", "Ethics"],
                anchor="Governance"
            )

            assert proposal.id == "prop_test_123"
            assert proposal.confidence == 0.9
            mock_yarnnn_client.create_proposal.assert_called_once()

            # Check that block was created correctly
            call_args = mock_yarnnn_client.create_proposal.call_args
            blocks = call_args.kwargs["blocks"]
            assert len(blocks) == 1
            assert blocks[0].title == "AI Ethics"
            assert blocks[0].body == "Important considerations for AI development"

    @pytest.mark.asyncio
    async def test_propose_concepts(self, mock_yarnnn_client):
        """Test convenience method for proposing concepts"""
        with patch('claude_agent_sdk.integrations.yarnnn.governance.YarnnnClient', return_value=mock_yarnnn_client):
            governance = YarnnnGovernance(basket_id="basket_123")

            concepts = ["Python", "JavaScript", "Rust"]

            proposal = await governance.propose_concepts(
                concepts=concepts,
                confidence=0.8,
                reasoning="Adding programming languages"
            )

            assert proposal.id == "prop_test_123"
            mock_yarnnn_client.create_proposal.assert_called_once()

            # Check that context items were created
            call_args = mock_yarnnn_client.create_proposal.call_args
            context_items = call_args.kwargs["context_items"]
            assert len(context_items) == 3
