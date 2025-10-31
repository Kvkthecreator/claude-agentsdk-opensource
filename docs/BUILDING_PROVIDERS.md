# Building Custom Providers

**Create your own memory, governance, and task providers**

The Agent SDK uses provider interfaces to stay generic and extensible. You can build providers for any backend: databases, APIs, file systems, or custom services.

## Provider Interfaces

### MemoryProvider

Store and retrieve context for agents.

```python
from abc import ABC, abstractmethod
from typing import List, Optional
from claude_agent_sdk.interfaces import MemoryProvider, Context


class MemoryProvider(ABC):
    """Abstract memory provider"""

    @abstractmethod
    async def query(
        self,
        query: str,
        filters: Optional[dict] = None,
        limit: int = 10
    ) -> List[Context]:
        """Search for relevant context"""
        pass

    @abstractmethod
    async def store(self, context: Context) -> str:
        """Store context, return ID"""
        pass

    @abstractmethod
    async def retrieve(self, context_id: str) -> Optional[Context]:
        """Retrieve context by ID"""
        pass
```

### GovernanceProvider

Manage proposals and approvals for agent actions.

```python
from claude_agent_sdk.interfaces import GovernanceProvider, Proposal, Change


class GovernanceProvider(ABC):
    """Abstract governance provider"""

    @abstractmethod
    async def propose(
        self,
        changes: List[Change],
        confidence: float = 0.7,
        reasoning: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> Proposal:
        """Create a proposal"""
        pass

    @abstractmethod
    async def get_proposal_status(self, proposal_id: str) -> Proposal:
        """Check proposal status"""
        pass

    @abstractmethod
    async def wait_for_approval(
        self,
        proposal_id: str,
        timeout: int = 3600
    ) -> bool:
        """Wait for approval (blocking)"""
        pass
```

### TaskProvider

Integrate with task management systems.

```python
from claude_agent_sdk.interfaces import TaskProvider, Task


class TaskProvider(ABC):
    """Abstract task provider"""

    @abstractmethod
    async def get_pending_tasks(self, agent_id: str) -> List[Task]:
        """Get tasks assigned to agent"""
        pass

    @abstractmethod
    async def update_task_status(
        self,
        task_id: str,
        status: str,
        result: Optional[Any] = None,
        error: Optional[str] = None
    ) -> None:
        """Update task status"""
        pass
```

---

## Example: File System Provider

Let's build a simple provider that stores memory in JSON files.

### Step 1: Implementation

```python
# my_providers/filesystem.py

import json
import os
from pathlib import Path
from typing import List, Optional
from claude_agent_sdk.interfaces import MemoryProvider, Context


class FileSystemProvider(MemoryProvider):
    """
    Store context in JSON files on disk.

    Simple persistent storage without external dependencies.
    """

    def __init__(self, storage_dir: str = "./memory_data"):
        """
        Initialize file system storage.

        Args:
            storage_dir: Directory to store JSON files
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = self.storage_dir / "index.json"
        self._load_index()

    def _load_index(self):
        """Load or create index"""
        if self.index_file.exists():
            with open(self.index_file, 'r') as f:
                self.index = json.load(f)
        else:
            self.index = {"contexts": [], "next_id": 0}
            self._save_index()

    def _save_index(self):
        """Save index to disk"""
        with open(self.index_file, 'w') as f:
            json.dump(self.index, f, indent=2)

    async def query(
        self,
        query: str,
        filters: Optional[dict] = None,
        limit: int = 10
    ) -> List[Context]:
        """
        Search contexts using keyword matching.

        Args:
            query: Search query
            filters: Optional metadata filters
            limit: Max results

        Returns:
            List of matching Context objects
        """
        results = []
        query_lower = query.lower()

        for ctx_ref in self.index["contexts"]:
            # Load context from file
            ctx_file = self.storage_dir / f"{ctx_ref['id']}.json"
            if not ctx_file.exists():
                continue

            with open(ctx_file, 'r') as f:
                ctx_data = json.load(f)

            # Check keyword match
            if query_lower in ctx_data["content"].lower():
                # Check filters
                if filters:
                    matches = all(
                        ctx_data["metadata"].get(k) == v
                        for k, v in filters.items()
                    )
                    if not matches:
                        continue

                # Add to results
                results.append(Context(
                    content=ctx_data["content"],
                    metadata=ctx_data["metadata"],
                    source=ctx_data.get("source", "filesystem")
                ))

                if len(results) >= limit:
                    break

        return results

    async def store(self, context: Context) -> str:
        """
        Store context to file.

        Args:
            context: Context to store

        Returns:
            Context ID
        """
        # Generate ID
        context_id = str(self.index["next_id"])
        self.index["next_id"] += 1

        # Save context to file
        ctx_file = self.storage_dir / f"{context_id}.json"
        with open(ctx_file, 'w') as f:
            json.dump({
                "id": context_id,
                "content": context.content,
                "metadata": context.metadata,
                "source": context.source
            }, f, indent=2)

        # Update index
        self.index["contexts"].append({
            "id": context_id,
            "preview": context.content[:100]
        })
        self._save_index()

        return context_id

    async def retrieve(self, context_id: str) -> Optional[Context]:
        """
        Retrieve context by ID.

        Args:
            context_id: Context identifier

        Returns:
            Context or None
        """
        ctx_file = self.storage_dir / f"{context_id}.json"
        if not ctx_file.exists():
            return None

        with open(ctx_file, 'r') as f:
            ctx_data = json.load(f)

        return Context(
            content=ctx_data["content"],
            metadata=ctx_data["metadata"],
            source=ctx_data.get("source", "filesystem")
        )
```

