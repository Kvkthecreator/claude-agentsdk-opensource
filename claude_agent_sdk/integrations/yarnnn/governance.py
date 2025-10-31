"""
YARNNN Governance Provider - Implements GovernanceProvider for YARNNN
"""

import os
import logging
from typing import Any, Dict, List, Optional

from claude_agent_sdk.interfaces import GovernanceProvider, Change, Proposal
from .client import YarnnnClient, Block, ContextItem


logger = logging.getLogger(__name__)


class YarnnnGovernance(GovernanceProvider):
    """
    YARNNN implementation of GovernanceProvider.

    Provides governance operations using YARNNN's proposal system.

    Usage:
        governance = YarnnnGovernance(
            api_url="https://yarnnn.example.com",
            api_key="ynk_...",
            workspace_id="ws_123",
            basket_id="basket_456"
        )

        # Propose changes
        proposal = await governance.propose(
            changes=[Change(operation="create", target="block", data={...})],
            confidence=0.8,
            reasoning="Adding new AI governance insights"
        )

        # Wait for approval
        approved = await governance.wait_for_approval(proposal.id)
    """

    def __init__(
        self,
        basket_id: str,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None,
        workspace_id: Optional[str] = None,
        timeout: int = 30
    ):
        """
        Initialize YARNNN governance provider.

        Args:
            basket_id: YARNNN basket to operate on
            api_url: YARNNN API URL (default: from YARNNN_API_URL env)
            api_key: YARNNN API key (default: from YARNNN_API_KEY env)
            workspace_id: Workspace ID (default: from YARNNN_WORKSPACE_ID env)
            timeout: Request timeout in seconds
        """
        self.basket_id = basket_id
        self.client = YarnnnClient(
            api_url=api_url,
            api_key=api_key,
            workspace_id=workspace_id,
            timeout=timeout
        )

        logger.info(f"Initialized YarnnnGovernance for basket {basket_id}")

    async def propose(
        self,
        changes: List[Change],
        confidence: float = 0.7,
        reasoning: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Proposal:
        """
        Create a governance proposal in YARNNN.

        Args:
            changes: List of changes to propose
            confidence: Agent's confidence (0.0-1.0)
            reasoning: Explanation of changes
            metadata: Additional metadata for linking sessions and tracking.
                     Recommended fields for session linking:
                     - agent_session_id: AgentSession.id from Agent SDK
                     - agent_id: Persistent agent identifier
                     - work_session_id: Optional YARNNN WorkSession ID
                     - workspace_id: Optional workspace context
                     - task_id: Optional external task identifier

        Returns:
            Created proposal with enriched metadata

        Example:
            # Link proposal to agent session and work session
            proposal = await governance.propose(
                changes=[...],
                confidence=0.85,
                reasoning="Adding research insights",
                metadata={
                    "agent_session_id": agent.current_session.id,
                    "agent_id": agent.agent_id,
                    "work_session_id": "work_session_123",
                    "workspace_id": "ws_001"
                }
            )
        """
        logger.info(f"Creating proposal with {len(changes)} changes")

        # Convert generic Changes to YARNNN-specific blocks/context items
        blocks = []
        context_items = []
        relationships = []

        for change in changes:
            if change.operation == "create":
                if change.target == "block":
                    # Create block from change data
                    blocks.append(Block(**change.data))
                elif change.target == "context_item":
                    # Create context item from change data
                    context_items.append(ContextItem(**change.data))
                elif change.target == "relationship":
                    # Create relationship from change data
                    relationships.append(change.data)
            # TODO: Handle update, delete operations

        # Create YARNNN proposal
        yarnnn_proposal = await self.client.create_proposal(
            basket_id=self.basket_id,
            blocks=blocks if blocks else None,
            context_items=context_items if context_items else None,
            relationships=relationships if relationships else None,
            confidence=confidence,
            reasoning=reasoning
        )

        # Convert to generic Proposal
        proposal = Proposal(
            id=yarnnn_proposal.id,
            changes=changes,
            status=self._map_status(yarnnn_proposal.status),
            confidence=confidence,
            reasoning=reasoning,
            metadata={
                "yarnnn_basket_id": self.basket_id,
                "yarnnn_status": yarnnn_proposal.status,
                **(metadata or {})
            }
        )

        logger.info(f"Proposal created: {proposal.id}")
        return proposal

    async def get_proposal_status(self, proposal_id: str) -> Proposal:
        """
        Get current status of a YARNNN proposal.

        Args:
            proposal_id: Proposal identifier

        Returns:
            Proposal with current status
        """
        logger.debug(f"Checking proposal status: {proposal_id}")

        yarnnn_proposal = await self.client.get_proposal(proposal_id)

        # Convert to generic Proposal
        # Note: We don't have the original changes list, so use empty list
        proposal = Proposal(
            id=yarnnn_proposal.id,
            changes=[],  # Not stored in YARNNN proposal response
            status=self._map_status(yarnnn_proposal.status),
            confidence=yarnnn_proposal.confidence,
            reasoning=yarnnn_proposal.validation_report.get("reasoning") if yarnnn_proposal.validation_report else None,
            metadata={
                "yarnnn_basket_id": yarnnn_proposal.basket_id,
                "yarnnn_status": yarnnn_proposal.status,
                "ops_count": len(yarnnn_proposal.ops)
            }
        )

        return proposal

    async def wait_for_approval(
        self,
        proposal_id: str,
        timeout: int = 3600,
        poll_interval: int = 5
    ) -> bool:
        """
        Wait for YARNNN proposal approval (blocking).

        Args:
            proposal_id: Proposal to monitor
            timeout: Maximum wait time in seconds
            poll_interval: Polling frequency in seconds

        Returns:
            True if approved, False if rejected

        Raises:
            TimeoutError: If approval not received within timeout
        """
        logger.info(f"Waiting for approval: {proposal_id} (timeout: {timeout}s)")

        approved = await self.client.wait_for_approval(
            proposal_id=proposal_id,
            timeout=timeout,
            poll_interval=poll_interval
        )

        if approved:
            logger.info(f"Proposal approved: {proposal_id}")
        else:
            logger.warning(f"Proposal rejected: {proposal_id}")

        return approved

    def _map_status(self, yarnnn_status: str) -> str:
        """
        Map YARNNN proposal status to generic status.

        Args:
            yarnnn_status: YARNNN status (PROPOSED, APPROVED, REJECTED, etc.)

        Returns:
            Generic status (pending, approved, rejected)
        """
        status_map = {
            "DRAFT": "pending",
            "PROPOSED": "pending",
            "UNDER_REVIEW": "pending",
            "APPROVED": "approved",
            "COMMITTED": "approved",
            "REJECTED": "rejected"
        }

        return status_map.get(yarnnn_status, "pending")

    @staticmethod
    def create_session_metadata(
        agent_session_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        work_session_id: Optional[str] = None,
        workspace_id: Optional[str] = None,
        task_id: Optional[str] = None,
        **additional_metadata: Any
    ) -> Dict[str, Any]:
        """
        Helper to create standardized session linking metadata for proposals.

        This ensures consistent metadata structure when linking Agent SDK sessions
        with YARNNN Work sessions and other external task systems.

        Args:
            agent_session_id: AgentSession.id from Agent SDK
            agent_id: Persistent agent identifier
            work_session_id: YARNNN WorkSession ID
            workspace_id: Workspace context
            task_id: External task system identifier
            **additional_metadata: Any other custom metadata fields

        Returns:
            Standardized metadata dictionary

        Example:
            from claude_agent_sdk.integrations.yarnnn import YarnnnGovernance

            metadata = YarnnnGovernance.create_session_metadata(
                agent_session_id=agent.current_session.id,
                agent_id=agent.agent_id,
                work_session_id="work_session_123",
                workspace_id="ws_001",
                custom_field="custom_value"
            )

            proposal = await governance.propose(
                changes=[...],
                confidence=0.85,
                reasoning="Research insights",
                metadata=metadata
            )
        """
        metadata: Dict[str, Any] = {}

        if agent_session_id:
            metadata["agent_session_id"] = agent_session_id
        if agent_id:
            metadata["agent_id"] = agent_id
        if work_session_id:
            metadata["work_session_id"] = work_session_id
        if workspace_id:
            metadata["workspace_id"] = workspace_id
        if task_id:
            metadata["task_id"] = task_id

        # Add any additional custom metadata
        metadata.update(additional_metadata)

        return metadata

    # Convenience methods

    async def propose_insight(
        self,
        title: str,
        body: str,
        confidence: float = 0.7,
        reasoning: Optional[str] = None,
        tags: Optional[List[str]] = None,
        anchor: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Proposal:
        """
        Convenience method to propose a single insight/block.

        Args:
            title: Block title
            body: Block content
            confidence: Confidence score
            reasoning: Explanation
            tags: Optional tags
            anchor: Optional anchor/category
            metadata: Additional metadata

        Returns:
            Created proposal
        """
        block_data = {
            "title": title,
            "body": body,
            "semantic_type": "knowledge",
            "state": "mature",
            "confidence": confidence,
            "tags": tags or []
        }

        if anchor:
            block_data["anchor_role"] = anchor

        change = Change(
            operation="create",
            target="block",
            data=block_data,
            reasoning=reasoning
        )

        return await self.propose(
            changes=[change],
            confidence=confidence,
            reasoning=reasoning,
            metadata=metadata
        )

    async def propose_concepts(
        self,
        concepts: List[str],
        confidence: float = 0.7,
        reasoning: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Proposal:
        """
        Convenience method to propose multiple concepts.

        Args:
            concepts: List of concept names
            confidence: Confidence score
            reasoning: Explanation
            metadata: Additional metadata

        Returns:
            Created proposal
        """
        changes = [
            Change(
                operation="create",
                target="context_item",
                data={
                    "name": concept,
                    "context_type": "concept",
                    "confidence": confidence
                },
                reasoning=f"Adding concept: {concept}"
            )
            for concept in concepts
        ]

        return await self.propose(
            changes=changes,
            confidence=confidence,
            reasoning=reasoning,
            metadata=metadata
        )
