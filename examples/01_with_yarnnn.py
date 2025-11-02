"""
Simple usage example for the Claude Agent SDK with YARNNN integration

This demonstrates the new generic architecture.
"""

import asyncio
import os
from claude_agent_sdk import BaseAgent
from claude_agent_sdk.integrations.yarnnn import YarnnnMemory, YarnnnGovernance


# Example 1: Simple agent with YARNNN
async def example_1_simple_agent():
    """Basic agent with YARNNN memory and governance"""

    print("=" * 60)
    print("Example 1: Simple Knowledge Agent")
    print("=" * 60)

    # Initialize YARNNN providers
    memory = YarnnnMemory(
        workspace_id=os.getenv("YARNNN_WORKSPACE_ID"),
        basket_id=os.getenv("YARNNN_BASKET_ID", "basket_demo"),
        api_url=os.getenv("YARNNN_API_URL", "http://localhost:3000"),
        api_key=os.getenv("YARNNN_API_KEY"))

    governance = YarnnnGovernance(
        workspace_id=os.getenv("YARNNN_WORKSPACE_ID"),
        basket_id=os.getenv("YARNNN_BASKET_ID", "basket_demo"),
        api_url=os.getenv("YARNNN_API_URL", "http://localhost:3000"),
        api_key=os.getenv("YARNNN_API_KEY"))

    # Import the new KnowledgeAgent
    from knowledge-agent.agent_v2 import KnowledgeAgent

    # Create agent with persistent identity
    agent = KnowledgeAgent(
        agent_id="demo_research_bot",
        agent_name="Demo Research Assistant",
        memory=memory,
        governance=governance,
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY")
    )

    print(f"\nAgent created: {agent}")
    print(f"Agent ID: {agent.agent_id}")
    print(f"Agent Name: {agent.agent_name}")

    # Execute a task
    print("\n--- Executing Research Task ---")
    result = await agent.execute("Research the key principles of AI governance")

    print(f"\nTask completed!")
    print(f"Session ID: {result['session_id']}")
    print(f"Claude Session: {result['claude_session_id']}")
    print(f"Proposals Created: {len(result['proposals'])}")

    # Get knowledge summary
    print("\n--- Knowledge Summary ---")
    summary = await agent.summarize_knowledge()
    print(f"Total blocks: {summary.get('total_blocks', 0)}")
    print(f"Total concepts: {summary.get('total_context_items', 0)}")


# Example 2: Multiple agents sharing memory
async def example_2_multiple_agents():
    """Multiple agents working on shared knowledge base"""

    print("\n" + "=" * 60)
    print("Example 2: Multiple Agents with Shared Memory")
    print("=" * 60)

    # Shared memory provider
    shared_memory = YarnnnMemory(
        workspace_id=os.getenv("YARNNN_WORKSPACE_ID"),
        basket_id=os.getenv("YARNNN_BASKET_ID", "basket_shared"),
    )

    shared_governance = YarnnnGovernance(
        workspace_id=os.getenv("YARNNN_WORKSPACE_ID"),
        basket_id=os.getenv("YARNNN_BASKET_ID", "basket_shared"),
    )

    from knowledge-agent.agent_v2 import KnowledgeAgent

    # Agent 1: Research focused
    research_agent = KnowledgeAgent(
        agent_id="research_specialist",
        agent_name="Research Specialist",
        memory=shared_memory,
        governance=shared_governance,
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY")
    )

    # Agent 2: Synthesis focused
    synthesis_agent = KnowledgeAgent(
        agent_id="synthesis_specialist",
        agent_name="Synthesis Specialist",
        memory=shared_memory,  # Same memory!
        governance=shared_governance,
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY")
    )

    print(f"\nAgent 1: {research_agent.agent_name} ({research_agent.agent_id})")
    print(f"Agent 2: {synthesis_agent.agent_name} ({synthesis_agent.agent_id})")

    # Agent 1 researches
    print("\n--- Research Agent: Gathering Information ---")
    await research_agent.execute("Research AI safety principles")

    # Agent 2 synthesizes (can see Agent 1's work via shared memory)
    print("\n--- Synthesis Agent: Creating Summary ---")
    await synthesis_agent.execute("Summarize the AI safety principles we know about")

    print("\nBoth agents contributed to the same knowledge base!")


