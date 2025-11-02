"""
Reporting Agent Archetype

Generate professional reports and artifacts in various formats.
Uses format-specific subagents and template learning.

Philosophy:
- Data → Insights → Deliverables
- Template-based style consistency
- Professional formatting
- Multi-format support
"""

import logging
from typing import Any, Dict, List, Optional, Literal
from datetime import datetime

from ..base import BaseAgent
from ..subagents import SubagentDefinition
from ..interfaces import MemoryProvider, GovernanceProvider, TaskProvider, Change


logger = logging.getLogger(__name__)


class ReportingAgent(BaseAgent):
    """
    Reporting agent for generating professional documents and artifacts.

    Job-to-be-Done:
    "Turn information into professional deliverables"

    Core Capabilities:
    - Data analysis and visualization
    - Document composition (Excel, PDF, PPT)
    - Template application
    - Brand/style consistency

    Subagents:
    - excel_specialist: Complex spreadsheets with formulas and charts
    - presentation_designer: Slide decks and presentations
    - report_writer: Professional PDFs and reports
    - data_analyst: Data processing and insights

    Usage:
        from claude_agent_sdk.archetypes import ReportingAgent
        from claude_agent_sdk.integrations.yarnnn import YarnnnMemory, YarnnnGovernance

        agent = ReportingAgent(
            memory=YarnnnMemory(basket_id="artifacts"),
            governance=YarnnnGovernance(basket_id="artifacts"),
            anthropic_api_key="sk-ant-...",
            template_library={
                "excel": "path/to/template.xlsx",
                "ppt": "path/to/template.pptx"
            }
        )

        # Generate monthly report
        result = await agent.generate(
            report_type="monthly_metrics",
            format="ppt",
            data=metrics_data
        )

        # Create executive summary
        result = await agent.generate(
            report_type="executive_summary",
            format="pdf",
            data=analysis_results
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

        # Template configuration
        template_library: Optional[Dict[str, str]] = None,
        brand_guidelines: Optional[Dict[str, Any]] = None,

        # Format preferences
        default_formats: Optional[List[str]] = None,

        # Advanced configuration
        session_id: Optional[str] = None,
        auto_approve: bool = False,
    ):
        """
        Initialize Reporting Agent.

        Args:
            memory: Memory provider for templates and past reports
            anthropic_api_key: Anthropic API key
            governance: Governance provider for approvals
            tasks: Task provider (optional)
            model: Claude model to use
            agent_id: Agent identifier (auto-generated if None)
            agent_name: Human-readable name
            template_library: Paths to template files by format
            brand_guidelines: Brand colors, fonts, logos
            default_formats: Preferred output formats
            session_id: Session to resume (optional)
            auto_approve: Auto-approve reports (not recommended)
        """
        super().__init__(
            agent_id=agent_id,
            agent_type="reporting",
            agent_name=agent_name or "Reporting Agent",
            memory=memory,
            governance=governance,
            tasks=tasks,
            anthropic_api_key=anthropic_api_key,
            model=model,
            session_id=session_id,
            auto_approve=auto_approve,
        )

        # Reporting configuration
        self.template_library = template_library or {}
        self.brand_guidelines = brand_guidelines or {}
        self.default_formats = default_formats or ["pdf", "xlsx"]

        # Register subagents
        self._register_subagents()

        self.logger.info(
            f"Reporting Agent initialized - Formats: {', '.join(self.default_formats)}"
        )

    def _register_subagents(self):
        """Register format-specific reporting subagents."""

        # Excel Specialist Subagent
        self.subagents.register(
            SubagentDefinition(
                name="excel_specialist",
                description="Create Excel spreadsheets with formulas, charts, and pivot tables",
                system_prompt="""You are an Excel specialist focused on professional spreadsheet creation.

Your Expertise:
- Complex formulas (VLOOKUP, INDEX/MATCH, SUMIFS)
- Data tables and formatting
- Charts and visualizations
- Pivot tables and summaries
- Conditional formatting
- Data validation

Spreadsheet Structure:
1. Summary sheet (executive overview)
2. Data sheets (raw data, organized)
3. Analysis sheets (calculations, insights)
4. Charts sheet (visualizations)

Best Practices:
- Clear sheet organization
- Named ranges for formulas
- Consistent formatting
- Professional color schemes
- Data validation for inputs
- Protection for formula cells
- Print-friendly layouts

Output Format:
Provide detailed specification:
1. Sheet structure (names, purpose)
2. Key formulas and logic
3. Chart specifications
4. Formatting guidelines
5. Data validation rules

