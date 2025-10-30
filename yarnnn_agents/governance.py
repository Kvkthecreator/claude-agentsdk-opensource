"""
Governance Layer - Agent interface to YARNNN governance

Handles proposal creation, approval workflows, and change management.
Agents use this layer to propose substrate changes that require human approval.
"""

from typing import Any, Dict, List, Optional
import logging
from integrations.yarnnn import YarnnnClient, Block, ContextItem, Proposal


logger = logging.getLogger(__name__)


class GovernanceLayer:
    """
    Governance layer abstraction for agents

    Provides agents with governance workflow operations:
    - Propose substrate changes
    - Monitor approval status
    - Auto-approve high-confidence changes (if enabled)
    - Track change history

    Usage:
        governance = GovernanceLayer(yarnnn_client, basket_id)

        # Propose changes
        proposal = await governance.propose(
            blocks=[{"title": "New Insight", "body": "Details..."}],
            reasoning="Adding research findings from today"
        )

        # Wait for approval
        approved = await governance.wait_for_approval(proposal.id)

        # Check status
        status = await governance.get_status(proposal.id)
    """

    def __init__(
        self,
        yarnnn_client: YarnnnClient,
        basket_id: str,
        auto_approve: bool = False,
        confidence_threshold: float = 0.8
    ):
        """
        Initialize governance layer

        Args:
            yarnnn_client: YARNNN client instance
            basket_id: Basket to operate on
            auto_approve: Enable auto-approval for high-confidence proposals
            confidence_threshold: Threshold for auto-approval (0.0-1.0)
        """
        self.yarnnn = yarnnn_client
        self.basket_id = basket_id
        self.auto_approve = auto_approve
        self.confidence_threshold = confidence_threshold

        if auto_approve:
            logger.warning(
                f"Auto-approval enabled with threshold {confidence_threshold}. "
                "This bypasses human governance - use with caution!"
            )

    async def propose(
        self,
        blocks: Optional[List[Dict[str, Any]]] = None,
        context_items: Optional[List[str]] = None,
        relationships: Optional[List[Dict[str, Any]]] = None,
        reasoning: Optional[str] = None,
        confidence: float = 0.7
    ) -> Proposal:
        """
        Propose changes to substrate

        Args:
            blocks: Building blocks to create (list of {title, body, ...})
            context_items: Context items to create (list of names)
            relationships: Relationships to create
            reasoning: Explanation of proposed changes
            confidence: Confidence score (0.0-1.0)

        Returns:
            Created proposal
        """
        logger.info(f"Creating proposal with {len(blocks or [])} blocks, {len(context_items or [])} concepts")

        # Parse blocks
        block_objs = []
        if blocks:
            for b in blocks:
                block_objs.append(Block(
                    title=b["title"],
                    body=b["body"],
                    semantic_type=b.get("semantic_type", "knowledge"),
                    anchor_role=b.get("anchor_role"),
                    state=b.get("state", "mature"),
                    scope=b.get("scope", "evergreen"),
                    confidence=b.get("confidence", confidence),
                    tags=b.get("tags", [])
                ))

        # Parse context items
        context_objs = []
        if context_items:
            for name in context_items:
                context_objs.append(ContextItem(
                    name=name,
                    confidence=confidence
                ))

        # Create proposal
        proposal = await self.yarnnn.create_proposal(
            basket_id=self.basket_id,
            blocks=block_objs if block_objs else None,
            context_items=context_objs if context_objs else None,
            relationships=relationships,
            confidence=confidence,
            reasoning=reasoning
        )

        logger.info(f"Proposal created: {proposal.id} (status: {proposal.status})")

        # Check auto-approval
        if self.auto_approve and confidence >= self.confidence_threshold:
            logger.info(f"Auto-approving proposal {proposal.id} (confidence: {confidence})")
            # Note: Auto-approval would need backend support
            # For now, just log the intent

        return proposal

    async def propose_insight(
        self,
        title: str,
        body: str,
        tags: Optional[List[str]] = None,
        confidence: float = 0.7,
        reasoning: Optional[str] = None
    ) -> Proposal:
        """
        Convenience method to propose a single insight

        Args:
            title: Insight title
            body: Insight content
            tags: Optional tags
            confidence: Confidence score
            reasoning: Explanation

        Returns:
            Created proposal
        """
        return await self.propose(
            blocks=[{
                "title": title,
                "body": body,
                "semantic_type": "knowledge",
                "tags": tags or [],
                "confidence": confidence
            }],
            reasoning=reasoning or f"Adding insight: {title}",
            confidence=confidence
        )

    async def propose_concepts(
        self,
        concepts: List[str],
        confidence: float = 0.7,
        reasoning: Optional[str] = None
    ) -> Proposal:
        """
        Convenience method to propose multiple concepts

        Args:
            concepts: List of concept names
            confidence: Confidence score
            reasoning: Explanation

        Returns:
            Created proposal
        """
        return await self.propose(
            context_items=concepts,
            reasoning=reasoning or f"Adding concepts: {', '.join(concepts)}",
            confidence=confidence
        )

    async def get_status(self, proposal_id: str) -> Dict[str, Any]:
        """
        Get proposal status

        Args:
            proposal_id: Proposal ID

        Returns:
            Status information
        """
        logger.info(f"Checking proposal status: {proposal_id}")

        proposal = await self.yarnnn.get_proposal(proposal_id)

        return {
            "id": proposal.id,
            "status": proposal.status,
            "ops_count": len(proposal.ops),
            "confidence": proposal.confidence,
            "basket_id": proposal.basket_id
        }

    async def wait_for_approval(
        self,
        proposal_id: str,
        timeout: int = 3600,
        poll_interval: int = 5
    ) -> bool:
        """
        Wait for proposal approval (blocking)

        Args:
            proposal_id: Proposal ID
            timeout: Maximum wait time in seconds
            poll_interval: Polling frequency in seconds

        Returns:
            True if approved, False if rejected

        Raises:
            TimeoutError: If not approved within timeout
        """
        logger.info(f"Waiting for approval: {proposal_id}")

        try:
            approved = await self.yarnnn.wait_for_approval(
                proposal_id=proposal_id,
                timeout=timeout,
                poll_interval=poll_interval
            )

            if approved:
                logger.info(f"Proposal {proposal_id} approved!")
            else:
                logger.warning(f"Proposal {proposal_id} rejected")

            return approved

        except TimeoutError:
            logger.error(f"Proposal {proposal_id} approval timeout after {timeout}s")
            raise

    async def list_pending_proposals(self) -> List[Dict[str, Any]]:
        """
        List all pending proposals for this basket

        Returns:
            List of pending proposals

        Note:
            This is a placeholder - full implementation requires
            list proposals API endpoint in YARNNN
        """
        logger.info("Listing pending proposals")

        # TODO: Implement when YARNNN has list proposals API
        # For now, return empty list
        return []

    def should_auto_approve(self, confidence: float) -> bool:
        """
        Check if proposal should be auto-approved

        Args:
            confidence: Proposal confidence score

        Returns:
            True if auto-approval criteria met
        """
        return self.auto_approve and confidence >= self.confidence_threshold

    def __repr__(self) -> str:
        return (
            f"GovernanceLayer(basket_id='{self.basket_id}', "
            f"auto_approve={self.auto_approve}, "
            f"threshold={self.confidence_threshold})"
        )
