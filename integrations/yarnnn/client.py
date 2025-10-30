"""
YARNNN Client - API/MCP client for YARNNN substrate

This client handles all interactions with the YARNNN substrate including:
- Querying building blocks and context items
- Creating proposals for substrate changes
- Monitoring proposal approval status
- Committing approved changes
"""

import os
from typing import Any, Dict, List, Optional
import httpx
from pydantic import BaseModel, Field


class Block(BaseModel):
    """Building block in YARNNN substrate"""
    id: Optional[str] = None
    title: str
    body: str
    semantic_type: str = "knowledge"  # knowledge, meaning, structural
    anchor_role: Optional[str] = None  # proto_anchor, mature_anchor, orphan
    state: str = "mature"  # proto, growing, mature, fading, archived
    scope: str = "evergreen"  # evergreen, timeboxed, ephemeral
    confidence: float = Field(ge=0.0, le=1.0, default=0.7)
    tags: List[str] = []


class ContextItem(BaseModel):
    """Context item (entity/concept) in YARNNN substrate"""
    id: Optional[str] = None
    name: str
    context_type: str = "concept"  # person, org, concept, entity
    confidence: float = Field(ge=0.0, le=1.0, default=0.7)


class Proposal(BaseModel):
    """Governance proposal for substrate changes"""
    id: Optional[str] = None
    basket_id: str
    ops: List[Dict[str, Any]]
    validation_report: Optional[Dict[str, Any]] = None
    status: str = "PROPOSED"  # DRAFT, PROPOSED, UNDER_REVIEW, APPROVED, REJECTED, COMMITTED
    confidence: float = Field(ge=0.0, le=1.0, default=0.7)


