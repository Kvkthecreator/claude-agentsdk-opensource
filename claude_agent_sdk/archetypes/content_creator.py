"""
Content Creator Agent Archetype

Multi-platform content creation with brand voice consistency.
Uses platform-specific subagents for optimization.

Philosophy:
- Voice consistency across all platforms
- Platform-specific optimization
- Efficient repurposing
- Learning from approved content
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


class ContentCreatorAgent(BaseAgent):
    """
    Content creation agent with platform-specific optimization.

    Job-to-be-Done:
    "Create content in my voice, optimized for each platform"

    Core Capabilities:
    - Platform-specific content creation
    - Brand voice consistency
    - Content repurposing across platforms
    - Multi-format support

    Subagents:
    - twitter_writer: Twitter/X posts and threads
    - linkedin_writer: LinkedIn posts and articles
    - blog_writer: Long-form blog posts
    - instagram_creator: Visual content with captions
    - repurposer: Cross-platform content adaptation

    Usage:
        from claude_agent_sdk.archetypes import ContentCreatorAgent
        from claude_agent_sdk.integrations.yarnnn import YarnnnMemory, YarnnnGovernance

        agent = ContentCreatorAgent(
            memory=YarnnnMemory(basket_id="brand_voice"),
            governance=YarnnnGovernance(basket_id="brand_voice"),
            anthropic_api_key="sk-ant-...",
            enabled_platforms=["twitter", "linkedin", "blog"]
        )

        # Create platform-specific content
        result = await agent.create(
            platform="twitter",
            topic="AI agent trends",
            content_type="thread"
        )

        # Repurpose existing content
        result = await agent.repurpose(
            source_platform="blog",
            source_content="My latest blog post...",
            target_platforms=["twitter", "linkedin"]
        )
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

        # Platform configuration
        enabled_platforms: Optional[List[str]] = None,

        # Voice configuration
        brand_voice_mode: Literal["adaptive", "strict", "creative"] = "adaptive",
        voice_temperature: float = 0.7,

        # Advanced configuration
        session_id: Optional[str] = None,
        auto_approve: bool = False,
    ):
        """
        Initialize Content Creator Agent.

        Args:
            memory: Memory provider for brand voice and content history
            anthropic_api_key: Anthropic API key
            governance: Governance provider for content approval
            tasks: Task provider (optional)
            model: Claude model to use
            agent_id: Agent identifier (auto-generated if None)
            agent_name: Human-readable name
            enabled_platforms: Platforms to support (default: all)
            brand_voice_mode: Voice learning approach
            voice_temperature: Creative temperature (0.0-1.0)
            session_id: Session to resume (optional)
            auto_approve: Auto-approve content (not recommended)
        """
        super().__init__(
            agent_id=agent_id,
            agent_type="content_creator",
            agent_name=agent_name or "Content Creator",
            memory=memory,
            governance=governance,
            tasks=tasks,
            anthropic_api_key=anthropic_api_key,
            model=model,
            session_id=session_id,
            auto_approve=auto_approve,
        )

        # Content configuration
        all_platforms = ["twitter", "linkedin", "blog", "instagram", "facebook"]
        self.enabled_platforms = enabled_platforms or all_platforms
        self.brand_voice_mode = brand_voice_mode
        self.voice_temperature = voice_temperature

        # Track content for voice learning
        self.approved_content_count = 0

        # Register subagents
        self._register_subagents()

        self.logger.info(
            f"Content Creator initialized - Platforms: {', '.join(self.enabled_platforms)}, "
            f"Voice mode: {brand_voice_mode}"
        )

    def _register_subagents(self):
        """Register platform-specific content subagents."""

        # Twitter/X Writer Subagent
        if "twitter" in self.enabled_platforms:
            self.subagents.register(
                SubagentDefinition(
                    name="twitter_writer",
                    description="Write engaging Twitter/X posts and threads (280 chars max)",
                    system_prompt="""You are a Twitter/X content specialist.

Platform Constraints:
- 280 character limit per tweet
- Thread format for longer content
- Casual, conversational tone
- Strategic hashtag use (2-3 max)
- Strong hooks in first tweet
- Visual media support (images, GIFs)

Best Practices:
- Start with attention-grabbing hook
- Use line breaks for readability
- Include call-to-action
- Engage with questions
- Use emojis sparingly but effectively

Content Types:
- Single tweets (insights, quotes, announcements)
- Threads (tutorials, stories, deep dives)
- Quote tweets (commentary on trends)

Output Format:
- For single tweet: Just the tweet text
- For thread: Number each tweet (1/, 2/, etc.)
""",
                    tools=None,  # Text-only for now
                    metadata={"platform": "twitter", "char_limit": 280}
                )
            )

        # LinkedIn Writer Subagent
        if "linkedin" in self.enabled_platforms:
            self.subagents.register(
                SubagentDefinition(
                    name="linkedin_writer",
                    description="Write professional LinkedIn posts and articles",
                    system_prompt="""You are a LinkedIn content specialist.

Platform Expectations:
- Professional but authentic tone
- 1300-2000 character posts (sweet spot for engagement)
- Long-form articles (1000-3000 words)
- Thought leadership positioning
- Data and insights emphasis
- Personal stories with professional lessons

Best Practices:
- Strong opening line (grab feed attention)
- Use line breaks (3-4 line paragraphs max)
- Include relevant hashtags (3-5)
- Add call-to-action
- Tag relevant people/companies when appropriate
- Share lessons learned, not just achievements

Content Types:
- Insight posts (professional observations)
- Story posts (personal experiences with lessons)
- Articles (deep dives on professional topics)
- Announcements (product launches, milestones)

Output Format:
- Clear structure with line breaks
- Professional but conversational
- Data-backed when possible
""",
                    tools=None,
                    metadata={"platform": "linkedin", "recommended_length": "1300-2000"}
                )
            )

        # Blog Writer Subagent
        if "blog" in self.enabled_platforms:
            self.subagents.register(
                SubagentDefinition(
                    name="blog_writer",
                    description="Write SEO-optimized long-form blog posts and articles",
                    system_prompt="""You are a blog content specialist.

Platform Expectations:
- SEO-optimized long-form (1500-3000 words)
- Clear structure (H2, H3 headings)
- Scannable (bullets, numbered lists)
- Internal/external links
- Meta description ready
- Featured image concepts

Best Practices:
- Compelling title (H1) - SEO + clickable
- Clear introduction (what, why, for who)
- Structured sections with H2/H3
- Examples and case studies
- Visual concepts (images, diagrams)
- Actionable takeaways
- Strong conclusion with CTA

Content Structure:
1. Title (SEO optimized)
2. Meta description (150-160 chars)
3. Introduction (hook + preview)
4. Body (3-5 main sections)
5. Conclusion (summary + CTA)
6. Suggested images/visuals

Output Format:
- Markdown formatting
- Clear heading hierarchy
- Code blocks if technical
- Image placeholders with descriptions
""",
                    tools=None,
                    metadata={"platform": "blog", "recommended_length": "1500-3000"}
                )
            )

        # Instagram Creator Subagent
        if "instagram" in self.enabled_platforms:
            self.subagents.register(
                SubagentDefinition(
                    name="instagram_creator",
                    description="Create Instagram posts with visual concepts and captions",
                    system_prompt="""You are an Instagram content specialist.

Platform Expectations:
- Visual-first (image/carousel is primary)
- Caption structure:
  - Hook (first 125 chars - shows in feed)
  - Body (up to 2200 chars total)
  - Call-to-action
  - Hashtags (5-10 relevant)
- Story format (vertical, ephemeral, casual)
- Carousel posts (multi-slide value)

Best Practices:
- Strong hook in first line
- Line breaks for readability
- Emoji use (strategic, on-brand)
- Hashtag research (niche + broad)
- Save-worthy content (high value)
- Engagement prompts (questions, polls)

Content Types:
- Feed posts (value, inspiration, behind-scenes)
- Carousel posts (tutorials, before/after, tips)
- Reels captions (short, punchy, trending)
- Stories (casual, time-sensitive)

Output Format:
1. Visual concept description
2. Caption with hook
3. Hashtag set (5-10)
4. Alt text for accessibility
""",
                    tools=None,
                    metadata={"platform": "instagram", "caption_limit": 2200}
                )
            )

        # Content Repurposer Subagent
        self.subagents.register(
            SubagentDefinition(
                name="repurposer",
                description="Adapt content across platforms while maintaining core message and voice",
                system_prompt="""You are a content repurposing specialist.

Your Mission:
Transform content between platforms while maintaining:
- Core message and value
- Brand voice consistency
- Platform-specific optimization

Common Transformations:
1. Blog → Twitter thread (extract key points)
2. Blog → LinkedIn post (professional angle)
3. LinkedIn → Twitter (condense, casualize)
4. Long-form → Instagram carousel (visual breakdown)
5. Technical → Non-technical (simplify)

Repurposing Strategy:
- Identify core message/value
- Extract 3-5 key points
- Adapt tone for target platform
- Optimize format (length, structure)
- Maintain brand voice
- Add platform-specific elements (hashtags, hooks)

Output Format:
For each target platform:
1. Platform name
2. Adapted content
3. Platform-specific notes (hashtags, visual needs, etc.)
""",
                tools=None,
                metadata={"type": "repurposer"}
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
        Execute a content creation task.

        Automatically routes based on task type.

        Args:
            task: Task description
            task_id: Optional task ID
            task_metadata: Optional task metadata
            **kwargs: Additional arguments

        Returns:
            Content creation results
        """
        # Start session
        if not self.current_session:
            self.current_session = self._start_session(task_id, task_metadata)

        # Parse task
        task_lower = task.lower()

        # Route based on keywords
        if "repurpose" in task_lower or "adapt" in task_lower:
            # Extract source and targets from kwargs
            return await self.repurpose(
                source_content=kwargs.get("source_content", ""),
                source_platform=kwargs.get("source_platform"),
                target_platforms=kwargs.get("target_platforms", self.enabled_platforms)
            )
        else:
            # Create new content
            # Detect platform from task
            platform = self._detect_platform(task)
            return await self.create(
                platform=platform,
                topic=task,
                content_type=kwargs.get("content_type", "post")
            )

    def _detect_platform(self, task: str) -> str:
        """Detect target platform from task description."""
        task_lower = task.lower()

        if "twitter" in task_lower or "tweet" in task_lower or "thread" in task_lower:
            return "twitter"
        elif "linkedin" in task_lower:
            return "linkedin"
        elif "blog" in task_lower or "article" in task_lower:
            return "blog"
        elif "instagram" in task_lower or "insta" in task_lower:
            return "instagram"
        else:
            # Default to first enabled platform
            return self.enabled_platforms[0] if self.enabled_platforms else "twitter"

    async def create(
        self,
        platform: str,
        topic: str,
        content_type: str = "post"
    ) -> Dict[str, Any]:
        """
        Create platform-specific content with optional metadata enhancement.

        Metadata Enhancement:
        - Uses reference_assets (brand guidelines, examples) if available
        - Applies agent_config (tone preferences, platform rules) if available
        - Gracefully degrades if metadata not provided (backward compatible)

        Args:
            platform: Target platform (twitter, linkedin, blog, instagram)
            topic: Content topic/brief
            content_type: Type of content (post, thread, article, carousel)

        Returns:
            Created content with metadata
        """
        self.logger.info(f"Creating {content_type} for {platform}: {topic[:50]}...")

        # Get brand voice context from memory
        contexts = []
        voice_context = ""

        if self.memory:
            # Query for approved content to learn voice
            contexts = await self.memory.query(
                f"{platform} approved content",
                limit=5
            )

            # Separate metadata context from regular block contexts
            block_contexts = [c for c in contexts if c.content not in ["[AGENT EXECUTION CONTEXT]", "[METADATA]"]]

            if block_contexts:
                voice_context = "Previous approved content (learn voice):\n"
                voice_context += "\n---\n".join([ctx.content for ctx in block_contexts])

        # ENHANCEMENT: Extract metadata (generic pattern)
        metadata = extract_metadata_from_contexts(contexts)
        enhanced_with_metadata = bool(metadata)

        # Build enhanced context from metadata (if available)
        if metadata:
            # Use reference assets if available (implementation-specific, but generic pattern)
            assets = metadata.get("reference_assets", [])
            if assets:
                voice_context += "\n\n=== Reference Materials ===\n"
                for asset in assets:
                    # Generic: Use whatever fields the asset has
                    name = asset.get("file_name", asset.get("name", "Unknown"))
                    desc = asset.get("description", "")
                    asset_type = asset.get("asset_type", asset.get("type", ""))
                    url = asset.get("signed_url", asset.get("url", ""))

                    voice_context += f"\n- **{name}**"
                    if asset_type:
                        voice_context += f" ({asset_type})"
                    if desc:
                        voice_context += f": {desc}"
                    if url:
                        voice_context += f"\n  URL: {url}"
                    voice_context += "\n"

                self.logger.info(f"Enhanced prompt with {len(assets)} reference assets")

            # Use agent config if available (implementation-specific, but generic pattern)
            config = metadata.get("agent_config", {})
            if config:
                voice_context += "\n\n=== Content Guidelines ===\n"

                # Example: Extract brand voice preferences (if implementation provides it)
                if "brand_voice" in config:
                    brand_voice = config["brand_voice"]
                    if isinstance(brand_voice, dict):
                        if "tone" in brand_voice:
                            voice_context += f"Tone: {brand_voice['tone']}\n"
                        if "voice_guidelines" in brand_voice:
                            voice_context += f"Voice: {brand_voice['voice_guidelines']}\n"
                    else:
                        voice_context += f"Brand Voice: {brand_voice}\n"

                # Example: Extract platform-specific settings (if implementation provides it)
                if "platforms" in config:
                    platform_config = config["platforms"].get(platform.lower(), {})
                    if platform_config:
                        if platform_config.get("include_hashtags"):
                            voice_context += "Include relevant hashtags.\n"
                        if platform_config.get("max_hashtags"):
                            voice_context += f"Maximum hashtags: {platform_config['max_hashtags']}\n"
                        if platform_config.get("include_emojis"):
                            voice_context += "Use emojis strategically.\n"

                # Example: Extract content rules (if implementation provides it)
                if "content_rules" in config:
                    rules = config["content_rules"]
                    if isinstance(rules, list):
                        voice_context += "Content Rules:\n"
                        for rule in rules:
                            voice_context += f"- {rule}\n"
                    elif isinstance(rules, dict):
                        for rule_type, rule_value in rules.items():
                            voice_context += f"{rule_type}: {rule_value}\n"

                self.logger.info(f"Enhanced prompt with agent configuration")

        # Select appropriate subagent
        subagent_name = f"{platform}_writer"
        if subagent_name not in [s.name for s in self.subagents.list_subagents()]:
            raise ValueError(f"Platform '{platform}' not supported or not enabled")

        # Delegate to platform subagent
        content_brief = f"Create a {content_type} about: {topic}"

        result = await self.subagents.delegate(
            subagent_name=subagent_name,
            task=content_brief,
            context=voice_context if voice_context else None
        )

        # Prepare results
        created_content = {
            "platform": platform,
            "content_type": content_type,
            "topic": topic,
            "content": str(result),
            "timestamp": datetime.utcnow().isoformat(),
            "status": "pending_approval",
            "enhanced_with_metadata": enhanced_with_metadata
        }

        # Propose to governance for approval
        if self.governance:
            await self._propose_content(created_content)

        self.logger.info(
            f"Content created for {platform}: {content_type}"
            f"{' (metadata-enhanced)' if enhanced_with_metadata else ''}"
        )

        return created_content

    async def repurpose(
        self,
        source_content: str,
        source_platform: Optional[str] = None,
        target_platforms: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Repurpose content across platforms.

        Args:
            source_content: Original content to repurpose
            source_platform: Source platform (optional)
            target_platforms: Target platforms (default: all enabled)

        Returns:
            Repurposed content for each platform
        """
        targets = target_platforms or self.enabled_platforms

        self.logger.info(f"Repurposing content to {len(targets)} platforms")

        # Build repurposing brief
        task = f"Adapt this content for {', '.join(targets)}:\n\n{source_content}"
        if source_platform:
            task = f"Original platform: {source_platform}\n{task}"

        # Delegate to repurposer
        result = await self.subagents.delegate(
            subagent_name="repurposer",
            task=task
        )

        repurposed = {
            "source_content": source_content,
            "source_platform": source_platform,
            "target_platforms": targets,
            "repurposed_content": str(result),
            "timestamp": datetime.utcnow().isoformat()
        }

        # Propose to governance
        if self.governance:
            await self._propose_content(repurposed, is_repurposed=True)

        return repurposed

    async def _propose_content(
        self,
        content: Dict[str, Any],
        is_repurposed: bool = False
    ) -> None:
        """
        Propose content to governance for approval.

        Args:
            content: Content to propose
            is_repurposed: Whether content is repurposed
        """
        if not self.governance:
            return

        content_type = "repurposed content" if is_repurposed else f"{content.get('platform')} {content.get('content_type')}"

        proposal = await self.governance.propose(
            changes=[
                Change(
                    operation="publish_content",
                    target=content.get("platform", "multi-platform"),
                    data=content,
                    reasoning=f"Content approval for {content_type}"
                )
            ],
            confidence=0.8,
            reasoning=f"Generated {content_type} for review"
        )

        self.logger.info(f"Proposed content for approval: {proposal.id}")

        # Track for voice learning
        self.approved_content_count += 1

    def _get_default_system_prompt(self) -> str:
        """Get Content Creator specific system prompt."""

        prompt = f"""You are an autonomous Content Creator Agent specializing in multi-platform content.

**Your Mission:**
Create high-quality content that:
- Maintains consistent brand voice
- Optimizes for each platform
- Engages target audience
- Drives desired actions

**Your Capabilities:**
- Memory: {"Available" if self.memory is not None else "Not configured"}
- Governance: {"Available" if self.governance is not None else "Not configured"}
- Enabled Platforms: {", ".join(self.enabled_platforms)}
- Voice Mode: {self.brand_voice_mode}

**Content Philosophy:**
1. Voice Consistency: Learn from approved content in memory
2. Platform Optimization: Adapt format, length, tone per platform
3. Value First: Every piece must provide clear value
4. Engagement: Include clear calls-to-action
5. Quality > Quantity: Better to delay than publish mediocre content

**Brand Voice Learning:**
- Query memory for approved content examples
- Identify voice patterns (tone, style, vocabulary)
- Adapt new content to match learned voice
- Approved content count: {self.approved_content_count}

"""

        # Add subagent information
        if self.subagents.list_subagents():
            prompt += "\n" + self.subagents.get_delegation_prompt()

        return prompt