# Example 3: Session resumption
async def example_3_session_resumption():
    """Resuming an agent session"""

    print("\n" + "=" * 60)
    print("Example 3: Session Resumption")
    print("=" * 60)

    memory = YarnnnMemory(
        workspace_id=os.getenv("YARNNN_WORKSPACE_ID"),
        basket_id=os.getenv("YARNNN_BASKET_ID", "basket_demo"))
    governance = YarnnnGovernance(
        workspace_id=os.getenv("YARNNN_WORKSPACE_ID"),
        basket_id=os.getenv("YARNNN_BASKET_ID", "basket_demo"))

    from knowledge-agent.agent_v2 import KnowledgeAgent

    # Start first session
    print("\n--- Session 1: Initial Research ---")
    agent = KnowledgeAgent(
        agent_id="persistent_researcher",
        memory=memory,
        governance=governance,
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY")
    )

    result1 = await agent.execute("Start researching quantum computing")
    session_id_1 = result1["session_id"]
    claude_session_1 = result1["claude_session_id"]

    print(f"Session 1 ID: {session_id_1}")
    print(f"Claude Session 1: {claude_session_1}")

    # Resume session later (e.g., next day)
    print("\n--- Session 2: Continue Research (Resumed) ---")
    agent_resumed = KnowledgeAgent(
        agent_id="persistent_researcher",  # Same agent ID!
        memory=memory,
        governance=governance,
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        claude_session_id=claude_session_1  # Resume Claude conversation
    )

    result2 = await agent_resumed.execute(
        "Continue researching quantum computing, focusing on applications",
        resume_session=True  # Resume Claude conversation
    )

    print(f"Session 2 ID: {result2['session_id']}")
    print(f"Claude Session 2: {result2['claude_session_id']}")
    print("\nAgent resumed previous conversation context!")


# Example 4: Agent without governance (read-only)
async def example_4_readonly_agent():
    """Agent with only memory (no governance) for read-only operations"""

    print("\n" + "=" * 60)
    print("Example 4: Read-Only Agent (No Governance)")
    print("=" * 60)

    from claude_agent_sdk import BaseAgent

    class ReadOnlyAgent(BaseAgent):
        """Simple read-only agent"""

        async def execute(self, task: str):
            # Query memory
            if self.memory:
                contexts = await self.memory.query(task, limit=10)
                context_str = "\n".join([c.content for c in contexts])
            else:
                context_str = "No memory available"

            # Reason with Claude (no tools, just conversation)
            response = await self.reason(task, context=context_str)

            return response

    # Initialize with only memory (no governance)
    memory_only = YarnnnMemory(
        workspace_id=os.getenv("YARNNN_WORKSPACE_ID"),
        basket_id=os.getenv("YARNNN_BASKET_ID", "basket_demo"))

    agent = ReadOnlyAgent(
        agent_id="readonly_assistant",
        agent_type="readonly",
        memory=memory_only,  # Memory only
        governance=None,  # No governance
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY")
    )

    print(f"\nAgent: {agent}")
    print(f"Has Memory: {agent.memory is not None}")
    print(f"Has Governance: {agent.governance is not None}")

    # Use agent for Q&A (no proposals)
    print("\n--- Asking Question ---")
    response = await agent.execute("What do we know about AI governance?")
    print("\nAgent answered based on existing knowledge (no new proposals)")


async def main():
    """Run all examples"""
    print("Claude Agent SDK - Usage Examples\n")

    # Check environment variables
    required_vars = ["ANTHROPIC_API_KEY", "YARNNN_API_KEY", "YARNNN_WORKSPACE_ID"]
    missing = [var for var in required_vars if not os.getenv(var)]

    if missing:
        print(f"⚠️  Missing environment variables: {', '.join(missing)}")
        print("\nPlease set the following:")
        print("  - ANTHROPIC_API_KEY: Your Anthropic API key")
        print("  - YARNNN_API_KEY: Your YARNNN API key")
        print("  - YARNNN_WORKSPACE_ID: Your YARNNN workspace ID")
        print("  - YARNNN_BASKET_ID (optional): Basket ID to use")
        print("  - YARNNN_API_URL (optional): YARNNN API URL (default: http://localhost:3000)")
        return

    try:
        # Run examples
        await example_1_simple_agent()
        await example_2_multiple_agents()
        await example_3_session_resumption()
        await example_4_readonly_agent()

        print("\n" + "=" * 60)
        print("✅ All examples completed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
