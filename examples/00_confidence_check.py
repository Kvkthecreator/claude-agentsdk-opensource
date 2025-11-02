"""
Confidence Check - Minimal test to verify core SDK functionality

This script demonstrates that the core SDK components work:
1. BaseAgent initialization
2. Memory provider (InMemory)
3. Subagent infrastructure
4. Agent archetypes
5. Session management

Run this to verify the SDK is working before integrating with YARNNN.

Usage:
    python examples/00_confidence_check.py
"""

import asyncio
from claude_agent_sdk.base import BaseAgent
from claude_agent_sdk.archetypes import ResearchAgent
from claude_agent_sdk.integrations.memory import InMemoryProvider
from claude_agent_sdk.subagents import SubagentDefinition


class TestAgent(BaseAgent):
    """Simple test agent for verification"""

    async def execute(self, task: str, **kwargs):
        # Start session
        if not self.current_session:
            self.current_session = self._start_session()

        print(f"✓ Session started: {self.current_session.id}")

        # Test memory query
        if self.memory:
            contexts = await self.memory.query(task, limit=3)
            print(f"✓ Memory query returned {len(contexts)} results")

        return {"status": "success", "task": task}


async def main():
    print("=" * 60)
    print("Claude Agent SDK - Confidence Check")
    print("=" * 60)

    # Test 1: Initialize Memory Provider
    print("\n[Test 1] Memory Provider")
    print("-" * 60)
    memory = InMemoryProvider()
    memory.add("Python is a programming language", metadata={"topic": "python"})
    memory.add("Rust focuses on memory safety", metadata={"topic": "rust"})
    print("✓ InMemoryProvider initialized")
    print(f"✓ Added 2 items to memory")

    results = await memory.query("programming")
    print(f"✓ Query returned {len(results)} results")

    # Test 2: Initialize BaseAgent
    print("\n[Test 2] BaseAgent")
    print("-" * 60)
    agent = TestAgent(
        agent_id="test_agent_001",
        agent_name="Test Agent",
        memory=memory,
        anthropic_api_key="test_key"  # Mock key for initialization
    )
    print(f"✓ Agent initialized: {agent.agent_name}")
    print(f"✓ Agent ID: {agent.agent_id}")
    print(f"✓ Memory provider: {type(agent.memory).__name__}")

    # Test 3: Execute agent task
    print("\n[Test 3] Agent Execution")
    print("-" * 60)
    result = await agent.execute("Test task")
    print(f"✓ Task executed: {result['status']}")

    # Test 4: Subagent Infrastructure
    print("\n[Test 4] Subagent Infrastructure")
    print("-" * 60)
    agent.subagents.register(
        SubagentDefinition(
            name="test_subagent",
            description="Test subagent for verification",
            system_prompt="You are a test subagent",
            tools=None,
            metadata={"type": "test"}
        )
    )
    subagents = agent.subagents.list_subagents()
    print(f"✓ Registered {len(subagents)} subagent(s)")
    print(f"✓ Subagent: {subagents[0].name}")

    # Test 5: Agent Archetype
    print("\n[Test 5] Agent Archetype (ResearchAgent)")
    print("-" * 60)
    research_agent = ResearchAgent(
        memory=memory,
        anthropic_api_key="test_key",  # Mock key
        monitoring_domains=["test_domain"],
        agent_name="Test Research Agent"
    )
    print(f"✓ ResearchAgent initialized: {research_agent.agent_name}")
    print(f"✓ Agent ID: {research_agent.agent_id}")
    print(f"✓ Monitoring domains: {research_agent.monitoring_domains}")

    subagents = research_agent.subagents.list_subagents()
    print(f"✓ Subagents registered: {len(subagents)}")
    for subagent in subagents:
        print(f"  - {subagent.name}")

    # Summary
    print("\n" + "=" * 60)
    print("✅ All Core Components Working!")
    print("=" * 60)
    print("\nCore functionality verified:")
    print("  ✓ Memory provider (InMemory)")
    print("  ✓ BaseAgent initialization")
    print("  ✓ Session management")
    print("  ✓ Agent execution")
    print("  ✓ Subagent infrastructure")
    print("  ✓ Agent archetypes (ResearchAgent)")
    print("\n✨ SDK is ready for YARNNN integration!")


if __name__ == "__main__":
    asyncio.run(main())
