"""
Agent Archetypes - Reusable agent patterns

This module provides pre-built agent archetypes that can be configured
and customized for specific use cases.

Archetypes:
- ResearchAgent: Continuous monitoring and deep-dive research
- ContentCreator: Multi-platform content creation
- ReportingAgent: Document and report generation
"""

from .research_agent import ResearchAgent
from .content_creator import ContentCreatorAgent
from .reporting_agent import ReportingAgent

__all__ = [
    "ResearchAgent",
    "ContentCreatorAgent",
    "ReportingAgent",
]
