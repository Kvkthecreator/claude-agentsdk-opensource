"""
Simple in-memory provider - no external dependencies required

Useful for:
- Quick prototyping and demos
- Testing
- Local development without backend setup
- Learning the Agent SDK
"""

import logging
from typing import List, Optional
from claude_agent_sdk.interfaces import MemoryProvider, Context


logger = logging.getLogger(__name__)


class InMemoryProvider(MemoryProvider):
    """
    Simple in-memory memory provider using keyword matching.

    No external dependencies - just stores data in a Python list.

    Usage:
        from claude_agent_sdk.integrations.memory import InMemoryProvider

        memory = InMemoryProvider()

        # Add some context
        memory.add("Python is a programming language known for readability")
        memory.add("JavaScript is used for web development")

        # Query
        results = await memory.query("Python programming")
        # Returns: [Context about Python]
    """

    def __init__(self):
        """Initialize empty in-memory storage"""
        self.data: List[Context] = []
        logger.info("Initialized InMemoryProvider (no backend required)")

    def add(self, content: str, metadata: Optional[dict] = None) -> None:
        """
        Add content to memory.

        Args:
            content: Text content to store
            metadata: Optional metadata dictionary
        """
        context = Context(
            content=content,
            metadata=metadata or {}
        )
        self.data.append(context)
        logger.debug(f"Added content: {content[:50]}...")

    def add_many(self, items: List[tuple]) -> None:
        """
        Add multiple items at once.

        Args:
            items: List of (content, metadata) tuples
        """
        for content, metadata in items:
            self.add(content, metadata)

    async def query(
        self,
        query: str,
        filters: Optional[dict] = None,
        limit: int = 10
    ) -> List[Context]:
        """
        Simple keyword-based search.

        Args:
            query: Search query
            filters: Optional metadata filters (checks exact match)
            limit: Maximum results to return

        Returns:
            List of matching Context objects
        """
        logger.debug(f"Querying memory: {query}")

        query_lower = query.lower()
        results = []

        for context in self.data:
            # Check keyword match
            content_lower = context.content.lower()
            if query_lower in content_lower or any(
                word in content_lower for word in query_lower.split()
            ):
                # Check filters if provided
                if filters:
                    matches_filter = all(
                        context.metadata.get(k) == v
                        for k, v in filters.items()
                    )
                    if not matches_filter:
                        continue

                results.append(context)

                if len(results) >= limit:
                    break

        logger.debug(f"Found {len(results)} results")
        return results

    async def get_all(
        self,
        filters: Optional[dict] = None,
        limit: int = 50
    ) -> List[Context]:
        """
        Get all items from memory (with optional filtering).

        Args:
            filters: Optional metadata filters (checks exact match)
            limit: Maximum results to return

        Returns:
            List of Context objects
        """
        logger.debug("Getting all items from memory")

        if not filters:
            # No filters, return all items up to limit
            return self.data[:limit]

        # Apply filters
        results = []
        for context in self.data:
            # Check if all filter criteria match
            matches = all(
                context.metadata.get(k) == v
                for k, v in filters.items()
            )
            if matches:
                results.append(context)

                if len(results) >= limit:
                    break

        logger.debug(f"Found {len(results)} items")
        return results

    async def store(self, context: Context) -> str:
        """
        Store a Context object.

        Args:
            context: Context to store

        Returns:
            Context ID (index in list)
        """
        self.data.append(context)
        context_id = str(len(self.data) - 1)
        logger.debug(f"Stored context with ID: {context_id}")
        return context_id

    async def retrieve(self, context_id: str) -> Optional[Context]:
        """
        Retrieve a Context by ID.

        Args:
            context_id: Context identifier (list index)

        Returns:
            Context object or None if not found
        """
        try:
            idx = int(context_id)
            if 0 <= idx < len(self.data):
                return self.data[idx]
        except (ValueError, IndexError):
            pass

        logger.warning(f"Context not found: {context_id}")
        return None

    def clear(self) -> None:
        """Clear all stored data"""
        count = len(self.data)
        self.data.clear()
        logger.info(f"Cleared {count} items from memory")

    def __len__(self) -> int:
        """Return number of stored items"""
        return len(self.data)

    def __repr__(self) -> str:
        return f"InMemoryProvider(items={len(self.data)})"
