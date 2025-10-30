"""
Knowledge Agent - Autonomous research and knowledge accumulation

This agent demonstrates the core YARNNN + Claude integration pattern:
1. Query substrate for existing knowledge
2. Reason about what's missing or needs updating
3. Research new information (simulated for now)
4. Synthesize insights
5. Propose additions via governance
6. Wait for approval and continue
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from yarnnn_agents import BaseAgent


logger = logging.getLogger(__name__)


class KnowledgeAgent(BaseAgent):
    """
    Knowledge Agent - Autonomous research and knowledge accumulation

    This agent specializes in:
    - Querying existing knowledge substrate
    - Identifying knowledge gaps
    - Researching new information
    - Synthesizing insights
    - Proposing governed additions to substrate
    - Building connected knowledge graphs

    Usage:
        agent = KnowledgeAgent(basket_id="basket_123")

        result = await agent.execute(
            "Research AI governance frameworks and add to memory"
        )

        # Agent will query memory, synthesize insights, and propose changes
    """

    def __init__(
        self,
        basket_id: str,
        anthropic_api_key: Optional[str] = None,
        yarnnn_client: Optional[Any] = None,
        model: str = "claude-3-5-sonnet-20241022",
        auto_approve: bool = False,
        confidence_threshold: float = 0.8,
        max_retries: int = 3,
        system_prompt: Optional[str] = None
    ):
        """
        Initialize Knowledge Agent

        Args:
            basket_id: YARNNN basket to operate on
            anthropic_api_key: Anthropic API key (default: from env)
            yarnnn_client: YARNNN client instance (default: auto-created)
            model: Claude model to use
            auto_approve: Auto-approve high-confidence proposals
            confidence_threshold: Threshold for auto-approval
            max_retries: Maximum retries for failed operations
            system_prompt: Custom system prompt (default: knowledge agent prompt)
        """
        super().__init__(
            basket_id=basket_id,
            anthropic_api_key=anthropic_api_key,
            yarnnn_client=yarnnn_client,
            model=model,
            auto_approve=auto_approve,
            confidence_threshold=confidence_threshold,
            max_retries=max_retries
        )

        self.custom_system_prompt = system_prompt
        self.logger = logging.getLogger(self.__class__.__name__)

    def _get_default_system_prompt(self) -> str:
        """Get Knowledge Agent specific system prompt"""
        if self.custom_system_prompt:
            return self.custom_system_prompt

        return f"""You are an autonomous Knowledge Agent with access to YARNNN substrate for long-term memory.

Your mission:
- Research topics deeply and accurately
- Build high-quality knowledge in the substrate
- Connect related concepts and ideas
- Identify knowledge gaps and fill them
- Maintain consistency with existing knowledge

Your capabilities:
- query_memory(query, limit): Search substrate for relevant knowledge
- propose_to_memory(blocks, context_items, reasoning, confidence): Propose new knowledge
- check_proposal_status(proposal_id): Check if proposals are approved
- get_anchor_context(anchor): Get all knowledge under a category

Important guidelines:

1. **Always query memory first** - Check what we already know before researching
2. **Build on existing knowledge** - Connect new insights to existing substrate
3. **Be confident but not overconfident** - Use appropriate confidence scores:
   - 0.9-1.0: Facts, established knowledge, high-quality sources
   - 0.7-0.9: Well-researched insights, reasonable confidence
   - 0.5-0.7: Preliminary findings, needs validation
   - <0.5: Speculative, uncertain

4. **Provide clear reasoning** - Explain why you're proposing changes
5. **Remember governance** - Proposals require human approval, so make them count
6. **Tag appropriately** - Use relevant tags to organize knowledge
7. **Identify concepts** - Extract key entities, people, orgs, concepts

Your current basket: {self.basket_id}

Approach each task methodically:
1. Query memory for existing knowledge
2. Identify what's missing or outdated
3. Synthesize new insights (from research)
4. Propose additions with clear reasoning
5. Confirm proposal submission"""

    async def execute(self, task: str) -> Dict[str, Any]:
        """
        Execute a knowledge accumulation task

        Args:
            task: Task description (e.g., "Research AI governance frameworks")

        Returns:
            Result with proposal IDs and status
        """
        self.logger.info(f"Executing task: {task}")

        try:
            # Step 1: Query existing knowledge
            self.logger.info("Querying existing knowledge...")
            context = await self.memory.query(task, limit=20)

            # Step 2: Use Claude to reason about task with context
            self.logger.info("Reasoning with Claude...")

            messages = [
                {
                    "role": "user",
                    "content": f"""**Task:** {task}

**Existing Knowledge from Substrate:**
{context}

