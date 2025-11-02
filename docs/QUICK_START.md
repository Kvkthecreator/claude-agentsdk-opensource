# Quick Start Guide

Get started with the Claude Agent SDK in 5 minutes.

## Prerequisites

- Python 3.10 or higher
- Anthropic API key ([get one here](https://console.anthropic.com))
- (Optional) YARNNN instance for memory/governance

## Installation

```bash
# Clone the repository
git clone https://github.com/Kvkthecreator/claude-agentsdk-yarnnn.git
cd claude-agentsdk-yarnnn

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your API keys
```

## Your First Agent

### Option 1: Simple Agent (No External Memory)

```python
import asyncio
from claude_agent_sdk import BaseAgent

class SimpleAgent(BaseAgent):
    """A simple agent that just uses Claude"""
    
    async def execute(self, task: str):
        # Reason with Claude (no memory needed)
        response = await self.reason(task)
        return response

async def main():
    # Create agent (no providers needed)
    agent = SimpleAgent(
        agent_id="simple_bot",
        anthropic_api_key="sk-ant-..."
    )
    
    # Execute task
    result = await agent.execute("Explain quantum computing in simple terms")
    print(result)

asyncio.run(main())
```

### Option 2: Agent with YARNNN Memory

```python
import asyncio
from claude_agent_sdk import BaseAgent
from claude_agent_sdk.integrations.yarnnn import YarnnnMemory, YarnnnGovernance

class KnowledgeAgent(BaseAgent):
    """Agent with long-term memory"""
    
    async def execute(self, task: str):
        # Query memory for context
        if self.memory:
            contexts = await self.memory.query(task, limit=10)
            context_str = "\n".join([c.content for c in contexts])
        else:
            context_str = ""
        
        # Reason with Claude using context
        response = await self.reason(task, context=context_str)
        
        return response

async def main():
    # Setup YARNNN providers
    memory = YarnnnMemory(
    workspace_id=workspace_id,  # From request context
    basket_id="my_knowledge_basket",
        api_key="ynk_...",           # From YARNNN
        workspace_id="ws_..."         # From YARNNN
    )
    
    governance = YarnnnGovernance(
    workspace_id=workspace_id,  # From request context
    basket_id="my_knowledge_basket",
        api_key="ynk_...",
        workspace_id="ws_..."
    )
    
    # Create agent with memory
    agent = KnowledgeAgent(
        agent_id="knowledge_bot",
        memory=memory,
        governance=governance,
        anthropic_api_key="sk-ant-..."
    )
    
    # Execute task (will query memory first)
    result = await agent.execute("What do we know about AI governance?")
    print(result)

asyncio.run(main())
```

### Option 3: Use Pre-built Knowledge Agent

```python
import asyncio
from examples.knowledge_agent.agent_v2 import KnowledgeAgent
from claude_agent_sdk.integrations.yarnnn import YarnnnMemory, YarnnnGovernance

async def main():
    # Setup providers
    memory = YarnnnMemory(
    workspace_id=workspace_id,  # From request context
    basket_id="research")
    governance = YarnnnGovernance(
    workspace_id=workspace_id,  # From request context
    basket_id="research")
    
    # Create specialized knowledge agent
    agent = KnowledgeAgent(
        agent_id="research_specialist",
        agent_name="AI Research Bot",
        memory=memory,
        governance=governance,
        anthropic_api_key="sk-ant-..."
    )
    
    # Execute research task
    result = await agent.execute(
        "Research the latest developments in AI governance and add to knowledge base"
    )
    
    print(f"Session: {result['session_id']}")
    print(f"Proposals created: {len(result['proposals'])}")

asyncio.run(main())
```

## Environment Variables

Create a `.env` file:

```bash
# Required: Anthropic
ANTHROPIC_API_KEY=sk-ant-your-key-here

# Optional: YARNNN (if using YARNNN integration)
YARNNN_API_URL=https://your-yarnnn-instance.com
YARNNN_API_KEY=ynk_your-key-here
YARNNN_BASKET_ID=basket_your-basket-id  # Can also specify per agent

# Optional: Agent behavior
AGENT_AUTO_APPROVE=false
AGENT_CONFIDENCE_THRESHOLD=0.8
LOG_LEVEL=INFO
```

## Running Examples

```bash
# Simple usage examples
python examples/simple_usage.py

# Knowledge agent example
cd examples/knowledge-agent
python run.py --basket-id basket_123 --task "Research AI governance"
```

## Next Steps

- **Learn more**: Read [Architecture](./architecture.md)
- **Create custom agents**: See [Creating Agents](./creating-agents.md)
- **Add integrations**: See [Creating Integrations](./creating-integrations.md)
- **YARNNN setup**: See [YARNNN Integration](./integrations/yarnnn.md)

## Troubleshooting

### "ANTHROPIC_API_KEY must be provided"
Set the environment variable:
```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

### "YARNNN_API_KEY must be set"
If using YARNNN integration, you need:
```bash
export YARNNN_API_KEY=ynk_...
export ```

### Import errors
Make sure you're in the project directory and dependencies are installed:
```bash
pip install -r requirements.txt
```

## Getting Help

- **Documentation**: [docs/](../docs/)
- **Examples**: [examples/](../examples/)
- **Issues**: [GitHub Issues](https://github.com/Kvkthecreator/claude-agentsdk-yarnnn/issues)
