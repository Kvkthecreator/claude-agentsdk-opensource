"""
Memory Layer - Agent interface to YARNNN substrate

Provides high-level memory operations for agents:
- Semantic querying
- Context retrieval
- Memory traversal
- Knowledge graph navigation
"""

from typing import Any, Dict, List, Optional
import logging
from integrations.yarnnn import YarnnnClient


logger = logging.getLogger(__name__)


class MemoryLayer:
    """
    Memory layer abstraction for agents

    Provides agents with intuitive memory operations that map to
    YARNNN substrate queries. This layer handles:
    - Semantic search across building blocks
    - Context item retrieval
    - Anchor-based knowledge organization
    - Relationship traversal

    Usage:
        memory = MemoryLayer(yarnnn_client, basket_id)

        # Query for relevant context
        context = await memory.query("AI governance frameworks")

        # Get specific anchor knowledge
        ethics = await memory.get_anchor("AI Ethics")

        # Find related concepts
        related = await memory.find_related("Machine Learning", depth=2)
    """

    def __init__(self, yarnnn_client: YarnnnClient, basket_id: str):
        """
        Initialize memory layer

        Args:
            yarnnn_client: YARNNN client instance
            basket_id: Basket to operate on
        """
        self.yarnnn = yarnnn_client
        self.basket_id = basket_id

    async def query(
        self,
        query: str,
        limit: int = 20,
        filters: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Semantic query across substrate

        Args:
            query: Natural language query
            limit: Maximum results
            filters: Optional filters (anchor, state, etc.)

        Returns:
            Formatted context string
        """
        logger.info(f"Querying memory: {query}")

        results = await self.yarnnn.query_substrate(
            basket_id=self.basket_id,
            query=query,
            limit=limit,
            filters=filters
        )

        return self._format_results(results)

    async def get_anchor(self, anchor: str, state: Optional[str] = None) -> str:
        """
        Get all knowledge under an anchor (category)

        Args:
            anchor: Anchor name
            state: Optional state filter (mature, growing, etc.)

        Returns:
            Formatted anchor knowledge
        """
        logger.info(f"Retrieving anchor: {anchor}")

        blocks = await self.yarnnn.get_blocks(
            basket_id=self.basket_id,
            anchor=anchor,
            state=state,
            limit=50
        )

        if not blocks:
            return f"No knowledge found under anchor: {anchor}"

        formatted = [f"## Anchor: {anchor}\n"]
        for block in blocks:
            formatted.append(
                f"### {block['title']}\n"
                f"{block['body']}\n"
                f"*State: {block.get('state', 'mature')} | "
                f"Type: {block.get('semantic_type', 'knowledge')}*\n"
            )

        return "\n".join(formatted)

    async def get_all_blocks(
        self,
        state: Optional[str] = None,
        semantic_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get all building blocks in basket

        Args:
            state: Filter by state
            semantic_type: Filter by semantic type
            limit: Maximum results

        Returns:
            List of blocks
        """
        logger.info("Retrieving all blocks")

        return await self.yarnnn.get_blocks(
            basket_id=self.basket_id,
            state=state,
            limit=limit
        )

    async def get_concepts(
        self,
        context_type: Optional[str] = None,
        limit: int = 100
    ) -> List[str]:
        """
        Get all concepts/entities in substrate

        Args:
            context_type: Filter by type (person, org, concept, entity)
            limit: Maximum results

        Returns:
            List of concept names
        """
        logger.info("Retrieving concepts")

        items = await self.yarnnn.get_context_items(
            basket_id=self.basket_id,
            context_type=context_type,
            limit=limit
        )

        return [item["name"] for item in items]

    async def find_related(
        self,
        concept: str,
        depth: int = 1,
        relationship_type: Optional[str] = None
    ) -> str:
        """
        Find related concepts/blocks (relationship traversal)

        Args:
            concept: Starting concept
            depth: Relationship depth to traverse
            relationship_type: Filter by relationship type

        Returns:
            Formatted related knowledge

        Note:
            This is a placeholder - full implementation requires
            relationship API endpoints in YARNNN
        """
        logger.info(f"Finding related to: {concept}")

        # For now, use semantic query as proxy
        # TODO: Implement proper relationship traversal when API available
        return await self.query(f"Related to: {concept}", limit=10)

    async def get_recent_updates(self, hours: int = 24, limit: int = 20) -> str:
        """
        Get recently updated knowledge

        Args:
            hours: Time window in hours
            limit: Maximum results

        Returns:
            Formatted recent updates

        Note:
            This is a placeholder - full implementation requires
            temporal query API in YARNNN
        """
        logger.info(f"Retrieving updates from last {hours} hours")

        # For now, get all blocks and sort by updated_at client-side
        # TODO: Implement temporal query API in YARNNN
        blocks = await self.get_all_blocks(limit=limit)

        formatted = ["## Recent Updates\n"]
        for block in blocks[:limit]:
            formatted.append(
                f"### {block['title']}\n"
                f"{block['body'][:200]}...\n"
                f"*Updated: {block.get('updated_at', 'unknown')}*\n"
            )

        return "\n".join(formatted)

    async def summarize_substrate(self) -> str:
        """
        Get high-level summary of substrate

        Returns:
            Formatted summary statistics
        """
        logger.info("Summarizing substrate")

        blocks = await self.get_all_blocks(limit=1000)
        concepts = await self.get_concepts(limit=1000)

        # Group by anchor
        anchors: Dict[str, int] = {}
        for block in blocks:
            anchor = block.get("anchor_role", "orphan")
            anchors[anchor] = anchors.get(anchor, 0) + 1

        # Group by state
        states: Dict[str, int] = {}
        for block in blocks:
            state = block.get("state", "mature")
            states[state] = states.get(state, 0) + 1

        summary = [
            "## Substrate Summary\n",
            f"**Total Building Blocks:** {len(blocks)}",
            f"**Total Concepts:** {len(concepts)}\n",
            "### By Anchor:",
            *[f"- {anchor}: {count}" for anchor, count in anchors.items()],
            "\n### By State:",
            *[f"- {state}: {count}" for state, count in states.items()]
        ]

        return "\n".join(summary)

    def _format_results(self, results: List[Dict[str, Any]]) -> str:
        """
        Format query results for agent consumption

        Args:
            results: Raw results from YARNNN

        Returns:
            Formatted string
        """
        if not results:
            return "No relevant context found in memory."

        formatted = ["## Relevant Context from Memory\n"]

        for item in results:
            if item.get("type") == "block":
                formatted.append(
                    f"### {item['title']}\n"
                    f"{item['body']}\n"
                    f"*Anchor: {item.get('anchor_role', 'orphan')} | "
                    f"State: {item.get('state', 'mature')} | "
                    f"Type: {item.get('semantic_type', 'knowledge')}*\n"
                )
            elif item.get("type") == "context_item":
                formatted.append(
                    f"**• {item['name']}** ({item.get('context_type', 'concept')})\n"
                )

        return "\n".join(formatted)

    def __repr__(self) -> str:
        return f"MemoryLayer(basket_id='{self.basket_id}')"