### Step 2: Usage

```python
from claude_agent_sdk import BaseAgent
from my_providers.filesystem import FileSystemProvider


class MyAgent(BaseAgent):
    async def execute(self, task: str, **kwargs):
        # Query filesystem memory
        contexts = await self.memory.query(task)
        context_str = "\n".join([c.content for c in contexts])

        # Reason with Claude
        response = await self.reason(task, context=context_str)

        return response


# Create agent with filesystem provider
memory = FileSystemProvider(storage_dir="./my_memory")
agent = MyAgent(
    agent_id="my_agent",
    memory=memory,
    anthropic_api_key="sk-ant-..."
)

# Use agent
result = await agent.execute("Research AI safety")
```

### Step 3: Add Data

```python
# Add some knowledge to filesystem
from claude_agent_sdk.interfaces import Context

memory = FileSystemProvider()

await memory.store(Context(
    content="AI safety focuses on ensuring AI systems are beneficial",
    metadata={"topic": "safety", "date": "2024-01-01"},
    source="manual"
))

await memory.store(Context(
    content="Alignment research studies how to align AI with human values",
    metadata={"topic": "alignment", "date": "2024-01-01"},
    source="manual"
))
```

---

## Example: Notion Integration

Connect to Notion as a memory provider.

```python
from notion_client import AsyncClient
from claude_agent_sdk.interfaces import MemoryProvider, Context


class NotionProvider(MemoryProvider):
    """Use Notion as memory storage"""

    def __init__(self, notion_token: str, database_id: str):
        self.client = AsyncClient(auth=notion_token)
        self.database_id = database_id

    async def query(
        self,
        query: str,
        filters: Optional[dict] = None,
        limit: int = 10
    ) -> List[Context]:
        """Search Notion database"""
        response = await self.client.databases.query(
            database_id=self.database_id,
            filter={
                "property": "Content",
                "rich_text": {"contains": query}
            },
            page_size=limit
        )

        contexts = []
        for page in response["results"]:
            # Extract content from page
            content = self._extract_content(page)
            contexts.append(Context(
                content=content,
                metadata={"notion_page_id": page["id"]},
                source="notion"
            ))

        return contexts

    async def store(self, context: Context) -> str:
        """Create new Notion page"""
        page = await self.client.pages.create(
            parent={"database_id": self.database_id},
            properties={
                "Content": {"rich_text": [{"text": {"content": context.content}}]}
            }
        )
        return page["id"]

    def _extract_content(self, page: dict) -> str:
        """Extract text from Notion page"""
        # Simplified - real implementation would handle blocks
        props = page["properties"]
        if "Content" in props:
            return props["Content"]["rich_text"][0]["text"]["content"]
        return ""
```

---

## Example: PostgreSQL Provider

Use PostgreSQL with vector similarity search.