Note: You provide specifications; actual .xlsx creation
happens via document generation tools.
""",
                tools=None,  # Specs only
                metadata={"format": "xlsx", "type": "specialist"}
            )
        )

        # Presentation Designer Subagent
        self.subagents.register(
            SubagentDefinition(
                name="presentation_designer",
                description="Design PowerPoint presentations with professional layouts",
                system_prompt="""You are a presentation design specialist.

Your Expertise:
- Slide layout design
- Visual hierarchy
- Data visualization for slides
- Storytelling through slides
- Professional formatting

Presentation Structure:
1. Title slide (branding, topic)
2. Agenda/Overview
3. Content slides (3-5 key points each)
4. Data slides (charts, metrics)
5. Conclusion/Recommendations
6. Appendix (supporting data)

Design Principles:
- One idea per slide
- 3-5 bullets max
- Large, readable fonts
- High-contrast colors
- Consistent layout
- Professional imagery
- Data-driven visuals

Slide Types:
- Title slides
- Bullet point slides
- Data/chart slides
- Image slides
- Quote/callout slides
- Comparison slides

Output Format:
For each slide, specify:
1. Slide number and title
2. Layout type
3. Content (text, bullets)
4. Visual elements (charts, images)
5. Design notes (colors, emphasis)
""",
                tools=None,
                metadata={"format": "pptx", "type": "specialist"}
            )
        )

        # Report Writer Subagent
        self.subagents.register(
            SubagentDefinition(
                name="report_writer",
                description="Write professional PDF reports and executive summaries",
                system_prompt="""You are a professional report writer.

Your Expertise:
- Executive summaries
- Technical reports
- Business analysis reports
- Research reports
- Professional formatting

Report Structure:
1. Cover page (title, date, author)
2. Executive summary (1-2 pages)
3. Table of contents
4. Main sections (analysis, findings)
5. Recommendations
6. Appendices (supporting data)

Writing Style:
- Clear, concise, professional
- Data-backed assertions
- Structured paragraphs
- Visual breaks (headings, bullets)
- Actionable recommendations
- Forward-looking insights

Report Types:
- Monthly/Quarterly reports
- Executive summaries
- Technical analysis
- Market research
- Business cases
- Project retrospectives

Output Format:
Provide report in structured format:
- Markdown or structured text
- Clear section headings
- Data tables where appropriate
- Chart/visual placeholders
- Citations and references
""",
                tools=None,
                metadata={"format": "pdf", "type": "specialist"}
            )
        )

        # Data Analyst Subagent
        self.subagents.register(
            SubagentDefinition(
                name="data_analyst",
                description="Analyze data, identify patterns, generate insights",
                system_prompt="""You are a data analyst focused on extracting insights.

Your Expertise:
- Data analysis and interpretation
- Trend identification
- Pattern recognition
- Statistical analysis
- Insight generation
- Recommendation development

Analysis Approach:
1. Understand the question
2. Explore the data
3. Identify patterns/trends
4. Assess significance
5. Generate insights
6. Develop recommendations

Analysis Types:
- Descriptive (what happened?)
- Diagnostic (why did it happen?)
- Predictive (what might happen?)
- Prescriptive (what should we do?)

Output Format:
1. Executive summary (key insights)
2. Data overview (what was analyzed)
3. Findings (patterns, trends, anomalies)
4. Insights (so what? implications)
5. Recommendations (actions to take)
6. Supporting data (charts, tables)

