"""
Tests for Memory Providers

Tests the InMemoryProvider and MemoryProvider interface contract.
"""

import pytest
from claude_agent_sdk.integrations.memory import InMemoryProvider
from claude_agent_sdk.interfaces import Context, MemoryProvider


class TestInMemoryProvider:
    """Test InMemoryProvider implementation"""

    def test_initialization(self):
        """Test provider initialization"""
        memory = InMemoryProvider()

        assert len(memory) == 0
        assert isinstance(memory.data, list)
        assert str(memory) == "InMemoryProvider(items=0)"

    def test_add_content(self):
        """Test adding content to memory"""
        memory = InMemoryProvider()

        memory.add("Python is a programming language")

        assert len(memory) == 1
        assert memory.data[0].content == "Python is a programming language"

    def test_add_content_with_metadata(self):
        """Test adding content with metadata"""
        memory = InMemoryProvider()
        metadata = {"topic": "programming", "language": "python"}

        memory.add("Python is awesome", metadata=metadata)

        assert len(memory) == 1
        assert memory.data[0].content == "Python is awesome"
        assert memory.data[0].metadata == metadata
        assert memory.data[0].metadata["topic"] == "programming"

    def test_add_many(self):
        """Test adding multiple items at once"""
        memory = InMemoryProvider()

        items = [
            ("Python is a programming language", {"lang": "python"}),
            ("JavaScript is for web development", {"lang": "javascript"}),
            ("Rust focuses on safety", {"lang": "rust"})
        ]

        memory.add_many(items)

        assert len(memory) == 3
        assert memory.data[0].content.startswith("Python")
        assert memory.data[1].content.startswith("JavaScript")
        assert memory.data[2].content.startswith("Rust")

    @pytest.mark.asyncio
    async def test_query_basic(self):
        """Test basic query functionality"""
        memory = InMemoryProvider()

        memory.add("Python is a high-level programming language")
        memory.add("JavaScript is used for web development")
        memory.add("Rust focuses on safety and performance")

        results = await memory.query("Python")

        assert len(results) == 1
        assert "Python" in results[0].content

    @pytest.mark.asyncio
    async def test_query_multiple_results(self):
        """Test query returning multiple results"""
        memory = InMemoryProvider()

        memory.add("Python is a programming language")
        memory.add("JavaScript is a programming language")
        memory.add("Rust is a programming language")

        results = await memory.query("programming")

        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_query_with_limit(self):
        """Test query with result limit"""
        memory = InMemoryProvider()

        for i in range(10):
            memory.add(f"Programming language number {i}")

        results = await memory.query("programming", limit=5)

        assert len(results) == 5

    @pytest.mark.asyncio
    async def test_query_with_filters(self):
        """Test query with metadata filters"""
        memory = InMemoryProvider()

        memory.add("Python is awesome", metadata={"lang": "python", "type": "interpreted"})
        memory.add("JavaScript is cool", metadata={"lang": "javascript", "type": "interpreted"})
        memory.add("Rust is safe", metadata={"lang": "rust", "type": "compiled"})

        # Query with a word that appears in all items, then filter
        results = await memory.query("is", filters={"type": "interpreted"})

        # Should only return interpreted languages
        assert len(results) == 2
        for result in results:
            assert result.metadata["type"] == "interpreted"

    @pytest.mark.asyncio
    async def test_query_with_multiple_filters(self):
        """Test query with multiple filter criteria"""
        memory = InMemoryProvider()

        memory.add("Python fact", metadata={"lang": "python", "difficulty": "easy", "type": "interpreted"})
        memory.add("JavaScript fact", metadata={"lang": "javascript", "difficulty": "medium", "type": "interpreted"})
        memory.add("Rust fact", metadata={"lang": "rust", "difficulty": "hard", "type": "compiled"})

        results = await memory.query(
            "fact",
            filters={"type": "interpreted", "difficulty": "easy"}
        )

        assert len(results) == 1
        assert results[0].metadata["lang"] == "python"

    @pytest.mark.asyncio
    async def test_query_no_results(self):
        """Test query with no matching results"""
        memory = InMemoryProvider()

        memory.add("Python is a programming language")
        memory.add("JavaScript is for web development")

        results = await memory.query("quantum physics")

        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_query_case_insensitive(self):
        """Test that query is case insensitive"""
        memory = InMemoryProvider()

        memory.add("Python is a Programming Language")

        results_lower = await memory.query("python")
        results_upper = await memory.query("PYTHON")
        results_mixed = await memory.query("PyThOn")

        assert len(results_lower) == 1
        assert len(results_upper) == 1
        assert len(results_mixed) == 1

    @pytest.mark.asyncio
    async def test_query_word_matching(self):
        """Test query matches individual words"""
        memory = InMemoryProvider()

        memory.add("Python is great for data science")
        memory.add("JavaScript is used in web development")

        # Should match because "data" is a word in the content
        results = await memory.query("data science programming")

        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_store_context(self):
        """Test storing a Context object"""
        memory = InMemoryProvider()

        context = Context(
            content="Test content",
            metadata={"test": "value"},
            confidence=0.9
        )

        context_id = await memory.store(context)

        assert context_id == "0"  # First item
        assert len(memory) == 1
        assert memory.data[0].content == "Test content"
        assert memory.data[0].confidence == 0.9

    @pytest.mark.asyncio
    async def test_store_multiple_contexts(self):
        """Test storing multiple Context objects"""
        memory = InMemoryProvider()

        context1 = Context(content="First", metadata={})
        context2 = Context(content="Second", metadata={})
        context3 = Context(content="Third", metadata={})

        id1 = await memory.store(context1)
        id2 = await memory.store(context2)
        id3 = await memory.store(context3)

        assert id1 == "0"
        assert id2 == "1"
        assert id3 == "2"
        assert len(memory) == 3

    @pytest.mark.asyncio
    async def test_retrieve_context(self):
        """Test retrieving a Context by ID"""
        memory = InMemoryProvider()

        memory.add("Test content", metadata={"key": "value"})

        context = await memory.retrieve("0")

        assert context is not None
        assert context.content == "Test content"
        assert context.metadata["key"] == "value"

    @pytest.mark.asyncio
    async def test_retrieve_nonexistent_context(self):
        """Test retrieving a nonexistent Context"""
        memory = InMemoryProvider()

        memory.add("Test content")

        context = await memory.retrieve("999")

        assert context is None

    @pytest.mark.asyncio
    async def test_retrieve_invalid_id(self):
        """Test retrieving with invalid ID format"""
        memory = InMemoryProvider()

        memory.add("Test content")

        context = await memory.retrieve("invalid")

        assert context is None

    def test_clear(self):
        """Test clearing all data"""
        memory = InMemoryProvider()

        memory.add("Item 1")
        memory.add("Item 2")
        memory.add("Item 3")

        assert len(memory) == 3

        memory.clear()

        assert len(memory) == 0

    def test_repr(self):
        """Test string representation"""
        memory = InMemoryProvider()

        assert repr(memory) == "InMemoryProvider(items=0)"

        memory.add("Test 1")
        memory.add("Test 2")

        assert repr(memory) == "InMemoryProvider(items=2)"

    @pytest.mark.asyncio
    async def test_empty_memory_query(self):
        """Test querying empty memory"""
        memory = InMemoryProvider()

        results = await memory.query("anything")

        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_workflow_add_query_retrieve(self):
        """Test a complete workflow: add, query, retrieve"""
        memory = InMemoryProvider()

        # Add content
        memory.add("Python programming tutorial", metadata={"topic": "programming"})
        memory.add("JavaScript web development", metadata={"topic": "web"})
        memory.add("Python data science", metadata={"topic": "data"})

        # Query
        results = await memory.query("Python", limit=5)

        assert len(results) == 2

        # Store a new context
        new_context = Context(content="Rust systems programming", metadata={"topic": "systems"})
        context_id = await memory.store(new_context)

        # Retrieve it
        retrieved = await memory.retrieve(context_id)

        assert retrieved is not None
        assert retrieved.content == "Rust systems programming"


class TestMemoryProviderInterface:
    """Test MemoryProvider interface compliance"""

    @pytest.mark.asyncio
    async def test_implements_query(self):
        """Test that InMemoryProvider implements query"""
        memory = InMemoryProvider()

        assert hasattr(memory, 'query')
        assert callable(memory.query)

        # Should be async
        memory.add("test")
        result = await memory.query("test")
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_implements_get_all(self):
        """Test that provider implements get_all"""
        memory = InMemoryProvider()

        # This should exist per the interface
        assert hasattr(memory, 'get_all')

    @pytest.mark.asyncio
    async def test_implements_summarize(self):
        """Test that provider implements summarize"""
        memory = InMemoryProvider()

        assert hasattr(memory, 'summarize')

        summary = await memory.summarize()
        assert isinstance(summary, dict)
        assert 'provider' in summary or 'total_items' in summary
