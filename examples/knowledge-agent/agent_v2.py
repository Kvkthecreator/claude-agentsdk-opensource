"""
Knowledge Agent - Autonomous research and knowledge accumulation

REFACTORED VERSION using the new generic Claude Agent SDK.

This agent demonstrates how to build a specialized agent using:
- Generic BaseAgent foundation
- YARNNN integration for memory and governance
- Agent identity and session tracking
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from claude_agent_sdk import BaseAgent
from claude_agent_sdk.integrations.yarnnn import YarnnnMemory, YarnnnGovernance, get_yarnnn_tools, Block, ContextItem
from claude_agent_sdk.interfaces import Change


logger = logging.getLogger(__name__)


class KnowledgeAgent(BaseAgent):
    """
    Knowledge Agent - Specialized for research and knowledge accumulation.

    This agent:
    - Queries existing knowledge from memory
    - Identifies knowledge gaps
    - Synthesizes new insights
    - Proposes governed additions
    - Builds connected knowledge graphs

    Usage:
        from claude_agent_sdk.integrations.yarnnn import YarnnnMemory, YarnnnGovernance

        memory = YarnnnMemory(basket_id="basket_123")
        governance = YarnnnGovernance(basket_id="basket_123")

        agent = KnowledgeAgent(
            agent_id="research_bot",
            memory=memory,
            governance=governance,
            anthropic_api_key="sk-ant-..."
        )

        result = await agent.execute("Research AI governance frameworks")
    """

    def __init__(
        self,
        # Agent identity (optional - auto-generated if not provided)
        agent_id: Optional[str] = None,
        agent_name: Optional[str] = None,

        # Required: Memory and governance providers
        memory: YarnnnMemory,
        governance: YarnnnGovernance,

        # Claude configuration
        anthropic_api_key: str,
        model: str = "claude-sonnet-4-5",

        # Session resumption (optional)
        session_id: Optional[str] = None,
        claude_session_id: Optional[str] = None,

        # Agent behavior
        auto_approve: bool = False,
        confidence_threshold: float = 0.8,

        # Custom prompt (optional)
        system_prompt: Optional[str] = None
    ):
        """
        Initialize Knowledge Agent.

        Args:
            agent_id: Persistent agent identifier (auto-generated if None)
            agent_name: Human-readable name
            memory: YARNNN memory provider
            governance: YARNNN governance provider
            anthropic_api_key: Anthropic API key
            model: Claude model to use
            session_id: Existing session to resume
            claude_session_id: Claude conversation to resume
            auto_approve: Auto-approve high-confidence proposals
            confidence_threshold: Threshold for auto-approval
            system_prompt: Custom system prompt
        """
        super().__init__(
            agent_id=agent_id,
            agent_type="knowledge",
            agent_name=agent_name,
            memory=memory,
            governance=governance,
            anthropic_api_key=anthropic_api_key,
            model=model,
            session_id=session_id,
            claude_session_id=claude_session_id,
            auto_approve=auto_approve,
            confidence_threshold=confidence_threshold
        )

        self.custom_system_prompt = system_prompt
        self.yarnnn_memory = memory  # Type hint for YARNNN-specific methods
        self.yarnnn_governance = governance

        # Get YARNNN tools for Claude
        self.yarnnn_tools = get_yarnnn_tools(
            memory.client,
            memory.basket_id
        )

        self.logger.info(f"Knowledge Agent initialized: {self.agent_name}")

    def _get_default_system_prompt(self) -> Optional[str]:
        """Get Knowledge Agent specific system prompt"""
        if self.custom_system_prompt:
            return self.custom_system_prompt

        return f"""You are an autonomous Knowledge Agent (ID: {self.agent_id}).

Your mission:
- Research topics deeply and accurately
- Build high-quality knowledge in the substrate
- Connect related concepts and ideas
- Identify knowledge gaps and fill them
- Maintain consistency with existing knowledge

Your YARNNN capabilities:
- query_memory(query, limit): Search substrate for relevant knowledge
- propose_to_memory(blocks, context_items, reasoning, confidence): Propose new knowledge
- check_proposal_status(proposal_id): Check if proposals are approved
- get_anchor_context(anchor): Get all knowledge under a category

Research methodology:
1. **Query First**: Always check existing knowledge before researching
2. **Identify Gaps**: Note what's missing or outdated
3. **Synthesize**: Create clear, well-structured insights
4. **Confidence**: Be honest about confidence levels
   - 0.9-1.0: Facts from authoritative sources
   - 0.7-0.9: Well-researched insights
   - 0.5-0.7: Preliminary findings
