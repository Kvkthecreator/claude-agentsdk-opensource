"""
Show Test Examples - Demonstrates what the tests verify

This script runs the same checks as the automated tests but with visible output
showing exactly what's being verified.
"""

import asyncio
from claude_agent_sdk.base import BaseAgent
from claude_agent_sdk.integrations.memory import InMemoryProvider
from claude_agent_sdk.session import AgentSession
from claude_agent_sdk.archetypes import ResearchAgent


class DemoAgent(BaseAgent):
    async def execute(self, task: str, **kwargs):
        if not self.current_session:
            self.current_session = self._start_session()
        return {"status": "success"}


async def main():
    print("=" * 70)
    print("TEST EXAMPLES - What the automated tests verify")
    print("=" * 70)

    # Example 1: Agent Initialization
    print("\n" + "=" * 70)
    print("TEST 1: Agent Initialization")
    print("=" * 70)
    print("\nWhat we're testing:")
    print("  - Agent ID is set correctly")
    print("  - Agent type defaults to 'generic'")
    print("  - Model defaults to 'claude-sonnet-4-5'")
    print("  - Providers are optional (None by default)")

    agent = DemoAgent(
        agent_id="test_001",
        anthropic_api_key="mock_key"
    )

    print("\nActual values:")
    print(f"  ✓ agent.agent_id = '{agent.agent_id}'")
    print(f"  ✓ agent.agent_type = '{agent.agent_type}'")
    print(f"  ✓ agent.model = '{agent.model}'")
    print(f"  ✓ agent.memory = {agent.memory}")
    print(f"  ✓ agent.governance = {agent.governance}")

    assert agent.agent_id == "test_001", "Agent ID should match"
    assert agent.agent_type == "generic", "Default type should be generic"
    assert agent.model == "claude-sonnet-4-5", "Default model should be sonnet-4-5"
    assert agent.memory is None, "Memory should be None by default"
    print("\n  ✅ All assertions passed!")

    # Example 2: Memory Provider
    print("\n" + "=" * 70)
    print("TEST 2: Memory Provider - Add and Query")
    print("=" * 70)
    print("\nWhat we're testing:")
    print("  - Can add content to memory")
    print("  - Can query content back")
    print("  - Query is case-insensitive")
    print("  - Metadata filtering works")

    memory = InMemoryProvider()

    # Add content
    memory.add("Python is a programming language", metadata={"lang": "python"})
    memory.add("Rust is a systems language", metadata={"lang": "rust"})
    memory.add("JavaScript runs in browsers", metadata={"lang": "javascript"})

    print("\nAdded 3 items to memory")

    # Query - case insensitive
    results = await memory.query("PYTHON")
    print(f"\nQuery 'PYTHON' (uppercase): {len(results)} results")
    print(f"  ✓ Result content: '{results[0].content[:50]}...'")
    assert len(results) == 1, "Should find 1 result"

    # Query with metadata filter
    results = await memory.query("language", filters={"lang": "rust"})
    print(f"\nQuery 'language' with filter lang='rust': {len(results)} results")
    print(f"  ✓ Result content: '{results[0].content[:50]}...'")
    assert len(results) == 1, "Should find 1 result with filter"
    assert "Rust" in results[0].content, "Should find Rust content"

    print("\n  ✅ All assertions passed!")

    # Example 3: Session Management
    print("\n" + "=" * 70)
    print("TEST 3: Session Management")
    print("=" * 70)
    print("\nWhat we're testing:")
    print("  - Sessions have unique IDs")
    print("  - Sessions track agent_id")
    print("  - Sessions can be completed")
    print("  - Sessions track errors and proposals")

    session = AgentSession(
        agent_id="test_agent_001",
        claude_session_id="claude_abc123"
    )

    print("\nCreated session:")
    print(f"  ✓ Session ID: {session.id}")
    print(f"  ✓ Agent ID: {session.agent_id}")
    print(f"  ✓ Claude session ID: {session.claude_session_id}")
    print(f"  ✓ Status: {session.status}")
    print(f"  ✓ Started at: {session.started_at}")

    assert session.agent_id == "test_agent_001", "Agent ID should match"
    assert session.status == "active", "New session should be active"
    assert session.ended_at is None, "Active session has no end time"

    # Track work
    session.add_proposal("prop_123")
    session.add_proposal("prop_456")
    session.add_error(ValueError("test error"))

    print("\nTracked work:")
    print(f"  ✓ Proposals created: {len(session.proposals_created)}")
    print(f"  ✓ Errors: {len(session.errors)}")

    assert len(session.proposals_created) == 2, "Should track proposals"
    assert len(session.errors) == 1, "Should track errors"

    # Complete session
    session.complete()
    print(f"\nCompleted session:")
    print(f"  ✓ Status: {session.status}")
    print(f"  ✓ Ended at: {session.ended_at}")

    assert session.status == "completed", "Should be completed"
    assert session.ended_at is not None, "Should have end time"

    print("\n  ✅ All assertions passed!")

    # Example 4: Agent with Memory
    print("\n" + "=" * 70)
    print("TEST 4: Agent with Memory Provider")
    print("=" * 70)
    print("\nWhat we're testing:")
    print("  - Agent can be initialized with memory")
    print("  - Agent can access memory during execution")

    memory = InMemoryProvider()
    memory.add("Test knowledge 1")
    memory.add("Test knowledge 2")

    agent = DemoAgent(
        agent_id="agent_with_memory",
        memory=memory,
        anthropic_api_key="mock_key"
    )

    print("\nAgent with memory:")
    print(f"  ✓ Agent ID: {agent.agent_id}")
    print(f"  ✓ Memory provider: {type(agent.memory).__name__}")

    # Agent can query memory
    contexts = await agent.memory.query("knowledge")
    print(f"  ✓ Memory query returned: {len(contexts)} results")

    assert agent.memory is not None, "Agent should have memory"
    assert len(contexts) == 2, "Should find knowledge in memory"

    print("\n  ✅ All assertions passed!")

    # Example 5: Subagent Registration
    print("\n" + "=" * 70)
    print("TEST 5: Subagent Registration (ResearchAgent)")
    print("=" * 70)
    print("\nWhat we're testing:")
    print("  - Archetypes automatically register subagents")
    print("  - Subagents have names and descriptions")
    print("  - Subagents have system prompts")

    research_agent = ResearchAgent(
        memory=memory,
        anthropic_api_key="mock_key",
        monitoring_domains=["test_domain"],
        agent_name="Test Researcher"
    )

    print("\nResearchAgent initialized:")
    print(f"  ✓ Agent ID: {research_agent.agent_id}")
    print(f"  ✓ Agent name: {research_agent.agent_name}")
    print(f"  ✓ Monitoring domains: {research_agent.monitoring_domains}")

    subagents = research_agent.subagents.list_subagents()
    print(f"\nSubagents registered: {len(subagents)}")

    for subagent in subagents:
        print(f"\n  Subagent: {subagent.name}")
        print(f"    - Description: {subagent.description[:60]}...")
        print(f"    - Has system prompt: {len(subagent.system_prompt) > 0}")
        print(f"    - Tools: {subagent.tools}")

        assert subagent.name, "Subagent should have name"
        assert subagent.description, "Subagent should have description"
        assert subagent.system_prompt, "Subagent should have system prompt"

    assert len(subagents) == 4, "ResearchAgent should have 4 subagents"

    print("\n  ✅ All assertions passed!")

    # Example 6: Session Integration
    print("\n" + "=" * 70)
    print("TEST 6: Agent Session Integration")
    print("=" * 70)
    print("\nWhat we're testing:")
    print("  - Agent creates session on first execution")
    print("  - Session tracks agent activity")

    agent = DemoAgent(
        agent_id="session_agent",
        anthropic_api_key="mock_key"
    )

    print("\nBefore execution:")
    print(f"  ✓ Current session: {agent.current_session}")

    assert agent.current_session is None, "No session before execution"

    # Execute task
    result = await agent.execute("Test task")

    print("\nAfter execution:")
    print(f"  ✓ Session created: {agent.current_session.id}")
    print(f"  ✓ Session agent_id: {agent.current_session.agent_id}")
    print(f"  ✓ Session status: {agent.current_session.status}")
    print(f"  ✓ Task result: {result}")

    assert agent.current_session is not None, "Session should be created"
    assert agent.current_session.agent_id == "session_agent", "Session tracks agent"
    assert agent.current_session.status == "active", "Session should be active"
    assert result["status"] == "success", "Task should complete"

    print("\n  ✅ All assertions passed!")

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print("\n✅ All 6 test examples passed!")
    print("\nWhat this proves:")
    print("  1. ✓ Agent initialization works correctly")
    print("  2. ✓ Memory provider stores and queries data")
    print("  3. ✓ Session management tracks agent activity")
    print("  4. ✓ Agents integrate with memory providers")
    print("  5. ✓ Archetypes register subagents automatically")
    print("  6. ✓ Session creation works during execution")
    print("\n🎯 These same checks run in the automated test suite (83 tests)")
    print("   Run: pytest tests/ -v")


if __name__ == "__main__":
    asyncio.run(main())
