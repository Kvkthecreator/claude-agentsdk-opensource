"""
YARNNN Memory Provider - Implements MemoryProvider for YARNNN substrate
"""

import os
import logging
from typing import Any, Dict, List, Optional

from claude_agent_sdk.interfaces import MemoryProvider, Context
from .client import YarnnnClient


logger = logging.getLogger(__name__)


class YarnnnMemory(MemoryProvider):
    """
    YARNNN implementation of MemoryProvider.

    Provides memory operations using YARNNN substrate as the backend.

    Usage:
        # workspace_id is REQUIRED (user/tenant-specific)
        memory = YarnnnMemory(
            workspace_id="ws_user123",  # Required from request context
            basket_id="basket_456",
            api_url="https://yarnnn.example.com",  # Optional, falls back to env
            api_key="ynk_..."  # Optional, falls back to env
        )

        # Query for context
        contexts = await memory.query("AI governance")

        # Get all items
        all_items = await memory.get_all(filters={"anchor": "AI Ethics"})
    """

    def __init__(
        self,
        workspace_id: str,
        basket_id: str,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: int = 30
    ):
        """
        Initialize YARNNN memory provider.

        Args:
            workspace_id: Workspace ID (REQUIRED - user/tenant-specific)
            basket_id: YARNNN basket to operate on
            api_url: YARNNN API URL (default: from YARNNN_API_URL env)
            api_key: YARNNN API key (default: from YARNNN_API_KEY env)
            timeout: Request timeout in seconds

        Raises:
            ValueError: If workspace_id is not provided

        Note:
            workspace_id must be explicitly provided as it's user/tenant-specific.
            Service-level credentials (api_url, api_key) can fall back to environment variables.
        """
        self.basket_id = basket_id
        self.client = YarnnnClient(
            workspace_id=workspace_id,
            api_url=api_url,
            api_key=api_key,
            timeout=timeout
        )

        logger.info(f"Initialized YarnnnMemory for workspace {workspace_id}, basket {basket_id}")

    async def query(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 20
    ) -> List[Context]:
        """
        Query YARNNN substrate for relevant context.

        Args:
            query: Semantic query string
            filters: Optional filters (anchor, state, semantic_type)
            limit: Maximum results to return

        Returns:
            List of Context items from substrate
        """
        logger.info(f"Querying YARNNN: {query}")

        results = await self.client.query_substrate(
            basket_id=self.basket_id,
            query=query,
            limit=limit,
            filters=filters or {}
        )

        # Convert YARNNN blocks to generic Context objects
        contexts = []
        for block in results:
            contexts.append(Context(
                content=self._format_block(block),
                metadata={
                    "id": block.get("id"),
                    "title": block.get("title"),
                    "semantic_type": block.get("semantic_type"),
                    "state": block.get("state"),
                    "anchor": block.get("anchor"),
                    "tags": block.get("tags", []),
                    "source": "yarnnn"
                },
                confidence=block.get("confidence", 1.0)
            ))

        return contexts

    async def get_all(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 50
    ) -> List[Context]:
        """
        Get all blocks from YARNNN basket.

        Args:
            filters: Optional filters (anchor, state)
            limit: Maximum results

        Returns:
            List of Context items
        """
        logger.info("Retrieving all blocks from YARNNN")

        # Extract YARNNN-specific filters
        anchor = filters.get("anchor") if filters else None
        state = filters.get("state") if filters else None

        blocks = await self.client.get_blocks(
            basket_id=self.basket_id,
            anchor=anchor,
            state=state,
            limit=limit
        )

        # Convert to Context objects
        contexts = []
        for block in blocks:
            contexts.append(Context(
                content=self._format_block(block),
                metadata={
                    "id": block.get("id"),
                    "title": block.get("title"),
                    "semantic_type": block.get("semantic_type"),
                    "state": block.get("state"),
                    "source": "yarnnn"
                },
                confidence=block.get("confidence", 1.0)
            ))

        return contexts

    async def summarize(self) -> Dict[str, Any]:
        """
        Get summary statistics about YARNNN substrate.

        Returns:
            Summary statistics
        """
        logger.info("Summarizing YARNNN substrate")

        # Get all blocks (limited sample)
        blocks = await self.client.get_blocks(
            basket_id=self.basket_id,
            limit=100
        )

        # Get context items
        context_items = await self.client.get_context_items(
            basket_id=self.basket_id,
            limit=100
        )

        # Aggregate statistics
        states = {}
        types = {}
        for block in blocks:
            state = block.get("state", "unknown")
            states[state] = states.get(state, 0) + 1

            semantic_type = block.get("semantic_type", "unknown")
            types[semantic_type] = types.get(semantic_type, 0) + 1

        return {
            "total_blocks": len(blocks),
            "total_context_items": len(context_items),
            "states": states,
            "semantic_types": types,
            "basket_id": self.basket_id,
            "provider": "yarnnn"
        }

    def _format_block(self, block: Dict[str, Any]) -> str:
        """
        Format a YARNNN block as a context string.

        Args:
            block: YARNNN block dictionary

        Returns:
            Formatted string
        """
        title = block.get("title", "Untitled")
        body = block.get("body", "")
        semantic_type = block.get("semantic_type", "knowledge")
        state = block.get("state", "mature")

        return f"""### {title}
{body}

*Type: {semantic_type} | State: {state}*"""

    # Additional YARNNN-specific convenience methods

    async def get_anchor(self, anchor: str, state: Optional[str] = None) -> List[Context]:
        """
        Get all knowledge under a specific anchor.

        Args:
            anchor: Anchor name
            state: Optional state filter

        Returns:
            List of Context items under anchor
        """
        return await self.get_all(
            filters={"anchor": anchor, "state": state},
            limit=100
        )

    async def get_concepts(
        self,
        context_type: Optional[str] = None,
        limit: int = 100
    ) -> List[str]:
        """
        Get all concepts/entities from substrate.

        Args:
            context_type: Filter by type (person, org, concept, entity)
            limit: Maximum results

        Returns:
            List of concept names
        """
        context_items = await self.client.get_context_items(
            basket_id=self.basket_id,
            context_type=context_type,
            limit=limit
        )

        return [item.get("name") for item in context_items if item.get("name")]
