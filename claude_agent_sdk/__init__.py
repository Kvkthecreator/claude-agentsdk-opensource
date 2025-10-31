"""
Claude Agent SDK - Generic framework for building autonomous agents

This SDK provides:
- BaseAgent: Foundation for all agent types
- Abstract providers: MemoryProvider, GovernanceProvider, TaskProvider
- Session management: Agent identity and Claude session tracking
- Pluggable integrations: YARNNN, Notion, GitHub, etc.

Example:
    from claude_agent_sdk import BaseAgent
    from claude_agent_sdk.integrations.yarnnn import YarnnnMemory, YarnnnGovernance

    class MyAgent(BaseAgent):
        async def execute(self, task: str):
            context = await self.memory.query(task)
            # ... agent logic

    agent = MyAgent(
        agent_id="my_agent_001",
        memory=YarnnnMemory(...),
        governance=YarnnnGovernance(...),
        anthropic_api_key="sk-ant-..."
    )
"""

from .base import BaseAgent
from .interfaces import MemoryProvider, GovernanceProvider, TaskProvider
from .session import AgentSession

__version__ = "0.1.0"

__all__ = [
    "BaseAgent",
    "MemoryProvider",
    "GovernanceProvider",
    "TaskProvider",
    "AgentSession",
]
