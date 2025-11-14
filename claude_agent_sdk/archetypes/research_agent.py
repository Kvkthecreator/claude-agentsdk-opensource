"""
Research Agent Archetype

Combines continuous monitoring and deep-dive research capabilities.
Uses subagents for specialized research tasks.

Philosophy:
- Proactive intelligence gathering (scheduled monitoring)
- Reactive deep dives (on-demand research)
- Signal detection (what changed? what's important?)
- Synthesis over raw data
"""

import logging
from typing import Any, Dict, List, Optional, Literal
from datetime import datetime

from ..base import BaseAgent
from ..subagents import SubagentDefinition
from ..interfaces import (
    MemoryProvider,
    GovernanceProvider,
    TaskProvider,
    Change,
    extract_metadata_from_contexts
)


logger = logging.getLogger(__name__)


class ResearchAgent(BaseAgent):
    """
    Research agent with continuous monitoring and deep-dive capabilities.

    Job-to-be-Done:
    "Keep me informed about my market and research topics deeply when asked"

    Core Capabilities:
    - Continuous monitoring (web, competitors, social media)
    - Deep-dive research (comprehensive analysis)
    - Signal detection (identify important changes)
    - Synthesis and insights (not just data aggregation)

    Subagents:
    - web_monitor: Monitors websites and blogs
    - competitor_tracker: Tracks competitor activity
    - social_listener: Monitors social media signals
    - analyst: Synthesizes findings into insights

    Usage:
        from claude_agent_sdk.archetypes import ResearchAgent
        from claude_agent_sdk.integrations.yarnnn import YarnnnMemory, YarnnnGovernance

        agent = ResearchAgent(
            memory=YarnnnMemory(basket_id="market_intelligence"),
            governance=YarnnnGovernance(basket_id="market_intelligence"),
            anthropic_api_key="sk-ant-...",
            monitoring_domains=["competitors", "market_trends"],
            monitoring_frequency="daily"
        )

        # Continuous monitoring (scheduled)
        await agent.monitor()

        # Deep dive research (on-demand)
        result = await agent.deep_dive("AI agent market landscape")
    """

    def __init__(
        self,
        # Required parameters
        memory: MemoryProvider,
        anthropic_api_key: str,

        # Optional providers
        governance: Optional[GovernanceProvider] = None,
        tasks: Optional[TaskProvider] = None,

        # Claude configuration
        model: str = "claude-sonnet-4-5",

        # Agent identity
        agent_id: Optional[str] = None,
        agent_name: Optional[str] = None,

        # Monitoring configuration
        monitoring_domains: Optional[List[str]] = None,
        monitoring_frequency: Literal["hourly", "daily", "weekly"] = "daily",

        # Signal detection
        signal_threshold: float = 0.7,
        synthesis_mode: Literal["summary", "detailed", "insights"] = "insights",

        # Advanced configuration
        session_id: Optional[str] = None,
        auto_approve: bool = False,
    ):
        """
        Initialize Research Agent.

        Args:
            memory: Memory provider for storing research
            governance: Governance provider for approvals
            anthropic_api_key: Anthropic API key
            model: Claude model to use
            agent_id: Agent identifier (auto-generated if None)
            agent_name: Human-readable name
            monitoring_domains: Domains to monitor (e.g., ["competitors", "market_trends"])
            monitoring_frequency: How often to monitor
            signal_threshold: Minimum importance score to alert (0.0-1.0)
            synthesis_mode: How to present findings
            tasks: Task provider (optional)
            session_id: Session to resume (optional)
            auto_approve: Auto-approve proposals (not recommended)
        """
        super().__init__(
            agent_id=agent_id,
            agent_type="research",
            agent_name=agent_name or "Research Agent",
            memory=memory,
            governance=governance,
            tasks=tasks,
            anthropic_api_key=anthropic_api_key,
            model=model,
            session_id=session_id,
            auto_approve=auto_approve,
        )

        # Research configuration
        self.monitoring_domains = monitoring_domains or ["general"]
        self.monitoring_frequency = monitoring_frequency
        self.signal_threshold = signal_threshold
        self.synthesis_mode = synthesis_mode

        # Register subagents
        self._register_subagents()

        self.logger.info(
            f"Research Agent initialized - Domains: {self.monitoring_domains}, "
            f"Frequency: {monitoring_frequency}"
        )

    def _register_subagents(self):
        """Register specialized research subagents."""

        # Web Monitor Subagent
        self.subagents.register(
            SubagentDefinition(
                name="web_monitor",
                description="Monitor websites, blogs, and news sources for updates and changes",
                system_prompt="""You are a web monitoring specialist.

Your job: Scrape websites, detect changes, extract key updates.
Focus on: What's NEW since last check? What CHANGED?

Approach:
1. Fetch current content from specified URLs
2. Compare with previous content (from memory)
3. Identify significant changes
4. Extract key updates and insights
5. Score importance of changes (0.0-1.0)

Return format:
- Changes detected (what, where, when)
- Importance score
- Summary of updates
""",
                tools=["web_search", "web_fetch"],
                metadata={"type": "monitor"}
            )
        )

        # Competitor Tracker Subagent
        self.subagents.register(
            SubagentDefinition(
                name="competitor_tracker",
                description="Track competitor activity - products, pricing, messaging, strategic moves",
                system_prompt="""You are a competitive intelligence analyst.

Your job: Monitor competitor activity across multiple channels.
Focus on: Strategic moves, product changes, market positioning.

What to track:
- Product launches and updates
- Pricing changes
- Marketing messaging shifts
- Job postings (hiring signals)
- Social media activity
- Press releases and announcements

Approach:
1. Check competitor websites and social accounts
2. Identify changes since last check
3. Assess strategic significance
4. Connect to broader market trends

Return format:
- Competitor actions detected
- Strategic implications
- Threat/opportunity assessment
""",
                tools=["web_search", "web_fetch"],
                metadata={"type": "monitor"}
            )
        )

        # Social Listener Subagent
        self.subagents.register(
            SubagentDefinition(
                name="social_listener",
                description="Monitor social media, communities, and forums for signals and sentiment",
                system_prompt="""You are a social listening specialist.

Your job: Track mentions, sentiment, and emerging discussions.
Focus on: Community sentiment, trending topics, viral content.

Channels to monitor:
- Twitter/X
- Reddit
- Hacker News
- LinkedIn
- Industry forums

What to capture:
- Mentions and sentiment
- Trending discussions
- Viral content and memes
- Community reactions
- Emerging narratives

Return format:
- Social signals detected
- Sentiment analysis
- Trending topics
- Notable mentions
""",
                tools=["web_search", "web_fetch"],
                metadata={"type": "monitor"}
            )
        )

        # Analyst Subagent
        self.subagents.register(
            SubagentDefinition(
                name="analyst",
                description="Synthesize research findings into actionable insights",
                system_prompt="""You are a research analyst and synthesizer.

Your job: Transform raw data into actionable insights.
Focus on: Patterns, trends, implications, recommendations.

Analysis approach:
1. Review all monitoring data
2. Identify patterns and trends
3. Assess significance and urgency
4. Connect to broader context
5. Generate actionable insights

Synthesis levels:
- Summary: Brief overview of findings
- Detailed: Comprehensive analysis
- Insights: "So what?" implications and recommendations

Output style:
- Clear, concise, actionable
- Prioritized by importance
- Forward-looking (what does this mean for the future?)
- Recommendation-oriented (what should we do?)
""",
                tools=None,  # No web tools, just analysis
                metadata={"type": "analyst"}
            )
        )

    async def execute(
        self,
        task: str,
        task_id: Optional[str] = None,
        task_metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute a research task.

        Automatically routes to monitor() or deep_dive() based on task.

        Args:
            task: Task description
            task_id: Optional task ID
            task_metadata: Optional task metadata
            **kwargs: Additional arguments

        Returns:
            Research results
        """
        # Start session
        if not self.current_session:
            self.current_session = self._start_session(task_id, task_metadata)

        # Route based on task type
        task_lower = task.lower()

        if any(word in task_lower for word in ["monitor", "track", "watch", "scan"]):
            # Continuous monitoring
            return await self.monitor()
        else:
            # Deep dive research
            return await self.deep_dive(task)

    async def monitor(self) -> Dict[str, Any]:
        """
        Execute continuous monitoring across all configured domains.

        Metadata Enhancement:
        - Uses agent_config for watchlist items, alert rules, confidence thresholds
        - Gracefully degrades if metadata not provided (backward compatible)

        This is typically scheduled to run automatically.

        Returns:
            Monitoring results with detected signals
        """
        self.logger.info(f"Starting monitoring scan - Domains: {self.monitoring_domains}")

        # Get context from memory (may include metadata)
        contexts = []
        if self.memory:
            contexts = await self.memory.query("Monitor configured topics and domains", limit=10)

        # ENHANCEMENT: Extract metadata (generic pattern)
        metadata = extract_metadata_from_contexts(contexts)
        config = metadata.get("agent_config", {}) if metadata else {}

        # Use config-driven monitoring parameters (if available)
        domains = self.monitoring_domains.copy()
        topics = []
        competitors = []
        confidence_threshold = self.signal_threshold
        enhanced_with_metadata = bool(config)

        if config:
            # Extract watchlist if available (implementation-specific, but generic pattern)
            if "watchlist" in config:
                watchlist = config["watchlist"]
                if isinstance(watchlist, dict):
                    topics = watchlist.get("topics", [])
                    competitors = watchlist.get("competitors", [])
                    # Extend monitoring scope with config-driven topics
                    if topics:
                        domains.extend([f"topic:{t}" for t in topics])
                    if competitors:
                        domains.extend([f"competitor:{c}" for c in competitors])

            # Extract alert rules if available (implementation-specific, but generic pattern)
            if "alert_rules" in config:
                alert_rules = config["alert_rules"]
                if isinstance(alert_rules, dict):
                    confidence_threshold = alert_rules.get("confidence_threshold", confidence_threshold)
                    # Could also extract other rules like keywords, notification preferences, etc.

            self.logger.info(
                f"Enhanced monitoring with config: "
                f"{len(topics)} topics, {len(competitors)} competitors, "
                f"threshold={confidence_threshold}"
            )

        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "domains": domains,
            "signals": [],
            "insights": None,
            "enhanced_with_metadata": enhanced_with_metadata,
            "config": {
                "topics": topics,
                "competitors": competitors,
                "confidence_threshold": confidence_threshold
            }
        }

        # Delegate to monitoring subagents in parallel
        monitoring_tasks = []

        for domain in domains:
            if domain == "competitors" or "competitor" in domain:
                monitoring_tasks.append(("competitor_tracker", f"Monitor competitors in {domain}"))
            elif domain == "social" or "trends" in domain:
                monitoring_tasks.append(("social_listener", f"Monitor social signals for {domain}"))
            else:
                monitoring_tasks.append(("web_monitor", f"Monitor web sources for {domain}"))

        # Execute monitoring (in real implementation, this would be parallel)
        for subagent_name, task in monitoring_tasks:
            try:
                # Get relevant context from memory (filter out metadata context)
                context = None
                if contexts:
                    block_contexts = [c for c in contexts if c.content not in ["[AGENT EXECUTION CONTEXT]", "[METADATA]"]]
                    if block_contexts:
                        context = "\n".join([r.content for r in block_contexts])

                # Delegate to subagent
                result = await self.subagents.delegate(
                    subagent_name=subagent_name,
                    task=task,
                    context=context
                )

                # TODO: Parse result and extract signals
                # For now, store raw result
                results["signals"].append({
                    "domain": domain,
                    "subagent": subagent_name,
                    "result": str(result)
                })

            except Exception as e:
                self.logger.error(f"Monitoring failed for {domain}: {e}")
                results["signals"].append({
                    "domain": domain,
                    "error": str(e)
                })

        # Synthesize findings with analyst subagent
        if results["signals"]:
            synthesis_task = f"Analyze these monitoring findings and provide {self.synthesis_mode} insights"
            synthesis_context = str(results["signals"])

            insights = await self.subagents.delegate(
                subagent_name="analyst",
                task=synthesis_task,
                context=synthesis_context
            )

            results["insights"] = str(insights)

            # Propose insights to memory if governance enabled
            if self.governance and results["insights"]:
                await self._propose_insights(results["insights"])

        self.logger.info(f"Monitoring complete - {len(results['signals'])} signals detected")

        return results

    async def deep_dive(self, topic: str) -> Dict[str, Any]:
        """
        Execute deep-dive research on a specific topic.

        This is on-demand, comprehensive research.

        Args:
            topic: Research topic

        Returns:
            Research findings
        """
        self.logger.info(f"Starting deep-dive research: {topic}")

        # Query existing knowledge
        context = None
        if self.memory:
            memory_results = await self.memory.query(topic, limit=10)
            context = "\n".join([r.content for r in memory_results])

        # Comprehensive research using Claude
        research_prompt = f"""Conduct comprehensive research on: {topic}

**Existing Knowledge:**
{context or "No prior context available"}

**Research Objectives:**
1. Provide comprehensive overview
2. Identify key trends and patterns
3. Analyze implications
4. Generate actionable insights

Please conduct thorough research and synthesis."""

        response = await self.reason(
            task=research_prompt,
            context=context,
            max_tokens=8000  # Longer for deep dives
        )

        results = {
            "topic": topic,
            "timestamp": datetime.utcnow().isoformat(),
            "findings": str(response)
        }

        # Propose findings to memory
        if self.governance:
            await self._propose_insights(results["findings"], topic=topic)

        self.logger.info(f"Deep-dive research complete: {topic}")

        return results

    async def _propose_insights(
        self,
        insights: str,
        topic: Optional[str] = None
    ) -> None:
        """
        Propose research insights to governance for memory storage.

        Args:
            insights: Research insights to store
            topic: Optional topic label
        """
        if not self.governance:
            return

        proposal = await self.governance.propose(
            changes=[
                Change(
                    operation="store",
                    target="research_insights",
                    data={"insights": insights, "topic": topic},
                    reasoning=f"Store research insights{' for ' + topic if topic else ''}"
                )
            ],
            confidence=0.8,
            reasoning="Research findings for memory storage"
        )

        self.logger.info(f"Proposed research insights: {proposal.id}")

        # Note: Actual storage happens after governance approval
        # This would be handled by your service layer

    def _get_default_system_prompt(self) -> str:
        """Get Research Agent specific system prompt."""

        prompt = f"""You are an autonomous Research Agent specializing in intelligence gathering and analysis.

**Your Mission:**
Keep users informed about their markets, competitors, and topics of interest through:
- Continuous monitoring (proactive)
- Deep-dive research (reactive)
- Signal detection (what's important?)
- Insight synthesis (so what?)

**Your Capabilities:**
- Memory: {"Available" if self.memory is not None else "Not configured"}
- Governance: {"Available" if self.governance is not None else "Not configured"}
- Monitoring Domains: {", ".join(self.monitoring_domains)}
- Monitoring Frequency: {self.monitoring_frequency}

**Research Approach:**
1. Query existing knowledge first (avoid redundant research)
2. Identify knowledge gaps
3. Conduct targeted research
4. Synthesize insights (not just data)
5. Propose findings to memory (via governance)

**Quality Standards:**
- Accuracy over speed
- Insights over data dumps
- Actionable over interesting
- Forward-looking over historical

"""

        # Add subagent information
        if self.subagents.list_subagents():
            prompt += "\n" + self.subagents.get_delegation_prompt()

        return prompt
