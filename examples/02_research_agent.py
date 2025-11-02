"""
Research Agent Example

Demonstrates the Research Agent archetype with subagents for:
- Continuous monitoring
- Deep-dive research
- Signal detection and synthesis

This archetype uses four subagents:
1. web_monitor - Monitor websites and blogs
2. competitor_tracker - Track competitor activity
3. social_listener - Monitor social media
4. analyst - Synthesize findings

Usage:
    python examples/02_research_agent.py
"""

import asyncio
import os
from dotenv import load_dotenv

from claude_agent_sdk.archetypes import ResearchAgent
from claude_agent_sdk.integrations.memory import InMemoryProvider
from claude_agent_sdk.integrations.yarnnn import YarnnnMemory, YarnnnGovernance


# Load environment variables
load_dotenv()


async def main():
    """Demonstrate Research Agent capabilities."""

    print("=" * 60)
    print("Research Agent Example")
    print("=" * 60)

    # Initialize providers
    # Option 1: Use in-memory provider (for testing)
    memory = InMemoryProvider()

    # Option 2: Use YARNNN provider (for production)
    # Uncomment these lines and comment out Option 1
    # memory = YarnnnMemory(basket_id="market_intelligence")
    # governance = YarnnnGovernance(basket_id="market_intelligence")

    # Initialize Research Agent
    agent = ResearchAgent(
        memory=memory,
        governance=None,  # Use governance for production
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),

        # Configure monitoring
        monitoring_domains=[
            "ai_agents",
            "competitors",
            "market_trends"
        ],
        monitoring_frequency="daily",

        # Signal detection
        signal_threshold=0.7,
        synthesis_mode="insights",

        # Agent identity
        agent_name="Market Intelligence Bot"
    )

    print(f"\n✓ Agent initialized: {agent.agent_name}")
    print(f"  Agent ID: {agent.agent_id}")
    print(f"  Monitoring domains: {', '.join(agent.monitoring_domains)}")
    print(f"  Subagents registered: {len(agent.subagents.list_subagents())}")

    # List available subagents
    print("\n📋 Available subagents:")
    for subagent in agent.subagents.list_subagents():
        print(f"  - {subagent.name}: {subagent.description}")

    # Example 1: Continuous Monitoring
    print("\n" + "=" * 60)
    print("Example 1: Continuous Monitoring")
    print("=" * 60)
    print("\nThis would typically run on a schedule (daily/hourly)")
    print("It delegates to multiple monitoring subagents in parallel")

    # Note: Actual monitoring requires web access
    # For this example, we'll show the structure
    print("\n⏩ Skipping actual monitoring (requires API access)")
    print("   In production, this would:")
    print("   1. Delegate to web_monitor, competitor_tracker, social_listener")
    print("   2. Collect signals from each")
    print("   3. Synthesize with analyst subagent")
    print("   4. Propose insights to memory (via governance)")

    # Example 2: Deep Dive Research
    print("\n" + "=" * 60)
    print("Example 2: Deep Dive Research")
    print("=" * 60)
    print("\nOn-demand comprehensive research on a topic")

    # Add some context to memory first
    memory.add(
        content="AI agent market is growing rapidly with new entrants like AutoGPT, BabyAGI",
        metadata={"topic": "ai_agents", "source": "previous_research"}
    )
    memory.add(
        content="Key players include: OpenAI (Assistants API), Anthropic (Claude), Microsoft (Copilot Studio)",
        metadata={"topic": "ai_agents", "source": "market_analysis"}
    )

    print("\n📚 Sample memory context added")
    print("\n⏩ Deep dive would:")
    print("   1. Query existing memory for context")
    print("   2. Conduct comprehensive research")
    print("   3. Synthesize findings")
    print("   4. Propose to memory for storage")

    # Example 3: Task Routing
    print("\n" + "=" * 60)
    print("Example 3: Automatic Task Routing")
    print("=" * 60)
    print("\nResearch Agent automatically routes tasks to monitor() or deep_dive()")

    print("\n Task: 'Monitor competitors' → Routes to monitor()")
    print(" Task: 'Research AI governance' → Routes to deep_dive()")

    # Example 4: Subagent Delegation
    print("\n" + "=" * 60)
    print("Example 4: Direct Subagent Delegation")
    print("=" * 60)
    print("\nYou can also delegate directly to specific subagents")

    print("\n⏩ Example delegation:")
    print("   await agent.subagents.delegate(")
    print("       subagent_name='analyst',")
    print("       task='Synthesize recent findings',")
    print("       context=monitoring_data")
    print("   )")

    # Inspect agent configuration
    print("\n" + "=" * 60)
    print("Agent Configuration")
    print("=" * 60)
    print(f"\nModel: {agent.model}")
    print(f"Memory provider: {type(agent.memory).__name__}")
    print(f"Governance: {type(agent.governance).__name__ if agent.governance else 'Not configured'}")
    print(f"Monitoring frequency: {agent.monitoring_frequency}")
    print(f"Signal threshold: {agent.signal_threshold}")
    print(f"Synthesis mode: {agent.synthesis_mode}")

    print("\n" + "=" * 60)
    print("Example Complete!")
    print("=" * 60)
    print("\n💡 Next steps:")
    print("   1. Configure YARNNN providers for production")
    print("   2. Set up scheduling for monitor() calls")
    print("   3. Add web search/scraping tools")
    print("   4. Customize subagent prompts for your domain")


if __name__ == "__main__":
    asyncio.run(main())
