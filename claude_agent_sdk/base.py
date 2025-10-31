"""
BaseAgent - Generic foundation for all autonomous agents

This class provides the core infrastructure for building agents with:
- Claude SDK integration for reasoning
- Pluggable memory providers (YARNNN, Notion, etc.)
- Pluggable governance providers
- Agent identity and session tracking
"""

import os
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from anthropic import AsyncAnthropic

from .interfaces import MemoryProvider, GovernanceProvider, TaskProvider
from .session import AgentSession, generate_agent_id


# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class BaseAgent(ABC):
    """
    Generic base class for all autonomous agents.

    This is provider-agnostic - works with any MemoryProvider implementation
    (YARNNN, Notion, GitHub, vector stores, etc.).

    Usage:
        from claude_agent_sdk import BaseAgent
        from claude_agent_sdk.integrations.yarnnn import YarnnnMemory, YarnnnGovernance

        class MyAgent(BaseAgent):
            async def execute(
                self,
                task: str,
                task_id: Optional[str] = None,
                task_metadata: Optional[Dict[str, Any]] = None,
                **kwargs
            ) -> str:
                # Start session with optional task linking
                if not self.current_session:
                    self.current_session = self._start_session(task_id, task_metadata)

                # 1. Query memory for context
                if self.memory:
                    contexts = await self.memory.query(task)
                    context_str = "\\n".join([c.content for c in contexts])
                else:
                    context_str = ""

                # 2. Reason with Claude
                response = await self.reason(task, context_str)

                # 3. Propose changes if needed (if governance enabled)
                # ... agent logic

                return response

        agent = MyAgent(
            agent_id="my_research_bot",
            memory=YarnnnMemory(...),
            governance=YarnnnGovernance(...),
            anthropic_api_key="sk-ant-..."
        )

        # Execute with optional task linking
        result = await agent.execute(
            "Research AI governance",
            task_id="work_session_123",
            task_metadata={"workspace_id": "ws_001", "basket_id": "basket_abc"}
        )
    """

    def __init__(
        self,
        # Agent identity
        agent_id: Optional[str] = None,
        agent_type: str = "generic",
        agent_name: Optional[str] = None,

        # Pluggable providers (all optional)
        memory: Optional[MemoryProvider] = None,
        governance: Optional[GovernanceProvider] = None,
        tasks: Optional[TaskProvider] = None,

        # Claude configuration
        anthropic_api_key: Optional[str] = None,
        model: str = "claude-sonnet-4-5",

        # Session resumption (optional)
        session_id: Optional[str] = None,
        claude_session_id: Optional[str] = None,

        # Agent behavior
        auto_approve: bool = False,
        confidence_threshold: float = 0.8,
        max_retries: int = 3,

        # Additional metadata
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize generic agent.

        Args:
            agent_id: Persistent agent identifier (auto-generated if None)
            agent_type: Agent category (knowledge, content, code, etc.)
            agent_name: Human-readable name for the agent
            memory: Memory provider implementation (optional)
            governance: Governance provider implementation (optional)
            tasks: Task provider implementation (optional)
            anthropic_api_key: Anthropic API key (or from ANTHROPIC_API_KEY env)
            model: Claude model to use
            session_id: Existing session ID to resume (optional)
            claude_session_id: Claude conversation session to resume (optional)
            auto_approve: Auto-approve high-confidence proposals
            confidence_threshold: Threshold for auto-approval
            max_retries: Maximum retries for failed operations
            metadata: Additional agent metadata
        """
        # Agent identity
        self.agent_id = agent_id or generate_agent_id(agent_type)
        self.agent_type = agent_type
        self.agent_name = agent_name or self.agent_id

        # Pluggable providers
        self.memory = memory
        self.governance = governance
        self.tasks = tasks

        # Claude configuration
        self.model = model
        api_key = anthropic_api_key or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY must be provided or set in environment")
        self.claude = AsyncAnthropic(api_key=api_key)

        # Agent behavior
        self.auto_approve = auto_approve or os.getenv("AGENT_AUTO_APPROVE", "false").lower() == "true"
        self.confidence_threshold = float(os.getenv("AGENT_CONFIDENCE_THRESHOLD", str(confidence_threshold)))
        self.max_retries = int(os.getenv("AGENT_MAX_RETRIES", str(max_retries)))

        # Session management
        if session_id:
            # Resume existing session
            self.current_session = AgentSession(
                id=session_id,
                agent_id=self.agent_id,
                claude_session_id=claude_session_id
            )
        else:
            # Create new session (will be initialized on first execute)
            self.current_session = None

        self._claude_session_id = claude_session_id  # For resumption

        # Metadata
        self.metadata = metadata or {}

        # Logger
        self.logger = logging.getLogger(f"{self.__class__.__name__}[{self.agent_id}]")
        self.logger.info(f"Initialized {self.agent_name} (type: {self.agent_type})")

    def _start_session(
        self,
        task_id: Optional[str] = None,
        task_metadata: Optional[Dict[str, Any]] = None
    ) -> AgentSession:
        """
        Start a new agent session.

        Args:
            task_id: Optional external task ID (e.g., YARNNN work_session_id)
            task_metadata: Optional task-specific metadata (e.g., workspace_id, basket_id)

        Returns:
            New AgentSession instance
        """
        session = AgentSession(
            agent_id=self.agent_id,
            claude_session_id=self._claude_session_id,
            task_id=task_id,
            task_metadata=task_metadata or {},
            metadata={
                "agent_type": self.agent_type,
                "agent_name": self.agent_name,
                "model": self.model,
                **self.metadata
            }
        )
        self.logger.info(
            f"Started new session: {session.id}"
            + (f" (linked to task: {task_id})" if task_id else "")
        )
        return session

    async def reason(
        self,
        task: str,
        context: Optional[str] = None,
        system_prompt: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        max_tokens: int = 4096,
        resume_session: bool = False
    ) -> Any:
        """
        Use Claude to reason about a task.

        Args:
            task: Task description
            context: Additional context (e.g., from memory)
            system_prompt: Custom system prompt
            tools: Tools to provide to Claude
            max_tokens: Maximum response tokens
            resume_session: Whether to resume previous Claude session

        Returns:
            Claude's response
        """
        # Build messages
        messages = []

        if context:
            messages.append({
                "role": "user",
                "content": f"**Relevant Context:**\n\n{context}"
            })

        messages.append({
            "role": "user",
            "content": task
        })

        # Build request parameters
        request_params = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": messages
        }

        if system_prompt or self._get_default_system_prompt():
            request_params["system"] = system_prompt or self._get_default_system_prompt()

        if tools:
            request_params["tools"] = [
                {
                    "name": tool["name"],
                    "description": tool["description"],
                    "input_schema": tool["input_schema"]
                }
                for tool in tools
            ]

        # Add session resumption if requested
        if resume_session and self._claude_session_id:
            request_params["resume"] = self._claude_session_id

        # Call Claude
        self.logger.info(f"Reasoning: {task[:100]}...")

        try:
            response = await self.claude.messages.create(**request_params)

            # Extract and store Claude session ID if this is first message
            # Note: Actual implementation depends on Claude SDK's session management
            # This is a placeholder for session ID extraction
            if not self._claude_session_id and hasattr(response, 'session_id'):
                self._claude_session_id = response.session_id
                if self.current_session:
                    self.current_session.claude_session_id = response.session_id
                    self.logger.info(f"Claude session started: {response.session_id}")

            return response

        except Exception as e:
            self.logger.error(f"Reasoning error: {e}")
            if self.current_session:
                self.current_session.add_error(e, context="reasoning")
            raise

    def _get_default_system_prompt(self) -> Optional[str]:
        """
        Get default system prompt for the agent.

        Override this in subclasses for agent-specific behavior.

        Returns:
            System prompt string or None
        """
        # Generic prompt - subclasses should override
        return f"""You are an autonomous agent (ID: {self.agent_id}, Type: {self.agent_type}).

Your capabilities depend on the providers configured:
- Memory: {"Available" if self.memory else "Not configured"}
- Governance: {"Available" if self.governance else "Not configured"}
- Tasks: {"Available" if self.tasks else "Not configured"}

Be helpful, accurate, and thoughtful in your responses."""

    @abstractmethod
    async def execute(
        self,
        task: str,
        task_id: Optional[str] = None,
        task_metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Any:
        """
        Execute a task (must be implemented by subclasses).

        Args:
            task: Task description
            task_id: Optional external task ID for linking to work management systems
            task_metadata: Optional task-specific metadata (workspace_id, basket_id, etc.)
            **kwargs: Additional task-specific parameters

        Returns:
            Task result

        Note:
            When implementing this method in subclasses, use _start_session(task_id, task_metadata)
            to properly link the AgentSession to external task systems.

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
        Execute multiple tasks autonomously.

        Args:
            tasks: List of tasks to execute
            delay_between_tasks: Delay in seconds between tasks

        Returns:
            List of task results
        """
        import asyncio

        results = []

        # Start session for the loop
        if not self.current_session:
            self.current_session = self._start_session()

        for i, task in enumerate(tasks):
            self.logger.info(f"Task {i+1}/{len(tasks)}: {task[:50]}...")

            try:
                result = await self.execute(task)
                results.append(result)
                self.current_session.tasks_completed += 1
                self.logger.info(f"Task {i+1} completed")

            except Exception as e:
                self.logger.error(f"Task {i+1} failed: {e}")
                self.current_session.add_error(e, context=f"task_{i+1}")
                results.append({"error": str(e)})

            if delay_between_tasks > 0 and i < len(tasks) - 1:
                await asyncio.sleep(delay_between_tasks)

        # Complete session
        self.current_session.complete()
        self.logger.info(f"Session completed: {self.current_session.to_dict()}")

        return results

    async def run_continuous(
        self,
        check_interval: int = 60,
        max_iterations: Optional[int] = None
    ):
        """
        Run agent continuously, polling task provider for work.

        Args:
            check_interval: Seconds between task checks
            max_iterations: Maximum iterations (None for infinite)

        Raises:
            ValueError: If no task provider configured
        """
        import asyncio

        if not self.tasks:
            raise ValueError("Task provider required for continuous operation")

        self.logger.info(f"Starting continuous operation (check every {check_interval}s)")

        iteration = 0
        while max_iterations is None or iteration < max_iterations:
            try:
                # Get pending tasks
                pending = await self.tasks.get_pending_tasks(self.agent_id)

                if pending:
                    self.logger.info(f"Found {len(pending)} pending tasks")

                    for task in pending:
                        # Update task status
                        await self.tasks.update_task_status(task.id, "in_progress")

                        # Execute task
                        try:
                            result = await self.execute(task.description)
                            await self.tasks.update_task_status(
                                task.id,
                                "completed",
                                result=result
                            )
                        except Exception as e:
                            self.logger.error(f"Task {task.id} failed: {e}")
                            await self.tasks.update_task_status(
                                task.id,
                                "failed",
                                error=str(e)
                            )
                else:
                    self.logger.debug("No pending tasks")

            except Exception as e:
                self.logger.error(f"Error in continuous loop: {e}")

            # Wait before next check
            await asyncio.sleep(check_interval)
            iteration += 1

        self.logger.info("Continuous operation stopped")

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"agent_id='{self.agent_id}', "
            f"type='{self.agent_type}', "
            f"model='{self.model}')"
        )
