"""
Minimal Agent Example - No Backend Required!

This example shows the simplest possible agent using in-memory storage.
You only need an Anthropic API key - no other services required.

Perfect for:
- Quick prototyping
- Learning the Agent SDK
- Testing ideas without setup
"""

import asyncio
import os
from claude_agent_sdk import BaseAgent
from claude_agent_sdk.integrations.memory import InMemoryProvider


class SimpleAgent(BaseAgent):
    """
    Simple agent that uses in-memory storage.

    No external dependencies beyond Claude API.
    """

    async def execute(self, task: str, **kwargs):
        """Execute a task with memory context"""

        # Start session
        if not self.current_session:
            self.current_session = self._start_session()

        # Query memory for relevant context
        if self.memory:
            contexts = await self.memory.query(task, limit=5)
            if contexts:
                context_str = "\n\n".join([
                    f"• {ctx.content}" for ctx in contexts
                ])
                context_str = f"Relevant context from memory:\n{context_str}"
            else:
                context_str = "No relevant context found in memory."
        else:
            context_str = ""

        # Reason with Claude
        system_prompt = """You are a helpful research assistant.

If context is provided from memory, use it to inform your response.
Be concise and practical in your answers."""

        response = await self.reason(
            task=task,
            context=context_str,
            system_prompt=system_prompt
        )

        # Extract text from response
        result_text = ""
        for block in response.content:
            if hasattr(block, 'text'):
                result_text += block.text

        return {
            "session_id": self.current_session.id,
            "result": result_text,
            "contexts_used": len(contexts) if contexts else 0
        }


async def main():
    """Run the minimal agent example"""

    # Check for API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ Please set ANTHROPIC_API_KEY environment variable")
        print("\nExample:")
        print('  export ANTHROPIC_API_KEY="sk-ant-..."')
        return

    print("=" * 60)
    print("Minimal Agent - No Backend Required!")
    print("=" * 60)

    # Create in-memory provider (no setup needed)
    memory = InMemoryProvider()

    # Add some initial knowledge
    print("\n📝 Adding some knowledge to memory...")
    memory.add("Python is a high-level programming language known for readability")
    memory.add("JavaScript is the primary language for web browser programming")
    memory.add("Rust is a systems programming language focused on safety and performance")
    memory.add("Go is designed for simplicity and efficient concurrent programming")
    print(f"   Added {len(memory)} items to memory")

    # Create agent
    print("\n🤖 Creating agent...")
    agent = SimpleAgent(
        agent_id="demo_agent",
        agent_name="Demo Assistant",
        memory=memory,
        anthropic_api_key=api_key,
        model="claude-sonnet-4"
    )
    print(f"   Agent: {agent.agent_name} ({agent.agent_id})")

    # Execute a task
    print("\n💭 Asking agent a question...")
    print("   Question: 'Tell me about Python'")

    result = await agent.execute("Tell me about Python")

    print("\n📤 Response:")
    print(f"   {result['result']}")
    print(f"\n   Contexts used: {result['contexts_used']}")
    print(f"   Session ID: {result['session_id']}")

    # Ask another question
    print("\n" + "-" * 60)
    print("\n💭 Asking another question...")
    print("   Question: 'What about Rust?'")

    result2 = await agent.execute("What about Rust?")

    print("\n📤 Response:")
    print(f"   {result2['result']}")
    print(f"\n   Contexts used: {result2['contexts_used']}")

    # Show memory stats
    print("\n" + "=" * 60)
    print(f"✅ Demo complete! Memory contains {len(memory)} items")
    print("=" * 60)

    print("\n💡 Next Steps:")
    print("   1. See examples/01_with_yarnnn.py for persistent memory")
    print("   2. Read docs/BUILDING_PROVIDERS.md to create custom providers")
    print("   3. Check examples/simple_usage.py for more patterns")


if __name__ == "__main__":
    asyncio.run(main())
