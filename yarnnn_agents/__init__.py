"""
YARNNN Agents Framework

Governed autonomous agents powered by Claude Agent SDK and YARNNN substrate.

This framework provides the foundation for building agents that:
- Operate autonomously over extended time periods
- Use YARNNN substrate for long-term governed memory
- Submit proposals for human review before changing substrate
- Maintain full auditability of operations
"""

from .base import BaseAgent
from .memory import MemoryLayer
from .governance import GovernanceLayer

__version__ = "0.1.0"
__all__ = ["BaseAgent", "MemoryLayer", "GovernanceLayer"]
