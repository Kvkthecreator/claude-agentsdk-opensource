"""
BaseAgent - Foundation for all YARNNN agents

This class provides the core infrastructure that all agents inherit:
- Claude SDK integration for reasoning and tool use
- YARNNN client for substrate interaction
- Memory and governance layer abstractions
- Autonomous operation loop
"""

import os
import logging
from typing import Any, Dict, List, Optional
from anthropic import Anthropic, AsyncAnthropic
from integrations.yarnnn import YarnnnClient, get_yarnnn_tools
from .memory import MemoryLayer
from .governance import GovernanceLayer


# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class BaseAgent:
    """
    Base class for all YARNNN agents

    Provides core functionality for autonomous agents that use:
    - Claude for reasoning and tool calling
    - YARNNN for long-term governed memory
    - Governance workflow for substrate changes

    Usage:
        class MyAgent(BaseAgent):
            async def execute(self, task: str) -> str:
                # 1. Query memory for context
                context = await self.memory.query(task)

                # 2. Reason with Claude
                response = await self.reason(task, context)

                # 3. Propose changes if needed
                if response.needs_memory_update:
                    await self.governance.propose(response.changes)

                return response.result

        agent = MyAgent(
            basket_id="basket_123",
            anthropic_api_key="sk-ant-...",
            yarnnn_client=yarnnn_client
        )

        result = await agent.execute("Research AI governance")
    """

    def __init__(
        self,
        basket_id: str,
        anthropic_api_key: Optional[str] = None,
        yarnnn_client: Optional[YarnnnClient] = None,
        model: str = "claude-3-5-sonnet-20241022",
        auto_approve: bool = False,
        confidence_threshold: float = 0.8,
        max_retries: int = 3
    ):
        """
        Initialize base agent

        Args:
            basket_id: YARNNN basket to operate on
            anthropic_api_key: Anthropic API key (default: from env)
            yarnnn_client: YARNNN client instance (default: auto-created)
            model: Claude model to use
            auto_approve: Auto-approve high-confidence proposals (not recommended)
            confidence_threshold: Threshold for auto-approval
            max_retries: Maximum retries for failed operations
        """
        self.basket_id = basket_id
        self.model = model
        self.auto_approve = auto_approve or os.getenv("AGENT_AUTO_APPROVE", "false").lower() == "true"
        self.confidence_threshold = float(os.getenv("AGENT_CONFIDENCE_THRESHOLD", str(confidence_threshold)))
        self.max_retries = int(os.getenv("AGENT_MAX_RETRIES", str(max_retries)))

        # Initialize Claude client
        api_key = anthropic_api_key or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY must be provided or set in environment")

        self.claude = AsyncAnthropic(api_key=api_key)

        # Initialize YARNNN client
        self.yarnnn = yarnnn_client or YarnnnClient()

        # Initialize layers
        self.memory = MemoryLayer(self.yarnnn, self.basket_id)
        self.governance = GovernanceLayer(
            self.yarnnn,
            self.basket_id,
            auto_approve=self.auto_approve,
            confidence_threshold=self.confidence_threshold
        )

        # Get YARNNN tools for Claude
        self.yarnnn_tools = get_yarnnn_tools(self.yarnnn, self.basket_id)

        # Logger
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info(f"Initialized {self.__class__.__name__} for basket {basket_id}")

    async def reason(
        self,
        task: str,
        context: Optional[str] = None,
        system_prompt: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        max_tokens: int = 4096
    ) -> Any:
        """
        Use Claude to reason about a task

        Args:
            task: Task description or user intent
            context: Additional context from memory
            system_prompt: Custom system prompt
            tools: Tools to provide to Claude (default: YARNNN tools)
            max_tokens: Maximum response tokens

        Returns:
            Claude's response
        """
        # Build messages
        messages = []

        if context:
            messages.append({
                "role": "user",
                "content": f"**Relevant Context from Memory:**\n\n{context}"
            })

        messages.append({
            "role": "user",
            "content": task
        })

        # Use provided tools or default to YARNNN tools
        tools_to_use = tools if tools is not None else self.yarnnn_tools

        # Call Claude
        self.logger.info(f"Reasoning about task: {task[:100]}...")

        response = await self.claude.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system_prompt or self._get_default_system_prompt(),
            messages=messages,
            tools=[
                {
                    "name": tool["name"],
                    "description": tool["description"],
                    "input_schema": tool["input_schema"]
                }
                for tool in tools_to_use
            ] if tools_to_use else None
        )

        # Handle tool use
        if response.stop_reason == "tool_use":
            return await self._handle_tool_use(response, tools_to_use)

        return response

    async def _handle_tool_use(
        self,
        response: Any,
        tools: List[Dict[str, Any]]
    ) -> Any:
        """
        Handle Claude's tool use requests

        Args:
            response: Claude's response with tool use
            tools: Available tools with function references

        Returns:
            Tool execution results
        """
        tool_results = []

        for content_block in response.content:
            if content_block.type == "tool_use":
                tool_name = content_block.name
                tool_input = content_block.input

                self.logger.info(f"Executing tool: {tool_name}")

                # Find tool function
                tool_func = None
                for tool in tools:
                    if tool["name"] == tool_name:
                        tool_func = tool["function"]
                        break

                if tool_func:
                    try:
                        result = await tool_func(**tool_input)
                        tool_results.append({
                            "tool_use_id": content_block.id,
                            "content": str(result)
                        })
                    except Exception as e:
                        self.logger.error(f"Tool execution error: {e}")
                        tool_results.append({
                            "tool_use_id": content_block.id,
                            "content": f"Error: {str(e)}",
                            "is_error": True
                        })

        return tool_results

    def _get_default_system_prompt(self) -> str:
        """
        Get default system prompt for the agent

        Override this in subclasses for agent-specific behavior
        """
        return f"""You are an autonomous agent with access to YARNNN substrate for long-term memory.

Your capabilities:
- Query YARNNN substrate for relevant context using query_memory()
- Propose changes to substrate using propose_to_memory()
- Check proposal status using check_proposal_status()
- Get anchor-specific context using get_anchor_context()

Important guidelines:
1. Always query memory before working on tasks to get relevant context
2. Propose changes to memory when you learn new information
3. Be confident but not overconfident in your proposals (use appropriate confidence scores)
4. Provide clear reasoning for proposed changes
5. Remember that proposals require human approval - don't assume they'll be accepted

You are operating on basket: {self.basket_id}

Your goal is to be helpful, accurate, and to build high-quality knowledge in the substrate over time."""

    async def execute(self, task: str) -> Any:
        """
        Execute a task (override in subclasses)

        Args:
            task: Task description

        Returns:
            Task result

        Raises:
            NotImplementedError: Must be implemented by subclass
        """
        raise NotImplementedError("Subclasses must implement execute()")

    async def autonomous_loop(
        self,
        tasks: List[str],
        delay_between_tasks: int = 0
    ) -> List[Any]:
        """
        Execute multiple tasks autonomously

        Args:
            tasks: List of tasks to execute
            delay_between_tasks: Delay in seconds between tasks

        Returns:
            List of task results
        """
        import asyncio

        results = []

        for i, task in enumerate(tasks):
            self.logger.info(f"Executing task {i+1}/{len(tasks)}: {task[:50]}...")

            try:
                result = await self.execute(task)
                results.append(result)
                self.logger.info(f"Task {i+1} completed successfully")

            except Exception as e:
                self.logger.error(f"Task {i+1} failed: {e}")
                results.append({"error": str(e)})

            if delay_between_tasks > 0 and i < len(tasks) - 1:
                await asyncio.sleep(delay_between_tasks)

        return results

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(basket_id='{self.basket_id}', model='{self.model}')"
