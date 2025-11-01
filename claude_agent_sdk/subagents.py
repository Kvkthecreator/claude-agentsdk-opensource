"""
Subagent Support for Claude Agent SDK

Implements subagent pattern inspired by official Claude Agent SDK (TypeScript).
Allows agents to delegate specialized tasks to purpose-built subagents.
"""

from typing import Any, Dict, List, Optional, Callable
from pydantic import BaseModel


class SubagentDefinition(BaseModel):
    """
    Defines a subagent's capabilities and configuration.

    Inspired by official SDK's agent definition pattern.
    """

    name: str
    """Unique identifier for the subagent"""

    description: str
    """Natural language description of when to use this subagent (for delegation)"""

    system_prompt: str
    """Subagent-specific system prompt defining role and approach"""

    tools: Optional[List[str]] = None
    """Tool names available to this subagent (None = inherit all from parent)"""

    model: Optional[str] = None
    """Model override for this subagent (None = inherit from parent)"""

    metadata: Dict[str, Any] = {}
    """Additional subagent-specific metadata"""


class SubagentRegistry:
    """
    Manages subagent definitions for an agent.

    Handles delegation logic and subagent execution.
    """

    def __init__(self, parent_agent: Any):
        """
        Initialize subagent registry.

        Args:
            parent_agent: The parent agent instance
        """
        self.parent_agent = parent_agent
        self.subagents: Dict[str, SubagentDefinition] = {}
        self.delegation_hooks: List[Callable] = []

    def register(self, definition: SubagentDefinition) -> None:
        """
        Register a subagent.

        Args:
            definition: Subagent definition
        """
        self.subagents[definition.name] = definition

    def register_multiple(self, definitions: List[SubagentDefinition]) -> None:
        """
        Register multiple subagents.

        Args:
            definitions: List of subagent definitions
        """
        for definition in definitions:
            self.register(definition)

    def get_subagent(self, name: str) -> Optional[SubagentDefinition]:
        """
        Get subagent definition by name.

        Args:
            name: Subagent name

        Returns:
            Subagent definition or None if not found
        """
        return self.subagents.get(name)

    def list_subagents(self) -> List[SubagentDefinition]:
        """
        List all registered subagents.

        Returns:
            List of subagent definitions
        """
        return list(self.subagents.values())

    def get_delegation_prompt(self) -> str:
        """
        Generate prompt section describing available subagents.

        Used in main agent's system prompt to enable delegation.

        Returns:
            Formatted prompt text describing subagents
        """
        if not self.subagents:
            return ""

        prompt_parts = [
            "\n## Available Subagents\n",
            "You can delegate tasks to specialized subagents:\n"
        ]

        for definition in self.subagents.values():
            prompt_parts.append(f"\n### {definition.name}")
            prompt_parts.append(f"{definition.description}\n")

        prompt_parts.append(
            "\nTo delegate to a subagent, use the delegate_to_subagent tool."
        )

        return "\n".join(prompt_parts)

    def add_delegation_hook(self, hook: Callable) -> None:
        """
        Add a hook called when subagent delegation occurs.

        Args:
            hook: Callable that takes (subagent_name, task, result)
        """
        self.delegation_hooks.append(hook)

    async def delegate(
        self,
        subagent_name: str,
        task: str,
        context: Optional[str] = None,
        **kwargs
    ) -> Any:
        """
        Delegate a task to a subagent.

        Args:
            subagent_name: Name of subagent to delegate to
            task: Task description for subagent
            context: Additional context
            **kwargs: Additional arguments

        Returns:
            Subagent's response

        Raises:
            ValueError: If subagent not found
        """
        subagent = self.get_subagent(subagent_name)
        if not subagent:
            raise ValueError(f"Subagent '{subagent_name}' not found")

        self.parent_agent.logger.info(
            f"Delegating to subagent: {subagent_name} - {task[:50]}..."
        )

        # Execute subagent (calls parent agent's reason method with subagent config)
        result = await self.parent_agent._execute_subagent(
            subagent=subagent,
            task=task,
            context=context,
            **kwargs
        )

        # Call delegation hooks
        for hook in self.delegation_hooks:
            try:
                hook(subagent_name, task, result)
            except Exception as e:
                self.parent_agent.logger.warning(
                    f"Delegation hook failed: {e}"
                )

        return result


def create_subagent_tool(registry: SubagentRegistry) -> Dict[str, Any]:
    """
    Create a Claude tool definition for subagent delegation.

    This tool allows the main agent to delegate tasks to subagents.

    Args:
        registry: Subagent registry

    Returns:
        Tool definition dict for Claude API
    """
    return {
        "name": "delegate_to_subagent",
        "description": """Delegate a specialized task to a subagent.

Use this when you encounter a task that matches a subagent's expertise.
Each subagent is optimized for specific types of work.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "subagent_name": {
                    "type": "string",
                    "description": "Name of the subagent to delegate to",
                    "enum": list(registry.subagents.keys())
                },
                "task": {
                    "type": "string",
                    "description": "Clear description of the task for the subagent"
                },
                "context": {
                    "type": "string",
                    "description": "Additional context the subagent needs"
                }
            },
            "required": ["subagent_name", "task"]
        },
        "function": registry.delegate
    }