```python
import asyncpg
from pgvector.asyncpg import register_vector
from claude_agent_sdk.interfaces import MemoryProvider, Context


class PostgresProvider(MemoryProvider):
    """PostgreSQL with pgvector for semantic search"""

    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.pool = None

    async def initialize(self):
        """Setup connection pool"""
        self.pool = await asyncpg.create_pool(self.connection_string)
        async with self.pool.acquire() as conn:
            await register_vector(conn)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS contexts (
                    id SERIAL PRIMARY KEY,
                    content TEXT NOT NULL,
                    embedding VECTOR(1536),
                    metadata JSONB DEFAULT '{}'
                )
            """)

    async def query(
        self,
        query: str,
        filters: Optional[dict] = None,
        limit: int = 10
    ) -> List[Context]:
        """Semantic search using embeddings"""
        # Generate embedding for query (use OpenAI/similar)
        query_embedding = await self._get_embedding(query)

        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT content, metadata
                FROM contexts
                ORDER BY embedding <=> $1
                LIMIT $2
            """, query_embedding, limit)

        return [
            Context(
                content=row["content"],
                metadata=row["metadata"],
                source="postgres"
            )
            for row in rows
        ]

    async def store(self, context: Context) -> str:
        """Store with embedding"""
        embedding = await self._get_embedding(context.content)

        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO contexts (content, embedding, metadata)
                VALUES ($1, $2, $3)
                RETURNING id
            """, context.content, embedding, context.metadata)

        return str(row["id"])

    async def _get_embedding(self, text: str):
        """Generate embedding (implement with OpenAI/etc)"""
        # Placeholder - use actual embedding model
        pass
```

---

## Tips for Building Providers

### 1. Start Simple

Begin with basic implementations:
- Keyword search before semantic search
- In-memory before persistent
- Sync before async (then wrap in async)

### 2. Handle Errors Gracefully

```python
async def query(self, query: str, **kwargs) -> List[Context]:
    try:
        # Your implementation
        return results
    except ConnectionError as e:
        logger.error(f"Connection failed: {e}")
        return []  # Return empty rather than crash
```

### 3. Add Logging

```python
import logging

logger = logging.getLogger(__name__)

class MyProvider(MemoryProvider):
    def __init__(self, ...):
        logger.info("Initialized MyProvider")

    async def query(self, query: str, **kwargs):
        logger.debug(f"Querying: {query}")
        results = # ...
        logger.debug(f"Found {len(results)} results")
        return results
```

### 4. Test Independently

```python
# test_my_provider.py
import pytest
from my_providers.filesystem import FileSystemProvider


@pytest.mark.asyncio
async def test_store_and_retrieve():
    provider = FileSystemProvider("./test_data")

    # Store
    ctx_id = await provider.store(Context(
        content="Test content",
        metadata={"type": "test"}
    ))

    # Retrieve
    ctx = await provider.retrieve(ctx_id)
    assert ctx.content == "Test content"
    assert ctx.metadata["type"] == "test"
```

### 5. Document Your Provider

```python
class MyProvider(MemoryProvider):
    """
    Brief description of what this provider does.

    Usage:
        provider = MyProvider(
            connection_string="...",
            api_key="..."
        )

    Configuration:
        - connection_string: Database connection
        - api_key: API authentication

    Notes:
        - Requires xyz service running
        - Uses semantic search via embeddings
    """
```

---

## Publishing Providers

Once you build a provider, consider sharing it:

### 1. Create Separate Package

```
claude-agent-sdk-notion/
├── pyproject.toml
├── README.md
└── claude_agent_sdk_notion/
    ├── __init__.py
    └── provider.py
```

### 2. Depend on Core SDK

```toml
# pyproject.toml
[project]
name = "claude-agent-sdk-notion"
dependencies = [
    "claude-agent-sdk>=0.1.0",
    "notion-client>=2.0.0"
]
```

### 3. Simple Installation

```bash
pip install claude-agent-sdk-notion
```

```python
from claude_agent_sdk import BaseAgent
from claude_agent_sdk_notion import NotionProvider  # Your package!
```

---

## Reference Implementations

Check these examples in the SDK:

- **InMemoryProvider**: `claude_agent_sdk/integrations/memory/simple.py`
- **YarnnnMemory**: `claude_agent_sdk/integrations/yarnnn/memory.py`
- **YarnnnGovernance**: `claude_agent_sdk/integrations/yarnnn/governance.py`

---

## Need Help?

- Open an issue: GitHub Issues
- Check examples: `examples/` directory
- Read architecture: `docs/architecture.md`