**Instructions:**
1. Review the existing knowledge above
2. Identify what new insights or information would be valuable
3. Synthesize new insights based on the task (simulate research for now)
4. Use the propose_to_memory tool to add your insights to the substrate
5. Provide a summary of what you proposed

Remember:
- Build on existing knowledge
- Use appropriate confidence scores
- Provide clear reasoning
- Extract key concepts
- Tag your insights appropriately"""
                }
            ]

            response = await self.claude.messages.create(
                model=self.model,
                max_tokens=4096,
                system=self._get_default_system_prompt(),
                messages=messages,
                tools=[
                    {
                        "name": tool["name"],
                        "description": tool["description"],
                        "input_schema": tool["input_schema"]
                    }
                    for tool in self.yarnnn_tools
                ]
            )

            # Step 3: Handle tool use (proposal creation)
            proposals = []
            final_response = None

            if response.stop_reason == "tool_use":
                self.logger.info("Agent is using tools...")
                tool_results = await self._handle_tool_use(response, self.yarnnn_tools)

                # Continue conversation with tool results
                messages.append({"role": "assistant", "content": response.content})
                messages.append({
                    "role": "user",
                    "content": tool_results
                })

                # Get final response
                final_response = await self.claude.messages.create(
                    model=self.model,
                    max_tokens=2048,
                    system=self._get_default_system_prompt(),
                    messages=messages
                )

                # Extract proposal IDs from tool results
                for result in tool_results:
                    if "Proposal created:" in result.get("content", ""):
                        # Parse proposal ID (format: "Proposal created: prop-xxx")
                        content = result["content"]
                        if "Proposal created:" in content:
                            proposal_id = content.split("Proposal created:")[1].split("\n")[0].strip()
                            proposals.append(proposal_id)

            # Step 4: Return result
            result = {
                "task": task,
                "proposals": proposals,
                "status": "proposals_submitted" if proposals else "no_proposals",
                "message": self._extract_text_content(final_response or response)
            }

            self.logger.info(f"Task completed: {len(proposals)} proposals submitted")
            return result

        except Exception as e:
            self.logger.error(f"Task execution failed: {e}", exc_info=True)
            return {
                "task": task,
                "status": "failed",
                "error": str(e)
            }

    async def research_and_wait(self, task: str, timeout: int = 3600) -> Dict[str, Any]:
        """
        Execute task and wait for all proposals to be approved

        Args:
            task: Task description
            timeout: Maximum wait time for approval

        Returns:
            Result with approval status
        """
        # Execute task
        result = await self.execute(task)

        if result["status"] != "proposals_submitted":
            return result

        # Wait for approvals
        proposals = result["proposals"]
        approvals = []

        for proposal_id in proposals:
            self.logger.info(f"Waiting for approval: {proposal_id}")
            try:
                approved = await self.governance.wait_for_approval(
                    proposal_id=proposal_id,
                    timeout=timeout,
                    poll_interval=5
                )
                approvals.append({
                    "proposal_id": proposal_id,
                    "approved": approved
                })
            except TimeoutError:
                approvals.append({
                    "proposal_id": proposal_id,
                    "approved": False,
                    "error": "timeout"
                })

        result["approvals"] = approvals
        result["all_approved"] = all(a.get("approved", False) for a in approvals)

        return result

    async def continuous_operation(
        self,
        check_interval: int = 300,
        max_runtime: Optional[int] = None
    ) -> None:
        """
        Run agent continuously, checking for tasks

        Args:
            check_interval: Seconds between task checks
            max_runtime: Maximum runtime in seconds (None = infinite)

        Note:
            This is a placeholder for continuous operation.
            In production, you'd integrate with a task queue or scheduler.
        """
        self.logger.info(f"Starting continuous operation (interval: {check_interval}s)")

        start_time = asyncio.get_event_loop().time()

        while True:
            # Check if max runtime exceeded
            if max_runtime:
                elapsed = asyncio.get_event_loop().time() - start_time
                if elapsed >= max_runtime:
                    self.logger.info(f"Max runtime reached: {max_runtime}s")
                    break

            # TODO: Check for new tasks from queue/scheduler
            # For now, just sleep
            self.logger.info("Waiting for tasks...")
            await asyncio.sleep(check_interval)

    def _extract_text_content(self, response: Any) -> str:
        """Extract text content from Claude response"""
        if not response:
            return ""

        text_parts = []
        for content in response.content:
            if hasattr(content, "text"):
                text_parts.append(content.text)
            elif isinstance(content, dict) and "text" in content:
                text_parts.append(content["text"])

        return "\n".join(text_parts)

    def __repr__(self) -> str:
        return f"KnowledgeAgent(basket_id='{self.basket_id}', model='{self.model}')"
