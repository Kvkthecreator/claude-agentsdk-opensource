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
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from anthropic import AsyncAnthropic

from .interfaces import (
    MemoryProvider,
    GovernanceProvider,
    TaskProvider,
    # Lifecycle hooks
    StepStartHook,
    StepEndHook,
    ExecuteStartHook,
    ExecuteEndHook,
    InterruptHook,
    ErrorHook,
    CheckpointHook,
    StepContext,
    StepResult,
    AgentState,
    InterruptDecision,
)
from .session import AgentSession, generate_agent_id
from .subagents import SubagentRegistry, SubagentDefinition, create_subagent_tool


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

        # Lifecycle hooks (all optional)
        on_step_start: Optional[StepStartHook] = None,
        on_step_end: Optional[StepEndHook] = None,
        before_execute: Optional[ExecuteStartHook] = None,
        after_execute: Optional[ExecuteEndHook] = None,
        on_interrupt_signal: Optional[InterruptHook] = None,
        on_error: Optional[ErrorHook] = None,
        on_checkpoint_opportunity: Optional[CheckpointHook] = None,

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
            on_step_start: Hook called before each step execution (optional)
            on_step_end: Hook called after each step execution (optional)
            before_execute: Hook called before agent.execute() (optional)
            after_execute: Hook called after agent.execute() (optional)
            on_interrupt_signal: Hook called when interrupt is signaled (optional)
            on_error: Hook called when error occurs (optional)
            on_checkpoint_opportunity: Hook called at checkpoint opportunities (optional)
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

        # Lifecycle hooks
        self.hooks = {
            "step_start": on_step_start,
            "step_end": on_step_end,
            "execute_start": before_execute,
            "execute_end": after_execute,
            "interrupt": on_interrupt_signal,
            "error": on_error,
            "checkpoint": on_checkpoint_opportunity,
        }

        # Subagent registry
        self.subagents = SubagentRegistry(self)

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
        prompt = f"""You are an autonomous agent (ID: {self.agent_id}, Type: {self.agent_type}).

Your capabilities depend on the providers configured:
- Memory: {"Available" if self.memory is not None else "Not configured"}
- Governance: {"Available" if self.governance is not None else "Not configured"}
- Tasks: {"Available" if self.tasks is not None else "Not configured"}"""

        # Add subagent information if any subagents are registered
        if self.subagents.list_subagents():
            prompt += "\n" + self.subagents.get_delegation_prompt()

        prompt += "\n\nBe helpful, accurate, and thoughtful in your responses."

        return prompt

    async def _execute_subagent(
        self,
        subagent: SubagentDefinition,
        task: str,
        context: Optional[str] = None,
        **kwargs
    ) -> Any:
        """
        Execute a subagent task.

        Args:
            subagent: Subagent definition
            task: Task for subagent
            context: Additional context
            **kwargs: Additional arguments

        Returns:
            Subagent's response
        """
        # Use subagent's system prompt
        system_prompt = subagent.system_prompt

        # Use subagent's model if specified, otherwise use parent's
        model = subagent.model or self.model

        # Filter tools if subagent has restrictions
        tools = kwargs.get("tools")
        if subagent.tools and tools:
            # Only provide tools that subagent is allowed to use
            tools = [t for t in tools if t["name"] in subagent.tools]

        # Call reason with subagent configuration
        return await self.reason(
            task=task,
            context=context,
            system_prompt=system_prompt,
            tools=tools,
            max_tokens=kwargs.get("max_tokens", 4096)
        )

    def _get_state(self) -> AgentState:
        """
        Build current agent state for hooks.

        Returns:
            AgentState with current state information
        """
        return AgentState(
            agent_id=self.agent_id,
            session_id=self.current_session.id if self.current_session else None,
            current_step=getattr(self, '_current_step', None),
            metadata=self.metadata
        )

    async def execute_step(
        self,
        step_name: str,
        step_fn: Any,
        inputs: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Execute a logical step with lifecycle hooks.

        This is a helper for agent implementations to define steps with
        automatic hook invocation.

        Args:
            step_name: Name of the step (e.g., "plan", "web_monitor", "analyze")
            step_fn: Async function to execute (can be lambda or method)
            inputs: Optional inputs to pass to the step

        Returns:
            Step execution result

        Example:
            await self.execute_step("plan", self._create_plan)
            await self.execute_step("monitor", lambda ctx: self.subagents.execute("web_monitor", task))

        Raises:
            Exception: If step execution fails (after calling on_error hook)
        """
        # Track current step
        self._current_step = step_name

        # Build context
        context = StepContext(
            step_name=step_name,
            inputs=inputs or {},
            metadata={}
        )

        # Hook: on_step_start
        if self.hooks["step_start"]:
            try:
                await self.hooks["step_start"](self._get_state(), context)
            except Exception as e:
                self.logger.error(f"on_step_start hook failed: {e}")
                raise

        # Execute step
        start_time = time.time()
        result = None
        success = False
        error_msg = None
        error_type = None

        try:
            result = await step_fn(context) if callable(step_fn) else step_fn
            success = True
        except Exception as e:
            error_msg = str(e)
            error_type = type(e).__name__
            self.logger.error(f"Step '{step_name}' failed: {e}")

            # Hook: on_error
            if self.hooks["error"]:
                try:
                    await self.hooks["error"](self._get_state(), e, step_name)
                except Exception as hook_error:
                    self.logger.error(f"on_error hook failed: {hook_error}")

            raise
        finally:
            duration = time.time() - start_time

            # Hook: on_step_end
            if self.hooks["step_end"]:
                step_result = StepResult(
                    step_name=step_name,
                    output=result,
                    success=success,
                    error=error_msg,
                    error_type=error_type,
                    duration=duration,
                    metadata={}
                )
                try:
                    await self.hooks["step_end"](self._get_state(), step_result)
                except Exception as e:
                    self.logger.error(f"on_step_end hook failed: {e}")
                    # Don't raise here - step completed successfully

            # Clear current step
            self._current_step = None

        return result

    async def send_interrupt(
        self,
        reason: str,
        data: Optional[Dict[str, Any]] = None
    ) -> InterruptDecision:
        """
        Signal an interrupt to the agent.

        This is called externally (e.g., from API endpoint) to interrupt
        agent execution. The hook decides how to handle the interrupt.

        Args:
            reason: Reason for interrupt (e.g., "user_interrupt", "error", "timeout")
            data: Optional additional data about the interrupt

        Returns:
            InterruptDecision (PAUSE, CONTINUE, or ABORT)

        Example:
            # From YARNNN API endpoint:
            decision = await agent.send_interrupt(
                reason="user_interrupt",
                data={"message": "Please review progress"}
            )
        """
        if self.hooks["interrupt"]:
            try:
                decision = await self.hooks["interrupt"](
                    self._get_state(),
                    reason,
                    data or {}
                )
                self.logger.info(f"Interrupt '{reason}' → {decision}")
                return decision
            except Exception as e:
                self.logger.error(f"on_interrupt_signal hook failed: {e}")
                raise
        else:
            # No hook - default to continue
            self.logger.warning(f"Interrupt '{reason}' received but no handler configured")
            return InterruptDecision.CONTINUE

    async def offer_checkpoint(
        self,
        checkpoint_name: str,
        data: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Signal a checkpoint opportunity to the hook.

        This is called by agent implementations when they reach a point
        where human review might be valuable. The hook decides whether
        to pause execution.

        Args:
            checkpoint_name: Name of checkpoint (e.g., "plan_ready", "findings_ready")
            data: Optional data for review (plan, findings, etc.)

        Example:
            await self.offer_checkpoint("plan_ready", {"plan": monitoring_plan})
            # Hook may pause execution here for review

        Raises:
            Exception: If checkpoint is rejected or times out
        """
        if self.hooks["checkpoint"]:
            try:
                await self.hooks["checkpoint"](
                    self._get_state(),
                    checkpoint_name,
                    data or {}
                )
                self.logger.info(f"Checkpoint '{checkpoint_name}' offered")
            except Exception as e:
                self.logger.error(f"Checkpoint '{checkpoint_name}' failed: {e}")
                raise
        else:
            # No hook - just log
            self.logger.debug(f"Checkpoint '{checkpoint_name}' (no handler)")

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

            To use lifecycle hooks, structure execution with execute_step():
                await self.execute_step("plan", self._create_plan)
                await self.execute_step("execute", self._do_work)

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