Quality Standards:
- Data-backed conclusions
- Clear cause-effect relationships
- Actionable recommendations
- Appropriate visualizations
- Statistical rigor when needed
""",
                tools=None,
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
        Execute a reporting task.

        Args:
            task: Task description
            task_id: Optional task ID
            task_metadata: Optional task metadata
            **kwargs: Additional arguments (data, format, etc.)

        Returns:
            Generated report
        """
        # Start session
        if not self.current_session:
            self.current_session = self._start_session(task_id, task_metadata)

        # Extract parameters
        report_type = kwargs.get("report_type", "general")
        format = kwargs.get("format", self.default_formats[0])
        data = kwargs.get("data")

        return await self.generate(
            report_type=report_type,
            format=format,
            data=data,
            task_description=task
        )

    async def generate(
        self,
        report_type: str,
        format: Literal["pdf", "xlsx", "pptx"],
        data: Optional[Any] = None,
        task_description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a report in specified format.

        Args:
            report_type: Type of report (monthly_metrics, executive_summary, etc.)
            format: Output format (pdf, xlsx, pptx)
            data: Data to include in report
            task_description: Additional context

        Returns:
            Generated report specification
        """
        self.logger.info(f"Generating {report_type} report in {format} format")

        # Step 1: Analyze data if provided
        analysis = None
        if data:
            analysis = await self._analyze_data(data, report_type)

        # Step 2: Get templates and style from memory
        style_context = await self._get_style_context(format)

        # Step 3: Delegate to format-specific subagent
        subagent_name = self._get_format_subagent(format)

        brief = self._build_report_brief(
            report_type=report_type,
            format=format,
            analysis=analysis,
            task_description=task_description
        )

        result = await self.subagents.delegate(
            subagent_name=subagent_name,
            task=brief,
            context=style_context
        )

        # Prepare report
        report = {
            "report_type": report_type,
            "format": format,
            "specification": str(result),
            "analysis": analysis,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "pending_approval"
        }

        # Propose to governance
        if self.governance:
            await self._propose_report(report)

        self.logger.info(f"Report generated: {report_type} ({format})")

        return report

    async def _analyze_data(
        self,
        data: Any,
        report_type: str
    ) -> Dict[str, Any]:
        """
        Analyze data using analyst subagent.

        Args:
            data: Data to analyze
            report_type: Type of report

        Returns:
            Analysis results
        """
        self.logger.info("Analyzing data...")

        # Build analysis task
        task = f"Analyze this data for {report_type} report:\n\n{str(data)}"

        # Delegate to analyst
        result = await self.subagents.delegate(
            subagent_name="data_analyst",
            task=task
        )

        return {
            "insights": str(result),
            "data_summary": str(data)[:500]  # Truncate for storage
        }

    async def _get_style_context(self, format: str) -> Optional[str]:
        """
        Get style/template context from memory.

        Args:
            format: Output format

        Returns:
            Style guidelines and examples
        """
        if not self.memory:
            return None

        # Query for template examples
        results = await self.memory.query(
            f"{format} template examples approved",
            limit=3
        )

        if results:
            context = f"Style guidelines for {format}:\n"
            context += "\n".join([r.content for r in results])
            return context

        return None

    def _get_format_subagent(self, format: str) -> str:
        """Map format to subagent name."""
        mapping = {
            "xlsx": "excel_specialist",
            "pptx": "presentation_designer",
            "pdf": "report_writer"
        }
        return mapping.get(format, "report_writer")

    def _build_report_brief(
        self,
        report_type: str,
        format: str,
        analysis: Optional[Dict[str, Any]],
        task_description: Optional[str]
    ) -> str:
        """Build comprehensive brief for subagent."""

        brief = f"Create a {report_type} report in {format} format.\n\n"

        if task_description:
            brief += f"**Context:** {task_description}\n\n"

        if analysis:
            brief += f"**Data Analysis:**\n{analysis.get('insights', 'No analysis provided')}\n\n"

        # Add template guidance if available
        if format in self.template_library:
            brief += f"**Template:** Use style from {self.template_library[format]}\n\n"

        # Add brand guidelines
        if self.brand_guidelines:
            brief += "**Brand Guidelines:**\n"
            for key, value in self.brand_guidelines.items():
                brief += f"- {key}: {value}\n"
            brief += "\n"

        brief += "Provide detailed specification for this report."

        return brief

    async def _propose_report(self, report: Dict[str, Any]) -> None:
        """
        Propose report to governance.

        Args:
            report: Report to propose
        """
        if not self.governance:
            return

        proposal = await self.governance.propose(
            changes=[
                Change(
                    operation="generate_report",
                    target=report["format"],
                    data=report,
                    reasoning=f"Generated {report['report_type']} report"
                )
            ],
            confidence=0.8,
            reasoning=f"Report specification for {report['report_type']}"
        )

        self.logger.info(f"Proposed report for approval: {proposal.id}")

    def _get_default_system_prompt(self) -> str:
        """Get Reporting Agent specific system prompt."""

        prompt = f"""You are an autonomous Reporting Agent specializing in professional document generation.

**Your Mission:**
Transform data and information into professional deliverables:
- Executive summaries
- Data reports
- Presentations
- Analysis documents

**Your Capabilities:**
- Memory: {"Available" if self.memory is not None else "Not configured"}
- Governance: {"Available" if self.governance is not None else "Not configured"}
- Supported Formats: {", ".join(self.default_formats)}
- Templates: {len(self.template_library)} configured

**Reporting Philosophy:**
1. Data → Insights → Action
2. Professional formatting and polish
3. Template consistency
4. Brand guideline adherence
5. Audience-appropriate detail level

**Quality Standards:**
- Clear structure and flow
- Data-backed assertions
- Professional formatting
- Actionable recommendations
- Visual clarity

"""

        # Add brand guidelines summary
        if self.brand_guidelines:
            prompt += "\n**Brand Guidelines:**\n"
            for key, value in self.brand_guidelines.items():
                prompt += f"- {key}: {value}\n"

        # Add subagent information
        if self.subagents.list_subagents():
            prompt += "\n" + self.subagents.get_delegation_prompt()

        return prompt
