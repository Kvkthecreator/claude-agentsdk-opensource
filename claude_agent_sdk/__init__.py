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
from .interfaces import (
    MemoryProvider,
    GovernanceProvider,
    TaskProvider,
    # Lifecycle hook models
    InterruptDecision,
    StepContext,
    StepResult,
    AgentState,
    # Hook type signatures
    StepStartHook,
    StepEndHook,
    ExecuteStartHook,
    ExecuteEndHook,
    InterruptHook,
    ErrorHook,
    CheckpointHook,
)
from .session import AgentSession
from .subagents import SubagentDefinition, SubagentRegistry

__version__ = "0.2.0"

__all__ = [
    "BaseAgent",
    "MemoryProvider",
    "GovernanceProvider",
    "TaskProvider",
    "AgentSession",
    "SubagentDefinition",
    "SubagentRegistry",
    # Lifecycle hooks
    "InterruptDecision",
    "StepContext",
    "StepResult",
    "AgentState",
    "StepStartHook",
    "StepEndHook",
    "ExecuteStartHook",
    "ExecuteEndHook",
    "InterruptHook",
    "ErrorHook",
    "CheckpointHook",
]