class YarnnnClient:
    """
    Client for interacting with YARNNN substrate via API or MCP.

    This client provides high-level methods for agents to:
    - Query the substrate for relevant context
    - Propose changes to the substrate
    - Monitor governance workflow
    - Commit approved changes

    Usage:
        client = YarnnnClient(
            api_url="http://localhost:3000",
            api_key="your_key",
            workspace_id="your_workspace"
        )

        # Query substrate
        context = await client.query_substrate(
            basket_id="basket_123",
            query="AI governance frameworks"
        )

        # Propose changes
        proposal = await client.create_proposal(
            basket_id="basket_123",
            blocks=[Block(title="New Insight", body="Details...")],
            context_items=[ContextItem(name="AI Ethics")]
        )

        # Wait for approval
        approved = await client.wait_for_approval(proposal.id)
    """

    def __init__(
        self,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None,
        workspace_id: Optional[str] = None,
        timeout: int = 30
    ):
        """
        Initialize YARNNN client

        Args:
            api_url: YARNNN API base URL (default: from YARNNN_API_URL env)
            api_key: YARNNN API key (default: from YARNNN_API_KEY env)
            workspace_id: Workspace ID (default: from YARNNN_WORKSPACE_ID env)
            timeout: Request timeout in seconds
        """
        self.api_url = api_url or os.getenv("YARNNN_API_URL", "http://localhost:3000")
        self.api_key = api_key or os.getenv("YARNNN_API_KEY")
        self.workspace_id = workspace_id or os.getenv("YARNNN_WORKSPACE_ID")
        self.timeout = timeout

        if not self.api_key:
            raise ValueError("YARNNN_API_KEY must be set")
        if not self.workspace_id:
            raise ValueError("YARNNN_WORKSPACE_ID must be set")

    def _get_headers(self) -> Dict[str, str]:
        """Get authorization headers"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    async def query_substrate(
        self,
        basket_id: str,
        query: str,
        limit: int = 20,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Query YARNNN substrate for relevant context

        Args:
            basket_id: Basket to query
            query: Semantic query string
            limit: Maximum results to return
            filters: Optional filters (e.g., {"anchor": "AI Ethics"})

        Returns:
            List of relevant blocks and context items
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.api_url}/api/baskets/{basket_id}/query",
                json={
                    "query": query,
                    "limit": limit,
                    "filters": filters or {}
                },
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()

    async def get_blocks(
        self,
        basket_id: str,
        anchor: Optional[str] = None,
        state: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get building blocks from substrate

        Args:
            basket_id: Basket to query
            anchor: Filter by anchor (optional)
            state: Filter by state (optional)
            limit: Maximum results

        Returns:
            List of blocks
        """
        params = {"limit": limit}
        if anchor:
            params["anchor"] = anchor
        if state:
            params["state"] = state

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.api_url}/api/baskets/{basket_id}/blocks",
                params=params,
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()

    async def get_context_items(
        self,
        basket_id: str,
        context_type: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get context items (entities/concepts) from substrate

        Args:
            basket_id: Basket to query
            context_type: Filter by type (person, org, concept, entity)
            limit: Maximum results

        Returns:
            List of context items
        """
        params = {"limit": limit}
        if context_type:
            params["context_type"] = context_type

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.api_url}/api/baskets/{basket_id}/context",
                params=params,
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()

    async def create_proposal(
        self,
        basket_id: str,
        blocks: Optional[List[Block]] = None,
        context_items: Optional[List[ContextItem]] = None,
        relationships: Optional[List[Dict[str, Any]]] = None,
        confidence: float = 0.7,
        reasoning: Optional[str] = None
    ) -> Proposal:
        """
        Create a governance proposal for substrate changes

        Args:
            basket_id: Target basket
            blocks: Building blocks to create/update
            context_items: Context items to create/update
            relationships: Relationships to create
            confidence: Agent confidence score (0.0-1.0)
            reasoning: Explanation of proposed changes

        Returns:
            Created proposal
        """
        # Build operations list
        ops = []

        if blocks:
            for block in blocks:
                ops.append({
                    "type": "block_create",
                    "data": block.model_dump(exclude_none=True)
                })

        if context_items:
            for item in context_items:
                ops.append({
                    "type": "context_item_create",
                    "data": item.model_dump(exclude_none=True)
                })

        if relationships:
            for rel in relationships:
                ops.append({
                    "type": "relationship_create",
                    "data": rel
                })

        # Create validation report
        validation_report = {
            "confidence": confidence,
            "reasoning": reasoning,
            "origin": "agent",
            "ops_count": len(ops)
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.api_url}/api/baskets/{basket_id}/proposals",
                json={
                    "ops": ops,
                    "validation_report": validation_report,
                    "origin": "agent"
                },
                headers=self._get_headers()
            )
            response.raise_for_status()
            data = response.json()
            return Proposal(**data)

    async def get_proposal(self, proposal_id: str) -> Proposal:
        """
        Get proposal status

        Args:
            proposal_id: Proposal ID

        Returns:
            Proposal with current status
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.api_url}/api/proposals/{proposal_id}",
                headers=self._get_headers()
            )
            response.raise_for_status()
            return Proposal(**response.json())

    async def wait_for_approval(
        self,
        proposal_id: str,
        timeout: int = 3600,
        poll_interval: int = 5
    ) -> bool:
        """
        Wait for proposal approval (blocking)

        Args:
            proposal_id: Proposal to monitor
            timeout: Maximum wait time in seconds
            poll_interval: Polling frequency in seconds

        Returns:
            True if approved, False if rejected

        Raises:
            TimeoutError: If approval not received within timeout
        """
        import asyncio
        elapsed = 0

        while elapsed < timeout:
            proposal = await self.get_proposal(proposal_id)

            if proposal.status == "APPROVED" or proposal.status == "COMMITTED":
                return True
            elif proposal.status == "REJECTED":
                return False

            await asyncio.sleep(poll_interval)
            elapsed += poll_interval

        raise TimeoutError(f"Proposal {proposal_id} not approved within {timeout}s")

    async def create_dump(
        self,
        basket_id: str,
        text_dump: Optional[str] = None,
        file_url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a raw dump (for agent-captured content)

        Args:
            basket_id: Target basket
            text_dump: Text content
            file_url: URL to file in storage
            metadata: Additional metadata

        Returns:
            Created dump
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.api_url}/api/baskets/{basket_id}/dumps",
                json={
                    "text_dump": text_dump,
                    "file_url": file_url,
                    "metadata": metadata or {}
                },
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()