5. **Propose**: Submit changes through governance
6. **Connect**: Link related concepts and build knowledge graphs

Quality guidelines:
- Write clear, concise titles
- Provide substantive content in bodies
- Use appropriate semantic types (knowledge, meaning, structural)
- Tag with relevant concepts
- Cite sources when possible (in body)
- Build on existing knowledge, don't duplicate

Remember: All changes require human approval. Provide clear reasoning to help humans evaluate your proposals.
"""

    async def execute(
        self,
        task: str,
        wait_for_approval: bool = False,
        resume_session: bool = False
    ) -> Dict[str, Any]:
        """
        Execute a research task.

        Args:
            task: Research task description
            wait_for_approval: Whether to wait for proposal approval
            resume_session: Whether to resume previous Claude session

        Returns:
            Dictionary with:
            - response: Claude's response
            - proposals: List of proposal IDs created
            - session_id: Current session ID
        """
        # Start session if not already active
        if not self.current_session:
            self.current_session = self._start_session()

        self.logger.info(f"Executing task: {task[:100]}...")

        try:
            # Step 1: Query existing knowledge
            self.logger.info("Querying existing knowledge...")
            contexts = await self.memory.query(task, limit=20)
            context_str = "\n\n".join([c.content for c in contexts]) if contexts else "No existing knowledge found."

            # Step 2: Reason with Claude using YARNNN tools
            self.logger.info("Reasoning with Claude...")
            response = await self.reason(
                task=task,
                context=context_str,
                tools=self.yarnnn_tools,
                resume_session=resume_session
            )

            # Track proposals created (if any)
            # Note: This would require parsing tool use responses
            # For now, we return the response

            result = {
                "response": response,
                "session_id": self.current_session.id,
                "claude_session_id": self._claude_session_id,
                "proposals": self.current_session.proposals_created
            }

            # Mark task as completed
            self.current_session.tasks_completed += 1

            return result

        except Exception as e:
            self.logger.error(f"Task execution failed: {e}")
            self.current_session.add_error(e, context="execute")
            raise

    async def research_and_wait(
        self,
        task: str,
        max_wait: int = 3600
    ) -> Dict[str, Any]:
        """
        Execute research task and wait for all proposals to be approved.

        Args:
            task: Research task
            max_wait: Maximum wait time for approvals

        Returns:
            Task result with approval statuses
        """
        # Execute task
        result = await self.execute(task)

        # Wait for approvals
        if result["proposals"] and self.governance:
            self.logger.info(f"Waiting for approval of {len(result['proposals'])} proposals...")

            approved_count = 0
            for proposal_id in result["proposals"]:
                try:
                    approved = await self.governance.wait_for_approval(
                        proposal_id,
                        timeout=max_wait
                    )
                    if approved:
                        approved_count += 1
                except TimeoutError:
                    self.logger.warning(f"Approval timeout for proposal {proposal_id}")

            result["approvals"] = {
                "total": len(result["proposals"]),
                "approved": approved_count
            }

        return result

    # Convenience methods for knowledge operations

    async def add_insight(
        self,
        title: str,
        body: str,
        confidence: float = 0.8,
        tags: Optional[List[str]] = None,
        wait: bool = False
    ) -> str:
        """
        Directly add an insight to knowledge base.

        Args:
            title: Insight title
            body: Insight content
            confidence: Confidence score
            tags: Optional tags
            wait: Whether to wait for approval

        Returns:
            Proposal ID
        """
        if not self.governance:
            raise ValueError("Governance provider required for adding insights")

        proposal = await self.yarnnn_governance.propose_insight(
            title=title,
            body=body,
            confidence=confidence,
            tags=tags,
            reasoning=f"Manual insight addition via {self.agent_id}",
            metadata={
                "agent_session_id": self.current_session.id if self.current_session else None
            }
        )

        # Track in session
        if self.current_session:
            self.current_session.add_proposal(proposal.id)

        # Wait for approval if requested
        if wait:
            approved = await self.governance.wait_for_approval(proposal.id)
            self.logger.info(f"Insight proposal {proposal.id}: {'approved' if approved else 'rejected'}")

        return proposal.id

    async def summarize_knowledge(self) -> Dict[str, Any]:
        """
        Get summary of current knowledge in substrate.

        Returns:
            Summary statistics
        """
        if not self.memory:
            return {"error": "No memory provider configured"}

        return await self.memory.summarize()
